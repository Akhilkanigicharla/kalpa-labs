#!/usr/bin/env python3
"""Pull a client's LLM usage out of their Langfuse (open source, MIT core) into the
usage CSV that audit.py reads. A215: "we install Langfuse for you, find the savings".

API: GET /api/public/v2/observations (Observations API v2, cursor pages, limit <= 1000),
checked on langfuse.com/docs/api-and-data-platform/features/public-api on 2026-11-21.

Keys come from the environment only (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY), never
from the command line, and are never printed. Only usage numbers are read (no prompt or
answer text: the "io" field group is never requested), so no client personal data lands here.

    LANGFUSE_HOST=https://cloud.langfuse.com python3 langfuse_pull.py --from 2026-10-01 --to 2026-11-01 --out usage.csv
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

FIELDS = "core,basic,model,usage,trace_context"
PAGE = 1000            # API maximum
MAX_PAGES = 500        # hard stop: 500k observations per run
TIMEOUT = 30           # seconds per request
RETRIES = 4            # on 429 / 5xx / network errors, with backoff
COLUMNS = ["date", "feature", "model", "provider", "requests", "input_tokens", "output_tokens",
           "cached_tokens", "cost", "prompt_hash", "status"]
# usageDetails keys that mean "input tokens served from the provider's prompt cache"
CACHE_KEYS = ("input_cached_tokens", "cache_read_input_tokens", "input_cache_read", "cached_tokens")


def check_host(host: str) -> str:
    """https anywhere; plain http only for a Langfuse on this machine (the CI demo)."""
    u = urllib.parse.urlparse((host or "").strip())
    local = u.hostname in ("localhost", "127.0.0.1")
    if u.scheme not in ("https", "http") or not u.hostname or (u.scheme == "http" and not local):
        raise ValueError("LANGFUSE_HOST must be an https:// URL (http only for localhost)")
    if u.username or u.password or u.query or u.fragment:
        raise ValueError("LANGFUSE_HOST must not carry credentials, a query or a fragment")
    return f"{u.scheme}://{u.netloc}{u.path.rstrip('/')}"


def _iso_day(s: str, flag: str) -> str:
    try:
        return date.fromisoformat(s).isoformat() + "T00:00:00Z"
    except ValueError:
        raise ValueError(f"{flag} must be a date like 2026-11-01") from None


def _get(url: str, auth: str, opener=None, sleep=time.sleep) -> dict:
    opener = opener or urllib.request.urlopen
    req = urllib.request.Request(url, headers={"Authorization": auth, "Accept": "application/json",
                                               "User-Agent": "kalpa-p1-audit"})
    for attempt in range(RETRIES + 1):
        try:
            with opener(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise PermissionError("Langfuse refused the keys (401/403): check the project keys") from None
            if e.code != 429 and e.code < 500 or attempt == RETRIES:
                raise RuntimeError(f"Langfuse answered HTTP {e.code}") from None
            wait = e.headers.get("Retry-After") if e.headers else None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == RETRIES:
                raise RuntimeError(f"cannot reach Langfuse ({getattr(e, 'reason', e)})") from None
            wait = None
        sleep(min(float(wait) if wait and str(wait).isdigit() else 2 ** attempt, 30))
    raise RuntimeError("unreachable")  # pragma: no cover


def fetch(host: str, pk: str, sk: str, start: str, end: str, *, opener=None,
          sleep=time.sleep, max_pages: int = MAX_PAGES) -> tuple[list[dict], bool]:
    """All GENERATION observations in [start, end). Returns (observations, truncated)."""
    if not pk or not sk:
        raise ValueError("set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in the environment")
    auth = "Basic " + base64.b64encode(f"{pk}:{sk}".encode()).decode()
    base = check_host(host) + "/api/public/v2/observations"
    params = {"type": "GENERATION", "fields": FIELDS, "limit": PAGE,
              "fromStartTime": _iso_day(start, "--from"), "toStartTime": _iso_day(end, "--to")}
    out, cursor = [], None
    for _ in range(max_pages):
        q = dict(params, **({"cursor": cursor} if cursor else {}))
        body = _get(base + "?" + urllib.parse.urlencode(q), auth, opener, sleep)
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list):
            raise RuntimeError("unexpected Langfuse answer (no data list)")
        out.extend(o for o in data if isinstance(o, dict))
        cursor = (body.get("meta") or {}).get("cursor")
        if not cursor:   # an empty page with a cursor is not the end (API docs)
            return out, False
    return out, True


def _num(x) -> Decimal:
    try:
        d = Decimal(str(x)) if x not in (None, "") else Decimal(0)
    except InvalidOperation:
        return Decimal(0)
    return d if d.is_finite() and d >= 0 else Decimal(0)


def _clean(s, limit=80) -> str:
    """Keep labels CSV- and spreadsheet-safe: one line, short, no formula start."""
    s = " ".join(str(s or "").split())[:limit]
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


def to_rows(observations: list[dict]) -> tuple[list[dict], list[str]]:
    """Group generations into audit.py rows: one per day + feature + model + ok/error."""
    buckets = defaultdict(lambda: {"requests": 0, "in": 0, "out": 0, "cached": 0, "cost": Decimal(0)})
    notes, no_cost = [], 0
    for o in observations:
        try:
            day = datetime.fromisoformat(str(o.get("startTime", "")).replace("Z", "+00:00"))
            day = day.astimezone(timezone.utc).date().isoformat()
        except ValueError:
            notes.append(f"skipped observation {_clean(o.get('id'), 40)}: no valid startTime")
            continue
        model = _clean(o.get("model") or o.get("providedModelName"))
        if not model:
            notes.append(f"skipped observation {_clean(o.get('id'), 40)}: no model")
            continue
        feature = _clean(o.get("traceName") or o.get("name") or "(untagged)")
        status = "error" if str(o.get("level", "")).upper() == "ERROR" else "ok"
        usage = o.get("usageDetails") if isinstance(o.get("usageDetails"), dict) else {}
        inp = int(_num(o.get("inputUsage", usage.get("input"))))
        out = int(_num(o.get("outputUsage", usage.get("output"))))
        cached = min(sum(int(_num(usage.get(k))) for k in CACHE_KEYS), inp)
        cost = o.get("totalCost")
        if cost in (None, ""):
            cost = (o.get("costDetails") or {}).get("total") if isinstance(o.get("costDetails"), dict) else None
        if cost in (None, ""):
            no_cost += 1
        b = buckets[(day, feature, model, status)]
        b["requests"] += 1
        b["in"] += inp
        b["out"] += out
        b["cached"] += cached
        b["cost"] += _num(cost)
    if no_cost:
        notes.append(f"{no_cost} generation(s) had no cost in Langfuse (model price not set there); "
                     "counted as 0, so the spend total is too low until the model price is added in Langfuse")
    rows = [{"date": d, "feature": f, "model": m, "provider": "", "requests": b["requests"],
             "input_tokens": b["in"], "output_tokens": b["out"], "cached_tokens": b["cached"],
             "cost": f"{b['cost']:.6f}", "prompt_hash": "", "status": s}
            for (d, f, m, s), b in sorted(buckets.items())]
    return rows, notes


def write_csv(rows: list[dict], path: str, *, source: str, synthetic: bool = False) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        if synthetic:
            fh.write("# SYNTHETIC SAMPLE DATA - seeded into a throwaway demo Langfuse. Not a real client.\n")
        fh.write(f"# Source: Langfuse Observations API v2 ({source}). One row = day+feature+model bucket.\n")
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Langfuse usage -> P1 audit CSV")
    ap.add_argument("--from", dest="start", required=True, help="first day, YYYY-MM-DD (UTC)")
    ap.add_argument("--to", dest="end", required=True, help="day after the last day, YYYY-MM-DD")
    ap.add_argument("--out", required=True)
    ap.add_argument("--synthetic", action="store_true", help="mark the CSV as demo data")
    a = ap.parse_args(argv)
    host = os.environ.get("LANGFUSE_HOST", "")
    try:
        obs, truncated = fetch(host, os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
                               os.environ.get("LANGFUSE_SECRET_KEY", ""), a.start, a.end)
    except (ValueError, PermissionError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    rows, notes = to_rows(obs)
    if truncated:
        notes.append(f"stopped after {MAX_PAGES} pages; narrow --from/--to and run again")
    write_csv(rows, a.out, source=f"{urllib.parse.urlparse(check_host(host)).hostname}, {a.start} to {a.end}",
              synthetic=a.synthetic)
    print(f"{len(obs)} generations -> {len(rows)} rows in {a.out}")
    for n in notes:
        print("note:", n)
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())

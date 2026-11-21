#!/usr/bin/env python3
"""A227/A61 post-deploy smoke: hit each live URL in smoke-targets.json and write smoke-results.json for check.py.

    python3 00-hq/launch/smoke.py                 # every target with a url
    python3 00-hq/launch/smoke.py --only hq-site  # one target (run this after every deploy)

Checks per target (pick in smoke-targets.json):
  page     GET url -> 200 HTML within 20 s
  headers  HSTS, nosniff, clickjacking block, CSP, Referrer-Policy, Permissions-Policy on that response
  chat     POST {chatInput:"hello"} to chat_url -> 200 with a non-empty "output" (one real model call)
  tap      00-hq/site/tests/test_tap_sweep.py <url> (390 px, light + dark) exits 0
Results for targets not run this time are kept with their own time; the file's "at" is the oldest kept result,
so check.py's age rule can never be fooled by a partial run. Exit 1 if any target run now failed.
Read-only GETs plus one chat POST; never deploys or changes anything.
"""
import argparse, json, os, subprocess, sys, urllib.error, urllib.request
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGETS = os.path.join(ROOT, "00-hq/launch/smoke-targets.json")
OUT = os.path.join(ROOT, "00-hq/launch/smoke-results.json")
TAP = os.path.join(ROOT, "00-hq/site/tests/test_tap_sweep.py")
UA = {"User-Agent": "kalpa-smoke/1 (+our own site)"}


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch(url, data=None, timeout=20):
    """-> (status, lower-case headers, body text). Never raises on HTTP errors."""
    hdr = dict(UA, **({"Content-Type": "application/json"} if data else {}))
    req = urllib.request.Request(url, data=data, headers=hdr, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read(300_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read(20_000).decode("utf-8", "replace")


def check_page(t, ctx):
    s, h, body = ctx["fetch"](t["url"])
    ctx["home"] = (s, h)
    if s != 200:
        return False, f"status {s}"
    if "<html" not in body[:2000].lower():
        return False, "not an HTML page"
    return True, "200 HTML"


def check_headers(t, ctx):
    s, h = ctx.get("home") or ctx["fetch"](t["url"])[:2]
    csp = h.get("content-security-policy", "")
    need = {
        "HSTS": "max-age=" in h.get("strict-transport-security", ""),
        "nosniff": h.get("x-content-type-options", "").lower() == "nosniff",
        "clickjacking": "frame-ancestors" in csp or h.get("x-frame-options", "").upper() in ("DENY", "SAMEORIGIN"),
        "CSP": bool(csp),
        "Referrer-Policy": bool(h.get("referrer-policy")),
        "Permissions-Policy": bool(h.get("permissions-policy")),
    }
    missing = [k for k, ok in need.items() if not ok]
    return (not missing), ("6 headers OK" if not missing else "missing " + ", ".join(missing))


def check_chat(t, ctx):
    try:
        s, _, body = ctx["fetch"](t["chat_url"], json.dumps({"chatInput": "hello", "sessionId": "smoke"}).encode(), 45)
    except (OSError, ValueError) as e:
        return False, f"chat error {type(e).__name__}"
    try:
        out = str(json.loads(body).get("output") or "").strip()
    except (ValueError, AttributeError):
        out = ""
    if s == 200 and out:
        return True, f"answered ({len(out)} chars)"
    return False, f"chat status {s}" + ("" if out else ", empty answer")


def check_tap(t, ctx):
    try:
        r = ctx["run"]([sys.executable, TAP, t["url"]], capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return False, "tap sweep timed out"
    last = (r.stdout.strip().splitlines() or ["no output"])[-1][:160]
    return r.returncode == 0, last


CHECKS = {"page": check_page, "headers": check_headers, "chat": check_chat, "tap": check_tap}


def run_target(name, t, fetch_fn=fetch, run_fn=subprocess.run):
    ctx, steps = {"fetch": fetch_fn, "run": run_fn}, {}
    for c in t.get("checks", ["page"]):
        try:
            ok, detail = CHECKS[c](t, ctx)
        except (OSError, ValueError, KeyError) as e:   # DNS, timeout, refused, bad config
            ok, detail = False, f"{type(e).__name__}: {str(e)[:100]}"
        steps[c] = {"ok": ok, "detail": detail}
        if c == "page" and not ok:   # site down: later checks would only repeat the same failure
            break
    bad = [f"{c}: {s['detail']}" for c, s in steps.items() if not s["ok"]]
    return {"name": name, "url": t["url"], "at": now_iso(), "ok": not bad,
            "detail": "; ".join(bad) if bad else ", ".join(steps), "steps": steps}


def merge(old, new_results):
    keep = {r["name"]: r for r in (old or {}).get("results", []) if isinstance(r, dict) and r.get("at")}
    keep.update({r["name"]: r for r in new_results})
    results = sorted(keep.values(), key=lambda r: r["name"])
    return {"at": min(r["at"] for r in results), "results": results}


def main(argv=None, fetch_fn=fetch, run_fn=subprocess.run):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", help="target name (repeatable)")
    ap.add_argument("--targets", default=TARGETS)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    with open(a.targets) as f:
        targets = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    unknown = [n for n in (a.only or []) if n not in targets]
    if unknown:
        sys.exit(f"unknown target(s): {', '.join(unknown)}; known: {', '.join(targets)}")
    names = a.only or [n for n, t in targets.items() if t.get("url")]
    results = [run_target(n, targets[n], fetch_fn, run_fn) for n in names]
    old = None
    if os.path.exists(a.out):
        try:
            with open(a.out) as f:
                old = json.load(f)
        except ValueError:
            old = None
    data = merge(old, results)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, a.out)
    for r in results:
        print(f"{'PASS' if r['ok'] else 'FAIL'} {r['name']} · {r['detail']}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

"""P1 AI Cost Audit: usage CSV -> markdown audit report. Offline, no network.

    python3 audit.py usage.csv --client "Acme" [--currency USD] [--out report.md]

CSV columns (header row; lines starting with '#' are comments):
  required  date, feature, model, input_tokens, output_tokens, cost
  optional  provider, requests, cached_tokens, prompt_hash, status, is_retry
`cost` is what the client was billed for that row, in --currency. It is the truth for spend.
Savings re-price each row with one change through the Ledger Peaks engine (06-finops/src/price,
genai-prices data) and apply that *ratio* to the billed cost, so the currency does not matter.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from ingest.schema import UsageRecord  # noqa: E402
from price.engine import usd_cost  # noqa: E402
from xray.report import CACHE_MIN_AVG_INPUT, CACHE_PROVIDERS, DOWNGRADE, SHORT_OUTPUT  # noqa: E402

REQUIRED = ("date", "feature", "model", "input_tokens", "output_tokens", "cost")
DAYS_PER_MONTH = Decimal("30.4375")
# Every number the estimate rests on. All of them are printed in the report.
ASSUME = {
    "short_prompt_tokens": 1000,       # avg input at or below this = "short prompt"
    "short_output_tokens": SHORT_OUTPUT,
    "cache_min_avg_input": CACHE_MIN_AVG_INPUT,
    "cache_reusable_share": Decimal("0.5"),   # half of a long input is a fixed system prompt/context
    "repeat_cache_hit": Decimal("0.9"),       # an exact-match response cache serves 90% of repeats
    "retry_avoidable": Decimal("0.8"),        # 80% of failed/retried calls are avoidable
    "conservative_factor": Decimal("0.5"),    # low end of the range = half the estimate
}
FAILED = {"error", "failed", "fail", "retry", "timeout", "rate_limited", "429", "500", "503"}
TRUE = {"1", "true", "yes", "y"}


@dataclass
class Row:
    n: int
    day: date
    feature: str
    model: str
    provider: str
    inp: int
    out: int
    cost: Decimal
    requests: int = 1
    cached: int = 0
    prompt_hash: str = ""
    failed: bool = False


def guess_provider(model: str) -> str:
    m = model.lower()
    if m.startswith(("gpt", "o1", "o3", "o4", "text-embedding", "chatgpt")):
        return "openai"
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("gemini"):
        return "google"
    return ""


def load(path: str | Path) -> tuple[list[Row], list[str], bool]:
    """Rows, problems (one line each), and whether the file says it is synthetic."""
    text = Path(path).read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    synthetic = any(ln.lstrip().startswith("#") and "SYNTHETIC" in ln.upper() for ln in lines)
    body = "\n".join(ln for ln in lines if not ln.lstrip().startswith("#"))
    reader = csv.DictReader(io.StringIO(body))
    cols = {c.strip().lower() for c in (reader.fieldnames or [])}
    missing = [c for c in REQUIRED if c not in cols]
    if missing:
        raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")
    rows, problems = [], []
    for i, raw in enumerate(reader, start=2):
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        try:
            inp, out = int(r["input_tokens"] or 0), int(r["output_tokens"] or 0)
            cost = Decimal(r["cost"] or "0")
            req = int(r.get("requests") or 1)
            cached = int(r.get("cached_tokens") or 0)
            if min(inp, out, req, cached) < 0 or cost < 0 or cached > inp:
                raise ValueError("negative value or cached_tokens > input_tokens")
            day = date.fromisoformat(r["date"][:10])
        except (ValueError, InvalidOperation) as e:
            problems.append(f"row {i}: skipped ({e})")
            continue
        model = r["model"]
        if not model:
            problems.append(f"row {i}: skipped (no model)")
            continue
        status = r.get("status", "").lower()
        rows.append(Row(i, day, r["feature"] or "(untagged)", model,
                        (r.get("provider") or guess_provider(model)).lower(), inp, out, cost, req, cached,
                        r.get("prompt_hash", ""), status in FAILED or r.get("is_retry", "").lower() in TRUE))
    return rows, problems, synthetic


def _ratio(row: Row, **change) -> Decimal | None:
    """new/old price of this row after one change, from the Ledger Peaks engine; None if unpriceable."""
    base = dict(ts=row.day.isoformat(), provider=row.provider, model=row.model, input_tokens=row.inp,
                output_tokens=row.out, cache_read_tokens=row.cached, requests=row.requests)
    old, _, _ = usd_cost(UsageRecord(**base))
    new, _, _ = usd_cost(UsageRecord(**{**base, **change}))
    if old is None or new is None or old <= 0:
        return None
    return min(new / old, Decimal(1))


def _avg(rows, attr) -> int:
    calls = sum(r.requests for r in rows) or 1
    return sum(getattr(r, attr) for r in rows) // calls


def analyse(rows: list[Row]) -> dict:
    total = sum((r.cost for r in rows), Decimal(0))
    days = ((max(r.day for r in rows) - min(r.day for r in rows)).days + 1) if rows else 1
    by_model, by_feature = defaultdict(Decimal), defaultdict(Decimal)
    calls_model, calls_feature = defaultdict(int), defaultdict(int)
    for r in rows:
        by_model[r.model] += r.cost
        by_feature[r.feature] += r.cost
        calls_model[r.model] += r.requests
        calls_feature[r.feature] += r.requests

    signals, unpriced = [], set()
    removed: dict[int, Decimal] = {}          # row -> share of its cost saved (retries, repeats)
    frac = defaultdict(list)                  # row -> list of saving fractions (downgrade, cache)

    # 1. retries / failed calls that were still billed
    failed = [r for r in rows if r.failed]
    if not any(r.failed for r in rows):       # no status column: zero-output calls are a proxy
        failed = [r for r in rows if r.out == 0 and r.inp > 0]
        how = "calls billed with 0 output tokens (proxy: no status column)"
    else:
        how = "calls marked error/retry in the status or is_retry column"
    if failed:
        for r in failed:
            removed[r.n] = ASSUME["retry_avoidable"]
        cost = sum((r.cost for r in failed), Decimal(0))
        signals.append({"kind": "retries", "where": "all features", "rows": len(failed), "cost": cost,
                        "saving": cost * ASSUME["retry_avoidable"],
                        "title": "Failed or retried calls you still paid for",
                        "fix": "add timeouts, capped retries with backoff, and validate inputs before calling",
                        "evidence": f"{sum(r.requests for r in failed):,} {how}"})

    # 2. repeat prompts (exact same prompt sent again)
    hashed = [r for r in rows if r.prompt_hash and r.n not in removed]
    seen, groups = set(), defaultdict(list)
    for r in sorted(hashed, key=lambda x: (x.day, x.n)):
        key = (r.feature, r.prompt_hash)
        if key in seen:
            groups[r.feature].append(r)
        seen.add(key)
    for feat, reps in groups.items():
        for r in reps:
            removed[r.n] = ASSUME["repeat_cache_hit"]
        cost = sum((r.cost for r in reps), Decimal(0))
        signals.append({"kind": "repeats", "where": feat, "rows": len(reps), "cost": cost,
                        "saving": cost * ASSUME["repeat_cache_hit"],
                        "title": f"Same prompt sent again in {feat}",
                        "fix": "add an exact-match response cache (key = prompt hash, short expiry)",
                        "evidence": f"{sum(r.requests for r in reps):,} calls repeat an earlier prompt_hash"})
    if not any(r.prompt_hash for r in rows):
        signals.append({"kind": "repeats-unknown", "where": "all features", "rows": 0, "cost": Decimal(0),
                        "saving": Decimal(0), "title": "Repeat prompts: not measurable from this file",
                        "fix": "ask the client to log a prompt_hash column for 7 days",
                        "evidence": "no prompt_hash column (not counted in savings)"})

    # 3 + 4. per feature and model: big model on short prompts; long prompts without caching
    grp = defaultdict(list)
    for r in rows:
        if r.n not in removed:
            grp[(r.feature, r.model)].append(r)
    for (feat, model), rs in grp.items():
        cost = sum((r.cost for r in rs), Decimal(0))
        ain, aout = _avg(rs, "inp"), _avg(rs, "out")
        if model in DOWNGRADE and ain <= ASSUME["short_prompt_tokens"] and aout <= ASSUME["short_output_tokens"]:
            small, saved = DOWNGRADE[model], Decimal(0)
            for r in rs:
                q = _ratio(r, model=small)
                if q is None:
                    unpriced.add(model)
                    continue
                frac[r.n].append(1 - q)
                saved += r.cost * (1 - q)
            if saved > 0:
                signals.append({"kind": "downgrade", "where": feat, "rows": len(rs), "cost": cost, "saving": saved,
                                "title": f"{model} used for short prompts in {feat}",
                                "fix": f"test {small} on 200 real cases; switch if quality holds",
                                "evidence": f"avg {ain} input / {aout} output tokens per call"})
        cached = sum(r.cached for r in rs)
        inp = sum(r.inp for r in rs)
        if rs[0].provider in CACHE_PROVIDERS and ain >= ASSUME["cache_min_avg_input"] \
                and cached < inp * ASSUME["cache_reusable_share"]:
            saved = Decimal(0)
            for r in rs:
                q = _ratio(r, cache_read_tokens=max(r.cached, int(r.inp * ASSUME["cache_reusable_share"])))
                if q is None:
                    unpriced.add(model)
                    continue
                frac[r.n].append(1 - q)
                saved += r.cost * (1 - q)
            if saved > 0:
                signals.append({"kind": "cache", "where": feat, "rows": len(rs), "cost": cost, "saving": saved,
                                "title": f"Long {model} prompts in {feat} with little prompt caching",
                                "fix": "put the fixed system prompt/context first and turn on prompt caching",
                                "evidence": f"avg {ain:,} input tokens; {cached * 100 // max(inp, 1)}% cached today"})

    # combined saving: no double counting (fractions compound on what is left of each row)
    combined = Decimal(0)
    for r in rows:
        if r.n in removed:
            combined += r.cost * removed[r.n]
        elif frac[r.n]:
            left = Decimal(1)
            for f in frac[r.n]:
                left *= 1 - f
            combined += r.cost * (1 - left)
    per_month = DAYS_PER_MONTH / days
    for s in signals:
        s["saving_month"] = s["saving"] * per_month
    signals.sort(key=lambda s: s["saving"], reverse=True)
    return {"total": total, "days": days, "rows": len(rows), "per_month": per_month,
            "by_model": by_model, "by_feature": by_feature, "calls_model": calls_model,
            "calls_feature": calls_feature, "signals": signals, "combined": combined,
            "unpriced": sorted(unpriced)}


def _m(x: Decimal, cur: str) -> str:
    return f"{cur} {x:,.2f}"


def _table(spend: dict, calls: dict, total: Decimal, cur: str, head: str) -> list[str]:
    out = [f"| {head} | Calls | Spend | Share |", "|---|---:|---:|---:|"]
    for k, v in sorted(spend.items(), key=lambda kv: kv[1], reverse=True):
        out.append(f"| {k} | {calls[k]:,} | {_m(v, cur)} | {v * 100 / total if total else 0:.1f}% |")
    return out


def render(a: dict, *, client: str, currency: str = "USD", synthetic: bool = False,
           problems: list[str] | None = None) -> str:
    cur, pm = currency, a["per_month"]
    est = a["combined"] * pm
    low = est * ASSUME["conservative_factor"]
    L = [f"# AI Cost Audit: {client}", ""]
    if synthetic:
        L += ["> **SYNTHETIC DATA.** This report was made from made-up sample data, not a real client.", ""]
    L += ["Prepared by Kalpa Labs (AI FinOps + AI Guardrails consulting). Not a certification. "
          "Savings are estimates, not guarantees.", "",
          "## 1. Summary", "",
          f"- Data: {a['rows']:,} rows over {a['days']} days.",
          f"- Spend in this data: **{_m(a['total'], cur)}**; monthly run-rate **{_m(a['total'] * pm, cur)}**.",
          f"- Estimated saving: **{_m(low, cur)} to {_m(est, cur)} per month** "
          f"({(est * 100 / (a['total'] * pm)) if a['total'] else 0:.0f}% of spend at the high end).",
          f"- Waste signals found: {sum(1 for s in a['signals'] if s['saving'] > 0)}.", "",
          "## 2. Spend by model", ""]
    L += _table(a["by_model"], a["calls_model"], a["total"], cur, "Model")
    L += ["", "## 3. Spend by feature", ""]
    L += _table(a["by_feature"], a["calls_feature"], a["total"], cur, "Feature")
    L += ["", "## 4. Top waste signals", "",
          "| # | Signal | Evidence | Fix | Saving / month |", "|---|---|---|---|---:|"]
    top = a["signals"][:10]
    for i, s in enumerate(top, 1):
        L.append(f"| {i} | {s['title']} | {s['evidence']} | {s['fix']} | {_m(s['saving_month'], cur)} |")
    if not top:
        L.append("| - | No waste signals found | - | - | - |")
    L += ["", "Each line is priced on its own. The total in section 1 is lower than their sum because "
          "it never saves the same money twice.", "",
          "## 5. How the saving was estimated", "",
          "1. Billed `cost` from the client's file is the spend. We never invent spend.",
          f"2. **Retries:** {ASSUME['retry_avoidable'] * 100:.0f}% of the cost of failed or retried calls is "
          "treated as avoidable.",
          f"3. **Repeat prompts:** calls whose `prompt_hash` repeats an earlier call in the same feature; an "
          f"exact-match cache is assumed to serve {ASSUME['repeat_cache_hit'] * 100:.0f}% of them.",
          f"4. **Big model on short prompts:** feature+model groups averaging <= {ASSUME['short_prompt_tokens']} "
          f"input and <= {ASSUME['short_output_tokens']} output tokens, re-priced on the same provider's "
          "smaller model.",
          f"5. **No prompt caching:** groups averaging >= {ASSUME['cache_min_avg_input']} input tokens with under "
          f"{ASSUME['cache_reusable_share'] * 100:.0f}% cached, re-priced with "
          f"{ASSUME['cache_reusable_share'] * 100:.0f}% of input as cache reads.",
          "6. Re-pricing uses public list prices (genai-prices data in the Ledger Peaks engine). Only the "
          "*ratio* new/old price is applied to the billed cost.",
          "7. Per row, savings compound on what is left (never above 100%). Monthly = saving / days in data "
          f"x 30.44. Low end = {ASSUME['conservative_factor'] * 100:.0f}% of the estimate.",
          "8. Test every change on real traffic before switching. Quality comes first.", "",
          "## 6. Data notes", ""]
    notes = list(problems or [])
    if a["unpriced"]:
        notes.append("no list price for: " + ", ".join(a["unpriced"]) + " (their savings are not counted)")
    L += [f"- {n}" for n in notes] or ["- No problems found in the file."]
    L += ["", "---", "Next step: 30-minute review call to agree which fixes to test first."]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P1 AI Cost Audit report from a usage CSV")
    ap.add_argument("csv")
    ap.add_argument("--client", default="Client")
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    try:
        rows, problems, synth = load(a.csv)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not rows:
        print("error: no usable rows", file=sys.stderr)
        return 2
    md = render(analyse(rows), client=a.client, currency=a.currency, synthetic=synth, problems=problems)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

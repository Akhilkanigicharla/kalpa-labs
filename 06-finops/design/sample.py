"""Synthetic data for the Ledger Peaks mockups (A12).

Every rupee on the landing, dashboard and X-ray mockups comes from here, and every
figure here comes from the real price engine (src/price) and the cached FBIL rate.
Nothing is real: "Chaiwala AI" is a made-up Hyderabad support-bot startup.

    python3 design/sample.py          # writes design/sample.json and injects it into the 3 pages
    python3 design/sample.py --check  # exit 1 if the pages are out of date
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
os.environ.setdefault("LP_ALLOW_DEV_SALT", "1")   # synthetic ids only; real runs need LP_HASH_SALT

from ingest.schema import UsageRecord, hash_id  # noqa: E402
from price.engine import price_all, price_record  # noqa: E402
from price.fx import FxTable  # noqa: E402

PAGES = ("landing.html", "dashboard.html", "xray.html")
DAYS = [f"2026-10-{d}" for d in range(12, 19)]        # one week covered by the cached FBIL rate
COMPANY = "Chaiwala AI (sample)"

# feature -> (provider, model, input, output, cache_read share of input) per call
FEATURES = {
    "support_reply": ("anthropic", "claude-sonnet-4-5", 3200, 420, 0.10),
    "rag_search":    ("google", "gemini-2.5-flash", 6500, 380, 0.00),
    "summarise":     ("openai", "gpt-4o-mini", 4200, 300, 0.00),
    "classify":      ("openai", "gpt-4o", 900, 15, 0.00),
    "telugu_voice":  ("sarvam", "sarvam-m", 1500, 200, 0.00),   # not in genai-prices -> "unpriced"
}
# customer -> (calls per day per feature, monthly plan revenue in Rs)
CUSTOMERS = {
    "Biryani Bazaar":   ({"support_reply": 900, "rag_search": 700, "summarise": 300, "classify": 2500, "telugu_voice": 120}, 59999),
    "Kirana Cloud":     ({"support_reply": 260, "rag_search": 400, "summarise": 150, "classify": 900, "telugu_voice": 40}, 34999),
    "MedPlus Lite":     ({"support_reply": 120, "rag_search": 200, "summarise": 60, "classify": 400}, 19999),
    "Auto Adda":        ({"support_reply": 70, "rag_search": 90, "summarise": 40, "classify": 300}, 9999),
    "Saree Studio":     ({"support_reply": 30, "rag_search": 50, "summarise": 20, "classify": 150, "telugu_voice": 30}, 4999),
    "Tiffin Tracker":   ({"support_reply": 15, "rag_search": 20, "summarise": 10, "classify": 80}, 2999),
}
WEEKDAY_FACTOR = [1.0, 1.05, 1.1, 1.0, 1.15, 0.8, 0.7]    # Mon 12 Oct ... Sun 18 Oct
WEEKS_PER_MONTH = Decimal("4.345")                        # 365.25 / 12 / 7


def records() -> list[UsageRecord]:
    out, row = [], 0
    for name, (calls, _) in CUSTOMERS.items():
        cid = hash_id(name)
        for di, day in enumerate(DAYS):
            for feat, n in calls.items():
                prov, model, inp, outp, cache = FEATURES[feat]
                req = round(n * WEEKDAY_FACTOR[di])
                row += 1
                out.append(UsageRecord(ts=day, provider=prov, model=model, input_tokens=inp * req,
                                       output_tokens=outp * req, cache_read_tokens=int(inp * req * cache),
                                       requests=req, customer=cid, feature=feat, source="generic",
                                       source_row=row))
    return out


def _paise(recs, fx) -> int:
    return sum(p.paise for p in (price_record(r, fx) for r in recs) if p.paise)


def savings(recs, fx) -> list[dict]:
    """Three estimates, each re-priced with the same engine. Assumptions are stated, never hidden."""
    by = defaultdict(list)
    for r in recs:
        by[r.feature].append(r)
    ideas, pairs = [], []
    # 1. prompt caching on support_reply: assume 70% of input is a repeated system prompt + FAQ block
    cur = by["support_reply"]
    new = [replace(r, cache_read_tokens=int(r.input_tokens * 0.70)) for r in cur]
    pairs.append((cur, new))
    ideas.append({"id": "cache", "title": "Cache the repeated support prompt",
                  "feature": "support_reply", "now": _paise(cur, fx), "after": _paise(new, fx),
                  "assumption": "70% of each support_reply input is the same system prompt and FAQ block "
                                "(today 10% is cached); Anthropic charges 10% for cache reads"})
    # 2. smaller model for classify
    cur = by["classify"]
    new = [replace(r, model="gpt-4o-mini") for r in cur]
    pairs.append((cur, new))
    ideas.append({"id": "downgrade", "title": "Classify with gpt-4o-mini instead of gpt-4o",
                  "feature": "classify", "now": _paise(cur, fx), "after": _paise(new, fx),
                  "assumption": "a 1-word label task; test 200 real tickets first and keep gpt-4o "
                                "if accuracy drops more than 2 points"})
    # 3. batch for summarise (summaries are read next morning)
    cur = by["summarise"]
    new = [replace(r, batch=True) for r in cur]
    pairs.append((cur, new))
    ideas.append({"id": "batch", "title": "Run nightly summaries through the Batch API",
                  "feature": "summarise", "now": _paise(cur, fx), "after": _paise(new, fx),
                  "assumption": "summaries can wait up to 24 h; OpenAI Batch API is 50% off"})
    for i, (cur_, new_) in zip(ideas, pairs):
        i["saved_week"] = i["now"] - i["after"]
        per = defaultdict(int)
        for r0, r1 in zip(cur_, new_):
            per[r0.customer] += _paise([r0], fx) - _paise([r1], fx)
        i["by_customer_week"] = dict(per)
        i["saved_month"] = int(Decimal(i["saved_week"]) * WEEKS_PER_MONTH)
    return sorted(ideas, key=lambda i: -i["saved_week"])


DPDP = [  # 20 readiness questions (our own wording; not legal advice). True = in place for the sample company
    ("Do you have a written list of every AI feature that touches personal data?", True),
    ("Is the purpose of each AI feature written in your privacy notice?", True),
    ("Does the notice name the AI providers you send data to?", False),
    ("Is there a consent or other lawful basis recorded for each purpose?", True),
    ("Can a user withdraw consent as easily as they gave it?", False),
    ("Do you strip phone numbers, Aadhaar and PAN before prompts leave India?", False),
    ("Do you know which provider regions (US, EU, India) receive your data?", True),
    ("Do provider contracts say they won't train on your data?", True),
    ("Are prompts and outputs deleted on a fixed schedule?", False),
    ("Is the retention period written down per feature?", False),
    ("Can you find and delete one user's data across AI logs on request?", False),
    ("Is there a named person who answers data requests (grievance officer)?", True),
    ("Do you log who accessed AI logs and when?", True),
    ("Is access to raw prompts limited to named staff?", True),
    ("Do you have a breach plan that covers your AI provider leaking data?", False),
    ("Could you tell the Data Protection Board and users within 72 hours?", False),
    ("Do you tell users when they are talking to an AI, not a person?", True),
    ("Are children's accounts blocked or handled with parental consent?", True),
    ("Have you checked whether you could be a Significant Data Fiduciary?", True),
    ("Is this checklist reviewed at least once a year?", True),
]


def build() -> dict:
    fx = FxTable.load()
    recs = records()
    _, s = price_all(recs, fx)
    labels = {hash_id(n): n for n in CUSTOMERS}
    rate = fx.for_date(DAYS[-1])
    by_day = defaultdict(int)
    by_cf = defaultdict(lambda: defaultdict(int))
    calls = defaultdict(int)
    for r in recs:
        p = price_record(r, fx)
        calls[labels[r.customer]] += r.requests
        if p.paise:
            by_day[r.ts] += p.paise
            by_cf[labels[r.customer]][r.feature] += p.paise
    customers = []
    for cid, paise in sorted(s.by_customer.items(), key=lambda kv: -kv[1]):
        name = labels[cid]
        month = int(Decimal(paise) * WEEKS_PER_MONTH)
        rev = CUSTOMERS[name][1] * 100
        customers.append({"name": name, "id": cid, "week": paise, "month": month, "revenue_month": rev,
                          "margin_pct": round((rev - month) * 100 / rev, 1), "calls": calls[name],
                          "by_feature": dict(by_cf[name])})
    ideas = savings(recs, fx)
    top = ideas[0]
    for c in customers:
        after = c["month"] - int(Decimal(top["by_customer_week"].get(c["id"], 0)) * WEEKS_PER_MONTH)
        c["month_after_top_idea"] = after
        c["margin_after_top_idea_pct"] = round((c["revenue_month"] - after) * 100 / c["revenue_month"], 1)
    unpriced_calls = sum(r.requests for r in recs if r.model == "sarvam-m")
    data = {
        "company": COMPANY, "period": {"from": DAYS[0], "to": DAYS[-1], "days": len(DAYS)},
        "fx": {"date": rate.date, "inr_per_usd": str(rate.inr_per_usd), "source": rate.source},
        "total_week": s.priced_paise, "total_month": int(Decimal(s.priced_paise) * WEEKS_PER_MONTH),
        "rows": s.rows, "calls": sum(r.requests for r in recs),
        "by_model": dict(sorted(s.by_model.items(), key=lambda kv: -kv[1])),
        "by_feature": dict(sorted(s.by_feature.items(), key=lambda kv: -kv[1])),
        "by_day": dict(sorted(by_day.items())), "customers": customers,
        "unpriced": {"models": s.unpriced_models and sorted(s.unpriced_models), "rows": s.unpriced_rows,
                     "tokens": s.unpriced_tokens, "calls": unpriced_calls},
        "savings": ideas, "savings_month": sum(i["saved_month"] for i in ideas),
        "gst_rcm_month": int(Decimal(s.priced_paise) * WEEKS_PER_MONTH * Decimal("0.18")),
        "dpdp": {"score": sum(1 for _, ok in DPDP if ok), "of": len(DPDP),
                 "questions": [{"q": q, "ok": ok} for q, ok in DPDP]},
        "weeks_per_month": str(WEEKS_PER_MONTH),
    }
    return data


DATA_RE = re.compile(r'(<script id="lp-data" type="application/json">)(.*?)(</script>)', re.S)


def inject(data: dict, check: bool = False) -> list[str]:
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    stale = []
    for name in PAGES:
        p = HERE / name
        html = p.read_text()
        if not DATA_RE.search(html):
            raise SystemExit(f"{name}: no <script id=\"lp-data\"> block")
        new = DATA_RE.sub(lambda m: m.group(1) + blob + m.group(3), html)
        if new != html:
            stale.append(name)
            if not check:
                p.write_text(new)
    return stale


def main(argv: list[str]) -> int:
    data = build()
    check = "--check" in argv
    if not check:
        (HERE / "sample.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    stale = inject(data, check)
    if check and stale:
        print("out of date: " + ", ".join(stale) + " (run python3 design/sample.py)")
        return 1
    print(f"total ₹{data['total_week'] / 100:,.2f} a week, savings ₹{data['savings_month'] / 100:,.0f} a month, "
          f"DPDP {data['dpdp']['score']}/{data['dpdp']['of']}" + (" (pages up to date)" if check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

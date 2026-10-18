"""Build the X-ray data from usage records. Every rupee comes from src/price (genai-prices + FBIL rate).

Savings are three generic rules, each re-pricing the real rows with one change applied:
  cache      a feature with long inputs and little caching: assume half the input is a reusable prefix
  downgrade  a feature with short outputs on a big model: same provider's smaller model
  batch      a feature on a provider with a Batch API (50% off): only if results can wait 24 h
They are estimates; each carries its assumption in plain words.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from ingest.schema import hash_id
from price.engine import BATCH_DISCOUNT_PROVIDERS, price_all, price_record
from price.fx import FxTable

from . import dpdp

DAYS_PER_MONTH = Decimal("30.4375")          # 365.25 / 12
CACHE_PROVIDERS = {"anthropic", "openai", "google"}
CACHE_MIN_AVG_INPUT = 1024                   # providers only cache prefixes of ~1k+ tokens
CACHE_ASSUMED_SHARE = Decimal("0.5")
SHORT_OUTPUT = 100                           # avg output tokens per call that suggests a simple task
OFFLINE = re.compile(r"summar|report|digest|nightly|batch|tag|classif|label|extract|embed|enrich|translat|index", re.I)
LIVE = re.compile(r"chat|reply|support|voice|live|agent|assist|search|realtime|call", re.I)
DOWNGRADE = {                                # same provider, smaller sibling
    "gpt-4o": "gpt-4o-mini", "gpt-4.1": "gpt-4.1-mini", "gpt-4.1-mini": "gpt-4.1-nano",
    "gpt-5": "gpt-5-mini", "gpt-5-mini": "gpt-5-nano", "o3": "o4-mini",
    "claude-opus-4-1": "claude-sonnet-4-5", "claude-opus-4": "claude-sonnet-4",
    "claude-sonnet-4-5": "claude-haiku-4-5", "claude-sonnet-4": "claude-3-5-haiku",
    "gemini-2.5-pro": "gemini-2.5-flash", "gemini-2.5-flash": "gemini-2.5-flash-lite",
}


def _paise(recs, fx) -> int:
    return sum(p.paise for p in (price_record(r, fx) for r in recs) if p.paise)


def _by_feature(recs) -> dict[str, list]:
    out = defaultdict(list)
    for r in recs:
        out[r.feature or "(untagged)"].append(r)
    return out


def _idea(kind, feature, cur, new, fx, title, assumption) -> dict | None:
    now, after = _paise(cur, fx), _paise(new, fx)
    if after >= now:
        return None
    per = defaultdict(int)
    for r0, r1 in zip(cur, new):
        per[r0.customer or "(unknown)"] += _paise([r0], fx) - _paise([r1], fx)
    return {"id": kind, "title": title, "feature": feature, "now": now, "after": after,
            "saved_week": now - after, "by_customer_week": dict(per), "assumption": assumption}


def savings(recs, fx) -> list[dict]:
    feats = _by_feature(recs)
    found: list[dict] = []

    def keep(i):
        if i:
            found.append(i)

    for f, rows in feats.items():
        calls = sum(r.requests for r in rows) or 1
        inp = sum(r.input_tokens for r in rows)
        out = sum(r.output_tokens for r in rows)
        cached = sum(r.cache_read_tokens for r in rows)
        # cache
        cands = [r for r in rows if r.provider in CACHE_PROVIDERS]
        if cands and inp / calls >= CACHE_MIN_AVG_INPUT and cached < inp * CACHE_ASSUMED_SHARE:
            new = [replace(r, cache_read_tokens=max(r.cache_read_tokens,
                                                    int(r.input_tokens * CACHE_ASSUMED_SHARE))) for r in cands]
            keep(_idea("cache", f, cands, new, fx, f"Cache the repeated part of {f} prompts",
                       f"half of each {f} input (avg {inp // calls:,} tokens) is the same system prompt or "
                       f"context block; today {cached * 100 // max(inp, 1)}% is cached. Check your prompt "
                       "template first."))
        # downgrade
        cands = [r for r in rows if r.model in DOWNGRADE]
        if cands and out / calls <= SHORT_OUTPUT:
            new = [replace(r, model=DOWNGRADE[r.model]) for r in cands]
            models = ", ".join(sorted({r.model for r in cands}))
            smaller = ", ".join(sorted({DOWNGRADE[r.model] for r in cands}))
            keep(_idea("downgrade", f, cands, new, fx, f"Run {f} on {smaller} instead of {models}",
                       f"outputs average {out // calls} tokens, a sign of a simple task; test 200 real "
                       "cases first and keep the bigger model if quality drops"))
        # batch
        cands = [r for r in rows if r.provider in BATCH_DISCOUNT_PROVIDERS and not r.batch]
        if cands and OFFLINE.search(f) and not LIVE.search(f):
            new = [replace(r, batch=True) for r in cands]
            keep(_idea("batch", f, cands, new, fx, f"Send {f} through the Batch API",
                       f"{f} looks like background work, so results can wait up to 24 h; "
                       "the providers' Batch APIs are 50% off. Skip this if users wait for it"))
    # biggest first; one idea per rule and per feature, so savings never overlap or double count
    picked, rules, used = [], set(), set()
    for i in sorted(found, key=lambda i: -i["saved_week"]):
        if i["id"] not in rules and i["feature"] not in used:
            picked.append(i)
            rules.add(i["id"])
            used.add(i["feature"])
    return picked


def load_revenue(path: str | Path | None, salt: str | None = None) -> dict[str, tuple[str, int]]:
    """CSV with customer (raw id, hashed inside this process), name (optional), monthly_revenue_inr."""
    if path is None:
        return {}
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            raw = (row.get("customer") or "").strip()
            if not raw:
                continue
            cid = raw if raw.startswith("c_") and len(raw) == 18 else hash_id(raw, salt)
            rev = Decimal(str(row.get("monthly_revenue_inr") or "0").replace(",", ""))
            out[cid] = ((row.get("name") or raw).strip(), int(rev * 100))
    return out


def build(records: list, *, company: str, fx: FxTable | None = None, revenue: dict | None = None,
          dpdp_answers: list | None = None, synthetic: bool = False) -> dict:
    fx = fx or FxTable.load()
    revenue = revenue or {}
    _, s = price_all(records, fx)
    days = sorted({r.ts[:10] for r in records})
    if not days:
        raise ValueError("no usage rows to report on")
    span = (date.fromisoformat(days[-1]) - date.fromisoformat(days[0])).days + 1
    factor = DAYS_PER_MONTH / span
    month = lambda p: int(Decimal(p) * factor)  # noqa: E731

    by_day, calls = defaultdict(int), defaultdict(int)
    by_cf = defaultdict(lambda: defaultdict(int))
    for r in records:
        p = price_record(r, fx)
        cid = r.customer or "(unknown)"
        calls[cid] += r.requests
        if p.paise:
            by_day[r.ts[:10]] += p.paise
            by_cf[cid][r.feature or "(untagged)"] += p.paise
    ideas = savings(records, fx)
    for i in ideas:
        i["saved_month"] = month(i["saved_week"])
    top = ideas[0] if ideas else None
    customers = []
    for cid, paise in sorted(s.by_customer.items(), key=lambda kv: -kv[1]):
        name, rev = revenue.get(cid, (cid, None))
        m = month(paise)
        c = {"name": name, "id": cid, "week": paise, "month": m, "revenue_month": rev,
             "margin_pct": round((rev - m) * 100 / rev, 1) if rev else None, "calls": calls[cid],
             "by_feature": dict(by_cf[cid])}
        after = m - (month(top["by_customer_week"].get(cid, 0)) if top else 0)
        c["month_after_top_idea"] = after
        c["margin_after_top_idea_pct"] = round((rev - after) * 100 / rev, 1) if rev else None
        customers.append(c)
    rate = fx.for_date(days[-1])
    unpriced_calls = sum(r.requests for r in records
                         if price_record(r, fx).status == "unpriced")
    return {
        "company": company, "synthetic": synthetic,
        "period": {"from": days[0], "to": days[-1], "days": span, "year": days[-1][:4]},
        "fx": {"date": rate.date, "inr_per_usd": str(rate.inr_per_usd), "source": rate.source},
        "total_week": s.priced_paise,              # total for the whole period (name kept for the template)
        "total_month": month(s.priced_paise),
        "rows": s.rows, "calls": sum(r.requests for r in records),
        "by_model": dict(sorted(s.by_model.items(), key=lambda kv: -kv[1])),
        "by_feature": dict(sorted(s.by_feature.items(), key=lambda kv: -kv[1])),
        "by_day": dict(sorted(by_day.items())), "customers": customers,
        "unpriced": {"models": sorted(s.unpriced_models), "rows": s.unpriced_rows,
                     "tokens": s.unpriced_tokens, "calls": unpriced_calls},
        "savings": ideas[:3], "savings_month": sum(i["saved_month"] for i in ideas[:3]),
        "gst_rcm_month": int(month(s.priced_paise) * Decimal("0.18")),
        "dpdp": dpdp.section(dpdp_answers or [None] * len(dpdp.QUESTIONS)),
        "scale_note": f"{DAYS_PER_MONTH} / {span} days",
        "cross_check_flags": s.cross_check_flags,
    }

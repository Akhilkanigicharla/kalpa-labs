"""INR price engine (A27 = F-01 + F-02).

USD prices come from pydantic's `genai-prices` (MIT, ADOPT in a7/deep-scan-v2).
USD -> INR uses the cached FBIL reference rate in price/data/usd_inr.json (fx.py).
Money is returned in whole paise (int), rounded half-up once per row.

Rules learnt in Deep Scan v2 (see research/deep-scan-v2.md §4):
- Aggregated rows (OpenAI daily buckets) must be priced PER REQUEST and then
  multiplied: genai-prices applies long-context tiers per call, so pricing
  1.2M summed tokens as one call wrongly triggers the >200k tier (e.g. Claude
  Sonnet 4.5 input jumps from $3 to $6 per million).
- Unknown or retired models are never priced at Rs 0: they go to an
  "unpriced" bucket with their token counts so the X-ray shows them (F-02).
- Gateway cache hits (LiteLLM cache_hit) cost nothing at the provider.
- Batch rows get the providers' published 50% batch discount
  (OpenAI Batch API, Anthropic Message Batches, Gemini Batch Mode).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

from .fx import FxTable

BATCH_DISCOUNT_PROVIDERS = {"openai", "anthropic", "google"}
CROSS_CHECK_TOLERANCE = Decimal("0.005")   # 0.5% vs the cost the source reported


@dataclass
class Priced:
    status: str                      # "priced" | "unpriced" | "cache_hit"
    usd: Decimal | None
    paise: int | None
    fx_date: str | None = None
    inr_per_usd: Decimal | None = None
    matched_model: str | None = None
    note: str = ""
    reported_diff: Decimal | None = None   # (ours - reported) / reported


AGGREGATE_SOURCES = {"openai", "anthropic"}   # usage APIs that report daily buckets
SHORT_CALL_TOKENS = 100_000                   # assumed max input per call when counts are missing


def _calls(rec) -> tuple[int, str]:
    n = max(int(rec.requests or 0), 1)
    if rec.source in AGGREGATE_SOURCES and n == 1 and rec.input_tokens > 2 * SHORT_CALL_TOKENS:
        n = -(-rec.input_tokens // SHORT_CALL_TOKENS)
        return n, "request count missing: priced as calls of <=100k input (standard tier)"
    return n, ""


def usd_cost(rec) -> tuple[Decimal | None, str | None, str]:
    """USD cost of one UsageRecord, or (None, None, reason) when the model is unknown."""
    from genai_prices import Usage, calc_price
    n, note = _calls(rec)
    # split uncached input, cache reads, cache writes and output separately so every
    # per-call and remainder slice is self-consistent (cache never exceeds input)
    parts = {"unc": rec.input_tokens - rec.cache_read_tokens - rec.cache_write_tokens,
             "cr": rec.cache_read_tokens, "cw": rec.cache_write_tokens, "out": rec.output_tokens}
    if parts["unc"] < 0:
        return None, None, "bad usage: cache tokens exceed input tokens"

    def _slice(k: dict) -> dict:
        return {"input_tokens": k["unc"] + k["cr"] + k["cw"], "output_tokens": k["out"],
                "cache_read_tokens": k["cr"], "cache_write_tokens": k["cw"]}
    per = _slice({k: v // n for k, v in parts.items()})
    rem = _slice({k: v - (v // n) * n for k, v in parts.items()})

    def _price(u: dict):
        return calc_price(Usage(input_tokens=u["input_tokens"], output_tokens=u["output_tokens"],
                                cache_read_tokens=u["cache_read_tokens"] or None,
                                cache_write_tokens=u["cache_write_tokens"] or None),
                          model_ref=rec.model, provider_id=rec.provider or None)
    try:
        one = _price(per)
    except Exception as e:  # LookupError / ValueError from unknown model or provider
        return None, None, f"unknown model: {type(e).__name__}"
    usd = Decimal(str(one.total_price)) * n
    if any(rem.values()):  # tokens left over by integer division, priced like one more small call
        usd += Decimal(str(_price(rem).total_price))
    if rec.batch and rec.provider in BATCH_DISCOUNT_PROVIDERS:
        usd = usd / 2
        note = "; ".join(x for x in (note, "batch 50% discount") if x)
    return usd, getattr(one.model, "id", rec.model), note


def to_paise(usd: Decimal, inr_per_usd: Decimal) -> int:
    return int((usd * inr_per_usd * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def price_record(rec, fx: FxTable) -> Priced:
    if rec.served_from_cache:
        return Priced("cache_hit", Decimal(0), 0, note="gateway cache hit: no provider bill")
    usd, matched, note = usd_cost(rec)
    if usd is None:
        return Priced("unpriced", None, None, note=note)
    rate = fx.for_date(rec.ts[:10])
    p = Priced("priced", usd, to_paise(usd, rate.inr_per_usd), rate.date, rate.inr_per_usd, matched, note)
    if rec.reported_cost_usd:
        rep = Decimal(rec.reported_cost_usd)
        if rep > 0:
            p.reported_diff = (usd - rep) / rep
    return p


@dataclass
class Summary:
    rows: int = 0
    priced_paise: int = 0
    priced_rows: int = 0
    cache_hit_rows: int = 0
    unpriced_rows: int = 0
    unpriced_tokens: int = 0
    unpriced_models: set = field(default_factory=set)
    by_model: dict = field(default_factory=lambda: defaultdict(int))
    by_feature: dict = field(default_factory=lambda: defaultdict(int))
    by_customer: dict = field(default_factory=lambda: defaultdict(int))
    cross_check_flags: list = field(default_factory=list)

    @property
    def rupees(self) -> str:
        return f"₹{self.priced_paise / 100:,.2f}"

    def to_dict(self) -> dict:
        return {"rows": self.rows, "priced_paise": self.priced_paise, "priced_rows": self.priced_rows,
                "cache_hit_rows": self.cache_hit_rows, "unpriced_rows": self.unpriced_rows,
                "unpriced_tokens": self.unpriced_tokens, "unpriced_models": sorted(self.unpriced_models),
                "by_model": dict(self.by_model), "by_feature": dict(self.by_feature),
                "by_customer": dict(self.by_customer), "cross_check_flags": self.cross_check_flags}


def price_all(records: Iterable, fx: FxTable) -> tuple[list[Priced], Summary]:
    out, s = [], Summary()
    for rec in records:
        p = price_record(rec, fx)
        out.append(p)
        s.rows += 1
        if p.status == "cache_hit":
            s.cache_hit_rows += 1
        elif p.status == "unpriced":
            s.unpriced_rows += 1
            s.unpriced_tokens += rec.input_tokens + rec.output_tokens
            s.unpriced_models.add(f"{rec.provider}/{rec.model}")
        else:
            s.priced_rows += 1
            s.priced_paise += p.paise
            s.by_model[rec.model] += p.paise
            s.by_feature[rec.feature or "(untagged)"] += p.paise
            s.by_customer[rec.customer or "(unknown)"] += p.paise
            if p.reported_diff is not None and abs(p.reported_diff) > CROSS_CHECK_TOLERANCE:
                s.cross_check_flags.append({"row": rec.source_row, "source": rec.source, "model": rec.model,
                                            "diff_pct": float(p.reported_diff * 100)})
    return out, s

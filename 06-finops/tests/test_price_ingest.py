"""A27 (price engine, unknown-model guard) + A29 (importers). Synthetic fixtures only.

Run: cd 06-finops && python -m pytest -q tests/test_price_ingest.py
Price tests need `genai-prices` (pip install genai-prices==0.1.11); they skip without it.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from ingest import importers  # noqa: E402
from ingest.schema import UsageRecord  # noqa: E402
from price.fx import FxRate, FxTable, StaleRateError, parse_rbi_home  # noqa: E402

FX_DIR = Path(__file__).resolve().parent / "fixtures" / "ingest"
HAS_GP = importlib.util.find_spec("genai_prices") is not None
needs_gp = pytest.mark.skipif(not HAS_GP, reason="genai-prices not installed")
FX = FxTable([FxRate("2026-10-12", Decimal("95.7485"), "test")])

EXPECTED = {  # file: (format, rows_in, records, skipped, merged)
    "openai_usage.json": ("openai", 4, 3, 1, 0),
    "anthropic_usage.json": ("anthropic", 3, 3, 0, 0),
    "litellm_spendlogs.csv": ("litellm", 5, 4, 1, 0),
    "langfuse_observations.jsonl": ("langfuse", 4, 2, 2, 0),
    "generic.csv": ("generic", 4, 3, 1, 0),
}


# ---------- importers (A29) ----------

@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_five_fixtures_import_with_no_rows_lost(name):
    fmt, rows_in, recs, skipped, merged = EXPECTED[name]
    assert importers.detect_format(FX_DIR / name) == fmt
    r = importers.load(FX_DIR / name)
    assert (r.rows_in, len(r.records), len(r.skipped), len(r.merged)) == (rows_in, recs, skipped, merged)
    assert r.balanced
    assert all(reason for _, reason in r.skipped)          # every skip has a reason


def test_importers_never_copy_prompt_text_or_raw_ids():
    for name in EXPECTED:
        r = importers.load(FX_DIR / name)
        blob = json.dumps([x.to_dict() for x in r.records])
        for secret in ("SECRET PROMPT TEXT", "PRIVATE", "cust_001", "u-77", "acme"):
            assert secret not in blob, (name, secret)
        assert all(x.customer is None or x.customer.startswith("c_") for x in r.records)


def test_openai_bucket_fields():
    r = importers.load(FX_DIR / "openai_usage.json")
    gpt4o = r.records[0]
    assert (gpt4o.model, gpt4o.input_tokens, gpt4o.cache_read_tokens, gpt4o.requests) == ("gpt-4o", 1_200_000, 400_000, 1500)
    assert gpt4o.ts.startswith("2026-10-12") and r.records[1].batch


def test_anthropic_cache_tokens_added_to_input():
    rec = importers.load(FX_DIR / "anthropic_usage.json").records[0]
    assert rec.input_tokens == 300_000 + 100_000 + 600_000
    assert (rec.cache_write_tokens, rec.cache_read_tokens) == (100_000, 600_000)


def test_anthropic_long_form_merges_rows(tmp_path):
    p = tmp_path / "anthropic_console.csv"
    p.write_text("usage_date_utc,model,workspace,api_key,token_type,usage\n"
                 "2026-10-12,claude-haiku-4-5,Default,k1,input_tokens,1000\n"
                 "2026-10-12,claude-haiku-4-5,Default,k1,output_tokens,200\n"
                 "2026-10-12,claude-haiku-4-5,Default,k1,cache_read_input_tokens,500\n"
                 "2026-10-12,claude-haiku-4-5,Default,k1,mystery_tokens,5\n")
    r = importers.load(p)
    assert r.balanced and len(r.records) == 1 and len(r.merged) == 2 and len(r.skipped) == 1
    assert r.records[0].input_tokens == 1500 and r.records[0].output_tokens == 200


def test_litellm_cache_hit_and_tags():
    recs = importers.load(FX_DIR / "litellm_spendlogs.csv").records
    assert [x.feature for x in recs] == ["faq", "summary", "faq", "agent"]
    assert recs[2].served_from_cache and recs[1].provider == "google"


# ---------- FX ----------

def test_fx_staleness_and_rbi_parser():
    assert FX.for_date("2026-10-15").inr_per_usd == Decimal("95.7485")
    with pytest.raises(StaleRateError):
        FX.for_date("2026-10-30")
    with pytest.raises(StaleRateError):
        FX.for_date("2026-10-01")
    html = "<td>INR / 1 USD</td><td>: 95.7485</td> (As at 1.00pm of October 12, 2026) (Source : FBIL)"
    r = parse_rbi_home(html, "2026-10-13")
    assert r.date == "2026-10-12" and r.inr_per_usd == Decimal("95.7485") and "FBIL" in r.source


def test_cached_rate_file_has_source():
    t = FxTable.load()
    assert t.latest().source and t.latest().inr_per_usd > 50


# ---------- price engine (A27) ----------

@needs_gp
def test_inr_equals_usd_times_rate_in_paise():
    from price.engine import price_record, to_paise
    rec = UsageRecord(ts="2026-10-12", provider="openai", model="gpt-4o",
                      input_tokens=1_000_000, output_tokens=1_000_000, requests=100)
    p = price_record(rec, FX)
    assert p.usd == Decimal("12.5")                           # $2.50 + $10.00 per million
    assert p.paise == to_paise(Decimal("12.5"), Decimal("95.7485")) == 119686
    assert p.fx_date == "2026-10-12"


@needs_gp
def test_a7_fixture_numbers():
    """The four a7 numbers: 1M in + 1M out at list price (100 calls, standard tier)."""
    from price.engine import usd_cost
    want = {("openai", "gpt-4o"): "12.5", ("openai", "gpt-4o-mini"): "0.75",
            ("anthropic", "claude-haiku-4-5"): "6", ("google", "gemini-2.5-flash"): "2.8"}
    for (prov, model), usd in want.items():
        rec = UsageRecord(ts="2026-10-12", provider=prov, model=model,
                          input_tokens=1_000_000, output_tokens=1_000_000, requests=100)
        assert usd_cost(rec)[0] == Decimal(usd), model


@needs_gp
def test_aggregates_priced_per_call_not_as_one_giant_call():
    """Deep Scan v2 finding: 1M summed tokens must not trigger the >200k long-context tier."""
    from price.engine import usd_cost
    many = UsageRecord(ts="2026-10-12", provider="anthropic", model="claude-sonnet-4-5",
                       input_tokens=1_000_000, output_tokens=0, requests=1000)
    assert usd_cost(many)[0] == Decimal("3")                  # $3/M standard tier
    unknown_count = UsageRecord(ts="2026-10-12", provider="anthropic", model="claude-sonnet-4-5",
                                input_tokens=1_000_000, source="anthropic")
    usd, _, note = usd_cost(unknown_count)
    assert usd == Decimal("3") and "request count missing" in note


@needs_gp
def test_cache_and_batch_and_remainders():
    from price.engine import usd_cost
    rec = UsageRecord(ts="2026-10-12", provider="openai", model="gpt-4o", input_tokens=1_200_000,
                      cache_read_tokens=400_000, output_tokens=300_000, requests=1500)
    assert usd_cost(rec)[0] == Decimal("5.5")                 # exact despite 400000/1500 remainders
    batch = UsageRecord(ts="2026-10-12", provider="openai", model="gpt-4o-mini",
                        input_tokens=1_000_000, output_tokens=0, requests=10, batch=True)
    usd, _, note = usd_cost(batch)
    assert usd == Decimal("0.075") and "batch" in note


@needs_gp
def test_unknown_model_is_unpriced_never_zero():
    from price.engine import price_all
    recs = importers.load(FX_DIR / "generic.csv").records
    priced, s = price_all(recs, FX)
    bad = [p for p in priced if p.status == "unpriced"]
    assert len(bad) == 1 and bad[0].paise is None and bad[0].usd is None
    assert s.unpriced_rows == 1 and s.unpriced_tokens == 6000
    assert s.unpriced_models == {"mystery/totally-unknown-model-x"}


@needs_gp
def test_summary_over_all_fixtures():
    from price.engine import price_all
    total = 0
    for name in EXPECTED:
        _, s = price_all(importers.load(FX_DIR / name).records, FX)
        assert s.rows == s.priced_rows + s.unpriced_rows + s.cache_hit_rows
        assert sum(s.by_feature.values()) == s.priced_paise == sum(s.by_model.values())
        total += s.priced_paise
        if name == "litellm_spendlogs.csv":
            assert s.cache_hit_rows == 1
            # fixture row 5 reports cost without the cache discount -> flagged (> 0.5%)
            assert [f["row"] for f in s.cross_check_flags] == [5]
    assert total > 0


@needs_gp
def test_crosscheck_against_litellm_snapshot():
    from price.crosscheck import compare
    snap = {"gpt-4o": {"input_cost_per_token": 2.5e-06, "output_cost_per_token": 1e-05,
                       "cache_read_input_token_cost": 1.25e-06},
            "claude-haiku-4-5": {"input_cost_per_token": 1.1e-06, "output_cost_per_token": 5e-06}}
    rows = compare(snap, [("openai", "gpt-4o", "gpt-4o"),
                          ("anthropic", "claude-haiku-4-5", "claude-haiku-4-5"),
                          ("openai", "gpt-4o-mini", "not-there")])
    assert [r["status"] for r in rows] == ["ok", "MISMATCH", "missing in litellm"]

"""F-11: price pass + LiteLLM callback (the JS ingest handler has its own node tests in src/api)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

API = Path(__file__).resolve().parents[1] / "src" / "api"
sys.path.insert(0, str(API))
import litellm_callback as lc  # noqa: E402
import price_pass as pp  # noqa: E402
from price.fx import FxTable  # noqa: E402

ROW = dict(id=1, ts="2026-10-12T05:00:00Z", provider="openai", model="gpt-4.1-mini", input_tokens=1_000_000,
           output_tokens=0, cache_read_tokens=0, cache_write_tokens=0, reasoning_tokens=0, requests=1,
           batch=False, served_from_cache=False)


def test_price_pass_prices_known_skips_unknown_and_cache_hits_are_zero():
    fx = FxTable.load()
    out = pp.price_rows([ROW, {**ROW, "id": 2, "model": "no-such-model-x"}, {**ROW, "id": 3, "served_from_cache": True}], fx)
    ids = {o["id"]: o["cost_paise"] for o in out}
    assert 2 not in ids and ids[3] == 0 and ids[1] > 0


def test_price_pass_matches_file_import_engine():
    from ingest.schema import UsageRecord
    from price.engine import price_record
    fx = FxTable.load()
    rec = UsageRecord(ts=ROW["ts"], provider="openai", model="gpt-4.1-mini", input_tokens=1_000_000)
    assert pp.price_rows([ROW], fx)[0]["cost_paise"] == price_record(rec, fx).paise


def test_run_fetches_only_unpriced_api_rows_and_patches():
    calls = []
    def call(url, key, method="GET", body=None):
        calls.append((method, url, body))
        return [ROW] if method == "GET" else None
    r = pp.run("https://p.supabase.co/", "svc", 10, FxTable.load(), call)
    assert r == {"fetched": 1, "priced": 1, "unpriced": 0}
    assert "source=eq.api" in calls[0][1] and "cost_paise=is.null" in calls[0][1]
    assert calls[1][0] == "PATCH" and calls[1][1].endswith("id=eq.1")


SLO = {"startTime": 1793000000.5, "custom_llm_provider": "anthropic", "model": "claude-sonnet-4-5",
       "prompt_tokens": 1500, "completion_tokens": 200, "prompt_tokens_details": {"cached_tokens": 1000},
       "end_user": "9848012345", "metadata": {"tags": ["team:x", "feature:support-bot"]},
       "messages": [{"role": "user", "content": "secret prompt"}], "response": "secret answer", "cache_hit": False}


def test_callback_event_has_counts_only_and_hashed_user():
    ev = lc.to_event(SLO)
    assert ev["feature"] == "support-bot" and ev["cache_read_tokens"] == 1000
    assert ev["customer"].startswith("c_") and "9848012345" not in str(ev)
    assert "secret" not in str(ev)


def test_callback_batches_and_keeps_events_when_post_fails():
    sent, fail = [], {"on": True}
    def post(events):
        if fail["on"]:
            raise OSError("down")
        sent.append(len(events))
    lg = lc.LedgerPeaksLogger(api_key="lp_x", batch_size=2, post=post)
    for _ in range(3):
        lg.log_success_event({"standard_logging_object": SLO}, None, None, None)
    assert sent == [] and len(lg.buf) == 3          # failed flush kept the events
    fail["on"] = False
    lg.flush()
    assert sent == [3] and lg.buf == []


def test_callback_buffer_is_bounded():
    lg = lc.LedgerPeaksLogger(api_key="lp_x", batch_size=1, post=lambda e: (_ for _ in ()).throw(OSError()))
    for _ in range(50):
        lg.add(SLO)
    assert len(lg.buf) <= 10


@pytest.mark.skipif(subprocess.run(["node", "--version"], capture_output=True).returncode != 0, reason="node missing")
def test_js_ingest_suite():
    r = subprocess.run(["node", "--test"], cwd=API, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-800:]

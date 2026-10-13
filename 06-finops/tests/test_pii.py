"""Tests for 06-finops/src/pii (ROADMAP A32 / PLAN F-15). Synthetic fixtures only.

Run:  python -m pytest 06-finops/tests/test_pii.py -q
Builtin tests need nothing but pytest; Presidio tests skip if it isn't installed.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from ingest.schema import hash_id  # noqa: E402
from pii import recognizers as R  # noqa: E402
from pii import presidio_engine  # noqa: E402
from pii.scan import main, scan  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "pii"
CSV, JSONL, NEG = FX / "llm_logs.csv", FX / "chat_export.jsonl", FX / "negatives.txt"
HAS_PRESIDIO = importlib.util.find_spec("presidio_analyzer") is not None

EXPECTED = {
    CSV: {"AADHAAR": 1, "PAN": 1, "IN_MOBILE": 3, "EMAIL": 2, "UPI_ID": 2, "IFSC": 1,
          "GSTIN": 1, "CARD": 1},
    JSONL: {"AADHAAR": 2, "PAN": 1, "IN_MOBILE": 3, "EMAIL": 1, "UPI_ID": 1, "IFSC": 1,
            "GSTIN": 1, "CARD": 1},
    NEG: {},
}
EXPECTED_UNIQUE = {"AADHAAR": 3, "PAN": 2, "IN_MOBILE": 5, "EMAIL": 3, "UPI_ID": 3,
                   "IFSC": 2, "GSTIN": 2, "CARD": 2}

# Every planted value, as written in the fixtures (all synthetic).
PLANTED = [
    "7260 1815 9082", "5016-6131-8603", "339099603089",
    "ABCPK1234F", "AAPFR4321M",
    "+91 98480 22338", "09912345678", "7702345678", "+919701234567", "+91-8885551234",
    "ravi.kumar@example.in", "priya.sharma@gmail.com", "help@acme-demo.co.in",
    "ravik@okaxis", "priya.s@ybl", "shop.owner@paytm",
    "HDFC0001234", "SBIN0004567",
    "36ABCPK1234F1Z6", "29AAACK7788Q1ZE",
    "4111 1111 1111 1111", "5555-5555-5555-4444",
]


def _forms(v: str) -> set[str]:
    digits = "".join(c for c in v if c.isdigit())
    out = {v, v.lower(), v.upper()}
    if len(digits) >= 10:
        out |= {digits, digits[-10:]}
    return out


def _counts(report, path):
    return report["per_file"][str(path)]


# ------------------------------------------------------------- validators

def test_checksums():
    assert R.verhoeff_ok("726018159082") and not R.verhoeff_ok("551819093786")
    assert R.luhn_ok("4111111111111111") and not R.luhn_ok("1234567812345678")
    assert R.gstin_ok("36ABCPK1234F1Z6") and not R.gstin_ok("36ABCPK1234F1Z5")


def test_bad_checksums_not_reported():
    text = "aadhaar 7260 1815 9083 gst 36ABCPK1234F1Z5 card 4111 1111 1111 1112"
    ents = [f.entity for f in R.find(text)]
    assert "AADHAAR" not in ents and "GSTIN" not in ents and "CARD" not in ents
    # the PAN inside the bad GSTIN is still not reported on its own (no word boundary)
    assert "PAN" not in ents


def test_pan_inside_gstin_counted_once():
    assert [f.entity for f in R.find("GSTIN 36ABCPK1234F1Z6")] == ["GSTIN"]


def test_mobile_shapes():
    good = ["+91 98480 22338", "+919701234567", "+91-8885551234", "09912345678", "7702345678"]
    for g in good:
        assert [f.entity for f in R.find(f"call {g} now")] == ["IN_MOBILE"], g
    for bad in ["1234567890", "5678901234", "ts=1728812345", "+1 415 555 0100"]:
        assert list(R.find(bad)) == [], bad
    norms = {f.norm for g in good[:1] + ["9848022338", "098480 22338"] for f in R.find(g)}
    assert norms == {"+919848022338"}


# ------------------------------------------------------- builtin engine

@pytest.fixture(scope="module")
def builtin_report():
    return scan([str(FX)], engine="builtin", salt="test-salt")


@pytest.mark.parametrize("path", [CSV, JSONL, NEG], ids=lambda p: p.name)
def test_exact_counts_per_file(builtin_report, path):
    assert _counts(builtin_report, path) == EXPECTED[path]


def test_totals_and_unique(builtin_report):
    tot = {}
    for exp in EXPECTED.values():
        for k, v in exp.items():
            tot[k] = tot.get(k, 0) + v
    assert builtin_report["totals"] == dict(sorted(tot.items()))
    assert builtin_report["unique"] == dict(sorted(EXPECTED_UNIQUE.items()))
    assert builtin_report["engine"] == "builtin"
    assert all(f["parse_errors"] == 0 for f in builtin_report["files"])


def test_zero_false_positives_on_negatives():
    assert scan([str(NEG)], engine="builtin")["totals"] == {}


def test_report_has_no_raw_values(tmp_path, capsys):
    out = tmp_path / "report.json"
    rc = main([str(FX), "--out", str(out), "--engine", "builtin", "--fail-on", "AADHAAR"])
    assert rc == 1
    cap = capsys.readouterr()
    blob = out.read_text() + cap.out + cap.err
    for v in PLANTED:
        for form in _forms(v):
            assert form not in blob, "a planted value leaked into the report/console"


def test_hashes_stable_and_salted(builtin_report):
    again = scan([str(FX)], engine="builtin", salt="test-salt")
    assert again["hashes"] == builtin_report["hashes"]
    other = scan([str(FX)], engine="builtin", salt="other-salt")
    assert set(other["hashes"]["AADHAAR"]).isdisjoint(builtin_report["hashes"]["AADHAAR"])
    # hash is ingest.schema.hash_id of the normalised value (spaces/dashes removed)
    assert hash_id("726018159082", "test-salt") in builtin_report["hashes"]["AADHAAR"]
    assert hash_id("+919848022338", "test-salt") in builtin_report["hashes"]["IN_MOBILE"]


def test_salt_from_env(monkeypatch):
    monkeypatch.setenv("LP_HASH_SALT", "env-salt")
    r = scan([str(CSV)], engine="builtin")
    assert r["salt_source"] == "env"
    assert hash_id("726018159082", "env-salt") in r["hashes"]["AADHAAR"]


def test_fail_on_exit_codes(tmp_path):
    out = str(tmp_path / "r.json")
    assert main([str(CSV), "--out", out, "--engine", "builtin", "--fail-on", "PAN,AADHAAR"]) == 1
    r = json.loads(Path(out).read_text())
    assert r["failed_entities"] == ["AADHAAR", "PAN"]
    assert main([str(NEG), "--out", out, "--engine", "builtin", "--fail-on", "AADHAAR,PAN"]) == 0
    assert main([str(CSV), "--out", out, "--engine", "builtin"]) == 0
    assert main([str(tmp_path / "missing.csv"), "--out", out, "--engine", "builtin"]) == 2


def test_auto_falls_back_to_builtin(monkeypatch):
    monkeypatch.setattr(presidio_engine, "available", lambda: False)
    assert scan([str(CSV)], engine="auto")["engine"] == "builtin"


# ------------------------------------------------------- presidio engine

@pytest.mark.skipif(not HAS_PRESIDIO, reason="presidio-analyzer not installed")
def test_presidio_pattern_only_matches_builtin(builtin_report):
    r = scan([str(FX)], engine="presidio", salt="test-salt")
    assert r["engine"] == "presidio" and r["presidio_version"]
    for path, exp in EXPECTED.items():
        assert _counts(r, path) == exp
    assert r["hashes"] == builtin_report["hashes"]
    # Presidio adds nothing on these fixtures; it has no mobile/UPI/IFSC recognizers
    assert r["engine_agreement"]["presidio_only"] == {}
    assert set(r["engine_agreement"]["builtin_only"]) == {"IN_MOBILE", "UPI_ID", "IFSC"}


@pytest.mark.skipif(not HAS_PRESIDIO, reason="presidio-analyzer not installed")
def test_presidio_no_false_positives_on_negatives():
    assert list(presidio_engine.find(NEG.read_text())) == []

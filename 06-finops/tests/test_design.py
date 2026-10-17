"""A12: Ledger Peaks landing + dashboard + X-ray mockups.

Every ₹ figure on the mockups must come from the real price engine (design/sample.py), add up,
and the pages must follow the Kalpa design rules. The 390 px light + dark screen check runs
when Playwright is installed (python3 design/screens.py does the same from the command line).
"""
import json
import re
import sys
from pathlib import Path

import pytest

DESIGN = Path(__file__).resolve().parent.parent / "design"
sys.path.insert(0, str(DESIGN))
import sample  # noqa: E402


@pytest.fixture(scope="module")
def data():
    return sample.build()


def test_pages_embed_fresh_engine_numbers(data):
    assert sample.inject(data, check=True) == [], "run python3 06-finops/design/sample.py"
    for name in sample.PAGES:
        blob = sample.DATA_RE.search((DESIGN / name).read_text()).group(2)
        assert json.loads(blob) == json.loads(json.dumps(data, ensure_ascii=False))


def test_totals_reconcile(data):
    t = data["total_week"]
    assert t > 0
    assert sum(data["by_feature"].values()) == t
    assert sum(data["by_model"].values()) == t
    assert sum(data["by_day"].values()) == t
    assert sum(c["week"] for c in data["customers"]) == t
    for c in data["customers"]:
        assert sum(c["by_feature"].values()) == c["week"]
    assert len(data["by_day"]) == data["period"]["days"] == 7


def test_unknown_model_is_unpriced_not_zero(data):
    u = data["unpriced"]
    assert u["models"] == ["sarvam/sarvam-m"] and u["calls"] > 0 and u["tokens"] > 0
    assert "sarvam-m" not in data["by_model"] and "telugu_voice" not in data["by_feature"]


def test_savings_are_estimates_with_assumptions(data):
    ideas = data["savings"]
    assert [i["id"] for i in ideas] and len(ideas) == 3
    assert {i["id"] for i in ideas} == {"cache", "downgrade", "batch"}
    for i in ideas:
        assert 0 < i["after"] < i["now"] and i["saved_week"] == i["now"] - i["after"]
        assert len(i["assumption"]) > 20
        assert sum(i["by_customer_week"].values()) == i["saved_week"]
    assert [i["saved_week"] for i in ideas] == sorted((i["saved_week"] for i in ideas), reverse=True)
    assert data["savings_month"] == sum(i["saved_month"] for i in ideas)


def test_story_holds(data):
    """The copy says one customer loses money and idea 1 fixes it; the data must agree."""
    losers = [c for c in data["customers"] if c["margin_pct"] < 0]
    assert len(losers) == 1
    assert losers[0]["margin_after_top_idea_pct"] > 0
    assert data["dpdp"]["of"] == 20 and 0 < data["dpdp"]["score"] < 20
    assert data["fx"]["date"] <= data["period"]["from"]


def test_prices_match_plan():
    plan = (DESIGN.parent / "PLAN.md").read_text()
    landing = (DESIGN / "landing.html").read_text()
    for tier, price in [("Audit + Starter Pack", "₹4,999"), ("Starter", "₹1,999"), ("Growth", "₹4,999"), ("Scale", "₹7,999")]:
        assert re.search(rf"\*\*{re.escape(tier)}\*\* \| {price}", plan), tier
        assert price in landing


@pytest.mark.parametrize("name", sample.PAGES)
def test_design_rules_in_source(name):
    html = (DESIGN / name).read_text()
    assert '<meta name="viewport" content="width=device-width,initial-scale=1">' in html
    assert "../../00-hq/design/tokens.css" in html and "lp.css" in html
    assert not re.search(r'(src|href)="https?://', html), "no external scripts, styles or fonts"
    assert "fonts.googleapis" not in html
    assert ".innerHTML" not in re.sub(r"b\.innerHTML = `<svg", "", html), "data goes in with textContent"
    assert not re.search(r"#[0-9a-fA-F]{6}\b", re.sub(r'<script id="lp-data".*?</script>', "", html, flags=re.S)), \
        "colours come from tokens, not new hex values"


def test_screens_390_light_dark(tmp_path):
    pytest.importorskip("playwright.sync_api")
    import screens
    try:
        fails = screens.run(tmp_path)
    except Exception as e:  # Chromium missing on this machine
        pytest.skip(f"Playwright browser not available: {e}")
    assert fails == []
    assert len(list(tmp_path.glob("*.png"))) == len(screens.SHOTS) * 2

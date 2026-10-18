"""A30 (F-06): the X-ray generator. Synthetic data and the importer fixtures only."""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "design"))
import sample  # noqa: E402
from ingest import hash_id, load  # noqa: E402
from xray import dpdp, generate  # noqa: E402
from xray.render import render  # noqa: E402
from xray.report import build, load_revenue  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "ingest"


@pytest.fixture(scope="module")
def synth():
    recs, revenue, answers, company = generate.synthetic_records()
    return build(recs, company=company, revenue=revenue, dpdp_answers=answers, synthetic=True)


def test_synthetic_totals_equal_the_mockup_engine_numbers(synth):
    ref = sample.build()
    assert synth["total_week"] == ref["total_week"]
    assert synth["by_model"] == ref["by_model"] and synth["by_feature"] == ref["by_feature"]
    assert sum(synth["by_day"].values()) == synth["total_week"]
    assert sum(c["week"] for c in synth["customers"]) == synth["total_week"]
    assert synth["unpriced"]["models"] == ["sarvam/sarvam-m"]     # never counted as Rs 0


def test_savings_are_repriced_estimates_with_assumptions(synth):
    ideas = synth["savings"]
    assert 1 <= len(ideas) <= 3 and len({i["id"] for i in ideas}) == len(ideas)
    assert [i["saved_week"] for i in ideas] == sorted((i["saved_week"] for i in ideas), reverse=True)
    for i in ideas:
        assert i["after"] < i["now"] and i["saved_week"] == i["now"] - i["after"] > 0
        assert len(i["assumption"]) > 40
        assert sum(i["by_customer_week"].values()) == i["saved_week"]
    assert synth["savings_month"] == sum(i["saved_month"] for i in ideas)
    assert len({i["feature"] for i in ideas}) == len(ideas), "two ideas on one feature would double count"
    for i in ideas:
        assert not (i["id"] == "batch" and i["feature"] in ("support_reply", "rag_search")), "live features can't wait"


def test_margins_use_revenue_and_dpdp_score(synth):
    worst = min(synth["customers"], key=lambda c: c["margin_pct"])
    assert worst["name"] == "Biryani Bazaar" and worst["margin_pct"] < 0
    assert synth["dpdp"]["score"] == 12 and synth["dpdp"]["of"] == 20


def test_dpdp_questions_match_the_mockup():
    assert [q for q, _ in sample.DPDP] == dpdp.QUESTIONS


@pytest.mark.parametrize("name", sorted(p.name for p in FIX.iterdir()))
def test_every_importer_fixture_makes_a_report(name):
    res = load(FIX / name)
    assert res.balanced
    data = build(res.records, company="Fixture Co")
    assert data["total_week"] == sum(data["by_model"].values())
    assert all(c["margin_pct"] is None for c in data["customers"])       # no revenue file given
    assert data["dpdp"]["answered"] == 0
    html = render(data)
    assert "Fixture Co" in html and not re.search(r'(?:href|src)="https?:', html)


def test_html_is_self_contained_and_escapes_data():
    recs, _, _, _ = generate.synthetic_records()
    evil = "</script><script>alert(1)</script>"
    html = render(build(recs[:20], company=evil))
    assert "<script>alert(1)</script>" not in html
    assert "fonts.googleapis" not in html and "../../00-hq" not in html
    assert "data:font/woff;base64," in html


def test_revenue_file_is_hashed_on_the_way_in(tmp_path):
    f = tmp_path / "rev.csv"
    f.write_text("customer,name,monthly_revenue_inr\nacme,Acme Corp,\"12,500\"\n")
    assert load_revenue(f) == {hash_id("acme"): ("Acme Corp", 1_250_000)}


def test_bad_dpdp_answers_rejected(tmp_path):
    f = tmp_path / "a.json"
    f.write_text(json.dumps([True] * 19))
    with pytest.raises(ValueError):
        dpdp.load_answers(f)


def test_cli_on_a_real_export_shape(tmp_path, capsys):
    out = tmp_path / "x.html"
    assert generate.main([str(FIX / "generic.csv"), "--company", "Acme", "--out", str(out)]) == 0
    assert out.exists() and "wrote" in capsys.readouterr().out


def test_renders_on_a_phone_light_and_dark_and_prints_2_pages(tmp_path, synth):
    pw = pytest.importorskip("playwright.sync_api")
    from xray.render import to_pdf
    res = load(FIX / "litellm_spendlogs.csv")
    files = {"synth": synth, "fixture": build(res.records, company="Fixture Co")}
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        for key, data in files.items():
            path = tmp_path / f"{key}.html"
            path.write_text(render(data))
            for scheme in ("light", "dark"):
                pg = b.new_page(viewport={"width": 390, "height": 844}, color_scheme=scheme)
                errors = []
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.on("request", lambda r: errors.append("request " + r.url) if r.url.startswith("http") else None)
                pg.goto(path.as_uri())
                assert errors == [], errors
                assert pg.evaluate("document.documentElement.scrollWidth") <= 390
                assert len(pg.inner_text("#headline")) > 30
                assert "NaN" not in pg.inner_text("body") and "undefined" not in pg.inner_text("body")
                pg.close()
        b.close()
    assert to_pdf(tmp_path / "synth.html", tmp_path / "synth.pdf") == 2

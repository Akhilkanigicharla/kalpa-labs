"""b6 consulting delivery kit: intake validator, P1 audit, P2 checklist + templates, P3 gap report.
Synthetic data only. No network."""
import copy
import csv
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

os.environ.setdefault("LP_ALLOW_DEV_SALT", "1")
KIT = Path(__file__).resolve().parents[1]
for sub in ("intake", "p1_cost_audit", "p2_guardrails", "p3_iso42001"):
    sys.path.insert(0, str(KIT / sub))
import audit  # noqa: E402
import build_checklist  # noqa: E402
import gap  # noqa: E402
import validate_intake  # noqa: E402

SAMPLE = KIT / "p1_cost_audit" / "sample_usage_SYNTHETIC.csv"
HEAD = "date,feature,model,input_tokens,output_tokens,cost"


def _csv(tmp_path, lines, name="u.csv"):
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ---------- intake ----------
def test_example_intake_is_valid():
    data = json.loads((KIT / "intake" / "example_intake_SYNTHETIC.json").read_text())
    assert validate_intake.validate(data) == []


def test_intake_catches_missing_bad_and_wrong_types():
    data = json.loads((KIT / "intake" / "example_intake_SYNTHETIC.json").read_text())
    bad = copy.deepcopy(data)
    del bad["consent"]
    bad["company"]["contact_email"] = "not-an-email"
    bad["goals"]["packages"] = ["P9"]
    bad["company"]["team_size"] = True
    errs = validate_intake.validate(bad)
    assert "$.consent: missing" in errs
    assert any("contact_email" in e for e in errs)
    assert any("packages[0]" in e for e in errs)
    assert any("team_size: should be integer" in e for e in errs)
    bad2 = copy.deepcopy(data)
    bad2["consent"]["data_processing"] = False
    assert any("data_processing" in e for e in validate_intake.validate(bad2))


def test_intake_cli(tmp_path, capsys):
    p = tmp_path / "i.json"
    p.write_text("{}")
    assert validate_intake.main([str(p)]) == 1
    assert validate_intake.main([str(KIT / "intake" / "example_intake_SYNTHETIC.json")]) == 0


# ---------- P1 cost audit ----------
def test_sample_is_marked_synthetic_and_finds_all_signal_kinds():
    rows, problems, synth = audit.load(SAMPLE)
    assert synth and not problems and len(rows) > 200
    a = audit.analyse(rows)
    kinds = {s["kind"] for s in a["signals"] if s["saving"] > 0}
    assert {"downgrade", "cache", "repeats", "retries"} <= kinds
    assert a["total"] == sum(r.cost for r in rows)
    assert sum(a["by_model"].values()) == a["total"] == sum(a["by_feature"].values())
    # combined never double counts: below the sum of standalone savings, and below spend
    assert 0 < a["combined"] <= sum(s["saving"] for s in a["signals"]) + Decimal("1e-9") and a["combined"] < a["total"]


def test_report_has_sections_method_and_synthetic_banner():
    rows, problems, synth = audit.load(SAMPLE)
    md = audit.render(audit.analyse(rows), client="Demo", currency="USD", synthetic=synth, problems=problems)
    for h in ("## 1. Summary", "## 2. Spend by model", "## 3. Spend by feature", "## 4. Top waste signals",
              "## 5. How the saving was estimated", "SYNTHETIC DATA", "not guarantees", "gpt-4o-mini"):
        assert h in md
    assert "certified" not in md.lower()


def test_downgrade_saving_uses_engine_ratio(tmp_path):
    p = _csv(tmp_path, [HEAD, "2026-10-01,chat,gpt-4o,400,50,10.00", "2026-10-02,chat,gpt-4o,400,50,10.00"])
    rows, _, synth = audit.load(p)
    a = audit.analyse(rows)
    assert not synth
    (s,) = [s for s in a["signals"] if s["kind"] == "downgrade"]
    # gpt-4o-mini lists at ~6% of gpt-4o, so saving is ~94% of the billed 20.00
    assert Decimal("18") < s["saving"] < Decimal("20")
    assert a["combined"] == s["saving"]


def test_proxy_retries_and_no_hash_note(tmp_path):
    p = _csv(tmp_path, [HEAD, "2026-10-01,chat,gpt-4o-mini,400,0,1.00", "2026-10-01,chat,gpt-4o-mini,400,300,1.00"])
    a = audit.analyse(audit.load(p)[0])
    r = [s for s in a["signals"] if s["kind"] == "retries"][0]
    assert r["saving"] == Decimal("0.80") and "proxy" in r["evidence"]
    assert any(s["kind"] == "repeats-unknown" and s["saving"] == 0 for s in a["signals"])


def test_unknown_model_is_reported_not_guessed(tmp_path):
    p = _csv(tmp_path, ["date,feature,model,provider,input_tokens,output_tokens,cost",
                        "2026-10-01,chat,acme-llm-9,acme,300,40,5.00"])
    a = audit.analyse(audit.load(p)[0])
    assert a["combined"] == 0 and a["total"] == Decimal("5.00")


def test_bad_rows_are_skipped_and_missing_columns_fail(tmp_path):
    p = _csv(tmp_path, [HEAD, "2026-10-01,chat,gpt-4o,400,50,1.0", "not-a-date,chat,gpt-4o,1,1,1",
                        "2026-10-01,chat,gpt-4o,-5,1,1"])
    rows, problems, _ = audit.load(p)
    assert len(rows) == 1 and len(problems) == 2
    with pytest.raises(ValueError, match="cost"):
        audit.load(_csv(tmp_path, ["date,feature,model,input_tokens,output_tokens", "2026-10-01,a,b,1,1"], "x.csv"))


def test_audit_cli(tmp_path):
    out = tmp_path / "r.md"
    assert audit.main([str(SAMPLE), "--client", "Demo", "--out", str(out)]) == 0
    assert out.read_text().startswith("# AI Cost Audit: Demo")
    assert audit.main([str(tmp_path / "missing.csv")]) == 2


# ---------- P2 guardrails ----------
LAWYER = "check with a lawyer before giving"


def test_checklist_covers_every_framework_item_and_is_fresh():
    md = build_checklist.build("Demo")
    fw = KIT.parents[0] / "src" / "frameworks"
    for name in ("dpdp-2023", "eu-ai-act-art50"):
        for c in json.loads((fw / f"{name}.json").read_text())["controls"]:
            line = next(ln for ln in md.splitlines() if ln.startswith(f"| {c['id']} |"))
            assert "[LAWYER CHECK]" in line
    shipped = (KIT / "p2_guardrails" / "templates" / "dpdp-eu-ai-act-art50-checklist.md").read_text()
    assert shipped == build_checklist.build("Client"), "re-run build_checklist.py --out templates/..."


@pytest.mark.parametrize("name", ["ai-use-policy.md", "prompt-injection-data-leak-tests.md",
                                  "staff-one-pager.md", "dpdp-eu-ai-act-art50-checklist.md"])
def test_every_legal_template_carries_the_lawyer_check(name):
    text = (KIT / "p2_guardrails" / "templates" / name).read_text()
    assert LAWYER in text.lower()
    assert "certified" not in text.lower()


def test_csv_templates_parse():
    inv = list(csv.DictReader((KIT / "p2_guardrails" / "templates" / "ai-system-inventory.csv").open()))
    assert inv and {"system_id", "model_provider", "personal_data", "eu_users", "discloses_ai"} <= set(inv[0])
    risks = list(csv.DictReader((KIT / "p2_guardrails" / "templates" / "risk-register.csv").open()))
    for r in risks:
        assert int(r["score"]) == int(r["likelihood_1to5"]) * int(r["impact_1to5"])
        if r["legal_point"].startswith("yes"):
            assert LAWYER in r["legal_point"]


# ---------- P3 ISO/IEC 42001 ----------
def test_every_catalogue_id_has_own_words_question_and_group():
    its = gap.items()
    assert len(its) == len(json.loads(gap.CATALOGUE.read_text())["controls"]) == 70
    assert all(i["question"].endswith("?") for i in its)
    assert {i["group"] for i in its} == set(json.loads(gap.AREAS.read_text())["groups"])


def _answers(score=0, **over):
    a = {i["id"]: {"score": score} for i in gap.items()}
    a.update(over)
    return {"client": "T", "answers": a}


def test_scores_and_roadmap_order():
    res = gap.score(_answers(3, **{"4.1": {"score": 0}, "A.8.2": {"score": 1}, "9.1": {"score": 2}}))
    assert [g["id"] for g in res["gaps"]] == ["4.1", "9.1", "A.8.2"]   # phase order, clauses first
    assert res["overall"] == round(100 * (67 * 3 + 0 + 1 + 2) / (70 * 3))
    assert res["groups"]["5"] == 100 and res["problems"] == []
    assert gap.score(_answers(0))["overall"] == 0 and gap.score(_answers(3))["gaps"] == []


def test_na_rules_and_bad_input():
    res = gap.score(_answers(3, **{"A.5.5": {"score": "na", "reason": "internal only"},
                                   "A.5.4": {"score": "na"}, "4.1": {"score": "na", "reason": "x"},
                                   "5.1": {"score": 7}, "Z.9": {"score": 1}}))
    assert [r["id"] for r in res["na"]] == ["A.5.5"]
    ids = {g["id"] for g in res["gaps"]}
    assert {"A.5.4", "4.1", "5.1"} <= ids
    text = " ".join(res["problems"])
    assert "A.5.4: 'na' needs a reason" in text and "4.1: clauses 4-10 cannot be 'na'" in text
    assert "5.1: score must be 0-3" in text and "unknown id ignored: Z.9" in text
    partial = gap.score({"answers": {"4.1": 3}})
    assert "69 item(s) not answered" in " ".join(partial["problems"])


def test_report_render_and_cli(tmp_path):
    ex = KIT / "p3_iso42001" / "answers_example_SYNTHETIC.json"
    data = gap.load_answers(ex)
    md = gap.render(data, gap.score(data))
    for h in ("SYNTHETIC DATA", "not a certification", "## 3. Gap list", "Days 1-30", "Days 31-60",
              "Days 61-90", "Statement of Applicability"):
        assert h in md
    out = tmp_path / "g.md"
    assert gap.main(["report", str(ex), "--out", str(out)]) == 0 and out.exists()
    bad = tmp_path / "bad.json"
    bad.write_text("[1]")
    assert gap.main(["report", str(bad)]) == 2


def test_template_round_trip(tmp_path, capsys):
    assert gap.main(["template"]) == 0
    t = json.loads(capsys.readouterr().out)
    assert len(t["answers"]) == 70
    res = gap.score(t)
    assert res["overall"] == 0 and len(res["gaps"]) == 70


def test_yaml_answers(tmp_path):
    yaml = pytest.importorskip("yaml")
    p = tmp_path / "a.yaml"
    p.write_text(yaml.safe_dump(_answers(2)))
    assert gap.score(gap.load_answers(p))["overall"] == 67

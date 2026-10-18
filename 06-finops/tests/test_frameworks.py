"""A31 (F-13): framework catalogue validator."""
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from frameworks import validate as v  # noqa: E402

FW = ROOT / "src" / "frameworks"


def test_real_catalogue_is_valid():
    assert v.validate() == []
    assert v.main() == 0


def test_every_dpdp_duty_cites_section_or_rule():
    for c in v.load("dpdp-2023.json")["controls"]:
        assert c["cite"] and all(v.CITE.match(x) for x in c["cite"]), c["id"]


def test_iso_has_70_probo_ids_and_attribution():
    iso = v.load("iso42001-2023.json")
    assert len(iso["controls"]) == 70
    assert iso["source"]["licence"] == "MIT"


@pytest.fixture
def copy(tmp_path):
    for f in FW.glob("*.json"):
        shutil.copy(f, tmp_path / f.name)
    return tmp_path


def _edit(folder, name, fn):
    p = folder / name
    d = json.loads(p.read_text())
    fn(d)
    p.write_text(json.dumps(d))


@pytest.mark.parametrize("name,fn,needle", [
    ("dpdp-2023.json", lambda d: d["controls"][0].update(cite=[]), "no section or rule"),
    ("dpdp-2023.json", lambda d: d["controls"][0].update(cite=["Section 8"]), "bad citation"),
    ("dpdp-2023.json", lambda d: d["controls"][0].update(iso42001=["A.99.9"]), "not in iso42001"),
    ("dpdp-2023.json", lambda d: d["controls"][1].update(id=d["controls"][0]["id"]), "duplicate"),
    ("dpdp-2023.json", lambda d: d["controls"][0].update(applies_from="May 2027"), "not a date"),
    ("dpdp-2023.json", lambda d: d.update(disclaimer="Read carefully."), "not legal advice"),
    ("iso42001-2023.json", lambda d: d["controls"][0].update(text="copied clause"), "extra fields"),
    ("iso42001-2023.json", lambda d: d["source"].update(licence=""), "attribution"),
    ("eu-ai-act-art50.json", lambda d: d["controls"][0].update(para="Art. 52(1)"), "bad paragraph"),
    ("eu-ai-act-art50.json", lambda d: d["controls"][0].update(role="user"), "role must be"),
])
def test_validator_catches_breakage(copy, name, fn, needle):
    _edit(copy, name, fn)
    errs = v.validate(copy)
    assert any(needle in e for e in errs), errs

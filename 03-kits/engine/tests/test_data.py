"""Data checks: every exam file is valid, no invented dates, no invented video links, Telugu names for TGPSC kits,
GATE data still matches the GATE kit. Run: python3 -m pytest 03-kits/engine/tests -q"""
import copy, datetime as dt, re
import pytest
import kit_engine as E

FILES = E.exam_files()
IDS = [f.stem for f in FILES]


def test_all_five_exams_present():
    assert {"tgpsc-group2", "tgpsc-group3", "ssc-cgl", "rrb-ntpc", "gate-2027-cs"} <= set(IDS)


@pytest.mark.parametrize("f", FILES, ids=IDS)
def test_exam_file_is_valid(f):
    assert E.validate(E.load(f)) == []


@pytest.mark.parametrize("f", FILES, ids=IDS)
def test_60_to_100_topics(f):
    assert 60 <= len(E.topics(E.load(f))) <= 100


@pytest.mark.parametrize("f", FILES, ids=IDS)
def test_no_invented_dates(f):
    d = E.load(f)
    for k in d["key_dates"]:
        assert k["status"] in E.DATE_STATUSES
        if k["status"] == "CONFIRMED":
            assert dt.date.fromisoformat(k["date"]) and re.match(r"^https://", k["source"]), k
        else:
            assert k["date"] is None, f"{k['event']}: only CONFIRMED dates may carry a day"


@pytest.mark.parametrize("f", FILES, ids=IDS)
def test_no_invented_video_links(f):
    for s in E.load(f)["subjects"]:
        assert len(s.get("videos") or []) >= 1, f"{s['name']}: add YouTube slots"
        for v in s["videos"]:
            assert v["status"] == "TO_CURATE" and v["url"] is None and v["query"].strip()


def test_tgpsc_group2_notification_not_announced():
    d = E.load(E.EXAMS / "tgpsc-group2.yaml")
    assert all(k["status"] == "NOT_ANNOUNCED" for k in d["key_dates"]), "Group 2 2026 notification is not out (Nov 2026)"


@pytest.mark.parametrize("eid", ["tgpsc-group2", "tgpsc-group3"])
def test_tgpsc_kits_have_telugu(eid):
    d = E.load(E.EXAMS / f"{eid}.yaml")
    assert "te" in d["languages"]
    tel = re.compile(r"[ఀ-౿]")
    for t in E.topics(d):
        assert tel.search(t["te"]), t["en"]
    assert all(tel.search(s["name_te"]) for s in d["subjects"])


def test_gate_data_matches_gate_kit():
    d = E.load(E.EXAMS / "gate-2027-cs.yaml")
    assert [(s["name"], [t["en"] for t in s["topics"]]) for s in d["subjects"]] == [(n, t) for n, _m, t in E.G.SUBJECTS]
    assert sorted(k["date"] for k in d["key_dates"] if k["status"] == "CONFIRMED") == sorted(E.G.EXAM_DAYS)


BASE = E.load(E.EXAMS / "ssc-cgl.yaml")


@pytest.mark.parametrize("break_it, expect", [
    (lambda d: d["key_dates"][0].update(status="CONFIRMED", date="2027-01-01", source=None), "official https source"),
    (lambda d: d["key_dates"][0].update(status="CONFIRMED", date=None), "real date"),
    (lambda d: d["key_dates"][1].update(date="2027-03-01"), "only CONFIRMED dates may have a date"),
    (lambda d: d["key_dates"][1].update(status="EXPECTED", note=""), "EXPECTED needs a note"),
    (lambda d: d["key_dates"][1].update(status="MAYBE"), "status must be one of"),
    (lambda d: d["subjects"][0]["videos"][0].update(url="https://www.youtube.com/watch?v=abcdefghijk"), "TO_CURATE slot must have url: null"),
    (lambda d: d["subjects"][0]["videos"][0].update(status="CURATED", url="https://example.com/v"), "real YouTube watch link"),
    (lambda d: d.update(languages=["en", "te"]), "Telugu"),
    (lambda d: d.update(official_site="http://ssc.gov.in"), "https"),
    (lambda d: d["subjects"][0]["topics"].append({"en": "Percentages"}), "duplicate topic"),
    (lambda d: d["materials"][0].update(url="ftp://x"), "url must be https"),
    (lambda d: d["plan"].update(revision_days=[7, 3]), "revision_days"),
])
def test_validator_catches_mistakes(break_it, expect):
    d = copy.deepcopy(BASE); break_it(d)
    errs = E.validate(d)
    assert any(expect in x for x in errs), errs

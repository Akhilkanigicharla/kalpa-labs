"""Output checks: xlsx / ics / html / telegram built for every exam, and they behave. LibreOffice recalculation
proves the progress % and revision formulas (skipped locally without soffice, required on CI)."""
import collections, datetime as dt, json, os, pathlib, re, shutil, subprocess
import pytest
from openpyxl import load_workbook
import kit_engine as E

START = dt.date(2026, 11, 10)
FILES = E.exam_files()
IDS = [f.stem for f in FILES]
PORTABLE = {"IF", "AND", "OR", "MAX", "MIN", "SUM", "COUNTIF", "COUNTIFS", "COUNTA", "INDEX", "MATCH", "CHOOSE", "TODAY", "DATE", "ROUND", "ISNUMBER"}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist")
    return {f.stem: (E.load(f), E.build_all(f, out, START, START)) for f in FILES}


@pytest.mark.parametrize("eid", IDS)
def test_four_files_built(built, eid):
    _, p = built[eid]
    assert set(p) == {"xlsx", "ics", "html", "telegram"}
    for f in p.values():
        assert f.exists() and 0 < f.stat().st_size < 200_000, f


@pytest.mark.parametrize("eid", IDS)
def test_xlsx(built, eid):
    d, p = built[eid]
    wb = load_workbook(p["xlsx"])
    assert {"Start", "Plan", "Progress", "Syllabus", "Dates", "Material", "Videos"} <= set(wb.sheetnames)
    sy = wb["Syllabus"]; heads = [c.value for c in sy[4]]
    n = len(E.topics(d))
    assert [sy.cell(4 + i, 4).value for i in range(1, n + 1)] == [t["en"] for t in E.topics(d)]
    st = heads.index("Status") + 1
    assert any(f"{sy.cell(5, st).column_letter}5" in str(v.sqref) and "Done" in v.formula1 for v in sy.data_validations.dataValidation)
    assert ("తెలుగు" in heads) == ("te" in d["languages"])
    used = {m for ws in wb for row in ws.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=") for m in re.findall(r"([A-Z][A-Z0-9.]*)\(", c.value)}
    assert used <= PORTABLE, used - PORTABLE
    pr = wb["Progress"]
    assert pr.cell(5 + len(d["subjects"]), 6).value.startswith("=IF(B")
    yt = [sy.cell(r, heads.index("YouTube") + 1).hyperlink.target for r in range(5, 5 + n)]
    assert all(u.startswith("https://www.youtube.com/results?search_query=") for u in yt)


def unfold(raw):
    return raw.replace("\r\n ", "").split("\r\n")


@pytest.mark.parametrize("eid", IDS)
def test_ics(built, eid):
    d, p = built[eid]
    raw = p["ics"].read_bytes()
    phys = raw.split(b"\r\n")
    assert phys[-1] == b"" and all(len(x) <= 75 for x in phys), "lines must be CRLF and at most 75 octets"
    raw.decode("utf-8")
    lines = unfold(raw.decode("utf-8"))
    assert lines[0] == "BEGIN:VCALENDAR" and lines[-2] == "END:VCALENDAR"
    cnt = collections.Counter(lines)
    assert cnt["BEGIN:VEVENT"] == cnt["END:VEVENT"] and cnt["BEGIN:VALARM"] == cnt["END:VALARM"]
    confirmed = [k for k in d["key_dates"] if k["status"] == "CONFIRMED"]
    allday = [x for x in lines if x.startswith("DTSTART;VALUE=DATE:")]
    assert sorted(x[-8:] for x in allday) == sorted(k["date"].replace("-", "") for k in confirmed), "only CONFIRMED dates go in the calendar"
    plan, _ = E.schedule(d, START)
    assert sum(1 for x in lines if x == "CATEGORIES:Study plan") == len(plan)
    assert sum(1 for x in lines if x.startswith("RRULE:FREQ=WEEKLY")) == 1
    uids = [x for x in lines if x.startswith("UID:")]
    assert len(uids) == len(set(uids))


@pytest.mark.parametrize("eid", IDS)
def test_html(built, eid):
    d, p = built[eid]
    h = p["html"].read_text(encoding="utf-8")
    tokens = E.TOKENS.read_text(encoding="utf-8")
    assert tokens in h, "tokens.css must be inlined unchanged"
    own = h.replace(tokens, "")
    assert set(re.findall(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b", own)) == set(), "no colours outside tokens.css"
    for m in re.findall(r"font(?:-family)?:([^;}]*)", E.CSS):
        assert "var(--f-" in m or m.strip() == "inherit", f"font not from tokens: {m}"
    assert not re.search(r"<script[^>]+src=|<link[^>]+stylesheet|fetch\(|XMLHttpRequest", h), "page must be self-contained"
    spots = [m.start() for m in re.finditer("localStorage", h)]
    assert len(spots) == 2 and all("try{" in h[i - 25:i] for i in spots), "every localStorage call sits in try/catch"
    assert 'name="viewport"' in h
    blob = re.search(r'<script type="application/json" id="kit">(.*?)</script>', h, re.S).group(1)
    data = json.loads(blob)
    assert len(data["topics"]) == len(E.topics(d)) and data["id"] == d["id"]
    ex = E.exam_date(d)
    assert data["exam"] == (ex.isoformat() if ex else None)
    assert ('id="lang"' in h) == ("te" in d["languages"])


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_html_script_parses(built, tmp_path):
    _, p = built["tgpsc-group2"]
    js = re.findall(r"<script>(.*?)</script>", p["html"].read_text(encoding="utf-8"), re.S)[0]
    f = tmp_path / "page.js"; f.write_text(js, encoding="utf-8")
    subprocess.run(["node", "--check", str(f)], check=True)


@pytest.mark.parametrize("eid", IDS)
def test_telegram(built, eid):
    d, p = built[eid]
    doc = json.loads(p["telegram"].read_text(encoding="utf-8"))
    msgs = doc["messages"]
    assert doc["exam"] == d["id"] and doc["method"] == "sendMessage" and msgs
    per_day = collections.Counter((m["send_at"][:10], m["lang"]) for m in msgs)
    assert max(per_day.values()) == 1, "at most one message a day per language"
    assert {m["lang"] for m in msgs} == set(d["languages"]) & set(E.TXT)
    for m in msgs:
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:00\+05:30", m["send_at"]) and 0 < len(m["text"]) <= E.TG_LIMIT
        assert "only today" not in m["text"].lower() and "chat_id" not in m
    studied = "\n".join(m["text"] for m in msgs if m["lang"] == "en" and "study" in m["kinds"])
    assert all(f"• {t['en']}" in studied for t in E.topics(d)), "every topic gets a study day"
    confirmed = [k for k in d["key_dates"] if k["status"] == "CONFIRMED"]
    assert any("date_alert" in m["kinds"] for m in msgs) == bool(confirmed)


def test_gate_plan_finishes_before_exam():
    d = E.load(E.EXAMS / "gate-2027-cs.yaml")
    plan, _ = E.schedule(d, START)
    assert max(p["date"] for p in plan if p["new"]) <= E.exam_date(d) - dt.timedelta(14)
    assert all(p["date"] < E.exam_date(d) for p in plan)


def test_dist_is_current():
    """dist/ holds the built kits for every exam (rebuild: python3 03-kits/engine/kit_engine.py)."""
    for f in FILES:
        for suffix in ("tracker.xlsx", "calendar.ics", "tracker.html", "telegram.json"):
            assert (E.DIST / f.stem / f"{f.stem}-{suffix}").exists(), f"{f.stem}-{suffix} missing: run the build"


def test_recalc_progress_and_revision(built, tmp_path):
    if not shutil.which("soffice"):
        if os.environ.get("CI"): pytest.fail("LibreOffice missing on CI")
        pytest.skip("needs LibreOffice")
    d, p = built["tgpsc-group2"]
    wb = load_workbook(p["xlsx"]); sy = wb["Syllabus"]
    heads = [c.value for c in sy[4]]; S, D = heads.index("Status") + 1, heads.index("Done on") + 1
    for r in (5, 6, 7):
        sy.cell(r, S).value = "Done"; sy.cell(r, D).value = START - dt.timedelta(1)
    sy.cell(8, S).value = "Learning"
    src = tmp_path / "in.xlsx"; wb.save(src)
    out = tmp_path / "out"
    subprocess.run(["soffice", f"-env:UserInstallation=file://{tmp_path}/lo", "--headless", "--calc", "--convert-to", "xlsx:Calc MS Excel 2007 XML",
                    "--outdir", str(out), str(src)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    v = load_workbook(out / "in.xlsx", data_only=True)
    n = len(E.topics(d)); tot = 5 + len(d["subjects"])
    pr = v["Progress"]
    assert pr.cell(tot, 2).value == n and pr.cell(tot, 3).value == 3 and pr.cell(tot, 4).value == 1
    assert abs(pr.cell(tot, 6).value - 3 / n) < 1e-9
    assert abs(pr.cell(5, 6).value - 3 / len(d["subjects"][0]["topics"])) < 1e-9
    vs = v["Syllabus"]; N, Q = heads.index("Next revision") + 1, heads.index("Due?") + 1
    nxt = vs.cell(5, N).value
    assert (nxt.date() if hasattr(nxt, "date") else nxt) == START and vs.cell(5, Q).value == "Revise"
    assert vs.cell(8, N).value in (None, "")
    pl = v["Plan"]
    assert pl["B6"].value == "Not announced" and pl["B10"].value == 3
    errs = [(ws.title, c.coordinate) for ws in v for row in ws.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("#") and c.value.endswith(("!", "?", "A"))]
    assert not errs, errs

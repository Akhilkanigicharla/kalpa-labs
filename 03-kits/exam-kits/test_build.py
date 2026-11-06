#!/usr/bin/env python3
"""A159 checks: every exam file is complete and sourced; every kit builds; with TODAY() pinned to 6 Nov 2026 and sample
inputs, LibreOffice recalculation gives the right days left, % done, revisions due, study days, needed pace, mock %, date
countdowns; no error cells; only Google-Sheets-portable functions. Run: python3 03-kits/exam-kits/test_build.py"""
import datetime as dt, pathlib, re, subprocess, sys, tempfile
from openpyxl import load_workbook
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B  # noqa: E402

TODAY = dt.date(2026, 11, 6)
PORTABLE = {"IF", "MAX", "MIN", "N", "CHOOSE", "COUNTA", "COUNTIF", "COUNTIFS", "COUNT", "ROUND", "OR", "AND", "DATE", "TODAY", "ISNUMBER"}
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def recalc(src, tmp):
    out = pathlib.Path(tmp) / "recalc"
    subprocess.run(["soffice", f"-env:UserInstallation=file://{tmp}/lo", "--headless", "--calc", "--convert-to", "xlsx:Calc MS Excel 2007 XML",
                    "--outdir", str(out), str(src)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    return load_workbook(out / pathlib.Path(src).name, data_only=True)


exams = B.load_exams()
check(len(exams) >= 5, "need at least 5 exams")
families = {e["family"].split(" · ")[0] for e in exams}
for fam in ("State PSC", "Teachers", "Banks", "Central Government"):
    check(fam in families, f"family missing: {fam}")

with tempfile.TemporaryDirectory() as tmp:
    for e in exams:
        eid = e["id"]
        # data checks
        check(e["official_url"].startswith("https://"), f"{eid}: official_url must be https")
        check(len(e["sources"]) >= 3 and e["sources"][0] == e["official_url"], f"{eid}: official site + 2 more sources")
        rows = B.topics(e)
        check(len(rows) >= 10, f"{eid}: only {len(rows)} topics")
        check(len(rows) == len(set(rows)), f"{eid}: duplicate topic rows")
        check(all(t.strip() for _, _, t in rows), f"{eid}: empty topic")
        # build with sample inputs
        src = pathlib.Path(tmp) / B.filename(e)
        B.build(e, src, TODAY)
        wb = load_workbook(src)
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str) and c.value.startswith("="):
                        for fn in re.findall(r"([A-Z]+)\(", c.value):
                            check(fn in PORTABLE, f"{eid}: non-portable {fn} in {ws.title}!{c.coordinate}")
        st, sy, lg, mk, ds = wb["Start"], wb["Syllabus"], wb["Daily log"], wb["Mocks"], wb["Dates"]
        st["B4"] = dt.date(2026, 12, 6)
        for r in (5, 6, 7):
            sy[f"D{r}"] = "Done"
        sy["D8"] = "Learning"; sy["E8"] = dt.date(2026, 11, 5); sy["F8"] = 0          # next = 6 Nov → due today
        sy["D9"] = "Learning"; sy["E9"] = dt.date(2026, 11, 1); sy["F9"] = 2          # next = 8 Nov → not due
        sy["D10"] = "Learning"; sy["E10"] = dt.date(2026, 10, 1); sy["F10"] = 5       # 3+ revisions → +21 → 22 Oct, due
        for i, d in enumerate(range(1, 7)):                                            # 1..6 Nov; window is 31 Oct..6 Nov
            lg[f"A{5+i}"] = dt.date(2026, 11, d); lg[f"B{5+i}"] = 2
        lg["A11"] = dt.date(2026, 10, 20); lg["B11"] = 3                               # outside the window
        mk["A5"] = dt.date(2026, 11, 2); mk["C5"] = 120; mk["D5"] = 200
        mk["A6"] = dt.date(2026, 11, 5); mk["C6"] = 150; mk["D6"] = 200
        ds["B9"] = dt.date(2026, 11, 10)                                               # exam row → 4 days
        ds["B5"] = dt.date(2026, 10, 1)                                                # past → "over"
        wb.save(src)
        v = recalc(src, tmp)
        s, y, m, d = v["Start"], v["Syllabus"], v["Mocks"], v["Dates"]
        n = len(rows)
        check(s["B5"].value == 30, f"{eid}: days left {s['B5'].value} != 30")
        check(s["B6"].value == n, f"{eid}: topics {s['B6'].value} != {n}")
        check(s["B7"].value == 3, f"{eid}: done {s['B7'].value} != 3")
        check(s["B8"].value == round(3 / n * 100), f"{eid}: % done {s['B8'].value}")
        check(s["B9"].value == 2, f"{eid}: revisions due {s['B9'].value} != 2")
        check(s["B10"].value == 6, f"{eid}: study days {s['B10'].value} != 6")
        check(abs(s["B11"].value - (n - 3) / 20) <= 0.051, f"{eid}: pace {s['B11'].value}")
        check(s["B12"].value == 75, f"{eid}: best mock {s['B12'].value} != 75")
        check(m["E5"].value == 60, f"{eid}: mock % {m['E5'].value}")
        check(d["C9"].value == 4 and d["C5"].value == "over", f"{eid}: date countdown {d['C9'].value} / {d['C5'].value}")
        nxt = y["G8"].value
        check(nxt is not None and getattr(nxt, "date", lambda: nxt)() == dt.date(2026, 11, 6), f"{eid}: next revision G8 {nxt}")
        for ws in v.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str) and c.value.startswith("#"):
                        check(False, f"{eid}: error {c.value} in {ws.title}!{c.coordinate}")
        print(f"{eid}: {n} topics checked")

print("FAIL\n" + "\n".join(fails) if fails else f"PASS: {len(exams)} kits")
sys.exit(1 if fails else 0)

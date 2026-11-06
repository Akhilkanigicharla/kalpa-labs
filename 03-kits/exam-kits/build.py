#!/usr/bin/env python3
"""
A159: one engine for every Kalpa exam kit (Akhil, 6 Nov 2026: AP + Telangana state exams, teachers, banks, central government).
Reads exams/<id>.json and writes one Google-Sheets-ready .xlsx per exam:
  Start     : exam date (you type it), days left, syllabus % done, revisions due today, study days in the last 7 days
  Syllabus  : every topic with status, last studied, revisions done, next revision (spaced 1/3/7/21 days), resource link, notes
  Daily log : date, hours, what you studied, mock score
  Mocks     : date, paper, score, max, %
  Dates     : official dates you copy from the notice (notification, apply, admit card, exam, key, result) with days left
  Sources   : official site and the syllabus sources checked
Only Sheets-portable functions. Same look as the GATE kit (Kalpa palette).

  python3 03-kits/exam-kits/build.py [--outdir 03-kits/products] [--today 2026-11-06] [--only ssc-cgl]
"""
import argparse, datetime as dt, json, pathlib
from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

HERE = pathlib.Path(__file__).resolve().parent
HERO, GOLD, INK, MUTED, OK, BAD = "1D3A25", "C38E12", "1E2A1F", "5A6152", "2C7A43", "B13A2D"
INPUT = PatternFill("solid", fgColor="FFF6DD"); HEAD = PatternFill("solid", fgColor=HERO); BAND = PatternFill("solid", fgColor="E9E3D3")
thin = Side(style="thin", color="DCD5C3"); BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
STATUSES = ["Not started", "Learning", "Done"]
LOG_ROWS, MOCK_ROWS = 200, 60
DATE_EVENTS = ["Notification out", "Apply from", "Last date to apply", "Admit card", "Exam (prelims / tier 1 / paper)", "Answer key", "Result", "Next stage exam"]
# Telugu labels for AP/TG kits (to be read once by a native speaker before sale; see README).
TE = {"date": "మీ పరీక్ష తేదీ", "left": "మిగిలిన రోజులు", "done": "సిలబస్ పూర్తి", "due": "ఈరోజు రివిజన్", "week": "గత 7 రోజుల్లో చదివిన రోజులు"}


def load_exams(only=None):
    out = []
    for p in sorted((HERE / "exams").glob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        if not only or e["id"] == only:
            out.append(e)
    return out


def topics(exam):
    return [(p["name"], s["name"], t) for p in exam["papers"] for s in p["sections"] for t in s["topics"]]


def today_ref(pinned):
    return f"DATE({pinned.year},{pinned.month},{pinned.day})" if pinned else "TODAY()"


def head(ws, title, sub, width):
    ws.sheet_view.showGridLines = False
    ws["A1"] = title; ws["A1"].font = Font(bold=True, size=15, color="FFFFFF"); ws["A1"].fill = HEAD
    ws["A2"] = sub; ws["A2"].font = Font(italic=True, size=9, color=MUTED)
    for c in range(2, width + 1):
        ws.cell(row=1, column=c).fill = HEAD


def cols(ws, row, names, widths):
    for i, (n, w) in enumerate(zip(names, widths), start=1):
        c = ws.cell(row=row, column=i, value=n)
        c.font = Font(bold=True, color=INK); c.fill = BAND; c.border = BOX; c.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[c.column_letter].width = w


def build(exam, out, pinned=None):
    T = today_ref(pinned)
    te = "te" in exam.get("languages", [])
    rows = topics(exam)
    n = len(rows); first, last = 5, 4 + n
    wb = Workbook()

    # Syllabus first (Start refers to it)
    sy = wb.active; sy.title = "Syllabus"
    head(sy, f"{exam['name']}: syllabus tracker", "Yellow cells are yours. Next revision follows 1 → 3 → 7 → 21 days. Red = revise today.", 9)
    cols(sy, 4, ["Paper", "Section", "Topic", "Status", "Last studied", "Revisions done", "Next revision", "Video / free resource link", "Notes"],
         [26, 30, 52, 13, 13, 11, 14, 34, 24])
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=False); sy.add_data_validation(dv)
    for i, (paper, section, topic) in enumerate(rows):
        r = first + i
        sy.cell(row=r, column=1, value=paper); sy.cell(row=r, column=2, value=section); sy.cell(row=r, column=3, value=topic)
        sy.cell(row=r, column=4, value="Not started").fill = INPUT; dv.add(f"D{r}")
        sy.cell(row=r, column=5).fill = INPUT; sy.cell(row=r, column=5).number_format = "dd-mmm-yyyy"
        sy.cell(row=r, column=6, value=0).fill = INPUT
        sy.cell(row=r, column=7, value=f'=IF(E{r}="","",E{r}+CHOOSE(MIN(N(F{r}),3)+1,1,3,7,21))').number_format = "dd-mmm-yyyy"
        sy.cell(row=r, column=8).fill = INPUT; sy.cell(row=r, column=9).fill = INPUT
        for c in range(1, 10):
            sy.cell(row=r, column=c).border = BOX; sy.cell(row=r, column=c).alignment = Alignment(wrap_text=True, vertical="top")
    rng = f"A{first}:I{last}"
    sy.conditional_formatting.add(rng, FormulaRule(formula=[f'$D{first}="Done"'], fill=PatternFill("solid", fgColor="DDEFD9")))
    sy.conditional_formatting.add(rng, FormulaRule(formula=[f'AND($G{first}<>"",$G{first}<={T},$D{first}<>"Not started")'], font=Font(color=BAD, bold=True)))
    sy.freeze_panes = "D5"

    # Start (dashboard)
    st = wb.create_sheet("Start", 0)
    head(st, f"Kalpa Exam Kit · {exam['name']}" + (f" · {exam['name_te']}" if te else ""), f"{exam['family']} · {exam['body']} · official site: {exam['official_url']}", 3)
    st.column_dimensions["A"].width = 44; st.column_dimensions["B"].width = 20; st.column_dimensions["C"].width = 60
    lines = [
        ("Your exam date (type it)" + (f" / {TE['date']}" if te else ""), None, "Copy it from the official notice. Everything below counts down to it."),
        ("Days left" + (f" / {TE['left']}" if te else ""), f'=IF(B4="","",MAX(0,B4-{T}))', ""),
        ("Topics in the syllabus", f"=COUNTA(Syllabus!C{first}:C{last})", ""),
        ("Topics done", f'=COUNTIF(Syllabus!D{first}:D{last},"Done")', ""),
        ("Syllabus done %" + (f" / {TE['done']}" if te else ""), "=IF(B6=0,0,ROUND(B7/B6*100,0))", ""),
        ("Revisions due today" + (f" / {TE['due']}" if te else ""), f'=COUNTIFS(Syllabus!G{first}:G{last},"<="&{T},Syllabus!D{first}:D{last},"<>Not started")', "Red rows in Syllabus"),
        ("Study days in the last 7" + (f" / {TE['week']}" if te else ""), f"=COUNTIFS('Daily log'!A5:A{4+LOG_ROWS},\">=\"&({T}-6),'Daily log'!A5:A{4+LOG_ROWS},\"<=\"&{T},'Daily log'!B5:B{4+LOG_ROWS},\">0\")", "Aim for 6 of 7"),
        ("Topics needed per day to finish 10 days early", '=IF(OR(B4="",B5=""),"",IF(B5<=10,B6-B7,ROUND((B6-B7)/(B5-10),1)))', ""),
        ("Best mock %", f"=IF(COUNT(Mocks!E5:E{4+MOCK_ROWS})=0,\"\",MAX(Mocks!E5:E{4+MOCK_ROWS}))", ""),
    ]
    for i, (label, formula, note) in enumerate(lines):
        r = 4 + i
        st.cell(row=r, column=1, value=label).font = Font(bold=True, color=INK)
        c = st.cell(row=r, column=2, value=formula)
        if formula is None:
            c.fill = INPUT; c.number_format = "dd-mmm-yyyy"
        st.cell(row=r, column=3, value=note).font = Font(size=9, color=MUTED)
        for col in (1, 2, 3):
            st.cell(row=r, column=col).border = BOX
    st["A15"] = "Exam pattern"; st["A15"].font = Font(bold=True, color=HERO)
    st["A16"] = exam["pattern"]; st["A16"].alignment = Alignment(wrap_text=True); st.merge_cells("A16:C17"); st.row_dimensions[16].height = 45
    st["A19"] = "Not affiliated with the exam body. Always confirm dates and syllabus on the official site."; st["A19"].font = Font(italic=True, size=9, color=MUTED)

    # Daily log
    lg = wb.create_sheet("Daily log")
    head(lg, "Daily log", "One row per day. Hours > 0 counts as a study day.", 4)
    cols(lg, 4, ["Date", "Hours", "What I studied", "Mock score (if any)"], [14, 9, 60, 16])
    for r in range(5, 5 + LOG_ROWS):
        for c in range(1, 5):
            lg.cell(row=r, column=c).fill = INPUT; lg.cell(row=r, column=c).border = BOX
        lg.cell(row=r, column=1).number_format = "dd-mmm-yyyy"

    # Mocks
    mk = wb.create_sheet("Mocks")
    head(mk, "Mock tests", "Use any free or paid mock. % is worked out for you.", 5)
    cols(mk, 4, ["Date", "Paper / mock name", "Score", "Max marks", "%"], [14, 34, 10, 11, 9])
    for r in range(5, 5 + MOCK_ROWS):
        for c in range(1, 5):
            mk.cell(row=r, column=c).fill = INPUT; mk.cell(row=r, column=c).border = BOX
        mk.cell(row=r, column=1).number_format = "dd-mmm-yyyy"
        mk.cell(row=r, column=5, value=f'=IF(OR(C{r}="",N(D{r})=0),"",ROUND(C{r}/D{r}*100,1))').border = BOX

    # Dates & alerts
    dt_ = wb.create_sheet("Dates")
    head(dt_, "Official dates", f"Copy each date from the official notice on {exam['official_url']}. Days left updates itself.", 4)
    cols(dt_, 4, ["Event", "Date", "Days left", "Official notice link"], [34, 14, 11, 50])
    for i, ev in enumerate(DATE_EVENTS):
        r = 5 + i
        dt_.cell(row=r, column=1, value=ev).border = BOX
        c = dt_.cell(row=r, column=2); c.fill = INPUT; c.border = BOX; c.number_format = "dd-mmm-yyyy"
        dt_.cell(row=r, column=3, value=f'=IF(B{r}="","",IF(B{r}<{T},"over",B{r}-{T}))').border = BOX
        d = dt_.cell(row=r, column=4, value=exam["official_url"]); d.fill = INPUT; d.border = BOX
    dt_.conditional_formatting.add("A5:D12", FormulaRule(formula=[f'AND(ISNUMBER($C5),$C5<=7)'], font=Font(color=BAD, bold=True)))

    # Sources
    so = wb.create_sheet("Sources")
    head(so, "Sources", f"Syllabus checked on {exam['checked']}. Official site wins if anything differs.", 2)
    cols(so, 4, ["No.", "Source"], [5, 90])
    for i, s in enumerate(exam["sources"], start=1):
        so.cell(row=4 + i, column=1, value=i); so.cell(row=4 + i, column=2, value=s)

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def filename(exam):
    return f"Kalpa-Exam-Kit-{exam['id']}.xlsx"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(HERE.parent / "products"))
    ap.add_argument("--today"); ap.add_argument("--only")
    a = ap.parse_args()
    pinned = dt.date.fromisoformat(a.today) if a.today else None
    for e in load_exams(a.only):
        p = build(e, pathlib.Path(a.outdir) / filename(e), pinned)
        print(f"{e['id']}: {len(topics(e))} topics → {p}")


if __name__ == "__main__":
    main()

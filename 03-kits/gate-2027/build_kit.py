#!/usr/bin/env python3
"""
A19 / K-02: GATE 2027 Final-120-Days Tracker, CS paper (v1). One builder, three files:
  Lite (free, view-only): countdown + syllabus checklist
  Kit (₹199): + daily log with streak, spaced revision (1/3/7/21 days), weekly plan
  Pro (₹299): + subject weights (GATE 2023–25 marks, published analysis, cited) + mock analyser + Telugu/Hindi tab
Only Sheets-portable functions (IF/AND/OR/MAX/MIN/SUM/SUMIF/COUNTIF/COUNTIFS/INDEX/MATCH/CHOOSE/TODAY/ROUND).

  python3 03-kits/gate-2027/build_kit.py [--outdir 03-kits/products] [--today 2026-10-16]   (--today pins TODAY() for tests)

Sources (checked 16 Oct 2026):
  · Dates 6, 7, 13, 14, 20, 21 Feb 2027; IIT Madras organises; syllabus revised for 2027 (IIT Madras press release).
  · CS 2027 changes (Digital Logic, COA, Networks; ARP/DHCP/ICMP and the OSI stack removed; Application layer = DNS + HTTP;
    cache mapping and hardwired/microprogrammed control added): reported by aspirantmitraa.com. QA item 3 re-checks the
    official syllabus PDF on gate2027.iitm.ac.in before launch.
  · Subject marks 2023 / 2024 / 2025-avg: GO Classes analysis (goclasses.in). Engineering Mathematics 10 / 13 / 12.
"""
import argparse, datetime as dt, pathlib
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule

HERO, GOLD, MADDER, INK, MUTED, OK, BAD = "1C2463", "D3940A", "B23A2C", "191C33", "5D6079", "23804F", "C0392B"
INPUT = PatternFill("solid", fgColor="FFF6DD"); HEAD = PatternFill("solid", fgColor=HERO); BAND = PatternFill("solid", fgColor="E6E6F1")
thin = Side(style="thin", color="DCDBE7"); BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
EXAM_DAYS = ["2027-02-06", "2027-02-07", "2027-02-13", "2027-02-14", "2027-02-20", "2027-02-21"]
STATUSES = ["Not started", "Learning", "Done"]

# Subjects with 2023 / 2024 / 2025-avg marks (GO Classes) and the CS 2027 subtopics (2027 changes applied).
SUBJECTS = [
    ("Engineering Mathematics", (10, 13, 12), ["Discrete Mathematics: propositional and first-order logic", "Sets, relations, functions, partial orders, lattices",
        "Monoids, groups", "Graphs: connectivity, matching, colouring", "Combinatorics: counting, recurrences, generating functions",
        "Linear Algebra: matrices, determinants, systems of linear equations", "Eigenvalues and eigenvectors, LU decomposition",
        "Calculus: limits, continuity, differentiability, maxima and minima, mean value theorem, integration",
        "Probability: random variables, uniform, normal, exponential, Poisson, binomial", "Mean, median, mode, standard deviation; conditional probability, Bayes"]),
    ("Digital Logic", (6, 5, 6), ["Boolean algebra", "Combinational circuits", "Sequential circuits", "Minimisation", "Number representations and computer arithmetic (fixed and floating point)"]),
    ("Computer Organization and Architecture", (12, 9, 8), ["Machine instructions and addressing modes", "ALU, data-path and control unit",
        "Hardwired control design (2027)", "Microprogrammed control design (2027)", "Instruction pipelining, pipeline hazards",
        "Memory hierarchy: cache memory", "Cache memory mapping (2027)", "I/O interface (interrupt and DMA mode)"]),
    ("Programming and Data Structures", (11, 8, 10), ["Programming in C", "Recursion", "Arrays, stacks, queues", "Linked lists", "Trees, binary search trees, binary heaps", "Graphs"]),
    ("Algorithms", (6, 8, 8), ["Searching, sorting, hashing", "Asymptotic worst-case time and space complexity", "Greedy", "Divide-and-conquer", "Dynamic programming",
        "Graph traversals, minimum spanning trees, shortest paths"]),
    ("Theory of Computation", (9, 7, 9), ["Regular expressions and finite automata", "Context-free grammars and push-down automata",
        "Regular and context-free languages, pumping lemma", "Turing machines and undecidability"]),
    ("Compiler Design", (5, 8, 5), ["Lexical analysis, parsing, syntax-directed translation", "Runtime environments", "Intermediate code generation",
        "Local optimisation", "Data flow analyses: constant propagation, liveness analysis, common subexpression elimination"]),
    ("Operating System", (7, 10, 8), ["System calls, processes, threads, inter-process communication", "Concurrency and synchronisation", "Deadlock",
        "CPU and I/O scheduling", "Memory management and virtual memory", "File systems"]),
    ("Databases", (5, 8, 8), ["ER-model", "Relational model: relational algebra, tuple calculus, SQL", "Integrity constraints, normal forms",
        "File organisation, indexing (B and B+ trees)", "Transactions and concurrency control"]),
    ("Computer Networks", (8, 9, 8), ["Packet, circuit and virtual circuit switching", "Data link layer: framing, error detection, MAC, Ethernet bridging",
        "Routing protocols: shortest path, flooding, distance vector, link state", "Fragmentation and IP addressing, IPv4, CIDR notation",
        "Transport layer: flow control and congestion control, UDP, TCP, sockets", "Application layer: DNS, HTTP (2027: only these two)"]),
    ("General Aptitude", (15, 15, 15), ["Verbal aptitude", "Quantitative aptitude", "Analytical aptitude", "Spatial aptitude"]),
]


def style_head(ws, title, sub, width=6):
    ws["A1"] = title; ws["A1"].font = Font(name="Arial", size=16, bold=True, color="FFFFFF")
    ws["A2"] = sub; ws["A2"].font = Font(name="Arial", size=10, color="B9BDE0")
    for r in (1, 2):
        for c in range(1, width + 1): ws.cell(r, c).fill = HEAD
    ws.sheet_view.showGridLines = False


def hdr(ws, row, names, widths):
    for i, (n, w) in enumerate(zip(names, widths), 1):
        c = ws.cell(row, i, n); c.font = Font(name="Arial", bold=True, color="FFFFFF"); c.fill = HEAD; c.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[c.column_letter].width = w


def today_ref(pinned):
    return f'DATE({pinned.year},{pinned.month},{pinned.day})' if pinned else "TODAY()"


def build(tier, out, pinned=None):
    assert tier in ("lite", "kit", "pro")
    T = today_ref(pinned)
    wb = Workbook()
    # ---------------- Start
    st = wb.active; st.title = "Start"; style_head(st, "GATE 2027 · CS · Final-120-Days Tracker", f"Kalpa Labs · {tier.capitalize()} v1.0 · {'free' if tier == 'lite' else 'personal licence'}")
    st.column_dimensions["A"].width = 100
    lines = ["How to use", "1. Plan tab: pick your exam date (it will be on your admit card). The countdown and plan update every day.",
             "2. Syllabus tab: mark each topic Not started / Learning / Done." + (" When you mark Done, type the date: revision dates appear (1, 3, 7, 21 days)." if tier != "lite" else ""),
             ]
    if tier != "lite":
        lines += ["3. Daily log tab: type the hours you studied each day. Your streak counts itself.", "4. Week tab: your hours this week and what's due for revision."]
    if tier == "pro":
        lines += ["5. Mocks tab: after each mock, count careless mistakes and concept mistakes per subject. The sheet shows where marks leak.",
                  "6. Subject weights are average marks from GATE 2023–2025 (published analysis, cited on the Sources tab). Use them to prioritise, not to skip subjects."]
    lines += ["", "Not an official GATE product. Dates and syllabus: gate2027.iitm.ac.in. Yellow cells are yours; don't type over white ones.",
              "Kalpa Labs · Udyam UDYAM-TS-02-0382711 · aakhiil51458@gmail.com"]
    for i, t in enumerate(lines, 4):
        st[f"A{i}"] = t; st[f"A{i}"].font = Font(name="Arial", size=11, bold=(t == "How to use"), color=HERO if t == "How to use" else INK)
        st[f"A{i}"].alignment = Alignment(wrap_text=True)

    # ---------------- Plan (countdown)
    pl = wb.create_sheet("Plan"); style_head(pl, "Countdown and plan", "Exam days: 6, 7, 13, 14, 20, 21 Feb 2027 (IIT Madras)", 4)
    pl.column_dimensions["A"].width = 40; pl.column_dimensions["B"].width = 22
    pl["A4"] = "My exam date"; pl["B4"] = dt.date(2027, 2, 6); pl["B4"].fill = INPUT; pl["B4"].number_format = "dd mmm yyyy"; pl["B4"].border = BOX
    dvd = DataValidation(type="date", operator="between", formula1="DATE(2027,2,6)", formula2="DATE(2027,2,21)", showErrorMessage=True,
                         errorTitle="GATE 2027 dates", error="GATE 2027 is on 6, 7, 13, 14, 20 or 21 Feb 2027"); pl.add_data_validation(dvd); dvd.add("B4")
    pl["A5"] = "Today"; pl["B5"] = f"={T}"; pl["B5"].number_format = "dd mmm yyyy"
    pl["A6"] = "Days left"; pl["B6"] = "=MAX(0,B4-B5)"; pl["B6"].font = Font(name="Arial", size=22, bold=True, color=MADDER)
    pl["A7"] = "Topics done"; pl["B7"] = '=COUNTIF(Syllabus!C:C,"Done")&" of "&COUNTA(Syllabus!B5:B200)'
    pl["A8"] = "Syllabus done"; pl["B8"] = '=IF(COUNTA(Syllabus!B5:B200)=0,0,COUNTIF(Syllabus!C:C,"Done")/COUNTA(Syllabus!B5:B200))'; pl["B8"].number_format = "0%"
    if tier != "lite":
        pl["A9"] = "Hours I can study a day"; pl["B9"] = 5; pl["B9"].fill = INPUT; pl["B9"].border = BOX
        pl["A10"] = "Topics left ÷ days left (topics a day)"; pl["B10"] = '=IF(B6=0,0,ROUND((COUNTA(Syllabus!B5:B200)-COUNTIF(Syllabus!C:C,"Done"))/B6,2))'
        pl["A11"] = "Current streak (days)"; pl["B11"] = "='Daily log'!F3"; pl["B11"].font = Font(name="Arial", size=18, bold=True, color=OK)
        pl["A12"] = "Revisions due today or overdue"; pl["B12"] = f'=COUNTIFS(Syllabus!F5:F200,"<="&{T},Syllabus!C5:C200,"Done")'
    for r in range(4, 13):
        pl[f"A{r}"].font = Font(name="Arial", bold=True)

    # ---------------- Syllabus
    sy = wb.create_sheet("Syllabus")
    cols = ["Subject", "Topic", "Status", "Done on", "Revisions done", "Next revision", "Due?"] + (["Subject weight (avg marks)", "My confidence 1–5"] if tier == "pro" else [])
    style_head(sy, "Syllabus checklist · GATE 2027 CS", "Revised syllabus applied (2027 changes marked) · check gate2027.iitm.ac.in", len(cols))
    hdr(sy, 4, cols, [28, 58, 14, 13, 11, 14, 9, 14, 12][:len(cols)])
    sdv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True); sy.add_data_validation(sdv)
    r = 5
    for subj, marks, topics in SUBJECTS:
        for t in topics:
            sy[f"A{r}"] = subj; sy[f"B{r}"] = t; sy[f"C{r}"] = "Not started"; sy[f"C{r}"].fill = INPUT; sdv.add(f"C{r}")
            if tier == "lite":
                for c in "DEFG": sy[f"{c}{r}"] = None
            else:
                sy[f"D{r}"].fill = INPUT; sy[f"D{r}"].number_format = "dd mmm"; sy[f"E{r}"] = 0; sy[f"E{r}"].fill = INPUT
                # spaced revision: 1, 3, 7, 21 days after the last review (Done date + gap for the next revision number)
                sy[f"F{r}"] = f'=IF(AND(C{r}="Done",ISNUMBER(D{r}),E{r}<4),D{r}+CHOOSE(E{r}+1,1,3,7,21),"")'; sy[f"F{r}"].number_format = "dd mmm"
                sy[f"G{r}"] = f'=IF(F{r}="","",IF(F{r}<={T},"Revise","Later"))'
            if tier == "pro":
                sy[f"H{r}"] = f"=ROUND(INDEX(Sources!$E$6:$E$16,MATCH(A{r},Sources!$A$6:$A$16,0)),1)"
                sy[f"I{r}"] = 3; sy[f"I{r}"].fill = INPUT
            if (r % 2) == 0:
                for c in "AB": sy[f"{c}{r}"].fill = BAND
            r += 1
    last = r - 1
    sy.conditional_formatting.add(f"C5:C{last}", CellIsRule(operator="equal", formula=['"Done"'], font=Font(color=OK, bold=True)))
    if tier != "lite":
        sy.conditional_formatting.add(f"G5:G{last}", CellIsRule(operator="equal", formula=['"Revise"'], font=Font(color=BAD, bold=True)))
        sy[f"A{last + 2}"] = "When you revise a topic, add 1 to 'Revisions done' and type today's date in 'Done on'. After 4 revisions it's off the list."
        sy[f"A{last + 2}"].font = Font(name="Arial", size=10, color=MUTED)
    sy.freeze_panes = "C5"

    if tier != "lite":
        # ---------------- Daily log: 120 days before the exam → exam day, streak counts itself
        lg = wb.create_sheet("Daily log"); style_head(lg, "Daily log", "Type the hours you studied · the streak counts consecutive days with hours > 0", 6)
        hdr(lg, 5, ["Date", "Hours", "Subject (optional)", "Questions solved", "Streak"], [14, 9, 28, 14, 9])
        lg["E3"] = "Current streak"; lg["E3"].font = Font(name="Arial", bold=True)
        for k in range(121):
            r2 = 6 + k
            lg[f"A{r2}"] = f"=Plan!$B$4-{120 - k}"; lg[f"A{r2}"].number_format = "ddd dd mmm"
            lg[f"B{r2}"].fill = INPUT; lg[f"C{r2}"].fill = INPUT; lg[f"D{r2}"].fill = INPUT
            lg[f"E{r2}"] = f'=IF(N(B{r2})>0,{"1" if k == 0 else f"E{r2 - 1}+1"},0)'
        # streak = value on today's row, or yesterday's if today isn't logged yet
        m = f"MATCH({T},A6:A126,0)"
        lg["F3"] = f'=IFERROR(IF(N(INDEX(B6:B126,{m}))>0,INDEX(E6:E126,{m}),IF({m}>1,INDEX(E6:E126,{m}-1),0)),0)'
        lg["F3"].font = Font(name="Arial", size=16, bold=True, color=OK)
        lg["A3"] = "Total hours"; lg["B3"] = "=SUM(B6:B126)"; lg["A3"].font = Font(name="Arial", bold=True)
        # ---------------- Week
        wk = wb.create_sheet("Week"); style_head(wk, "This week", "Monday to Sunday of the current week", 3)
        wk.column_dimensions["A"].width = 38; wk.column_dimensions["B"].width = 16
        wk["A4"] = "Week starts"; wk["B4"] = f"={T}-WEEKDAY({T},3)"; wk["B4"].number_format = "ddd dd mmm"
        wk["A5"] = "Hours studied this week"; wk["B5"] = "=SUMIFS('Daily log'!B6:B126,'Daily log'!A6:A126,\">=\"&B4,'Daily log'!A6:A126,\"<\"&B4+7)"
        wk["A6"] = "Target hours this week"; wk["B6"] = "=Plan!B9*7"
        wk["A7"] = "Revisions due by Sunday"; wk["B7"] = "=COUNTIFS(Syllabus!F5:F200,\"<\"&B4+7,Syllabus!C5:C200,\"Done\")"
        wk["A8"] = "Topics still not started"; wk["B8"] = '=COUNTIF(Syllabus!C5:C200,"Not started")'
        for rr in range(4, 9): wk[f"A{rr}"].font = Font(name="Arial", bold=True)

    if tier == "pro":
        # ---------------- Mocks
        mk = wb.create_sheet("Mocks"); style_head(mk, "Mock analyser", "After each mock: score, then careless vs concept mistakes per subject", 8)
        mk["A4"] = "Mocks"; mk["A4"].font = Font(name="Arial", bold=True)
        hdr(mk, 5, ["Mock", "Date", "Score /100"], [30, 13, 11])
        for i in range(1, 21):
            mk[f"A{5 + i}"] = f"Mock {i}"; mk[f"B{5 + i}"].fill = INPUT; mk[f"B{5 + i}"].number_format = "dd mmm"; mk[f"C{5 + i}"].fill = INPUT
        mk["E4"] = "Best"; mk["F4"] = "=MAX(C6:C25)"; mk["E5"] = "Average"; mk["F5"] = '=IFERROR(ROUND(AVERAGE(C6:C25),1),"")'
        mk["E6"] = "Last 3 average"; mk["F6"] = '=IFERROR(ROUND(AVERAGE(INDEX(C6:C25,MAX(1,COUNT(C6:C25)-2)):INDEX(C6:C25,MAX(1,COUNT(C6:C25)))),1),"")'
        top = 28
        hdr(mk, top, ["Subject", "Careless mistakes (total)", "Concept mistakes (total)", "Marks lost (approx)", "Weight", "Fix first?"], [30, 14, 14, 13, 9, 12])
        for i, (subj, *_rest) in enumerate(SUBJECTS):
            rr = top + 1 + i
            mk[f"A{rr}"] = subj; mk[f"B{rr}"] = 0; mk[f"C{rr}"] = 0; mk[f"B{rr}"].fill = INPUT; mk[f"C{rr}"].fill = INPUT
            mk[f"D{rr}"] = f"=ROUND((B{rr}+C{rr})*1.5,1)"  # GATE questions are 1 or 2 marks: 1.5 on average
            mk[f"E{rr}"] = f"=INDEX(Sources!$E$6:$E$16,MATCH(A{rr},Sources!$A$6:$A$16,0))"
            mk[f"F{rr}"] = f'=IF(B{rr}+C{rr}=0,"",IF(C{rr}>B{rr},"Re-learn","Slow down"))'
        end = top + len(SUBJECTS)
        mk[f"A{end + 2}"] = "Totals"; mk[f"B{end + 2}"] = f"=SUM(B{top + 1}:B{end})"; mk[f"C{end + 2}"] = f"=SUM(C{top + 1}:C{end})"
        mk[f"A{end + 3}"] = "Biggest leak"; mk[f"B{end + 3}"] = f'=IF(SUM(D{top + 1}:D{end})=0,"",INDEX(A{top + 1}:A{end},MATCH(MAX(D{top + 1}:D{end}),D{top + 1}:D{end},0)))'
        mk[f"A{end + 4}"] = '"Careless" = you knew it but slipped (re-read, units, options). "Concept" = you didn\'t know it: re-learn the topic.'
        for rr in (end + 2, end + 3): mk[f"A{rr}"].font = Font(name="Arial", bold=True)
        # ---------------- Telugu + Hindi instructions
        th = wb.create_sheet("తెలుగు · हिंदी"); style_head(th, "సూచనలు · निर्देश", "Telugu and Hindi instructions", 1)
        th.column_dimensions["A"].width = 100
        tl = ["తెలుగు", "1. Plan ట్యాబ్: మీ పరీక్ష తేదీ ఎంచుకోండి. రోజులు, ప్లాన్ ప్రతిరోజూ మారుతాయి.",
              "2. Syllabus ట్యాబ్: ప్రతి టాపిక్‌కి Not started / Learning / Done గుర్తు పెట్టండి. Done అయితే తేదీ రాయండి: 1, 3, 7, 21 రోజుల తర్వాత రివిజన్ తేదీలు వస్తాయి.",
              "3. Daily log: రోజూ ఎన్ని గంటలు చదివారో రాయండి. స్ట్రీక్ దానంతట అదే లెక్కిస్తుంది.",
              "4. Mocks: ప్రతి మాక్ తర్వాత, అజాగ్రత్త తప్పులు, కాన్సెప్ట్ తప్పులు సబ్జెక్ట్ వారీగా రాయండి.", "",
              "हिंदी", "1. Plan टैब: अपनी परीक्षा की तारीख चुनें। बचे हुए दिन और प्लान रोज़ अपने आप बदलते हैं।",
              "2. Syllabus टैब: हर टॉपिक पर Not started / Learning / Done चुनें। Done होने पर तारीख लिखें: 1, 3, 7, 21 दिन बाद रिविज़न की तारीखें दिखेंगी।",
              "3. Daily log: रोज़ कितने घंटे पढ़ा, लिखें। स्ट्रीक अपने आप गिनी जाती है।",
              "4. Mocks: हर मॉक के बाद, लापरवाही की गलतियाँ और कॉन्सेप्ट की गलतियाँ विषय के हिसाब से लिखें।"]
        for i, t in enumerate(tl, 4):
            th[f"A{i}"] = t; th[f"A{i}"].alignment = Alignment(wrap_text=True); th[f"A{i}"].font = Font(name="Arial", size=12, bold=t in ("తెలుగు", "हिंदी"))

    # ---------------- Sources (and the weight table the Pro tabs read)
    so = wb.create_sheet("Sources"); style_head(so, "Sources and weights", "Checked 16 Oct 2026", 5)
    hdr(so, 5, ["Subject", "2023 marks", "2024 marks", "2025 marks (avg)", "Average"], [36, 11, 11, 15, 10])
    for i, (subj, (a, b, c), _t) in enumerate(SUBJECTS, 6):
        so[f"A{i}"] = subj; so[f"B{i}"] = a; so[f"C{i}"] = b; so[f"D{i}"] = c; so[f"E{i}"] = f"=ROUND(AVERAGE(B{i}:D{i}),1)"
    src = ["Exam dates and organising institute: IIT Madras press release, iitm.ac.in (GATE 2027: 6, 7, 13, 14, 20, 21 Feb 2027; syllabus revised for 2027).",
           "CS 2027 syllabus changes: aspirantmitraa.com summary; the official syllabus is on gate2027.iitm.ac.in (always check it).",
           "Subject marks 2023–2025: GO Classes, 'A Strategic Analysis of Subject-wise Weightage Trends in GATE CSE (2023-2025)'. Engineering Mathematics 10 / 13 / 12; General Aptitude 15 every year.",
           "Weights guide your time; any subject can carry more marks in 2027."]
    for i, t in enumerate(src, 19):
        so[f"A{i}"] = t; so[f"A{i}"].alignment = Alignment(wrap_text=True); so.merge_cells(f"A{i}:E{i}"); so.row_dimensions[i].height = 32
    if tier != "pro":  # Lite/Kit: keep the dates + syllabus sources, drop the weight table (a Pro feature)
        for rr in range(5, 17):
            for c in "ABCDE": so[f"{c}{rr}"] = None; so[f"{c}{rr}"].fill = PatternFill()
    wb.properties.title = f"GATE 2027 CS Tracker ({tier})"; wb.properties.creator = "Kalpa Labs"
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True); wb.save(out)
    return out


FILES = {"lite": "Kalpa-GATE-2027-CS-Lite.xlsx", "kit": "Kalpa-GATE-2027-CS-Kit.xlsx", "pro": "Kalpa-GATE-2027-CS-Pro.xlsx"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--outdir", default=str(pathlib.Path(__file__).resolve().parent.parent / "products"))
    ap.add_argument("--today", help="pin TODAY() (tests only)"); a = ap.parse_args()
    pin = dt.date.fromisoformat(a.today) if a.today else None
    for t, f in FILES.items(): print(build(t, pathlib.Path(a.outdir) / f, pin))

#!/usr/bin/env python3
"""
A20 / K-08: Salary Tax-Regime + SIP Goal Planner 2026-27 (Kit tier, ₹199). Builds an .xlsx that imports into Google
Sheets as-is (only IF/MIN/MAX/ROUND/SUMPRODUCT/CHOOSE/MATCH/PMT/INDEX: no LET/LAMBDA/array-only functions).

  python3 03-kits/tax-sip/build_kit.py [--out 03-kits/products/Kalpa-Tax-SIP-Planner-2026-27.xlsx] [--extra cases.json]

Rules = the calculator site's tested engine (05-deals/site/src/lib/fin.ts): tax year 2026-27 under the Income-tax Act
2025, new regime slabs 0/5/10/15/20/25/30 with the ₹12 lakh rebate + marginal relief, ₹75,000 / ₹50,000 standard
deduction, old regime by age band, 4% cess, rounding to ₹10. Surcharge (income above ₹50 lakh) is NOT included: the
sheet says so instead of guessing. Every tax formula comes from one function, so the Tax tab and the in-sheet
Self-check tab can't drift apart. test_kit.py recalculates the real file in LibreOffice and compares with fin.ts.
"""
import argparse, json, pathlib
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule

HERO, GOLD, MADDER, INK, MUTED, SOFT, PANEL, OK, BAD = "1C2463", "D3940A", "B23A2C", "191C33", "5D6079", "E6E6F1", "FBFBFD", "23804F", "C0392B"
INPUT = PatternFill("solid", fgColor="FFF6DD")       # turmeric tint = "type here"
HEAD = PatternFill("solid", fgColor=HERO)
BAND = PatternFill("solid", fgColor=SOFT)
thin = Side(style="thin", color="DCDBE7")
BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
RS = "#,##0"             # rupee number format (₹ shown in labels; Indian lakh grouping isn't portable between Excel and Sheets)
AGES = ["Below 60", "60 to 80", "80 and above"]


def head(ws, title, sub):
    ws["A1"] = title; ws["A1"].font = Font(name="Arial", size=16, bold=True, color="FFFFFF"); ws["A1"].fill = HEAD
    ws["A2"] = sub; ws["A2"].font = Font(name="Arial", size=10, color="B9BDE0"); ws["A2"].fill = HEAD
    for c in "BCDEF":
        ws[f"{c}1"].fill = HEAD; ws[f"{c}2"].fill = HEAD
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 46
    for c in "BCDEF": ws.column_dimensions[c].width = 18


def label(ws, cell, text, bold=False, color=INK):
    ws[cell] = text; ws[cell].font = Font(name="Arial", size=11, bold=bold, color=color); ws[cell].alignment = Alignment(wrap_text=True, vertical="center")


def inp(ws, cell, value, fmt=RS):
    ws[cell] = value; ws[cell].fill = INPUT; ws[cell].number_format = fmt; ws[cell].border = BOX; ws[cell].font = Font(name="Arial", size=11, bold=True)


def out(ws, cell, formula, fmt=RS, bold=False):
    ws[cell] = formula; ws[cell].number_format = fmt; ws[cell].border = BOX; ws[cell].font = Font(name="Arial", size=11, bold=bold)


# ---------------------------------------------------------------- the one place tax formulas are written
def tax_formulas(gross, ded, age):
    """Formulas for one person. gross/ded/age are cell references. Returns {key: (new, old)}."""
    t_new = f"MAX(0,ROUND(({gross}-Rules!$B$4)/10,0)*10)"
    t_old = f"MAX(0,ROUND(({gross}-Rules!$C$4-{ded})/10,0)*10)"
    slab = lambda t, lo, d: f"SUMPRODUCT(({t}>{lo})*({t}-{lo})*{d})"
    s_new = slab("{T}", "Rules!$A$9:$A$15", "Rules!$C$9:$C$15")
    s_old = ("CHOOSE(MATCH({A},Rules!$A$27:$A$29,0)," + ",".join(slab("{T}", f"Rules!${c}$19:${c}$22", f"Rules!${d}$19:${d}$22") for c, d in (("A", "B"), ("C", "D"), ("E", "F"))) + ")").replace("{A}", age)
    return {"taxable": (t_new, t_old), "slab": (s_new, s_old)}


def tax_block(ws, r, gross, ded, age):
    """Writes taxable/slab/rebate/after/cess/total/monthly for New (col B) and Old (col C) from row r. Returns row map."""
    f = tax_formulas(gross, ded, age); rows = {}
    names = [("Standard deduction (₹)", "std"), ("Taxable income (₹, rounded to ₹10)", "taxable"), ("Tax on slabs (₹)", "slab"),
             ("Rebate u/s 156, ex-87A, with marginal relief (₹)", "rebate"), ("Tax after rebate (₹)", "after"),
             ("Health and education cess, 4% (₹)", "cess"), ("Total tax for the year (₹)", "total"), ("Per month (₹)", "monthly")]
    for i, (text, key) in enumerate(names):
        rows[key] = r + i; label(ws, f"A{r + i}", text, bold=key == "total")
    R = rows
    out(ws, f"B{R['std']}", "=Rules!$B$4"); out(ws, f"C{R['std']}", "=Rules!$C$4")
    out(ws, f"B{R['taxable']}", "=" + f["taxable"][0]); out(ws, f"C{R['taxable']}", "=" + f["taxable"][1])
    out(ws, f"B{R['slab']}", "=" + f["slab"][0].replace("{T}", f"B{R['taxable']}")); out(ws, f"C{R['slab']}", "=" + f["slab"][1].replace("{T}", f"C{R['taxable']}"))
    out(ws, f"B{R['rebate']}", f"=IF(B{R['taxable']}<=Rules!$B$5,MIN(B{R['slab']},Rules!$B$6),MAX(0,B{R['slab']}-(B{R['taxable']}-Rules!$B$5)))")
    out(ws, f"C{R['rebate']}", f"=IF(C{R['taxable']}<=Rules!$C$5,MIN(C{R['slab']},Rules!$C$6),0)")
    for c in "BC":
        out(ws, f"{c}{R['after']}", f"={c}{R['slab']}-{c}{R['rebate']}")
        out(ws, f"{c}{R['cess']}", f"={c}{R['after']}*Rules!$B$7")
        out(ws, f"{c}{R['total']}", f"=ROUND(({c}{R['after']}+{c}{R['cess']})/10,0)*10", bold=True)
        out(ws, f"{c}{R['monthly']}", f"=ROUND({c}{R['total']}/12,0)")
    return R


def rules_sheet(wb):
    ws = wb.create_sheet("Rules"); head(ws, "Rules used (tax year 2026-27)", "Income-tax Act 2025 · checked 16 Oct 2026 · don't edit unless the law changes")
    label(ws, "A3", "", bold=True); ws["B3"] = "New regime"; ws["C3"] = "Old regime"
    for c in ("B3", "C3"): ws[c].font = Font(name="Arial", bold=True)
    rows = [("Standard deduction for salaried (₹)", 75000, 50000), ("Rebate: taxable income up to (₹)", 1200000, 500000),
            ("Rebate: maximum (₹)", 60000, 12500), ("Cess", 0.04, 0.04)]
    for i, (t, n, o) in enumerate(rows, 4):
        label(ws, f"A{i}", t); ws[f"B{i}"] = n; ws[f"C{i}"] = o
        ws[f"B{i}"].number_format = ws[f"C{i}"].number_format = "0%" if t == "Cess" else RS
    label(ws, "A8", "New regime slabs: from (₹) · rate · rate step", bold=True)
    new = [(0, 0), (400000, .05), (800000, .10), (1200000, .15), (1600000, .20), (2000000, .25), (2400000, .30)]
    for i, (lo, rate) in enumerate(new, 9):
        ws[f"A{i}"] = lo; ws[f"B{i}"] = rate; ws[f"C{i}"] = rate - (new[i - 10][1] if i > 9 else 0)
        ws[f"A{i}"].number_format = RS; ws[f"B{i}"].number_format = ws[f"C{i}"].number_format = "0%"
    label(ws, "A17", "Old regime slabs by age: from (₹) · rate step", bold=True)
    for col, (name, sl) in zip(("A", "C", "E"), [("Below 60", [(0, 0), (250000, .05), (500000, .20), (1000000, .30)]),
                                                  ("60 to 80", [(0, 0), (300000, .05), (500000, .20), (1000000, .30)]),
                                                  ("80 and above", [(0, 0), (500000, .20), (1000000, .30), (10 ** 15, .30)])]):
        ws[f"{col}18"] = name; ws[f"{col}18"].font = Font(name="Arial", bold=True)
        nxt = chr(ord(col) + 1)
        for i, (lo, rate) in enumerate(sl, 19):
            ws[f"{col}{i}"] = lo; ws[f"{nxt}{i}"] = rate - (sl[i - 20][1] if i > 19 else 0)
            ws[f"{col}{i}"].number_format = RS; ws[f"{nxt}{i}"].number_format = "0%"
    label(ws, "A26", "Age bands (for the drop-down)", bold=True)
    for i, a in enumerate(AGES, 27): ws[f"A{i}"] = a
    label(ws, "A31", "HRA: metro cities that get the 50% limit (2026-27)", bold=True)
    for i, c in enumerate(["Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Hyderabad", "Pune", "Ahmedabad", "Other city"], 32): ws[f"A{i}"] = c
    label(ws, "A42", "Sources: Finance Bill 2026 memorandum (no change in rates); incometaxindia.gov.in tax rates; Income-tax Act 2025. Surcharge above ₹50 lakh is not included in this kit.", color=MUTED)
    return ws


def tax_sheet(wb):
    ws = wb.create_sheet("Tax", 1); head(ws, "Old vs new regime · 2026-27", "Salaried, resident · yellow cells are yours to fill · everything else calculates")
    label(ws, "A4", "Gross salary for the year (₹)", bold=True); inp(ws, "B4", 1300000)
    label(ws, "A5", "Your age band", bold=True); inp(ws, "B5", "Below 60", "@")
    dv = DataValidation(type="list", formula1="=Rules!$A$27:$A$29", allow_blank=False); ws.add_data_validation(dv); dv.add("B5")
    label(ws, "A7", "Old regime deductions (the sheet applies the caps)", bold=True, color=HERO)
    ded = [("80C: PF, PPF, ELSS, LIC, tuition… (cap ₹1,50,000)", 150000, 150000), ("80D: health insurance (cap ₹1,00,000 incl. parents)", 0, 100000),
           ("HRA exemption (from the HRA tab)", "=HRA!B12", None), ("Home-loan interest, self-occupied (cap ₹2,00,000)", 0, 200000),
           ("NPS 80CCD(1B) (cap ₹50,000)", 0, 50000), ("Other deductions you're sure of", 0, None)]
    ws["B7"] = "You enter"; ws["C7"] = "Counted"
    for i, (t, v, cap) in enumerate(ded, 8):
        label(ws, f"A{i}", t)
        if isinstance(v, str): out(ws, f"B{i}", v)
        else: inp(ws, f"B{i}", v)
        out(ws, f"C{i}", f"=MIN(MAX(0,B{i}),{cap})" if cap else f"=MAX(0,B{i})")
    label(ws, "A14", "Total old-regime deductions (₹)", bold=True); out(ws, "C14", "=SUM(C8:C13)", bold=True)
    ws["B16"] = "New regime"; ws["C16"] = "Old regime"
    for c in ("B16", "C16"): ws[c].font = Font(name="Arial", bold=True, color="FFFFFF"); ws[c].fill = PatternFill("solid", fgColor=MADDER)
    R = tax_block(ws, 17, "$B$4", "$C$14", "$B$5")
    label(ws, "A27", "Lower tax under", bold=True); out(ws, "B27", f'=IF(B{R["total"]}<=C{R["total"]},"New regime","Old regime")', "@", bold=True)
    label(ws, "A28", "You save (₹ a year)", bold=True); out(ws, "B28", f"=ABS(B{R['total']}-C{R['total']})", bold=True)
    label(ws, "A30", "Check", bold=True)
    ws["B30"] = f'=IF(MAX(B{R["taxable"]},C{R["taxable"]})>5000000,"Income above ₹50 lakh: surcharge isn\'t included here. Ask a CA.","OK: within this kit\'s range")'
    ws["B30"].font = Font(name="Arial", bold=True, color=BAD)
    label(ws, "A32", "This is a calculator, not tax advice. It names no investments and makes no return promises.", color=MUTED)
    return ws


def hra_sheet(wb):
    ws = wb.create_sheet("HRA", 2); head(ws, "HRA exemption (old regime only)", "Yearly amounts · the smallest of three limits is exempt")
    for i, (t, v) in enumerate([("Basic + DA for the year (₹)", 600000), ("HRA received for the year (₹)", 240000), ("Rent paid for the year (₹)", 240000)], 4):
        label(ws, f"A{i}", t, bold=True); inp(ws, f"B{i}", v)
    label(ws, "A7", "City you live in", bold=True); inp(ws, "B7", "Hyderabad", "@")
    dv = DataValidation(type="list", formula1="=Rules!$A$32:$A$40", allow_blank=False); ws.add_data_validation(dv); dv.add("B7")
    label(ws, "A9", "1. HRA actually received"); out(ws, "B9", "=B5")
    label(ws, "A10", "2. 50% of basic+DA (metro) or 40% (other city)"); out(ws, "B10", '=B4*IF(B7="Other city",0.4,0.5)')
    label(ws, "A11", "3. Rent paid minus 10% of basic+DA"); out(ws, "B11", "=MAX(0,B6-0.1*B4)")
    label(ws, "A12", "HRA exempt (smallest of 1, 2, 3) (₹)", bold=True); out(ws, "B12", "=ROUND(MAX(0,MIN(B9,B10,B11)),0)", bold=True)
    label(ws, "A13", "HRA that stays taxable (₹)"); out(ws, "B13", "=ROUND(B5-B12,0)")
    label(ws, "A15", "Goes to the Tax tab automatically. Claim it only in the old regime, with rent receipts (and the landlord's PAN above ₹1 lakh rent a year).", color=MUTED)
    return ws


def sip_sheet(wb):
    ws = wb.create_sheet("SIP goal", 3); head(ws, "SIP goal planner", "How much to invest each month, with a yearly step-up · returns are your assumption, not a promise")
    items = [("Goal in today's money (₹)", 2000000, RS), ("Years to the goal", 10, "0"), ("Inflation a year", 0.06, "0.0%"),
             ("Return you assume a year", 0.10, "0.0%"), ("Increase your SIP every year by", 0.10, "0%"), ("Money already saved for it (₹)", 0, RS)]
    for i, (t, v, fmt) in enumerate(items, 4):
        label(ws, f"A{i}", t, bold=True); inp(ws, f"B{i}", v, fmt)
    label(ws, "A11", "Goal in future money (₹)"); out(ws, "B11", "=B4*(1+B6)^B5")
    label(ws, "A12", "Your savings will grow to (₹)"); out(ws, "B12", "=B9*(1+B7)^B5")
    label(ws, "A13", "Still needed (₹)"); out(ws, "B13", "=MAX(0,B11-B12)")
    label(ws, "A14", "₹1 a month this year grows to (₹)"); out(ws, "B14", "=SUM(D20:D59)", "#,##0.00")
    label(ws, "A15", "Start your SIP at (₹ a month, rounded up to ₹100)", bold=True); out(ws, "B15", '=IF(B14=0,0,CEILING(B13/B14,100))', bold=True)
    label(ws, "A16", "Check", bold=True); ws["B16"] = '=IF(OR(B5<1,B5>40),"Use 1 to 40 years","OK")'
    for c, t in zip("ABCD", ["Year", "Monthly SIP this year (₹)", "Step-up factor", "₹1/month factor at the goal"]):
        ws[f"{c}19"] = t; ws[f"{c}19"].font = Font(name="Arial", bold=True, color="FFFFFF"); ws[f"{c}19"].fill = HEAD
    for k in range(1, 41):
        r = 19 + k
        ws[f"A{r}"] = k
        ws[f"C{r}"] = f"=IF(A{r}<=$B$5,(1+$B$8)^(A{r}-1),0)"
        # 12 payments at the start of each month in year k, then compounding until the goal year ends (fin.ts sip(): annuity due)
        ws[f"D{r}"] = f"=IF(A{r}<=$B$5,C{r}*IF($B$7=0,12,((1+$B$7/12)^12-1)/($B$7/12)*(1+$B$7/12))*(1+$B$7/12)^(12*($B$5-A{r})),0)"
        ws[f"B{r}"] = f"=IF(A{r}<=$B$5,ROUND($B$15*C{r},0),\"\")"
        for c in "BD": ws[f"{c}{r}"].number_format = RS if c == "B" else "#,##0.00"
        if k % 2 == 0:
            for c in "ABCD": ws[f"{c}{r}"].fill = BAND
    return ws


def loan_sheet(wb):
    ws = wb.create_sheet("Loan", 4); head(ws, "Loan EMI and prepayment", "Reducing balance, the way banks calculate it · up to 30 years")
    for i, (t, v, fmt) in enumerate([("Loan amount (₹)", 3000000, RS), ("Interest rate a year", 0.085, "0.00%"), ("Years", 20, "0"), ("Extra you'll pay every month (₹)", 5000, RS)], 4):
        label(ws, f"A{i}", t, bold=True); inp(ws, f"B{i}", v, fmt)
    label(ws, "A9", "EMI (₹ a month)", bold=True); out(ws, "B9", "=ROUND(PMT(B5/12,B6*12,-B4),0)", bold=True)
    label(ws, "A10", "Total interest without prepaying (₹)"); out(ws, "B10", "=ROUND(PMT(B5/12,B6*12,-B4)*B6*12-B4,0)")
    label(ws, "A11", "Total interest with the extra payment (₹)"); out(ws, "B11", "=ROUND(SUM(C17:C376),0)")
    label(ws, "A12", "Interest you save (₹)", bold=True); out(ws, "B12", "=B10-B11", bold=True)
    label(ws, "A13", "Months you finish early"); out(ws, "B13", '=B6*12-COUNTIF(C17:C376,">0")', "0")
    for c, t in zip("ABCD", ["Month", "Balance at start (₹)", "Interest (₹)", "Balance at end (₹)"]):
        ws[f"{c}16"] = t; ws[f"{c}16"].font = Font(name="Arial", bold=True, color="FFFFFF"); ws[f"{c}16"].fill = HEAD
    for m in range(1, 361):
        r = 16 + m
        ws[f"A{r}"] = m
        ws[f"B{r}"] = "=$B$4" if m == 1 else f"=D{r - 1}"
        ws[f"C{r}"] = f"=IF(AND(B{r}>0,A{r}<=$B$6*12),B{r}*$B$5/12,0)"
        ws[f"D{r}"] = f"=IF(B{r}>0,MAX(0,B{r}-(PMT($B$5/12,$B$6*12,-$B$4)-C{r}+$B$7)),0)"
        for c in "BCD": ws[f"{c}{r}"].number_format = RS
    label(ws, "A14", "Prepaying saves the interest above. Investing the extra instead may earn more or less: compare with your SIP tab's assumed return.", color=MUTED)
    return ws


FIXTURES = [(1275000, 150000, 0, 140400), (1300000, 150000, 26000, 148200), (2500000, 150000, 319800, 522600)]  # roadmap A20 / india-tax-guru


def selfcheck_sheet(wb, extra=()):
    ws = wb.create_sheet("Self-check", 5); head(ws, "Self-check: this sheet against official examples", "Every row runs the same formulas as the Tax tab · all rows must say PASS")
    cols = ["Gross (₹)", "Deductions (₹)", "Age", "New: sheet", "New: expected", "Old: sheet", "Old: expected", "Result"]
    for i, t in enumerate(cols):
        c = chr(65 + i); ws[f"{c}4"] = t; ws[f"{c}4"].font = Font(name="Arial", bold=True, color="FFFFFF"); ws[f"{c}4"].fill = HEAD; ws.column_dimensions[c].width = 15
    ws.column_dimensions["A"].width = 16
    rows = [(g, d, "Below 60", n, o) for g, d, n, o in FIXTURES] + [tuple(x) for x in extra]
    helper = 1000  # hidden helper area far down the sheet for the intermediate cells
    for k, (g, d, age, n, o) in enumerate(rows):
        r = 5 + k; ws[f"A{r}"] = g; ws[f"B{r}"] = d; ws[f"C{r}"] = age; ws[f"E{r}"] = n; ws[f"G{r}"] = o
        R = tax_block(ws, helper + 10 * k, f"$A${r}", f"$B${r}", f"$C${r}")
        ws[f"D{r}"] = f"=B{R['total']}"; ws[f"F{r}"] = f"=C{R['total']}"
        ws[f"H{r}"] = f'=IF(AND(D{r}=E{r},F{r}=G{r}),"PASS","FAIL")'
        for c in "ABDEFG": ws[f"{c}{r}"].number_format = RS
    end = 4 + len(rows)
    ws.conditional_formatting.add(f"H5:H{end}", CellIsRule(operator="equal", formula=['"PASS"'], font=Font(bold=True, color=OK)))
    ws.conditional_formatting.add(f"H5:H{end}", CellIsRule(operator="equal", formula=['"FAIL"'], font=Font(bold=True, color=BAD)))
    label(ws, f"A{end + 2}", "Expected values: tax year 2026-27, salaried below 60, old regime with ₹1,50,000 deductions (india-tax-guru fixtures, MIT).", color=MUTED)
    ws.row_dimensions.group(helper - 1, helper + 10 * len(rows) + 10, hidden=True)
    return ws


def start_sheet(wb):
    ws = wb.active; ws.title = "Start"; head(ws, "Salary Tax-Regime + SIP Goal Planner 2026-27", "Kalpa Labs · Kit v1.0 · personal licence")
    lines = [
        ("How to use (English)", True),
        ("1. Tax tab: type your yearly gross salary and age band. Fill the old-regime deductions you really have.", False),
        ("2. HRA tab: only if you pay rent and get HRA. The result flows into the Tax tab.", False),
        ("3. The Tax tab shows both regimes, which is lower, and how much you save.", False),
        ("4. SIP goal tab: a goal, years, and your own return assumption → the monthly SIP to start with.", False),
        ("5. Loan tab: EMI, and how much interest an extra monthly payment saves.", False),
        ("6. Self-check tab: every row must say PASS. That proves the formulas match official examples.", False),
        ("", False),
        ("ఎలా వాడాలి (తెలుగు)", True),
        ("1. Tax ట్యాబ్: మీ ఏడాది మొత్తం జీతం, వయసు ఎంచుకోండి. పాత విధానం మినహాయింపులు నిజంగా ఉన్నవే రాయండి.", False),
        ("2. HRA ట్యాబ్: అద్దె కట్టి HRA వస్తేనే నింపండి. ఫలితం Tax ట్యాబ్‌కు వెళ్తుంది.", False),
        ("3. Tax ట్యాబ్‌లో రెండు విధానాలు, ఏది తక్కువ, ఎంత ఆదా అవుతుంది అన్నీ కనిపిస్తాయి.", False),
        ("4. SIP goal ట్యాబ్: లక్ష్యం, సంవత్సరాలు, మీరు అనుకునే రాబడి → నెలకు ఎంత SIP మొదలుపెట్టాలి.", False),
        ("5. Self-check ట్యాబ్‌లో అన్నీ PASS అని ఉండాలి.", False),
        ("", False),
        ("Yellow cells are for you; don't type over the white ones. If something breaks, make a fresh copy from your link.", False),
        ("A calculator, not tax, investment or legal advice. Rules for tax year 2026-27 (Income-tax Act 2025), checked 16 Oct 2026. Income above ₹50 lakh: surcharge not included.", False),
        ("Kalpa Labs · Udyam UDYAM-TS-02-0382711 · aakhiil51458@gmail.com", False),
    ]
    for i, (t, b) in enumerate(lines, 4):
        label(ws, f"A{i}", t, bold=b, color=HERO if b else INK); ws.merge_cells(f"A{i}:F{i}"); ws.row_dimensions[i].height = 30 if len(t) > 90 else 20
    ws.column_dimensions["A"].width = 60
    return ws


def build(out, extra=()):
    wb = Workbook(); start_sheet(wb); rules_sheet(wb); tax_sheet(wb); hra_sheet(wb); sip_sheet(wb); loan_sheet(wb); selfcheck_sheet(wb, extra)
    wb.move_sheet("Rules", offset=len(wb.sheetnames))
    wb.properties.title = "Salary Tax-Regime + SIP Goal Planner 2026-27"; wb.properties.creator = "Kalpa Labs"
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True); wb.save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "products" / "Kalpa-Tax-SIP-Planner-2026-27.xlsx"))
    ap.add_argument("--extra", help="JSON list of [gross, deductions, age, expected_new, expected_old] rows (tests)")
    a = ap.parse_args()
    print(build(a.out, json.loads(pathlib.Path(a.extra).read_text()) if a.extra else ()))

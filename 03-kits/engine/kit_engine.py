#!/usr/bin/env python3
"""
b3 Exam Kits engine: one data file per exam (exams/<id>.yaml) -> four kit files per exam in dist/<id>/:
  <id>-tracker.xlsx    syllabus tracker: status dropdown, progress % formulas, spaced revision dates (Sheets-portable)
  <id>-calendar.ics    CONFIRMED exam dates (with 7-day and 1-day alarms) + a daily study plan + weekly check
  <id>-tracker.html    phone page: progress saved in localStorage (try/catch), Kalpa design tokens only
  <id>-telegram.json   reminder messages for the BotBhai Telegram flow (messages only: this file sends nothing)

  python3 03-kits/engine/kit_engine.py                      # validate + build every exam into dist/
  python3 03-kits/engine/kit_engine.py --exam ssc-cgl --start 2026-11-10
  python3 03-kits/engine/kit_engine.py --check              # validate only

No network calls. Reuses the GATE kit's palette and sheet helpers (../gate-2027/build_kit.py).
Date rule: only CONFIRMED dates carry a day, and every CONFIRMED date needs an official https source.
"""
import argparse, datetime as dt, importlib.util, json, math, pathlib, re, sys, urllib.parse
import yaml
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HERE = pathlib.Path(__file__).resolve().parent
EXAMS = HERE / "exams"
DIST = HERE / "dist"
TOKENS = HERE.parent.parent / "00-hq" / "design" / "tokens.css"
_spec = importlib.util.spec_from_file_location("gate_build_kit", HERE.parent / "gate-2027" / "build_kit.py")
G = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(G)

STATUSES = G.STATUSES                                   # Not started / Learning / Done (same as the GATE kit)
DATE_STATUSES = ("CONFIRMED", "EXPECTED", "NOT_ANNOUNCED")
VIDEO_STATUSES = ("TO_CURATE", "CURATED")
LINK_STATUSES = ("TO_VERIFY", "VERIFIED")
CATEGORIES = ("state-govt", "central-govt", "bank", "private", "entrance")
LANGS = ("en", "te", "hi")
HTTPS = re.compile(r"^https://[a-z0-9.-]+\.[a-z]{2,}(/\S*)?$", re.I)
YT_VIDEO = re.compile(r"^https://(www\.youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}$")
TZ = "Asia/Kolkata"


# ------------------------------------------------------------------ data
def load(path):
    path = pathlib.Path(path)
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    for k in d.get("key_dates") or []:                    # YAML turns 2027-02-06 into a date: keep ISO text
        if isinstance(k.get("date"), dt.date): k["date"] = k["date"].isoformat()
    if isinstance(d.get("checked_on"), dt.date): d["checked_on"] = d["checked_on"].isoformat()
    d["_file"] = path.name
    return d


def _iso(s):
    try: return dt.date.fromisoformat(str(s))
    except ValueError: return None


def validate(d):
    """Return a list of plain-English problems (empty = good)."""
    e = []
    for k in ("id", "short", "name", "body", "category", "official_site", "languages", "checked_on", "stages", "key_dates", "plan", "materials", "youtube", "subjects"):
        if k not in d or d[k] in (None, "", []): e.append(f"missing '{k}'")
    if e: return e
    if not re.fullmatch(r"[a-z0-9-]+", str(d["id"])): e.append("id: use lowercase letters, digits and dashes")
    if d.get("_file") and d["_file"] != f"{d['id']}.yaml": e.append(f"file name must be {d['id']}.yaml")
    if d["category"] not in CATEGORIES: e.append(f"category must be one of {CATEGORIES}")
    if not HTTPS.match(str(d["official_site"])): e.append("official_site must be an https link")
    langs = d["languages"]
    if "en" not in langs or not set(langs) <= set(LANGS): e.append(f"languages must include en and only use {LANGS}")
    te = "te" in langs
    if not _iso(d["checked_on"]): e.append("checked_on must be a date like 2026-11-07")
    for i, k in enumerate(d["key_dates"], 1):
        w = f"key_dates #{i} ({k.get('event')})"
        if not k.get("event"): e.append(f"{w}: missing event")
        st = k.get("status")
        if st not in DATE_STATUSES: e.append(f"{w}: status must be one of {DATE_STATUSES}"); continue
        if st == "CONFIRMED":
            if not _iso(k.get("date")): e.append(f"{w}: CONFIRMED needs a real date (YYYY-MM-DD)")
            if not HTTPS.match(str(k.get("source") or "")): e.append(f"{w}: CONFIRMED needs an official https source link")
        elif k.get("date") is not None:
            e.append(f"{w}: only CONFIRMED dates may have a date; {st} must use date: null (put the guess in note)")
        if st == "EXPECTED" and not k.get("note"): e.append(f"{w}: EXPECTED needs a note saying why")
        if k.get("source") and not HTTPS.match(str(k["source"])): e.append(f"{w}: source must be an https link")
        if te and not k.get("event_te"): e.append(f"{w}: Telugu kit needs event_te")
    p = d["plan"]
    if not (isinstance(p.get("topics_per_day"), int) and 1 <= p["topics_per_day"] <= 10): e.append("plan.topics_per_day must be 1 to 10")
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", str(p.get("reminder_time", ""))): e.append("plan.reminder_time must look like 07:30")
    rd = p.get("revision_days")
    if not (isinstance(rd, list) and rd and all(isinstance(x, int) and x > 0 for x in rd) and rd == sorted(rd)): e.append("plan.revision_days must be rising whole days, e.g. [1, 3, 7, 21]")
    for i, m in enumerate(d["materials"], 1):
        if not m.get("title"): e.append(f"materials #{i}: missing title")
        if not HTTPS.match(str(m.get("url") or "")): e.append(f"materials #{i}: url must be https")
        if m.get("status") not in LINK_STATUSES: e.append(f"materials #{i}: status must be one of {LINK_STATUSES}")
    if "{topic}" not in str((d["youtube"] or {}).get("query_template", "")): e.append("youtube.query_template must contain {topic}")
    seen = set()
    for s in d["subjects"]:
        w = f"subject '{s.get('name')}'"
        if not s.get("name") or not s.get("topics"): e.append(f"{w}: needs name and topics"); continue
        if te and not s.get("name_te"): e.append(f"{w}: Telugu kit needs name_te")
        for v in s.get("videos") or []:
            if v.get("status") not in VIDEO_STATUSES: e.append(f"{w}: video status must be one of {VIDEO_STATUSES}")
            elif v["status"] == "TO_CURATE":
                if v.get("url"): e.append(f"{w}: a TO_CURATE slot must have url: null (never guess a video link)")
                if not v.get("query"): e.append(f"{w}: video slot needs a search query")
            elif not YT_VIDEO.match(str(v.get("url") or "")): e.append(f"{w}: CURATED video needs a real YouTube watch link")
        for t in s["topics"]:
            en = (t or {}).get("en", "").strip()
            if not en: e.append(f"{w}: topic without an English name"); continue
            if en.lower() in seen: e.append(f"{w}: duplicate topic '{en}'")
            seen.add(en.lower())
            if te and not t.get("te"): e.append(f"{w}: topic '{en}' needs its Telugu name (te)")
    if not 20 <= len(seen) <= 150: e.append(f"{len(seen)} topics: aim for 60–100 rows")
    return e


def topics(d):
    out, n = [], 0
    for s in d["subjects"]:
        for t in s["topics"]:
            n += 1
            out.append({"n": n, "paper": s.get("paper", ""), "subject": s["name"], "subject_te": s.get("name_te", ""), "en": t["en"], "te": t.get("te", ""),
                        "query": d["youtube"]["query_template"].format(topic=t["en"])})
    return out


def yt_search(q):
    return "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(q)   # a search page, never a guessed video


def exam_date(d):
    days = sorted(k["date"] for k in d["key_dates"] if k["status"] == "CONFIRMED" and "exam" in k["event"].lower())
    return dt.date.fromisoformat(days[0]) if days else None


def schedule(d, start):
    """Day-by-day plan from start: new topics (topics_per_day, raised if a CONFIRMED exam date needs it) + spaced revisions."""
    ts, p = topics(d), d["plan"]
    tpd, ex = p["topics_per_day"], exam_date(d)
    if ex and ex > start:
        avail = (ex - start).days - 14                    # leave the last two weeks for mocks and revision
        if avail > 0: tpd = max(tpd, math.ceil(len(ts) / avail))
    days = {}
    for i in range(math.ceil(len(ts) / tpd)):
        chunk = ts[i * tpd:(i + 1) * tpd]
        days.setdefault(start + dt.timedelta(i), {"new": [], "revise": []})["new"] += chunk
        for gap in p["revision_days"]:
            day = start + dt.timedelta(i + gap)
            if ex and day >= ex: continue
            days.setdefault(day, {"new": [], "revise": []})["revise"] += chunk
    return [{"date": k, **v} for k, v in sorted(days.items())], tpd


def label(t, lang):
    return t["te"] if lang == "te" and t.get("te") else t["en"]


# ------------------------------------------------------------------ xlsx
def build_xlsx(d, out, pinned=None):
    te = "te" in d["languages"]
    T = G.today_ref(pinned)
    ts = topics(d)
    rd = d["plan"]["revision_days"]
    ex = exam_date(d)
    wb = Workbook()
    # Start
    st = wb.active; st.title = "Start"
    G.style_head(st, f"{d['short']} · Study tracker", f"Kalpa Labs · Exam Kit · data checked {d['checked_on']}", 2)
    st.column_dimensions["A"].width = 100
    lines = ["How to use",
             "1. Plan tab: type your exam date when it is announced (yellow cell). Days left and topics-a-day update every day.",
             f"2. Syllabus tab: mark each topic Not started / Learning / Done. When Done, type the date: revision dates appear ({', '.join(map(str, rd))} days).",
             "3. Progress tab: your % done per subject. Dates tab: every date with its status and official link.",
             "4. Videos tab: each slot is a YouTube search until our team checks and adds the best video.", ""]
    if te:
        lines += ["ఎలా వాడాలి",
                  "1. Plan ట్యాబ్: పరీక్ష తేదీ ప్రకటించగానే పసుపు గడిలో రాయండి. మిగిలిన రోజులు రోజూ మారుతాయి.",
                  "2. Syllabus ట్యాబ్: ప్రతి టాపిక్‌కి Not started / Learning / Done గుర్తు పెట్టండి. Done అయితే తేదీ రాయండి: రివిజన్ తేదీలు వస్తాయి.",
                  "3. Progress ట్యాబ్: సబ్జెక్ట్ వారీగా మీరు పూర్తి చేసిన శాతం. Dates ట్యాబ్: అధికారిక లింక్‌తో ప్రతి తేదీ.", ""]
    lines += [f"Not an official {d['body']} product. Only trust dates on {d['official_site']}. Yellow cells are yours.",
              "Kalpa Labs · Udyam UDYAM-TS-02-0382711 · aakhiil51458@gmail.com"]
    for i, t in enumerate(lines, 4):
        c = st[f"A{i}"]; c.value = t; c.alignment = Alignment(wrap_text=True)
        c.font = Font(name="Arial", size=11, bold=t in ("How to use", "ఎలా వాడాలి"), color=G.INK)

    # Syllabus (built before Plan/Progress so the column letters are known)
    sy = wb.create_sheet("Syllabus")
    names = ["#", "Paper", "Subject", "Topic"] + (["తెలుగు"] if te else []) + ["Status", "Done on", "Revisions done", "Next revision", "Due?", "YouTube", "My notes"]
    widths = [5, 14, 30, 52] + ([44] if te else []) + [13, 12, 10, 13, 9, 10, 30]
    col = {n: get_column_letter(i) for i, n in enumerate(names, 1)}
    S_, D_, R_, N_, Q_, SUBJ = col["Status"], col["Done on"], col["Revisions done"], col["Next revision"], col["Due?"], col["Subject"]
    G.style_head(sy, f"Syllabus · {d['short']}", f"{len(ts)} topics · check the official syllabus on {d['official_site']}", len(names))
    G.hdr(sy, 4, names, widths)
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True); sy.add_data_validation(dv)
    for t in ts:
        r = 4 + t["n"]
        sy[f"A{r}"] = t["n"]; sy[f"B{r}"] = t["paper"]; sy[f"C{r}"] = t["subject"]; sy[f"D{r}"] = t["en"]
        if te: sy[f"{col['తెలుగు']}{r}"] = t["te"]
        sy[f"{S_}{r}"] = "Not started"; sy[f"{S_}{r}"].fill = G.INPUT; dv.add(f"{S_}{r}")
        sy[f"{D_}{r}"].fill = G.INPUT; sy[f"{D_}{r}"].number_format = "dd mmm"
        sy[f"{R_}{r}"] = 0; sy[f"{R_}{r}"].fill = G.INPUT
        sy[f"{N_}{r}"] = f'=IF(AND({S_}{r}="Done",ISNUMBER({D_}{r}),{R_}{r}<{len(rd)}),{D_}{r}+CHOOSE({R_}{r}+1,{",".join(map(str, rd))}),"")'
        sy[f"{N_}{r}"].number_format = "dd mmm"
        sy[f"{Q_}{r}"] = f'=IF({N_}{r}="","",IF({N_}{r}<={T},"Revise","Later"))'
        y = sy[f"{col['YouTube']}{r}"]; y.value = "Search"; y.hyperlink = yt_search(t["query"]); y.font = Font(name="Arial", color=G.HERO, underline="single")
        sy[f"{col['My notes']}{r}"].fill = G.INPUT
        if r % 2 == 0:
            for c in ("C", "D"): sy[f"{c}{r}"].fill = G.BAND
    last = 4 + len(ts)
    sy.conditional_formatting.add(f"{S_}5:{S_}{last}", CellIsRule(operator="equal", formula=['"Done"'], font=Font(color=G.OK, bold=True)))
    sy.conditional_formatting.add(f"{Q_}5:{Q_}{last}", CellIsRule(operator="equal", formula=['"Revise"'], font=Font(color=G.BAD, bold=True)))
    sy[f"A{last + 2}"] = "When you revise a topic, add 1 to 'Revisions done' and type today's date in 'Done on'."
    sy[f"A{last + 2}"].font = Font(name="Arial", size=10, color=G.MUTED)
    sy.freeze_panes = "E5"
    rng = lambda c: f"Syllabus!${c}$5:${c}${last}"

    # Plan
    pl = wb.create_sheet("Plan", 1); G.style_head(pl, "Countdown and plan", f"{d['name']} · {d['body']}", 3)
    pl.column_dimensions["A"].width = 42; pl.column_dimensions["B"].width = 24; pl.column_dimensions["C"].width = 48
    pl["A4"] = "My exam date"; pl["B4"].fill = G.INPUT; pl["B4"].border = G.BOX; pl["B4"].number_format = "dd mmm yyyy"
    if ex: pl["B4"] = ex; pl["C4"] = "CONFIRMED on the official site"
    else: pl["C4"] = "Not announced yet: type it here when the official notice gives it"
    pl["A5"] = "Today"; pl["B5"] = f"={T}"; pl["B5"].number_format = "dd mmm yyyy"
    pl["A6"] = "Days left"; pl["B6"] = '=IF(ISNUMBER(B4),MAX(0,B4-B5),"Not announced")'; pl["B6"].font = Font(name="Arial", size=20, bold=True, color=G.MADDER)
    pl["A7"] = "Topics done"; pl["B7"] = f'=COUNTIF({rng(S_)},"Done")&" of {len(ts)}"'
    pl["A8"] = "Syllabus done"; pl["B8"] = f'=COUNTIF({rng(S_)},"Done")/{len(ts)}'; pl["B8"].number_format = "0%"
    pl["A9"] = "Topics a day needed (if the date is set)"; pl["B9"] = f'=IF(ISNUMBER(B6),IF(B6=0,0,ROUND(({len(ts)}-COUNTIF({rng(S_)},"Done"))/B6,2)),"")'
    pl["A10"] = "Revisions due today or overdue"; pl["B10"] = f'=COUNTIFS({rng(N_)},"<="&{T},{rng(S_)},"Done")'
    pl["A11"] = "Planned pace (topics a day)"; pl["B11"] = d["plan"]["topics_per_day"]; pl["B11"].fill = G.INPUT
    for r in range(4, 12): pl[f"A{r}"].font = Font(name="Arial", bold=True)

    # Progress (per subject %)
    pr = wb.create_sheet("Progress", 2); G.style_head(pr, "Progress", "Counts itself from the Syllabus tab", 6)
    G.hdr(pr, 4, ["Subject", "Topics", "Done", "Learning", "Not started", "% done"], [44, 9, 9, 10, 12, 10])
    subs = [s["name"] for s in d["subjects"]]
    for i, s in enumerate(subs, 5):
        pr[f"A{i}"] = s
        pr[f"B{i}"] = f'=COUNTIF({rng(SUBJ)},A{i})'
        pr[f"C{i}"] = f'=COUNTIFS({rng(SUBJ)},A{i},{rng(S_)},"Done")'
        pr[f"D{i}"] = f'=COUNTIFS({rng(SUBJ)},A{i},{rng(S_)},"Learning")'
        pr[f"E{i}"] = f"=B{i}-C{i}-D{i}"
        pr[f"F{i}"] = f"=IF(B{i}=0,0,C{i}/B{i})"; pr[f"F{i}"].number_format = "0%"
    tot = 5 + len(subs)
    pr[f"A{tot}"] = "All subjects"; pr[f"A{tot}"].font = Font(name="Arial", bold=True)
    for c in "BCDE": pr[f"{c}{tot}"] = f"=SUM({c}5:{c}{tot - 1})"
    pr[f"F{tot}"] = f"=IF(B{tot}=0,0,C{tot}/B{tot})"; pr[f"F{tot}"].number_format = "0%"; pr[f"F{tot}"].font = Font(name="Arial", bold=True, color=G.OK)

    # Dates
    da = wb.create_sheet("Dates"); G.style_head(da, "Exam dates and alerts", f"Status: CONFIRMED (official) · EXPECTED (not official) · NOT_ANNOUNCED · checked {d['checked_on']}", 6)
    dn = ["Event"] + (["తెలుగు"] if te else []) + ["Date", "Status", "Official source", "Note"]
    G.hdr(da, 4, dn, [40] + ([30] if te else []) + [14, 16, 34, 50])
    for i, k in enumerate(d["key_dates"], 5):
        vals = [k["event"]] + ([k.get("event_te", "")] if te else []) + [dt.date.fromisoformat(k["date"]) if k.get("date") else "—", k["status"], k.get("source") or "", k.get("note") or ""]
        for j, v in enumerate(vals, 1):
            c = da.cell(i, j, v); c.alignment = Alignment(wrap_text=True, vertical="top")
            if isinstance(v, dt.date): c.number_format = "dd mmm yyyy"
            if dn[j - 1] == "Official source" and v: c.hyperlink = v; c.font = Font(name="Arial", color=G.HERO, underline="single")
    sc = get_column_letter(dn.index("Status") + 1); dl = 4 + len(d["key_dates"])
    da.conditional_formatting.add(f"{sc}5:{sc}{dl}", CellIsRule(operator="equal", formula=['"CONFIRMED"'], font=Font(color=G.OK, bold=True)))
    da.conditional_formatting.add(f"{sc}5:{sc}{dl}", CellIsRule(operator="equal", formula=['"NOT_ANNOUNCED"'], font=Font(color=G.MADDER, bold=True)))

    # Material + videos
    ma = wb.create_sheet("Material"); G.style_head(ma, "Best free material", "Official and free sources only · links checked by the team before sale", 4)
    G.hdr(ma, 4, ["Title", "Kind", "Link", "Link status"], [60, 16, 40, 13])
    for i, m in enumerate(d["materials"], 5):
        ma[f"A{i}"] = m["title"]; ma[f"B{i}"] = m.get("kind", ""); ma[f"C{i}"] = m["url"]; ma[f"C{i}"].hyperlink = m["url"]; ma[f"D{i}"] = m["status"]
        ma[f"A{i}"].alignment = Alignment(wrap_text=True)
    vi = wb.create_sheet("Videos"); G.style_head(vi, "Best YouTube videos", "TO_CURATE = our team has not picked the video yet; use the search link", 5)
    G.hdr(vi, 4, ["Subject", "Search query", "Search", "Video link (after curation)", "Status"], [40, 50, 10, 40, 12])
    r = 5
    for s in d["subjects"]:
        for v in s.get("videos") or []:
            vi[f"A{r}"] = s["name"]; vi[f"B{r}"] = v["query"]; vi[f"C{r}"] = "Search"; vi[f"C{r}"].hyperlink = yt_search(v["query"])
            vi[f"D{r}"] = v.get("url") or ""; vi[f"D{r}"].fill = G.INPUT; vi[f"E{r}"] = v["status"]; r += 1
    wb.properties.title = f"{d['short']} tracker"; wb.properties.creator = "Kalpa Labs"
    out = pathlib.Path(out); out.parent.mkdir(parents=True, exist_ok=True); wb.save(out)
    return out


# ------------------------------------------------------------------ ics
def _esc(s):
    return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line):
    """RFC 5545: lines of at most 75 octets; continuation lines start with one space. Never split a UTF-8 character."""
    out, cur, size = [], "", 0
    for ch in line:
        b = len(ch.encode("utf-8"))
        if size + b > (75 if not out else 74):
            out.append(cur); cur, size = "", 0
        cur += ch; size += b
    out.append(cur)
    return "\r\n ".join(out)


def build_ics(d, out, start, stamp=None):
    stamp = stamp or dt.datetime.combine(start, dt.time()).strftime("%Y%m%dT%H%M%SZ")
    hh, mm = map(int, d["plan"]["reminder_time"].split(":"))
    te = "te" in d["languages"]
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Kalpa Labs//Exam Kit Engine//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         f"X-WR-CALNAME:{_esc(d['short'] + ' · Kalpa Exam Kit')}", f"X-WR-TIMEZONE:{TZ}",
         "BEGIN:VTIMEZONE", f"TZID:{TZ}", "BEGIN:STANDARD", "DTSTART:19700101T000000", "TZOFFSETFROM:+0530", "TZOFFSETTO:+0530", "TZNAME:IST", "END:STANDARD", "END:VTIMEZONE"]

    def alarm(trigger, text):
        return ["BEGIN:VALARM", "ACTION:DISPLAY", f"TRIGGER:{trigger}", f"DESCRIPTION:{_esc(text)}", "END:VALARM"]

    for i, k in enumerate(d["key_dates"]):
        if k["status"] != "CONFIRMED": continue          # EXPECTED / NOT_ANNOUNCED never go in a calendar
        day = dt.date.fromisoformat(k["date"])
        L += ["BEGIN:VEVENT", f"UID:{d['id']}-date-{i}@kalpalabs", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
              f"DTEND;VALUE=DATE:{day + dt.timedelta(1):%Y%m%d}", f"SUMMARY:{_esc(d['short'] + ': ' + k['event'])}",
              f"DESCRIPTION:{_esc((k.get('note') or '') + ' Official: ' + k['source'])}", f"URL:{k['source']}", "TRANSP:TRANSPARENT"]
        L += alarm("-P7D", f"7 days to {k['event']}") + alarm("-P1D", f"Tomorrow: {k['event']}") + ["END:VEVENT"]
    plan, _ = schedule(d, start)
    for n, day in enumerate(plan, 1):
        t0 = dt.datetime.combine(day["date"], dt.time(hh, mm)); t1 = t0 + dt.timedelta(hours=1)
        bits = []
        if day["new"]: bits.append(" + ".join(t["en"] for t in day["new"]))
        if day["revise"]: bits.append(f"revise {len(day['revise'])}")
        desc = []
        if day["new"]: desc += ["New today:"] + [f"• {t['en']}" + (f" ({t['te']})" if te and t['te'] else "") for t in day["new"]]
        if day["revise"]: desc += ["Revise today:"] + [f"• {t['en']}" for t in day["revise"]]
        desc.append("Mark them in your Kalpa tracker.")
        L += ["BEGIN:VEVENT", f"UID:{d['id']}-plan-{day['date']:%Y%m%d}@kalpalabs", f"DTSTAMP:{stamp}",
              f"DTSTART;TZID={TZ}:{t0:%Y%m%dT%H%M%S}", f"DTEND;TZID={TZ}:{t1:%Y%m%dT%H%M%S}",
              f"SUMMARY:{_esc(d['short'] + ' · Day ' + str(n) + ': ' + ' · '.join(bits))}", f"DESCRIPTION:{_esc(chr(10).join(desc))}",
              "CATEGORIES:Study plan"] + alarm("-PT10M", "Study block in 10 minutes") + ["END:VEVENT"]
    weeks = max(1, math.ceil(((plan[-1]["date"] - start).days + 1) / 7)) if plan else 1
    sun = start + dt.timedelta((6 - start.weekday()) % 7)
    L += ["BEGIN:VEVENT", f"UID:{d['id']}-weekly@kalpalabs", f"DTSTAMP:{stamp}", f"DTSTART;TZID={TZ}:{sun:%Y%m%d}T180000", f"DTEND;TZID={TZ}:{sun:%Y%m%d}T183000",
          f"RRULE:FREQ=WEEKLY;COUNT={weeks}", f"SUMMARY:{_esc(d['short'] + ' · Weekly check: update progress %, check official dates')}",
          f"DESCRIPTION:{_esc('Only trust dates on ' + d['official_site'])}", f"URL:{d['official_site']}", "END:VEVENT", "END:VCALENDAR"]
    out = pathlib.Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(("\r\n".join(_fold(x) for x in L) + "\r\n").encode("utf-8"))
    return out


# ------------------------------------------------------------------ telegram
TXT = {
    "en": {"head": "📚 {short} · Day {n}", "new": "New today:", "rev": "Revise today:", "done": "Mark them Done in your tracker.",
           "a7": "⏰ 7 days to {event} ({date}). Official: {src}", "a1": "⏰ Tomorrow: {event}. Official: {src}", "a0": "📌 Today: {event}. All the best!",
           "wk": "🗓 Weekly check: update your progress %.", "na": "Not announced yet: {list}. Only trust {site}.", "wkhead": "🗓 {short} · weekly check", "alhead": "📌 {short}"},
    "te": {"head": "📚 {short} · రోజు {n}", "new": "ఈరోజు కొత్త టాపిక్‌లు:", "rev": "ఈరోజు రివిజన్:", "done": "పూర్తయ్యాక ట్రాకర్‌లో Done అని గుర్తు పెట్టండి.",
           "a7": "⏰ {event}కు ఇంకా 7 రోజులు ({date}). అధికారిక సైట్: {src}", "a1": "⏰ రేపు: {event}. అధికారిక సైట్: {src}", "a0": "📌 ఈరోజు: {event}. ఆల్ ది బెస్ట్!",
           "wk": "🗓 వారపు సమీక్ష: మీ ప్రోగ్రెస్ % అప్‌డేట్ చేయండి.", "na": "ఇంకా ప్రకటించలేదు: {list}. అధికారిక సమాచారం {site} లో మాత్రమే.", "wkhead": "🗓 {short} · వారపు సమీక్ష", "alhead": "📌 {short}"},
}
TG_LIMIT = 4096


def build_telegram(d, out, start):
    hh, mm = d["plan"]["reminder_time"].split(":")
    plan, tpd = schedule(d, start)
    langs = [l for l in d["languages"] if l in TXT]
    days = {p["date"]: {"n": i, **p} for i, p in enumerate(plan, 1)}
    alerts, firsts = {}, {}
    for k in d["key_dates"]:                              # one alert set per event: GATE's six exam days alert once, from the first day
        if k["status"] == "CONFIRMED" and (k["event"] not in firsts or k["date"] < firsts[k["event"]]["date"]): firsts[k["event"]] = k
    for k in firsts.values():
        day = dt.date.fromisoformat(k["date"])
        for gap, key in ((7, "a7"), (1, "a1"), (0, "a0")):
            when = day - dt.timedelta(gap)
            if when >= start: alerts.setdefault(when, []).append((key, k))
    last = max(list(days) + list(alerts)) if (days or alerts) else start
    sundays = {start + dt.timedelta(x) for x in range((last - start).days + 1) if (start + dt.timedelta(x)).weekday() == 6}
    pending = lambda lang: ", ".join((k.get("event_te") if lang == "te" and k.get("event_te") else k["event"]) for k in d["key_dates"] if k["status"] != "CONFIRMED")
    msgs = []
    for when in sorted(set(days) | set(alerts) | sundays):
        for lang in langs:
            S, parts, kinds = TXT[lang], [], []
            p = days.get(when)
            parts.append(S["head"].format(short=d["short"], n=p["n"]) if p else S["wkhead" if when in sundays else "alhead"].format(short=d["short"]))
            for key, k in alerts.get(when, []):
                ev = k.get("event_te") if lang == "te" and k.get("event_te") else k["event"]
                parts.append(S[key].format(event=ev, date=dt.date.fromisoformat(k["date"]).strftime("%d %b %Y"), src=k["source"])); kinds.append("date_alert")
            if p and p["new"]: parts += [S["new"]] + [f"• {label(t, lang)}" for t in p["new"]]; kinds.append("study")
            if p and p["revise"]: parts += [S["rev"]] + [f"• {label(t, lang)}" for t in p["revise"]]; kinds.append("revision")
            if p: parts.append(S["done"])
            if when in sundays:
                parts.append(S["wk"]); kinds.append("weekly")
                if pending(lang): parts.append(S["na"].format(list=pending(lang), site=d["official_site"]))
            text = "\n".join(parts)
            if len(text) > TG_LIMIT: text = text[:TG_LIMIT - 1] + "…"
            msgs.append({"id": f"{d['id']}-{when:%Y%m%d}-{lang}", "send_at": f"{when.isoformat()}T{hh}:{mm}:00+05:30", "lang": lang, "kinds": kinds, "text": text})
    doc = {"exam": d["id"], "short": d["short"], "timezone": TZ, "start": start.isoformat(), "topics_per_day": tpd,
           "flow": "BotBhai Telegram (01-botbhai/botbhai/core/functions/telegram.js) · Library of Ranks channel / opted-in subscribers",
           "method": "sendMessage", "rules": ["At most one message a day per language.", "Send only to people who joined or opted in.",
                                              "No 'only today' or rank-guarantee wording.", "This file sends nothing; the bot flow fills chat_id and sends."],
           "messages": msgs}
    out = pathlib.Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=0), encoding="utf-8")
    return out


# ------------------------------------------------------------------ html
CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 var(--f-body);overflow-wrap:anywhere}
a{color:var(--accent)}
.wrap{max-width:720px;margin:0 auto;padding:0 14px 40px}
.hero{background:var(--hero);color:var(--hero-fg);padding:18px 14px 16px}
.hero h1{font:400 26px/1.15 var(--f-display);margin:0 0 4px}
.hero p{margin:0;color:var(--hero-mute);font-size:14px}
.hero a{color:var(--hero-fg)}
.vine{height:10px;background:var(--vine)}
.stats{display:flex;gap:10px;margin:14px 0}
.stat{flex:1;background:var(--panel);border:1px solid var(--rule);border-radius:var(--r-m);padding:10px 12px;box-shadow:var(--shadow)}
.stat b{display:block;font:600 24px/1.1 var(--f-mono);color:var(--l3)}
.stat span{font-size:13px;color:var(--muted)}
.bar{height:10px;background:var(--soft);border-radius:var(--r-s);overflow:hidden}
.bar i{display:block;height:100%;width:0;background:var(--l3)}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
button,select{font:inherit;color:var(--fg);background:var(--panel);border:1px solid var(--rule);border-radius:var(--r-s);min-height:44px;padding:6px 12px}
select{max-width:100%}
.tools select{flex:1 1 100%}
button.on{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}
h2{font:400 21px/1.2 var(--f-display);margin:24px 0 8px}
.card{background:var(--panel);border:1px solid var(--rule);border-radius:var(--r-m);margin:10px 0;box-shadow:var(--shadow)}
details summary{cursor:pointer;padding:12px;font-weight:600;list-style:none;display:flex;gap:8px;align-items:center;justify-content:space-between}
details summary small{color:var(--muted);font-weight:400}
.topic{border-top:1px solid var(--rule);padding:10px 12px;display:grid;grid-template-columns:1fr auto;gap:6px 10px;align-items:center}
.topic .nm{font-size:15px}
.topic .meta{grid-column:1/-1;display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:13px;color:var(--muted)}
.topic.done .nm{color:var(--ok)}
.due{color:var(--bad);font-weight:600}
table{width:100%;border-collapse:collapse;font-size:14px}
td{border-top:1px solid var(--rule);padding:8px;vertical-align:top}
.badge{display:inline-block;font:600 11px/1 var(--f-mono);padding:4px 6px;border-radius:var(--r-s);border:1px solid currentColor}
.CONFIRMED{color:var(--ok)}.EXPECTED{color:var(--warn)}.NOT_ANNOUNCED{color:var(--madder)}
ul.links{padding-left:18px}ul.links li{margin:6px 0}
.note{font-size:13px;color:var(--muted)}
#warn{display:none;background:var(--soft);border:1px solid var(--warn);border-radius:var(--r-s);padding:8px;margin:10px 0;font-size:14px}
"""

JS = r"""
(function(){
var K=JSON.parse(document.getElementById('kit').textContent);
var KEY='kalpa-kit:'+K.id+':v1', S={t:{},lang:'en'}, canSave=true;
try{var raw=window.localStorage.getItem(KEY);if(raw){var p=JSON.parse(raw);if(p&&typeof p==='object'&&p.t&&typeof p.t==='object')S=p;}}catch(e){canSave=false;}
function warn(){var w=document.getElementById('warn');w.style.display='block';w.textContent=K.ui.nosave;}
function save(){if(!canSave){warn();return;}try{window.localStorage.setItem(KEY,JSON.stringify(S));}catch(e){canSave=false;warn();}}
function el(tag,cls,txt){var x=document.createElement(tag);if(cls)x.className=cls;if(txt!=null)x.textContent=txt;return x;}
function iso(d){return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2);}
function addDays(s,n){var p=s.split('-');var d=new Date(+p[0],+p[1]-1,+p[2]+n);return iso(d);}
var TODAY=iso(new Date());
function st(n){return S.t[n]||{s:'Not started',d:'',r:0};}
function nextRev(x){if(x.s!=='Done'||!x.d||x.r>=K.rev.length)return '';return addDays(x.d,K.rev[x.r]);}
function name(t){return S.lang==='te'&&t.te?t.te:t.en;}
function render(){
  var done=0,due=0,box=document.getElementById('syl');box.textContent='';
  var filt=document.getElementById('filter').value;
  K.subjects.forEach(function(sub){
    var ts=K.topics.filter(function(t){return t.subject===sub.name;});
    var sd=ts.filter(function(t){return st(t.n).s==='Done';}).length;done+=sd;
    var det=el('details','card');det.open=(filt===sub.name);
    var sm=el('summary');sm.appendChild(el('span',null,(S.lang==='te'&&sub.te?sub.te:sub.name)));
    sm.appendChild(el('small',null,sd+'/'+ts.length));det.appendChild(sm);
    var bar=el('div','bar');var bi=el('i');bi.style.width=Math.round(100*sd/ts.length)+'%';bar.appendChild(bi);bar.style.margin='0 12px 10px';det.appendChild(bar);
    ts.forEach(function(t){
      var x=st(t.n),nr=nextRev(x),isDue=nr&&nr<=TODAY;if(isDue)due++;
      if(filt==='__due'&&!isDue)return;
      var row=el('div','topic'+(x.s==='Done'?' done':''));row.appendChild(el('div','nm',t.n+'. '+name(t)));
      var sel=el('select');sel.setAttribute('aria-label','Status');K.statuses.forEach(function(o){var op=el('option',null,o);op.value=o;if(o===x.s)op.selected=true;sel.appendChild(op);});
      sel.onchange=function(){var y=st(t.n);y.s=sel.value;if(y.s==='Done'){if(!y.d)y.d=TODAY;}else{y.d='';y.r=0;}S.t[t.n]=y;save();render();};
      row.appendChild(sel);
      var meta=el('div','meta');
      if(nr){meta.appendChild(el('span',isDue?'due':null,(isDue?K.ui.due:K.ui.next)+' '+nr));
        if(isDue){var b=el('button',null,K.ui.revised);b.onclick=function(){var y=st(t.n);y.r=(y.r||0)+1;y.d=TODAY;S.t[t.n]=y;save();render();};meta.appendChild(b);}}
      var a=el('a',null,'▶ YouTube');a.href=t.yt;a.target='_blank';a.rel='noopener';meta.appendChild(a);
      row.appendChild(meta);det.appendChild(row);
    });
    if(filt==='__due'){det.open=true;if(det.querySelectorAll('.topic').length===0)return;}
    if(filt===''||filt==='__due'||filt===sub.name)box.appendChild(det);
  });
  var pct=Math.round(100*done/K.topics.length);
  document.getElementById('pct').textContent=pct+'%';document.getElementById('pbar').style.width=pct+'%';
  document.getElementById('due').textContent=due;
}
function days(){var b=document.getElementById('days'),l=document.getElementById('dayslbl');
  if(!K.exam){b.textContent='—';l.textContent=K.ui.na;return;}
  var p=K.exam.split('-'),t=new Date();t.setHours(0,0,0,0);var n=Math.max(0,Math.round((new Date(+p[0],+p[1]-1,+p[2])-t)/864e5));b.textContent=n;l.textContent=K.ui.days;}
var f=document.getElementById('filter');
[['',K.ui.all],['__due',K.ui.dueonly]].concat(K.subjects.map(function(s){return [s.name,s.name];})).forEach(function(o){var op=el('option',null,o[1]);op.value=o[0];f.appendChild(op);});
f.onchange=render;
var lb=document.getElementById('lang');
if(lb){lb.onclick=function(){S.lang=S.lang==='te'?'en':'te';lb.className=S.lang==='te'?'on':'';save();render();};lb.className=S.lang==='te'?'on':'';}
document.getElementById('reset').onclick=function(){if(window.confirm(K.ui.confirm)){S={t:{},lang:S.lang};save();render();}};
if(!canSave)warn();
days();render();
})();
"""


def _h(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_html(d, out):
    te = "te" in d["languages"]
    ts = topics(d)
    ex = exam_date(d)
    data = {"id": d["id"], "exam": ex.isoformat() if ex else None, "rev": d["plan"]["revision_days"], "statuses": STATUSES,
            "subjects": [{"name": s["name"], "te": s.get("name_te", "")} for s in d["subjects"]],
            "topics": [{"n": t["n"], "subject": t["subject"], "en": t["en"], "te": t["te"], "yt": yt_search(t["query"])} for t in ts],
            "ui": {"due": "Revise now:", "next": "Next revision:", "revised": "Revised ✓", "na": "exam date not announced", "days": "days to the exam",
                   "all": "All subjects", "dueonly": "Due for revision", "confirm": "Clear all progress on this phone?",
                   "nosave": "This browser is not saving progress (private mode?). Your marks will be lost when you close the page."}}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    tokens = TOKENS.read_text(encoding="utf-8")
    rows = []
    for k in d["key_dates"]:
        ev = _h(k["event"]) + (f"<br><span class=note>{_h(k['event_te'])}</span>" if te and k.get("event_te") else "")
        when = dt.date.fromisoformat(k["date"]).strftime("%d %b %Y") if k.get("date") else "—"
        src = f' · <a href="{_h(k["source"])}" rel="noopener" target="_blank">official</a>' if k.get("source") else ""
        note = f"<br><span class=note>{_h(k['note'])}</span>" if k.get("note") else ""
        rows.append(f'<tr><td>{ev}{note}</td><td>{when}<br><span class="badge {k["status"]}">{k["status"].replace("_", " ")}</span>{src}</td></tr>')
    mats = "".join(f'<li><a href="{_h(m["url"])}" rel="noopener" target="_blank">{_h(m["title"])}</a> <span class=note>({_h(m["status"].replace("_", " ").lower())})</span></li>' for m in d["materials"])
    vids = "".join(
        f'<li>{_h(s["name"])}: ' + (f'<a href="{_h(v["url"])}" rel="noopener" target="_blank">video</a>' if v.get("url") else
                                     f'<span class=note>to curate ·</span> <a href="{_h(yt_search(v["query"]))}" rel="noopener" target="_blank">search “{_h(v["query"])}”</a>') + "</li>"
        for s in d["subjects"] for v in (s.get("videos") or []))
    stages = "".join(f"<li>{_h(s['name'])}" + (f" <span class=note>· {_h(s['name_te'])}</span>" if te and s.get("name_te") else "") + "</li>" for s in d["stages"])
    lang_btn = '<button id="lang" type="button">తెలుగు</button>' if te else ""
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_h(d['short'])} · Kalpa Exam Kit</title><meta name="color-scheme" content="light dark">
<style>
{tokens}
{CSS}</style></head><body>
<header class="hero"><div class="wrap" style="padding-bottom:0"><h1>{_h(d['short'])} tracker</h1>
<p>{_h(d['name'])}{(' · ' + _h(d['name_te'])) if te and d.get('name_te') else ''}</p>
<p>{_h(d['body'])} · <a href="{_h(d['official_site'])}" rel="noopener" target="_blank">official site</a> · dates checked {_h(d['checked_on'])}</p></div></header>
<div class="vine" aria-hidden="true"></div>
<main class="wrap">
<div id="warn" role="status"></div>
<div class="stats"><div class="stat"><b id="days">—</b><span id="dayslbl"></span></div>
<div class="stat"><b id="pct">0%</b><span>syllabus done</span></div><div class="stat"><b id="due">0</b><span>revisions due</span></div></div>
<div class="bar" aria-hidden="true"><i id="pbar"></i></div>
<h2>Exam dates and alerts</h2><div class="card"><table>{''.join(rows)}</table></div>
<p class="note">Only CONFIRMED dates come from the official site. NOT ANNOUNCED means no official date yet: we alert you when it is out.</p>
<h2>Syllabus ({len(ts)} topics)</h2>
<div class="tools"><select id="filter" aria-label="Show"></select>{lang_btn}<button id="reset" type="button">Reset</button></div>
<div id="syl"></div>
<h2>Exam stages</h2><ul class="links">{stages}</ul>
<h2>Best free material</h2><ul class="links">{mats}</ul>
<h2>Best YouTube videos</h2><ul class="links">{vids}</ul>
<p class="note">Progress is saved on this phone only. Not an official {_h(d['body'])} product. Kalpa Labs · Udyam UDYAM-TS-02-0382711</p>
</main>
<script type="application/json" id="kit">{blob}</script>
<script>{JS}</script>
</body></html>
"""
    out = pathlib.Path(out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(page, encoding="utf-8")
    return out


# ------------------------------------------------------------------ all
def exam_files():
    return sorted(EXAMS.glob("*.yaml"))


def build_all(path, outdir=DIST, start=None, pinned=None):
    d = load(path)
    errs = validate(d)
    if errs: raise ValueError(f"{d.get('_file')}: " + "; ".join(errs))
    start = start or dt.date.today()
    o = pathlib.Path(outdir) / d["id"]
    return {"xlsx": build_xlsx(d, o / f"{d['id']}-tracker.xlsx", pinned), "ics": build_ics(d, o / f"{d['id']}-calendar.ics", start),
            "html": build_html(d, o / f"{d['id']}-tracker.html"), "telegram": build_telegram(d, o / f"{d['id']}-telegram.json", start)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--exam", action="append", help="exam id (file name without .yaml); repeat for more; default all")
    ap.add_argument("--start", help="first study day, YYYY-MM-DD (default today)")
    ap.add_argument("--out", default=str(DIST)); ap.add_argument("--check", action="store_true", help="validate only")
    a = ap.parse_args(argv)
    files = [EXAMS / f"{x}.yaml" for x in a.exam] if a.exam else exam_files()
    bad = 0
    for f in files:
        d = load(f); errs = validate(d)
        print(f"{'OK ' if not errs else 'BAD'} {f.name}: {len(topics(d)) if not errs else '-'} topics" + ("".join(f"\n    - {x}" for x in errs)))
        bad += bool(errs)
        if not errs and not a.check:
            for kind, p in build_all(f, a.out, dt.date.fromisoformat(a.start) if a.start else None).items(): print(f"    {kind}: {p}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

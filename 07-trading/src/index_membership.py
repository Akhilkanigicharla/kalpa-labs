"""A290: point-in-time Nifty 100 / Nifty 200 membership from NSE Indices press releases.

Why: a momentum backtest on TODAY's index list keeps only the survivors (A289 bias check: 25.9%/yr fell to 9-10.5%).
How: every replacement press release on niftyindices.com/press-release (official, public PDFs) is parsed into
events (date, index, in/out, company, symbol). Starting from today's official constituent CSV we walk BACK in time,
undoing each change, so each month-end gets the list that was really in the index then.

Old releases (before about 2012) give company names only; names are mapped to symbols with NSE's own files
(EQUITY_L.csv, namechange.csv, symbolchange.csv) and the name+symbol pairs of later releases. A name that cannot be
mapped keeps an id "NAME:<key>" so the walk still counts it (it just has no price later).
Nifty 100 = Nifty 50 + Nifty Next 50: a release without its own Nifty 100 / CNX 100 section is derived from those two.

Run (cloud only): python3 07-trading/src/index_membership.py   -> 07-trading/research/index_membership/*.csv
"""
from __future__ import annotations

import csv
import difflib
import html
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "nse_releases"          # git-ignored (07-trading/data/)
OUT = ROOT / "research" / "index_membership"
SITE = "https://www.niftyindices.com"
ARCH = "https://archives.nseindia.com/content"
UA = "Mozilla/5.0"  # the site gives an empty reply to unusual agents

INDEX_RE = {
    "N50": re.compile(r"(s&p\s+)?(cnx\s+)?nifty(\s*50)?"),
    "NN50": re.compile(r"(cnx\s+)?nifty\s+junior|nifty\s+next\s*50"),
    "N100": re.compile(r"(s&p\s+)?cnx\s*100|nifty\s*100"),
    "N200": re.compile(r"(s&p\s+)?cnx\s*200|nifty\s*200"),
}
HEAD = re.compile(r"^\s*(?:\(\d{1,2}\)|\d{1,2}\)|\(?[a-zA-Z]\)|[A-Z]\.)\s+(\S.{0,80}?)\s*:?\s*$")
ROW = re.compile(r"^\s*(\d{1,3})\s{1,}(\S.*?)\s*$")
SYM = re.compile(r"^[A-Z0-9][A-Z0-9&\-]{0,19}$")
ISIN = re.compile(r"^IN[A-Z0-9]{10}$")
MONTHS = "january february march april may june july august september october november december".split()
DATE_RE = re.compile(r"(?i)\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})\s*,?\s*(\d{4})")
SKIP_TITLE = re.compile(r"(?i)fixed income|bond|g-?sec|gilt|\bsdl\b|t-bill|money market|target maturity|debt")

# Releases that never took effect as printed (read from NSE's own follow-up releases):
SUPERSEDED = {
    "/Press_Release/ind_prs18022020.pdf": "Mar 2020 review deferred (ind_prs23032020, ind_prs25032020); Yes Bank "
                                          "advanced to 19 Mar (ind_prs16032020); rest re-announced for 26 Jun 2020 "
                                          "(ind_prs13052020, ind_prs10062020)",
}
# Revocation tables ("Index Name | Security | Symbol | Remarks") are rare and laid out unevenly; typed in by hand from
# the release itself. A same-day in + out of one stock cancels in net_changes().
MANUAL = [
    (date(2024, 3, 28), "N200", "out", "IREDA", "/Press_Release/ind_prs19032024.pdf"),     # inclusion revoked
    (date(2024, 3, 28), "N200", "in", "BSE", "/Press_Release/ind_prs19032024.pdf"),       # included instead
    (date(2024, 9, 30), "N200", "in", "IDEA", "/Press_Release/ind_prs25092024.pdf"),      # exclusion revoked
    (date(2024, 9, 30), "N200", "out", "CENTRALBK", "/Press_Release/ind_prs25092024.pdf"),  # inclusion revoked
]
OCR_MARK = "#OCR tesseract"
DATE_FIX = {"/Press_Release/ind_prs07112013.pdf": (date(2013, 11, 18), "holiday moved, ind_prs13112013"),
            "/Press_Release/ind_prs13112013.pdf": (date(2013, 11, 18), "its own annexure repeats the 7 Nov changes")}


@dataclass(frozen=True)
class Event:
    eff: date
    index: str
    action: str       # "in" | "out"
    name: str
    symbol: str       # symbol as printed ("" if the release had none)
    source: str


def index_of(heading: str) -> str | None:
    h = re.sub(r"\s+", " ", heading.lower().replace("index", "").strip(" :.-"))
    for k, rx in INDEX_RE.items():
        if rx.fullmatch(h):
            return k
    return None


def first_date(text: str) -> date | None:
    m = re.search(r"(?is)effective\s+(?:from|on)?\s*(.{0,60})", text)
    for chunk in ([m.group(1)] if m else []) + [text]:
        d = DATE_RE.search(chunk)
        if d:
            return date(int(d.group(3)), MONTHS.index(d.group(1).lower()) + 1, int(d.group(2)))
    return None


def parse_row(line: str) -> tuple[str, str] | None:
    m = ROW.match(line)
    if not m or len(m.group(2)) < 3:
        return None
    parts = [p for p in re.split(r"\s{2,}", m.group(2).strip()) if p]
    sym = ""
    while len(parts) > 1 and (SYM.match(parts[-1]) or ISIN.match(parts[-1])):
        p = parts.pop()
        if SYM.match(p) and p not in ("EQ", "BE") and not sym:
            sym = p
    name = " ".join(parts).strip()
    if not re.search(r"[a-z]", name) or name[0].islower() or re.match(r"(?i)sr\.?\s*no|company\s+name", name):
        return None
    return name, sym


DOT_HEAD = re.compile(r"^\s*\d{1,2}\.\s+(\S.{0,45}?)\s*:?\s*$")
INVERTED = re.compile(r"(?is)\(symbol:\s*([A-Z0-9&\-]+)\)\s*shall\s+be\s+(excluded|included)\s+(?:from|in)\s+the\s+"
                      r"following\s+indices")


def _dot_head(line: str):
    """'1. CNX Nifty Junior index:' is a heading; '1. BSE Ltd. (average free-float ...' is a note."""
    m = DOT_HEAD.match(line)
    return m if m and (index_of(m.group(1)) or re.search(r"(?i)\b(nifty|cnx|index)\b", m.group(1))) else None


def parse_inverted(text: str, eff: date, source: str) -> list[Event]:
    """'Tata Motors DVR (Symbol: TATAMTRDVR) shall be excluded from the following indices:' + a table of index names."""
    out = []
    for m in INVERTED.finditer(text):
        for line in text[m.end():].splitlines()[1:40]:
            r = ROW.match(line)
            if r is None and line.strip() and not line.strip().lower().startswith("sr"):
                break
            ix = index_of(r.group(2)) if r else None
            if ix:
                out.append(Event(eff, ix, "out" if m.group(2).lower() == "excluded" else "in", m.group(1), m.group(1), source))
    return out


def parse_ocr_row(line: str) -> tuple[str, str] | None:
    """OCR tables lose the column gaps and often the serial number: 'Bank of Baroda BANKBARODA', 'MRF Ltd.'."""
    t = re.sub(r"^\s*\d{1,3}\s+", "", re.sub(r"[|_\[\]]", " ", line)).split()
    if len(t) < 2 or re.match(r"(?i)sr\.?\s*no|company\s+name", " ".join(t)) or not re.search(r"[a-z]", " ".join(t)):
        return None
    sym = t.pop() if SYM.match(t[-1]) and len(t[-1]) > 1 else ""
    return " ".join(t), sym


def parse_release(text: str, source: str, eff: date | None = None) -> list[Event]:
    """Events for N50 / NN50 / N100 / N200 found in one press release text (pdftotext -layout, or OCR)."""
    ocr = text.startswith(OCR_MARK)
    eff = eff or first_date(text)
    if eff is None:
        return []
    out, cur, mode = [], None, None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        hm = HEAD.match(line) or _dot_head(line)
        if hm:
            cur, mode = index_of(hm.group(1) if hm else s), None
            continue
        low = s.lower()
        if low.startswith("note") or "also be applicable" in low:
            mode = None
            continue
        if re.search(r"(following|below)\b.{0,40}\b(exclud|includ)|being (exclud|includ)", low):
            m = re.search(r"exclud|includ", low[re.search(r"following|below|being", low).start():])
            mode = "out" if m.group(0) == "exclud" else "in"
            continue
        if cur and mode:
            r = parse_ocr_row(line) if ocr else parse_row(line)
            if r:
                out.append(Event(eff, cur, mode, r[0], r[1], source))
    return out + parse_inverted(text, eff, source)


# ---------- names -> symbols ----------
def key(name: str, loose: bool = False) -> str:
    n = html.unescape(name).lower().replace("&", " and ").replace("corpn", "corporation")
    n = re.sub(r"\(.*?\)", lambda m: m.group(0)[1:-1], n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    drop = {"ltd", "limited", "the"} | ({"company", "industries", "corporation", "co", "inds", "enterprises",
                                         "and", "of", "india"} if loose else set())
    return " ".join(w for w in n.split() if w not in drop)


class Resolver:
    def __init__(self, pairs: list[tuple[str, str]], symchange: list[tuple[str, str, date]]):
        self.next = {}
        for old, new, _ in sorted(symchange, key=lambda x: x[2]):
            if old != new:
                self.next[old] = new
        self.strict, self.loose = {}, {}
        for name, sym in pairs:
            c = self.canon(sym)
            self.strict.setdefault(key(name), set()).add(c)
            self.loose.setdefault(key(name, True), set()).add(c)

    def canon(self, sym: str) -> str:
        seen = set()
        while sym in self.next and sym not in seen:
            seen.add(sym)
            sym = self.next[sym]
        return sym

    def resolve(self, name: str, sym: str) -> str:
        if sym:
            return self.canon(sym)
        for table, k in ((self.strict, key(name)), (self.loose, key(name, True))):
            hit = table.get(k, set())
            if len(hit) == 1:
                return next(iter(hit))
        close = difflib.get_close_matches(key(name, True), list(self.loose), n=2, cutoff=0.93)   # 'System' vs 'Systems'
        if len(close) == 1 and len(self.loose[close[0]]) == 1:
            return next(iter(self.loose[close[0]]))
        return "NAME:" + key(name, True).replace(" ", "_")


# ---------- the walk back ----------
def net_changes(events: list[Event], rid) -> dict[tuple[date, str], dict[str, set[str]]]:
    """(eff, index) -> {'in': ids, 'out': ids}; N100 derived from N50+NN50 when a release has no N100 section."""
    g: dict[tuple[date, str, str], dict[str, set[str]]] = {}
    for e in events:
        g.setdefault((e.eff, e.source, e.index), {"in": set(), "out": set()})[e.action].add(rid(e))
    res: dict[tuple[date, str], dict[str, set[str]]] = {}
    for (eff, src, ix), ch in g.items():
        tgt = res.setdefault((eff, ix), {"in": set(), "out": set()})
        tgt["in"] |= ch["in"]; tgt["out"] |= ch["out"]
    for (eff, src) in {(k[0], k[1]) for k in g}:
        if (eff, src, "N100") in g:
            continue
        a, b = g.get((eff, src, "N50"), {"in": set(), "out": set()}), g.get((eff, src, "NN50"), {"in": set(), "out": set()})
        inn, out = a["in"] | b["in"], a["out"] | b["out"]
        if inn - out or out - inn:
            t = res.setdefault((eff, "N100"), {"in": set(), "out": set()})
            t["in"] |= inn - out; t["out"] |= out - inn
    for ch in res.values():            # same id in and out on one day (moved between sections) = no change
        both = ch["in"] & ch["out"]
        ch["in"] -= both; ch["out"] -= both
    return res


def walk_back(today: set[str], changes: dict[tuple[date, str], dict[str, set[str]]], ix: str, asof: date,
              months: list[date]) -> tuple[dict[date, set[str]], list[str]]:
    """Membership at each month-end (as held at that day's close) + anomalies found while undoing changes."""
    steps = sorted([(d, ch) for (d, i), ch in changes.items() if i == ix and d <= asof], key=lambda x: x[0], reverse=True)
    cur, notes, out, si = set(today), [], {}, 0
    for m in sorted(months, reverse=True):
        while si < len(steps) and steps[si][0] > m:          # change effective after month-end m: undo it
            d, ch = steps[si]
            for s in ch["in"]:
                if s not in cur:
                    notes.append(f"{d} {ix} undo-in {s}: not a member")
                cur.discard(s)
            for s in ch["out"]:
                if s in cur:
                    notes.append(f"{d} {ix} undo-out {s}: already a member")
                cur.add(s)
            si += 1
        out[m] = set(cur)
    return out, notes


def month_ends(start: date, end: date) -> list[date]:
    out, y, mo = [], start.year, start.month
    while (y, mo) <= (end.year, end.month):
        ny, nm = (y + 1, 1) if mo == 12 else (y, mo + 1)
        out.append(date.fromordinal(date(ny, nm, 1).toordinal() - 1))
        y, mo = ny, nm
    return [d for d in out if d <= end]


# ---------- fetching (cloud only) ----------
def _get(url: str, path: Path) -> Path:
    if not path.exists() or path.stat().st_size == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sfL", "-m", "60", "--retry", "3", "-A", UA, "-o", str(path), url], check=True)
    return path


def releases(min_year: int = 2010) -> list[tuple[str, str]]:
    s = _get(f"{SITE}/press-release", CACHE / "press-release.html").read_text(encoding="utf-8", errors="ignore")
    out = []
    for h, t in re.findall(r"href='(/Press_Release/[^']+\.pdf)'[^>]*>([^<]+)</a>", s):
        m = re.search(r"_prs\d{4}(\d{4})", h)
        t = html.unescape(t).strip()
        if m and int(m.group(1)) >= min_year and not SKIP_TITLE.search(t):
            out.append((h, t))
    return sorted(set(out))


def _pdf_text(pdf: Path) -> str:
    r = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True)
    if len(r.stdout.strip()) > 100:
        return r.stdout
    # scanned release (no text layer): OCR each page with tesseract (Apache-2.0, cloud only)
    pages = []
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", "200", "-png", str(pdf), f"{d}/p"], check=False)
        for img in sorted(Path(d).glob("p*.png")):
            o = subprocess.run(["tesseract", str(img), "-", "--psm", "6"], capture_output=True, text=True)
            pages.append(o.stdout)
    return OCR_MARK + "\n" + "\n".join(pages)


def release_text(href: str) -> str:
    txt = CACHE / "txt" / (Path(href).stem + ".txt")
    if not txt.exists() or txt.stat().st_size < 100:
        pdf = CACHE / "pdf" / Path(href).name
        pdf.unlink(missing_ok=True)                    # a short text = a cut download last time: fetch again
        try:
            _get(SITE + href, pdf)
        except subprocess.CalledProcessError:
            return ""                                   # missing file: shows up in the count check, not fatal
        txt.parent.mkdir(parents=True, exist_ok=True)
        txt.write_text(_pdf_text(pdf), encoding="utf-8")
        pdf.unlink(missing_ok=True)
    return txt.read_text(encoding="utf-8", errors="ignore")


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", errors="ignore", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]


IXS = ("N50", "N100", "N200")


def load_monthly(ix: str = "N100") -> dict[date, set[str]]:
    """{month_end: member ids} from the committed file (no network)."""
    with open(OUT / f"{ix.lower()}_monthly.csv") as f:
        return {date.fromisoformat(r["month_end"]): set(r["members"].split()) for r in csv.DictReader(f)}


def build(asof: date | None = None) -> dict:
    asof = asof or date.today()
    files = {n: _get(f"{ARCH}/{p}", CACHE / n) for n, p in [
        ("EQUITY_L.csv", "equities/EQUITY_L.csv"), ("namechange.csv", "equities/namechange.csv"),
        ("symbolchange.csv", "equities/symbolchange.csv"), ("n100.csv", "indices/ind_nifty100list.csv"),
        ("n200.csv", "indices/ind_nifty200list.csv"),
        ("n50.csv", "indices/ind_nifty50list.csv")]}
    events = [e for h, t in releases() if h not in SUPERSEDED
              for e in parse_release(release_text(h), h, DATE_FIX.get(h, (None,))[0])]
    events += [Event(d, ix, a, sym, sym, src) for d, ix, a, sym, src in MANUAL]
    symch = [(r["OLD SYMBOL"], r["NEW SYMBOL"], datetime.strptime(r["EFFECTIVE DATE"], "%d-%b-%Y").date())
             for r in read_csv(files["symbolchange.csv"]) if r.get("EFFECTIVE DATE")]
    pairs = [(e.name, e.symbol) for e in events if e.symbol]
    pairs += [(r["NAME OF COMPANY"], r["SYMBOL"]) for r in read_csv(files["EQUITY_L.csv"])]
    for r in read_csv(files["namechange.csv"]):
        pairs += [(r["OLD NAME OF THE COMPANY"], r["SYMBOL"]), (r["NEW NAME OF THE COMPANY"], r["SYMBOL"])]
    cur = {ix: [(r["Company Name"], r["Symbol"]) for r in read_csv(files[f])] for ix, f in (("N50", "n50.csv"), ("N100", "n100.csv"), ("N200", "n200.csv"))}
    for v in cur.values():
        pairs += v
    rs = Resolver(pairs, symch)
    rid = lambda e: rs.resolve(e.name, e.symbol)  # noqa: E731
    changes = net_changes(events, rid)
    months = month_ends(date(2011, 1, 1), asof)
    res = {"asof": asof, "events": events, "rid": rid, "months": months}
    for ix in IXS:
        mem, notes = walk_back({rs.canon(s) for _, s in cur[ix]}, changes, ix, asof, months)
        res[ix] = (mem, notes)
    return res


def write(res: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["effective", "index", "action", "company", "symbol_printed", "id", "source"])
        for e in sorted(res["events"], key=lambda e: (e.eff, e.index, e.action, e.name)):
            w.writerow([e.eff, e.index, e.action, e.name, e.symbol, res["rid"](e), SITE + e.source])
    for ix in IXS:
        mem, notes = res[ix]
        with open(OUT / f"{ix.lower()}_monthly.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["month_end", "count", "members"])
            for m in sorted(mem):
                w.writerow([m, len(mem[m]), " ".join(sorted(mem[m]))])
        (OUT / f"{ix.lower()}_anomalies.txt").write_text("\n".join(notes) + ("\n" if notes else ""))


if __name__ == "__main__":
    r = build()
    write(r)
    for ix in IXS:
        mem, notes = r[ix]
        c = [len(v) for v in mem.values()]
        names = sum(1 for v in mem.values() for s in v if s.startswith("NAME:"))
        print(f"{ix}: {len(mem)} months, count {min(c)}-{max(c)}, anomalies {len(notes)}, unmapped member-months {names}")

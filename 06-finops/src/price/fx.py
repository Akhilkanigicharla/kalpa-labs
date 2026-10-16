"""USD -> INR reference rate cache with its source.

The rate is the FBIL USD/INR reference rate as RBI shows it on its home page
('Current Rates', 'INR / 1 USD ... (As at 1.00pm of <date>) (Source : FBIL)').
Rates live in data/usd_inr.json; every priced row carries the rate, date and source.

    python -m price.fx show
    python -m price.fx refresh        # fetch rbi.org.in, append if new (run weekly in Actions)
    python -m price.fx add 2026-10-13 95.80 "manual: RBI page read by Akhil"
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent / "data" / "usd_inr.json"
RBI_URL = "https://www.rbi.org.in/Home.aspx/scripts/home.aspx"


class FxError(Exception):
    pass


class StaleRateError(FxError):
    pass


@dataclass(frozen=True)
class FxRate:
    date: str
    inr_per_usd: Decimal
    source: str
    source_url: str = ""
    retrieved: str = ""

    def to_json(self) -> dict:
        d = asdict(self)
        d["inr_per_usd"] = str(self.inr_per_usd)
        return d


class FxTable:
    def __init__(self, rates: list[FxRate]):
        if not rates:
            raise FxError("no USD/INR rates cached")
        self.rates = sorted(rates, key=lambda r: r.date)

    @classmethod
    def load(cls, path: str | Path = DEFAULT_PATH) -> "FxTable":
        obj = json.loads(Path(path).read_text())
        return cls([FxRate(r["date"], Decimal(r["inr_per_usd"]), r["source"], r.get("source_url", ""),
                           r.get("retrieved", "")) for r in obj["rates"]])

    def latest(self) -> FxRate:
        return self.rates[-1]

    def for_date(self, d: str | date, max_age_days: int = 7) -> FxRate:
        """Newest rate on or before d. Raises StaleRateError if it is older than max_age_days
        (weekends and holidays have no fixing, so a few days' gap is normal)."""
        d = d if isinstance(d, date) else date.fromisoformat(str(d)[:10])
        best = None
        for r in self.rates:
            if date.fromisoformat(r.date) <= d:
                best = r
        if best is None:
            raise StaleRateError(f"no cached USD/INR rate on or before {d}; earliest is {self.rates[0].date}")
        age = (d - date.fromisoformat(best.date)).days
        if age > max_age_days:
            raise StaleRateError(f"USD/INR rate {best.date} is {age} days older than {d}")
        return best


def parse_rbi_home(html: str, retrieved: str | None = None) -> FxRate:
    """Read 'INR / 1 USD : 95.7485' and '(As at 1.00pm of October 12, 2026)' from RBI's page."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;|\s+", " ", text)
    m = re.search(r"INR\s*/\s*1\s*USD\s*:\s*([0-9]+\.[0-9]+)", text)
    if not m:
        raise FxError("INR / 1 USD not found on RBI page")
    d = re.search(r"As at [0-9.:]+\s*[ap]m of ([A-Z][a-z]+ [0-9]{1,2}, [0-9]{4})", text)
    if not d:
        raise FxError("'As at ... of <date>' not found on RBI page")
    day = datetime.strptime(d.group(1), "%B %d, %Y").date().isoformat()
    src = "FBIL" if re.search(r"Source\s*:\s*FBIL", text) else "RBI"
    return FxRate(day, Decimal(m.group(1)),
                  f"RBI home page 'Current Rates' ({src} reference rate, as at 1.00pm of {d.group(1)})",
                  RBI_URL, retrieved or date.today().isoformat())


def add_rate(rate: FxRate, path: str | Path = DEFAULT_PATH) -> bool:
    """Append a rate if its date is new. Returns True if the file changed."""
    p = Path(path)
    obj = json.loads(p.read_text())
    if any(r["date"] == rate.date for r in obj["rates"]):
        return False
    obj["rates"].append(rate.to_json())
    obj["rates"].sort(key=lambda r: r["date"])
    p.write_text(json.dumps(obj, indent=2) + "\n")
    return True


def fetch_rbi(url: str = RBI_URL, timeout: int = 30) -> FxRate:  # network; not used in tests
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "ledger-peaks-fx/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return parse_rbi_home(resp.read().decode("utf-8", "replace"))


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "show"
    if cmd == "show":
        r = FxTable.load().latest()
        print(f"{r.date}  ₹{r.inr_per_usd}/USD  ({r.source})")
    elif cmd == "refresh":
        # Reading RBI's home page HTML is fragile scraping (REA audit, 16 Oct 2026). Prefer the official reference
        # rate typed in with `add`; the page read stays available only when asked for explicitly.
        if "--from-rbi-home-page" not in argv:
            print("Use: fx.py add YYYY-MM-DD <INR per USD> <source>  (official RBI/FBIL reference rate).\n"
                  "Reading the RBI home page is opt-in: fx.py refresh --from-rbi-home-page", file=sys.stderr)
            return 2
        r = fetch_rbi()
        print(("added " if add_rate(r) else "already have ") + f"{r.date} ₹{r.inr_per_usd}")
    elif cmd == "add" and len(argv) == 4:
        r = FxRate(argv[1], Decimal(argv[2]), argv[3], "", date.today().isoformat())
        print("added" if add_rate(r) else "date already present")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

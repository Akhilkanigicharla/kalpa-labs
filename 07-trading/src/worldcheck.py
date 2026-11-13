"""World Check: a daily pre-market / post-close briefing for the Track A bot. ALERTS ONLY.

What it reads (all free, no keys): global markets via Yahoo Finance (S&P 500, Nasdaq-100,
Nikkei, Hang Seng, US 10-year yield, dollar index, USD/INR, Brent oil, US VIX, India VIX,
Nifty), the event calendar in `events.json` (Fed, RBI, Budget, elections; every date has two
sources), and the latest headlines from the official Fed and RBI press RSS feeds.

Why alerts only: on Nifty 2008-2026 every one of these risk rules was tested through the gate
(trials T0015-T0019, 13 Nov 2026) and NONE improved the trend bot: each gave slightly less
money and no smaller worst fall. Event days cut both ways (election results: +17.7% in 2009,
-5.9% in 2024). So they inform Akhil; they do not change orders. A rule may become a trading
input only after it passes the gate. Not investment advice.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

import pandas as pd

IST = ZoneInfo("Asia/Kolkata")
EVENTS_FILE = Path(__file__).resolve().parents[1] / "research" / "events.json"
TICKERS = {
    "Nifty 50": "^NSEI", "India VIX": "^INDIAVIX", "S&P 500": "^GSPC", "Nasdaq-100": "^NDX",
    "Nikkei 225": "^N225", "Hang Seng": "^HSI", "US 10Y yield": "^TNX", "Dollar index": "DX-Y.NYB",
    "USD/INR": "INR=X", "Brent oil": "BZ=F", "US VIX": "^VIX",
}
FEEDS = {
    "Fed": "https://www.federalreserve.gov/feeds/press_all.xml",
    "RBI": "https://www.rbi.org.in/pressreleases_rss.xml",
}
Fetcher = Callable[[str], pd.Series]


@dataclass
class Report:
    asof: date
    snapshot: dict = field(default_factory=dict)      # name -> (last, 1-day %, 3-month %)
    flags: dict = field(default_factory=dict)         # rule -> (on, why)
    events: list = field(default_factory=list)        # upcoming within the window
    headlines: dict = field(default_factory=dict)     # source -> [titles]
    errors: list = field(default_factory=list)

    def text(self) -> str:
        on = [k for k, (v, _) in self.flags.items() if v]
        lines = [f"WORLD CHECK · {self.asof.isoformat()} · alerts only (the bot trades the tested trend rule)",
                 f"Risk flags on: {len(on)}/4" + (f" ({', '.join(on)})" if on else " (calm)")]
        for k, (v, why) in self.flags.items():
            lines.append(f"  [{'!' if v else ' '}] {k}: {why}")
        lines.append("Markets (last, 1 day, 3 months):")
        for k, (last, d1, m3) in self.snapshot.items():
            unit = "%" if k == "US 10Y yield" else ""
            lines.append(f"  {k:13} {last:>10,.2f}{unit}  {d1:+6.2f}%  {m3:+7.2f}%")
        lines.append("Coming up (14 days):" if self.events else "Coming up (14 days): nothing on the calendar")
        lines += [f"  {e['date']} {e['name']}" for e in self.events]
        for src, titles in self.headlines.items():
            lines.append(f"Latest {src} news:")
            lines += [f"  - {t}" for t in titles]
        if self.errors:
            lines.append("Could not load: " + "; ".join(self.errors))
        lines.append("Not investment advice.")
        return "\n".join(lines)


def _yf(ticker: str) -> pd.Series:
    import yfinance as yf  # lazy: tests need no network
    d = yf.Ticker(ticker).history(period="2y", auto_adjust=True, actions=False)
    s = d["Close"].dropna()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s


def flags_from(series: dict[str, pd.Series]) -> dict:
    """The four pre-registered rules (same definitions as the 13 Nov gate test)."""
    out = {}
    spx = series.get("S&P 500")
    if spx is not None and len(spx) >= 200:
        ma = spx.rolling(200).mean().iloc[-1]
        out["Global trend"] = (bool(spx.iloc[-1] < ma), f"S&P 500 {spx.iloc[-1]:,.0f} vs 200-day avg {ma:,.0f}")
    vix = series.get("India VIX")
    if vix is not None and len(vix) >= 200:
        q = vix.tail(252).quantile(0.8)
        out["Fear"] = (bool(vix.iloc[-1] > q), f"India VIX {vix.iloc[-1]:.1f} vs 1-year top-20% line {q:.1f}")
    y, fx = series.get("US 10Y yield"), series.get("USD/INR")
    if y is not None and fx is not None and len(y) > 63 and len(fx) > 63:
        dy, dfx = y.iloc[-1] - y.iloc[-64], fx.iloc[-1] / fx.iloc[-64] - 1
        out["Dollar squeeze"] = (bool(dy >= 0.5 and dfx >= 0.02),
                                 f"US 10Y {dy:+.2f} pts and USD/INR {dfx:+.1%} in 3 months (alert at +0.50 and +2%)")
    b = series.get("Brent oil")
    if b is not None and len(b) > 63:
        ch = b.iloc[-1] / b.iloc[-64] - 1
        out["Oil shock"] = (bool(ch >= 0.30), f"Brent {ch:+.1%} in 3 months (alert at +30%)")
    return out


def upcoming(events: list[dict], today: date, days: int = 14) -> list[dict]:
    end = today + timedelta(days=days)
    return sorted((e for e in events if today <= date.fromisoformat(e["date"]) <= end), key=lambda e: e["date"])


def parse_rss(xml_text: str, n: int = 3) -> list[str]:
    root = ET.fromstring(xml_text.lstrip("﻿"))
    titles = [(it.findtext("title") or "").strip() for it in root.iter("item")]
    return [t for t in titles if t][:n]


def _get(url: str, timeout: float = 10.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "kalpa-worldcheck/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (fixed https URLs above)
        return r.read().decode("utf-8", errors="replace")


def build(today: date | None = None, *, fetch: Fetcher | None = None, get: Callable[[str], str] | None = None,
          events_file: Path = EVENTS_FILE) -> Report:
    today = today or datetime.now(IST).date()
    fetch, get = fetch or _yf, get or _get
    rep = Report(today)
    series: dict[str, pd.Series] = {}
    for name, t in TICKERS.items():
        try:
            s = fetch(t)
            s = s[s.index.date <= today]
            if len(s) < 2:
                raise ValueError("too few bars")
            series[name] = s
            m3 = s.iloc[-1] / s.iloc[-64] - 1 if len(s) > 63 else float("nan")
            rep.snapshot[name] = (float(s.iloc[-1]), float(s.iloc[-1] / s.iloc[-2] - 1) * 100, float(m3) * 100)
        except Exception as e:   # one bad series never stops the report
            rep.errors.append(f"{name} ({type(e).__name__})")
    rep.flags = flags_from(series)
    try:
        rep.events = upcoming(json.loads(events_file.read_text(encoding="utf-8"))["events"], today)
    except Exception as e:
        rep.errors.append(f"events ({type(e).__name__})")
    for src, url in FEEDS.items():
        try:
            rep.headlines[src] = parse_rss(get(url))
        except Exception as e:
            rep.errors.append(f"{src} news ({type(e).__name__})")
    return rep


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="World Check briefing (alerts only)")
    p.add_argument("--out", type=Path, default=None)
    a = p.parse_args(argv)
    text = build().text()
    print(text)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Stocks-in-Play 5-minute opening-range breakout on Nifty 50 stocks (PAPER ONLY).

Method: Zarattini, Barbon & Aziz (2024), "A Profitable Day Trading Strategy For The U.S. Equity
Market", SSRN 4729284: trade only stocks with abnormal opening volume (a stand-in for news),
in the direction of the first 5-minute candle, entering on a break of its high/low, stop at
10% of the 14-day ATR, exit at the close.

India changes (13 Nov 2026):
- Yahoo shows 0 volume on the 09:15 bar for ~85% of days for NSE stocks, so "opening volume" is
  the 09:20 bar's volume vs its average over the previous 14 sessions, and entries start at
  09:25 (no look-ahead). Opening range = the 09:15 bar.
- Universe: 51 large NSE stocks with sectors; top 3 by relative volume (>= 1x).
- Forced exit 15:15 (broker MIS square-off is ~15:20). Full intraday costs + 2 bps slippage.

Test, 60 sessions 18 Aug - 13 Nov 2026: top-3 -3.7% after costs (107 trades), top-3 in busiest
sector -2.9%, all 51 stocks -6.0%, Nifty +5.7%. REJECTED. Runs on paper to build evidence.
Not investment advice.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import costs

SECTORS = {
    "Financials": "HDFCBANK ICICIBANK SBIN KOTAKBANK AXISBANK INDUSINDBK BAJFINANCE BAJAJFINSV SHRIRAMFIN HDFCLIFE SBILIFE JIOFIN",
    "IT": "TCS INFY HCLTECH WIPRO TECHM", "Energy": "RELIANCE ONGC NTPC POWERGRID COALINDIA BPCL",
    "Auto": "MARUTI M&M BAJAJ-AUTO EICHERMOT HEROMOTOCO", "FMCG": "HINDUNILVR ITC NESTLEIND BRITANNIA TATACONSUM",
    "Metals": "TATASTEEL JSWSTEEL HINDALCO", "Pharma": "SUNPHARMA CIPLA DRREDDY APOLLOHOSP",
    "Infra": "LT ULTRACEMCO GRASIM ADANIENT ADANIPORTS", "Consumer": "TITAN ASIANPAINT TRENT BEL ETERNAL BHARTIARTL",
}
SECTOR_OF = {t: s for s, ts in SECTORS.items() for t in ts.split()}
TOP_N, LOOKBACK, ATR_STOP, SLIP = 3, 14, 0.10, 2e-4
LAST_ENTRY, FORCE_EXIT = time(14, 45), time(15, 15)


@dataclass
class SipTrade:
    day: str
    symbol: str
    sector: str
    side: int
    rvol: float
    entry_at: str
    entry: float
    exit_at: str
    exit: float
    reason: str
    ret_net: float      # fraction of the position, after costs


def session(df: pd.DataFrame) -> pd.DataFrame:
    d = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].copy()
    idx = pd.DatetimeIndex(d.index)
    d.index = idx.tz_convert("Asia/Kolkata") if idx.tz is not None else idx.tz_localize("Asia/Kolkata")
    t = d.index.time
    return d[(t >= time(9, 15)) & (t < time(15, 30))]


def opening_volume(bars: pd.DataFrame) -> pd.Series:
    """Volume of each day's 09:20 bar (the 09:15 bar is often 0 in Yahoo data)."""
    second = bars.groupby(bars.index.date).nth(1)
    return pd.Series(second["volume"].values, index=[i.date() for i in second.index])


def relative_volume(bars: pd.DataFrame, day, lookback: int = LOOKBACK) -> float:
    ov = opening_volume(bars)
    prev = ov[[d for d in ov.index if d < day]].tail(lookback)
    if day not in ov.index or len(prev) < lookback or prev.mean() <= 0:
        return float("nan")
    return float(ov[day] / prev.mean())


def atr14(daily: pd.DataFrame, day) -> float:
    d = daily.rename(columns=str.lower)
    d.index = pd.DatetimeIndex(d.index).tz_localize(None).normalize() if pd.DatetimeIndex(d.index).tz is not None \
        else pd.DatetimeIndex(d.index).normalize()
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1)
    a = tr.rolling(14).mean().shift(1)          # known before today's open
    v = a.get(pd.Timestamp(day))
    return float(v) if v is not None and np.isfinite(v) else float("nan")


def trade_one(day_bars: pd.DataFrame, atr: float, cost_frac: float) -> tuple[float, str, str, float, str, float, int] | None:
    if len(day_bars) < 10 or not np.isfinite(atr) or atr <= 0:
        return None
    o = day_bars.iloc[0]
    side = 1 if o.close > o.open else (-1 if o.close < o.open else 0)
    if side == 0:
        return None
    lvl = o.high if side == 1 else o.low
    pos = None
    for ts, b in day_bars.iloc[2:].iterrows():
        if pos is None:
            if ts.time() > LAST_ENTRY:
                return None
            if (side == 1 and b.high >= lvl) or (side == -1 and b.low <= lvl):
                px = (max(lvl, b.open) if side == 1 else min(lvl, b.open)) * (1 + SLIP * side)
                pos = (px, px - side * ATR_STOP * atr, ts)
                if (side == 1 and b.low <= pos[1]) or (side == -1 and b.high >= pos[1]):
                    ex = pos[1] * (1 - SLIP * side)
                    return ((ex / px - 1) * side - cost_frac, ts.strftime("%H:%M"), ts.strftime("%H:%M"), ex, "stop", px, side)
            continue
        px, stop, at = pos
        if (side == 1 and b.low <= stop) or (side == -1 and b.high >= stop):
            ex = stop * (1 - SLIP * side)
            return ((ex / px - 1) * side - cost_frac, at.strftime("%H:%M"), ts.strftime("%H:%M"), ex, "stop", px, side)
        if ts.time() >= FORCE_EXIT:
            ex = b.close * (1 - SLIP * side)
            return ((ex / px - 1) * side - cost_frac, at.strftime("%H:%M"), ts.strftime("%H:%M"), ex, "eod", px, side)
    if pos:
        px, _, at = pos
        last = day_bars.iloc[-1]
        ex = last.close * (1 - SLIP * side)
        return ((ex / px - 1) * side - cost_frac, at.strftime("%H:%M"), day_bars.index[-1].strftime("%H:%M"), ex, "eod", px, side)
    return None


def run_day(intraday: dict[str, pd.DataFrame], daily: dict[str, pd.DataFrame], day, capital: float = 5_000.0,
            top_n: int = TOP_N) -> tuple[list[SipTrade], dict]:
    rv = {}
    for s, bars in intraday.items():
        v = relative_volume(bars, day)
        if np.isfinite(v) and v >= 1.0:
            rv[s] = v
    picks = sorted(rv, key=lambda s: -rv[s])[:top_n]
    per = capital / max(len(picks), 1)
    cost_frac = costs.intraday(per, per).total / per if picks else 0.0
    out = []
    for s in picks:
        b = intraday[s]
        r = trade_one(b[b.index.date == day], atr14(daily[s], day), cost_frac)
        if r:
            ret, ein, eout, ex, why, px, side = r
            out.append(SipTrade(str(day), s, SECTOR_OF.get(s, "?"), side, round(rv[s], 2), ein, round(px, 2), eout,
                                round(ex, 2), why, ret))
    sector_rv = {}
    for s, v in rv.items():
        sector_rv.setdefault(SECTOR_OF.get(s, "?"), []).append(v)
    return out, {k: round(float(np.mean(v)), 2) for k, v in sorted(sector_rv.items(), key=lambda kv: -np.mean(kv[1]))}


def paper_day(intraday: dict[str, pd.DataFrame], daily: dict[str, pd.DataFrame], out: Path,
              capital: float = 5_000.0) -> str:
    days = sorted(set(next(iter(intraday.values())).index.date))
    d = days[-1]
    out.mkdir(parents=True, exist_ok=True)
    done = out / "days.txt"
    seen = set(done.read_text(encoding="utf-8").split()) if done.exists() else set()
    head = f"Kalpa b7 · Stocks-in-Play 5-min ORB · PAPER · {d} · Rs {capital:,.0f}"
    if str(d) in seen:
        return head + "\nAlready done (no new session). No action."
    trades, sectors = run_day(intraday, daily, d, capital)
    led = out / "trades.csv"
    cols = ["day", "symbol", "sector", "side", "rvol", "entry_at", "entry", "exit_at", "exit", "reason", "ret_net"]
    hist = pd.read_csv(led) if led.exists() else pd.DataFrame(columns=cols)
    if trades:
        hist = pd.concat([hist, pd.DataFrame([t.__dict__ for t in trades])[cols]], ignore_index=True)
    hist.to_csv(led, index=False)
    done.write_text(" ".join(sorted(seen | {str(d)})) + "\n", encoding="utf-8")
    lines = [head, "Busiest sectors by opening volume (x normal): " +
             (", ".join(f"{k} {v}x" for k, v in list(sectors.items())[:3]) or "none above normal")]
    lines += [f"  {t.symbol:10} {t.sector:10} {'long' if t.side == 1 else 'short':5} vol {t.rvol}x in {t.entry_at} @ {t.entry} "
              f"out {t.exit_at} @ {t.exit} ({t.reason}) {t.ret_net * 100:+.2f}%" for t in trades] or ["  no breakout today"]
    if len(hist):
        day_ret = hist.groupby("day")["ret_net"].sum() / TOP_N
        lines.append(f"Running: {len(hist)} trades over {len(seen) + 1} sessions, win {(hist.ret_net > 0).mean():.0%}, "
                     f"net {((1 + day_ret).prod() - 1) * 100:+.2f}% of capital")
    lines.append("REJECTED on Aug-Nov 2026 data (-3.7% after costs). Paper only. Not advice.")
    text = "\n".join(lines)
    (out / "summary.txt").write_text(text + "\n", encoding="utf-8")
    return text


def fetch(period: str = "60d"):
    import yfinance as yf
    ticks = [t + ".NS" for t in SECTOR_OF]
    m = yf.download(ticks, period=period, interval="5m", group_by="ticker", auto_adjust=False, progress=False, threads=True)
    d = yf.download(ticks, period="6mo", interval="1d", group_by="ticker", auto_adjust=False, progress=False, threads=True)
    intra, daily = {}, {}
    for t in SECTOR_OF:
        try:
            x, y = m[t + ".NS"].dropna(), d[t + ".NS"].dropna()
        except KeyError:
            continue
        if len(x) > 500 and len(y) > 30:
            intra[t], daily[t] = session(x), y
    return intra, daily


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Stocks-in-Play ORB paper run (Nifty 50)")
    p.add_argument("--paper", type=Path, required=True)
    p.add_argument("--capital", type=float, default=5_000.0)
    a = p.parse_args(argv)
    intra, daily = fetch()
    if not intra:
        print("no data")
        return 1
    print(paper_day(intra, daily, a.paper, a.capital))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

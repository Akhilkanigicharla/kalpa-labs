"""A163: Nifty + Gold trend bot for Rs 10,000 (Akhil, 13 Nov 2026: "capital 10k, few trades").

Same honest walk-forward as Track A (gate.walk_forward: settings picked on the past only, traded on the next
block), run on each asset, then split 50/50:
  Nifty leg  signal and returns from ^NSEI (as Track A), idle cash earns 4.7%/yr (LIQUIDBEES)
  Gold leg   GOLDBEES.NS (real ETF prices), idle cash 4.7%/yr
Costs: the gate's per-trade costs PLUS the fixed DP charge (Rs 15.34 per scrip per sell day), which hurts small
accounts: on a Rs 5,000 leg one sell costs 0.31%.
Run from 07-trading/:  python -I research/a163_nifty_gold_10k.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import costs, data, gate  # noqa: E402

CAPITAL, CASH = 10_000.0, 0.047
DP = costs.rate("dp_per_scrip_sell")


def leg(close: pd.Series, capital: float):
    oos, round_trips, chosen, _ = gate.walk_forward(close, "tsmom", cash_rate=CASH)
    yrs = (oos.index[-1] - oos.index[0]).days / 365.25
    # DP charge: one per sell; spread evenly as a daily drag on this leg's capital
    drag = (round_trips / yrs) * DP / capital / 252
    return oos - drag, round_trips, yrs, chosen


def stats(r: pd.Series):
    eq = (1 + r).cumprod()
    yrs = (r.index[-1] - r.index[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    dd = (eq / eq.cummax() - 1).min()
    worst_yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1).min()
    return cagr, dd, worst_yr, eq.iloc[-1]


def main():
    nifty = pd.read_parquet(Path(__file__).resolve().parents[1] / "data" / "IDX_NSEI.parquet")
    nifty = nifty["close"].dropna()
    import yfinance as yf
    gold = yf.download("GOLDBEES.NS", start="2008-01-01", progress=False, auto_adjust=True)["Close"].squeeze().dropna()
    gold.index = pd.to_datetime(gold.index).tz_localize(None)
    # Yahoo glitch: 19-20 Dec 2019 quoted at 1/100 (the 1:100 split is otherwise adjusted). Repair those rows.
    med = gold.rolling(11, center=True, min_periods=3).median()
    bad = gold < 0.2 * med
    gold[bad] = gold[bad] * 100
    assert bad.sum() <= 5 and (gold.pct_change().dropna().abs() < 0.4).all(), "gold data still broken"
    rows = []
    for split, label in [((1.0, 0.0), "Nifty only (Track A)"), ((0.0, 1.0), "Gold only"), ((0.5, 0.5), "50/50 Nifty + Gold")]:
        parts, info = [], []
        for w, (name, s) in zip(split, [("nifty", nifty), ("gold", gold)]):
            if w == 0:
                continue
            r, rt, yrs, ch = leg(s, CAPITAL * w)
            parts.append(w * r)
            info.append(f"{name}: {rt / yrs:.1f} round trips/yr")
        r = pd.concat(parts, axis=1).dropna().sum(axis=1)
        cagr, dd, wy, mult = stats(r)
        rows.append({"bot": label, "from": r.index[0].date(), "years": round((r.index[-1] - r.index[0]).days / 365.25, 1),
                     "cagr_%": round(cagr * 100, 1), "worst_fall_%": round(dd * 100, 1), "worst_year_%": round(wy * 100, 1),
                     "rs10k_per_year": round(CAPITAL * cagr), "rs_per_trading_day": round(CAPITAL * cagr / 250, 1),
                     "trades": "; ".join(info)})
    # same period, buy and hold both (no bot), for comparison
    both = pd.concat([nifty.pct_change(), gold.pct_change()], axis=1).dropna()
    bh = both.loc[both.index >= pd.Timestamp(rows[-1]["from"])].mean(axis=1)
    cagr, dd, wy, _ = stats(bh)
    rows.append({"bot": "Hold 50/50 (no bot)", "from": bh.index[0].date(), "years": round((bh.index[-1] - bh.index[0]).days / 365.25, 1),
                 "cagr_%": round(cagr * 100, 1), "worst_fall_%": round(dd * 100, 1), "worst_year_%": round(wy * 100, 1),
                 "rs10k_per_year": round(CAPITAL * cagr), "rs_per_trading_day": round(CAPITAL * cagr / 250, 1), "trades": "none"})
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    print(df.to_string(index=False))
    df.to_csv(Path(__file__).with_name("a163_results.csv"), index=False)


if __name__ == "__main__":
    main()

"""Can Rs 5,000 make Rs 200 a day after all charges? (Akhil, 13 Nov 2026)

Tests every aggressive route that is actually open to a Rs 5,000 account in India (Nov 2026):
  A. Intraday stocks with 5x MIS leverage (SEBI cap: 20% margin) -> Rs 25,000 exposure.
     3 strategies x 2 settings x 51 Nifty stocks, 5-min bars, last ~60 days, real charges.
  B. Stocks-in-Play (relative volume pick) with 5x leverage.
  C. Nifty option BUYING with Rs 5,000 (no leverage allowed on options; lot = 65).
     Premiums are MODELLED with Black-Scholes using India VIX as volatility (no free
     intraday option prices), so treat C as an approximation.
Target: average >= Rs 200 net per trading day.
Run:  python -I research/aggressive_5k_test.py   (from 07-trading/)
"""
from __future__ import annotations

import math
import sys
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import costs, intraday, stocks_in_play as sip  # noqa: E402

CAPITAL, LEV = 5_000.0, 5.0
EXPO = CAPITAL * LEV
TARGET = 200.0
LOT = 65


def day_series(trades, days):
    s = pd.Series(0.0, index=days)
    for t in trades:
        s[t.day] += t.net
    return s


def summarize(name, daily):
    d = daily.values
    eq = CAPITAL + np.cumsum(d)
    ruin = bool((eq <= 0).any())
    return {"test": name, "days": len(d), "avg_per_day": round(d.mean(), 1), "total": round(d.sum()),
            "days_ge_200_pct": round((d >= TARGET).mean() * 100, 1), "worst_day": round(d.min()),
            "best_day": round(d.max()), "min_equity": round(eq.min()), "wiped_out": ruin}


def test_a_b(intra, daily):
    rows, per_stock = [], []
    all_days = sorted({str(x) for df in intra.values() for x in df.index.date})
    for strat, grid in intraday.GRIDS.items():
        for p in grid:
            tot = pd.Series(0.0, index=all_days)
            for tk, bars in intra.items():
                res = intraday.backtest(bars, strat, capital=EXPO, **p)
                s = day_series(res.trades, all_days)
                per_stock.append({"strategy": strat, "params": str(p), "stock": tk, "net": s.sum(),
                                  "first_half": s.iloc[: len(s) // 2].sum(), "second_half": s.iloc[len(s) // 2:].sum()})
                tot += s
            rows.append(summarize(f"A {strat} {p} avg of {len(intra)} stocks", tot / len(intra)))
    ps = pd.DataFrame(per_stock)
    best = ps.sort_values("net", ascending=False).iloc[0]
    # honesty check: pick the best stock on the FIRST half only, then see the second half
    pick = ps.sort_values("first_half", ascending=False).iloc[0]
    # B: stocks in play, 5x
    days = sorted({d for df in intra.values() for d in pd.Index(df.index.date).unique()})
    b = pd.Series(0.0, index=[str(d) for d in days[20:]])
    for d in days[20:]:
        # top 1 pick only, so the whole Rs 25,000 goes into one stock (as aggressive as allowed)
        trades, _ = sip.run_day(intra, daily, d, capital=EXPO, top_n=1)
        b[str(d)] = sum(t.ret_net * EXPO for t in trades)
    rows.append(summarize("B stocks-in-play top pick, 5x", b))
    return rows, best, pick, ps


def bs(S, K, T, sig, call):
    if T <= 0:
        return max(0.0, (S - K) if call else (K - S))
    d1 = (math.log(S / K) + 0.5 * sig * sig * T) / (sig * math.sqrt(T))
    d2 = d1 - sig * math.sqrt(T)
    N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))  # noqa: E731
    return S * N(d1) - K * N(d2) if call else K * N(-d2) - S * N(-d1)


def test_c(nifty, vix):
    """ORB on Nifty: break of the first 15-min range -> buy the nearest strike (50s) whose
    modelled premium x 65 fits in Rs 5,000. Exit: premium doubles, halves, or 15:15."""
    out = {}
    for d, day in nifty.groupby(nifty.index.date):
        day = day.between_time(time(9, 15), time(15, 25))
        if len(day) < 20:
            continue
        v = vix.asof(pd.Timestamp(d))
        if pd.isna(v):
            continue
        sig = float(v) / 100
        # weekly Nifty expiry is Tuesday since Sep 2025
        dte = (1 - pd.Timestamp(d).weekday()) % 7
        hi, lo = day.iloc[:3].high.max(), day.iloc[:3].low.min()
        pnl = 0.0
        for i in range(3, len(day) - 1):
            c = day.iloc[i].close
            side = 1 if c > hi else (-1 if c < lo else 0)
            if side == 0 or day.index[i + 1].time() > time(14, 45):
                continue
            call = side == 1
            S0 = day.iloc[i + 1].open
            mins_left = lambda ts: (dte * 375 + (15 * 60 + 30) - (ts.hour * 60 + ts.minute)) / (375 * 252)  # noqa: E731
            T0 = max(mins_left(day.index[i + 1]), 1e-6)
            base = round(S0 / 50) * 50
            K, prem = None, None
            for k in range(0, 40):
                Kc = base + 50 * k if call else base - 50 * k
                pr = bs(S0, Kc, T0, sig, call)
                if pr * LOT * 1.01 <= CAPITAL:
                    K, prem = Kc, pr * 1.01  # 1% slippage on entry (wide spreads on cheap options)
                    break
            if K is None or prem < 0.5:
                break
            exit_p = None
            for j in range(i + 1, len(day)):
                ts = day.index[j]
                T = max(mins_left(ts), 1e-6)
                best_S = day.iloc[j].high if call else day.iloc[j].low
                worst_S = day.iloc[j].low if call else day.iloc[j].high
                if bs(worst_S, K, T, sig, call) <= prem * 0.5:
                    exit_p = prem * 0.5; break
                if bs(best_S, K, T, sig, call) >= prem * 2:
                    exit_p = prem * 2; break
                if ts.time() >= time(15, 15):
                    exit_p = bs(day.iloc[j].close, K, T, sig, call); break
            exit_p = (exit_p if exit_p is not None else bs(day.iloc[-1].close, K, max(mins_left(day.index[-1]), 1e-6), sig, call)) * 0.99
            ch = costs.options(prem * LOT, exit_p * LOT).total
            pnl = (exit_p - prem) * LOT - ch
            break  # one trade a day
        out[str(d)] = pnl
    return summarize("C Nifty option buying (modelled), Rs 5,000", pd.Series(out))


def main():
    import yfinance as yf
    print("fetching 51 stocks (5-min, 60 days)...", flush=True)
    intra, daily = sip.fetch("60d")
    rows, best, pick, ps = test_a_b(intra, daily)
    n = yf.download("^NSEI", period="60d", interval="5m", progress=False, auto_adjust=False)
    n.columns = [c[0] if isinstance(c, tuple) else c for c in n.columns]
    n = n.rename(columns=str.lower)
    n.index = n.index.tz_convert("Asia/Kolkata").tz_localize(None) if n.index.tz is not None else n.index
    vx = yf.download("^INDIAVIX", period="6mo", interval="1d", progress=False, auto_adjust=False)["Close"].squeeze()
    vx.index = pd.to_datetime(vx.index).tz_localize(None)
    rows.append(test_c(n, vx))
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))
    print("\nBest single stock+strategy over all 60 days (cherry-picked, in hindsight):")
    print(best.to_string())
    print("\nHonest version: best stock picked on the FIRST half, then traded the SECOND half:")
    print(pick.to_string())
    print(f"\nshare of stock+strategy combos that made money after charges: {(ps.net > 0).mean() * 100:.1f}%")
    out = Path(__file__).with_name("aggressive_5k_results.csv")
    df.to_csv(out, index=False)
    ps.to_csv(out.with_name("aggressive_5k_per_stock.csv"), index=False)


if __name__ == "__main__":
    main()

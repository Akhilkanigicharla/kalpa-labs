"""All markets, all common strategies, any leverage: can Rs 5,000 average Rs 200/day? (13 Nov 2026)

Markets (hourly bars, ~2 years, Yahoo): BTC, ETH, SOL (crypto perps, Delta Exchange India style),
Gold (MCX-style futures), USD/INR (NSE currency futures), Nifty 50, Nasdaq-100 (QQQ), EUR/USD (info only:
offshore leveraged forex is not allowed for Indian residents under FEMA).

Strategies (long AND short, signal on bar close, fill next bar open):
  ema    EMA fast/slow crossover trend       donch  Donchian breakout (n), exit at n/2 channel
  rsi    RSI(14) reversal to 50              boll   Bollinger(20, k) fade to the mean
  mom    time-series momentum (lookback L)   hold   buy and hold (baseline)
Walk-forward: every strategy/setting is ranked on the FIRST year only (Sharpe); the single best one per
market is then traded on the SECOND year, untouched. Leverage 1x..100x is applied to that out-of-sample
year with costs scaled by leverage; equity at or below 0 = account wiped (exchanges liquidate earlier, so
this is generous). Bootstrap: 2,000 one-year paths resampled from out-of-sample days.
Run from 07-trading/:  python -I research/all_markets_5k_test.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

CAPITAL, TARGET = 5_000.0, 200.0
# cost per side as a fraction of position value (fee incl. 18% GST + slippage)
MARKETS = {
    "BTC-USD": ("crypto perp", 0.0005 * 1.18 + 0.0002, 0.0001 / 8),   # taker 0.05% + GST; funding ~0.01%/8h
    "ETH-USD": ("crypto perp", 0.0005 * 1.18 + 0.0002, 0.0001 / 8),
    "SOL-USD": ("crypto perp", 0.0005 * 1.18 + 0.0003, 0.0001 / 8),
    "GC=F": ("gold futures", 0.0002, 0.0),
    "INR=X": ("USD/INR futures", 0.0001, 0.0),
    "^NSEI": ("Nifty futures", 0.0002, 0.0),
    "QQQ": ("Nasdaq-100", 0.0002, 0.0),
    "EURUSD=X": ("EUR/USD (not legal offshore)", 0.0001, 0.0),
}
LEVERAGE = [1, 2, 3, 5, 10, 20, 50, 100]


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(c, n=14):
    d = c.diff()
    up, dn = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(), (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def positions(df, strat, p):
    c, h, l = df.close, df.high, df.low
    if strat == "hold":
        return pd.Series(1.0, index=c.index)
    if strat == "ema":
        return np.sign(ema(c, p["f"]) - ema(c, p["s"])).fillna(0)
    if strat == "mom":
        return np.sign(c / c.shift(p["L"]) - 1).fillna(0)
    pos = np.zeros(len(c))
    if strat == "donch":
        hi, lo = h.rolling(p["n"]).max().shift(1), l.rolling(p["n"]).min().shift(1)
        xh, xl = h.rolling(p["n"] // 2).max().shift(1), l.rolling(p["n"] // 2).min().shift(1)
        cur = 0
        for i in range(len(c)):
            ci = c.iat[i]
            if cur == 0:
                cur = 1 if ci > hi.iat[i] else (-1 if ci < lo.iat[i] else 0)
            elif cur == 1 and ci < xl.iat[i]:
                cur = 0
            elif cur == -1 and ci > xh.iat[i]:
                cur = 0
            pos[i] = cur
    elif strat == "rsi":
        r = rsi(c).values
        cur = 0
        for i in range(len(c)):
            if cur == 0:
                cur = 1 if r[i] < p["lo"] else (-1 if r[i] > 100 - p["lo"] else 0)
            elif (cur == 1 and r[i] >= 50) or (cur == -1 and r[i] <= 50):
                cur = 0
            pos[i] = cur
    elif strat == "boll":
        m, sd = c.rolling(20).mean(), c.rolling(20).std()
        cur = 0
        for i in range(len(c)):
            if np.isnan(sd.iat[i]):
                continue
            z = (c.iat[i] - m.iat[i]) / sd.iat[i]
            if cur == 0:
                cur = 1 if z < -p["k"] else (-1 if z > p["k"] else 0)
            elif (cur == 1 and z >= 0) or (cur == -1 and z <= 0):
                cur = 0
            pos[i] = cur
    return pd.Series(pos, index=c.index)


GRID = ([("hold", {})]
        + [("ema", {"f": f, "s": s}) for f, s in [(5, 20), (10, 50), (20, 100), (50, 200)]]
        + [("donch", {"n": n}) for n in (20, 55, 100, 200)]
        + [("rsi", {"lo": lo}) for lo in (20, 25, 30)]
        + [("boll", {"k": k}) for k in (2.0, 2.5, 3.0)]
        + [("mom", {"L": L}) for L in (6, 24, 72, 168)])


def hourly_returns(df, strat, p, cost, fund):
    pos = positions(df, strat, p).shift(1).fillna(0)          # trade on next bar
    r = df.close.pct_change().fillna(0)
    turn = pos.diff().abs().fillna(pos.abs())
    return pos * r - turn * cost - pos.abs() * fund


def sharpe(x):
    return x.mean() / x.std() * np.sqrt(len(x)) if x.std() > 0 else -9


def lever_path(hr, L):
    """Compound hourly returns at leverage L; wiped when equity <= 0."""
    eq, out = CAPITAL, []
    for v in hr.values:
        eq = eq * (1 + L * v) if eq > 0 else 0.0
        eq = max(eq, 0.0)
        out.append(eq)
    return pd.Series(out, index=hr.index)


def main():
    import yfinance as yf
    rows, boot = [], []
    rng = np.random.default_rng(7)
    for tk, (kind, cost, fund) in MARKETS.items():
        d = yf.download(tk, period="730d", interval="1h", progress=False, auto_adjust=False)
        d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
        d = d.rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
        mid = d.index[0] + (d.index[-1] - d.index[0]) / 2
        tr, te = d[d.index < mid], d[d.index >= mid]
        scores = [(sharpe(hourly_returns(tr, s, p, cost, fund)), s, p) for s, p in GRID]
        sc, s, p = max(scores, key=lambda x: x[0])
        hr = hourly_returns(d, s, p, cost, fund).loc[te.index]   # computed on full history, scored on test only
        days = (te.index[-1] - te.index[0]).days
        for L in LEVERAGE:
            eq = lever_path(hr, L)
            daily = eq.resample("1D").last().ffill().diff().dropna()
            rows.append({"market": tk, "type": kind, "picked_on_year1": f"{s} {p}", "lev": L,
                         "end_equity": round(eq.iloc[-1]), "avg_rs_per_day": round((eq.iloc[-1] - CAPITAL) / days, 1),
                         "days_ge_200_pct": round((daily >= TARGET).mean() * 100, 1),
                         "worst_day": round(daily.min()), "wiped": bool((eq <= 0).any())})
        # bootstrap 1-year paths from out-of-sample daily unlevered returns
        dr = (1 + hr).resample("1D").prod().dropna() - 1
        dr = dr[dr != 0] if (dr != 0).sum() > 30 else dr
        for L in LEVERAGE:
            ok = wiped = 0
            for _ in range(2000):
                path = rng.choice(dr.values, size=365)
                eq = CAPITAL
                for v in path:
                    eq = max(eq * (1 + L * v), 0.0)
                    if eq == 0:
                        break
                wiped += eq == 0
                ok += (eq - CAPITAL) / 365 >= TARGET
            boot.append({"market": tk, "lev": L, "p_hit_200_per_day_pct": round(ok / 20, 1),
                         "p_wiped_pct": round(wiped / 20, 1)})
        print("done", tk, s, p, flush=True)
    res, bt = pd.DataFrame(rows), pd.DataFrame(boot)
    out = Path(__file__).with_name("all_markets_5k_results.csv")
    res.merge(bt, on=["market", "lev"]).to_csv(out, index=False)
    pd.set_option("display.width", 250)
    print(res.merge(bt, on=["market", "lev"]).to_string(index=False))


if __name__ == "__main__":
    main()

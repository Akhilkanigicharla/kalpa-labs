"""A330b: the same pre-registered trend-following recipe (research/gold_trend_25y.py) on a DIVERSIFIED basket,
which is what the long-run evidence (Hurst, Ooi & Pedersen 2017: 67 markets; Moskowitz, Ooi & Pedersen 2012)
is actually about.  No setting is tuned here; the only choices are the baskets, fixed before running:

  the5ers  markets The5%ers High Stakes lists (FX, metals, indices, oil): gold, silver, WTI oil, S&P 500,
           Nasdaq 100, Dow, DAX, EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, USD/CHF  (Yahoo futures/FX)
  india    what a resident can trade live on Indian exchanges through a SEBI-registered broker:
           NSE Nifty 50, NSE Bank Nifty, MCX gold, silver, crude oil, copper (global price x USD/INR),
           NSE USD/INR currency futures (USDINR=X)

Each market: signal = mean sign of 1/3/6/12-month return, sized to 10% vol on its own; the basket is the
equal-weight average, re-scaled to a 10% portfolio vol target (EWMA, max 4x), 5 bp costs (7.5 bp for India).
Checks: per market, by decade, every year, placebo (random directions, same sizes), deflated Sharpe,
double costs, The5%ers High Stakes simulation (from research/gold_trend_25y.the5ers).
Research code only.  Not investment advice.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gold_trend_25y as gt  # noqa: E402

BASKETS = {
    "the5ers": {"gold": "GC=F", "silver": "SI=F", "oil": "CL=F", "sp500": "ES=F", "nasdaq": "NQ=F", "dow": "YM=F",
                "dax": "^GDAXI", "eurusd": "EURUSD=X", "gbpusd": "GBPUSD=X", "usdjpy": "JPY=X", "audusd": "AUDUSD=X",
                "usdcad": "CAD=X", "usdchf": "CHF=X"},
    "india": {"nifty": "^NSEI", "banknifty": "^NSEBANK", "gold_inr": "GC=F", "silver_inr": "SI=F",
              "crude_inr": "CL=F", "copper_inr": "HG=F", "usdinr": "USDINR=X"},
}
INR_CONVERT = {"gold_inr", "silver_inr", "crude_inr", "copper_inr"}
PORT_MAX_LEV = 4.0


def fetch(tickers: list[str]) -> pd.DataFrame:
    cache = Path("/tmp/trend_basket_prices.parquet")
    have = pd.read_parquet(cache) if cache.exists() else pd.DataFrame()
    need = [t for t in tickers if t not in have.columns]
    if need:
        import yfinance as yf
        cols = {}
        for t in need:
            x = yf.download(t, period="max", interval="1d", progress=False, auto_adjust=False)
            x.columns = [c[0] if isinstance(c, tuple) else c for c in x.columns]
            s = x["Close"]
            s.index = pd.to_datetime(s.index).tz_localize(None)
            cols[t] = s
        have = pd.concat([have, pd.DataFrame(cols)], axis=1)
        have.to_parquet(cache)
    return have


def market_returns(basket: str) -> pd.DataFrame:
    spec = BASKETS[basket]
    px = fetch(sorted(set(spec.values()) | {"USDINR=X"}))
    out = {}
    fx = px["USDINR=X"].ffill().pct_change()
    for name, t in spec.items():
        s = px[t].dropna()
        s = s[s > 0]
        r = s.pct_change()
        if name in INR_CONVERT:
            r = (1 + r) * (1 + fx.reindex(r.index).fillna(0.0)) - 1
            r = r[r.index >= px["USDINR=X"].dropna().index[0] + pd.Timedelta("30D")]
        r = r[(r.abs() < 0.25)].dropna()                          # drop roll / data glitches
        out[name] = r
    return pd.DataFrame(out)


def run(basket: str, cost: float) -> tuple[pd.Series, dict]:
    R = market_returns(basket)
    per = {}
    for m in R.columns:
        r = R[m].dropna()
        px = (1 + r).cumprod()
        pos = gt.positions(r, gt.signal(px))
        per[m] = gt.pnl(r, pos, cost)
    P = pd.DataFrame(per)
    active = P.notna().sum(axis=1)
    eq = P.mean(axis=1, skipna=True)[active >= 3]                  # need at least 3 live markets
    vol = eq.ewm(com=60, min_periods=60).std() * math.sqrt(252)
    lev = (gt.TARGET_VOL / vol).shift(1).clip(upper=PORT_MAX_LEV)
    port = (eq * lev).dropna()
    return port, {m: gt.stats(P[m].dropna()) for m in P.columns}


def placebo(basket: str, cost: float, runs=200, seed=11) -> tuple[float, float]:
    """Random directions per market (same sizes and rebalance timing): share of runs beating the real sum."""
    R = market_returns(basket)
    rng = np.random.default_rng(seed)
    real_port, _ = run(basket, cost)
    real = real_port.sum()
    cached = {}
    for m in R.columns:
        r = R[m].dropna()
        pos = gt.positions(r, gt.signal((1 + r).cumprod()))
        cached[m] = (r, pos, (pos.diff().fillna(0) != 0).cumsum())
    beats, sums = 0, []
    for _ in range(runs):
        per = {}
        for m, (r, pos, blk) in cached.items():
            flips = rng.choice([-1.0, 1.0], int(blk.max()) + 1)
            per[m] = gt.pnl(r, pd.Series(pos.abs().values * flips[blk.values], index=pos.index), cost)
        P = pd.DataFrame(per)
        eq = P.mean(axis=1, skipna=True)[P.notna().sum(axis=1) >= 3]
        vol = eq.ewm(com=60, min_periods=60).std() * math.sqrt(252)
        s = (eq * (gt.TARGET_VOL / vol).shift(1).clip(upper=PORT_MAX_LEV)).dropna().sum()
        sums.append(s)
        beats += s >= real
    return beats / runs, float(np.mean(sums))


def main() -> int:
    rep = dict(generated=str(date.today()), recipe="1/3/6/12-month mean-sign trend, 10% vol per market and portfolio")
    for basket, cost in (("the5ers", gt.COST), ("india", gt.COST * 1.5)):
        port, per = run(basket, cost)
        dbl, _ = run(basket, cost * 2)
        variants = [port, dbl]
        share, rnd = placebo(basket, cost)
        rep[basket] = dict(
            data=f"{port.index[0].date()} to {port.index[-1].date()}",
            portfolio=gt.stats(port),
            double_costs=gt.stats(dbl),
            by_decade={f"{y}s": gt.stats(port[(port.index.year >= y) & (port.index.year < y + 10)]) for y in (2000, 2010, 2020)},
            last_2_years=gt.stats(port[port.index >= port.index[-1] - pd.Timedelta("730D")]),
            every_year_pct={int(y): round(float((1 + x).prod() - 1) * 100, 1) for y, x in port.groupby(port.index.year)},
            per_market_sharpe={m: v.get("sharpe") for m, v in per.items()},
            placebo_share_beating_real=round(share, 3),
            deflated_sharpe_prob=round(gt.deflated_sharpe(port, 12, 0.01), 3),
            the5ers_high_stakes_new=gt.the5ers(port) if basket == "the5ers" else None,
        )
        port.to_frame("pnl").to_csv(Path(__file__).resolve().parents[1] / "reports" / f"trend-{basket}-{date.today()}.csv")
    out = Path(__file__).resolve().parents[1] / "reports" / f"trend-portfolio-25y-{date.today()}.json"
    out.write_text(json.dumps(rep, indent=1, default=str))
    for b in ("the5ers", "india"):
        v = rep[b]
        print(b, v["data"])
        for k in ("portfolio", "double_costs", "last_2_years", "placebo_share_beating_real", "deflated_sharpe_prob", "per_market_sharpe", "the5ers_high_stakes_new"):
            print(" ", k, v[k])
        print("  decades", {k: (d.get("sharpe"), d.get("cagr_pct")) for k, d in v["by_decade"].items()})
        print("  years", v["every_year_pct"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

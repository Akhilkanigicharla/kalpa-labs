"""A330c: is the MSNR edge from the 2-year intraday test real over the long run?

The A323 mix's main earners were MSNR fresh_v and QM setups.  Free intraday data stops at 2 years, but the same
setups can run on DAILY bars for 25+ years and on other markets.  Same code as the mix (src/msnr.SETUPS,
msnr_gold_robust.filt 9-EMA filter, src/smc.simulate: limit at the level, stop rule of the setup, 2R target,
wait 10 bars, hold 20 bars), cost 0.03% of price per trade (2x that as a stress test).
For every market and side: trades, win rate, avg R, and the same count of random entries (src.smc.placebo, 15
seeds) -> share of random runs that beat the real avg R.  Earlier half vs later half shown separately.
Markets: gold, silver, oil, copper, S&P 500, Nasdaq, DAX, Nifty, EUR/USD, USD/JPY (Yahoo daily).
Research code only.  Not investment advice.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import msnr_gold_robust as mr  # noqa: E402
import trend_portfolio_25y as tp  # noqa: E402
from src.msnr import SETUPS, mirror  # noqa: E402
from src.smc import placebo as zone_placebo, simulate  # noqa: E402

MARKETS = {"gold": "GC=F", "silver": "SI=F", "oil": "CL=F", "copper": "HG=F", "sp500": "ES=F", "nasdaq": "NQ=F",
           "dax": "^GDAXI", "nifty": "^NSEI", "eurusd": "EURUSD=X", "usdjpy": "JPY=X"}
COST = 0.0003


def daily_ohlc(ticker: str) -> pd.DataFrame:
    cache = Path(f"/tmp/ohlc_{ticker.replace('^', '').replace('=', '_')}.parquet")
    if cache.exists():
        return pd.read_parquet(cache)
    import yfinance as yf
    x = yf.download(ticker, period="max", interval="1d", progress=False, auto_adjust=False)
    x.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in x.columns]
    x = x[["open", "high", "low", "close"]].dropna()
    x = x[(x > 0).all(axis=1)]
    x.index = pd.to_datetime(x.index).tz_localize(None)
    # drop bars with impossible ranges (bad prints): high < max(open, close) etc.
    x = x[(x.high >= x[["open", "close"]].max(axis=1)) & (x.low <= x[["open", "close"]].min(axis=1))]
    x.to_parquet(cache)
    return x


def trades(real: pd.DataFrame, setup: str, side: str, cost=COST, seed=None) -> pd.DataFrame:
    df = mirror(real) if side == "short" else real
    zs = mr.filt(SETUPS[setup](df, k=2, storyline_on=False), real, df, True, side)
    if seed is not None:
        zs = zone_placebo(df, zs, seed=seed)
    t = simulate(df, zs, wait=10, hold=20, rr=2.0, cost=cost)
    if t.empty:
        return t
    t["date"] = df.index[t.entry_bar.values]
    return t


def summary(t: pd.DataFrame) -> dict:
    if t.empty:
        return dict(n=0)
    r = t.r.values
    return dict(n=int(len(r)), win=round(float((r > 0).mean()), 3), avg_r=round(float(r.mean()), 3), total_r=round(float(r.sum()), 1))


def one_market(name: str) -> tuple[str, dict, list]:
    real = daily_ohlc(MARKETS[name])
    mid = real.index[len(real) // 2]
    res, edges = {"data": f"{real.index[0].date()} to {real.index[-1].date()}"}, []
    for setup in ("fresh_v", "qm"):
        for side in ("long", "short"):
            t = trades(real, setup, side)
            if t.empty:
                res[f"{setup} {side}"] = dict(n=0)
                continue
            rnd = [trades(real, setup, side, seed=s) for s in range(15)]
            ravg = [x.r.mean() for x in rnd if len(x)]
            row = summary(t) | dict(
                earlier=summary(t[t.date < mid]), later=summary(t[t.date >= mid]),
                double_cost=summary(trades(real, setup, side, COST * 2)),
                random_avg_r=round(float(np.mean(ravg)), 3),
                p_random_beats=round(float((np.array(ravg) >= t.r.mean()).mean()), 2))
            res[f"{setup} {side}"] = row
            edges.append(float(t.r.mean() - np.mean(ravg)))
    return name, res, edges


def main() -> int:
    from concurrent.futures import ProcessPoolExecutor
    for tk in MARKETS.values():                      # download once, serially
        daily_ohlc(tk)
    rep = dict(generated=str(date.today()), rule="daily bars, k=2, 9-EMA filter, 2R, wait 10, hold 20, 0.03% cost", markets={})
    edges = []
    with ProcessPoolExecutor() as ex:
        for name, res, e in ex.map(one_market, MARKETS):
            rep["markets"][name] = res
            edges += e
            for k, row in res.items():
                if k != "data" and row.get("n"):
                    print(name, k, {x: row[x] for x in ("n", "win", "avg_r", "random_avg_r", "p_random_beats")},
                          "earlier", row["earlier"].get("avg_r"), "later", row["later"].get("avg_r"),
                          "2xcost", row["double_cost"].get("avg_r"), flush=True)
    edge = np.array(edges)
    rep["all_markets_edge_over_random_r"] = dict(mean=round(float(edge.mean()), 3), positive=f"{int((edge > 0).sum())} of {len(edge)}")
    out = Path(__file__).resolve().parents[1] / "reports" / f"msnr-daily-25y-{date.today()}.json"
    out.write_text(json.dumps(rep, indent=1, default=str))
    print(rep["all_markets_edge_over_random_r"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

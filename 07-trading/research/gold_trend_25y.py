"""A330: gold trend following (time-series momentum, TSMOM) over 25+ years, judged with hedge-fund checks.

Akhil (21 Nov 2026): "go through internet and use quant technique ... goal is profitable funded account algo
bot which I can run in the live real market in India ... show me results".

Why this method: it is the one with the longest public evidence.  Hurst, Ooi & Pedersen (AQR, JPM 2017,
"A Century of Evidence on Trend-Following Investing") and Moskowitz, Ooi & Pedersen (JFE 2012, "Time Series
Momentum") find it profitable across decades and markets, gold included.  Everything below is their standard
recipe, fixed BEFORE looking at gold results (no tuning to this data):
  signal   = average of sign(past return) over 1, 3, 6 and 12 months (21/63/126/252 trading days)
  sizing   = volatility targeting: position = signal x (target vol / EWMA vol, 60-day centre of mass)
  target   = 10% a year (chosen for prop-firm loss limits: daily sd ~0.63%), max 3x, rebalance only when the
             position moves > 10% (cuts costs)
  costs    = 5 bp per unit of position traded (futures spread + slippage, conservative)
  trading  = decide on day t's close, hold from day t+1 (no look-ahead)
Checks: every lookback on its own (a real effect should not live in one setting), by decade, every year,
long+short vs long-only, random-signal placebo with the same turnover (500 runs), Deflated Sharpe Ratio
(Bailey & Lopez de Prado 2014) for the number of variants shown, worst drawdown, The5%ers High Stakes
simulation on the daily P&L, and the same strategy in rupees for MCX gold (gold USD return + USD/INR return).
Data: Yahoo GC=F (COMEX gold futures, continuous front month) daily, and USDINR=X.
Research code only.  Not investment advice.
"""
from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

LOOKBACKS = (21, 63, 126, 252)
TARGET_VOL = 0.10
MAX_LEV = 3.0
BUFFER = 0.10
COST = 0.0005
CACHE = Path("/tmp/gc_daily_max.parquet")


def load() -> tuple[pd.Series, pd.Series]:
    if CACHE.exists():
        d = pd.read_parquet(CACHE)
    else:
        import yfinance as yf
        g = yf.download("GC=F", period="max", interval="1d", progress=False, auto_adjust=False)
        r = yf.download("USDINR=X", period="max", interval="1d", progress=False, auto_adjust=False)
        g.columns = [c[0] if isinstance(c, tuple) else c for c in g.columns]
        r.columns = [c[0] if isinstance(c, tuple) else c for c in r.columns]
        d = pd.DataFrame({"gold": g["Close"], "usdinr": r["Close"]})
        d.index = pd.to_datetime(d.index).tz_localize(None)
        d.to_parquet(CACHE)
    gold = d.gold.dropna()
    gold = gold[gold > 0]
    return gold, d.usdinr.ffill()


def signal(px: pd.Series, lookbacks=LOOKBACKS) -> pd.Series:
    s = sum(np.sign(px / px.shift(lb) - 1.0) for lb in lookbacks) / len(lookbacks)
    return s.fillna(0.0)


def positions(ret: pd.Series, sig: pd.Series, target=TARGET_VOL, long_only=False) -> pd.Series:
    vol = ret.ewm(com=60, min_periods=60).std() * math.sqrt(252)
    raw = (sig.clip(lower=0) if long_only else sig) * (target / vol)
    raw = raw.clip(-MAX_LEV, MAX_LEV).fillna(0.0)
    pos, cur = np.zeros(len(raw)), 0.0
    for i, x in enumerate(raw.values):
        if abs(x - cur) > BUFFER * max(abs(cur), 0.25):
            cur = x
        pos[i] = cur
    return pd.Series(pos, index=raw.index)


def pnl(ret: pd.Series, pos: pd.Series, cost=COST) -> pd.Series:
    held = pos.shift(1).fillna(0.0)                      # decided at t's close, held over t+1
    turnover = pos.diff().abs().fillna(0.0).shift(1).fillna(0.0)
    return held * ret - turnover * cost


def stats(p: pd.Series) -> dict:
    p = p.dropna()
    if len(p) < 30 or p.std() == 0:
        return {}
    ann = p.mean() * 252
    vol = p.std() * math.sqrt(252)
    eq = (1 + p).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    yrs = p.groupby(p.index.year).apply(lambda x: (1 + x).prod() - 1)
    return dict(years=round(len(p) / 252, 1), cagr_pct=round(((eq.iloc[-1]) ** (252 / len(p)) - 1) * 100, 2),
                ann_vol_pct=round(vol * 100, 1), sharpe=round(ann / vol, 2), max_drawdown_pct=round(dd * 100, 1),
                positive_years=f"{int((yrs > 0).sum())} of {len(yrs)}", worst_year_pct=round(yrs.min() * 100, 1),
                best_year_pct=round(yrs.max() * 100, 1), worst_day_pct=round(p.min() * 100, 2))


def deflated_sharpe(p: pd.Series, n_trials: int, sr_trials_sd: float) -> float:
    """Probability the true Sharpe > 0 after correcting for n_trials variants (Bailey & Lopez de Prado 2014)."""
    from scipy.stats import norm
    p = p.dropna()
    sr = p.mean() / p.std()                                     # per-day Sharpe
    T = len(p)
    skew, kurt = p.skew(), p.kurt() + 3
    emc = 0.5772156649
    sr0 = sr_trials_sd * ((1 - emc) * norm.ppf(1 - 1 / n_trials) + emc * norm.ppf(1 - 1 / (n_trials * math.e)))
    z = (sr - sr0) * math.sqrt(T - 1) / math.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2)
    return float(norm.cdf(z))


def placebo(ret: pd.Series, pos: pd.Series, runs=500, seed=7) -> float:
    """Share of random-direction strategies (same position sizes and timing of changes) that beat the real one."""
    rng = np.random.default_rng(seed)
    real = pnl(ret, pos).sum()
    change = (pos.diff().fillna(0) != 0).cumsum()               # blocks between real rebalances
    mag = pos.abs()
    beat = 0
    for _ in range(runs):
        flips = pd.Series(rng.choice([-1.0, 1.0], change.max() + 1), index=range(change.max() + 1))
        fake = mag * flips.reindex(change.values).values
        beat += pnl(ret, pd.Series(fake, index=pos.index)).sum() >= real
    return beat / runs


def the5ers(p: pd.Series, step1=0.10, step2=0.05) -> dict:
    """$10K High Stakes attempts started every month: daily 5% / max 10% / 3 profitable days >= 0.5%;
    funded: 80% of profit paid every 14 days, balance back to $10K."""
    p = p.dropna()
    starts = pd.date_range(p.index[0] + pd.Timedelta("400D"), p.index[-1] - pd.Timedelta("365D"), freq="MS")
    out = []
    for s in starts:
        u = p[p.index >= s]
        bal, stage, prof, paid, t_fund, nxt = 1.0, 1, 0, 0.0, None, None
        res = "running"
        for d, x in u.items():
            if stage <= 2:
                if x <= -0.05:
                    res = f"failed step {stage}"; break
                bal += x
                prof += x >= 0.005
                if bal <= 0.90:
                    res = f"failed step {stage}"; break
                if bal >= 1 + (step1 if stage == 1 else step2) and prof >= 3:
                    if stage == 1:
                        stage, bal, prof = 2, 1.0, 0
                    else:
                        stage, bal, t_fund, nxt = 3, 1.0, d, d + pd.Timedelta("14D")
            else:
                if d >= nxt:
                    if bal > 1:
                        paid += 0.8 * (bal - 1) * 10_000
                        bal = 1.0
                    nxt += pd.Timedelta("14D")
                bal += x
                if x <= -0.05 or bal <= 0.90:
                    res = "funded then lost"; break
                if (d - t_fund).days >= 365:
                    res = "funded 1 year+"; break
        out.append(dict(res=res if stage <= 2 or res != "running" else "funded, data ended",
                        days=(t_fund - s).days if t_fund is not None else None, paid=paid))
    df = pd.DataFrame(out)
    return dict(attempts=len(df), outcomes=df.res.value_counts(normalize=True).round(2).to_dict(),
                reached_funded=round(float(df.days.notna().mean()), 2),
                median_days_to_funded=float(df.days.median()) if df.days.notna().any() else None,
                avg_payout_first_year_funded_usd=round(float(df[df.days.notna()].paid.mean()), 0) if df.days.notna().any() else 0)


def main() -> int:
    gold, usdinr = load()
    ret = gold.pct_change().dropna()
    ret = ret[ret.abs() < 0.2]                                  # drop data glitches (roll gaps > 20%)
    px = (1 + ret).cumprod()
    sig = signal(px)
    pos = positions(ret, sig)
    p = pnl(ret, pos)
    rep = dict(generated=str(date.today()), data=f"GC=F daily {ret.index[0].date()} to {ret.index[-1].date()}",
               recipe=dict(lookbacks=LOOKBACKS, target_vol=TARGET_VOL, max_leverage=MAX_LEV, cost_bp=COST * 1e4))
    rep["trend_long_short"] = stats(p)
    rep["trend_long_only"] = stats(pnl(ret, positions(ret, sig, long_only=True)))
    bh = ret * (TARGET_VOL / (ret.ewm(com=60, min_periods=60).std() * math.sqrt(252))).shift(1).clip(upper=MAX_LEV)
    rep["buy_and_hold_same_vol"] = stats(bh.dropna())
    rep["each_lookback_alone"] = {f"{lb}d": stats(pnl(ret, positions(ret, signal(px, (lb,))))) for lb in LOOKBACKS}
    rep["by_decade"] = {f"{y}s": stats(p[(p.index.year >= y) & (p.index.year < y + 10)]) for y in (2000, 2010, 2020)}
    rep["every_year_pct"] = {int(y): round(float((1 + x).prod() - 1) * 100, 1) for y, x in p.groupby(p.index.year)}
    rep["last_2_years"] = stats(p[p.index >= p.index[-1] - pd.Timedelta("730D")])
    variants = [p] + [pnl(ret, positions(ret, signal(px, (lb,)))) for lb in LOOKBACKS] + \
               [pnl(ret, positions(ret, sig, long_only=True))]
    srs = [v.mean() / v.std() for v in variants]
    rep["deflated_sharpe_prob"] = round(deflated_sharpe(p, len(variants), float(np.std(srs))), 3)
    rep["placebo_share_beating_real"] = round(placebo(ret, pos), 3)
    rep["double_costs"] = stats(pnl(ret, pos, COST * 2))
    rep["the5ers_high_stakes_new"] = the5ers(p)
    rep["the5ers_classic_8pct"] = the5ers(p, 0.08, 0.05)
    # India: MCX gold in rupees ~ gold USD x USD/INR (duties are a level, not a daily return)
    inr = usdinr.reindex(ret.index).ffill().pct_change().fillna(0.0)
    ret_inr = (1 + ret) * (1 + inr) - 1
    ret_inr = ret_inr[ret_inr.index >= usdinr.dropna().index[0] + pd.Timedelta("30D")]
    px_inr = (1 + ret_inr).cumprod()
    p_inr = pnl(ret_inr, positions(ret_inr, signal(px_inr)), COST * 1.5)   # MCX costs a bit higher
    rep["mcx_gold_in_rupees"] = stats(p_inr) | dict(note="gold USD return x USD/INR; 7.5 bp costs; MCX petal 1 g lots")
    out = Path(__file__).resolve().parents[1] / "reports" / f"gold-trend-25y-{date.today()}.json"
    out.write_text(json.dumps(rep, indent=1, default=str))
    p.to_frame("pnl").assign(position=pos.shift(1)).to_csv(out.with_suffix(".csv"))
    print(json.dumps({k: v for k, v in rep.items() if k != "every_year_pct"}, indent=1, default=str))
    print("years:", rep["every_year_pct"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

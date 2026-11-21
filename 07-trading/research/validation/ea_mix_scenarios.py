"""EA mix scenarios A-F (21 Nov 2026): the EA risk changes being made now, replayed on the same 2.4 years of GC=F
hourly data with research/ea_mix_backtest.portfolio (fixed $10K sizing, no compounding).  Research only.

Declared before running:
  A  current: all 13 strategies, 0.25% (EA 0.25% too), open-risk cap 2%, old closed-loss 4% day stop
  B  weights (KEEP 1 / HALF 0.5 / CUT 0), 0.25%, + EA rails
  C  weights, 0.40%, + rails            D  C + max 3 open positions + no opposite positions
  E  D + Friday cut to <= 1.25% open risk at Friday 22:00 (data time ~ server time; GC=F's last Friday bar
     closes 21:00 or 22:00 UTC, so the cut lands on the last Friday bar close)
  F  E + $0.30/oz per side extra cost
  A2 A + rails (to separate the rails from the weights)
  rails = min stop $1.50, lot cap 0.10, day stop 4% of max(balance, equity) at day start (equity-based, closes all),
          equity floor $9,100 (close all, stop for good).  Day = UTC date (data time ~ server time).
The5%ers High Stakes sim: weekly Monday starts; Step 1 +10%, Step 2 +5% (on closed balance), 3 profitable days
(closed P&L >= $50) per step; breach = equity <= 95% of max(balance, equity) at day start, or equity <= $9,000;
EA floor halt at equity <= $9,100 counted separately (not a breach, but the attempt is over).  Funded: every 14 days
80% of closed profit above $10K is paid and the balance resets to $10K.  Equity is checked at 1h bar closes only.
Monte Carlo (E, F): 5,000 paths x 252 trading days, stationary block bootstrap of daily (P&L, intraday low,
closed P&L), mean block 5 days.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import best_combo_gold as b  # noqa: E402
import ea_mix_backtest as em  # noqa: E402

START = 10_000.0
RAILS = dict(min_stop=1.5, lot_cap=0.10, day_stop_eq=0.04, eq_floor=9_100.0)
W = em.WEIGHTS_2026_11_21
SCEN = {
    "A current 13, 0.25%, cap 2%": dict(mix_risk=0.0025),
    "A2 A + rails": dict(mix_risk=0.0025, **RAILS),
    "B weights, 0.25%": dict(mix_risk=0.0025, weights=W, **RAILS),
    "C weights, 0.40%": dict(mix_risk=0.004, weights=W, **RAILS),
    "D C + max 3 pos + no opposite": dict(mix_risk=0.004, weights=W, max_pos=3, no_opposite=True, **RAILS),
    "E D + Friday cut 1.25%": dict(mix_risk=0.004, weights=W, max_pos=3, no_opposite=True, friday_cut=0.0125, **RAILS),
    "F E + $0.30/oz/side": dict(mix_risk=0.004, weights=W, max_pos=3, no_opposite=True, friday_cut=0.0125,
                               extra_cost=0.30, **RAILS),
    # added after seeing D: the position cap / no-opposite rule cost profit and raised drawdown, so test C + Friday cut
    "G C + Friday cut 1.25%": dict(mix_risk=0.004, weights=W, friday_cut=0.0125, **RAILS),
    "H G + $0.30/oz/side": dict(mix_risk=0.004, weights=W, friday_cut=0.0125, extra_cost=0.30, **RAILS),
    "I B + Friday cut + $0.30/oz/side": dict(mix_risk=0.0025, weights=W, friday_cut=0.0125, extra_cost=0.30, **RAILS),
}


def haircut_days(p, d, cut=0.5):
    """Lower every trade's R by cut x the scenario's avg R (out-of-sample decay ~45% + placebo share), charged on
    the close day (to P&L, closed P&L and the intraday low)."""
    h = cut * float(p.pnl.sum() / p.risk.sum()) * p.risk
    by = h.groupby(p.t_close.dt.normalize()).sum().reindex(d.index, fill_value=0.0)
    return d.assign(pnl=d.pnl - by.values, closed=d.closed - by.values, low=d.low - by.values)


def weekend(ck, fr):
    """Exposure carried over each weekend (after any Friday cut) and the P&L of the actual Monday gap."""
    h1 = fr["1h"]
    cuts = sorted(em._friday_cuts(h1, 22))
    ci = pd.Series(range(len(ck)), index=ck.c)
    rows = []
    for c in cuts:
        k = ci.get(c)
        if k is None or k + 1 >= len(ck):
            continue
        fri_close = float(h1.close.iloc[k])
        mon_open = float(h1.open.iloc[k + 1])
        lots = float(ck.net_lots.iloc[k])
        rows.append((c, lots, mon_open / fri_close - 1, lots * 100 * (mon_open - fri_close), fri_close))
    w = pd.DataFrame(rows, columns=["fri", "net_lots", "gap", "gap_pnl", "px"])
    i = int(w.net_lots.abs().idxmax())
    return dict(weekends=len(w), weekends_with_exposure=int((w.net_lots != 0).sum()),
                max_weekend_net_lots=round(float(w.net_lots.iloc[i]), 2), at=str(w.fri.iloc[i].date()),
                loss_if_9_5pct_gap_on_max_usd=round(abs(float(w.net_lots.iloc[i])) * 100 * float(w.px.iloc[i]) * 0.095, 0),
                worst_actual_gap_pct=round(float(w.gap.abs().max() * 100), 2),
                worst_actual_weekend_gap_pnl_usd=round(float(w.gap_pnl.min()), 0))


def run(allt, fr, kw):
    kw = dict(kw)
    mr = kw.pop("mix_risk")
    return em.portfolio(allt, fr, ea_risk=mr, mix_risk=mr, cap=0.02, curve=True, **kw)


def daily_table(ck):
    """Per trading day: equity change vs previous day's close, intraday low vs previous close, closed P&L."""
    ck = ck.assign(day=(ck.c - pd.Timedelta("1h")).dt.normalize())
    g = ck.groupby("day")
    end, low, bal = g["eq"].last(), g["eq"].min(), g["bal"].last()
    prev = end.shift(1).fillna(START)
    prevb = bal.shift(1).fillna(START)
    return pd.DataFrame(dict(pnl=end - prev, low=np.minimum(low - prev, 0.0), closed=bal - prevb, start=prev))


def stats(p, ck):
    eq = ck["eq"].values
    peak = np.maximum.accumulate(np.r_[START, eq])
    dd = float((peak[1:] - eq).max())
    d = daily_table(ck)
    rr = p.r_real.values
    return dict(trades=int(len(p)), wins=int((rr > 0.05).sum()), losses=int((rr < -0.05).sum()),
                win_pct=round(float((rr > 0.05).mean() * 100), 1), avg_r=round(float(p.pnl.sum() / p.risk.sum()), 3),
                net_usd=round(float(p.pnl.sum()), 0), worst_day_usd=round(float(d.pnl.min()), 0),
                worst_intraday_usd=round(float(d.low.min()), 0), max_dd_usd=round(dd, 0),
                max_dd_pct_of_10k=round(dd / START * 100, 2), lowest_equity_usd=round(float(eq.min()), 0),
                lowest_equity_vs_9000_floor_usd=round(float(eq.min() - 9_000), 0),
                exits={k: int(v) for k, v in p.exit.value_counts().items()},
                max_open_risk_pct=round(float(ck.open_risk.max() / START * 100), 2))


def attempts(p, mt, ck, step1=0.10, step2=0.05, daily=0.05, maxloss=0.10, floor=9_100.0):
    C = ck.c.values
    K = len(C)
    day = (ck.c - pd.Timedelta("1h")).dt.normalize().values
    tin = p.t_in.values
    kclose = np.minimum(np.searchsorted(C, p.t_close.values.astype(C.dtype), "left"), K - 1)
    closed_g = np.bincount(kclose, weights=p.pnl.values, minlength=K)
    mtm_g = np.bincount(mt.k.values, weights=mt.mtm.values, minlength=K)
    rec_tin = tin[mt.tid.map(dict(zip(p.tid, range(len(p))))).values]
    end = ck.c.iloc[-1]
    starts = pd.date_range(p.t_in.min().normalize(), end - pd.Timedelta("90D"), freq="W-MON")
    res = []
    for s in starts:
        s64 = np.datetime64(s)
        k0 = int(np.searchsorted(C, s64, "left"))
        cl, mm = closed_g[k0:].copy(), mtm_g[k0:].copy()
        x = (tin < s64) & (kclose >= k0)
        np.subtract.at(cl, kclose[x] - k0, p.pnl.values[x])
        y = (rec_tin < s64) & (mt.k.values >= k0)
        np.subtract.at(mm, mt.k.values[y] - k0, mt.mtm.values[y])
        stage, bal, eq_prev, cur, ref, dclosed, pdays = 1, START, START, None, START, 0.0, 0
        out = dict(start=s, outcome=None, step1_days=None, funded_days=None, paid=0.0, first_pay_days=None)
        next_pay = None
        for i in range(K - k0):
            k = k0 + i
            if day[k] != cur:
                if cur is not None and dclosed >= 0.005 * START:
                    pdays += 1
                cur, ref, dclosed = day[k], max(bal, eq_prev), 0.0
            bal += cl[i]
            dclosed += cl[i]
            eq = bal + mm[i]
            eq_prev = eq
            tnow = pd.Timestamp(C[k])
            if stage == 3 and tnow >= next_pay:
                if bal > START:
                    amt = 0.8 * (bal - START)
                    out["paid"] += amt
                    if out["first_pay_days"] is None:
                        out["first_pay_days"] = (tnow - s).days
                    eq -= bal - START
                    ref -= bal - START                       # the withdrawal is not a loss
                    bal = START
                    eq_prev = eq
                next_pay += pd.Timedelta("14D")
            lab = "funded then " if stage == 3 else f"step {stage} "
            if eq <= ref * (1 - daily) or eq <= START * (1 - maxloss):
                out["outcome"] = lab + "breached"
                break
            if floor is not None and eq <= floor:
                out["outcome"] = lab + "halted by EA floor"
                break
            if stage <= 2:
                n = pdays + (dclosed >= 0.005 * START)
                if bal >= START * (1 + (step1 if stage == 1 else step2)) and n >= 3:
                    if stage == 1:
                        out["step1_days"] = (tnow - s).days
                    else:
                        out["funded_days"] = (tnow - s).days
                        next_pay = tnow + pd.Timedelta("14D")
                    eq -= bal - START
                    stage, bal, pdays, dclosed, eq_prev, ref = stage + 1, START, 0, 0.0, eq, START
        if out["outcome"] is None:
            out["outcome"] = "funded, still running" if stage == 3 else f"still in step {stage}"
        out["runway_days"] = (end - s).days
        res.append(out)
    return res


def summarize_attempts(res):
    n = len(res)
    o = pd.Series([r["outcome"] for r in res]).value_counts().to_dict()
    pas = {}
    for h in (30, 60, 90, 180):
        elig = [r for r in res if r["runway_days"] >= h]
        pas[f"{h}d"] = round(100 * float(np.mean([r["step1_days"] is not None and r["step1_days"] <= h for r in elig])), 1)
        pas[f"{h}d_n"] = len(elig)
    fp = [r["first_pay_days"] for r in res if r["first_pay_days"] is not None]
    return dict(attempts=n, outcomes=o, step1_pass_pct=pas,
                funded_pct=round(100 * float(np.mean([r["funded_days"] is not None for r in res])), 1),
                breached_pct=round(100 * float(np.mean(["breached" in r["outcome"] for r in res])), 1),
                floor_halt_pct=round(100 * float(np.mean(["floor" in r["outcome"] for r in res])), 1),
                avg_payout_per_attempt_usd=round(float(np.mean([r["paid"] for r in res])), 0),
                median_months_to_first_payout=round(float(np.median(fp)) / 30.4, 1) if fp else None,
                with_payout_pct=round(100 * len(fp) / n, 1),
                failed_pct=round(100 * float(np.mean(["breached" in r["outcome"] or "floor" in r["outcome"] for r in res])), 1))


def monte_carlo(d, paths=5000, n_days=252, block=5, seed=21):
    rng = np.random.default_rng(seed)
    L = len(d)
    idx = np.empty((paths, n_days), int)
    j = rng.integers(L, size=paths)
    for t in range(n_days):
        idx[:, t] = j
        j = np.where(rng.random(paths) < 1 / block, rng.integers(L, size=paths), (j + 1) % L)
    pnl, low, closed = d.pnl.values[idx], d.low.values[idx], d.closed.values[idx]
    cum = np.cumsum(pnl, 1)
    prev = np.c_[np.zeros(paths), cum[:, :-1]]
    lo = prev + low
    ref = START + np.maximum(prev, 0)
    day5 = low <= -0.05 * ref
    loss10 = lo <= -0.10 * START
    fail = day5 | loss10
    hit = (cum >= 0.10 * START) & (np.cumsum(closed >= 0.005 * START, 1) >= 3)
    ff = np.where(fail.any(1), fail.argmax(1), 10 ** 9)
    fh = np.where(hit.any(1), hit.argmax(1), 10 ** 9)
    passed = fh < ff
    return dict(paths=paths, horizon_trading_days=n_days,
                p_hit_10pct_loss=round(float(loss10.any(1).mean()), 4),
                p_hit_ea_floor_9pct=round(float((lo <= -0.09 * START).any(1).mean()), 4),
                p_any_day_le_minus5pct=round(float(day5.any(1).mean()), 4),
                p_step1_pass_1y=round(float(passed.mean()), 3),
                median_trading_days_to_plus10=float(np.median(fh[passed] + 1)) if passed.any() else None)


def crash_day(p, ck, fr, day):
    d = daily_table(ck)
    h = fr["1h"]
    dc = h.close.resample("1D").last().dropna()
    move = float(dc.pct_change().loc[day] * 100)
    rng_pct = float((h.loc[str(day.date())].low.min() / dc.shift(1).loc[day] - 1) * 100)
    tr = p[(p.t_in <= day + pd.Timedelta("1D")) & (p.t_close >= day)]
    row = d.loc[day] if day in d.index else None
    return dict(day=str(day.date()), gold_close_to_close_pct=round(move, 2), gold_low_vs_prev_close_pct=round(rng_pct, 2),
                day_pnl_usd=round(float(row.pnl), 0) if row is not None else 0.0,
                intraday_low_usd=round(float(row.low), 0) if row is not None else 0.0,
                trades_touching_day=int(len(tr)), trades_pnl_usd=round(float(tr.pnl.sum()), 0))


def main() -> int:
    fr = b.frames()
    cand = b.candidates(fr)
    mix = pd.concat([cand[k]().assign(strategy=k) for k in em.MIX])
    ea = em.ea_rules_trades(fr)[["t_in", "t_out", "side", "r", "strategy"]]
    allt = pd.concat([mix[["t_in", "t_out", "side", "r", "strategy"]], ea])
    dc = fr["1h"].close.resample("1D").last().dropna()
    worst = dc.pct_change().nsmallest(3)
    rep = dict(generated="2026-11-21", period=f"{fr['1h'].index[0].date()} to {fr['1h'].index[-1].date()}",
               data="GC=F hourly (yfinance), UTC; assumed ~ server time", scenarios={})
    for name, kw in SCEN.items():
        p, mt, ck = run(allt, fr, kw)
        r = dict(settings={k: v for k, v in kw.items() if k != "weights"} | {"weights": "weights" in kw},
                 **stats(p, ck), the5ers=summarize_attempts(attempts(p, mt, ck, floor=kw.get("eq_floor"))))
        if True:                                    # MC asked for E and F; run on all for comparison
            d = daily_table(ck)
            r["monte_carlo"] = monte_carlo(d)
            if kw.get("extra_cost"):
                r["monte_carlo_haircut50"] = monte_carlo(haircut_days(p, d))
            r["weekend_gap"] = weekend(ck, fr)
            r["worst_gold_days"] = [crash_day(p, ck, fr, dd) for dd in worst.index]
            i = int(ck.net_lots.abs().idxmax())
            lots, px = float(ck.net_lots.iloc[i]), float(fr["1h"].close.asof(ck.c.iloc[i] - pd.Timedelta("1h")))
            r["gap_stress_9_5pct"] = dict(max_net_lots=round(lots, 2), at=str(ck.c.iloc[i]), price=round(px, 1),
                                          loss_if_all_stops_gapped_usd=round(abs(lots) * 100 * px * 0.095, 0),
                                          max_open_risk_usd=round(float(ck.open_risk.max()), 0))
        rep["scenarios"][name] = r
        print(name, {k: r[k] for k in ("trades", "win_pct", "avg_r", "net_usd", "worst_day_usd", "max_dd_pct_of_10k",
                                       "lowest_equity_usd")}, r["the5ers"]["step1_pass_pct"], r["the5ers"]["funded_pct"],
              r["the5ers"]["breached_pct"], r["the5ers"]["floor_halt_pct"],
              r["the5ers"]["avg_payout_per_attempt_usd"], r["the5ers"]["median_months_to_first_payout"], r["monte_carlo"], flush=True)
    out = ROOT / "reports" / "ea-mix-scenarios-2026-11-21.json"
    out.write_text(json.dumps(rep, indent=1, default=str))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

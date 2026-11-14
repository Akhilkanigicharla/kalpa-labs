"""A282: Alpha Brain on live data, day by day (Akhil 14 Nov 2026: "do more testing with live data and give me
results day wise").

1. 2026 so far, day by day: Rs 10,000 starting 1 Jan 2026, fresh prices to the latest NSE close. The 2026 model
   was trained only on data up to Dec 2025 (21-day gap), so every day here is unseen. Compared with the current
   bot and buy-and-hold Nifty on the same days.
2. Rolling starts: start Rs 10,000 at every month from Jan 2019 and hold the rules for 3 and 12 months.
   Shows how often a new user would have been up or down, not just one lucky start date.

Run: python3 07-trading/research/a282_alpha_brain_live.py   (refresh: delete 07-trading/data/a273 first)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a273_multi_strategy as A  # noqa: E402
import a281_alpha_brain as B  # noqa: E402

LIVE_START = "2026-01-01"


def lines(px, nifty, pred, start, end=None):
    """Daily Rs values for each line on px[start:end]. Decisions at month ends inside the window
    (plus the start day itself, so money goes in at once)."""
    w = px.loc[start:end] if end else px.loc[start:]
    rb = A.rebalance_days(w.index, "M")
    if rb[0] != w.index[0]:
        rb = [w.index[0]] + rb
    rb = [d for d in rb if d != w.index[-1]]
    tr200 = A.trend_on(nifty)
    out = {
        "brain": A.simulate(w, B.targets_from(pred, px, rb, 5)),
        "brain_filter": A.simulate(w, B.targets_from(pred, px, rb, 5, tr200)),
        "bot": A.simulate(w, A.strat_baseline(w, nifty, rb)),
        "nifty": A.simulate(w, {rb[0]: {"NIFTYBEES": 1.0}}),
    }
    return {k: v[0] for k, v in out.items()}, {k: v[1] for k, v in out.items()}


def predictions_for(px, pn, dates_needed):
    """Walk-forward predictions; adds any decision day not on the weekly grid (first day of a window)."""
    return B.walk_forward(pn)


def main():
    px, nifty, vix, inr, cpi = B.load()
    weekly = A.rebalance_days(px.index, "W")
    monthly = A.rebalance_days(px.index, "M")
    extra = [d for d in px.index[px.index >= "2019-01-01"] if d.is_month_start or d == px.index[px.index >= LIVE_START][0]]
    dates = sorted(set(weekly) | set(monthly) | set(extra))
    pn = B.panel(px, nifty, vix, inr, cpi, dates)
    pred = B.walk_forward(pn)
    last = px.index[-1].date()
    print(f"live data to {last}; assets {px.shape[1]}")

    # ---------- 1. 2026 day by day ----------
    vals, trades = lines(px, nifty, pred, LIVE_START)
    day = pd.DataFrame(vals).round(0)
    for k in vals:
        day[f"{k}_day_rs"] = day[k].diff().fillna(day[k].iloc[0] - A.CAPITAL).round(0)
    day.index.name = "date"
    day.to_csv(HERE / "a282_daily_2026.csv")
    picks = []
    for d in [x for x in A.rebalance_days(px.loc[LIVE_START:].index, "M") if x != px.index[-1]] or []:
        pass
    rb = A.rebalance_days(px.loc[LIVE_START:].index, "M")
    rb = [px.loc[LIVE_START:].index[0]] + [d for d in rb if d != px.index[-1]]
    tg = B.targets_from(pred, px, rb, 5)
    for d in rb:
        picks.append({"decided": d.date(), "picks": " ".join(sorted(tg.get(d, {})))})
    pd.DataFrame(picks).to_csv(HERE / "a282_picks_2026.csv", index=False)

    summ = []
    for k in vals:
        v = vals[k]
        dr = v.diff().fillna(v.iloc[0] - A.CAPITAL)
        m = v.groupby(v.index.to_period("M")).last()
        summ.append({"line": k, "end_rs": round(v.iloc[-1]), "return_%": round(100 * (v.iloc[-1] / A.CAPITAL - 1), 1),
                     "worst_fall_%": round(100 * (v / v.cummax() - 1).min(), 1),
                     "green_days_%": round(100 * (dr > 0).mean(), 1), "avg_day_rs": round(dr.mean(), 1),
                     "best_day_rs": round(dr.max()), "worst_day_rs": round(dr.min()), "trades": trades[k],
                     "days": len(v)})
    summ = pd.DataFrame(summ)
    monthly_tbl = pd.DataFrame({k: v.groupby(v.index.to_period("M")).last() for k, v in vals.items()})
    monthly_tbl = pd.concat([pd.DataFrame({k: [A.CAPITAL] for k in vals}, index=["start"]), monthly_tbl])
    mret = (monthly_tbl.pct_change() * 100).round(1).iloc[1:]
    mret.index = [str(i) for i in mret.index]
    mret.to_csv(HERE / "a282_monthly_2026.csv")

    # ---------- 2. rolling starts ----------
    roll = []
    starts = [d for d in px.index if d >= pd.Timestamp("2019-01-01") and d.is_month_start] or []
    starts = sorted({px.index[px.index >= pd.Timestamp(f"{y}-{m:02d}-01")][0]
                     for y in range(2019, 2027) for m in range(1, 13)
                     if (px.index >= pd.Timestamp(f"{y}-{m:02d}-01")).any()})
    for s in starts:
        for months in (3, 12):
            e = s + pd.DateOffset(months=months)
            if e > px.index[-1]:
                continue
            v, _ = lines(px, nifty, pred, s, e)
            roll.append({"start": s.date(), "months": months,
                         **{k: round(100 * (vv.iloc[-1] / A.CAPITAL - 1), 2) for k, vv in v.items()}})
    roll = pd.DataFrame(roll)
    roll.to_csv(HERE / "a282_rolling_starts.csv", index=False)
    rs = []
    for months, g in roll.groupby("months"):
        for k in vals:
            rs.append({"hold_months": months, "line": k, "starts": len(g), "median_%": round(g[k].median(), 1),
                       "worst_%": round(g[k].min(), 1), "best_%": round(g[k].max(), 1),
                       "lost_money_%_of_starts": round(100 * (g[k] < 0).mean(), 1),
                       "beat_bot_%_of_starts": round(100 * (g[k] > g["bot"]).mean(), 1) if k != "bot" else np.nan})
    rs = pd.DataFrame(rs)
    rs.to_csv(HERE / "a282_rolling_summary.csv", index=False)

    pd.set_option("display.width", 220)
    print(summ.to_string(index=False))
    print(mret.to_string())
    print(pd.read_csv(HERE / "a282_picks_2026.csv").to_string(index=False))
    print(rs.to_string(index=False))
    print(day[["brain", "brain_day_rs", "bot", "bot_day_rs", "nifty", "nifty_day_rs"]].tail(10).to_string())


if __name__ == "__main__":
    main()

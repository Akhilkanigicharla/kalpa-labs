"""A326: judge the gold bot ONLY as a funded-account bot (Akhil, 21 Nov 2026: "we are building this bot for
algo funded account trading only").

Rules: The5%ers High Stakes, checked 21 Nov 2026 on the5ers.com/high-stakes plus second sources:
  Step 1 target 10% ("New"; "Classic" = 8%), Step 2 target 5%, 5% daily loss, 10% max loss (from the starting
  balance), 3 profitable days per step (a day with >= 0.5% of the starting balance in CLOSED profit),
  no time limit, no trades within 2 min of high-impact news (our 2 h blackout covers it),
  funded split 80/20, EAs allowed if every position has a stop loss.  First payout 14 days after funding and
  every 14 days after (third-party sources; not on the official page = unverified).
Simulation: a new $10K attempt starts every Monday of the 2-year test.  Trades = the A323 mix (or the EA-only
  strategy), A325 streak sizing on, news-blackout trades removed, at several risk levels.  The EA's own
  4% daily stop is applied (closes the day), so the 5% firm limit is a buffer.  Daily loss is measured on
  CLOSED trades plus the day's worst closing trade timing; open floating loss inside the day cannot be
  measured from these trades, so real fail rates are somewhat higher (the 1% buffer is for that).
Funded stage: from funding to the end of the data; every 14 days 80% of the profit above $10K is paid out
  and the balance resets to $10K (no scaling assumed: conservative).  Fee per attempt: unverified for $10K,
  shown as "fee" in the summary so Akhil can plug in the real price.
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
import macro_layer_gold as ml  # noqa: E402

START = 10_000.0
EA_DAY_STOP = 0.04


def prepare(t: pd.DataFrame) -> pd.DataFrame:
    """A325 layer: drop trades within 2 h of CPI/NFP/FOMC, streak size per strategy (closed trades only)."""
    t = t.sort_values("t_in").reset_index(drop=True)
    ev = ml.events_utc().values
    ti = t.t_in.values.astype("datetime64[ns]")
    j = np.searchsorted(ev, ti)
    gap = np.minimum(np.abs((ev[np.minimum(j, len(ev) - 1)] - ti) / np.timedelta64(1, "h")),
                     np.abs((ti - ev[np.maximum(j - 1, 0)]) / np.timedelta64(1, "h")))
    t = t[gap > 2].reset_index(drop=True)
    w = []
    for _, row in t.iterrows():
        prior = t[(t.strategy == row.strategy) & (t.t_out < row.t_in)]
        last = prior.sort_values("t_out").r.iloc[-1] if len(prior) else 0.0
        w.append(1.5 if last > 0.05 else (0.75 if last < -0.05 else 1.0))
    t["w"] = w
    return t


def run_attempt(t: pd.DataFrame, start: pd.Timestamp, risk: float, step1: float, step2: float, end: pd.Timestamp):
    """One The5%ers High Stakes attempt from `start`. Returns dict(outcome, days_to_fund, payouts_usd, ...)."""
    u = t[t.t_in >= start].sort_values("t_out")
    stage, targets = 1, {1: step1, 2: step2}
    bal = START
    day, day_pnl, prof_days, locked_day = None, 0.0, set(), None
    funded_at, paid, next_pay, fund_bal = None, 0.0, None, START
    for _, row in u.iterrows():
        d = row.t_out.normalize()
        if d != day:
            day, day_pnl = d, 0.0
        if locked_day is not None and row.t_in.normalize() == locked_day:
            continue                                        # EA's 4% daily stop: no new trades that day
        p = row.r * row.w * START * risk
        day_pnl += p
        if stage <= 2:
            bal += p
            if day_pnl <= -0.05 * START or bal <= START * 0.90:
                return dict(outcome=f"failed step {stage}", payouts_usd=0.0, days_to_fund=None)
            if day_pnl <= -EA_DAY_STOP * START:
                locked_day = d
            if day_pnl >= 0.005 * START:
                prof_days.add(d)
            if bal >= START * (1 + targets[stage]) and len(prof_days) >= 3:
                if stage == 1:
                    stage, bal, prof_days = 2, START, set()
                else:
                    stage, funded_at = 3, row.t_out
                    next_pay, fund_bal = funded_at + pd.Timedelta("14D"), START
                    day_pnl = 0.0
        else:
            if row.t_out >= next_pay:                        # payout day: 80% of profit above start
                if fund_bal > START:
                    paid += 0.8 * (fund_bal - START)
                    fund_bal = START
                next_pay = next_pay + pd.Timedelta("14D")
            fund_bal += p
            if day_pnl <= -0.05 * START or fund_bal <= START * 0.90:
                return dict(outcome="funded then lost", payouts_usd=round(paid, 0),
                            days_to_fund=(funded_at - start).days, funded_days=(row.t_out - funded_at).days)
            if day_pnl <= -EA_DAY_STOP * START:
                locked_day = d
    if stage <= 2:
        return dict(outcome=f"still in step {stage}", payouts_usd=0.0, days_to_fund=None)
    return dict(outcome="funded, still running", payouts_usd=round(paid, 0), days_to_fund=(funded_at - start).days,
                funded_days=(end - funded_at).days)


def summarize(t, risk, step1, step2):
    end = t.t_out.max()
    starts = pd.date_range(t.t_in.min().normalize(), end - pd.Timedelta("90D"), freq="W-MON")  # 90+ days of runway each
    res = [run_attempt(t, s, risk, step1, step2, end) for s in starts]
    out = pd.Series([r["outcome"] for r in res]).value_counts(normalize=True).round(2).to_dict()
    funded = [r for r in res if r["days_to_fund"] is not None]
    pays = np.array([r["payouts_usd"] for r in res])
    return dict(risk_pct=risk * 100, attempts=len(res), outcomes=out,
                reached_funded=round(len(funded) / len(res), 2),
                median_days_to_funded=float(np.median([r["days_to_fund"] for r in funded])) if funded else None,
                avg_payout_per_attempt_usd=round(float(pays.mean()), 0),
                median_payout_per_attempt_usd=round(float(np.median(pays)), 0),
                avg_payout_per_funded_month_usd=round(float(sum(r["payouts_usd"] for r in funded) /
                                                      max(sum(r.get("funded_days", 0) for r in funded) / 30.4, 1)), 0))


def main() -> int:
    src = sorted(Path("reports").glob("best-combo-gold-trades-2*.csv"))[-1]
    raw = pd.read_csv(src, parse_dates=["t_in", "t_out"])
    books = {"mix_13_strategies": raw, "ea_only_EA+MSNR_1h": raw[raw.strategy == "EA+MSNR 1h"]}
    rep = dict(generated=str(date.today()), rules="The5%ers High Stakes, checked 2026-11-21", results={})
    for name, t in books.items():
        tt = prepare(t)
        for prog, (s1, s2) in (("New 10%/5%", (0.10, 0.05)), ("Classic 8%/5%", (0.08, 0.05))):
            risks = (0.0015, 0.0025, 0.0035) if name.startswith("mix") else (0.005, 0.0075, 0.01, 0.015)
            rep["results"][f"{name} | {prog}"] = [summarize(tt, r, s1, s2) for r in risks]
    (Path("reports") / f"funded-sim-gold-{date.today()}.json").write_text(json.dumps(rep, indent=1, default=str))
    for k, v in rep["results"].items():
        print(k)
        for r in v:
            print("  ", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

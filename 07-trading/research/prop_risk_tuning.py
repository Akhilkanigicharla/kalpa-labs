"""A331: tune the bot's RISK PLAN like the traders who pass (Akhil, 21 Nov 2026: "tune our bot in the top 14%
... use first principles ... make it happen").

First principles.  A challenge is a race between two barriers: +10% target (step 2: +5%) before -10% max loss
or -5% in one day.  For a strategy with zero edge and small bets, P(reach +a before -b) ~ b / (a + b), so a
disciplined zero-edge bot gets funded ~ 0.5 x 0.67 ~ 1/3 of the time; industry data says 14% do, because most
traders blow the daily limit or bet too big.  So the levers are risk per trade, how risk reacts to drawdown,
how it reacts near the target, the daily stop, and (after funding) how to keep the account alive for payouts.

Input: every trade of the EA as built (reports/ea-mix-backtest-trades-*.csv, A329): R result, entry/exit time,
and the risk multiplier the EA actually used (streak sizing and 0.01-lot rounding: risk / $25).
Edge scenarios (robustness, decided before the test): as tested, half the edge, zero edge (each trade's R
shifted so the average R is 50% / 0% of the tested one).  A plan must hold up when the edge shrinks.
Risk plans (each scales the EA's base risk; fixed list, no fitting inside):
  base      0.10 / 0.15 / 0.20 / 0.25 / 0.35 / 0.50 % per trade
  dd_ladder risk x max(0.25, 1 - drawdown / 6%)   (cut size as losses grow; never bet the account back)
  finish    near the target, risk <= remaining distance / 4 (do not overshoot into a loss streak at the end)
  daystop   no new trades after the day's closed P&L reaches -1.5% / -2.5% (EA default -4%)
  funded    after funding use half the challenge risk (payouts need survival, not speed)
Attempts start every Monday; selection on attempts started before 2025-09-01; results also reported for later
starts and for the half-edge and zero-edge scenarios.  Score = average payout per attempt in the first 12
funded months (80% split, paid every 14 days, balance back to $10K), plus P(funded).
Research code only.  Not investment advice.
"""
from __future__ import annotations

import itertools
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

START = 10_000.0
SPLIT = pd.Timestamp("2025-09-01")


def load() -> pd.DataFrame:
    src = sorted((Path(__file__).resolve().parents[1] / "reports").glob("ea-mix-backtest-trades-*.csv"))[-1]
    t = pd.read_csv(src, parse_dates=["t_in", "t_out"]).sort_values("t_in").reset_index(drop=True)
    t["mult"] = t.risk / (START * 0.0025)                 # what the EA used vs the 0.25% base
    return t


def shift_edge(t: pd.DataFrame, keep: float) -> pd.DataFrame:
    w = t.mult
    mean_r = float((t.r * w).sum() / w.sum())
    return t.assign(r=t.r - (1 - keep) * mean_r)


DAY = 86_400 * 10**9
D14 = 14 * DAY


def arrays(t: pd.DataFrame) -> dict:
    return dict(ti=t.t_in.values.astype("datetime64[ns]").astype("int64"), to=t.t_out.values.astype("datetime64[ns]").astype("int64"),
                r=t.r.values.astype(float), m=t.mult.values.astype(float))


def attempt(A: dict, start: pd.Timestamp, plan: dict, months_funded=12) -> dict:
    """Event loop: risk is set at ENTRY from the equity of trades CLOSED by then; P&L lands at exit.
    Days are UTC calendar days of the exit (closed-P&L daily limit; open floating loss is not seen)."""
    import heapq
    ti, to, rr, mm = A["ti"], A["to"], A["r"], A["m"]
    i0 = int(np.searchsorted(ti, start.value))
    stage, bal, peak = 1, START, START
    target = (0.0, 0.10, 0.05)
    prof_days, day_pnl = set(), {}
    heap = []                                             # (t_out, seq, pnl, stage)
    funded_at, paid, next_pay, fund_end = None, 0.0, None, None
    res, seq = "running", 0

    def settle(ts):
        nonlocal bal, peak, stage, funded_at, next_pay, fund_end, paid, res, prof_days
        while heap and heap[0][0] <= ts:
            tout, _, pnl, st = heapq.heappop(heap)
            if st != stage:
                continue                                  # opened before an account reset
            d = tout // DAY
            if stage == 3:
                while tout >= next_pay:
                    if bal > START:
                        paid += 0.8 * (bal - START)
                        bal = peak = START
                    next_pay += D14
            bal += pnl
            peak = max(peak, bal)
            day_pnl[d] = day_pnl.get(d, 0.0) + pnl
            if day_pnl[d] <= -0.05 * START or bal <= 0.90 * START:
                res = f"failed step {stage}" if stage <= 2 else "funded then lost"
                return False
            if stage <= 2:
                if day_pnl[d] >= 0.005 * START:
                    prof_days.add(d)
                if bal >= START * (1 + target[stage]) and len(prof_days) >= 3:
                    if stage == 1:
                        stage, bal, peak, prof_days = 2, START, START, set()
                    else:
                        stage, bal, peak = 3, START, START
                        funded_at = tout
                        next_pay = tout + D14
                        fund_end = tout + int(30.4 * months_funded) * DAY
            elif tout >= fund_end:
                res = "funded 12 months"
                return False
        return True

    alive = True
    for i in range(i0, len(ti)):
        if not settle(ti[i]):
            alive = False
            break
        if day_pnl.get(ti[i] // DAY, 0.0) <= -plan["daystop"] * START:
            continue
        risk = plan["base"] * (plan["funded_mult"] if stage == 3 else 1.0)
        if plan["dd_ladder"]:
            risk *= max(0.25, 1 - max(0.0, (peak - bal) / START) / 0.06)
        if plan["finish"] and stage <= 2:
            remaining = START * (1 + target[stage]) - bal
            if remaining > 0:
                risk = min(risk, remaining / 4 / START)
        seq += 1
        heapq.heappush(heap, (to[i], seq, rr[i] * START * risk * mm[i], stage))
    if alive:
        settle(np.iinfo("int64").max)
    if res == "running" and stage == 3:
        res = "funded, data ended"
    return dict(res=res, funded=funded_at is not None,
                days=(funded_at - start.value) / DAY if funded_at is not None else None, paid=paid)


def evaluate(t, plan: dict, starts) -> dict:
    A = t if isinstance(t, dict) else arrays(t)
    rs = [attempt(A, s, plan) for s in starts]
    f = [r for r in rs if r["funded"]]
    return dict(attempts=len(rs), p_funded=round(len(f) / len(rs), 3),
                median_days=float(np.median([r["days"] for r in f])) if f else None,
                payout_per_attempt=round(float(np.mean([r["paid"] for r in rs])), 0),
                funded_lost=round(float(np.mean([r["res"] == "funded then lost" for r in rs])), 3))


def plans():
    for base, ladder, finish, daystop, fm in itertools.product(
            (0.0010, 0.0015, 0.0020, 0.0025, 0.0035, 0.0050), (False, True), (False, True), (0.015, 0.025, 0.04), (1.0, 0.5)):
        yield dict(base=base, dd_ladder=ladder, finish=finish, daystop=daystop, funded_mult=fm)


def name(p):
    return (f"{p['base']*100:.2f}%" + (" +ladder" if p["dd_ladder"] else "") + (" +finish" if p["finish"] else "")
            + f" daystop {p['daystop']*100:.1f}%" + (" funded x0.5" if p["funded_mult"] < 1 else ""))


_SC: dict = {}
_EARLY: list = []


def _one(p):
    return dict(plan=name(p), cfg=p, early=evaluate(_SC["as tested"], p, _EARLY),
                early_half=evaluate(_SC["half edge"], p, _EARLY))


def main() -> int:
    t = load()
    end = t.t_out.max()
    starts = pd.date_range(t.t_in.min().normalize(), end - pd.Timedelta("120D"), freq="W-MON")
    early = [s for s in starts if s < SPLIT]
    late = [s for s in starts if s >= SPLIT]
    scen = {"as tested": t, "half edge": shift_edge(t, 0.5), "zero edge": shift_edge(t, 0.0)}
    global _SC, _EARLY
    _SC = {k: arrays(v) for k, v in scen.items()}
    _EARLY = early
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(_one, list(plans()), chunksize=4))
    # choose on the EARLY starts: best payout per attempt in the HALF-EDGE world (robust), tie -> P(funded)
    best = max(rows, key=lambda r: (r["early_half"]["payout_per_attempt"], r["early_half"]["p_funded"]))
    current = next(r for r in rows if r["cfg"] == dict(base=0.0025, dd_ladder=False, finish=False, daystop=0.04, funded_mult=1.0))
    rep = dict(generated=str(date.today()), selection="best payout per attempt with HALF the backtest edge, attempts started before 2025-09-01",
               chosen=best["plan"], chosen_cfg=best["cfg"], current_ea=current["plan"], results={})
    for label, r in (("chosen", best), ("current EA", current)):
        rep["results"][label] = {sc: dict(all_starts=evaluate(tt, r["cfg"], starts), later_starts=evaluate(tt, r["cfg"], late))
                                 for sc, tt in scen.items()}
    rep["top10_early_half_edge"] = [dict(plan=r["plan"], **r["early_half"]) for r in
                                    sorted(rows, key=lambda r: -r["early_half"]["payout_per_attempt"])[:10]]
    out = Path(__file__).resolve().parents[1] / "reports" / f"prop-risk-tuning-{date.today()}.json"
    out.write_text(json.dumps(rep, indent=1, default=str))
    print("chosen:", best["plan"])
    for label, d in rep["results"].items():
        print(label)
        for sc, v in d.items():
            print("  ", sc, "ALL", v["all_starts"], "| LATER", v["later_starts"])
    print("top 5 (early, half edge):")
    for r in rep["top10_early_half_edge"][:5]:
        print("  ", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

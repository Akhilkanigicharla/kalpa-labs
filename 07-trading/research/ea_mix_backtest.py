"""A329: backtest of the MT5 EA as it is now built (A320 EA + A325 layer + A327 mix engine), 2 years of gold.

Akhil (21 Nov 2026): "Do back testing now".  The MT5 Strategy Tester cannot run in the build cloud (Windows
desktop app), so this replays the EA's own rules in Python on the same free hourly data:
  - the 13 strategies' setups, fills and exits come from the research functions that tests/test_mix_port.py
    proves identical to the MQL5 port (fresh / QM / EMA9 + the EA's own EA+MSNR H1 strategy);
  - the EA's own strategy runs with the EA rules (1 position, 3 trades a day, cooldown, 3-loss pause),
    at its own risk input (inp_RiskPct, default 0.75%), tested also at 0.25%;
  - mix trades: 0.25% risk (inp_MixRiskPct), x1.5 after that strategy's last trade won, x0.75 after a loss;
  - open-risk cap 2% of equity for mix trades (inp_MixMaxOpenRiskPct; 3% until A335): a new trade that would push the
    open mix risk over it is skipped;
  - broker lots: $100 per $1 move per lot, 0.01-lot steps; below 0.01 lot the trade uses 0.01 only if that
    risks <= 1.5x the target, else it is skipped (CMixEngine.Lot);
  - no entries within 2 h of CPI / jobs report / FOMC (A325);
  - EA daily stop: after closed losses reach 4% in a day, no new entries that day;
  - The5%ers High Stakes check (funded_sim_gold.run_attempt) on the resulting dollar results.
Not modelled: broker spread spikes, swaps, partial fills, H4 bars aligned to broker time.
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
import best_combo_gold as b  # noqa: E402
import ea_design_gold as e  # noqa: E402
import ea_msnr_gold as m  # noqa: E402
import funded_sim_gold as fs  # noqa: E402
import macro_layer_gold as ml  # noqa: E402

START = 10_000.0
USD_PER_LOT_PER_DOLLAR = 100.0      # XAUUSD: 100 oz per lot
MIX = ["MSNR fresh_v long 1h", "MSNR qm long 1h", "MSNR qm short 1h", "EMA9 2h", "MSNR fresh_v long 2h",
       "MSNR fresh_v short 2h", "MSNR qm long 2h", "EMA9 4h", "MSNR fresh_v long 4h", "MSNR fresh_v short 4h",
       "MSNR qm long 4h", "MSNR qm short 4h"]


def ea_rules_trades(fr) -> pd.DataFrame:
    """The EA's own EA+MSNR H1 strategy under the EA rules (not 'every setup')."""
    h1, h4 = fr["1h"], fr["4h"]
    e.SCALED, e.DROP, e.EVERY, e.LADDER = True, set(e.LOOSE), False, False
    h4f, h1f = e.h4_features(h4, h1), e.h1_features(h1)
    sig = e.setups(h1, pd.Timedelta("1h"), h1f, h4f)
    st = m.msnr_state(h1, h4)
    sig = m.apply(sig, st, pd.Series(0.0, index=h1.index), pd.Series(e.g.atr(h1), index=h1.index), {"fresh"}, h1.index)
    t = e.simulate(h1, pd.Timedelta("1h"), sig, pd.Timedelta("2h"))
    t = t[["t_in", "t_out", "side", "r", "entry", "stop"]] if "entry" in t else t[["t_in", "t_out", "side", "r"]]
    return t.assign(strategy="EA+MSNR 1h (EA rules)")


def stop_dist(strategy: str, row, atr_by_tf) -> float:
    """Stop distance in $ for lot sizing. Research trades carry R only, so the distance is rebuilt from the
    timeframe ATR at entry with each setup's stop rule (fresh: 1 ATR, QM: ~1.2 ATR median, EMA9: ~0.6 ATR,
    EA: max(1.5 ATR(M15-scaled), swing))."""
    tf = strategy.split()[-1].replace("(EA", "").strip() if "EA rules" not in strategy else "1h"
    a = atr_by_tf[tf].asof(row.t_in)
    if not np.isfinite(a):
        a = atr_by_tf[tf].dropna().iloc[0]
    if "fresh_v" in strategy:
        return 1.0 * a
    if "qm" in strategy:
        return 1.2 * a
    if "EMA9" in strategy:
        return 0.6 * a
    return 1.5 * a / 2.0                         # EA: 1.5 x M15 ATR ~ 0.75 x H1 ATR


# 21 Nov 2026 quant validation (research/validation/quant-validation-2026-11-21.md, section 8): risk multiplier per
# strategy. KEEP 1.0 / HALF 0.5 / CUT 0.  Strategies not listed keep 1.0.
WEIGHTS_2026_11_21 = {
    "MSNR fresh_v long 1h": 1.0, "MSNR fresh_v long 2h": 1.0, "MSNR fresh_v short 2h": 1.0,
    "MSNR fresh_v long 4h": 0.5, "MSNR qm long 1h": 0.5, "MSNR qm long 4h": 0.5, "MSNR qm short 1h": 0.5,
    "EA+MSNR 1h (EA rules)": 0.5,
    "EMA9 2h": 0.0, "EMA9 4h": 0.0, "MSNR qm long 2h": 0.0, "MSNR fresh_v short 4h": 0.0, "MSNR qm short 4h": 0.0,
}


def _friday_cuts(h1: pd.DataFrame, hour: int) -> set:
    """Checkpoint (bar close) time of the Friday cut: the first bar close at/after Friday `hour`:00, or the last
    Friday bar close when the market shuts before then (GC=F's last Friday bar closes 21:00 or 22:00 UTC)."""
    c = pd.Series(h1.index + pd.Timedelta("1h"), index=h1.index)
    fri = c[c.index.dayofweek == 4]
    out = set()
    for _, g in fri.groupby(fri.index.date):
        cut = g.iloc[0].normalize() + pd.Timedelta(hours=hour)
        late = g[g >= cut]
        out.add(late.iloc[0] if len(late) else g.iloc[-1])
    return out


def portfolio(trades: pd.DataFrame, fr, ea_risk: float, mix_risk: float = 0.0025, cap: float = 0.02,
              news_block_h: float = 2.0, *, weights: dict | None = None, max_pos: int | None = None,
              no_opposite: bool = False, friday_cut: float | None = None, friday_hour: int = 22,
              extra_cost: float = 0.0, min_stop: float = 0.0, lot_cap: float | None = None,
              day_stop_eq: float | None = None, eq_floor: float | None = None, curve: bool = False,
              gap_pct: float | None = None, gap_budget: float = 0.03, day_profit_cap: float | None = None,
              margin_lev: float | None = None, margin_use: float = 0.5,
              shock_pct: float | None = None, shock_budget: float = 0.02,
              derisk_at: set | None = None, derisk_shock: float = 0.03, derisk_budget: float = 0.02):
    """EA portfolio replay.  Defaults = the A329 behaviour (closed-loss 4% day stop, no MTM rules).

    Options (21 Nov 2026, mirroring the EA changes):
      weights      risk multiplier per strategy (0 = strategy off)
      max_pos      max open positions across all strategies (EA included)
      no_opposite  skip a signal whose side is opposite to any open position
      friday_cut   at the Friday `friday_hour`:00 checkpoint, close positions (losers first, most negative first)
                   until open risk <= friday_cut x $10K
      extra_cost   extra $ per oz per side, charged on every fill (entry + exit)
      min_stop     minimum stop distance in $ used for sizing;  lot_cap: max lots per trade
      day_stop_eq  replaces the closed-loss day stop: if equity <= (1-x) x max(balance, equity) at day start,
                   close all at the current price and no new entries that day
      eq_floor     if equity <= this ($), close all and stop trading for good
      day_profit_cap (A337, E8 Pro) once equity is day_profit_cap x START above the day base, close all and stop for
                   the day (E8 only counts 2%/day toward target and payouts)
      shock_pct    (A346) skip an entry if an instant jump of shock_pct against the whole net book (stops skipped)
                   would lose more than shock_budget x START minus what the day has already lost
      derisk_at    (A346) bar times (CPI/NFP/FOMC and the daily break) where the net book is cut, losers first then
                   biggest lot, until a derisk_shock jump would lose <= derisk_budget x START minus today's loss;
                   no new entries on those bars
      margin_lev   (A337) skip an entry if all open lots + this one need more than margin_use x equity at this
                   leverage (E8 metals 1:15; EA uses 50% of free margin)
      gap_pct      (A336) at the Friday cut also assume a weekend gap of gap_pct jumps every stop: worst loss of a
                   position = max(risk, gap_pct x price x 100 oz x lot); close losers first, then largest lot,
                   until the sum <= gap_budget x max(balance, equity)
    Equity is marked at every 1h bar close (checkpoint).  Research trades carry R only, so the entry price is the
    1h open at t_in and the open R is side x (close - entry) / stop distance, clipped to [min(-1, r), max(2, r)].
    With curve=True returns (trades, mtm_records, checkpoints)."""
    atr_by_tf = {tf: pd.Series(e.g.atr(x), index=x.index + pd.Timedelta(tf)) for tf, x in fr.items()}
    ev = ml.events_utc().values
    h1 = fr["1h"]
    C = list(h1.index + pd.Timedelta("1h"))
    PX = h1.close.values
    open_px = h1.open
    fri = _friday_cuts(h1, friday_hour) if friday_cut is not None else set()
    t = trades.sort_values("t_in").reset_index(drop=True)
    open_pos: list[dict] = []
    last_r: dict[str, float] = {}
    closed_day: dict = {}
    out: list[dict] = []
    mtm_rec: list[tuple] = []
    ck_rec: list[tuple] = []
    st = dict(bal=START, eq=START, day=None, ref=START, locked=None, halted=False, k=0)

    def cost(p):
        return extra_cost * USD_PER_LOT_PER_DOLLAR * p["lot"] * 2

    def roll(ts):
        d = ts.normalize()
        if d != st["day"]:
            st["day"], st["ref"] = d, max(st["bal"], st["eq"])

    def close(p, pnl, when, why):
        p["pnl"], p["t_close"], p["exit"] = pnl, when, why
        p["r_real"] = pnl / p["risk"]
        st["bal"] += pnl
        last_r[p["strategy"]] = p["r"] if why == "rule" and extra_cost == 0 else p["r_real"]
        dd = when.normalize()
        closed_day[dd] = closed_day.get(dd, 0.0) + pnl
        open_pos.remove(p)

    def mtm(p, px):
        rr = p["side"] * (px - p["entry"]) / p["dist"]
        rr = min(max(rr, min(-1.0, p["r"])), max(2.0, p["r"]))
        return rr * p["risk"] - cost(p)

    def checkpoint(k):
        c, px = C[k], PX[k]
        roll(c - pd.Timedelta("1h"))
        m = {id(p): mtm(p, px) for p in open_pos}
        eq = st["bal"] + sum(m.values())
        why = None
        if eq_floor is not None and eq <= eq_floor:
            why, st["halted"] = "floor", True
        elif day_stop_eq is not None and eq <= (1 - day_stop_eq) * st["ref"]:
            why, st["locked"] = "daystop", st["day"]
        elif day_profit_cap is not None and eq - st["ref"] >= day_profit_cap * START:
            why, st["locked"] = "profitcap", st["day"]
        if why:
            for p in list(open_pos):
                close(p, m[id(p)], c, why)
        elif derisk_at is not None and c in derisk_at:
            room = derisk_budget * START - max(0.0, st["ref"] - eq)
            netf = lambda: abs(sum(q["lot"] * q["side"] for q in open_pos)) * USD_PER_LOT_PER_DOLLAR * px * derisk_shock
            for p in sorted(open_pos, key=lambda z: (m[id(z)] >= 0, -z["lot"])):
                if netf() <= room:
                    break
                close(p, m[id(p)], c, "derisk")
        if not why and c in fri:
            if sum(p["risk"] for p in open_pos) > friday_cut * START:
                for p in sorted(open_pos, key=lambda z: m[id(z)]):
                    if sum(q["risk"] for q in open_pos) <= friday_cut * START:
                        break
                    close(p, m[id(p)], c, "friday")
            if gap_pct is not None:
                worst = lambda q: max(q["risk"], gap_pct * px * USD_PER_LOT_PER_DOLLAR * q["lot"])
                budget = gap_budget * max(st["bal"], eq)
                for p in sorted(open_pos, key=lambda z: (m[id(z)] >= 0, -z["lot"])):
                    if sum(worst(q) for q in open_pos) <= budget:
                        break
                    close(p, m[id(p)], c, "weekend")
        m = {id(p): mtm(p, px) for p in open_pos}
        st["eq"] = st["bal"] + sum(m.values())
        if curve:
            mtm_rec.extend((p["tid"], k, v) for p in open_pos for v in (m[id(p)],))
            ck_rec.append((c, st["bal"], st["eq"], sum(p["lot"] * p["side"] for p in open_pos),
                           sum(p["risk"] for p in open_pos)))

    def advance(T):
        while True:
            tc = min((p["t_out"] for p in open_pos), default=None)
            kc = C[st["k"]] if st["k"] < len(C) else None
            nxt = [x for x in (tc, kc) if x is not None and x <= T]
            if not nxt:
                return
            if tc is not None and tc <= T and (kc is None or tc <= kc):
                p = min(open_pos, key=lambda z: z["t_out"])
                roll(tc)
                close(p, p["pnl"], p["t_out"], "rule")
            else:
                checkpoint(st["k"])
                st["k"] += 1

    for tid, row in enumerate(t.itertuples(index=False)):
        advance(row.t_in)
        roll(row.t_in)
        if st["halted"]:
            continue
        # news blackout
        ti = np.datetime64(row.t_in)
        j = np.searchsorted(ev, ti)
        gap = min(abs((ev[min(j, len(ev) - 1)] - ti) / np.timedelta64(1, "h")),
                  abs((ti - ev[max(j - 1, 0)]) / np.timedelta64(1, "h")))
        if gap <= news_block_h:
            continue
        # EA daily stop 4%: closed losses (default) or equity-based (day_stop_eq)
        if st["locked"] == row.t_in.normalize():
            continue
        if day_stop_eq is None:
            if closed_day.get(row.t_in.normalize(), 0.0) <= -0.04 * START:
                continue
        elif st["locked"] == row.t_in.normalize():
            continue
        w = 1.0 if weights is None else weights.get(row.strategy, 1.0)
        if w <= 0:
            continue
        if max_pos is not None and len(open_pos) >= max_pos:
            continue
        if no_opposite and any(p["side"] != row.side for p in open_pos):
            continue
        is_ea = row.strategy.startswith("EA+MSNR")
        base = ea_risk if is_ea else mix_risk
        lr = last_r.get(row.strategy, 0.0)
        mult = 1.5 if lr > 0.05 else (0.75 if lr < -0.05 else 1.0)
        target = START * base * mult * w               # funded account: payouts reset it to $10K, so no compounding
        dist = max(stop_dist(row.strategy, row, atr_by_tf), min_stop)
        lot = np.floor(target / (dist * USD_PER_LOT_PER_DOLLAR) / 0.01) * 0.01
        if lot < 0.01:
            if 0.01 * dist * USD_PER_LOT_PER_DOLLAR <= 1.5 * target:
                lot = 0.01
            else:
                continue
        if lot_cap is not None:
            lot = min(lot, lot_cap)
        risk_usd = lot * dist * USD_PER_LOT_PER_DOLLAR
        if not is_ea:
            open_mix = sum(p["risk"] for p in open_pos if not p["is_ea"])
            if open_mix + risk_usd > cap * START:
                continue
        e0 = open_px.asof(row.t_in)
        if derisk_at is not None and row.t_in.floor("h") in derisk_at:
            continue
        if shock_pct is not None:
            net = sum(p["lot"] * p["side"] for p in open_pos) + lot * row.side
            room = shock_budget * START - max(0.0, st["ref"] - st["eq"])
            if abs(net) * USD_PER_LOT_PER_DOLLAR * float(e0) * shock_pct > room:
                continue
        if margin_lev is not None:
            lots_open = sum(p["lot"] for p in open_pos) + lot
            if lots_open * USD_PER_LOT_PER_DOLLAR * float(e0) / margin_lev > margin_use * st["eq"]:
                continue
        rec = dict(tid=tid, t_in=row.t_in, t_out=row.t_out, strategy=row.strategy, side=row.side, r=row.r,
                   lot=round(lot, 2), risk=risk_usd, is_ea=is_ea, entry=float(e0), dist=dist)
        rec["pnl"] = row.r * risk_usd - cost(rec)
        rec.update(t_close=row.t_out, exit="rule", r_real=rec["pnl"] / risk_usd)
        open_pos.append(rec)
        out.append(rec)
    advance(max(t.t_out.max(), C[-1]) if len(t) else C[-1])
    p = pd.DataFrame(out)
    if not curve:
        return p
    mt = pd.DataFrame(mtm_rec, columns=["tid", "k", "mtm"])
    ck = pd.DataFrame(ck_rec, columns=["c", "bal", "eq", "net_lots", "open_risk"])
    return p, mt, ck


def report(p: pd.DataFrame) -> dict:
    r = p.r.values
    p = p.sort_values("t_out")
    eq = START + p.pnl.cumsum().values
    peak = np.maximum.accumulate(np.r_[START, eq])[1:]
    day = p.groupby(p.t_out.dt.normalize()).pnl.sum()
    months = p.groupby(p.t_out.dt.to_period("M")).pnl.sum()
    return dict(trades=int(len(p)), wins=int((r > 0.05).sum()), losses=int((r < -0.05).sum()),
                breakeven=int(((r >= -0.05) & (r <= 0.05)).sum()), win_rate=round(float((r > 0.05).mean()), 3),
                profit_usd=round(float(p.pnl.sum()), 0), worst_drop_pct=round(float(((peak - eq) / peak).max() * 100), 1),
                worst_day_usd=round(float(day.min()), 0), best_day_usd=round(float(day.max()), 0),
                profit_months=f"{int((months > 0).sum())} of {len(months)}",
                per_month_usd={str(k): round(float(v), 0) for k, v in months.items()},
                per_strategy={k: dict(trades=int(len(g)), wins=int((g.r > 0.05).sum()), losses=int((g.r < -0.05).sum()),
                                      usd=round(float(g.pnl.sum()), 0)) for k, g in p.groupby("strategy")})


def funded(p: pd.DataFrame) -> dict:
    """The5%ers High Stakes New (10%/5%) weekly attempts, using the portfolio's dollar results."""
    t = p.assign(r=p.pnl / (START * 0.0025), w=1.0)[["t_in", "t_out", "r", "w", "strategy", "side"]]
    return fs.summarize(t, 0.0025, 0.10, 0.05)


def main() -> int:
    fr = b.frames()
    cand = b.candidates(fr)
    mix = pd.concat([cand[k]().assign(strategy=k) for k in MIX])
    ea = ea_rules_trades(fr)[["t_in", "t_out", "side", "r", "strategy"]]
    allt = pd.concat([mix[["t_in", "t_out", "side", "r", "strategy"]], ea])
    rep = dict(generated=str(date.today()), period=f"{fr['1h'].index[0].date()} to {fr['1h'].index[-1].date()}", runs={})
    for name, ea_risk in (("EA risk 0.75% (current default) + mix 0.25%", 0.0075),
                          ("EA risk 0.25% + mix 0.25%", 0.0025)):
        p = portfolio(allt, fr, ea_risk)
        rep["runs"][name] = dict(**report(p), the5ers_high_stakes_new=funded(p),
                                 skipped_trades=int(len(allt) - len(p)))
        if ea_risk == 0.0025:
            p.to_csv(Path("reports") / f"ea-mix-backtest-trades-{date.today()}.csv", index=False)
    (Path("reports") / f"ea-mix-backtest-{date.today()}.json").write_text(json.dumps(rep, indent=1, default=str))
    for k, v in rep["runs"].items():
        print(k)
        print({x: v[x] for x in ("trades", "wins", "losses", "breakeven", "win_rate", "profit_usd", "worst_drop_pct",
                                 "worst_day_usd", "profit_months", "skipped_trades")})
        print(v["the5ers_high_stakes_new"])
        print(v["per_month_usd"])
        print(v["per_strategy"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

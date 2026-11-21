"""A328: backtest of the MT5 EA as it is now built (A320 EA + A325 layer + A327 mix engine), 2 years of gold.

Akhil (21 Nov 2026): "Do back testing now".  The MT5 Strategy Tester cannot run in the build cloud (Windows
desktop app), so this replays the EA's own rules in Python on the same free hourly data:
  - the 13 strategies' setups, fills and exits come from the research functions that tests/test_mix_port.py
    proves identical to the MQL5 port (fresh / QM / EMA9 + the EA's own EA+MSNR H1 strategy);
  - the EA's own strategy runs with the EA rules (1 position, 3 trades a day, cooldown, 3-loss pause),
    at its own risk input (inp_RiskPct, default 0.75%), tested also at 0.25%;
  - mix trades: 0.25% risk (inp_MixRiskPct), x1.5 after that strategy's last trade won, x0.75 after a loss;
  - open-risk cap 3% of equity for mix trades (inp_MixMaxOpenRiskPct): a new trade that would push the
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


def portfolio(trades: pd.DataFrame, fr, ea_risk: float, mix_risk: float = 0.0025, cap: float = 0.03,
              news_block_h: float = 2.0) -> pd.DataFrame:
    atr_by_tf = {tf: pd.Series(e.g.atr(x), index=x.index + pd.Timedelta(tf)) for tf, x in fr.items()}
    ev = ml.events_utc().values
    t = trades.sort_values("t_in").reset_index(drop=True)
    open_pos: list[dict] = []
    last_r: dict[str, float] = {}
    closed_day: dict = {}
    out = []
    eq = START
    for _, row in t.iterrows():
        # close everything that ended before this entry (realise P&L, update streaks)
        still = []
        for p in sorted(open_pos, key=lambda z: z["t_out"]):
            if p["t_out"] <= row.t_in:
                eq += p["pnl"]
                last_r[p["strategy"]] = p["r"]
                dd = p["t_out"].normalize()
                closed_day[dd] = closed_day.get(dd, 0.0) + p["pnl"]
            else:
                still.append(p)
        open_pos = still
        # news blackout
        ti = np.datetime64(row.t_in)
        j = np.searchsorted(ev, ti)
        gap = min(abs((ev[min(j, len(ev) - 1)] - ti) / np.timedelta64(1, "h")),
                  abs((ti - ev[max(j - 1, 0)]) / np.timedelta64(1, "h")))
        if gap <= news_block_h:
            continue
        # EA daily stop 4%
        if closed_day.get(row.t_in.normalize(), 0.0) <= -0.04 * START:
            continue
        is_ea = row.strategy.startswith("EA+MSNR")
        base = ea_risk if is_ea else mix_risk
        lr = last_r.get(row.strategy, 0.0)
        mult = 1.5 if lr > 0.05 else (0.75 if lr < -0.05 else 1.0)
        target = START * base * mult                   # funded account: payouts reset it to $10K, so no compounding
        dist = stop_dist(row.strategy, row, atr_by_tf)
        lot = np.floor(target / (dist * USD_PER_LOT_PER_DOLLAR) / 0.01) * 0.01
        if lot < 0.01:
            if 0.01 * dist * USD_PER_LOT_PER_DOLLAR <= 1.5 * target:
                lot = 0.01
            else:
                continue
        risk_usd = lot * dist * USD_PER_LOT_PER_DOLLAR
        if not is_ea:
            open_mix = sum(p["risk"] for p in open_pos if not p["is_ea"])
            if open_mix + risk_usd > cap * START:
                continue
        pnl = row.r * risk_usd
        rec = dict(t_in=row.t_in, t_out=row.t_out, strategy=row.strategy, side=row.side, r=row.r,
                   lot=round(lot, 2), risk=risk_usd, pnl=pnl, is_ea=is_ea)
        open_pos.append(rec)
        out.append(rec)
    return pd.DataFrame(out)


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

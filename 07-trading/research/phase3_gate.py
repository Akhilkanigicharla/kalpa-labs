"""A317: Akhil's "Phase 3 Market Intelligence Layer" gate, measured on 2 years of gold (21 Nov 2026).

Source: Akhil's upload "Phase3_Intelligence_Design.md". Implements the layer-level validity gate
(entry_environment_ok) and reports how often it is open in London/NY hours, and what it does to the
118 signals of the loose A315 version (research/ea_design_gold.py).
Pip = $1 (the reading that fits the doc's ATR numbers: "calm M15 ATR 8-12 pips, events 40-80").
Gate = all of: regime (persistence-confirmed) not RANGING/UNKNOWN; H1 trend set and equal to regime
direction; volatility not TOO_QUIET (< 5) or NEWS_SPIKE (> 40 or last range > 2.5 ATR); liquidity
score >= 0.50; H4 and H1 swing structure agree (min swing H4 150, H1 60).
Approximations: M15 ATR ~ H1 ATR / 2 (sqrt of 4 bars); sweep bonus not counted (needs M15 history).
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ea_design_gold as e  # noqa: E402
import gold_ema9_msnr as g  # noqa: E402


def structure(d, min_size):
    hi, lo = e.pivots(d, 2, min_size=min_size)
    ph, ch = e._last_two(hi, len(d))
    pl, cl = e._last_two(lo, len(d))
    return pd.Series(np.where((ch > ph) & (cl > pl), 1, np.where((ch < ph) & (cl < pl), -1, 0)), index=d.index)


def regime_raw(h4):
    e50, e200 = g.ema(h4.close, 50), g.ema(h4.close, 200)
    at = pd.Series(g.atr(h4), index=h4.index)
    ratio = at / at.rolling(20).mean()
    slope = e50.diff().rolling(3).mean()
    st = structure(h4, 150)
    inside = ((h4.high <= h4.high.shift()) & (h4.low >= h4.low.shift())).rolling(5).sum()
    hr = h4.index.hour
    sess = ((hr >= 7) & (hr < 17)).astype(int)
    side = np.where(h4.close > e200 + 50, 1, np.where(h4.close < e200 - 50, -1, 0))
    score = ((slope.abs() > 2).astype(int) + (side != 0).astype(int) + (ratio > 1.1).astype(int)
             + (st != 0).astype(int) + (inside <= 1).astype(int) + sess
             - 2 * (st == 0).astype(int) - (ratio < 0.8).astype(int) - ((h4.close - e200).abs() < 50).astype(int))
    dirn = np.sign(slope).fillna(0).astype(int)
    return pd.DataFrame(dict(score=score.clip(lower=0), dirn=dirn, st=st), index=h4.index)


def persist(raw: pd.DataFrame) -> pd.Series:
    """Confirmed regime: +1/-1 trending (weak or strong), 0 ranging. RANGING -> TRENDING needs 2 bars
    score >= 4 same direction; TRENDING -> RANGING needs 3 bars score < 3 (TRANSITIONING in between
    still counts as not ranging for the gate); no direct bull <-> bear flip."""
    out, cur, strong, weak = [], 0, 0, 0
    for s, d in zip(raw.score.values, raw.dirn.values):
        if cur == 0:
            strong = strong + 1 if (s >= 4 and d != 0 and (strong == 0 or d == last_d)) else (1 if s >= 4 and d else 0)
            last_d = d
            if strong >= 2:
                cur, weak = int(d), 0
        else:
            weak = weak + 1 if s < 3 else 0
            if weak >= 3:
                cur, strong = 0, 0
        out.append(cur)
    return pd.Series(out, index=raw.index)


def liquidity(h1: pd.DataFrame) -> pd.Series:
    """Score per H1 bar from levels known BEFORE that bar closes (session H/L of the last 5 London and
    NY sessions, previous day H/L, $50 round numbers, H1 swing pools)."""
    c = h1.close.values
    day = pd.Series(h1.index.normalize(), index=h1.index)
    dh = h1.high.groupby(day).max().shift(1)
    dl = h1.low.groupby(day).min().shift(1)
    pdh, pdl = day.map(dh).values, day.map(dl).values
    hr = h1.index.hour
    sess_levels: list[float] = []
    hi, lo = e.pivots(h1, 2, min_size=60)
    pools = sorted(hi + lo)
    j, active_pools = 0, []
    score = np.ones(len(h1))
    cur_sess, s_hi, s_lo = None, -np.inf, np.inf
    for t in range(len(h1)):
        s = "L" if 7 <= hr[t] < 12 else ("N" if 13 <= hr[t] < 17 else None)
        if s != cur_sess:
            if cur_sess and np.isfinite(s_hi):
                sess_levels = (sess_levels + [s_hi, s_lo])[-20:]
            cur_sess, s_hi, s_lo = s, -np.inf, np.inf
        while j < len(pools) and pools[j][0] <= t:
            active_pools = (active_pools + [pools[j][1]])[-10:]
            j += 1
        sc = 1.0
        if any(abs(c[t] - x) <= 15 for x in sess_levels):
            sc -= 0.25
        if any(abs(c[t] - x) <= 20 for x in active_pools):
            sc -= 0.25
        if abs(c[t] - round(c[t] / 50) * 50) <= 25:            # always true when 1 pip = $1
            sc -= 0.25
        if np.isfinite(pdh[t]) and (abs(c[t] - pdh[t]) <= 10 or abs(c[t] - pdl[t]) <= 10):
            sc -= 0.25
        score[t] = max(0.0, sc)
        if s:
            s_hi, s_lo = max(s_hi, h1.high.iloc[t]), min(s_lo, h1.low.iloc[t])
    return pd.Series(score, index=h1.index)


def gate(h1: pd.DataFrame) -> pd.DataFrame:
    h4 = e.resample(h1, "4h")
    raw = regime_raw(h4)
    reg = persist(raw)
    e.SCALED = False
    h1f = e.h1_features(h1)
    cross = (np.sign(g.ema(h1.close, 20) - g.ema(h1.close, 50)).diff().abs() > 0).rolling(3).sum() > 0
    trend = pd.Series(np.where(cross, 0, h1f.trend.values), index=h1.index)
    at15 = pd.Series(g.atr(h1), index=h1.index) / 2.0
    rng15 = (h1.high - h1.low) / 2.0
    vol_ok = (at15 >= 5) & (at15 <= 40) & (rng15 <= 2.5 * at15)
    liq = liquidity(h1)
    st1 = structure(h1, 60)
    close_t = h1.index + pd.Timedelta("1h")
    a4 = e.align(close_t, pd.DataFrame(dict(reg=reg, st4=raw.st), index=h4.index), pd.Timedelta("4h"))
    df = pd.DataFrame(dict(reg=a4.reg.fillna(0).values, st4=a4.st4.fillna(0).values, trend=trend.values,
                           vol_ok=vol_ok.values, liq=liq.values, st1=st1.values), index=h1.index)
    df["ok_regime"] = df.reg != 0
    df["ok_trend"] = (df.trend != 0) & (df.trend == df.reg)
    df["ok_liq"] = df.liq >= 0.5
    df["ok_struct"] = (df.st4 != 0) & (df.st4 == df.st1)
    df["gate"] = df.ok_regime & df.ok_trend & df.vol_ok & df.ok_liq & df.ok_struct
    df["session"] = [e.in_session(t) for t in close_t]
    return df


def main() -> int:
    import yfinance as yf
    h1 = e._ohlc(yf.download("GC=F", period="730d", interval="1h", progress=False, auto_adjust=False))
    df = gate(h1)
    s = df[df.session]
    steps, keep = {}, pd.Series(True, index=s.index)
    for k in ("ok_regime", "ok_trend", "vol_ok", "ok_liq", "ok_struct"):
        keep &= s[k]
        steps[k] = dict(alone=round(float(s[k].mean()), 3), cumulative=round(float(keep.mean()), 4), bars=int(keep.sum()))
    t = e.ladder_run(h1)["doc_exits"]
    sig_bar = t.t_in.dt.floor("h") - pd.Timedelta("1h")
    ok = df.gate.reindex(sig_bar).fillna(False).values
    kept, dropped = t[ok], t[~ok]
    out = dict(generated=str(date.today()), session_bars=int(len(s)), gate_open_share=round(float(s.gate.mean()), 4),
               gate_open_bars=int(s.gate.sum()), funnel=steps,
               liquidity_round_number_always_hit=bool((df.liq <= 0.75).all()),
               on_a315_signals=dict(total=len(t), kept=len(kept),
                                    kept_avg_r=round(float(kept.r.mean()), 3) if len(kept) else None,
                                    dropped_avg_r=round(float(dropped.r.mean()), 3) if len(dropped) else None,
                                    kept_total_r=round(float(kept.r.sum()), 1) if len(kept) else 0.0))
    Path("reports").mkdir(exist_ok=True)
    (Path("reports") / f"phase3-gate-{date.today()}.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

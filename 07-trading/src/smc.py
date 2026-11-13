"""Smart-money concepts, Fibonacci and martingale, tested honestly (Akhil, 13 Nov 2026).

Detectors (each zone is "known" only at the close of the bar that completes it; no look-ahead):
  fvg           Fair value gap. Bullish: low[i] > high[i-2] -> zone [high[i-2], low[i]], known at i.
  order_block   Bullish: the last down candle before a displacement candle (range >= 1.5 x ATR14,
                closing above the prior 10-bar high) -> zone = that candle's [low, high], known at
                the displacement bar.
  fib           After a confirmed swing low -> swing high (5-bar pivots, confirmed 5 bars later),
                buy zone = 61.8%-50% retracement, stop just under 78.6%.
Trade rule (same for all): a limit order at the zone top, valid `wait` bars; stop = zone bottom
(minus a 10% buffer of the zone) except fib (78.6%); target = 2R; time exit after `hold` bars.
Stop counted first when a bar touches both. Long only on daily (no overnight shorts in Indian
cash); costs charged per round trip.

Placebo control (the method from the TradingView FVG/OB studies): every real zone gets a twin of
the same height and the same distance below price, placed at a random bar with no signal. If
real zones do not beat their twins, the pattern itself carries no information.

Martingale: replays a trade sequence with doubling after each loss (capped by the account) vs a
fixed 1% risk, and reports ruin by Monte Carlo reshuffles. Research only. Not investment advice.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Zone:
    known_at: int        # bar index whose close makes the zone known
    top: float
    bottom: float
    stop: float
    kind: str


def _ohlc(df: pd.DataFrame) -> pd.DataFrame:
    d = df.rename(columns=str.lower)[["open", "high", "low", "close"]].astype(float)
    return d.dropna()


def atr(d: pd.DataFrame, n: int = 14) -> pd.Series:
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def fvg(df: pd.DataFrame) -> list[Zone]:
    d = _ohlc(df)
    h, lo = d.high.values, d.low.values
    out = []
    for i in range(2, len(d)):
        if lo[i] > h[i - 2]:
            top, bot = lo[i], h[i - 2]
            out.append(Zone(i, top, bot, bot - 0.1 * (top - bot), "fvg"))
    return out


def order_blocks(df: pd.DataFrame, k: float = 1.5, look: int = 10) -> list[Zone]:
    d = _ohlc(df)
    a = atr(d).values
    o, h, lo, c = d.open.values, d.high.values, d.low.values, d.close.values
    out = []
    for i in range(look + 14, len(d)):
        if not np.isfinite(a[i - 1]):
            continue
        displacement = (h[i] - lo[i]) >= k * a[i - 1] and c[i] > o[i] and c[i] > h[i - look:i].max()
        if not displacement:
            continue
        for j in range(i - 1, max(i - 6, 0), -1):        # last down candle before the move
            if c[j] < o[j]:
                top, bot = h[j], lo[j]
                out.append(Zone(i, top, bot, bot - 0.1 * (top - bot), "ob"))
                break
    return out


def swings(d: pd.DataFrame, k: int = 5) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Pivot highs/lows as (pivot_bar, confirmed_bar): a pivot is only known k bars later."""
    h, lo = d.high.values, d.low.values
    hi_p, lo_p = [], []
    for i in range(k, len(d) - k):
        if h[i] == h[i - k:i + k + 1].max():
            hi_p.append((i, i + k))
        if lo[i] == lo[i - k:i + k + 1].min():
            lo_p.append((i, i + k))
    return hi_p, lo_p


def fib(df: pd.DataFrame, k: int = 5) -> list[Zone]:
    d = _ohlc(df)
    hi_p, lo_p = swings(d, k)
    out = []
    li = 0
    for ph, conf in hi_p:
        lows_before = [p for p in lo_p if p[0] < ph and p[1] <= conf]
        if not lows_before:
            continue
        pl = lows_before[-1][0]
        top_px, bot_px = d.high.values[ph], d.low.values[pl]
        rng = top_px - bot_px
        if rng <= 0:
            continue
        z_top, z_bot = top_px - 0.5 * rng, top_px - 0.618 * rng
        out.append(Zone(conf, z_top, z_bot, top_px - 0.786 * rng, "fib"))
        li += 1
    return out


def simulate(df: pd.DataFrame, zones: list[Zone], *, wait: int = 10, hold: int = 20, rr: float = 2.0,
             cost: float = 0.0025, one_at_a_time: bool = True) -> pd.DataFrame:
    """Long trades from zones. Returns one row per filled trade with R multiple after costs."""
    d = _ohlc(df)
    h, lo, c, o = d.high.values, d.low.values, d.close.values, d.open.values
    rows, busy_until = [], -1
    for z in sorted(zones, key=lambda z: z.known_at):
        if one_at_a_time and z.known_at <= busy_until:
            continue
        risk = z.top - z.stop
        if risk <= 0 or z.top <= 0:
            continue
        entry_bar = None
        for i in range(z.known_at + 1, min(z.known_at + 1 + wait, len(d))):
            if lo[i] <= z.top:
                entry_bar, px = i, min(z.top, o[i])         # gap down through the level fills at the open
                break
        if entry_bar is None:
            continue
        stop, target = z.stop, px + rr * (px - z.stop)
        if px <= stop:
            continue
        exit_px, reason, ex = None, None, None
        for i in range(entry_bar, min(entry_bar + hold, len(d))):
            if lo[i] <= stop:
                exit_px, reason, ex = min(stop, o[i]) if i > entry_bar else stop, "stop", i
                break
            if h[i] >= target and i > entry_bar or (i == entry_bar and c[i] >= target):
                exit_px, reason, ex = max(target, o[i]) if i > entry_bar else target, "target", i
                break
        if exit_px is None:
            ex = min(entry_bar + hold, len(d)) - 1
            exit_px, reason = c[ex], "time"
        ret = exit_px / px - 1 - cost
        rows.append({"kind": z.kind, "known_at": z.known_at, "entry_bar": entry_bar, "exit_bar": ex, "entry": px,
                     "exit": exit_px, "reason": reason, "ret": ret, "r": ret * px / (px - stop)})
        busy_until = ex
    return pd.DataFrame(rows)


def placebo(df: pd.DataFrame, zones: list[Zone], seed: int = 0) -> list[Zone]:
    """Same-height, same-distance zones at random bars that carry no real signal."""
    d = _ohlc(df)
    c = d.close.values
    rng = np.random.default_rng(seed)
    real = {z.known_at for z in zones}
    pool = np.array([i for i in range(30, len(d) - 30) if i not in real])
    out = []
    for z in zones:
        if not len(pool):
            break
        j = int(rng.choice(pool))
        base = c[z.known_at]
        top_rel, bot_rel, stop_rel = (z.top - base) / base, (z.bottom - base) / base, (z.stop - base) / base
        out.append(Zone(j, c[j] * (1 + top_rel), c[j] * (1 + bot_rel), c[j] * (1 + stop_rel), z.kind + "_placebo"))
    return out


def summarize(t: pd.DataFrame) -> dict:
    if t.empty:
        return {"trades": 0, "win": 0.0, "avg_ret": 0.0, "avg_r": 0.0, "pf": 0.0}
    g, l_ = t.ret[t.ret > 0].sum(), -t.ret[t.ret <= 0].sum()
    return {"trades": len(t), "win": float((t.ret > 0).mean()), "avg_ret": float(t.ret.mean()),
            "avg_r": float(t.r.mean()), "pf": float(g / l_) if l_ > 0 else float("inf")}


def martingale(rets: np.ndarray, *, start: float = 100_000.0, base_risk: float = 0.01, mult: float = 2.0,
               max_steps: int = 10) -> tuple[np.ndarray, bool]:
    """Equity path when risk doubles after each loss (reset after a win). Ruin = equity <= 10% of start
    or a bet that the account cannot cover. rets are per-trade R multiples (loss ~ -1R)."""
    eq, risk, eqs, steps = start, base_risk, [start], 0
    for r in rets:
        stake = eq * risk
        if stake > eq or eq <= 0.1 * start:
            return np.array(eqs), True
        eq += stake * r
        eqs.append(eq)
        if r < 0:
            steps += 1
            risk = min(base_risk * mult ** steps, 1.0) if steps <= max_steps else risk
        else:
            steps, risk = 0, base_risk
    return np.array(eqs), eq <= 0.1 * start


def fixed_fraction(rets: np.ndarray, *, start: float = 100_000.0, risk: float = 0.01) -> np.ndarray:
    eq, eqs = start, [start]
    for r in rets:
        eq += eq * risk * r
        eqs.append(eq)
    return np.array(eqs)


def ruin_odds(rets: np.ndarray, n_paths: int = 2000, seed: int = 0, **kw) -> dict:
    """Reshuffle the same trades many times: how often does each sizing rule blow up?"""
    rng = np.random.default_rng(seed)
    m_ruin, m_final, f_final, f_dd = 0, [], [], []
    for _ in range(n_paths):
        x = rng.permutation(rets)
        mp, ruined = martingale(x, **kw)
        m_ruin += ruined
        m_final.append(mp[-1] / mp[0])
        fp = fixed_fraction(x)
        f_final.append(fp[-1] / fp[0])
        f_dd.append(float((fp / np.maximum.accumulate(fp) - 1).min()))
    return {"martingale_ruin": m_ruin / n_paths, "martingale_median": float(np.median(m_final)),
            "fixed_median": float(np.median(f_final)), "fixed_worst_dd_median": float(np.median(f_dd)),
            "fixed_below_start": float(np.mean(np.array(f_final) < 1))}

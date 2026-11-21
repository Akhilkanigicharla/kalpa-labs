"""A315: Akhil's "XAUUSD Institutional EA" design (The5%ers High Stakes), backtested as written.

Source: Akhil's upload 21 Nov 2026, "XAUUSD Institutional EA - Full Architecture Design" (sections 1-9,
text cut off inside section 9). Rules implemented (doc section in brackets):
  H4 regime score >= 3 with direction (5): EMA50 slope, side of EMA200, ATR expansion, swing structure,
     inside bars, H1 ATR proxy; -2 mixed structure, -1 ATR contracting, -1 within $30 of EMA200.
  H1 trend (5): EMA20 vs EMA50, close beyond EMA20, last 2 swing lows higher (highs lower),
     no opposite engulfing in last 3 H1 bars; must agree with H4.
  M15 setup (5): close within $15 of EMA20, not overextended (> $30), rejection candle (hammer / pin /
     engulfing), ATR14 between $8 and $35, no bar range > $40 in last 3, no H1 swing high/low within $30.
  M5 trigger (5): within 30 min, an M5 close beyond the rejection candle's high/low with body > 50%.
  Stop (4A): 1.5 x ATR(M15) beyond the swing, min $30, skip if > $80.  Pip = $1 (the only reading
     that fits the doc's ATR, stop and swing numbers at today's gold price).
  Management (9): 50% off at 1.5R and stop to breakeven + $0.20; rest trails 0.75 x ATR(M15); TP2 2.5R.
  Guards (4, 8): London 07:30-12:00 + NY 13:00-17:00 GMT entries, no Friday entries after 20:00,
     1 position, max 3 trades/day, 15-min cooldown, 3 losses in a row -> 1 hour pause,
     own daily stop -3%, EA floor at $9,100.  Not testable without data: spread and news guards
     (cost of $0.40 per round trip is charged instead).
Prop rules used (checked 21 Nov 2026): The5%ers High Stakes $10K, 5% daily loss = terminate (the doc
says "no daily DD", which is wrong), 10% max loss, step 1 target 8% (doc: 10%), step 2 5%.
Variant A = M15/M5 on 60 days of free 5-minute data.  Variant B = setup and trigger on H1, 2 years.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gold_ema9_msnr as g  # noqa: E402

COST = 0.40
RISK_PCT = 0.0075
START_BAL = 10_000.0
SESSIONS = [(7.5, 12.0), (13.0, 17.0)]
DROP: set = set()   # ablation only: {"rejection", "room", "h1", "pullback"}
SCALED = False       # True: every $ number in the doc becomes ATR multiples, using the doc's own
                     # "normal" M15 ATR of ~$12 as 1x ($15 -> 1.25 ATR, $30 -> 2.5 ATR, $80 -> 6.7 ATR).
                     # Decided before seeing results; no other settings were tried.


def _ohlc(x):
    x = x.copy()
    x.columns = [c[0] if isinstance(c, tuple) else c for c in x.columns]
    x = g.clean(x)
    x.index = (x.index.tz_convert("UTC") if x.index.tz is not None else x.index).tz_localize(None)
    return x


def resample(d, rule):
    return d.resample(rule, label="left", closed="left").agg(
        dict(open="first", high="max", low="min", close="last")).dropna()


def pivots(d, k=2, min_size=0.0):
    """Confirmed swing highs/lows (k bars each side); known k bars after the pivot."""
    h, lo = d.high.values, d.low.values
    hi_k, lo_k = [], []
    for i in range(k, len(d) - k):
        if h[i] == h[i - k:i + k + 1].max():
            hi_k.append((i + k, h[i]))
        if lo[i] == lo[i - k:i + k + 1].min():
            lo_k.append((i + k, lo[i]))
    if min_size:
        hi_k = [p for p in hi_k if any(abs(p[1] - q[1]) >= min_size for q in lo_k if q[0] <= p[0])]
        lo_k = [p for p in lo_k if any(abs(p[1] - q[1]) >= min_size for q in hi_k if q[0] <= p[0])]
    return hi_k, lo_k


def _last_two(piv, n):
    """For each bar t: the last two confirmed pivot prices known at t (nan if fewer)."""
    a, b = np.full(n, np.nan), np.full(n, np.nan)
    j, prev, cur = 0, np.nan, np.nan
    for t in range(n):
        while j < len(piv) and piv[j][0] <= t:
            prev, cur = cur, piv[j][1]
            j += 1
        a[t], b[t] = prev, cur
    return a, b


def h4_features(h4, h1):
    e50, e200 = g.ema(h4.close, 50), g.ema(h4.close, 200)
    at = pd.Series(g.atr(h4), index=h4.index)
    slope = e50.diff().rolling(3).mean()
    hi, lo = pivots(h4, 2)
    ph, ch = _last_two(hi, len(h4))
    pl, cl = _last_two(lo, len(h4))
    up_s = (ch > ph) & (cl > pl)
    dn_s = (ch < ph) & (cl < pl)
    mixed = ~(up_s | dn_s)
    inside = ((h4.high <= h4.high.shift()) & (h4.low >= h4.low.shift())).rolling(5).sum()
    h1_atr = pd.Series(g.atr(h1), index=h1.index)
    h1x = (h1_atr > 1.0 * h1_atr.rolling(20).mean()).reindex(h4.index, method="ffill").fillna(False)
    exp = at > 1.1 * at.rolling(20).mean()
    contr = at < at.rolling(20).mean()
    bull = (slope > 0) & (h4.close > e200)
    bear = (slope < 0) & (h4.close < e200)
    u4 = at / 50.0 if SCALED else 1.0                    # doc-typical H4 ATR ~ $50
    score = ((slope.abs() > 2 * u4).astype(int) + (bull | bear).astype(int) + exp.astype(int)
             + (up_s | dn_s).astype(int) + (inside <= 1).astype(int) + h1x.astype(int)
             - 2 * mixed.astype(int) - contr.astype(int) - ((h4.close - e200).abs() < 30 * u4).astype(int))
    dirn = np.where(bull & up_s, 1, np.where(bear & dn_s, -1, 0))
    dirn = np.where(score >= 3, dirn, 0)
    return pd.DataFrame(dict(regime=dirn, score=score), index=h4.index)


def h1_features(h1):
    e20, e50 = g.ema(h1.close, 20), g.ema(h1.close, 50)
    hi, lo = pivots(h1, 2, min_size=0 if SCALED else 60)   # scaled: swing size via 2-bar pivots only
    ph, ch = _last_two(hi, len(h1))
    pl, cl = _last_two(lo, len(h1))
    o, c = h1.open, h1.close
    bear_eng = (c < o) & (c.shift() > o.shift()) & (c < o.shift()) & (o > c.shift())
    bull_eng = (c > o) & (c.shift() < o.shift()) & (c > o.shift()) & (o < c.shift())
    up = (e20 > e50) & (c > e20) & (cl > pl) & (bear_eng.rolling(3).sum() == 0)
    dn = (e20 < e50) & (c < e20) & (ch < ph) & (bull_eng.rolling(3).sum() == 0)
    return pd.DataFrame(dict(trend=np.where(up, 1, np.where(dn, -1, 0)), last_hi=ch, last_lo=cl), index=h1.index)


def align(lower_close_times, higher: pd.DataFrame, tf: pd.Timedelta):
    """Values of the last HIGHER bar that has closed by each lower bar's close (no look-ahead)."""
    hv = higher.copy()
    hv["t_close"] = hv.index + tf
    lv = pd.DataFrame({"t": lower_close_times})
    m = pd.merge_asof(lv, hv.sort_values("t_close"), left_on="t", right_on="t_close", direction="backward")
    return m.drop(columns=["t", "t_close"])


def in_session(ts):
    hr = ts.hour + ts.minute / 60
    if ts.weekday() >= 5 or (ts.weekday() == 4 and hr >= 20):
        return False
    return any(a <= hr < b for a, b in SESSIONS)


def setups(s: pd.DataFrame, s_tf, h1f, h4f):
    """Setup bars on the setup timeframe (M15 in A, H1 in B)."""
    e20 = g.ema(s.close, 20)
    at = pd.Series(g.atr(s), index=s.index)
    o, h, lo, c = s.open, s.high, s.low, s.close
    rng = (h - lo).replace(0, np.nan)
    body = (c - o).abs()
    lower_w = np.minimum(o, c) - lo
    upper_w = h - np.maximum(o, c)
    bull_rej = ((lower_w >= 2 * body) & (upper_w <= body)) | ((c > o) & (c.shift() < o.shift()) & (c > o.shift()) & (o <= c.shift()))
    bear_rej = ((upper_w >= 2 * body) & (lower_w <= body)) | ((c < o) & (c.shift() > o.shift()) & (c < o.shift()) & (o >= c.shift()))
    spike = (h - lo).rolling(3).max() > 40
    avg_at = at.rolling(100, min_periods=20).mean()
    close_t = s.index + s_tf
    a1 = align(close_t, h1f, pd.Timedelta("1h"))
    a4 = align(close_t, h4f, pd.Timedelta("4h"))
    out = []
    for i in range(len(s)):
        if not in_session(close_t[i]) or not np.isfinite(at.iloc[i]):
            continue
        reg, tr = a4.regime.iloc[i], a1.trend.iloc[i]
        if "h1" in DROP:
            tr = reg
        if not reg or reg != tr:
            continue
        u = at.iloc[i] / 12.0 if SCALED else 1.0         # $ -> ATR scaling
        if SCALED:
            ok_vol = 0.67 * avg_at.iloc[i] <= at.iloc[i] <= 2.9 * avg_at.iloc[i]
            spk = (h - lo).iloc[max(0, i - 2):i + 1].max() > 40 * u
        else:
            ok_vol, spk = 8 <= at.iloc[i] <= 35, spike.iloc[i]
        if not ok_vol or spk:
            continue
        dist = (c.iloc[i] - e20.iloc[i]) * reg
        if "pullback" not in DROP and abs(c.iloc[i] - e20.iloc[i]) > 15 * u:
            continue
        if dist > 30 * u:
            continue
        rej_ok = "rejection" in DROP or (bull_rej.iloc[i] if reg == 1 else bear_rej.iloc[i])
        room = (a1.last_hi.iloc[i] - c.iloc[i]) if reg == 1 else (c.iloc[i] - a1.last_lo.iloc[i])
        room_ok = "room" in DROP or not (room < 30 * u)
        if not (rej_ok and room_ok):
            continue
        out.append(dict(t_close=close_t[i], side=int(reg), trig=float(h.iloc[i] if reg == 1 else lo.iloc[i]),
                        swing=float(lo.iloc[i] if reg == 1 else h.iloc[i]), atr=float(at.iloc[i])))
    return out


def simulate(x: pd.DataFrame, x_tf, sets, trig_window: pd.Timedelta, rule="the5ers"):
    """Trigger + trade management + all guards on the trigger timeframe (M5 in A, H1 in B)."""
    o, h, lo, c = (x[k].values for k in ("open", "high", "low", "close"))
    close_t = x.index + x_tf
    pos = np.searchsorted(close_t.values, np.array([s["t_close"] for s in sets], dtype="datetime64[ns]"))
    trades, bal = [], START_BAL
    busy_until, cool_until, pause_until = pd.Timestamp(0), pd.Timestamp(0), pd.Timestamp(0)
    day_trades, day_pnl, loss_streak, cur_day, halted = {}, {}, 0, None, False
    for s, p0 in zip(sets, pos):
        if halted:
            break
        t0 = s["t_close"]
        if t0 < max(busy_until, cool_until, pause_until):
            continue
        d = t0.date()
        if day_trades.get(d, 0) >= 3 or day_pnl.get(d, 0) <= -0.03 * START_BAL:
            continue
        side, entry_i = s["side"], None
        for i in range(p0, len(x)):
            if close_t[i] - t0 > trig_window:
                break
            if close_t[i] <= t0:
                continue
            body_ok = abs(c[i] - o[i]) > 0.5 * (h[i] - lo[i]) if h[i] > lo[i] else False
            if body_ok and ((side == 1 and c[i] > s["trig"]) or (side == -1 and c[i] < s["trig"])):
                entry_i = i + 1
                break
        if entry_i is None or entry_i >= len(x):
            continue
        en = o[entry_i]
        u = s["atr"] / 12.0 if SCALED else 1.0
        sl_dist = max(1.5 * s["atr"], abs(en - s["swing"]) + 0.25 * s["atr"], 30.0 * u)
        if sl_dist > 80 * u:
            continue
        risk_usd = bal * RISK_PCT
        size = risk_usd / sl_dist                          # $ per $1 move
        if LADDER:
            leg = size / 3                                 # 3 trades x 0.25% risk
            lp, k, hits = ladder_exit(o, h, lo, c, close_t, entry_i, side, en, sl_dist, s["atr"])
            pnl = lp * leg - 3 * COST * leg
            bal += pnl
            t_out = close_t[k]
            trades.append(dict(t_in=x.index[entry_i], t_out=t_out, side=side, r=pnl / risk_usd, pnl=pnl, bal=bal,
                               entry=en, stop=en - side * sl_dist, legs_hit=hits))
            day_trades[d] = day_trades.get(d, 0) + 1
            day_pnl[d] = day_pnl.get(d, 0) + pnl
            loss_streak = loss_streak + 1 if pnl < 0 else 0
            busy_until, cool_until = t_out, t_out + pd.Timedelta("15min")
            if loss_streak >= 3:
                pause_until, loss_streak = t_out + pd.Timedelta("1h"), 0
            if bal <= 9_100:
                halted = True
            continue
        tp2_d = 2.5 * sl_dist
        if "tp2_level" in s:                                # A320 MSNR target: next opposite level
            tp2_d = (s["tp2_level"] - en) * side - 0.1 * s["atr"]
            if tp2_d < 1.5 * sl_dist:
                continue                                    # no room to the next level
        st, tp1, tp2 = en - side * sl_dist, en + side * 1.5 * sl_dist, en + side * tp2_d
        half_done, pnl, k, trail = False, 0.0, entry_i, None
        for k in range(entry_i, len(x)):
            if side == 1:
                if lo[k] <= st:
                    pnl += (st - en) * size * (0.5 if half_done else 1.0)
                    break
                if not half_done and h[k] >= tp1:
                    pnl += (tp1 - en) * size * 0.5
                    half_done, st = True, en + 0.2
                if half_done:
                    if h[k] >= tp2:
                        pnl += (tp2 - en) * size * 0.5
                        break
                    st = max(st, c[k] - 0.75 * s["atr"])
            else:
                if h[k] >= st:
                    pnl += (en - st) * size * (0.5 if half_done else 1.0)
                    break
                if not half_done and lo[k] <= tp1:
                    pnl += (en - tp1) * size * 0.5
                    half_done, st = True, en - 0.2
                if half_done:
                    if lo[k] <= tp2:
                        pnl += (en - tp2) * size * 0.5
                        break
                    st = min(st, c[k] + 0.75 * s["atr"])
            if (close_t[k] - x.index[entry_i]) > pd.Timedelta("3D"):
                pnl += (c[k] - en) * side * size * (0.5 if half_done else 1.0)
                break
        pnl -= COST * size
        bal += pnl
        t_out = close_t[k]
        trades.append(dict(t_in=x.index[entry_i], t_out=t_out, side=side, r=pnl / risk_usd, pnl=pnl, bal=bal))
        day_trades[d] = day_trades.get(d, 0) + 1
        day_pnl[d] = day_pnl.get(d, 0) + pnl
        loss_streak = loss_streak + 1 if pnl < 0 else 0
        busy_until = t_out
        cool_until = t_out + pd.Timedelta("15min")
        if loss_streak >= 3:
            pause_until, loss_streak = t_out + pd.Timedelta("1h"), 0
        if bal <= 9_100:
            halted = True
    return pd.DataFrame(trades)


LADDER = False        # Akhil 21 Nov: "every opportunity take three trades with stop loss"
LOOSE = {"rejection", "room", "h1", "pullback"}   # the A315 version that trades most (never broke rules)


def ladder_exit(o, h, lo, c, close_t, entry_i, side, en, sl, atr_):
    """3 legs, one stop: targets 1R/2R/3R. Leg 1 hit -> stop to breakeven + $0.20; leg 2 hit -> stop
    to the 1R level. Stop checked first in a bar (worst case). Max hold 3 days. Returns
    (pnl per $1-per-leg size summed over legs, exit index, legs that hit target)."""
    tps = [en + side * k * sl for k in (1, 2, 3)]
    st = en - side * sl
    open_legs, pnl, hits, k = [0, 1, 2], 0.0, 0, entry_i
    for k in range(entry_i, len(o)):
        if (side == 1 and lo[k] <= st) or (side == -1 and h[k] >= st):
            pnl += len(open_legs) * (st - en) * side
            open_legs = []
            break
        for leg in list(open_legs):
            if (side == 1 and h[k] >= tps[leg]) or (side == -1 and lo[k] <= tps[leg]):
                pnl += (tps[leg] - en) * side
                open_legs.remove(leg)
                hits += 1
                if leg == 0:
                    st = en + side * 0.2
                elif leg == 1:
                    st = tps[0]
        if not open_legs:
            break
        if close_t[k] - close_t[entry_i] > pd.Timedelta("3D"):
            pnl += len(open_legs) * (c[k] - en) * side
            open_legs = []
            break
    if open_legs:
        pnl += len(open_legs) * (c[k] - en) * side
    return pnl, k, hits


def prop(trades: pd.DataFrame, target=0.08, daily=0.05, maxloss=0.10, start=None):
    t = trades if start is None else trades[trades.t_in >= start]
    bal, peak_day = START_BAL, {}
    day_start = {}
    for _, x in t.iterrows():
        d = x.t_out.date()
        day_start.setdefault(d, bal)
        bal += x.pnl * (1.0)          # pnl was sized on the running balance already
        if bal <= START_BAL * (1 - maxloss) or bal <= day_start[d] - daily * START_BAL:
            return "fail"
        if bal >= START_BAL * (1 + target):
            return "pass"
    return "running"


def summary(t: pd.DataFrame) -> dict:
    if t.empty:
        return dict(n=0)
    r = t.r.values
    eq = t.bal.values
    days = max((t.t_out.max() - t.t_in.min()).days, 1)
    return dict(n=int(len(r)), per_month=round(len(r) / days * 30, 1), win=round(float((r > 0).mean()), 3),
                avg_r=round(float(r.mean()), 3), total_r=round(float(r.sum()), 1),
                profit_usd=round(float(eq[-1] - START_BAL), 0),
                worst_drop_pct=round(float((1 - eq / np.maximum.accumulate(np.r_[START_BAL, eq])[1:]).max() * 100), 1),
                longs=int((t.side == 1).sum()), shorts=int((t.side == -1).sum()))


def weekly_prop(t: pd.DataFrame, **kw) -> dict:
    if t.empty:
        return {}
    starts = pd.date_range(t.t_in.min().normalize(), t.t_in.max().normalize(), freq="7D")
    res = []
    for s in starts:
        sub = t[t.t_in >= s].copy()
        if sub.empty:
            continue
        sub["pnl"] = sub.r * START_BAL * RISK_PCT          # each attempt starts at $10K
        res.append(prop(sub, **kw))
    n = len(res)
    return dict(starts=n, pass_=round(res.count("pass") / n, 2), fail=round(res.count("fail") / n, 2),
                running=round(res.count("running") / n, 2))


PAPER_START = pd.Timestamp("2026-11-21")


def ladder_run(h1=None):
    """2-year H1 test of the loose A315 version with the 3-trade ladder vs the doc's own exits."""
    global SCALED, DROP, LADDER
    import yfinance as yf
    if h1 is None:
        h1 = _ohlc(yf.download("GC=F", period="730d", interval="1h", progress=False, auto_adjust=False))
    SCALED, DROP = True, set(LOOSE)                    # must be set BEFORE the features are built
    h4 = resample(h1, "4h")
    h4f, h1f = h4_features(h4, h1), h1_features(h1)
    sig = setups(h1, pd.Timedelta("1h"), h1f, h4f)
    res = {}
    for name, lad in (("doc_exits", False), ("three_trades", True)):
        LADDER = lad
        res[name] = simulate(h1, pd.Timedelta("1h"), sig, pd.Timedelta("2h"))
    LADDER = True
    return res


def paper(out: Path, flags: Path | None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    if flags and (flags / "KILL").exists():
        st = dict(status="killed")
    else:
        t = ladder_run()["three_trades"]
        t = t[t.t_in >= PAPER_START] if not t.empty else t
        t.to_csv(out / "ledger.csv", index=False)
        st = dict(status="running", start=str(PAPER_START.date()), rule="3 trades per signal, 0.25% risk each, "
                  "targets 1R/2R/3R, one stop, breakeven after target 1", **summary(t))
        if not t.empty:
            st["the5ers"] = prop(t.assign(pnl=t.r * START_BAL * RISK_PCT))
    (out / "state.json").write_text(json.dumps(st, indent=1, default=str))
    return st


def main() -> int:
    global SCALED
    if "--paper" in sys.argv:
        fl = sys.argv[sys.argv.index("--flags") + 1] if "--flags" in sys.argv else None
        print(json.dumps(paper(Path(sys.argv[sys.argv.index("--paper") + 1]), Path(fl) if fl else None), default=str))
        return 0
    if "--ladder" in sys.argv:
        res = ladder_run()
        split = pd.Timestamp("2025-09-01")
        out = {}
        for k, t in res.items():
            a, b = t[t.t_in < split], t[t.t_in >= split]
            out[k] = dict(**summary(t), early_avg_r=round(float(a.r.mean()), 3), late_avg_r=round(float(b.r.mean()), 3),
                          the5ers_8pct=weekly_prop(t), the5ers_by_month={str(p): int(v) for p, v in t.groupby(t.t_in.dt.to_period("M")).pnl.sum().round(0).items()})
            if "legs_hit" in t:
                out[k]["legs_hit_share"] = {int(i): round(float(v), 2) for i, v in t.legs_hit.value_counts(normalize=True).sort_index().items()}
        (Path("reports") / f"ea-ladder-gold-{date.today()}.json").write_text(json.dumps(out, indent=1, default=str))
        print(json.dumps(out, indent=1, default=str))
        return 0
    SCALED = "--scaled" in sys.argv
    import yfinance as yf
    m5 = _ohlc(yf.download("GC=F", period="60d", interval="5m", progress=False, auto_adjust=False))
    h1 = _ohlc(yf.download("GC=F", period="730d", interval="1h", progress=False, auto_adjust=False))
    h4 = resample(h1, "4h")
    h4f, h1f = h4_features(h4, h1), h1_features(h1)
    m15 = resample(m5, "15min")
    out = dict(generated=str(date.today()), scaled=SCALED)
    sa = setups(m15, pd.Timedelta("15min"), h1f, h4f)
    ta = simulate(m5, pd.Timedelta("5min"), sa, pd.Timedelta("30min"))
    out["A_m15_m5_60days"] = dict(period=f"{m5.index[0].date()} to {m5.index[-1].date()}", setups=len(sa),
                                  **summary(ta), the5ers_step1=weekly_prop(ta))
    sb = setups(h1, pd.Timedelta("1h"), h1f, h4f)
    tb = simulate(h1, pd.Timedelta("1h"), sb, pd.Timedelta("2h"))
    out["B_h1_2years"] = dict(period=f"{h1.index[0].date()} to {h1.index[-1].date()}", setups=len(sb),
                              **summary(tb), the5ers_step1_8pct=weekly_prop(tb),
                              doc_target_10pct=weekly_prop(tb, target=0.10))
    if not tb.empty:
        out["B_by_quarter_r"] = {str(k): round(float(v), 1) for k, v in tb.groupby(tb.t_in.dt.to_period("Q")).r.sum().items()}
    Path("reports").mkdir(exist_ok=True)
    (Path("reports") / f"ea-design-gold{'-scaled' if SCALED else ''}-{date.today()}.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

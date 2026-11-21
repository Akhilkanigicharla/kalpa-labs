"""A320: does adding MSNR to Akhil's The5%ers EA (A315 loose version) make it more profitable?

Akhil (21 Nov 2026): "Fix it and try to include msnr where ever it possible and make this more profitable".

Base = the A315 loose EA on H1 (H4 regime + H1 trend, setup and trigger on H1, doc exits, all guards,
$0.40 cost, The5%ers $10K rules).  MSNR parts that can be bolted on (src/msnr.py rules, levels from
CLOSES, key levels k=2, levels built on H4 and tracked on H1, no look-ahead):
  level    the setup bar's pullback reached an active H4 support (long) / resistance (short):
           low <= level + 0.5 x ATR(H1) and close stayed on the right side
  fresh    that level was fresh (first touch since it formed or flipped)
  story    weekly MSNR storyline agrees with the trade side
  stop     stop beyond the MSNR level (level -/+ 0.25 ATR) instead of beyond the swing
  target   final target = the next opposite H4 level; skip the trade if it is closer than 1.5R

All 32 on/off combinations are run.  Selection uses ONLY the earlier part (before 2025-09-01); the
chosen version is then reported on the later part once.  Random-entry baseline: same number of
trades, same sides, same session hours, same exits, 50 seeds.
Research code only.  Not investment advice.
"""
from __future__ import annotations

import itertools
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ea_design_gold as e  # noqa: E402
from src.msnr import levels, storyline  # noqa: E402

SPLIT = pd.Timestamp("2025-09-01")
PARTS = ("level", "fresh", "story", "stop", "target")
CACHE = Path("/tmp/gc_h1_730d.parquet")


def load_h1() -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    import yfinance as yf
    h1 = e._ohlc(yf.download("GC=F", period="730d", interval="1h", progress=False, auto_adjust=False))
    h1.to_parquet(CACHE)
    return h1


def msnr_state(h1: pd.DataFrame, h4: pd.DataFrame, k: int = 2) -> pd.DataFrame:
    """For every H1 bar (as of its close): nearest active support below / resistance above built from
    H4 key levels known by then, whether each is fresh, and whether this bar touched it."""
    lv = levels(h4, k)
    known_t = np.array([h4.index[x.known_at] + pd.Timedelta("4h") for x in lv], dtype="datetime64[ns]")
    price = np.array([x.price for x in lv])
    role = np.array([1 if x.kind == "V" else -1 for x in lv])          # +1 support, -1 resistance
    fresh = np.ones(len(lv), dtype=bool)
    h, lo, c = h1.high.values, h1.low.values, h1.close.values
    close_t = (h1.index + pd.Timedelta("1h")).values
    out = np.full((len(h1), 6), np.nan)    # sup, sup_fresh_before, sup_touched, res, res_fresh_before, res_touched
    for t in range(len(h1)):
        act = known_t <= close_t[t]
        if not act.any():
            continue
        idx = np.where(act)[0]
        fr_before = fresh[idx].copy()
        r, p = role[idx], price[idx]
        # flips (close through) and touches (wick reaches, close stays)
        flip_dn = (r == 1) & (c[t] < p)
        flip_up = (r == -1) & (c[t] > p)
        touch_s = (r == 1) & ~flip_dn & (lo[t] <= p)
        touch_r = (r == -1) & ~flip_up & (h[t] >= p)
        # nearest support at/under the bar (after this bar's flips) and resistance above
        r_new = r.copy()
        r_new[flip_dn], r_new[flip_up] = -1, 1
        sup = (r_new == 1) & (p <= c[t])
        res = (r_new == -1) & (p >= c[t])
        if sup.any():
            j = np.argmax(np.where(sup, p, -np.inf))
            out[t, 0], out[t, 1], out[t, 2] = p[j], fr_before[j] and not (flip_up[j]), touch_s[j] or flip_up[j]
        if res.any():
            j = np.argmin(np.where(res, p, np.inf))
            out[t, 3], out[t, 4], out[t, 5] = p[j], fr_before[j] and not (flip_dn[j]), touch_r[j] or flip_dn[j]
        role[idx] = r_new
        g = idx[flip_dn | flip_up]
        fresh[g] = True
        fresh[idx[touch_s | touch_r]] = False
    st = pd.DataFrame(out, columns=["sup", "sup_fresh", "sup_touch", "res", "res_fresh", "res_touch"],
                      index=h1.index)
    return st


def weekly_story(h1: pd.DataFrame) -> pd.Series:
    d = e.resample(h1, "1D").dropna()
    s = storyline(d, 2)
    # a day's storyline value is known after that day closes -> shift onto the next day's H1 bars
    s.index = s.index + pd.Timedelta("1D")
    return s.reindex(h1.index, method="ffill").fillna(0)


def apply(sig: list[dict], st: pd.DataFrame, story: pd.Series, at_h1: pd.Series, on: set, h1_index) -> list[dict]:
    pos = h1_index.get_indexer([s["t_close"] - pd.Timedelta("1h") for s in sig])
    out = []
    for s, i in zip(sig, pos):
        if i < 0:
            continue
        row, a = st.iloc[i], at_h1.iloc[i]
        side = s["side"]
        lvl, fr, touched = (row.sup, row.sup_fresh, row.sup_touch) if side == 1 else (row.res, row.res_fresh, row.res_touch)
        opp = row.res if side == 1 else row.sup
        s = dict(s)
        if "level" in on:
            near = np.isfinite(lvl) and (touched or abs(s["swing"] - lvl) <= 0.5 * a)
            if not near:
                continue
        if "fresh" in on and not (np.isfinite(lvl) and fr):
            continue
        if "story" in on and story.iloc[i] * side <= 0:
            continue
        if "stop" in on and np.isfinite(lvl):
            s["swing"] = float(lvl)
        if "target" in on:
            if not np.isfinite(opp):
                continue
            s["tp2_level"] = float(opp)
        out.append(s)
    return out


def placebo(sig, h1, seed):
    """Same count, sides and hours, random H1 bars inside the session; MSNR target kept as distance."""
    rng = np.random.default_rng(seed)
    ses = [t for t in (h1.index + pd.Timedelta("1h")) if e.in_session(t)]
    ses = pd.DatetimeIndex(ses)
    at = pd.Series(e.g.atr(h1), index=h1.index + pd.Timedelta("1h"))
    out = []
    for s in sig:
        t = ses[rng.integers(len(ses))]
        i = h1.index.get_indexer([t - pd.Timedelta("1h")])[0]
        side = s["side"]
        a = float(at.loc[t]) if np.isfinite(at.loc[t]) else s["atr"]
        out.append(dict(t_close=t, side=side, trig=float(h1.high.iloc[i] if side == 1 else h1.low.iloc[i]),
                        swing=float(h1.low.iloc[i] if side == 1 else h1.high.iloc[i]), atr=a,
                        **({"tp2_level": float(h1.close.iloc[i] + side * (s["tp2_level"] - s["trig"]))}
                           if "tp2_level" in s else {})))
    return sorted(out, key=lambda z: z["t_close"])


def run(h1, sig) -> pd.DataFrame:
    return e.simulate(h1, pd.Timedelta("1h"), sig, pd.Timedelta("2h"))


def part(t: pd.DataFrame, early: bool) -> pd.DataFrame:
    if t.empty:
        return t
    return t[t.t_in < SPLIT] if early else t[t.t_in >= SPLIT]


def stat(t):
    return dict(n=int(len(t)), avg_r=round(float(t.r.mean()), 3) if len(t) else None,
                total_r=round(float(t.r.sum()), 1) if len(t) else 0.0)


def main() -> int:
    e.SCALED, e.DROP = True, set(e.LOOSE)
    h1 = load_h1()
    h4 = e.resample(h1, "4h")
    h4f, h1f = e.h4_features(h4, h1), e.h1_features(h1)
    base = e.setups(h1, pd.Timedelta("1h"), h1f, h4f)
    st = msnr_state(h1, h4)
    story = weekly_story(h1)
    at_h1 = pd.Series(e.g.atr(h1), index=h1.index)
    rows, trades = [], {}
    for bits in itertools.product([0, 1], repeat=len(PARTS)):
        on = {p for p, b in zip(PARTS, bits) if b}
        sig = apply(base, st, story, at_h1, on, h1.index)
        t = run(h1, sig)
        key = "+".join(sorted(on)) or "base"
        trades[key] = (sig, t)
        a, b = part(t, True), part(t, False)
        rows.append(dict(version=key, early=stat(a), late=stat(b), all=e.summary(t)))
    # selection on the EARLY part only: highest early total R with >= 20 early trades
    elig = [r for r in rows if r["early"]["n"] >= 20]
    best = max(elig, key=lambda r: r["early"]["total_r"])
    sig, t = trades[best["version"]]
    pl = []
    for sd in range(50):
        pt = run(h1, placebo(sig, h1, sd))
        pl.append(float(pt.r.mean()) if len(pt) else 0.0)
    late = part(t, False)
    pl_late = []
    late_sig = [s for s in sig if s["t_close"] >= SPLIT]
    for sd in range(50):
        pt = run(h1, placebo(late_sig, h1, 100 + sd))
        pl_late.append(float(pt.r.mean()) if len(pt) else 0.0)
    real_late = float(late.r.mean()) if len(late) else 0.0
    rep = dict(generated=str(date.today()), period=f"{h1.index[0].date()} to {h1.index[-1].date()}",
               split=str(SPLIT.date()), versions=sorted(rows, key=lambda r: -r["early"]["total_r"]),
               base=next(r for r in rows if r["version"] == "base"),
               chosen=best["version"], chosen_all=e.summary(t), chosen_late=stat(late),
               random_all_avg_r=round(float(np.mean(pl)), 3),
               random_late_avg_r=round(float(np.mean(pl_late)), 3),
               p_late_vs_random=round(float((np.array(pl_late) >= real_late).mean()), 2),
               the5ers_chosen=e.weekly_prop(t) if len(t) else None,
               the5ers_base=e.weekly_prop(trades["base"][1]))
    Path("reports").mkdir(exist_ok=True)
    (Path("reports") / f"ea-msnr-gold-{date.today()}.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: v for k, v in rep.items() if k != "versions"}, indent=1, default=str))
    print("top 8 by early R:")
    for r in rep["versions"][:8]:
        print(r["version"], r["early"], r["late"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

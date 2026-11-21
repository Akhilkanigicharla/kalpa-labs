"""A314: MSNR + Fair Value Gap + Order Block (+ Fibonacci) on gold 1h/4h, combined into one strategy.

Akhil (21 Nov 2026): "Msnr 1hr and 4hr fix also try adding fair value gap and order block and other
things and take best trades from other and form a new strategy and test it".

Families (long logic; shorts = same logic on the mirrored chart 1/price):
  MSNR: fresh_k2, fresh_k5, qm, eq_sweep, rejection   (src/msnr.py, research/msnr_gold_robust.py)
  SMC:  fvg, ob, fib                                   (src/smc.py)
Signals: each family alone, and every pair "A confirmed by B" = an A zone counts only if a B zone on
the same side was formed in the last N bars (1h: 12, 4h: 6) and overlaps it within 0.5 ATR.
Filters: 9 EMA on/off, weekly storyline on/off.  -> 1,024 configs.

No-cheating protocol (fixed before running):
  SELECT on the earlier data only (Jul 2024 -> 31 Aug 2025): >= 30 trades, avg R >= +0.10 at DOUBLE
  costs, beats matched random entries (bootstrap p < 0.05). Keep the 5 best by (avg R - random).
  NEW STRATEGY = take a trade whenever any of those 5 fires (one position at a time per timeframe).
  TEST once on the later data (1 Sep 2025 -> now), which the selection never saw.
Run: python research/combo_gold.py   -> reports/combo-gold-<date>.json
"""
from __future__ import annotations

import itertools
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src import smc  # noqa: E402
from src.msnr import _gate, mirror, storyline  # noqa: E402
import gold_ema9_msnr as g  # noqa: E402
import msnr_gold_robust as m  # noqa: E402

SPLIT = pd.Timestamp("2025-09-01")
COST = m.COST
CONFIRM_BARS = {"1h": 12, "4h": 6}
FAM = {
    "fresh_k2": lambda d: m.ALL["fresh_v"](d, k=2, storyline_on=False),
    "fresh_k5": lambda d: m.ALL["fresh_v"](d, k=5, storyline_on=False),
    "qm": lambda d: m.ALL["qm"](d, k=2, storyline_on=False),
    "eq_sweep": lambda d: m.ALL["eq_sweep"](d, k=2, storyline_on=False),
    "rejection": lambda d: m.ALL["rejection"](d, k=2, storyline_on=False),
    "fvg": smc.fvg,
    "ob": smc.order_blocks,
    "fib": smc.fib,
}
_D: dict = {}
_Z: dict = {}


def _init():
    data = m.load()
    for tf in ("1h", "4h"):
        _D[(tf, "long")] = data[tf]
        _D[(tf, "short")] = mirror(data[tf])


def zones_job(key):
    tf, side, fam = key
    return key, FAM[fam](_D[(tf, side)])


def confirm(a: list, b: list, d: pd.DataFrame, n: int) -> list:
    """Keep A zones that have a B zone formed within the last n bars overlapping within 0.5 ATR."""
    at = smc.atr(smc._ohlc(d)).values
    bt = np.array([z.known_at for z in b])
    out = []
    for z in a:
        if not np.isfinite(at[z.known_at]):
            continue
        lo, hi = np.searchsorted(bt, z.known_at - n), np.searchsorted(bt, z.known_at, side="right")
        pad = 0.5 * at[z.known_at]
        if any(b[i].bottom <= z.top + pad and b[i].top >= z.bottom - pad for i in range(lo, hi)):
            out.append(z)
    return out


def build(tf, side, sig, ema_on, story_on, zmap):
    d = _D[(tf, side)]
    a, b = sig
    zs = zmap[(tf, side, a)]
    if b:
        zs = confirm(zs, sorted(zmap[(tf, side, b)], key=lambda z: z.known_at), d, CONFIRM_BARS[tf])
    if ema_on:
        e = g.ema(d.close).values
        c = d.close.values
        zs = [z for z in zs if z.known_at > 0 and c[z.known_at] > e[z.known_at] > e[z.known_at - 1]]
    if story_on:
        zs = _gate(zs, storyline(d, 2))
    return zs


def trades(tf, side, zs, cost):
    d = _D[(tf, side)]
    p = m.TF[tf]
    t = smc.simulate(d, zs, wait=p["wait"], hold=p["hold"], rr=2.0, cost=cost)
    if not t.empty:
        t["date"] = d.index[t.entry_bar.values]
        t["tf"], t["side"] = tf, side
    return t


def score(tf, side, zs, part):
    """avg R (2x cost), random-entry avg R and bootstrap p on one part of the data."""
    d = _D[(tf, side)]
    t = trades(tf, side, zs, 2 * COST)
    sel = (lambda x: x[x.date < SPLIT]) if part == "early" else (lambda x: x[x.date >= SPLIT])
    t = sel(t) if not t.empty else t
    if len(t) < 5:
        return dict(n=int(len(t)), r=None, pl=None, p=1.0)
    pl = []
    for s in range(5):
        tp = trades(tf, side, smc.placebo(d, zs, seed=s), 2 * COST)
        tp = sel(tp) if not tp.empty else tp
        if len(tp):
            pl.append(tp.r.mean())
    plm = float(np.mean(pl)) if pl else 0.0
    boot = np.random.default_rng(5).choice(t.r.values, (2000, len(t))).mean(axis=1)
    return dict(n=int(len(t)), r=round(float(t.r.mean()), 3), pl=round(plm, 3), p=round(float(np.mean(boot <= plm)), 4))


def eval_job(arg):
    cfg, zs = arg
    tf, side = cfg[0], cfg[1]
    return dict(cfg=cfg, early=score(tf, side, zs, "early"))


def selected_ok(e: dict) -> bool:
    return e["n"] >= 30 and (e["r"] or -9) >= 0.10 and e["p"] < 0.05


def merge_trades(cfgs, zsets, cost):
    """New strategy: union of the selected setups' zones, one position at a time per timeframe+side."""
    parts = []
    by = {}
    for cfg, zs in zip(cfgs, zsets):
        by.setdefault((cfg[0], cfg[1]), []).extend(zs)
    for (tf, side), zs in by.items():
        uniq = {(z.known_at, round(z.top, 8)): z for z in zs}
        t = trades(tf, side, sorted(uniq.values(), key=lambda z: z.known_at), cost)
        if not t.empty:
            parts.append(t)
    return pd.concat(parts).sort_values("date") if parts else pd.DataFrame()


def main() -> int:
    sigs = [(a, None) for a in FAM] + [(a, b) for a in FAM for b in FAM if a != b]
    zkeys = list(itertools.product(("1h", "4h"), ("long", "short"), FAM))
    with ProcessPoolExecutor(initializer=_init) as ex:
        zmap = dict(ex.map(zones_job, zkeys))
    _init()
    cfgs = list(itertools.product(("1h", "4h"), ("long", "short"), sigs, (True, False), (True, False)))
    jobs = [(c, build(*c, zmap)) for c in cfgs]
    zsets = {c: z for c, z in jobs}
    with ProcessPoolExecutor(initializer=_init) as ex:
        rows = list(ex.map(eval_job, jobs, chunksize=8))
    ok = [r for r in rows if selected_ok(r["early"])]
    ok.sort(key=lambda r: -(r["early"]["r"] - r["early"]["pl"]))
    pick = ok[:5]
    for r in pick:                                     # look at the later data ONLY for the picks
        r["later"] = score(r["cfg"][0], r["cfg"][1], zsets[r["cfg"]], "later")
    t2 = merge_trades([r["cfg"] for r in pick], [zsets[r["cfg"]] for r in pick], 2 * COST)
    late = t2[t2.date >= SPLIT] if not t2.empty else t2
    early = t2[t2.date < SPLIT] if not t2.empty else t2

    def summ(t):
        if t.empty:
            return dict(n=0)
        r = t.r.values
        eq = np.cumsum(r)
        yrs = max((t.date.max() - t.date.min()).days / 365.25, 0.1)
        return dict(n=len(r), win=round(float((r > 0).mean()), 3), avg_r=round(float(r.mean()), 3),
                    total_r=round(float(r.sum()), 1), per_year_r=round(float(r.sum() / yrs), 1),
                    worst_drop_r=round(float((eq - np.maximum.accumulate(eq)).min()), 1),
                    rupees_at_100_per_trade=int(round(r.sum() * 100)),
                    longs=int((t.side == "long").sum()), shorts=int((t.side == "short").sum()))

    # random-entry twin of the whole new strategy on the later data
    pls = []
    for s in range(10):
        zp = [smc.placebo(_D[(c[0], c[1])], zsets[c], seed=s) for c in [r["cfg"] for r in pick]]
        tp = merge_trades([r["cfg"] for r in pick], zp, 2 * COST)
        tp = tp[tp.date >= SPLIT] if not tp.empty else tp
        if len(tp):
            pls.append(tp.r.mean())
    new = dict(early=summ(early), later=summ(late), random_later_avg_r=round(float(np.mean(pls)), 3) if pls else None)
    if len(late) >= 5 and pls:
        boot = np.random.default_rng(9).choice(late.r.values, (4000, len(late))).mean(axis=1)
        new["p_not_better_than_random"] = round(float(np.mean(boot <= np.mean(pls))), 4)
    names = ["tf", "side", "signal", "ema9", "storyline"]
    fmt = lambda c: dict(zip(names, (c[0], c[1], c[2][0] + ("+" + c[2][1] if c[2][1] else ""), c[3], c[4])))
    out = dict(generated=str(date.today()), configs=len(rows), passed_selection=len(ok),
               picks=[dict(cfg=fmt(r["cfg"]), early=r["early"], later=r["later"]) for r in pick],
               new_strategy=new,
               family_best_early={f: max((r["early"]["r"] or -9 for r in rows
                                          if r["cfg"][2][0] == f and r["early"]["n"] >= 30), default=None) for f in FAM})
    Path("reports").mkdir(exist_ok=True)
    (Path("reports") / f"combo-gold-{date.today()}.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

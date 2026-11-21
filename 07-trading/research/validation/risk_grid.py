"""Second pass (21 Nov 2026): realistic risk scaling through the real portfolio engine (open-risk cap binds),
current 13-strategy mix vs a CUT mix, plus a limit-fill 'trade-through' test.  Research only.

Pre-declared CUT (from quant_validate.py evidence: negative after 2025-09-01 and/or negative at +$0.30/oz, DSR~0):
  drop EMA9 2h, EMA9 4h, MSNR qm long 2h, MSNR fresh_v short 4h, MSNR qm short 4h.
Prop MC: same as quant_validate (10k paths x 252 business days, block 5, The5%ers High Stakes 10%/5%, 5% daily,
10% max, 3 profit days).  Two cost cases: as backtested ($0.40 round trip) and +$0.30/oz/side extra.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import best_combo_gold as b  # noqa: E402
import ea_mix_backtest as em  # noqa: E402
import src.smc as smc  # noqa: E402

START = 10_000.0
OUT = Path(__file__).parent
rng = np.random.default_rng(11)
CUT = {"EMA9 2h", "EMA9 4h", "MSNR qm long 2h", "MSNR fresh_v short 4h", "MSNR qm short 4h"}
SEL = pd.Timestamp("2025-09-01")


def boot(base, n_days=252, paths=10000, block=5):
    L = len(base)
    idx = np.empty((paths, n_days), int)
    j = rng.integers(L, size=paths)
    for d in range(n_days):
        idx[:, d] = j
        j = np.where(rng.random(paths) < 1 / block, rng.integers(L, size=paths), (j + 1) % L)
    return base[idx]


def prop(sim, target):
    cum = np.cumsum(sim, 1)
    fail = (sim <= -0.05 * START) | (cum <= -0.10 * START)
    hit = (cum >= target * START) & (np.cumsum(sim >= 0.005 * START, 1) >= 3)
    ff = np.where(fail.any(1), fail.argmax(1), 10 ** 9)
    fh = np.where(hit.any(1), hit.argmax(1), 10 ** 9)
    o = {f"pass_{h}d": round(float(((fh < ff) & (fh < int(h * 5 / 7))).mean()), 3) for h in (60, 90, 180)}
    o["fail_1y"] = round(float((ff < fh).mean()), 3)
    o["pass_1y"] = round(float((fh < ff).mean()), 3)
    return o


def daily(p):
    days = pd.bdate_range(p.t_in.min().normalize(), p.t_out.max().normalize())
    d = p.groupby(p.t_out.dt.normalize()).pnl.sum()
    d.index = d.index.map(lambda z: z if z.weekday() < 5 else z - pd.offsets.BDay(1))
    return d.groupby(level=0).sum().reindex(days, fill_value=0.0)


def summ(p, extra=0.0):
    p = p.assign(pnl=p.pnl - extra * 100 * p.lot * 2).sort_values("t_out")
    d = daily(p)
    eq = START + np.cumsum(p.pnl.values)
    dd_start = float((np.maximum.accumulate(np.r_[START, eq])[1:] - eq).max() / START * 100)  # $ DD as % of $10K
    s1 = prop(boot(d.values), 0.10)
    s2 = prop(boot(d.values), 0.05)
    post = p[p.t_in >= SEL]
    return dict(n=len(p), pnl=round(float(p.pnl.sum()), 0), pnl_post_sel=round(float(post.pnl.sum()), 0),
                sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 2), maxdd_pct_of_start=round(dd_start, 2),
                worst_day_pct=round(float(d.min() / START * 100), 2), mean_month=round(float(p.groupby(p.t_out.dt.to_period("M")).pnl.sum().mean()), 0),
                mean_month_post_sel=round(float(post.groupby(post.t_out.dt.to_period("M")).pnl.sum().mean()), 0),
                step1=s1, step2=s2)


fr = b.frames()
cand = b.candidates(fr)
mix = pd.concat([cand[k]().assign(strategy=k) for k in em.MIX])
ea = em.ea_rules_trades(fr)[["t_in", "t_out", "side", "r", "strategy"]]
allt = pd.concat([mix[["t_in", "t_out", "side", "r", "strategy"]], ea])
cut = allt[~allt.strategy.isin(CUT)]
res = {"grid": {}}
for lab, tr in (("current13", allt), ("cut8", cut)):
    for mr in (0.0025, 0.004, 0.005):
        for cap in (0.02, 0.03):
            if lab == "current13" and (mr, cap) not in ((0.0025, 0.02), (0.005, 0.02), (0.005, 0.03)):
                continue
            p = em.portfolio(tr, fr, ea_risk=mr, mix_risk=mr, cap=cap)
            for extra in (0.0, 0.30):
                res["grid"][f"{lab} risk={mr*100:.2f}% cap={cap*100:.0f}% extra_cost={extra}"] = summ(p, extra)
            print(lab, mr, cap, "done", flush=True)

# trade-through fill test on MSNR strategies (limit must trade through the level by $d, not just touch)
orig = smc.simulate


def make_sim(dollars):
    """Copy of src.smc.simulate: fill at the level only if the bar trades THROUGH it by `dollars` (no touch fills)."""
    def sim(df, zones, *, wait=10, hold=20, rr=2.0, cost=0.0025, one_at_a_time=True):
        d = smc._ohlc(df)
        h, lo, c, o = d.high.values, d.low.values, d.close.values, d.open.values
        px_mean = float(np.mean(c))
        frac = dollars * px_mean if px_mean < 1 else dollars / px_mean  # mirrored series is 1/price
        rows, busy = [], -1
        for z in sorted(zones, key=lambda z: z.known_at):
            if one_at_a_time and z.known_at <= busy:
                continue
            if z.top - z.stop <= 0 or z.top <= 0:
                continue
            eb = None
            for i in range(z.known_at + 1, min(z.known_at + 1 + wait, len(d))):
                if lo[i] <= z.top * (1 - frac):
                    eb, px = i, min(z.top, o[i])
                    break
            if eb is None:
                continue
            stop, target = z.stop, px + rr * (px - z.stop)
            if px <= stop:
                continue
            ex_px = ex = None
            for i in range(eb, min(eb + hold, len(d))):
                if lo[i] <= stop:
                    ex_px, ex = (min(stop, o[i]) if i > eb else stop), i
                    break
                if h[i] >= target and i > eb or (i == eb and c[i] >= target):
                    ex_px, ex = (max(target, o[i]) if i > eb else target), i
                    break
            if ex_px is None:
                ex = min(eb + hold, len(d)) - 1
                ex_px = c[ex]
            ret = ex_px / px - 1 - cost
            rows.append({"entry_bar": eb, "exit_bar": ex, "r": ret * px / (px - stop)})
            busy = ex
        return pd.DataFrame(rows)
    return sim


fill = {}
names = [k for k in em.MIX if k.startswith("MSNR")]
for dlr in (0.0, 0.30, 1.00):
    smc.simulate = make_sim(dlr)
    row = {}
    for k in names:
        t = cand[k]()
        row[k] = dict(n=len(t), avg_r=round(float(t.r.mean()), 3))
    allr = pd.concat([cand[k]() for k in names]).r
    row["ALL_MSNR"] = dict(n=int(len(allr)), avg_r=round(float(allr.mean()), 3))
    fill[f"through_{dlr}"] = row
smc.simulate = orig
res["fill_through"] = fill
(OUT / "risk_grid.json").write_text(json.dumps(res, indent=1, default=str))
print("ok")

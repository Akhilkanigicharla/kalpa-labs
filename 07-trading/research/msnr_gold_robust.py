"""A309: every MSNR playlist setup on gold, both directions, three timeframes, judged robustly.

Akhil (21 Nov 2026): "Build it very robust, did you malaysh[ian]" + the MSNR playlist (Sujith Surya).

Setups (src/msnr.py, from the playlist mapping in research/msnr-2026-11-20.md):
  fresh      first touch of a fresh V / flipped A (RBS) level          (videos 4, 10)
  qm         Quasimodo: V broken down, then the A between broken up     (QM)
  eq_sweep   equal lows swept and closed back above                     (video 9.x)
  rejection  wick into a fresh level + close back, 9 EMA sloping (A308 trigger)
Shorts = the same long logic on the mirrored chart (1/price), as in src/msnr.mirror.
Filters, every combination: k (key level width) 2/5 · weekly storyline on/off · 9 EMA on/off.
(Akhil's $3,100 side rule removed 21 Nov 2026, A322).  Timeframes: 1h and 4h (Jul 2024 → now), daily (2005 → now).

PASS rules (written before any result was looked at):
  1. out-of-sample (1h/4h: from 2025-09-01; daily: from 2019-01-01) trades >= 30
  2. out-of-sample avg R >= +0.10 with DOUBLE costs
  3. in-sample avg R > 0 (works in both halves)
  4. Benjamini-Hochberg q < 0.10 across ALL configs (bootstrap p vs matched random entries)
  5. the neighbour config (other k) is also positive out of sample (not a lucky parameter)
Run:  python research/msnr_gold_robust.py   -> reports/msnr-gold-robust-<date>.json/.md
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
from src.msnr import SETUPS, mirror  # noqa: E402
from src.smc import Zone, placebo, simulate  # noqa: E402
import gold_ema9_msnr as g  # noqa: E402

COST = 0.0002          # ~$0.70 a round trip at $3,500 (MGC commission + 1 tick + spread)
TF = {"1h": dict(wait=20, hold=48, split="2025-09-01"),
      "4h": dict(wait=10, hold=20, split="2025-09-01"),
      "1d": dict(wait=20, hold=20, split="2019-01-01")}
_DATA: dict = {}


def rejection(df: pd.DataFrame, k: int = 2, storyline_on: bool = True) -> list[Zone]:
    """A308's trigger as a long-only zone list (shorts come from the mirror), so every setup
    goes through the same simulator, filters and placebo."""
    from src.msnr import _gate, storyline
    d = g.clean(df)
    sig = g.setups(d, np.ones(len(d), dtype=int), k=k)          # long side only
    out = [Zone(s["t"], float(d.close.iloc[s["t"]]), s["level"], s["stop"], "rejection")
           for s in sig if s["side"] == 1]
    return _gate(out, storyline(d, k) if storyline_on else None)


ALL = dict(SETUPS, rejection=rejection)


def load() -> dict[str, pd.DataFrame]:
    h = g.load_hourly()
    h.index = h.index.tz_convert("UTC").tz_localize(None)
    four = h.resample("4h").agg(dict(open="first", high="max", low="min", close="last")).dropna()
    return {"1h": h, "4h": four, "1d": g.load_daily()}


def _init():
    _DATA.update(load())


def zones_job(key):
    tf, setup, side, k, story = key
    real = _DATA[tf]
    df = mirror(real) if side == "short" else real
    return key, ALL[setup](df, k=k, storyline_on=story)


def filt(zs, real, df, ema_on, side):
    c_real = real.close.values
    e = g.ema(df.close).values
    c = df.close.values
    out = []
    for z in zs:
        t = z.known_at
        if ema_on and not (c[t] > e[t] and e[t] > e[t - 1]):
            continue
        out.append(z)
    return out


def trades(df, zs, tf, cost):
    p = TF[tf]
    t = simulate(df, zs, wait=p["wait"], hold=p["hold"], rr=2.0, cost=cost)
    if not t.empty:
        t["date"] = df.index[t.entry_bar.values]
    return t


def evaluate(cfg, zs):
    tf, setup, side, k, story, ema_on = cfg
    real = _DATA[tf]
    df = mirror(real) if side == "short" else real
    zs = filt(zs, real, df, ema_on, side)
    split = pd.Timestamp(TF[tf]["split"])
    t1, t2 = trades(df, zs, tf, COST), trades(df, zs, tf, 2 * COST)
    if t1.empty:
        return dict(cfg=cfg, is_n=0, oos_n=0, p=1.0)
    ins, oos, oos2 = t1[t1.date < split], t1[t1.date >= split], t2[t2.date >= split]
    pl = []
    for s in range(5):
        tp = trades(df, placebo(df, zs, seed=s), tf, COST)
        if not tp.empty:
            pl.append(tp[tp.date >= split].r.mean())
    plm = float(np.nanmean(pl)) if pl else 0.0
    if len(oos) >= 5:
        rng = np.random.default_rng(11)
        boot = rng.choice(oos.r.values, (2000, len(oos))).mean(axis=1)
        p = float(np.mean(boot <= plm))
    else:
        p = 1.0
    return dict(cfg=cfg, is_n=int(len(ins)), is_r=round(float(ins.r.mean()), 3) if len(ins) else None,
                oos_n=int(len(oos)), oos_r=round(float(oos.r.mean()), 3) if len(oos) else None,
                oos_r_2x=round(float(oos2.r.mean()), 3) if len(oos2) else None,
                oos_win=round(float((oos.r > 0).mean()), 3) if len(oos) else None,
                placebo_r=round(plm, 3), p=round(p, 4))


def eval_job(arg):
    return evaluate(*arg)


def bh(ps: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted q-values."""
    n = len(ps)
    o = np.argsort(ps)
    q = np.empty(n)
    prev = 1.0
    for rank in range(n, 0, -1):
        i = o[rank - 1]
        prev = min(prev, ps[i] * n / rank)
        q[i] = prev
    return q


def verdict(rows: list[dict]) -> list[dict]:
    q = bh(np.array([r["p"] for r in rows]))
    by = {r["cfg"]: r for r in rows}
    for r, qq in zip(rows, q):
        r["q"] = round(float(qq), 4)
    for r in rows:
        tf, setup, side, k, story, e = r["cfg"]
        nb = by.get((tf, setup, side, 5 if k == 2 else 2, story, e), {})
        why = []
        if r["oos_n"] < 30:
            why.append("oos<30")
        if (r.get("oos_r_2x") or -9) < 0.10:
            why.append("oos 2x-cost R<0.10")
        if (r.get("is_r") or -9) <= 0:
            why.append("in-sample R<=0")
        if r["q"] >= 0.10:
            why.append("q>=0.10")
        if (nb.get("oos_r") or -9) <= 0:
            why.append("neighbour k fails")
        r["pass"] = not why
        r["why"] = ", ".join(why)
    return rows


def monte_carlo_dd(r: np.ndarray, risk=0.01, n=2000, seed=3) -> float:
    rng = np.random.default_rng(seed)
    dds = []
    for _ in range(n):
        eq = np.cumprod(1 + risk * rng.permutation(r))
        dds.append(1 - (eq / np.maximum.accumulate(eq)).min())
    return round(float(np.percentile(dds, 95)), 3)


# Closest to passing under Akhil's rule (9 EMA on, $3,100 side rule on), picked from the
# 21 Nov report BEFORE any forward data existed. None passed; paper decides from here.
CANDIDATES = {
    "1h_fresh_short_k2": ("1h", "fresh_v", "short", 2, False, True),
    "1h_fresh_short_k2_story": ("1h", "fresh_v", "short", 2, True, True),
    "4h_fresh_short_k5": ("4h", "fresh_v", "short", 5, False, True),
}
PAPER_START = "2026-11-21"


def paper(out: Path, flags: Path | None = None, data: dict | None = None) -> dict:
    """Forward test of CANDIDATES: only trades entered on/after PAPER_START count. No orders sent."""
    out.mkdir(parents=True, exist_ok=True)
    if flags and (flags / "KILL").exists():
        st = dict(status="killed")
    else:
        _DATA.update(data or load())
        st = {}
        for name, cfg in CANDIDATES.items():
            tf, setup, side, k, story, e = cfg
            real = _DATA[tf]
            df = mirror(real) if side == "short" else real
            zs = filt(ALL[setup](df, k=k, storyline_on=story), real, df, e, side)
            t = trades(df, zs, tf, COST)
            t = t[t.date >= pd.Timestamp(PAPER_START)] if not t.empty else t
            t.to_csv(out / f"{name}.csv", index=False)
            st[name] = dict(trades=int(len(t)), sum_r=round(float(t.r.sum()), 2) if len(t) else 0.0,
                            avg_r=round(float(t.r.mean()), 3) if len(t) else None,
                            verdict="watch" if len(t) < 30 else ("earning" if t.r.mean() >= 0.10 else "not earning"))
        st = dict(status="running", start=PAPER_START, rule="30+ trades and avg R >= +0.10", candidates=st)
    (out / "state.json").write_text(json.dumps(st, indent=1))
    return st


def main() -> int:
    if "--paper" in sys.argv:
        i = sys.argv.index("--paper")
        fl = sys.argv[sys.argv.index("--flags") + 1] if "--flags" in sys.argv else None
        print(json.dumps(paper(Path(sys.argv[i + 1]), Path(fl) if fl else None)))
        return 0
    keys = list(itertools.product(TF, ALL, ("long", "short"), (2, 5), (True, False)))
    with ProcessPoolExecutor(initializer=_init) as ex:
        zmap = dict(ex.map(zones_job, keys))
        jobs = [((*key, e), zmap[key]) for key in keys for e in (True, False)]
        rows = list(ex.map(eval_job, jobs, chunksize=4))
    rows = verdict(rows)
    _init()
    for r in rows:
        if r["pass"]:
            tf, setup, side, k, story, e = r["cfg"]
            real = _DATA[tf]
            df = mirror(real) if side == "short" else real
            t = trades(df, filt(zmap[r["cfg"][:5]], real, df, e, side), tf, 2 * COST)
            r["mc_dd95_1pct"] = monte_carlo_dd(t[t.date >= pd.Timestamp(TF[tf]["split"])].r.values)
    rows.sort(key=lambda r: (not r["pass"], -(r.get("oos_r_2x") or -9)))
    names = ["tf", "setup", "side", "k", "storyline", "ema9"]
    for r in rows:
        r["cfg"] = dict(zip(names, r["cfg"]))
    out = dict(generated=str(date.today()), configs=len(rows), passed=sum(r["pass"] for r in rows),
               rules="oos>=30, oos R@2x cost>=0.10, in-sample R>0, BH q<0.10, neighbour k positive",
               top=rows[:25])
    Path("reports").mkdir(exist_ok=True)
    p = Path("reports") / f"msnr-gold-robust-{date.today()}.json"
    p.write_text(json.dumps(dict(out, all=rows), indent=1, default=str))
    print(json.dumps(dict(configs=out["configs"], passed=out["passed"]), indent=1))
    for r in rows[:15]:
        c = r["cfg"]
        print(c["tf"], c["setup"], c["side"], "k", c["k"], "story", int(c["storyline"]), "ema", int(c["ema9"]),
              "| IS", r["is_n"], r.get("is_r"), "| OOS", r["oos_n"], r.get("oos_r"),
              "2x", r.get("oos_r_2x"), "pl", r["placebo_r"], "q", r["q"], "PASS" if r["pass"] else r["why"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

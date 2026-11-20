"""MSNR on gold (Akhil 20 Nov 2026: "check with gold"). Research only, paper only, not advice.

Markets (Yahoo, read at run time):
  GOLDBEES.NS daily 2012-   the lawful way for Akhil to hold gold (NSE ETF, long only, 0.25% round trip)
  GC=F daily 2005-          COMEX gold futures, the closest free series to XAUUSD (0.05% round trip)
  GC=F 1-hour (730 days)    the timeframe MSNR traders actually use on gold
  GOLDBEES.NS 1-hour        NSE hours only
GC=F is tested long AND short (short = the same rules on the 1/price mirror). Indian residents can't
trade XAUUSD with overseas brokers; GC=F here only shows whether the method works on gold at all.
Same rules as src/msnr.py: config picked on the early part, the later part looked at once, a
same-shape placebo, and a bootstrap chance that the result is no better than the placebo.

Run: cd 07-trading && python3 research/msnr_gold.py --out reports
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import msnr  # noqa: E402


def fetch(sym: str, **kw) -> pd.DataFrame:
    import yfinance as yf
    d = yf.download(sym, auto_adjust=False, progress=False, **kw)
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d = d.rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
    d = d[(d > 0).all(axis=1)]
    if d.index.tz is not None:
        d.index = d.index.tz_convert("Asia/Kolkata").tz_localize(None)
    d["high"] = d[["open", "high", "low", "close"]].max(axis=1)      # Yahoo sometimes stores a close above the high
    d["low"] = d[["open", "high", "low", "close"]].min(axis=1)
    return d


def split_at(df: pd.DataFrame, frac: float = 0.6) -> str:
    return str(df.index[int(len(df) * frac)].date())


def row(name: str, res: dict, split: str) -> list[str]:
    out = []
    for s, r in res.items():
        t, p = r["test"], r["placebo_test"]
        out.append(f"| {name} | {s} | k={r['config']['k']}, story={'on' if r['config']['storyline_on'] else 'off'} | "
                   f"{t['trades']} | {t['win']:.0%} | {t['avg_r']:+.2f} | {t['pf']:.2f} | {p['avg_r']:+.2f} | "
                   f"{t['p_not_better_than_placebo']:.0%} | {r['verdict']} |")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports")
    a = ap.parse_args(argv)
    gb = fetch("GOLDBEES.NS", start="2012-01-01")
    from src import data
    gb, dropped = data.repair_spikes(gb)
    gc = fetch("GC=F", start="2005-01-01")
    gc_h = fetch("GC=F", period="730d", interval="1h")
    gb_h = fetch("GOLDBEES.NS", period="730d", interval="1h")
    runs = [
        ("GOLDBEES daily, long", {"GOLDBEES": gb}, "2019-01-01", 0.0025),
        ("Gold futures daily, long", {"GC": gc}, "2016-01-01", 0.0005),
        ("Gold futures daily, short", {"GC": msnr.mirror(gc)}, "2016-01-01", 0.0005),
        ("Gold futures 1h, long", {"GC": gc_h}, split_at(gc_h), 0.0005),
        ("Gold futures 1h, short", {"GC": msnr.mirror(gc_h)}, split_at(gc_h), 0.0005),
        ("GOLDBEES 1h, long", {"GOLDBEES": gb_h}, split_at(gb_h), 0.0025),
    ]
    lines = ["# MSNR on gold — research only", "",
             f"GOLDBEES daily {gb.index[0].date()}–{gb.index[-1].date()} (bad rows dropped: {', '.join(dropped) or 'none'}); "
             f"GC=F daily {gc.index[0].date()}–{gc.index[-1].date()}; GC=F 1h {gc_h.index[0].date()}–{gc_h.index[-1].date()}; "
             f"GOLDBEES 1h {gb_h.index[0].date()}–{gb_h.index[-1].date()}. Yahoo Finance.",
             "Config picked on the early part only; test = everything after the split date, looked at once. "
             "Hold up to 20 bars, 2R target, stop counted first. Short = same rules on the 1/price mirror.", "",
             "| Market | Setup | Config | Test trades | Win | Avg R | PF | Placebo avg R | Chance no better than placebo | Verdict |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    allres = {}
    for name, frames, split, cost in runs:
        res = msnr.research(frames, split=split, cost=cost)
        allres[name] = {"split": split, "cost": cost, "result": res}
        lines += row(name, res, split)
        print(name, "done", flush=True)
    lines += ["", "Split dates: " + "; ".join(f"{k} {v['split']}" for k, v in allres.items()),
              "", "PASS = ≥30 test trades, avg R ≥ 0.10, PF ≥ 1.2 and above the placebo. A 'chance' under 5% means the",
              "edge over random dip-buying is unlikely to be luck. Not investment advice."]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    day = gc.index[-1].date()
    (out / f"msnr-gold-{day}.md").write_text("\n".join(lines) + "\n")
    (out / f"msnr-gold-{day}.json").write_text(json.dumps(allres, indent=1, default=str))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

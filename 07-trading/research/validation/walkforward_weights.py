"""A347: profit tweak without curve-fitting. Weights are learned ONLY on year 1 (Jul 2024 - Jun 2025) and judged
ONLY on the later 17 months. Rule fixed before running: for every strategy with a positive year-1 average R,
weight = 1 / (std of its year-1 daily R), scaled so the average weight equals today's average, capped at 1.5;
strategies negative in year 1 get 0. Compared with today's weights on the same unseen months."""
import json, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE)); sys.argv = [sys.argv[0], "10000"]
import numpy as np, pandas as pd
import video_tweaks as V
FIT_END = pd.Timestamp("2025-07-01")
KW = dict(V.KW, mix_risk=0.003)


def main():
    fr = V.b.frames(); t = V.trades(fr)
    cur = {k: w for k, w in V.em.WEIGHTS_2026_11_21.items()}
    y1 = t[t.t_in < FIT_END]
    stats = {}
    for s, g in y1.groupby("strategy"):
        daily = g.groupby(pd.to_datetime(g.t_out).dt.date).r.sum()
        stats[s] = dict(avg_r=float(g.r.mean()), n=len(g), sd=float(daily.std()) if len(daily) > 5 else np.nan)
    raw = {s: (1 / v["sd"] if v["avg_r"] > 0 and v["sd"] > 0 else 0.0) for s, v in stats.items()}
    live = [s for s in cur if cur[s] > 0 and s in raw]
    target_mean = np.mean([cur[s] for s in live])
    pos = [s for s in live if raw[s] > 0]
    scale = target_mean * len(live) / sum(raw[s] for s in pos) if pos else 0
    new = dict(cur)
    for s in live:
        new[s] = round(min(1.5, raw[s] * scale), 3)
    test = t[t.t_in >= FIT_END].reset_index(drop=True)
    a = V.evaluate(test, fr, KW, name="today's weights, unseen months")
    b = V.evaluate(test, fr, dict(KW, weights=new), name="walk-forward inverse-vol weights, unseen months")
    rep = dict(year1_stats=stats, new_weights={s: new[s] for s in live}, old_weights={s: cur[s] for s in live},
               current=a, walkforward=b)
    print(json.dumps(rep["new_weights"], indent=0))
    pathlib.Path("reports/walkforward-weights-2026-11-26.json").write_text(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    main()

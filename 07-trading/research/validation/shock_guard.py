"""A346: instant-jump guard. Before each entry: if gold jumped X% against the whole net book at once, skipping
every stop, the loss must stay inside the room left under E8's 2.5% daily limit (budget minus today's loss).
Variants fixed before running: X = 3% / 2%, budget 2.0% / 2.4% of the start balance."""
import json, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE)); sys.argv = [sys.argv[0], "10000"]
import numpy as np, pandas as pd
import video_tweaks as V
KW = dict(V.KW, mix_risk=0.003)


def shock_stats(fr, t, kw):
    p, mt, ck = V.S.run(t, fr, kw)
    px = fr["1h"].close.reindex(pd.to_datetime(ck.c), method="ffill").values
    ex = np.abs(ck.net_lots.values) * 100 * px
    day_loss = np.maximum(0, pd.Series(ck["eq"].values).groupby(pd.to_datetime(ck.c).dt.date.values).transform("max").values - ck["eq"].values)
    out = {}
    for s in (0.02, 0.03, 0.05):
        tot = ex * s + day_loss
        out[f"jump_{s*100:g}pct"] = dict(worst_total_day_loss=round(float(tot.max())),
                                         hours_breaking_2_5pct=round(float((tot > 250).mean() * 100), 2))
    return out


def main():
    fr = V.b.frames(); t = V.trades(fr); rep = {}
    for nm, kw in [("current", KW), ("jump3_budget2.0", dict(KW, shock_pct=0.03, shock_budget=0.020)),
                   ("jump3_budget2.4", dict(KW, shock_pct=0.03, shock_budget=0.024)),
                   ("jump2_budget2.0", dict(KW, shock_pct=0.02, shock_budget=0.020))]:
        r = V.evaluate(t, fr, kw, name=nm); r.update(shock_stats(fr, t, kw)); rep[nm] = r
        print(nm, {k: r[k] for k in ("trades", "net_usd", "positive_months", "worst_day", "pass_pct", "days_to_pass", "payouts_6m")},
              r["jump_3pct"], r["jump_2pct"], flush=True)
    pathlib.Path("reports/shock-guard-2026-11-26.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()

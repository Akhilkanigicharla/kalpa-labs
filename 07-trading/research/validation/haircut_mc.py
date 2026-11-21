"""Edge-haircut Monte Carlo (21 Nov 2026): shift every trade's R down so avg R falls by 25/50/75%, plus +$0.30/oz
extra cost, then The5%ers High Stakes pass odds.  Reuses risk_grid helpers.  Research only."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("rg_helpers", Path(__file__).parent / "risk_grid.py")
src = (Path(__file__).parent / "risk_grid.py").read_text().split("fr = b.frames()")[0]
ns = {"__file__": str(Path(__file__).parent / "risk_grid.py")}
exec(compile(src, "risk_grid_head", "exec"), ns)
b, em, START = ns["b"], ns["em"], ns["START"]
fr = b.frames(); cand = b.candidates(fr)
mix = pd.concat([cand[k]().assign(strategy=k) for k in em.MIX])
ea = em.ea_rules_trades(fr)[["t_in", "t_out", "side", "r", "strategy"]]
allt = pd.concat([mix[["t_in", "t_out", "side", "r", "strategy"]], ea])
out = {}
for lab, tr, mr, cap in (("current13 0.25%/2%", allt, 0.0025, 0.02), ("cut8 0.25%/2%", allt[~allt.strategy.isin(ns["CUT"])], 0.0025, 0.02),
                         ("cut8 0.40%/2%", allt[~allt.strategy.isin(ns["CUT"])], 0.004, 0.02), ("cut8 0.50%/2%", allt[~allt.strategy.isin(ns["CUT"])], 0.005, 0.02)):
    p = em.portfolio(tr, fr, ea_risk=mr, mix_risk=mr, cap=cap)
    p = p.assign(pnl=p.pnl - 0.30 * 100 * p.lot * 2)
    p["r"] = p.pnl / p.risk
    mean_r = p.r.mean()
    for hc in (0.0, 0.25, 0.5, 0.75):
        q = p.assign(pnl=p.pnl - hc * mean_r * p.risk)
        d = ns["daily"](q).values
        out[f"{lab} haircut={int(hc*100)}%"] = dict(avg_r=round(float(q.pnl.sum() / q.risk.sum()), 3),
            mean_month=round(float(q.groupby(q.t_out.dt.to_period('M')).pnl.sum().mean()), 0),
            step1=ns["prop"](ns["boot"](d), 0.10), step2_1y=ns["prop"](ns["boot"](d), 0.05)["pass_1y"])
(Path(__file__).parent / "haircut_mc.json").write_text(json.dumps(out, indent=1))
for k, v in out.items(): print(k, v["avg_r"], v["mean_month"], v["step1"], v["step2_1y"])

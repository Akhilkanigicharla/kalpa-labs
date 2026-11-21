"""A336 final config, month by month (fixed $10K sizing, no compounding).
Final EA defaults: scenario G weights, 0.40% risk, 2% open cap, Friday cut 1.25% + weekend gap 3.75%/3% budget,
+$0.30/oz/side extra cost (realistic). Two firm rule-sets: The5%ers (4% day stop, $9,100 floor) and
E8 $5K-style limits scaled to $10K (1.5% day stop = firm 2.5% - 1%, floor at 93% = firm 8% - 1%)."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
import ea_mix_scenarios as S
em, b = S.em, S.b

def main():
    fr = b.frames(); cand = b.candidates(fr)
    mix = pd.concat([cand[k]().assign(strategy=k) for k in em.MIX])
    ea = em.ea_rules_trades(fr)[["t_in", "t_out", "side", "r", "strategy"]]
    allt = pd.concat([mix[["t_in", "t_out", "side", "r", "strategy"]], ea])
    base = dict(mix_risk=0.004, weights=em.WEIGHTS_2026_11_21, friday_cut=0.0125, gap_pct=0.0375, gap_budget=0.03,
                extra_cost=0.30, min_stop=1.5, lot_cap=0.10)
    cfg = {"the5ers": dict(base, day_stop_eq=0.04, eq_floor=9100.0),
           "e8": dict(base, day_stop_eq=0.015, eq_floor=9300.0)}
    out = {}
    for name, kw in cfg.items():
        p, mt, ck = S.run(allt, fr, kw)
        p = p.copy(); p["m"] = pd.to_datetime(p["t_close"]).dt.to_period("M")
        ck = ck.copy(); ck["m"] = pd.to_datetime(ck["c"]).dt.to_period("M")
        rows = []
        for m, g in p.groupby("m"):
            e = ck[ck.m == m]
            peak = e["eq"].cummax(); dd = float((peak - e["eq"]).max()) if len(e) else 0.0
            dly = g.groupby(pd.to_datetime(g.t_close).dt.date).pnl.sum()
            rows.append(dict(month=str(m), trades=len(g), wins=int((g.pnl > 0).sum()), losses=int((g.pnl <= 0).sum()),
                             net_usd=round(float(g.pnl.sum()), 0), pct=round(float(g.pnl.sum()) / 100, 2),
                             worst_day_usd=round(float(dly.min()), 0), max_dd_usd=round(dd, 0),
                             exits_weekend=int((g.exit == "weekend").sum())))
        df = pd.DataFrame(rows); out[name] = dict(stats=S.stats(p, ck), months=rows,
            the5ers=S.summarize_attempts(S.attempts(p, mt, ck, floor=kw["eq_floor"])) if name == "the5ers" else None)
        print(name, "| total", int(df.net_usd.sum()), "| +months", int((df.net_usd > 0).sum()), "/", len(df),
              "| trades", int(df.trades.sum()))
        print(df.drop(columns="pct").to_string(index=False))
        if name == "the5ers": print({k: out[name]["the5ers"][k] for k in ("step1_pass_pct", "funded_pct")})
    json.dump(out, open("reports/ea-final-monthly-2026-11-22.json", "w"), indent=1, default=str)

if __name__ == "__main__":
    main()

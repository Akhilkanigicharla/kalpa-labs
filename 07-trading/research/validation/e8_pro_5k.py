"""A337: final EA re-tested under E8 Pro $5K rules (help.e8markets / intercom.help/e8, fetched 22 Nov 2026):
8% target, only 2% of initial balance per day counts (daily profit cap), 2.5% daily drawdown of initial balance
from the day's starting balance, 8% static max loss, no min days / time limit, payouts any day once profit >= 1%,
50% of profit requestable (rest stays as buffer), 80% split, metals leverage 1:15.
EA settings: $5K, 0.40% risk, scenario-G weights, 2% open cap, weekend gap cut, +$0.30/oz/side cost,
own day stop 1.5% (firm 2.5% - 1%), own floor $4,650 (firm 8% - 1%), close+stop for the day at +2%.
Data: GC=F hourly (gold futures, not E8's own feed, which needs an account)."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import ea_mix_scenarios as S
em, b = S.em, S.b
INIT = float(sys.argv[1]) if len(sys.argv) > 1 else 5000.0
em.START = INIT; S.START = INIT

def sim(d, horizon=180):
    """d: daily table (pnl vs prev close, low vs prev close). Start a challenge every trading day."""
    days = d.index; pnl = d.pnl.values; low = d.low.values; n = len(d); res = []
    for s in range(n):
        eq, counted, t, out = INIT, 0.0, s, None
        while t < n and t - s < horizon:
            if low[t] < -0.025 * INIT or eq + low[t] < INIT * 0.92:
                out = "fail"; break
            eq += pnl[t]; counted += min(pnl[t], 0.02 * INIT)
            if eq < INIT * 0.92: out = "fail"; break
            t += 1
            if counted >= 0.08 * INIT: out = "pass"; break
        if out is None and t >= n:
            continue
        r = dict(start=str(days[s].date()), result=out or "open", days=t - s)
        if out == "pass":                       # funded: 180 days after passing, payouts any day >= 1% counted
            eqf, cnt, paid, k, brk = INIT, 0.0, 0.0, t, False
            floor = INIT * 0.92
            while k < n and k - t < 180:
                if low[k] < -0.025 * INIT or eqf + low[k] < floor: brk = True; break
                eqf += pnl[k]; cnt += min(pnl[k], 0.02 * INIT)
                if eqf < floor: brk = True; break
                if cnt >= 0.01 * INIT:
                    req = 0.5 * cnt; paid += 0.8 * req; eqf -= req; cnt = 0.0
                k += 1
            r.update(funded_days=k - t, payouts_usd=round(paid, 0), funded_breach=brk,
                     full=bool(k - t >= 180 or brk))
        res.append(r)
    return pd.DataFrame(res)

def main():
    fr = b.frames(); cand = b.candidates(fr)
    mix = pd.concat([cand[k]().assign(strategy=k) for k in em.MIX])
    ea = em.ea_rules_trades(fr)[["t_in", "t_out", "side", "r", "strategy"]]
    allt = pd.concat([mix[["t_in", "t_out", "side", "r", "strategy"]], ea])
    kw = dict(mix_risk=float(sys.argv[3]) / 100 if len(sys.argv) > 3 else 0.004, weights=em.WEIGHTS_2026_11_21, friday_cut=0.0125, gap_pct=0.0375, gap_budget=0.03,
              extra_cost=0.30, min_stop=1.5, lot_cap=0.10, day_stop_eq=float(sys.argv[2]) if len(sys.argv) > 2 else 0.015, eq_floor=INIT * 0.93, day_profit_cap=0.02,
              margin_lev=15.0)
    p, mt, ck = S.run(allt, fr, kw)
    d = S.daily_table(ck)
    p = p.copy(); p["m"] = pd.to_datetime(p.t_close).dt.to_period("M")
    ck = ck.copy(); ck["m"] = pd.to_datetime(ck.c).dt.to_period("M")
    rows = []
    for m, g in p.groupby("m"):
        e = ck[ck.m == m]; dd = float((e["eq"].cummax() - e["eq"]).max())
        dly = g.groupby(pd.to_datetime(g.t_close).dt.date).pnl.sum()
        capped = float(np.minimum(d[d.index.to_period("M") == m].pnl, 0.02 * INIT).sum())
        rows.append(dict(month=str(m), trades=len(g), wins=int((g.pnl > 0).sum()), losses=int((g.pnl <= 0).sum()),
                         net_usd=round(float(g.pnl.sum()), 0), counted_usd=round(capped, 0),
                         worst_day_usd=round(float(dly.min()), 0), max_dd_usd=round(dd, 0)))
    df = pd.DataFrame(rows)
    a = sim(d); pas = a[a.result == "pass"]; fin = a[a.result != "open"]
    full = pas[pas.full]
    summ = dict(trades=len(p), net_usd=round(float(p.pnl.sum()), 0), positive_months=int((df.net_usd > 0).sum()),
                months=len(df), worst_day_intraday_usd=round(float(d.low.min()), 0),
                worst_day_vs_2_5pct_limit_usd=-0.025 * INIT, lowest_equity=round(float(ck["eq"].min()), 0),
                peak_lots=round(float(ck.net_lots.abs().max()), 2),
                worst_day_pct_of_limit=round(float(-d.low.min()) / (0.025 * INIT) * 100, 0), exits={k: int(v) for k, v in p.exit.value_counts().items()},
                attempts=len(fin), pass_pct=round(len(pas) / max(len(fin), 1) * 100, 1),
                days_to_pass_median=float(pas.days.median()) if len(pas) else None,
                pass_within_30=round(float((pas.days <= 30).sum() / max(len(fin), 1) * 100), 1),
                pass_within_60=round(float((pas.days <= 60).sum() / max(len(fin), 1) * 100), 1),
                funded_breach_pct_6m=round(float(full.funded_breach.mean() * 100), 1) if len(full) else None,
                payouts_6m_median_usd=float(full.payouts_usd.median()) if len(full) else None,
                payouts_6m_p10_usd=float(full.payouts_usd.quantile(.1)) if len(full) else None)
    print(df.to_string(index=False)); print(json.dumps(summ, indent=1))
    json.dump(dict(rules=__doc__, summary=summ, months=rows), open(f"reports/ea-e8-pro-{int(INIT//1000)}k-r{sys.argv[3] if len(sys.argv) > 3 else '0.40'}.json", "w"),
              indent=1, default=str)

if __name__ == "__main__":
    main()

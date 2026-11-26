"""A345: can the final E8 bot (0.30% risk) take gold spikes? Akhil 26 Nov 2026.
1. P&L on the 20 most violent days in the data (largest high-low range) and on every CPI / NFP / FOMC day.
2. News blackout 2h (current) vs 4h vs 0h (the firm's 2-minute rule only), full E8 test.
3. Shock test: at EVERY hour, if gold jumped 3% / 5% / 9.5% against the open book instantly (stops skipped),
   how much of E8's 2.5% daily limit would that use?  9.5% = the 30 Jan 2026 crash size reported by 3 sources."""
import json, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE)); sys.argv = [sys.argv[0], "10000"]
import numpy as np, pandas as pd
import video_tweaks as V
import macro_layer_gold as M
KW = dict(V.KW, mix_risk=0.003)


def main():
    fr = V.b.frames(); h1 = fr["1h"]; t = V.trades(fr)
    p, mt, ck = V.S.run(t, fr, KW)
    day_pnl = p.groupby(pd.to_datetime(p.t_close).dt.date).pnl.sum()
    d = h1.groupby(h1.index.date).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    d["range_pct"] = (d.high - d.low) / d.close * 100
    top = d.sort_values("range_pct", ascending=False).head(20)
    wild = [dict(day=str(k), range_pct=round(float(r.range_pct), 1), bot_pnl=round(float(day_pnl.get(k, 0.0))))
            for k, r in top.iterrows()]
    ev_days = {ts.date() for ts in M.events_utc()}
    ev = day_pnl[[k in ev_days for k in day_pnl.index]]; non = day_pnl[[k not in ev_days for k in day_pnl.index]]
    rep = dict(wildest_20_days=wild,
               wildest_20_total=round(float(sum(w["bot_pnl"] for w in wild))),
               wildest_20_worst=min(w["bot_pnl"] for w in wild),
               event_days=dict(n=len(ev), total=round(float(ev.sum())), avg=round(float(ev.mean()), 1), worst=round(float(ev.min()))),
               other_days=dict(n=len(non), total=round(float(non.sum())), avg=round(float(non.mean()), 1), worst=round(float(non.min()))))
    px = h1.close.reindex(pd.to_datetime(ck.c), method="ffill").values
    exposure = np.abs(ck.net_lots.values) * 100 * px                      # $ per 1.00 = 100% move
    lim = 0.025 * V.INIT
    for s in (0.03, 0.05, 0.095):
        loss = exposure * s
        rep[f"shock_{s*100:g}pct"] = dict(worst_loss=round(float(loss.max())), pct_of_daily_limit=round(float(loss.max() / lim * 100)),
                                          hours_over_daily_limit_pct=round(float((loss > lim).mean() * 100), 2),
                                          hours_over_max_loss_pct=round(float((loss > 0.08 * V.INIT).mean() * 100), 3))
    for h in (0.0, 4.0):
        kw = dict(KW); kw["news_block_h"] = h
        rep[f"news_block_{h:g}h"] = V.evaluate(t, fr, kw, name=f"news blackout {h:g}h")
    rep["news_block_2h_current"] = V.evaluate(t, fr, KW, name="news blackout 2h (current)")
    print(json.dumps({k: v for k, v in rep.items() if k != "wildest_20_days"}, indent=1))
    pathlib.Path("reports/spike-stress-2026-11-26.json").write_text(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    main()

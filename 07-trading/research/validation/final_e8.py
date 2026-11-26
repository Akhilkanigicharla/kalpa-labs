"""A347: the final E8 Pro $10K bot, every live setting on: 0.30% risk, scenario-G weights, 2% open cap, Friday cut
1.25% + weekend gap budget 1.5% (audit fix), news de-risk (A346), 2h news pause, 1.5% day stop, $9,300 floor,
2% daily profit cap, 1:15 margin, +$0.30/oz/side cost. Month by month + E8 challenge/funded simulation."""
import json, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE)); sys.argv = [sys.argv[0], "10000"]
import pandas as pd
import derisk_windows as D
V = D.V


def main():
    fr = V.b.frames(); t = V.trades(fr); win, ev = D.windows(fr["1h"])
    news = {w for w in win if not (w.hour in (20, 21) and w.dayofweek <= 3) or any(abs((w - e).total_seconds()) <= 3 * 3600 for e in ev)}
    kw = dict(V.KW, mix_risk=0.003, gap_budget=0.015, derisk_at=news)
    r = V.evaluate(t, fr, kw, name="FINAL E8 Pro $10K bot")
    r["jump_risk"] = D.jump_risk(fr, t, kw, ev)
    p, mt, ck = V.S.run(t, fr, kw)
    p["m"] = pd.to_datetime(p.t_close).dt.to_period("M")
    months = [dict(month=str(m), trades=len(g), wins=int((g.pnl > 0).sum()), losses=int((g.pnl <= 0).sum()),
                   profit=round(float(g.pnl.sum()))) for m, g in p.groupby("m")]
    r["months"] = months
    r["exits"] = {k: int(v) for k, v in p.exit.value_counts().items()}
    pathlib.Path("reports/final-e8-2026-11-26.json").write_text(json.dumps(r, indent=1, default=str))
    for m in months:
        print(m["month"], m["trades"], m["wins"], m["losses"], m["profit"])
    print(r["exits"], r["jump_risk"]["at_news"])


if __name__ == "__main__":
    main()

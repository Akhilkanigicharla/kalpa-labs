"""A346 v2: cut the open book only where instant jumps really happen. Fixed before running:
windows = 2h before each CPI / NFP / FOMC release (official dates) and the daily trading break (20:00-21:59 UTC
bars, Mon-Thu); in a window, close losers first then the biggest lot until a 3% jump against the net book
would lose <= 2.0% of the start balance minus today's loss; no new entries in a window. The weekend is already
covered by the Friday cut."""
import json, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE)); sys.argv = [sys.argv[0], "10000"]
import numpy as np, pandas as pd
import video_tweaks as V
import macro_layer_gold as M
KW = dict(V.KW, mix_risk=0.003)


def windows(h1):
    ev = M.events_utc()
    ev = pd.DatetimeIndex([e.tz_localize(None) if getattr(e, "tzinfo", None) else e for e in ev])
    s = set()
    for e in ev:
        for k in (2, 1, 0):
            s.add(e.floor("h") - pd.Timedelta(hours=k))
    br = h1.index[(h1.index.hour.isin([20, 21])) & (h1.index.dayofweek <= 3)]
    s |= set(br)
    return s, ev


def jump_risk(fr, t, kw, ev):
    p, mt, ck = V.S.run(t, fr, kw)
    c = pd.DatetimeIndex(pd.to_datetime(ck.c)); px = fr["1h"].close.reindex(c, method="ffill").values
    ex = np.abs(ck.net_lots.values) * 100 * px
    eq = pd.Series(ck["eq"].values, index=c)
    day_loss = (eq.groupby(c.date).transform("max") - eq).clip(lower=0).values
    at_event = c.floor("h").isin(set(ev.floor("h")))
    at_break = (c.hour == 22) & (c.dayofweek <= 3)
    out = {}
    for nm, msk in (("at_news", at_event), ("at_daily_break", at_break), ("all_hours", np.ones(len(c), bool))):
        tot = ex[msk] * 0.03 + day_loss[msk]
        out[nm] = dict(hours=int(msk.sum()), worst_3pct_jump_day_loss=round(float(tot.max())) if msk.any() else 0,
                       breaks_e8_daily_pct=round(float((tot > 250).mean() * 100), 2) if msk.any() else 0)
    return out


def main():
    fr = V.b.frames(); t = V.trades(fr); win, ev = windows(fr["1h"]); rep = {}
    for nm, kw in [("current", KW), ("derisk_news_and_break", dict(KW, derisk_at=win))]:
        r = V.evaluate(t, fr, kw, name=nm); r["jump_risk"] = jump_risk(fr, t, kw, ev); rep[nm] = r
        print(nm, {k: r[k] for k in ("trades", "net_usd", "positive_months", "worst_day", "lowest_equity", "pass_pct",
                                     "days_to_pass", "payouts_6m")}, r["jump_risk"], flush=True)
    pathlib.Path("reports/derisk-windows-2026-11-26.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()

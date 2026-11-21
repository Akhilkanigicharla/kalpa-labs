"""A321: the A320 strategy (A315 loose EA + MSNR fresh-level filter) on 5m, 30m and 1h, every setup.

Akhil (21 Nov 2026): "use same strategy for 5mins and 1hr and 30mins and try to trade every one setup
is found backtest it ... I assume gold will drop 3100 and from there it will go up so check support
and resistance and everything and take trades".

Same rules on every timeframe: H4 regime + (loose) trend from H1/H4, setup AND trigger on the chosen
timeframe, trigger window = 2 bars, stop 1.5 x ATR (ATR-scaled doc numbers), doc exits (50% at 1.5R,
breakeven, trail, 2.5R), $0.40 cost, $10K, 0.75% risk.  MSNR: H4 key levels from closes, tracked on the
trading timeframe; the nearest level on the trade side must be fresh.
Two trade rules:  ea     = the EA's guards (1 position, 3 a day, cooldown, 3-loss pause, -3% day)
                  every  = every setup is taken, positions may overlap
Akhil's bias:     none   = both directions (EA regime decides)
                  3100   = only shorts while price is above $3,100; only longs at/below $3,100
Data (free): 5m and 30m = last 60 days (Yahoo limit for intraday), 1h = 2 years.  Random-entry
baseline per row (same count, sides, hours and exits, 30 seeds).
Research code only.  Not investment advice.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ea_design_gold as e  # noqa: E402
import ea_msnr_gold as m  # noqa: E402
from src.msnr import levels  # noqa: E402

LEVEL = 3100.0
CACHE5 = Path("/tmp/gc_m5_60d.parquet")


def load():
    h1 = m.load_h1()
    if CACHE5.exists():
        m5 = pd.read_parquet(CACHE5)
    else:
        import yfinance as yf
        m5 = e._ohlc(yf.download("GC=F", period="60d", interval="5m", progress=False, auto_adjust=False))
        m5.to_parquet(CACHE5)
    return m5, h1


def bias3100(sig):
    out = []
    for s in sig:
        px = s["trig"]
        if (s["side"] == -1 and px > LEVEL) or (s["side"] == 1 and px <= LEVEL):
            out.append(s)
    return out


def placebo(sig, x, tf, seed):
    rng = np.random.default_rng(seed)
    ct = x.index + pd.Timedelta(tf)
    ok = np.array([e.in_session(t) for t in ct])
    pool = np.where(ok)[0]
    at = e.g.atr(x)
    out = []
    for s in sig:
        i = int(pool[rng.integers(len(pool))])
        a = at[i] if np.isfinite(at[i]) else s["atr"]
        out.append(dict(t_close=ct[i], side=s["side"], trig=float(x.high.iloc[i] if s["side"] == 1 else x.low.iloc[i]),
                        swing=float(x.low.iloc[i] if s["side"] == 1 else x.high.iloc[i]), atr=float(a)))
    return sorted(out, key=lambda z: z["t_close"])


def row(x, tf, sig, every, seeds=30):
    e.EVERY = every
    t = e.simulate(x, pd.Timedelta(tf), sig, 2 * pd.Timedelta(tf))
    res = dict(setups=len(sig), **e.summary(t))
    if len(t):
        res["the5ers_8pct"] = e.weekly_prop(t) if (t.t_in.max() - t.t_in.min()).days > 30 else None
        pr = []
        for sd in range(seeds):
            pt = e.simulate(x, pd.Timedelta(tf), placebo(sig, x, tf, sd), 2 * pd.Timedelta(tf))
            pr.append(float(pt.r.mean()) if len(pt) else 0.0)
        res["random_avg_r"] = round(float(np.mean(pr)), 3)
        res["p_vs_random"] = round(float((np.array(pr) >= t.r.mean()).mean()), 2)
    e.EVERY = False
    return res


def levels_now(h1: pd.DataFrame):
    """Current MSNR support/resistance: fresh/unfresh key levels on H4 and daily between price and $3,100."""
    out = {}
    px = float(h1.close.iloc[-1])
    for name, rule in (("H4", "4h"), ("D1", "1D")):
        d = e.resample(h1, rule).dropna()
        st = []
        for lv in levels(d, 2):
            role, fresh = (1 if lv.kind == "V" else -1), True
            for t in range(lv.known_at + 1, len(d)):
                c, h, lo = d.close.iloc[t], d.high.iloc[t], d.low.iloc[t]
                if role == 1:
                    if c < lv.price: role, fresh = -1, True
                    elif lo <= lv.price: fresh = False
                else:
                    if c > lv.price: role, fresh = 1, True
                    elif h >= lv.price: fresh = False
            st.append((round(lv.price, 1), "support" if role == 1 else "resistance", fresh))
        sup = sorted({s for s in st if s[1] == "support" and LEVEL - 50 <= s[0] <= px}, key=lambda z: -z[0])
        res = sorted({s for s in st if s[1] == "resistance" and px <= s[0] <= px + 300}, key=lambda z: z[0])
        out[name] = dict(supports_down_to_3100=[dict(price=p, fresh=f) for p, _, f in sup][:12],
                         resistances_above=[dict(price=p, fresh=f) for p, _, f in res][:5])
    return px, out


def main() -> int:
    e.SCALED, e.DROP = True, set(e.LOOSE)
    m5, h1 = load()
    h4 = e.resample(h1, "4h")
    h4f, h1f = e.h4_features(h4, h1), e.h1_features(h1)
    frames = {"5m": m5, "30m": e.resample(m5, "30min").dropna(), "1h": h1}
    story0 = None
    rep = dict(generated=str(date.today()), last_price=None, results={})
    for tf, x in frames.items():
        base = e.setups(x, pd.Timedelta(tf), h1f, h4f)
        st = m.msnr_state(x, h4, tf=tf)
        at = pd.Series(e.g.atr(x), index=x.index)
        story0 = pd.Series(0.0, index=x.index)
        fresh = m.apply(base, st, story0, at, {"fresh"}, x.index, tf=tf)
        per = f"{x.index[0].date()} to {x.index[-1].date()}"
        for bname, sig in (("none", fresh), ("3100", bias3100(fresh))):
            for rule in ("ea", "every"):
                rep["results"][f"{tf}|{bname}|{rule}"] = dict(period=per, **row(x, tf, sig, rule == "every"))
        # 1h only: same window as 5m/30m for a fair comparison
        if tf == "1h":
            x60 = x[x.index >= m5.index[0]]
            s60 = [s for s in fresh if s["t_close"] >= m5.index[0]]
            rep["results"]["1h_last60d|none|every"] = dict(period=f"{x60.index[0].date()} to {x60.index[-1].date()}",
                                                           **row(x, tf, s60, True))
    px, lv = levels_now(h1)
    rep["last_price"] = dict(price=round(px, 1), at=str(h1.index[-1]))
    rep["levels"] = lv
    Path("reports").mkdir(exist_ok=True)
    (Path("reports") / f"ea-multitf-gold-{date.today()}.json").write_text(json.dumps(rep, indent=1, default=str))
    for k, v in rep["results"].items():
        print(f"{k:24s} {v.get('period')} n={v.get('n')} setups={v.get('setups')} avg={v.get('avg_r')} totR={v.get('total_r')} "
              f"$={v.get('profit_usd')} dd={v.get('worst_drop_pct')} win={v.get('win')} rnd={v.get('random_avg_r')} p={v.get('p_vs_random')} 5ers={v.get('the5ers_8pct')}")
    print(json.dumps({"last_price": rep["last_price"], "levels": lv}, indent=0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

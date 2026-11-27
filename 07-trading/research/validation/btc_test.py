"""Akhil 27 Nov 2026: "do you think our strategy works on BTC as well" -> "test it".
Replays the SAME 13 gold strategies (12 mix + EA+MSNR 1h, scenario-G weights) on BTC-USD hourly (yfinance, ~730 days)
and on gold for comparison. Results in R (1R = the trade's planned risk), so price scale does not matter.
Costs: gold $0.40 round trip (as in all gold tests); BTC 0.05% of price round trip (base) and 0.10% (stress).
Checks: per-strategy trades/win rate/avg R, first half vs second half (out-of-sample), portfolio at 0.30% risk per
weight-1 trade, month by month, worst day, cost stress. Research only, not investment advice."""
import functools, json, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent))
import numpy as np, pandas as pd
import best_combo_gold as b, ea_design_gold as e, ea_msnr_gold as m, gold_ema9_msnr as g

W = {"MSNR fresh_v long 1h": 1.0, "MSNR fresh_v long 2h": 1.0, "MSNR fresh_v short 2h": 1.0,
     "MSNR fresh_v long 4h": 0.5, "MSNR qm long 1h": 0.5, "MSNR qm long 4h": 0.5, "MSNR qm short 1h": 0.5,
     "EA+MSNR 1h": 0.5}
RISK = 0.003
_RUN = g.run


def load(ticker):
    import yfinance as yf
    return e._ohlc(yf.download(ticker, period="730d", interval="1h", progress=False, auto_adjust=False))


def trades(h1, cost_frac):
    mean = float(h1.close.mean())
    b.MSNR_COST = cost_frac * mean; e.COST = cost_frac * mean
    g.run = functools.partial(_RUN, cost=cost_frac * mean)
    m.load_h1 = lambda: h1
    fr = b.frames(); cand = b.candidates(fr)
    out = []
    for k, w in W.items():
        t = cand[k]()
        if len(t): out.append(t.assign(strategy=k, w=w))
    g.run = _RUN
    return pd.concat(out).sort_values("t_out").reset_index(drop=True), fr


def stats(t):
    r = t.r.values
    return dict(trades=len(r), win_rate=round(float((r > 0.05).mean()), 3) if len(r) else None,
                avg_r=round(float(r.mean()), 3) if len(r) else None, total_r=round(float(r.sum()), 1))


def portfolio(t):
    t = t.copy(); t["usd"] = t.r * t.w * RISK * 10_000
    t["day"] = pd.to_datetime(t.t_out).dt.date; t["m"] = pd.to_datetime(t.t_out).dt.to_period("M")
    eq = 10_000 + t.usd.cumsum(); dd = float((eq - eq.cummax()).min())
    months = {str(k): round(float(v)) for k, v in t.groupby("m").usd.sum().items()}
    return dict(profit_usd=round(float(t.usd.sum())), worst_drop_usd=round(dd), worst_day_usd=round(float(t.groupby("day").usd.sum().min())),
                months_positive=f"{sum(v > 0 for v in months.values())}/{len(months)}", months=months)


def report(name, h1, cost):
    t, fr = trades(h1, cost)
    half = t.t_in.iloc[len(t) // 2] if len(t) else None
    return dict(market=name, period=f"{h1.index[0].date()} to {h1.index[-1].date()}", cost_round_trip_pct=round(cost * 100, 3),
                all=stats(t), first_half=stats(t[t.t_in < half]), second_half=stats(t[t.t_in >= half]),
                per_strategy={k: stats(g_) for k, g_ in t.groupby("strategy")}, portfolio_0_30pct=portfolio(t))


def main():
    btc = load("BTC-USD"); gold = m.load_h1()
    res = dict(btc_base=report("BTC-USD", btc, 0.0005), btc_stress=report("BTC-USD", btc, 0.0010),
               gold_reference=report("GC=F", gold, 0.40 / float(gold.close.mean())))
    out = HERE.parent.parent / "reports" / "btc-test-2026-11-27.json"
    out.write_text(json.dumps(res, indent=1, default=str))
    for k, v in res.items():
        p = v["portfolio_0_30pct"]
        print(k, v["period"], v["all"], "| 1st half", v["first_half"]["avg_r"], "2nd half", v["second_half"]["avg_r"],
              "| $", p["profit_usd"], "worst drop", p["worst_drop_usd"], "worst day", p["worst_day_usd"], "months+", p["months_positive"])


if __name__ == "__main__":
    main()

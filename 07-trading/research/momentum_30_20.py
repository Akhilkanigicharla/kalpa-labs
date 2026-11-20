"""A294: "A simple momentum strategy that beat the market by 10%" (Akhil's reel, Kushal Lodha x Groww,
20 Nov 2026). Research only, paper only, not advice.

The reel's rule as shown on screen (no numbers for lookback or rebalance day were shown, so the
textbook choices below were fixed BEFORE running):
  1. Universe: rank the stocks by momentum (12-month return, skipping the last month).
  2. Hold the top 20 in equal weight.
  3. Rebalance monthly: a holding stays while it is still in the top 30 (the "buffer"); a holding
     that drops to rank 31+ is sold, and the best-ranked new entrants fill the gap.
Variants: with and without a market filter (stay in cash when the Nifty is below its 200-day average).

Honest limits:
  - Universe = TODAY's Nifty 50 list (Yahoo has no free point-in-time history), so winners that
    joined later flatter the result (survivorship bias). Treat the number as an upper bound.
  - A 20-stock portfolio needs about Rs 1 lakh to buy whole shares; run at Rs 1,00,000.
  - Missing Yahoo quotes are filled with the last price (otherwise the engine values a holding at 0).
  - Costs: every NSE delivery charge, 0.1% slippage each side, Rs 15.34 DP charge per sell (A273 engine).

Run: cd 07-trading && python3 research/momentum_30_20.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a273_multi_strategy as A  # noqa: E402

A.CAPITAL = 100_000.0
LOOK, SKIP, HOLD, BUFFER = 252, 21, 20, 30


def ranks(hist: pd.DataFrame) -> pd.Series:
    ret = hist.iloc[-1 - SKIP] / hist.iloc[-1 - LOOK] - 1
    ret = ret[hist.iloc[-1].notna() & hist.iloc[-1 - LOOK].notna()]
    return ret.rank(ascending=False)


def strat_30_20(px: pd.DataFrame, nifty: pd.Series, rb: list, filt: bool) -> dict:
    stocks = [c for c in px if c in A.NIFTY50]
    tr = A.trend_on(nifty)
    out, held = {}, []
    for d in rb:
        hist = px.loc[:d, stocks]
        if len(hist) <= LOOK + SKIP:
            continue
        if filt and not bool(tr.get(d, False)):
            held, out[d] = [], {}
            continue
        r = ranks(hist)
        held = [s for s in held if r.get(s, 999) <= BUFFER]                  # keep while inside the top 30
        for s in r.sort_values().index:                                      # fill with the best new entrants
            if len(held) >= HOLD:
                break
            if s not in held:
                held.append(s)
        out[d] = {s: 1.0 / HOLD for s in held}
    return out


def main() -> int:
    px = A.repair(A.yahoo([f"{s}.NS" for s in A.NIFTY50] + ["NIFTYBEES.NS", "^NSEI"], "a273_stocks"))
    px.columns = [c.replace(".NS", "") for c in px.columns]
    nifty = px.pop("^NSEI") if "^NSEI" in px else px["NIFTYBEES"]
    px = px[px.index >= "2010-01-01"].ffill()        # a missing quote must not value a holding at Rs 0
    rb = A.rebalance_days(px.index, "M")
    rows = []
    for start, label in [("2011-02-01", "2011–2026"), (A.TEST_START, "2019–2026 (test years)")]:
        sub = px[px.index >= start]
        rbs = [d for d in rb if d >= sub.index[0]]
        for name, tg in [("Momentum 30/20", strat_30_20(px, nifty, rbs, filt=False)),
                         ("Momentum 30/20 + Nifty 200-day filter", strat_30_20(px, nifty, rbs, filt=True)),
                         ("Buy and hold NIFTYBEES", {rbs[0]: {"NIFTYBEES": 1.0}})]:
            v, n = A.simulate(sub, tg)
            s = A.stats(v, n)
            rows.append({"period": label, "line": name, "cagr": s["cagr"], "max_dd": s["max_dd"],
                         "worst_year": s["worst_year"], "sharpe": s["sharpe"], "trades_yr": s["trades_per_yr"],
                         "end_rs": v.iloc[-1]})
    t = pd.DataFrame(rows)
    lines = ["# Momentum 30/20 (reel, 20 Nov 2026) — research only", "",
             "Universe: today's Nifty 50 (survivorship bias: an upper bound). Rs 1,00,000, all NSE charges, "
             "0.1% slippage, monthly rebalance at the close, traded next close. 12-1 month momentum, hold 20, "
             "sell when rank > 30.", "",
             "| Period | Strategy | Yearly return | Worst fall | Worst year | Sharpe | Trades/yr | Rs 1 lakh became |",
             "|---|---|---|---|---|---|---|---|"]
    for r in t.itertuples():
        lines.append(f"| {r.period} | {r.line} | {r.cagr:.1%} | {r.max_dd:.0%} | {r.worst_year:.0%} | {r.sharpe:.2f} | "
                     f"{r.trades_yr:.0f} | Rs {r.end_rs:,.0f} |")
    lines += ["", "Not investment advice. Paper only."]
    out = Path(__file__).resolve().parents[1] / "reports"
    out.mkdir(exist_ok=True)
    day = px.index[-1].date()
    (out / f"momentum-30-20-{day}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""A339: export the gold bot's backtest for the private trade dashboard.

Re-runs the FINAL E8 Pro $10K bot exactly as research/validation/final_e8.py does (same cached GC=F hourly
candles, same settings), then writes dashboard/data.json with:
  candles  every hourly candle (UTC), packed: hour gaps + tenths of a dollar (gold ticks are $0.10)
  trades   every simulated trade: entry/exit time, side, strategy, entry price, effective exit price, R, P&L, exit reason
  months   trades / wins / losses / profit per month (same grouping as the report: month of the exit, UTC)
  stats    headline numbers; the script stops if they don't match reports/final-e8-2026-11-26.json
  demo     [] for now: live demo-account trades go here later, in the same shape as trades

Run from 07-trading:  python3 dashboard/export_data.py      (about 30 s; then python3 dashboard/build.py)
"""
import json, pathlib, sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent                                   # 07-trading
for p in (ROOT / "research" / "validation", ROOT / "research", ROOT):
    sys.path.insert(0, str(p))

import numpy as np
import pandas as pd

REPORT = ROOT / "reports" / "final-e8-2026-11-26.json"
OUT = HERE / "data.json"
START = 10_000


def run_bot():
    import final_e8 as F                             # sets the account size and loads the same modules
    D, V = F.D, F.V
    fr = V.b.frames(); t = V.trades(fr); win, ev = D.windows(fr["1h"])
    news = {w for w in win if not (w.hour in (20, 21) and w.dayofweek <= 3)
            or any(abs((w - e).total_seconds()) <= 3 * 3600 for e in ev)}
    kw = dict(V.KW, mix_risk=0.003, gap_budget=0.015, derisk_at=news)
    p, mt, ck = V.S.run(t, fr, kw)
    return fr["1h"], p, ck, V.S.daily_table(ck)


def secs(ts):
    return (pd.to_datetime(pd.Series(ts)).astype("datetime64[s]").astype("int64")).tolist()


def pack_candles(h1):
    """Columnar + integer tenths: t as hour steps, close as a running delta, o/h/l as offsets from close."""
    t = np.array(secs(h1.index))
    c = np.round(h1.close.values * 10).astype(int)
    tenth = lambda col: (np.round(h1[col].values * 10).astype(int) - c).tolist()
    return dict(t0=int(t[0]), dt=(np.diff(t) // 3600).astype(int).tolist(), c0=int(c[0]),
                dc=np.diff(c).tolist(), o=tenth("open"), h=tenth("high"), l=tenth("low"))


def main():
    h1, p, ck, d = run_bot()
    p = p.sort_values(["t_in", "tid"]).reset_index(drop=True)
    strategies = sorted(p.strategy.unique()); exits = sorted(p.exit.unique())
    # Effective exit price after costs: the price move that gives this P&L (1 lot = 100 oz).
    exit_px = p.entry + p.side * p.pnl / (p.lot * 100)
    trades = [[int(r.tid), a, b, int(r.side), strategies.index(r.strategy), round(float(r.entry), 2),
               round(float(x), 2), round(float(r.r_real), 3), round(float(r.pnl), 4), exits.index(r.exit), float(r.lot)]
              for r, a, b, x in zip(p.itertuples(), secs(p.t_in), secs(p.t_close), exit_px)]

    p["m"] = pd.to_datetime(p.t_close).dt.to_period("M")
    months = [dict(month=str(m), trades=len(g), wins=int((g.pnl > 0).sum()), losses=int((g.pnl <= 0).sum()),
                   profit=round(float(g.pnl.sum()))) for m, g in p.groupby("m")]
    eq = ck["eq"].values
    peak = np.maximum.accumulate(np.r_[START, eq])
    dd = float((peak[1:] - eq).max())
    msum = pd.Series([m["profit"] for m in months])
    stats = dict(trades=len(p), wins=int((p.pnl > 0).sum()), win_pct=round(float((p.pnl > 0).mean() * 100), 1),
                 net_usd=round(float(p.pnl.sum())), worst_day=round(float(d.low.min())),
                 max_drop_usd=round(dd), max_drop_pct=round(dd / START * 100, 2), lowest_equity=round(float(eq.min())),
                 positive_months=f"{int((msum > 0).sum())}/{len(msum)}", start_usd=START)

    rep = json.loads(REPORT.read_text())
    for k_mine, k_rep in (("trades", "trades"), ("net_usd", "net_usd"), ("worst_day", "worst_day"),
                          ("lowest_equity", "lowest_equity"), ("positive_months", "positive_months")):
        if stats[k_mine] != rep[k_rep]:
            sys.exit(f"STOP: {k_mine}={stats[k_mine]} but the report says {rep[k_rep]}")
    if months != rep["months"]:
        sys.exit("STOP: monthly table differs from the report")

    data = dict(meta=dict(name=rep["name"], report=REPORT.name, generated=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                          first=str(h1.index[0])[:10], last=str(h1.index[-1])[:10], symbol="GC=F (COMEX gold futures)",
                          tz="UTC", candles_from="Yahoo Finance hourly candles via yfinance (cached)"),
                strategies=strategies, exits=exits,
                trade_cols=["id", "t_in", "t_out", "side", "strategy", "entry", "exit", "r", "pnl", "exit_reason", "lot"],
                trades=trades, months=months, stats=stats, candles=pack_candles(h1), demo=[])
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(f"wrote {OUT.name}: {len(h1)} candles, {len(trades)} trades, {len(months)} months, "
          f"net ${stats['net_usd']}, {OUT.stat().st_size // 1024} KB (matches {REPORT.name})")


if __name__ == "__main__":
    main()

"""A281: Alpha Brain, a machine-learning stock picker built the way quant funds do it (Akhil 14 Nov 2026).

Akhil: "make a world-class quantitative trading brain, all markets and charts, fundamental and technical,
best trading methods, at least 25 strategies, that makes money."

What the big quant shops publish (Microsoft Qlib's Alpha158 + LightGBM, the Medallion papers) points one way:
not one clever rule, but MANY weak signals combined by a model that ranks every stock against every other
stock, retrained on a schedule, judged only on years it never saw. This script does that for India.

- Universe: 47 Nifty 50 stocks (today's members found on Yahoo; survivorship bias FLATTERS results) + 5 NSE
  ETFs (Nifty, Bank Nifty, Next 50, gold, Nasdaq 100). Daily closes 2009-2026.
- 38 inputs per asset per week:
  * 25 strategy signals (the strategies become inputs): momentum 5/10/21/63/126/252 days, 12-1 momentum,
    distance from 20/50/100/200-day averages, 50/200 cross, Turtle 20/55 breakout, RSI 2/14, Bollinger z,
    52-week-high ratio, 63-day drawdown, MACD, short-term reversal, momentum consistency (share of up days),
    trend strength (63-day slope / risk), 21-day high-low position.
  * risk: volatility 21/63 days, beta to Nifty, downside volatility.
  * market and macro (same for every asset, the model learns when each signal works): Nifty above its
    200-day average, Nifty 63-day momentum, India VIX percentile (fear), USD/INR 63-day change (rupee),
    India CPI inflation (FRED, lagged 2 months), market breadth (share of the 52 assets above their 200-day).
  * Fundamentals: no free point-in-time history of Indian company financials exists, so none are used in the
    backtest (using today's numbers on 2015 prices would be look-ahead). Noted, not faked.
- Inputs are ranked across assets each week (Qlib's CSRankNorm). Target: next 21 trading days' return, ranked.
- Model: gradient-boosted trees (scikit-learn HistGradientBoosting, the same algorithm family as LightGBM)
  averaged with a ridge regression (ensemble). Retrained every January on all earlier data, with a 21-day gap
  (embargo) so no training label overlaps the test year. First test year 2019.
- Trading: Rs 10,000 account share by share (A273 engine: whole shares, every NSE delivery charge, Rs 15.34 DP
  per sell, 0.1% slippage, idle cash 4.7%/yr). Buy the top K predicted assets, equal money.

Run: python3 07-trading/research/a281_alpha_brain.py   (data cached in 07-trading/data/a273, not in git)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a273_multi_strategy as A  # noqa: E402  (data, Rs 10k share engine, baselines)

HORIZON, EMBARGO, FIRST_TEST = 21, 21, 2019
CONFIGS = [("M", 5), ("M", 3), ("W", 5), ("W", 3)]     # declared before the run; M5 is the main line


def rsi(s: pd.DataFrame, n: int) -> pd.DataFrame:
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d).clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def asset_features(px: pd.DataFrame, nifty: pd.Series) -> dict[str, pd.DataFrame]:
    r = px.pct_change(fill_method=None)
    f = {}
    for n in (5, 10, 21, 63, 126, 252):
        f[f"mom{n}"] = px / px.shift(n) - 1
    f["mom12_1"] = px.shift(21) / px.shift(252) - 1
    for n in (20, 50, 100, 200):
        f[f"ma_gap{n}"] = px / px.rolling(n).mean() - 1
    f["cross50_200"] = (px.rolling(50).mean() > px.rolling(200).mean()).astype(float)
    f["turtle20"] = (px >= px.rolling(20).max()).astype(float)
    f["turtle55"] = (px >= px.rolling(55).max()).astype(float)
    f["rsi2"], f["rsi14"] = rsi(px, 2), rsi(px, 14)
    f["boll_z"] = (px - px.rolling(20).mean()) / px.rolling(20).std()
    f["high52"] = px / px.rolling(252).max()
    f["dd63"] = px / px.rolling(63).max() - 1
    macd = px.ewm(span=12, adjust=False).mean() - px.ewm(span=26, adjust=False).mean()
    f["macd"] = (macd - macd.ewm(span=9, adjust=False).mean()) / px
    f["rev5"] = -(px / px.shift(5) - 1)
    f["consist63"] = (r > 0).rolling(63).mean()
    f["trend_strength"] = (px / px.shift(63) - 1) / (r.rolling(63).std() * np.sqrt(63))
    lo, hi = px.rolling(21).min(), px.rolling(21).max()
    f["range_pos21"] = (px - lo) / (hi - lo)
    f["vol21"], f["vol63"] = r.rolling(21).std(), r.rolling(63).std()
    f["downvol63"] = r.clip(upper=0).rolling(63).std()
    nr = nifty.pct_change().reindex(px.index)
    f["beta126"] = r.rolling(126).cov(nr).div(nr.rolling(126).var(), axis=0)
    return f


def market_features(px, nifty, vix, inr, cpi) -> pd.DataFrame:
    idx = px.index
    n = nifty.reindex(idx).ffill()
    m = pd.DataFrame(index=idx)
    m["mkt_trend"] = (n > n.rolling(200).mean()).astype(float)
    m["mkt_mom63"] = n / n.shift(63) - 1
    v = vix.reindex(idx).ffill()
    m["vix_pct"] = v.rolling(252, min_periods=100).rank(pct=True)
    u = inr.reindex(idx).ffill()
    m["inr63"] = u / u.shift(63) - 1
    c = cpi.copy()
    c.index = c.index + pd.Timedelta(days=60)                      # public about two months later
    yoy = (c / c.shift(12) - 1).reindex(idx, method="ffill")
    m["cpi_yoy"] = yoy
    m["breadth200"] = (px > px.rolling(200).mean()).mean(axis=1)
    return m


def panel(px, nifty, vix, inr, cpi, dates) -> pd.DataFrame:
    af = asset_features(px, nifty)
    mf = market_features(px, nifty, vix, inr, cpi)
    fwd = px.shift(-HORIZON) / px - 1
    rows = []
    for d in dates:
        x = pd.DataFrame({k: v.loc[d] for k, v in af.items()})
        x = x[px.loc[d].notna() & x["mom252"].notna()]
        if len(x) < 10:
            continue
        x = x.rank(pct=True)                                       # cross-sectional rank (CSRankNorm)
        for k in mf:
            x[k] = mf.at[d, k]
        x["y"] = fwd.loc[d, x.index].rank(pct=True)
        x["fwd"] = fwd.loc[d, x.index]
        x["date"], x["asset"] = d, x.index
        rows.append(x.reset_index(drop=True))
    return pd.concat(rows, ignore_index=True)


def walk_forward(pn: pd.DataFrame) -> pd.DataFrame:
    feats = [c for c in pn if c not in ("y", "fwd", "date", "asset")]
    out = []
    for yr in range(FIRST_TEST, pn.date.dt.year.max() + 1):
        start = pd.Timestamp(f"{yr}-01-01")
        train = pn[(pn.date < start - pd.Timedelta(days=EMBARGO * 7 // 5 + 3)) & pn.y.notna()]
        test = pn[pn.date.dt.year == yr]
        if test.empty:
            continue
        X, y = train[feats].fillna(0.5), train.y
        gb = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                           min_samples_leaf=200, l2_regularization=1.0, random_state=0)
        gb.fit(X, y)
        rd = Ridge(alpha=10.0).fit(X, y)
        Xt = test[feats].fillna(0.5)
        t = test[["date", "asset", "y", "fwd"]].copy()
        t["p_gb"], t["p_ridge"] = gb.predict(Xt), rd.predict(Xt)
        t["score"] = (t.groupby("date").p_gb.rank(pct=True) + t.groupby("date").p_ridge.rank(pct=True)) / 2
        out.append(t)
    return pd.concat(out, ignore_index=True)


def rank_ic(pred: pd.DataFrame, col: str = "score") -> tuple[float, float]:
    ic = pred.dropna(subset=["y"]).groupby("date").apply(lambda g: g[col].corr(g.y, method="spearman"))
    return float(ic.mean()), float(ic.mean() / ic.std())


def targets_from(pred: pd.DataFrame, px: pd.DataFrame, dates, k: int, trend: pd.Series | None = None) -> dict:
    """trend: if given, hold cash (liquid ETF rate) when Nifty is below its 200-day average (risk filter)."""
    out = {}
    by = {d: g for d, g in pred.groupby("date")}
    for d in dates:
        g = by.get(d)
        if g is None:
            continue
        if trend is not None and not bool(trend.get(d, False)):
            out[d] = {}
            continue
        g = g.sort_values("score", ascending=False)
        pick = [a for a in g.asset if px.at[d, a] * 1.01 <= A.CAPITAL / k][:k]   # whole shares affordable
        out[d] = {a: 1.0 / k for a in pick}
    return out


def load():
    stocks = A.repair(A.yahoo([f"{s}.NS" for s in A.NIFTY50], "nifty50"))
    stocks.columns = [c.replace(".NS", "") for c in stocks.columns]
    etfs = A.repair(A.yahoo([f"{e}.NS" for e in A.ETFS], "etfs"))
    etfs.columns = [c.replace(".NS", "") for c in etfs.columns]
    mac = A.yahoo(["^NSEI", "^INDIAVIX", "USDINR=X"], "macro")
    nifty, vix, inr = mac["^NSEI"].dropna(), mac["^INDIAVIX"].dropna(), mac["USDINR=X"].dropna()
    cpi = A.fred("INDCPIALLMINMEI")
    px = pd.concat([stocks, etfs], axis=1, sort=True)
    px = px[px.index >= "2009-06-01"].ffill(limit=5)
    return px, nifty, vix, inr, cpi


def paper(out: Path, k: int = 5) -> str:
    """PAPER ONLY: train on every labelled week, score the latest close, write the top-k picks.
    The ledger only changes on the last trading day of a month (the main line rebalances monthly)."""
    import json
    from datetime import datetime, timedelta, timezone
    px, nifty, vix, inr, cpi = load()
    dates = A.rebalance_days(px.index, "W")
    if dates[-1] != px.index[-1]:
        dates.append(px.index[-1])
    pn = panel(px, nifty, vix, inr, cpi, dates)
    feats = [c for c in pn if c not in ("y", "fwd", "date", "asset")]
    last = px.index[-1]
    train = pn[(pn.date < last - pd.Timedelta(days=35)) & pn.y.notna()]
    test = pn[pn.date == last]
    X, Xt = train[feats].fillna(0.5), test[feats].fillna(0.5)
    gb = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                       min_samples_leaf=200, l2_regularization=1.0, random_state=0).fit(X, train.y)
    rd = Ridge(alpha=10.0).fit(X, train.y)
    t = test[["date", "asset"]].copy()
    t["score"] = (pd.Series(gb.predict(Xt)).rank(pct=True).values + pd.Series(rd.predict(Xt)).rank(pct=True).values) / 2
    picks = targets_from(t, px, [last], k).get(last, {})
    month_end = (last + pd.offsets.BDay(1)).month != last.month      # last weekday of the month
    out.mkdir(parents=True, exist_ok=True)
    state = {"date": str(last.date()), "paper_only": True, "rebalance_day": bool(month_end),
             "run_ist": datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M"),
             "picks": {a: round(w * A.CAPITAL) for a, w in picks.items()},
             "top10": t.sort_values("score", ascending=False).head(10)[["asset", "score"]].round(3).values.tolist()}
    (out / "state.json").write_text(json.dumps(state, indent=1))
    if month_end:
        with (out / "rebalances.csv").open("a") as f:
            f.write(f"{state['date']}," + ";".join(f"{a}:{v}" for a, v in state["picks"].items()) + "\n")
    return f"Alpha Brain paper {state['date']} (PAPER ONLY): picks " + ", ".join(state["picks"]) + \
        (" [month-end rebalance logged]" if month_end else " [next rebalance at month end]")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--paper":
        print(paper(Path(sys.argv[2])))
        return
    px, nifty, vix, inr, cpi = load()
    print(f"assets {px.shape[1]}, days {len(px)}, {px.index[0].date()} to {px.index[-1].date()}")

    weekly = A.rebalance_days(px.index, "W")
    pn = panel(px, nifty, vix, inr, cpi, weekly)
    pred = walk_forward(pn)
    ic_all, icir_all = rank_ic(pred)
    ic_gb, _ = rank_ic(pred, "p_gb")
    ic_rd, _ = rank_ic(pred, "p_ridge")
    print(f"rank IC 2019+: ensemble {ic_all:.3f} (ICIR {icir_all:.2f}), trees {ic_gb:.3f}, ridge {ic_rd:.3f}")

    test_px = px[px.index >= f"{FIRST_TEST}-01-01"]
    monthly = [d for d in A.rebalance_days(test_px.index, "M")]
    weekly_t = [d for d in weekly if d >= test_px.index[0]]
    rows = []
    for freq, k in CONFIGS:
        rb = monthly if freq == "M" else weekly_t
        v, n = A.simulate(test_px, targets_from(pred, px, rb, k))
        rows.append({"line": f"Alpha Brain, top {k}, {'monthly' if freq == 'M' else 'weekly'}", **A.stats(v, n),
                     "end_value": v.iloc[-1]})
    rb_m = A.rebalance_days(test_px.index, "M")
    tr200 = A.trend_on(nifty)          # added after the first run (one extra trial, T0032)
    v, n = A.simulate(test_px, targets_from(pred, px, monthly, 5, tr200))
    rows.append({"line": "Alpha Brain, top 5, monthly + Nifty 200-day risk filter", **A.stats(v, n),
                 "end_value": v.iloc[-1]})
    v, n = A.simulate(test_px, A.strat_baseline(test_px, nifty, rb_m))
    rows.append({"line": "Current bot: Nifty trend + gold (A273 engine)", **A.stats(v, n), "end_value": v.iloc[-1]})
    v, n = A.simulate(test_px, A.strat_stock_momentum(px, nifty, rb_m, n=5, look=252, skip=21, filt=True))
    rows.append({"line": "Top 5 Nifty 50 by 12-1 momentum (A273 best stock rule)", **A.stats(v, n), "end_value": v.iloc[-1]})
    v, n = A.simulate(test_px, {d: {"NIFTYBEES": 1.0} for d in rb_m[:1]})
    rows.append({"line": "Buy and hold NIFTYBEES", **A.stats(v, n), "end_value": v.iloc[-1]})
    res = pd.DataFrame(rows)

    # what the model leaned on (permutation-free proxy: ridge weights on ranked inputs)
    feats = [c for c in pn if c not in ("y", "fwd", "date", "asset")]
    tr = pn[pn.date < pd.Timestamp("2026-01-01") - pd.Timedelta(days=35)].dropna(subset=["y"])
    coef = pd.Series(Ridge(alpha=10.0).fit(tr[feats].fillna(0.5), tr.y).coef_, index=feats)
    yearly = pred.dropna(subset=["y"]).groupby(pred.date.dt.year).apply(
        lambda g: g.groupby("date").apply(lambda x: x.score.corr(x.y, method="spearman")).mean())

    res.to_csv(HERE / "a281_results.csv", index=False, float_format="%.4f")
    coef.sort_values().to_csv(HERE / "a281_ridge_weights.csv", header=["weight"], float_format="%.5f")
    pd.set_option("display.width", 220)
    print(res.round(3).to_string(index=False))
    print("rank IC by year:", yearly.round(3).to_dict())
    print("strongest inputs (+):", coef.sort_values().tail(6).round(4).to_dict())
    print("strongest inputs (-):", coef.sort_values().head(6).round(4).to_dict())


if __name__ == "__main__":
    main()

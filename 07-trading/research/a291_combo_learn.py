"""A291: learn from the successful trades of Alpha Brain, the current bot and Nifty, then re-apply (Akhil 14 Nov 2026:
"combine successful trades from alpha brain and current bot and nifty, analyse the success trades, reapply the same
strategy and give me results again").

The trap: if you study winning trades and test on the SAME years, any rule looks great (hindsight). So:
- LEARN only from trades in 2011-2018.
- APPLY the learned rule untouched to 2019 - 13 Nov 2026.
- For contrast, also show the hindsight version (learned on all years) and mark it as not usable.

Trades: every month each candidate is a 1-month holding, entered at the month-end close and sold at the next month-end
(exactly how the monthly bots trade). Candidates = what the three strategies would buy:
  Alpha Brain (top 10 Nifty 50 stocks by 12-1 momentum), current bot (NIFTYBEES when Nifty trend is up, GOLDBEES),
  Nifty buy-and-hold (NIFTYBEES), plus MON100 (Nasdaq ETF, the rotate leg of Alpha Brain v2).
Success = the month's return beats 1% (round-trip charges + DP on a Rs 2,000 slice) -> a profitable trade.
Features at entry (no future data): momentum 1/3/6/12 months and 12-1, momentum rank, volatility, distance from the
20/50/200-day averages, 52-week-high ratio, RSI(14), Nifty above its 200-day, India VIX percentile, is it an ETF.
Learner: a small decision tree (depth 3, at least 40 trades per leaf) so the rules are readable, not a black box.
Re-applied strategy ("Combo"): each month buy up to 5 candidates the tree rates >= 55% likely to win, equal money,
rest in the liquid fund. Rs 10,000 share engine with every NSE charge (A273).

Run: python3 07-trading/research/a291_combo_learn.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a273_multi_strategy as A  # noqa: E402
import a289_alpha_brain_v2 as V  # noqa: E402

TRAIN_END, TEST_START = "2018-12-31", "2019-01-01"
COST = 0.01
THRESH, MAX_POS = 0.55, 5
ETFS = ["NIFTYBEES", "GOLDBEES", "MON100"]


def rsi(px, n=14):
    d = px.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d).clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def feature_panels(px, nifty, vix):
    r = px.pct_change(fill_method=None)
    f = {f"mom{m}m": px / px.shift(21 * m) - 1 for m in (1, 3, 6, 12)}
    f["mom12_1"] = px.shift(21) / px.shift(252) - 1
    f["vol"] = r.rolling(126).std() * np.sqrt(252)
    for n in (20, 50, 200):
        f[f"gap{n}"] = px / px.rolling(n).mean() - 1
    f["high52"] = px / px.rolling(252).max()
    f["rsi14"] = rsi(px)
    n = nifty.reindex(px.index).ffill()
    mkt = pd.DataFrame({"nifty_up": (n > n.rolling(200).mean()).astype(float),
                        "vix_pct": vix.reindex(px.index).ffill().rolling(252, min_periods=100).rank(pct=True)})
    return f, mkt


def candidates(px, f, nifty_up, d):
    stocks = [s for s in A.NIFTY50 if s in px]
    m = f["mom12_1"].loc[d, stocks].dropna()
    m = m[[px.at[d, s] * 1.01 <= A.CAPITAL / MAX_POS for s in m.index]]       # affordable whole shares
    top = list(m.sort_values(ascending=False).index[:10])                       # Alpha Brain's pool
    c = {s: "alpha_brain" for s in top}
    c["NIFTYBEES"] = "bot_nifty_trend" if nifty_up.get(d, False) else "nifty_hold"
    c["GOLDBEES"] = "bot_gold"
    c["MON100"] = "alpha_rotate_nasdaq"
    return c


def build_trades(px, f, mkt, rb, nifty_up):
    rows = []
    rank = f["mom12_1"][[s for s in A.NIFTY50 if s in px]].rank(axis=1, pct=True)
    for d, nxt in zip(rb[:-1], rb[1:]):
        for a, src in candidates(px, f, nifty_up, d).items():
            p0, p1 = px.at[d, a], px.at[nxt, a]
            if not (np.isfinite(p0) and np.isfinite(p1)):
                continue
            row = {"date": d, "asset": a, "source": src, "ret": p1 / p0 - 1}
            for k, v in f.items():
                row[k] = v.at[d, a]
            row["mom_rank"] = rank.at[d, a] if a in rank else np.nan
            row["nifty_up"], row["vix_pct"] = mkt.at[d, "nifty_up"], mkt.at[d, "vix_pct"]
            row["is_etf"] = float(a in ETFS)
            rows.append(row)
    t = pd.DataFrame(rows)
    t["win"] = (t.ret > COST).astype(int)
    return t


FEATS = ["mom1m", "mom3m", "mom6m", "mom12m", "mom12_1", "mom_rank", "vol", "gap20", "gap50", "gap200", "high52",
         "rsi14", "nifty_up", "vix_pct", "is_etf"]


def fit(tr):
    X = tr[FEATS].fillna(tr[FEATS].median())
    return DecisionTreeClassifier(max_depth=3, min_samples_leaf=40, random_state=0).fit(X, tr.win), tr[FEATS].median()


def combo_targets(px, f, mkt, rb, nifty_up, model, med):
    out = {}
    for d in rb:
        c = candidates(px, f, nifty_up, d)
        X = pd.DataFrame([{**{k: f[k].at[d, a] for k in f}, "mom_rank": np.nan, "nifty_up": mkt.at[d, "nifty_up"],
                           "vix_pct": mkt.at[d, "vix_pct"], "is_etf": float(a in ETFS)} for a in c], index=list(c))
        stocks = [s for s in A.NIFTY50 if s in px]
        rk = f["mom12_1"].loc[d, stocks].rank(pct=True)
        X["mom_rank"] = [rk.get(a, np.nan) for a in X.index]
        p = pd.Series(model.predict_proba(X[FEATS].fillna(med))[:, 1], index=X.index)
        keep = p[p >= THRESH].sort_values(ascending=False).index[:MAX_POS]
        out[d] = {a: 1.0 / MAX_POS for a in keep}
    return out


def window(px, start, end=None):
    w = px.loc[start:end] if end else px.loc[start:]
    rb = A.rebalance_days(w.index, "M")
    if rb[0] != w.index[0]:
        rb = [w.index[0]] + rb
    return w, [d for d in rb if d != w.index[-1]]


def main():
    px, nifty = V.load()
    vix = A.yahoo(["^NSEI", "^INDIAVIX", "USDINR=X"], "macro")["^INDIAVIX"].dropna()
    f, mkt = feature_panels(px, nifty, vix)
    nifty_up = mkt["nifty_up"].astype(bool)
    rb_all = A.rebalance_days(px.loc["2010-06-01":].index, "M")
    trades = build_trades(px, f, mkt, rb_all, nifty_up)
    tr, te = trades[trades.date <= TRAIN_END], trades[trades.date >= TEST_START]
    trades.to_csv(HERE / "a291_trades.csv", index=False, float_format="%.4f")

    # 1. what did the successful trades have in common? (train years only)
    print(f"trades: train {len(tr)}, test {len(te)}; train success rate {tr.win.mean():.1%}")
    by_src = tr.groupby("source").agg(trades=("win", "size"), success=("win", "mean"), avg_month=("ret", "mean"))
    print(by_src.round(3).to_string())
    buckets = []
    for k in ["mom12_1", "mom_rank", "gap200", "high52", "vol", "rsi14", "vix_pct"]:
        q = pd.qcut(tr[k], 4, duplicates="drop")
        g = tr.groupby(q, observed=True).agg(success=("win", "mean"), avg_month=("ret", "mean"), n=("win", "size"))
        g.index = [f"{k} {i}" for i in g.index.astype(str)]
        buckets.append(g)
    g = tr.groupby("nifty_up").agg(success=("win", "mean"), avg_month=("ret", "mean"), n=("win", "size"))
    g.index = [f"nifty_up={int(i)}" for i in g.index]
    buckets.append(g)
    bk = pd.concat(buckets)
    bk.to_csv(HERE / "a291_success_buckets.csv", float_format="%.4f")
    print(bk.round(3).to_string())

    model, med = fit(tr)
    rules = export_text(model, feature_names=FEATS, decimals=3)
    (HERE / "a291_rules.txt").write_text(rules)
    print(rules)
    p_te = model.predict_proba(te[FEATS].fillna(med))[:, 1]
    picked = te[p_te >= THRESH]
    print(f"test months: trades the rule would take {len(picked)} of {len(te)}; success {picked.win.mean():.1%} vs all "
          f"{te.win.mean():.1%}; avg month {picked.ret.mean():.3%} vs {te.ret.mean():.3%}")

    # 2. re-apply on 2019-2026 with the Rs 10k engine, against the three originals
    w, rb = window(px, TEST_START)
    cfg_ab = dict(univ="N50", score="m12_1", k=5, buffer=1, regime="rotate", mix=1.0)
    sc = V.scores(px)
    up = nifty_up
    res = {}
    res["Combo (learned on 2011-18, applied 2019-26)"] = A.simulate(w, combo_targets(px, f, mkt, rb, nifty_up, model, med))
    res["Alpha Brain v2 (Nifty 50 version)"] = A.simulate(w, V.targets(px, sc, up, rb, cfg_ab))
    res["Current bot: Nifty trend + gold"] = A.simulate(w, A.strat_baseline(w, nifty, rb))
    res["Buy and hold Nifty"] = A.simulate(w, {rb[0]: {"NIFTYBEES": 1.0}})
    hind, hmed = fit(trades)  # hindsight: learned on ALL years incl. the test years
    res["Hindsight combo (learned on ALL years; NOT usable)"] = A.simulate(w, combo_targets(px, f, mkt, rb, nifty_up, hind, hmed))
    rows = [{"line": k, **A.stats(v, n), "end_rs": v.iloc[-1]} for k, (v, n) in res.items()]
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "a291_results.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 220)
    print(out.round(3).to_string(index=False))

    v = res["Combo (learned on 2011-18, applied 2019-26)"][0]
    yr = pd.concat([pd.Series([A.CAPITAL], index=[2018]), v.groupby(v.index.year).last()]).pct_change().dropna()
    print("Combo year by year (%):", (yr * 100).round(1).to_dict())
    roll = []
    for s in sorted({w.index[w.index >= pd.Timestamp(f"{y}-{m:02d}-01")][0] for y in range(2019, 2026) for m in range(1, 13)}):
        e = s + pd.DateOffset(months=12)
        if e > px.index[-1]:
            continue
        ww, rr = window(px, s, e)
        vv, _ = A.simulate(ww, combo_targets(px, f, mkt, rr, nifty_up, model, med))
        vb, _ = A.simulate(ww, A.strat_baseline(ww, nifty, rr))
        roll.append({"start": s.date(), "combo": vv.iloc[-1] / A.CAPITAL - 1, "bot": vb.iloc[-1] / A.CAPITAL - 1})
    roll = pd.DataFrame(roll)
    roll.to_csv(HERE / "a291_rolling.csv", index=False, float_format="%.4f")
    print(f"12-month starts {len(roll)}: combo median {roll.combo.median():.3f}, lost {100 * (roll.combo < 0).mean():.0f}%, "
          f">=20% {100 * (roll.combo >= 0.2).mean():.0f}%, beat bot {100 * (roll.combo > roll.bot).mean():.0f}%; "
          f"bot median {roll.bot.median():.3f}, lost {100 * (roll.bot < 0).mean():.0f}%")
    w26, rb26 = window(px, "2026-01-01")
    v26, _ = A.simulate(w26, combo_targets(px, f, mkt, rb26, nifty_up, model, med))
    d26 = pd.DataFrame({"value": v26.round(0)})
    d26["day_rs"] = d26.value.diff().fillna(d26.value.iloc[0] - A.CAPITAL)
    d26.to_csv(HERE / "a291_daily_2026.csv")
    print(f"Combo 2026 so far: Rs {v26.iloc[-1]:.0f}, worst fall {100 * (v26 / v26.cummax() - 1).min():.1f}%")
    last = px.index[-1]
    print("Combo picks at the latest close:", combo_targets(px, f, mkt, [last], nifty_up, model, med)[last])


if __name__ == "__main__":
    main()

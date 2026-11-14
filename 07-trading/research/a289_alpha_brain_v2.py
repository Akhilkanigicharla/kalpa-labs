"""A289: Alpha Brain v2, built to aim for 20% a year on Rs 10,000 (Akhil 14 Nov 2026: "just 20%, act as a
world-class quant").

Why this design (evidence, checked 14 Nov 2026):
- NSE's own momentum whitepaper: the Nifty200 Momentum 30 index returned 19.19% a year from Apr 2005 to Feb 2026,
  against 15.08% for its parent index. Momentum is the one factor with a 20%-a-year record in India.
- Antonacci's dual momentum (GEM): hold what is rising relative to the others AND rising in absolute terms, else a
  safe asset. It mostly cuts the big falls (2008: about -21% vs Nifty's -50%+ in Indian tests).
- Professional momentum books use a "buffer" (keep a holding until it falls well out of the top) to cut turnover,
  and risk-adjusted momentum scores (NSE's "normalised momentum score" = return / volatility over 6 and 12 months).

So v2 = a stock momentum sleeve (NSE-style score, monthly, buffer, market-trend switch) + an ETF dual-momentum sleeve
(Nifty, Bank, Next 50, PSU banks, infra, CPSE, gold, Nasdaq 100, Hang Seng; else liquid fund). One small grid of 64
settings is fixed BEFORE any test, chosen ONLY on 2011-2018, then run untouched on 2019 - 13 Nov 2026.

Honest limits (printed in the report):
- Stock lists are TODAY's Nifty 50 / Nifty 100 (survivorship bias: flatters stock results, more so for Nifty 100).
  ETF sleeve has no such bias.
- Rs 10,000 means whole shares: a stock above Rs 2,000 (top 5) or Rs 3,333 (top 3) cannot be bought; this is
  enforced, as in real life.

Run: python3 07-trading/research/a289_alpha_brain_v2.py   (data cached in 07-trading/data/a273, not in git)
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a273_multi_strategy as A  # noqa: E402  (Rs 10k share engine with every NSE charge)

TRAIN = ("2011-01-01", "2018-12-31")
TEST = ("2019-01-01", None)
NEXT50 = ("ABB ADANIENSOL ADANIGREEN ADANIPOWER AMBUJACEM DMART BAJAJHLDNG BANKBARODA BPCL BOSCHLTD BRITANNIA CGPOWER "
          "CANBK CHOLAFIN CUMMINSIND DLF DIVISLAB GAIL GODREJCP HDFCAMC HAL HINDZINC POWERINDIA HYUNDAI IOC IRFC "
          "JINDALSTEL LTM MAZDOCK MUTHOOTFIN PIDILITIND POLYCAB PFC PNB MOTHERSON ENRIN SIEMENS SOLARINDS TVSMOTOR "
          "TATACAP TMCV TATAPOWER TORNTPHARM UNIONBANK VBL VAML VEDL IDEA WIPRO ZYDUSLIFE").split()
ETF_SLEEVE = ["NIFTYBEES", "JUNIORBEES", "BANKBEES", "PSUBNKBEES", "INFRABEES", "CPSEETF", "GOLDBEES", "MON100", "HNGSNGBEES"]
SAFE = ["GOLDBEES", "MON100"]


def load():
    s50 = A.repair(A.yahoo([f"{s}.NS" for s in A.NIFTY50], "nifty50"))
    s50.columns = [c.replace(".NS", "") for c in s50.columns]
    etfs = A.repair(A.yahoo([f"{e}.NS" for e in A.ETFS], "etfs"))
    etfs.columns = [c.replace(".NS", "") for c in etfs.columns]
    extra = A.repair(pd.read_parquet(A.CACHE / "next50_etfs.parquet"))
    mac = A.yahoo(["^NSEI", "^INDIAVIX", "USDINR=X"], "macro")
    px = pd.concat([s50, etfs, extra.drop(columns=[c for c in extra if c in s50 or c in etfs])], axis=1, sort=True)
    px = px[px.index >= "2009-06-01"].ffill(limit=5)
    return px, mac["^NSEI"].dropna()


def scores(px: pd.DataFrame) -> dict[str, pd.DataFrame]:
    r = px.pct_change(fill_method=None)
    vol = r.rolling(252, min_periods=200).std() * np.sqrt(252)
    m6, m12 = px / px.shift(126) - 1, px / px.shift(252) - 1
    z = lambda x: x.sub(x.mean(axis=1), axis=0).div(x.std(axis=1), axis=0)
    return {"m12_1": px.shift(21) / px.shift(252) - 1,
            "nse": (z(m6 / vol) + z(m12 / vol)) / 2,          # NSE's normalised momentum score (6 and 12 months)
            "m12": m12, "blend": (px / px.shift(63) - 1 + m6 + m12) / 3}


def stock_sleeve(px, sc, nifty_up, d, universe, score, k, buffer, regime, held):
    """Weights for the stock sleeve on date d (sum 1 or less)."""
    if not nifty_up.get(d, False):
        if regime == "cash":
            return {}
        b = sc["blend"].loc[d, SAFE].dropna()                  # market weak: best of gold / Nasdaq if rising
        b = b[b > (1 + A.CASH_RATE) ** 0.5 - 1]
        return {b.idxmax(): 1.0} if len(b) else {}
    s = sc[score].loc[d, universe].dropna()
    s = s[(sc["m12"].loc[d, s.index] > 0)]                     # absolute momentum: must be up over 12 months
    s = s[[px.at[d, c] * 1.01 <= A.CAPITAL / k for c in s.index]]   # whole shares must be affordable
    ranked = list(s.sort_values(ascending=False).index)
    keep = [h for h in held if h in ranked[: 2 * k]] if buffer else []
    pick = (keep + [c for c in ranked if c not in keep])[:k]
    return {c: 1.0 / k for c in pick}


def etf_sleeve(sc, d):
    b = sc["blend"].loc[d, [e for e in ETF_SLEEVE if e in sc["blend"]]].dropna()
    b = b[b > ((1 + A.CASH_RATE) ** 0.5 - 1)].sort_values(ascending=False)  # beat the liquid fund
    top = list(b.index[:2])
    return {e: 1.0 / 2 for e in top}


def targets(px, sc, nifty_up, rb, cfg):
    universe = [c for c in (A.NIFTY50 + (NEXT50 if cfg["univ"] == "N100" else [])) if c in px]
    out, held = {}, []
    for d in rb:
        w = {}
        st = stock_sleeve(px, sc, nifty_up, d, universe, cfg["score"], cfg["k"], cfg["buffer"], cfg["regime"], held)
        held = [c for c in st if c in universe]
        for c, x in st.items():
            w[c] = w.get(c, 0) + x * cfg["mix"]
        if cfg["mix"] < 1:
            for c, x in etf_sleeve(sc, d).items():
                w[c] = w.get(c, 0) + x * (1 - cfg["mix"])
        out[d] = w
    return out


GRID = [dict(univ=u, score=s, k=k, buffer=b, regime=g, mix=m) for u, s, k, b, g, m in itertools.product(
    ["N50", "N100"], ["m12_1", "nse"], [3, 5], [0, 1], ["cash", "rotate"], [1.0, 0.5])]


def run(px, sc, nifty_up, cfg, start, end=None):
    w = px.loc[start:end] if end else px.loc[start:]
    rb = A.rebalance_days(w.index, "M")
    if rb[0] != w.index[0]:
        rb = [w.index[0]] + rb
    rb = [d for d in rb if d != w.index[-1]]
    v, n = A.simulate(w, targets(px, sc, nifty_up, rb, cfg))
    return v, n


def main():
    px, nifty = load()
    sc = scores(px)
    nifty_up = (nifty > nifty.rolling(200).mean()).reindex(px.index).ffill().fillna(False)
    print(f"assets {px.shape[1]}, {px.index[0].date()} to {px.index[-1].date()}, settings {len(GRID)}")
    rows = []
    for i, cfg in enumerate(GRID):
        vt, nt = run(px, sc, nifty_up, cfg, *TRAIN)
        vs, ns = run(px, sc, nifty_up, cfg, TEST[0])
        st, ss = A.stats(vt, nt), A.stats(vs, ns)
        rows.append({**cfg, **{f"train_{k}": v for k, v in st.items()}, **{f"test_{k}": v for k, v in ss.items()},
                     "test_end_rs": vs.iloc[-1]})
    res = pd.DataFrame(rows)
    ok = res[res.train_max_dd > -0.30]
    pick = ok.sort_values("train_cagr", ascending=False).iloc[0]     # chosen on 2011-2018 ONLY
    res["chosen"] = res.index == pick.name
    res.to_csv(HERE / "a289_grid.csv", index=False, float_format="%.4f")
    cfg = {k: pick[k] for k in ("univ", "score", "k", "buffer", "regime", "mix")}
    cfg["k"], cfg["buffer"], cfg["mix"] = int(cfg["k"]), int(cfg["buffer"]), float(cfg["mix"])
    print("CHOSEN on 2011-2018:", cfg)
    cols = ["univ", "score", "k", "buffer", "regime", "mix", "train_cagr", "train_max_dd", "test_cagr", "test_max_dd",
            "test_worst_year", "test_trades_per_yr", "test_end_rs"]
    pd.set_option("display.width", 250)
    print(res.sort_values("train_cagr", ascending=False)[cols].head(10).round(3).to_string(index=False))
    print("test CAGR across all 64 settings: median", round(res.test_cagr.median(), 3), "| share >= 20%:",
          round((res.test_cagr >= 0.20).mean(), 2), "| N50 only median", round(res[res.univ == "N50"].test_cagr.median(), 3))
    best_test = res.sort_values("test_cagr", ascending=False).iloc[0]
    print("best on TEST (hindsight, not usable):", best_test[cols[:6]].to_dict(), round(best_test.test_cagr, 3))

    # rolling 12-month starts + 2026 day by day for the chosen setting
    roll = []
    starts = sorted({px.index[px.index >= pd.Timestamp(f"{y}-{m:02d}-01")][0] for y in range(2019, 2027) for m in range(1, 13)
                     if (px.index >= pd.Timestamp(f"{y}-{m:02d}-01")).any()})
    for s in starts:
        e = s + pd.DateOffset(months=12)
        if e > px.index[-1]:
            continue
        v, _ = run(px, sc, nifty_up, cfg, s, e)
        roll.append({"start": s.date(), "ret": v.iloc[-1] / A.CAPITAL - 1})
    roll = pd.DataFrame(roll)
    roll.to_csv(HERE / "a289_rolling.csv", index=False, float_format="%.4f")
    print(f"12-month starts: {len(roll)}, median {roll.ret.median():.3f}, worst {roll.ret.min():.3f}, best {roll.ret.max():.3f},"
          f" lost money {100 * (roll.ret < 0).mean():.0f}%, >=20% {100 * (roll.ret >= 0.2).mean():.0f}%")
    v26, _ = run(px, sc, nifty_up, cfg, "2026-01-01")
    d26 = pd.DataFrame({"value": v26.round(0)}); d26["day_rs"] = d26.value.diff().fillna(d26.value.iloc[0] - A.CAPITAL)
    d26.to_csv(HERE / "a289_daily_2026.csv")
    print(f"2026 so far: Rs {v26.iloc[-1]:.0f} ({100 * (v26.iloc[-1] / A.CAPITAL - 1):.1f}%), worst fall "
          f"{100 * (v26 / v26.cummax() - 1).min():.1f}%")
    vs, ns = run(px, sc, nifty_up, cfg, TEST[0])
    yearly = vs.groupby(vs.index.year).last()
    yr = pd.concat([pd.Series([A.CAPITAL], index=[2018]), yearly]).pct_change().dropna()
    print("chosen, year by year (%):", (yr * 100).round(1).to_dict())
    tg = targets(px, sc, nifty_up, [px.index[-1]], cfg)[px.index[-1]]
    print("picks for the next month (latest close):", {k: round(v * A.CAPITAL) for k, v in tg.items()})


if __name__ == "__main__":
    main()

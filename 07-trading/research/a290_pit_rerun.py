"""A290: re-run A289 (Alpha Brain v2) on point-in-time Nifty 50 / Nifty 100 lists instead of today's lists.

Same 64 settings, same Rs 10,000 share engine with every NSE charge (a273), same rule: pick on 2011-2018 only
(max fall better than -30%, best return), then run untouched on 2019 to today. Each month the stock sleeve may only
choose from the stocks that were in the index at that month-end (07-trading/research/index_membership/, built from
NSE Indices press releases by src/index_membership.py).

Known limit (printed): Yahoo has no prices for companies that later delisted (mergers like HDFC, Cairn, Ranbaxy), so
those member-months cannot be picked. Coverage is reported year by year. A stock whose prices stop while held is sold
at its last price at the next monthly rebalance.

Run (cloud only, downloads Yahoo prices once into 07-trading/data/a273): python3 07-trading/research/a290_pit_rerun.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import a273_multi_strategy as A  # noqa: E402
import a289_alpha_brain_v2 as B  # noqa: E402
from src import index_membership as im  # noqa: E402

CFG_COLS = ["univ", "score", "k", "buffer", "regime", "mix"]


def load():
    mem = {ix: im.load_monthly(ix) for ix in ("N50", "N100")}
    ids = sorted({s for m in mem.values() for v in m.values() for s in v if not s.startswith("NAME:")})
    stocks = A.repair(A.yahoo([f"{s}.NS" for s in ids], "a290_pit_stocks"))
    etfs = A.repair(A.yahoo([f"{e}.NS" for e in B.ETF_SLEEVE], "a290_etfs"))
    mac = A.yahoo(["^NSEI"], "a290_macro")
    raw = pd.concat([stocks, etfs], axis=1, sort=True)
    raw.columns = [c.replace(".NS", "") for c in raw.columns]
    raw = raw.loc[:, ~raw.columns.duplicated()]
    raw = raw[raw.index >= "2009-06-01"]
    return raw, mac["^NSEI"].dropna(), mem


def universe_fn(mem: dict, raw: pd.DataFrame, ix: str, mode: str):
    """Stocks the sleeve may pick on day d: today's list (biased, as A289) or the list at d's month-end (A290)."""
    today = mem[ix][max(mem[ix])]
    months = sorted(mem[ix])

    def at(d: pd.Timestamp) -> list[str]:
        if mode == "today":
            names = today
        else:
            same = [m for m in months if (m.year, m.month) == (d.year, d.month)]      # list in force at that month-end
            names = mem[ix][same[0] if same else max(m for m in months if m <= d.date())]
        return [c for c in names if c in raw and pd.notna(raw.at[d, c])]     # must really trade that day
    return at


def targets(px, sc, nifty_up, rb, cfg, uni):
    out, held = {}, []
    for d in rb:
        u = uni(d)
        st = B.stock_sleeve(px, sc, nifty_up, d, u, cfg["score"], cfg["k"], cfg["buffer"], cfg["regime"], held)
        held = [c for c in st if c in u]
        w = {c: x * cfg["mix"] for c, x in st.items()}
        if cfg["mix"] < 1:
            for c, x in B.etf_sleeve(sc, d).items():
                w[c] = w.get(c, 0) + x * (1 - cfg["mix"])
        out[d] = w
    return out


def run(px, sc, nifty_up, cfg, uni, start, end=None):
    w = px.loc[start:end] if end else px.loc[start:]
    rb = A.rebalance_days(w.index, "M")
    if rb[0] != w.index[0]:
        rb = [w.index[0]] + rb
    rb = [d for d in rb if d != w.index[-1]]
    return A.simulate(w, targets(px, sc, nifty_up, rb, cfg, uni))


def coverage(mem, raw):
    rows = []
    for ix in ("N50", "N100"):
        for y in range(2011, date.today().year + 1):
            ms = [m for m in mem[ix] if m.year == y]
            tot = sum(len(mem[ix][m]) for m in ms)
            have = sum(1 for m in ms for s in mem[ix][m] if s in raw and raw[s].loc[:str(m)].last_valid_index() is not None
                       and raw[s].loc[:str(m)].last_valid_index() >= pd.Timestamp(m) - pd.Timedelta(days=10))
            rows.append({"index": ix, "year": y, "member_months": tot, "with_prices": have, "share": have / tot})
    return pd.DataFrame(rows)


def main():
    raw, nifty, mem = load()
    px = raw.ffill()                                   # held stock whose prices stop: valued, then sold, at last price
    sc = B.scores(raw.ffill(limit=5))
    nifty_up = (nifty > nifty.rolling(200).mean()).reindex(px.index).ffill().fillna(False)
    cov = coverage(mem, raw)
    cov.to_csv(HERE / "a290_coverage.csv", index=False, float_format="%.3f")
    print(f"assets {raw.shape[1]}, {raw.index[0].date()} to {raw.index[-1].date()}; price coverage of point-in-time "
          f"member-months: N50 {cov[cov['index'] == 'N50'].share.min():.0%}-{cov[cov['index'] == 'N50'].share.max():.0%}, "
          f"N100 {cov[cov['index'] == 'N100'].share.min():.0%}-{cov[cov['index'] == 'N100'].share.max():.0%}")
    rows = []
    for mode in ("today", "pit"):
        for cfg in B.GRID:
            uni = universe_fn(mem, raw, cfg["univ"], mode)
            vt, nt = run(px, sc, nifty_up, cfg, uni, *B.TRAIN)
            vs, ns = run(px, sc, nifty_up, cfg, uni, B.TEST[0])
            st, ss = A.stats(vt, nt), A.stats(vs, ns)
            rows.append({"lists": mode, **cfg, **{f"train_{k}": v for k, v in st.items()},
                         **{f"test_{k}": v for k, v in ss.items()}, "test_end_rs": vs.iloc[-1]})
    res = pd.DataFrame(rows)
    res["chosen"] = False
    for mode in ("today", "pit"):
        ok = res[(res.lists == mode) & (res.train_max_dd > -0.30)]
        res.loc[ok.sort_values("train_cagr", ascending=False).index[0], "chosen"] = True
    res.to_csv(HERE / "a290_grid.csv", index=False, float_format="%.4f")
    a289_pick = dict(univ="N100", score="m12_1", k=5, buffer=1, regime="rotate", mix=1.0)
    show = ["lists"] + CFG_COLS + ["train_cagr", "train_max_dd", "test_cagr", "test_max_dd", "test_end_rs"]
    print("CHOSEN on 2011-2018 (each list type):")
    print(res[res.chosen][show].round(3).to_string(index=False))
    same = res[(res[list(a289_pick)] == pd.Series(a289_pick)).all(axis=1)]
    print("A289's chosen setting under both list types:")
    print(same[show].round(3).to_string(index=False))
    for mode in ("today", "pit"):
        r = res[res.lists == mode]
        print(f"{mode}: median test CAGR {r.test_cagr.median():.3f} | N100 median {r[r.univ == 'N100'].test_cagr.median():.3f}"
              f" | N50 median {r[r.univ == 'N50'].test_cagr.median():.3f} | share >= 20%: {(r.test_cagr >= 0.20).mean():.2f}")


if __name__ == "__main__":
    main()

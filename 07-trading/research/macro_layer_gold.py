"""A325: macro / news / fear layer on top of the A323 best gold mix.

Akhil (21 Nov 2026): "does our algo cover CPI news and greed and fear index and wars, interest rates and
fed news ... if not add extra layer which can handle huge volumes and test one trade, if it is successful
take trades more like that".

Input: every trade of the A323 mix (reports/best-combo-gold-trades-2026-11-21.csv, 4,745 trades, 2 years).
Data (all free, official or Yahoo):
  CPI and jobs-report (NFP) release dates: BLS archive pages (bls.gov/bls/news-release/cpi.htm, empsit.htm),
    08:30 New York time.  FOMC statement days: federalreserve.gov fomccalendars.htm, 14:00 New York time.
    (Fetched 21 Nov 2026.  Oct 2025 CPI/NFP were not published: US funding lapse.)
  Fear: ^VIX (stock-market fear index; CNN's Fear & Greed history is not freely downloadable, VIX is one of
    its 7 inputs) and ^GVZ (CBOE gold volatility index).
  Rates / dollar: ^TNX (US 10-year yield), DX-Y.NYB (dollar index).
  Wars / shocks: no free daily war dataset reachable from here; a GVZ jump (> 1.3x its 20-day average) is
    used as the "shock day" proxy.
All macro values are taken from the PREVIOUS day's close (no look-ahead).

Layers tested (each alone; chosen on the EARLIER part only, before 2025-09-01; reported on the later part):
  news_block_Xh   skip entries within X hours before/after CPI, NFP, FOMC (X = 1, 2, 4, 12)
  fear_skip       skip entries when VIX or GVZ is in its top 20% (rolling 1 year)
  shock_skip      skip entries on GVZ shock days
  rates_align     longs only when the 10y yield fell over 20 days, shorts only when it rose
  dollar_align    same with the dollar index
  streak_take     take a strategy's trade only if its last 5 CLOSED trades sum to > 0R ("take more like that")
  streak_size     1.5x size after that strategy's last closed trade won, 0.75x after a loss
A layer is kept only if its earlier-part total R beats the plain mix AND its later-part avg R is not worse.
Random check: removing the same share of trades at random (200 seeds).
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
import best_combo_gold as b  # noqa: E402

SPLIT = pd.Timestamp("2025-09-01")
CPI = ["2024-07-11", "2024-08-14", "2024-09-11", "2024-10-10", "2024-11-13", "2024-12-11", "2025-01-15", "2025-02-12",
       "2025-03-12", "2025-04-10", "2025-05-13", "2025-06-11", "2025-07-15", "2025-08-12", "2025-09-11", "2025-10-24",
       "2025-12-18", "2026-01-13", "2026-02-13", "2026-03-11", "2026-04-10", "2026-05-12", "2026-06-10", "2026-07-14",
       "2026-08-12", "2026-09-11", "2026-10-14", "2026-11-10", "2026-12-10", "2027-01-13", "2027-02-11", "2027-03-10",
       "2027-04-13", "2027-05-12"]
NFP = ["2024-07-05", "2024-08-02", "2024-09-06", "2024-10-04", "2024-11-01", "2024-12-06", "2025-01-10", "2025-02-07",
       "2025-03-07", "2025-04-04", "2025-05-02", "2025-06-06", "2025-07-03", "2025-08-01", "2025-09-05", "2025-11-20",
       "2025-12-16", "2026-01-09", "2026-02-11", "2026-03-06", "2026-04-03", "2026-05-08", "2026-06-05", "2026-07-02",
       "2026-08-07", "2026-09-04", "2026-10-02", "2026-11-06", "2026-12-04", "2027-01-08", "2027-02-05", "2027-03-05",
       "2027-04-02", "2027-05-07"]
FOMC = ["2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18", "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
        "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10", "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09"]


def events_utc() -> pd.DatetimeIndex:
    ts = [pd.Timestamp(f"{d} 08:30", tz="America/New_York") for d in CPI + NFP]
    ts += [pd.Timestamp(f"{d} 14:00", tz="America/New_York") for d in FOMC]
    return pd.DatetimeIndex(sorted(ts)).tz_convert("UTC").tz_localize(None)


def macro_daily() -> pd.DataFrame:
    p = Path("/tmp/macro_daily.parquet")
    if p.exists():
        return pd.read_parquet(p)
    import yfinance as yf
    cols = {}
    for sym, name in (("^VIX", "vix"), ("^GVZ", "gvz"), ("^TNX", "tnx"), ("DX-Y.NYB", "dxy")):
        x = yf.download(sym, start="2023-06-01", interval="1d", progress=False, auto_adjust=False)
        x.columns = [c[0] if isinstance(c, tuple) else c for c in x.columns]
        cols[name] = x["Close"]
    d = pd.DataFrame(cols).ffill()
    d.index = pd.to_datetime(d.index).tz_localize(None)
    d.to_parquet(p)
    return d


def features(t: pd.DataFrame, mac: pd.DataFrame) -> pd.DataFrame:
    t = t.sort_values("t_in").reset_index(drop=True).copy()
    ev = events_utc().values
    ti = t.t_in.values
    j = np.searchsorted(ev, ti)
    nxt = np.where(j < len(ev), (ev[np.minimum(j, len(ev) - 1)] - ti) / np.timedelta64(1, "h"), 1e9)
    prv = np.where(j > 0, (ti - ev[np.maximum(j - 1, 0)]) / np.timedelta64(1, "h"), 1e9)
    t["h_to_event"] = np.minimum(np.abs(nxt), np.abs(prv))
    m = mac.copy()
    m["vix_hi"] = m.vix > m.vix.rolling(252, min_periods=60).quantile(0.8)
    m["gvz_hi"] = m.gvz > m.gvz.rolling(252, min_periods=60).quantile(0.8)
    m["shock"] = m.gvz > 1.3 * m.gvz.rolling(20).mean()
    m["tnx_dn"] = m.tnx < m.tnx.shift(20)
    m["dxy_dn"] = m.dxy < m.dxy.shift(20)
    m = m.shift(1)                                         # previous day's close only
    day = t.t_in.dt.normalize()
    mm = m.reindex(pd.date_range(m.index.min(), day.max() + pd.Timedelta("1D"))).ffill()
    for c in ("vix_hi", "gvz_hi", "shock", "tnx_dn", "dxy_dn"):
        t[c] = mm[c].reindex(day).fillna(False).astype(bool).values
    # strategy streak using only trades CLOSED before this entry
    last5, lastw = [], []
    for k, row in t.iterrows():
        prior = t[(t.strategy == row.strategy) & (t.t_out < row.t_in)].sort_values("t_out")
        last5.append(prior.r.tail(5).sum() if len(prior) >= 5 else np.nan)
        lastw.append(prior.r.iloc[-1] if len(prior) else np.nan)
    t["last5"], t["last1"] = last5, lastw
    return t


def layers(t: pd.DataFrame) -> dict[str, pd.Series]:
    """name -> weight per trade (0 = skipped)."""
    w = {"plain": pd.Series(1.0, index=t.index)}
    for x in (1, 2, 4, 12):
        w[f"news_block_{x}h"] = (t.h_to_event > x).astype(float)
    w["news_only_2h"] = (t.h_to_event <= 2).astype(float)
    w["fear_skip"] = (~(t.vix_hi | t.gvz_hi)).astype(float)
    w["shock_skip"] = (~t.shock).astype(float)
    w["rates_align"] = (((t.side == 1) & t.tnx_dn) | ((t.side == -1) & ~t.tnx_dn)).astype(float)
    w["dollar_align"] = (((t.side == 1) & t.dxy_dn) | ((t.side == -1) & ~t.dxy_dn)).astype(float)
    w["streak_take"] = (t.last5.fillna(0) > 0).astype(float)
    w["streak_size"] = np.where(t.last1.isna(), 1.0, np.where(t.last1 > 0.05, 1.5, 0.75))
    w["streak_size"] = pd.Series(w["streak_size"], index=t.index)
    return w


def score(t, wt):
    r = t.r * wt
    kept = wt > 0
    return dict(trades=int(kept.sum()), wins=int(((t.r > 0.05) & kept).sum()), losses=int(((t.r < -0.05) & kept).sum()),
                avg_r=round(float(r[kept].sum() / max(wt[kept].sum(), 1e-9)), 3) if kept.any() else None,
                total_r=round(float(r.sum()), 1))


def random_drop(t, keep_share, seeds=200):
    rng = np.random.default_rng(7)
    tot = []
    for _ in range(seeds):
        k = rng.random(len(t)) < keep_share
        tot.append(float(t.r[k].sum()))
    return float(np.mean(tot)), float(np.percentile(tot, 95))


def main() -> int:
    src = sorted(Path("reports").glob("best-combo-gold-trades-2*.csv"))[-1]
    t = pd.read_csv(src, parse_dates=["t_in", "t_out"])
    t = features(t, macro_daily())
    W = layers(t)
    early, late = t.t_in < SPLIT, t.t_in >= SPLIT
    rows = {}
    base_e = score(t[early], W["plain"][early])
    base_l = score(t[late], W["plain"][late])
    for name, w in W.items():
        e, l = score(t[early], w[early]), score(t[late], w[late])
        share = float((w > 0).mean())
        rnd_mean, rnd_95 = random_drop(t[late], float((w[late] > 0).mean()))
        keep = (name != "plain" and e["total_r"] > base_e["total_r"] and (l["avg_r"] or -9) >= (base_l["avg_r"] or 9))
        rows[name] = dict(early=e, late=l, share_kept=round(share, 3), late_random_drop_total_r=round(rnd_mean, 1),
                          late_random_95pct=round(rnd_95, 1), kept=bool(keep))
    chosen = [k for k, v in rows.items() if v["kept"]]
    wt = W["plain"].copy()
    for k in chosen:
        wt = wt * W[k]
    b.RISK = 0.0025
    final = t.assign(r=t.r * wt)[wt > 0]
    rep = dict(generated=str(date.today()), trades_file=str(src), chosen=chosen, layers=rows,
               combined_2y=score(t, wt) | b.account(final), combined_later=score(t[late], wt[late]),
               plain_2y=score(t, W["plain"]) | b.account(t),
               news_trades=dict(within_2h=score(t, (t.h_to_event <= 2).astype(float)),
                                outside_2h=score(t, (t.h_to_event > 2).astype(float))),
               the5ers_combined=b.the5ers(final))
    (Path("reports") / f"macro-layer-gold-{date.today()}.json").write_text(json.dumps(rep, indent=1, default=str))
    for k, v in rows.items():
        print(f"{k:16s} kept={v['share_kept']:.2f} early {v['early']['avg_r']} ({v['early']['total_r']}R) | late {v['late']['avg_r']} "
              f"({v['late']['total_r']}R, random-drop {v['late_random_drop_total_r']}R) {'<- KEEP' if v['kept'] else ''}")
    print(json.dumps({k: rep[k] for k in ("chosen", "combined_2y", "combined_later", "plain_2y", "news_trades", "the5ers_combined")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

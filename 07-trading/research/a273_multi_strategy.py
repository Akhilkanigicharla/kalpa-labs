"""A273: can more trades, more companies, more ETFs, other timeframes and fear / inflation / rupee filters beat
the current Rs 10,000 bot (Nifty trend Rs 5,000 + gold held Rs 5,000)? (Akhil, 14 Nov 2026)

Honest method:
  * Rs 10,000 account simulated share by share: whole shares, every NSE delivery charge (src/costs.py),
    Rs 15.34 DP charge per scrip sold, 10 bps slippage each side, idle cash earns 4.7%/yr (LIQUIDBEES).
  * Signal at the close of the rebalance day, trade at the NEXT day's close (no look-ahead).
  * Settings are chosen on 2011-2018 ONLY, then judged untouched on 2019-2026 (out of sample).
  * Every configuration tried is counted (more tries = more luck; the report says how many).
Limits stated in the report: stock universe = today's Nifty 50 (survivorship bias flatters stock results);
no free historical news-sentiment or fear & greed index for India (India VIX is the fear proxy);
CPI from FRED is monthly and published with a delay (lagged 2 months here).
Research only. Own money only. Not advice.
"""
from __future__ import annotations

import io
import itertools
import math
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import costs  # noqa: E402

CAPITAL = 10_000.0
DP = 15.34
SLIP = 0.0010
CASH_RATE = 0.047
BUY_R, SELL_R = costs.delivery_side_rates()
TRAIN_END, TEST_START = "2018-12-31", "2019-01-01"

NIFTY50 = """ADANIENT ADANIPORTS APOLLOHOSP ASIANPAINT AXISBANK BAJAJ-AUTO BAJFINANCE BAJAJFINSV BEL BHARTIARTL CIPLA
COALINDIA DRREDDY EICHERMOT GRASIM HCLTECH HDFCBANK HDFCLIFE HEROMOTOCO HINDALCO HINDUNILVR ICICIBANK INDUSINDBK
INFY ITC JSWSTEEL KOTAKBANK LT M&M MARUTI NESTLEIND NTPC ONGC POWERGRID RELIANCE SBILIFE SHRIRAMFIN SBIN
SUNPHARMA TCS TATACONSUM TATASTEEL TECHM TITAN TRENT ULTRACEMCO WIPRO""".split()
ETFS = ["NIFTYBEES", "BANKBEES", "JUNIORBEES", "GOLDBEES", "MON100"]
CACHE = ROOT / "data" / "a273"


# ------------------------------------------------------------------ data
def yahoo(tickers: list[str], name: str) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{name}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    import yfinance as yf
    raw = yf.download(tickers, start="2009-01-01", progress=False, auto_adjust=True, group_by="ticker", threads=True)
    closes = {}
    for t in tickers:
        try:
            s = raw[t]["Close"].dropna()
        except KeyError:
            continue
        if len(s) > 250:
            closes[t] = s
    df = pd.DataFrame(closes)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.sort_index()
    df.to_parquet(f)
    return df


def repair(df: pd.DataFrame) -> pd.DataFrame:
    """Yahoo glitches: single days quoted at 1/100 or 100x (e.g. GOLDBEES Dec 2019). Fix isolated spikes."""
    out = df.copy()
    for c in out:
        s = out[c]
        med = s.rolling(11, center=True, min_periods=3).median()
        for k in (100.0, 10.0):
            lo, hi = s < med / (k * 0.5), s > med * (k * 0.5)
            s = s.where(~lo, s * k).where(~hi, s / k)
        out[c] = s
    return out


def fred(series: str) -> pd.Series:
    f = CACHE / f"fred_{series}.csv"
    if not f.exists():
        with urllib.request.urlopen(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}", timeout=30) as r:
            f.write_bytes(r.read())
    d = pd.read_csv(f)
    d.columns = ["date", "v"]
    d["date"] = pd.to_datetime(d["date"])
    return pd.to_numeric(d.set_index("date")["v"], errors="coerce").dropna()


# ------------------------------------------------------------------ engine
def simulate(px: pd.DataFrame, targets: dict[pd.Timestamp, dict[str, float]]) -> tuple[pd.Series, int]:
    """Share-level Rs 10,000 account. targets[day] = weights decided at that day's close; traded next day's close."""
    days = px.index
    cash, shares, value, trades = CAPITAL, {}, [], 0
    pending = None
    tdates = set(targets)
    for i, d in enumerate(days):
        if i:
            cash *= (1 + CASH_RATE) ** (1 / 252)
        row = px.loc[d]
        if pending is not None:
            want = pending
            pending = None
            equity = cash + sum(q * row[s] for s, q in shares.items() if np.isfinite(row.get(s, np.nan)))
            # sells first
            for s in list(shares):
                p = row.get(s, np.nan)
                if not np.isfinite(p):
                    continue
                tgt_q = math.floor(want.get(s, 0.0) * equity / (p * (1 + SLIP + BUY_R))) if want.get(s, 0) > 0 else 0
                if tgt_q < shares[s]:
                    q = shares[s] - tgt_q
                    v = q * p * (1 - SLIP)
                    cash += v - v * SELL_R - DP
                    shares[s] = tgt_q
                    trades += 1
                    if shares[s] == 0:
                        del shares[s]
            for s, w in sorted(want.items(), key=lambda kv: -kv[1]):
                p = row.get(s, np.nan)
                if w <= 0 or not np.isfinite(p):
                    continue
                tgt_q = math.floor(w * equity / (p * (1 + SLIP + BUY_R)))
                q = tgt_q - shares.get(s, 0)
                cost = q * p * (1 + SLIP) * (1 + BUY_R)
                if q > 0 and cost <= cash:
                    cash -= cost
                    shares[s] = shares.get(s, 0) + q
                    trades += 1
        if d in tdates:
            pending = targets[d]
        value.append(cash + sum(q * row[s] for s, q in shares.items() if np.isfinite(row.get(s, np.nan))))
    return pd.Series(value, index=days), trades


def rebalance_days(idx: pd.DatetimeIndex, freq: str) -> list[pd.Timestamp]:
    s = pd.Series(idx, index=idx)
    key = idx.to_period("M") if freq == "M" else idx.to_period("W-FRI")
    return list(s.groupby(key).last())


def stats(v: pd.Series, trades: int) -> dict:
    r = v.pct_change().dropna()
    yrs = (v.index[-1] - v.index[0]).days / 365.25
    cagr = (v.iloc[-1] / v.iloc[0]) ** (1 / yrs) - 1
    dd = (v / v.cummax() - 1).min()
    wy = v.groupby(v.index.year).last().pct_change()
    first = v.groupby(v.index.year).last().iloc[0] / v.iloc[0] - 1
    wy = pd.concat([pd.Series([first]), wy.dropna()]).min()
    sharpe = r.mean() / r.std() * math.sqrt(252) if r.std() > 0 else 0.0
    return {"cagr": cagr, "max_dd": dd, "worst_year": wy, "sharpe": sharpe, "trades_per_yr": trades / yrs,
            "rs_per_day": CAPITAL * cagr / 250}


# ------------------------------------------------------------------ strategies (all return targets by day)
def trend_on(close: pd.Series, days: int = 200) -> pd.Series:
    return close > close.rolling(days).mean()


def strat_baseline(px, nifty, rb):
    """Current bot: Nifty trend (63-day momentum) Rs 5,000 + gold held Rs 5,000, decided monthly here."""
    mom = nifty / nifty.shift(63) - 1
    return {d: {"NIFTYBEES": 0.5 if mom.get(d, -1) > 0 else 0.0, "GOLDBEES": 0.5} for d in rb}


def strat_stock_momentum(px, nifty, rb, n=5, look=252, skip=21, filt=True, vix=None, vix_rule=None, cpi=None, inr=None):
    stocks = [c for c in px if c in NIFTY50]
    tr = trend_on(nifty)
    out = {}
    for d in rb:
        hist = px.loc[:d, stocks]
        if len(hist) <= look + skip:
            continue
        ret = hist.iloc[-1 - skip] / hist.iloc[-1 - look] - 1
        ret = ret[hist.iloc[-1].notna() & hist.iloc[-1 - look].notna()]
        risk_on = bool(tr.get(d, False)) if filt else True
        risk_on = overlay(d, risk_on, vix, vix_rule)
        w = {}
        if risk_on:
            top = list(ret.sort_values(ascending=False).index[: n * 2])
            pick = [s for s in top if px.loc[d, s] * 1.01 <= CAPITAL / n][:n]   # whole shares must be affordable
            w = {s: 1.0 / n for s in pick}
        out[d] = add_macro(w, d, cpi, inr)
    return out


def strat_etf_momentum(px, nifty, rb, k=1, look=126, vix=None, vix_rule=None, cpi=None, inr=None):
    etfs = [e for e in ETFS if e in px]
    out = {}
    for d in rb:
        hist = px.loc[:d, etfs].dropna(axis=1, how="any") if False else px.loc[:d, etfs]
        if len(hist) <= look:
            continue
        ret = (hist.iloc[-1] / hist.iloc[-1 - look] - 1).dropna()
        cash_ret = (1 + CASH_RATE) ** (look / 252) - 1
        good = ret[ret > cash_ret].sort_values(ascending=False)
        risk_on = overlay(d, True, vix, vix_rule)
        pick = list(good.index[:k]) if risk_on else [e for e in good.index[:k] if e == "GOLDBEES"]
        w = {e: 1.0 / k for e in pick}
        out[d] = add_macro(w, d, cpi, inr)
    return out


def overlay(d, risk_on: bool, vix: pd.Series | None, rule: str | None) -> bool:
    """India VIX as the fear gauge (no free fear & greed history for India). 'fear_out': go to cash when VIX is in
    its top 20% of the last year; 'fear_in': buy when fear is extreme even if the trend filter says no."""
    if vix is None or rule is None:
        return risk_on
    hist = vix.loc[:d].tail(252)
    if len(hist) < 100:
        return risk_on
    high = hist.iloc[-1] >= hist.quantile(0.8)
    if rule == "fear_out":
        return risk_on and not high
    if rule == "fear_in":
        return risk_on or high
    return risk_on


def add_macro(w: dict, d, cpi: pd.Series | None, inr: pd.Series | None) -> dict:
    """Inflation: CPI YoY above 6% (RBI's upper band) -> move 30% into gold. Rupee: USD/INR up >3% in 3 months
    -> move 30% into MON100 (Nasdaq ETF, gains when the rupee falls). Data lagged so it was public on that day."""
    w = dict(w)
    tilt = []
    if cpi is not None:
        c = cpi.loc[: d - pd.Timedelta(days=60)]
        if len(c) > 13 and (c.iloc[-1] / c.iloc[-13] - 1) > 0.06:
            tilt.append("GOLDBEES")
    if inr is not None:
        u = inr.loc[:d]
        if len(u) > 64 and (u.iloc[-1] / u.iloc[-64] - 1) > 0.03:
            tilt.append("MON100")
    for t in tilt:
        w = {s: v * 0.7 for s, v in w.items()}
        w[t] = w.get(t, 0.0) + 0.3
    return w


# ------------------------------------------------------------------ run
def main():
    stocks = repair(yahoo([f"{s}.NS" for s in NIFTY50], "nifty50"))
    stocks.columns = [c.replace(".NS", "") for c in stocks.columns]
    etfs = repair(yahoo([f"{e}.NS" for e in ETFS], "etfs"))
    etfs.columns = [c.replace(".NS", "") for c in etfs.columns]
    idx = yahoo(["^NSEI", "^INDIAVIX", "USDINR=X"], "macro")
    nifty, vix, inr = idx["^NSEI"].dropna(), idx.get("^INDIAVIX", pd.Series(dtype=float)).dropna(), idx["USDINR=X"].dropna()
    cpi = fred("INDCPIALLMINMEI")
    px = pd.concat([stocks, etfs], axis=1).loc["2011-01-01":].ffill(limit=5)
    px = px[px.index.isin(nifty.index)]
    nifty = nifty.reindex(px.index).ffill()
    print(f"data: {px.shape[1]} instruments, {px.index[0].date()} to {px.index[-1].date()}; "
          f"stocks {stocks.shape[1]}/{len(NIFTY50)}, etfs {etfs.shape[1]}/{len(ETFS)}, VIX {len(vix)} days, CPI {len(cpi)} months")

    configs = []
    for freq in ("M", "W"):
        rb = rebalance_days(px.index, freq)
        configs.append(("baseline: Nifty trend + gold held", freq, strat_baseline(px, nifty, rb)))
        for n, look, filt in itertools.product((3, 5), (126, 252), (True, False)):
            configs.append((f"stocks momentum top{n} {look}d {'trend-filter' if filt else 'no-filter'}", freq,
                            strat_stock_momentum(px, nifty, rb, n=n, look=look, filt=filt)))
        for k, look in itertools.product((1, 2), (63, 126, 252)):
            configs.append((f"ETF momentum top{k} {look}d", freq, strat_etf_momentum(px, nifty, rb, k=k, look=look)))

    rows = []
    for name, freq, tg in configs:
        tr_t = {d: w for d, w in tg.items() if d <= pd.Timestamp(TRAIN_END)}
        v, t = simulate(px.loc[:TRAIN_END], tr_t)
        rows.append({"name": name, "freq": freq, **{f"train_{k}": x for k, x in stats(v, t).items()}})
    res = pd.DataFrame(rows)

    # pick the best stock and best ETF config on TRAIN Sharpe only, then try overlays on train too
    best = {}
    for fam in ("stocks", "ETF"):
        sub = res[res.name.str.startswith(fam)].sort_values("train_sharpe", ascending=False)
        best[fam] = sub.iloc[0]
    overlay_rows = []
    for fam, row in best.items():
        rb = rebalance_days(px.index, row.freq)
        parts = row["name"].split()
        for vr, use_cpi, use_inr in itertools.product((None, "fear_out", "fear_in"), (False, True), (False, True)):
            if fam == "stocks":
                n, look, filt = int(parts[2][3:]), int(parts[3][:-1]), parts[4] == "trend-filter"
                tg = strat_stock_momentum(px, nifty, rb, n=n, look=look, filt=filt, vix=vix if vr else None, vix_rule=vr,
                                          cpi=cpi if use_cpi else None, inr=inr if use_inr else None)
            else:
                k, look = int(parts[2][3:]), int(parts[3][:-1])
                tg = strat_etf_momentum(px, nifty, rb, k=k, look=look, vix=vix if vr else None, vix_rule=vr,
                                        cpi=cpi if use_cpi else None, inr=inr if use_inr else None)
            label = f"{row['name']} | VIX:{vr or 'none'} CPI:{'on' if use_cpi else 'off'} INR:{'on' if use_inr else 'off'}"
            v, t = simulate(px.loc[:TRAIN_END], {d: w for d, w in tg.items() if d <= pd.Timestamp(TRAIN_END)})
            overlay_rows.append({"name": label, "freq": row.freq, "tg": tg, **{f"train_{k}": x for k, x in stats(v, t).items()}})
    ov = pd.DataFrame(overlay_rows)
    n_tried = len(res) + len(ov)

    # out-of-sample: baseline + each family's best plain config + each family's best overlay (chosen on train)
    finals = [("baseline: Nifty trend + gold held", "M", strat_baseline(px, nifty, rebalance_days(px.index, "M")))]
    for fam, row in best.items():
        finals.append((row["name"], row.freq, dict(configs)[row["name"]] if False else
                       next(tg for nm, fq, tg in configs if nm == row["name"] and fq == row.freq)))
        o = ov[ov.name.str.startswith(row["name"])].sort_values("train_sharpe", ascending=False).iloc[0]
        finals.append((o["name"], o.freq, o.tg))
    out = []
    for name, freq, tg in finals:
        test_px = px.loc[TEST_START:]
        v, t = simulate(test_px, {d: w for d, w in tg.items() if d >= pd.Timestamp(TEST_START)})
        tr = res[(res.name == name) & (res.freq == freq)]
        trs = ov[(ov.name == name)]["train_sharpe"]
        out.append({"strategy": name, "rebalance": "monthly" if freq == "M" else "weekly",
                    "train_sharpe": round(float(tr.train_sharpe.iloc[0] if len(tr) else trs.iloc[0] if len(trs) else np.nan), 2),
                    **{f"test_{k}": x for k, x in stats(v, t).items()}, "test_final_rs": round(v.iloc[-1])})
    o = pd.DataFrame(out)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 80)
    print(f"\nconfigs tried: {n_tried} (all on train only)\n")
    print(res.sort_values("train_sharpe", ascending=False).head(12)[["name", "freq", "train_cagr", "train_sharpe", "train_max_dd", "train_trades_per_yr"]].round(3).to_string(index=False))
    print("\nfilters on the best stock + ETF settings (train 2011-2018):")
    print(ov.sort_values("train_sharpe", ascending=False)[["name", "train_cagr", "train_sharpe", "train_max_dd"]].round(3).to_string(index=False))
    ov.drop(columns=["tg"]).to_csv(Path(__file__).with_name("a273_filters_train.csv"), index=False)
    print("\nOUT OF SAMPLE 2019-2026 (never seen when choosing):")
    print(o.round(3).to_string(index=False))
    o.to_csv(Path(__file__).with_name("a273_results.csv"), index=False)
    res.drop(columns=[], errors="ignore").to_csv(Path(__file__).with_name("a273_train_all.csv"), index=False)


if __name__ == "__main__":
    main()

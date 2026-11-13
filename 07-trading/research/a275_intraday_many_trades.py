"""A275: intraday, 10-15 trades a day, Rs 10,000 at 5x MIS (Akhil, 14 Nov 2026).

Per strategy we report: trades per day, success rate (net win %), average win / loss, gross P&L, charges, net P&L,
best / worst day, % of green days. Rules so the numbers can be trusted:
  * 5-minute bars, ~60 trading days (the most Yahoo gives free), 20 liquid Nifty stocks + NIFTYBEES.
  * One position at a time, Rs 50,000 notional (Rs 10,000 x 5, the MIS cap checked in aggressive-5k report).
  * Signal on a closed bar, entry at the NEXT bar's open + 0.02% slippage; stop / target checked on later bars'
    high / low (if both touch in one bar, the stop is assumed first); everything closed by 15:15.
  * Every NSE intraday charge from src/costs.py (brokerage 0.03% capped Rs 20/order, STT, exchange, GST, stamp, SEBI).
  * Settings picked on the FIRST half of the days only; the SECOND half is the honest test.
Research only. Own money only. Not advice.
"""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import costs  # noqa: E402

NOTIONAL, CAPITAL, SLIP = 50_000.0, 10_000.0, 0.0002
TICKERS = """RELIANCE HDFCBANK ICICIBANK INFY TCS SBIN BHARTIARTL AXISBANK KOTAKBANK LT ITC TATASTEEL
BAJFINANCE MARUTI SUNPHARMA HINDUNILVR M&M NTPC TATACONSUM ADANIPORTS NIFTYBEES""".split()
CACHE = ROOT / "data" / "a275"


def load() -> dict[str, pd.DataFrame]:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / "bars5m.parquet"
    if f.exists():
        raw = pd.read_parquet(f)
    else:
        import yfinance as yf
        raw = yf.download([f"{t}.NS" for t in TICKERS], period="60d", interval="5m", progress=False,
                          auto_adjust=False, group_by="ticker", threads=True)
        raw.to_parquet(f)
    out = {}
    for t in TICKERS:
        try:
            df = raw[f"{t}.NS"][["Open", "High", "Low", "Close", "Volume"]].dropna()
        except KeyError:
            continue
        df.columns = ["open", "high", "low", "close", "volume"]
        idx = pd.DatetimeIndex(df.index)
        idx = idx.tz_convert("Asia/Kolkata").tz_localize(None) if idx.tz is not None else idx
        df.index = idx
        df = df.between_time("09:15", "15:25")
        if len(df) > 1000:
            out[t] = df
    return out


def indicators(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    day = d.index.date
    tp = (d.high + d.low + d.close) / 3
    pv = (tp * d.volume).groupby(day).cumsum()
    vv = d.volume.groupby(day).cumsum().replace(0, np.nan)
    d["vwap"] = pv / vv
    d["ema9"] = d.close.ewm(span=9, adjust=False).mean()
    d["ema21"] = d.close.ewm(span=21, adjust=False).mean()
    delta = d.close.diff()
    up, dn = delta.clip(lower=0), -delta.clip(upper=0)
    for n in (2, 14):
        rs = up.ewm(alpha=1 / n, adjust=False).mean() / dn.ewm(alpha=1 / n, adjust=False).mean().replace(0, np.nan)
        d[f"rsi{n}"] = 100 - 100 / (1 + rs)
    d["vol_ratio"] = d.volume / d.volume.rolling(20).mean()
    d["bar_pos"] = (d.close - d.low) / (d.high - d.low).replace(0, np.nan)
    first = d.groupby(day).head(3)
    orh = first.high.groupby(first.index.date).max()
    orl = first.low.groupby(first.index.date).min()
    d["or_high"] = pd.Series(day, index=d.index).map(orh)
    d["or_low"] = pd.Series(day, index=d.index).map(orl)
    d["bar_no"] = d.groupby(day).cumcount()
    return d


# --- signals: +1 long, -1 short, 0 none, decided on the CLOSED bar ---------------------------------------
def sig_ema(d, **p):
    cross_up = (d.ema9 > d.ema21) & (d.ema9.shift() <= d.ema21.shift()) & (d.close > d.vwap)
    cross_dn = (d.ema9 < d.ema21) & (d.ema9.shift() >= d.ema21.shift()) & (d.close < d.vwap)
    return cross_up.astype(int) - cross_dn.astype(int)


def sig_vwap_revert(d, dev=0.004, **p):
    lo = (d.close <= d.vwap * (1 - dev)) & (d.rsi14 < 30)
    hi = (d.close >= d.vwap * (1 + dev)) & (d.rsi14 > 70)
    return lo.astype(int) - hi.astype(int)


def sig_volume_spike(d, k=3.0, **p):
    green = (d.close > d.open) & (d.bar_pos > 0.75) & (d.vol_ratio > k)
    red = (d.close < d.open) & (d.bar_pos < 0.25) & (d.vol_ratio > k)
    return green.astype(int) - red.astype(int)


def sig_orb(d, **p):
    after = d.bar_no >= 3
    up = after & (d.close > d.or_high) & (d.close.shift() <= d.or_high)
    dn = after & (d.close < d.or_low) & (d.close.shift() >= d.or_low)
    return up.astype(int) - dn.astype(int)


def sig_rsi2(d, lo=5, hi=95, **p):
    return ((d.rsi2 < lo) & (d.close > d.vwap)).astype(int) - ((d.rsi2 > hi) & (d.close < d.vwap)).astype(int)


STRATS = {
    "EMA 9/21 cross + VWAP": (sig_ema, [{}]),
    "VWAP snap-back": (sig_vwap_revert, [{"dev": 0.003}, {"dev": 0.005}]),
    "Volume-spike momentum": (sig_volume_spike, [{"k": 2.5}, {"k": 4.0}]),
    "Opening-range breakout": (sig_orb, [{}]),
    "RSI(2) scalp": (sig_rsi2, [{"lo": 5, "hi": 95}, {"lo": 10, "hi": 90}]),
}
EXITS = [(0.004, 0.002), (0.006, 0.003), (0.010, 0.005)]   # (target, stop) as fractions


def run(data: dict[str, pd.DataFrame], fn, params, tp, sl, days: list) -> pd.DataFrame:
    """Event loop over time; when flat, take the strongest signal of any stock on the latest closed bar."""
    sigs = {t: fn(d, **params) for t, d in data.items()}
    times = sorted(set().union(*[d.index for d in data.values()]))
    times = [x for x in times if x.date() in days]
    pos, trades = None, []
    by_t = {t: d for t, d in data.items()}
    for i, ts in enumerate(times[:-1]):
        nxt = times[i + 1]
        if pos is not None:                         # manage the open trade on bar `ts`
            d = by_t[pos["sym"]]
            if ts in d.index and ts > pos["t_in"]:
                bar = d.loc[ts]
                hit_sl = bar.low <= pos["sl"] if pos["side"] > 0 else bar.high >= pos["sl"]
                hit_tp = bar.high >= pos["tp"] if pos["side"] > 0 else bar.low <= pos["tp"]
                exit_px = pos["sl"] if hit_sl else pos["tp"] if hit_tp else None
                if exit_px is None and ts.time() >= pd.Timestamp("15:15").time():
                    exit_px = bar.close
                if exit_px is not None:
                    trades.append(close_trade(pos, exit_px, ts))
                    pos = None
            continue
        if ts.time() >= pd.Timestamp("15:05").time():
            continue
        best = None
        for t, d in by_t.items():
            if ts not in d.index or nxt not in d.index or nxt.date() != ts.date():
                continue
            s = sigs[t].get(ts, 0)
            if s:
                strength = d.at[ts, "vol_ratio"] if np.isfinite(d.at[ts, "vol_ratio"]) else 0
                if best is None or strength > best[2]:
                    best = (t, int(s), strength)
        if best:
            t, side, _ = best
            px = by_t[t].at[nxt, "open"] * (1 + SLIP * side)
            qty = math.floor(NOTIONAL / px)
            if qty > 0:
                pos = {"sym": t, "side": side, "qty": qty, "px": px, "t_in": nxt,
                       "tp": px * (1 + tp * side), "sl": px * (1 - sl * side)}
    return pd.DataFrame(trades)


def close_trade(pos, exit_px, ts):
    exit_px *= (1 - SLIP * pos["side"])
    buy_v, sell_v = (pos["px"], exit_px) if pos["side"] > 0 else (exit_px, pos["px"])
    gross = (exit_px - pos["px"]) * pos["qty"] * pos["side"]
    ch = costs.intraday(buy_v * pos["qty"], sell_v * pos["qty"]).total
    return {"day": ts.date(), "sym": pos["sym"], "side": pos["side"], "gross": gross, "charges": ch, "net": gross - ch}


def summarise(tr: pd.DataFrame, days: list) -> dict:
    if tr.empty:
        return {"trades_per_day": 0, "win_rate_%": 0, "net_rs": 0}
    daily = tr.groupby("day").net.sum().reindex(days, fill_value=0.0)
    wins, losses = tr[tr.net > 0], tr[tr.net <= 0]
    return {"trades": len(tr), "trades_per_day": round(len(tr) / len(days), 1),
            "win_rate_%": round(100 * len(wins) / len(tr), 1),
            "gross_win_rate_%": round(100 * (tr.gross > 0).mean(), 1),
            "avg_win_rs": round(wins.net.mean(), 1) if len(wins) else 0.0,
            "avg_loss_rs": round(losses.net.mean(), 1) if len(losses) else 0.0,
            "gross_rs": round(tr.gross.sum()), "charges_rs": round(tr.charges.sum()), "net_rs": round(tr.net.sum()),
            "net_per_day_rs": round(daily.mean(), 1), "best_day_rs": round(daily.max()), "worst_day_rs": round(daily.min()),
            "green_days_%": round(100 * (daily > 0).mean(), 1)}


def main():
    data = {t: indicators(d) for t, d in load().items()}
    all_days = sorted(set().union(*[set(d.index.date) for d in data.values()]))
    half = len(all_days) // 2
    train, test = all_days[:half], all_days[half:]
    print(f"{len(data)} instruments, {len(all_days)} days ({all_days[0]} to {all_days[-1]}); train {len(train)}, test {len(test)}")
    rows, n_tried = [], 0
    for name, (fn, grid) in STRATS.items():
        cands = []
        for params, (tp, sl) in itertools.product(grid, EXITS):
            n_tried += 1
            s = summarise(run(data, fn, params, tp, sl, train), train)
            cands.append((s.get("net_rs", 0), params, tp, sl, s))
        _, params, tp, sl, s_tr = max(cands, key=lambda c: c[0])
        tr_test = run(data, fn, params, tp, sl, test)
        s_te = summarise(tr_test, test)
        rows.append({"strategy": name, "settings": f"{params or ''} target {tp:.1%} stop {sl:.1%}".strip(),
                     "train_net_per_day": s_tr.get("net_per_day_rs", 0), **s_te})
        tr_test.to_csv(CACHE / f"trades_{name.split()[0].lower()}.csv", index=False)
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 260)
    print(f"\nsettings tried: {n_tried} (picked on the first {len(train)} days)\nTEST on the last {len(test)} days (Rs 10,000 at 5x, all charges):")
    print(out.to_string(index=False))
    out.to_csv(Path(__file__).with_name("a275_results.csv"), index=False)


if __name__ == "__main__":
    main()

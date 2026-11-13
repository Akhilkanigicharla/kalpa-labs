"""5-minute intraday engine (Akhil, 13 Nov 2026: "take trades on 5 mins time frame ... take profit and close").

Each trade opens and closes the same day: take-profit, stop-loss, or a forced exit at 15:15 IST.
No look-ahead: a signal is computed on a bar's CLOSE and filled at the NEXT bar's OPEN. Inside a
bar, if both the stop and the target could have been hit, we assume the STOP hit first.
Costs: Indian intraday equity charges from src/costs.py (brokerage, 0.025% STT on sell, exchange,
SEBI, stamp, GST) + slippage on both sides. Long and short (intraday shorts are allowed in cash
MIS; they must be closed the same day).

Strategies (rules fixed BEFORE the first test, 13 Nov 2026; small grids only):
  orb      Opening-range breakout: range = first 15 min (3 bars). Close above the high -> long,
           below the low -> short. Stop = other side of the range; target = R x range.
  vwap     VWAP trend: after 09:45, close crosses VWAP in the direction of EMA9 vs EMA21.
           Stop and target in % of price.
  rsi_mr   Mean reversion: RSI(14) on 5-min < 25 -> long, > 75 -> short. Target/stop in %.
At most 2 trades a day per strategy. Research and paper only. Not investment advice.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import costs

OPEN, LAST_ENTRY, FORCE_EXIT = time(9, 15), time(14, 45), time(15, 15)
SLIPPAGE_BPS = 2.0            # per side, liquid ETF/index-sized orders
MAX_TRADES_PER_DAY = 2

GRIDS = {
    "orb": [{"r": 1.0}, {"r": 2.0}],
    "vwap": [{"stop": 0.003, "target": 0.006}, {"stop": 0.004, "target": 0.008}],
    "rsi_mr": [{"stop": 0.004, "target": 0.004}, {"stop": 0.006, "target": 0.006}],
}


@dataclass
class Trade:
    day: str
    side: int            # +1 long, -1 short
    entry_at: str
    entry: float
    exit_at: str
    exit: float
    reason: str          # target | stop | eod
    qty: int
    gross: float         # Rs
    cost: float          # Rs

    @property
    def net(self) -> float:
        return self.gross - self.cost


@dataclass
class Result:
    strategy: str
    params: dict
    trades: list[Trade] = field(default_factory=list)

    def stats(self, capital: float) -> dict:
        n = len(self.trades)
        net = np.array([t.net for t in self.trades]) if n else np.zeros(0)
        gross = sum(t.gross for t in self.trades)
        cost = sum(t.cost for t in self.trades)
        wins = net[net > 0]
        days = len({t.day for t in self.trades})
        tstat = float(net.mean() / (net.std(ddof=1) / math.sqrt(n))) if n > 2 and net.std(ddof=1) > 0 else 0.0
        return {"trades": n, "days_traded": days, "win_rate": float(len(wins) / n) if n else 0.0,
                "net_rs": float(net.sum()), "net_pct": float(net.sum() / capital * 100), "gross_rs": float(gross),
                "cost_rs": float(cost), "avg_net_rs": float(net.mean()) if n else 0.0, "t_stat": tstat,
                "by_reason": {r: sum(1 for t in self.trades if t.reason == r) for r in ("target", "stop", "eod")}}


def clean(bars: pd.DataFrame) -> pd.DataFrame:
    """Lower-case OHLC, IST index, regular session only (09:15-15:30)."""
    df = bars.rename(columns=str.lower)[["open", "high", "low", "close"]].copy()
    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_convert("Asia/Kolkata") if idx.tz is not None else idx.tz_localize("Asia/Kolkata")
    df.index = idx
    t = df.index.time
    df = df[(t >= OPEN) & (t < time(15, 30))].dropna()
    return df[~df.index.duplicated()]


def _rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def signals(day: pd.DataFrame, strategy: str, **p) -> pd.DataFrame:
    """Per-bar entry signal (+1/-1/0) and its stop/target, from bars up to and including that bar."""
    out = pd.DataFrame(index=day.index, data={"sig": 0, "stop": np.nan, "target": np.nan})
    c = day["close"]
    if strategy == "orb":
        rng = day.iloc[:3]
        if len(day) < 4:
            return out
        hi, lo = rng["high"].max(), rng["low"].min()
        width = hi - lo
        if width <= 0:
            return out
        after = day.index > rng.index[-1]
        up, dn = after & (c > hi), after & (c < lo)
        out.loc[up, ["sig", "stop", "target"]] = [1, lo, np.nan]
        out.loc[up, "target"] = c[up] + p["r"] * width
        out.loc[dn, ["sig", "stop"]] = [-1, hi]
        out.loc[dn, "target"] = c[dn] - p["r"] * width
    elif strategy == "vwap":
        tp = (day["high"] + day["low"] + day["close"]) / 3
        vwap = tp.expanding().mean()              # index has no volume: equal-weight typical price
        e9, e21 = c.ewm(span=9, adjust=False).mean(), c.ewm(span=21, adjust=False).mean()
        ok = day.index.time >= time(9, 45)
        cross_up = (c > vwap) & (c.shift(1) <= vwap.shift(1)) & (e9 > e21) & ok
        cross_dn = (c < vwap) & (c.shift(1) >= vwap.shift(1)) & (e9 < e21) & ok
        out.loc[cross_up, "sig"], out.loc[cross_dn, "sig"] = 1, -1
        out["stop"] = np.where(out["sig"] == 1, c * (1 - p["stop"]), c * (1 + p["stop"]))
        out["target"] = np.where(out["sig"] == 1, c * (1 + p["target"]), c * (1 - p["target"]))
    elif strategy == "rsi_mr":
        r = _rsi(c)
        ok = day.index.time >= time(9, 30)
        out.loc[(r < 25) & ok, "sig"], out.loc[(r > 75) & ok, "sig"] = 1, -1
        out["stop"] = np.where(out["sig"] == 1, c * (1 - p["stop"]), c * (1 + p["stop"]))
        out["target"] = np.where(out["sig"] == 1, c * (1 + p["target"]), c * (1 - p["target"]))
    else:
        raise ValueError(f"unknown strategy {strategy}")
    out.loc[out["sig"] == 0, ["stop", "target"]] = np.nan
    return out


def _cost(entry: float, exit_: float, qty: int, side: int) -> float:
    buy, sell = (entry, exit_) if side == 1 else (exit_, entry)
    return costs.intraday(buy * qty, sell * qty).total


def run_day(day: pd.DataFrame, strategy: str, capital: float, **p) -> list[Trade]:
    """Walk one session bar by bar. Signal on bar i close -> fill at bar i+1 open."""
    sig = signals(day, strategy, **p)
    trades: list[Trade] = []
    pos = None
    bars = list(day.itertuples())
    slip = SLIPPAGE_BPS / 1e4
    for i in range(len(bars) - 1):
        b, nxt = bars[i], bars[i + 1]
        t_next = nxt.Index.time()
        if pos is None:
            s = sig.iloc[i]
            if s["sig"] != 0 and len(trades) < MAX_TRADES_PER_DAY and t_next <= LAST_ENTRY:
                side = int(s["sig"])
                px = nxt.open * (1 + slip * side)
                qty = int(capital // px)
                # skip if the next open already jumped past the stop or target (gap)
                if qty > 0 and (side * (px - s["stop"]) > 0) and (side * (s["target"] - px) > 0):
                    pos = {"side": side, "entry": px, "at": nxt.Index, "stop": s["stop"], "target": s["target"],
                           "qty": qty, "from": i + 1}
            continue
        # manage the open position on bar i (fills from bar 'from' onward)
        if i < pos["from"]:
            continue
        side, exit_px, reason = pos["side"], None, None
        hit_stop = b.low <= pos["stop"] if side == 1 else b.high >= pos["stop"]
        hit_tgt = b.high >= pos["target"] if side == 1 else b.low <= pos["target"]
        if hit_stop:                                    # stop first when both are possible (conservative)
            exit_px, reason = pos["stop"], "stop"
        elif hit_tgt:
            exit_px, reason = pos["target"], "target"
        elif b.Index.time() >= FORCE_EXIT:
            exit_px, reason = b.close, "eod"
        if exit_px is not None:
            exit_px *= (1 - slip * side)
            gross = side * (exit_px - pos["entry"]) * pos["qty"]
            trades.append(Trade(str(b.Index.date()), side, pos["at"].strftime("%H:%M"), round(pos["entry"], 2),
                                b.Index.strftime("%H:%M"), round(exit_px, 2), reason, pos["qty"], gross,
                                _cost(pos["entry"], exit_px, pos["qty"], side)))
            pos = None
    if pos is not None:                                 # still open at the last bar: close at its close
        last = bars[-1]
        exit_px = last.close * (1 - slip * pos["side"])
        gross = pos["side"] * (exit_px - pos["entry"]) * pos["qty"]
        trades.append(Trade(str(last.Index.date()), pos["side"], pos["at"].strftime("%H:%M"), round(pos["entry"], 2),
                            last.Index.strftime("%H:%M"), round(exit_px, 2), "eod", pos["qty"], gross,
                            _cost(pos["entry"], exit_px, pos["qty"], pos["side"])))
    return trades


def backtest(bars: pd.DataFrame, strategy: str, capital: float = 5_000.0, **p) -> Result:
    df = clean(bars)
    res = Result(strategy, p)
    for _, day in df.groupby(df.index.date):
        if len(day) >= 10:
            res.trades += run_day(day, strategy, capital, **p)
    return res


def verdict(stats: dict, half_stats: tuple[dict, dict], min_trades: int = 30) -> tuple[str, list[str]]:
    """Paper only if: >= 30 trades, net > 0 after costs, t-stat >= 2, and both halves net > 0."""
    why = []
    if stats["trades"] < min_trades:
        why.append(f"only {stats['trades']} trades (need {min_trades})")
    if stats["net_rs"] <= 0:
        why.append("loses money after costs")
    if stats["t_stat"] < 2.0:
        why.append(f"t-stat {stats['t_stat']:.2f} < 2 (could be luck)")
    if any(h["net_rs"] <= 0 for h in half_stats):
        why.append("not profitable in both halves")
    return ("paper" if not why else "rejected"), why


PAPER_SET = {"orb": {"r": 2.0}, "vwap": {"stop": 0.004, "target": 0.008}, "rsi_mr": {"stop": 0.006, "target": 0.006}}
TRADE_COLS = ["day", "strategy", "side", "entry_at", "entry", "exit_at", "exit", "reason", "qty", "gross_rs", "cost_rs", "net_rs"]


def store_bars(bars: pd.DataFrame, path: Path) -> pd.DataFrame:
    """Append 5-min bars to our own history (Yahoo keeps only 60 days). Never in git: Actions cache."""
    new = clean(bars)
    if path.exists():
        old = pd.read_parquet(path)
        new = pd.concat([old, new])
        new = new[~new.index.duplicated(keep="last")].sort_index()
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_parquet(path)
    return new


def paper_day(bars: pd.DataFrame, out: Path, capital: float = 5_000.0, day=None) -> str:
    """Replay one finished session bar by bar for every PAPER_SET strategy. Same day twice = no action."""
    df = clean(bars)
    days = sorted(set(df.index.date))
    if not days:
        return "Intraday paper: no 5-min bars."
    d = day or days[-1]
    session = df[df.index.date == d]
    out.mkdir(parents=True, exist_ok=True)
    led = out / "trades.csv"
    hist = pd.read_csv(led) if led.exists() else pd.DataFrame(columns=TRADE_COLS)
    done = out / "days.txt"
    seen = set(done.read_text(encoding="utf-8").split()) if done.exists() else set()
    lines = [f"Kalpa b7 · 5-min intraday · PAPER · {d} · Rs {capital:,.0f} per strategy"]
    if str(d) in seen:
        return lines[0] + "\nAlready done (no new session). No action."
    rows = []
    for s, prm in PAPER_SET.items():
        for t in (run_day(session, s, capital, **prm) if len(session) >= 10 else []):
            rows.append([t.day, s, "long" if t.side == 1 else "short", t.entry_at, t.entry, t.exit_at, t.exit,
                         t.reason, t.qty, round(t.gross, 2), round(t.cost, 2), round(t.net, 2)])
    if rows:
        hist = pd.concat([hist, pd.DataFrame(rows, columns=TRADE_COLS)], ignore_index=True)
    hist.to_csv(led, index=False)
    done.write_text(" ".join(sorted(seen | {str(d)})) + "\n", encoding="utf-8")
    today = [r for r in rows]
    lines.append(f"Today: {len(today)} trades" + ("" if today else " (no signal)"))
    lines += [f"  {r[1]:7} {r[2]:5} in {r[3]} @ {r[4]} out {r[5]} @ {r[6]} ({r[7]}) net Rs {r[11]:+.2f}" for r in today]
    lines.append(f"Running total since {hist['day'].min() if len(hist) else d} ({len(seen) + 1} sessions):")
    for s in PAPER_SET:
        h = hist[hist["strategy"] == s]
        if len(h):
            lines.append(f"  {s:7} {len(h):3} trades, win {(h['net_rs'] > 0).mean():.0%}, before costs Rs {h['gross_rs'].sum():+.0f}, "
                         f"costs Rs {h['cost_rs'].sum():.0f}, NET Rs {h['net_rs'].sum():+.0f}")
        else:
            lines.append(f"  {s:7} no trades yet")
    lines.append("All 3 were REJECTED on Aug-Nov 2026 data (they lose after costs). Paper only, to collect evidence. Not advice.")
    text = "\n".join(lines)
    (out / "summary.txt").write_text(text + "\n", encoding="utf-8")
    return text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="5-minute intraday backtest (research only)")
    p.add_argument("--symbol", default="NIFTYBEES.NS")
    p.add_argument("--capital", type=float, default=5_000.0)
    p.add_argument("--bars", type=Path, default=None, help="CSV of 5-min bars (else Yahoo, last 60 days)")
    p.add_argument("--paper", type=Path, default=None, help="paper mode: replay today's session into this folder")
    p.add_argument("--store", type=Path, default=None, help="append the fetched 5-min bars to this parquet")
    a = p.parse_args(argv)
    if a.bars:
        bars = pd.read_csv(a.bars, index_col=0, parse_dates=True)
    else:
        import yfinance as yf
        bars = yf.Ticker(a.symbol).history(period="60d", interval="5m", auto_adjust=False)
    if a.store:
        store_bars(bars, a.store)
    if a.paper:
        print(paper_day(bars, a.paper, a.capital))
        return 0
    df = clean(bars)
    days = sorted(set(df.index.date))
    mid = days[len(days) // 2]
    print(f"{a.symbol} 5-min, {len(days)} days {days[0]} .. {days[-1]}, capital Rs {a.capital:,.0f}")
    for s, grid in GRIDS.items():
        for prm in grid:
            r = backtest(bars, s, a.capital, **prm)
            st = r.stats(a.capital)
            h1 = Result(s, prm, [t for t in r.trades if pd.Timestamp(t.day).date() < mid]).stats(a.capital)
            h2 = Result(s, prm, [t for t in r.trades if pd.Timestamp(t.day).date() >= mid]).stats(a.capital)
            v, why = verdict(st, (h1, h2))
            print(f"{s:7} {str(prm):34} trades {st['trades']:3} win {st['win_rate']:.0%} gross Rs {st['gross_rs']:7.1f} "
                  f"costs Rs {st['cost_rs']:6.1f} NET Rs {st['net_rs']:7.1f} ({st['net_pct']:+.1f}%) t {st['t_stat']:+.2f} "
                  f"-> {v.upper()}" + (f" ({'; '.join(why)})" if why else ""))
    print("Research only. Not investment advice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

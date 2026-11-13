"""One CLI for both tracks: python -m src.live.runner --track A|B --mode paper|live

Flow: bars -> strategy target (ONLY bars with timestamp <= decision time are visible)
-> sizing (risk caps) -> Live Guard -> broker -> ledger CSV + Telegram-ready summary
text (written to a file and printed; never sent from here).

Every result is reported next to buy-and-hold of the SAME asset over the SAME paper
period, both after costs and tax (track A: delivery charges + 20% STCG + cess with
set-off; track B: exchange fee + 1% TDS credit + 30% tax + cess per sell, no set-off).

paper (default): FakeBroker, state kept in <out>/state-<track>.json between runs.
live: refused unless ALL hold: env LIVE_TRADING=YES, <flags>/GO says "go", no
<flags>/KILL file, <flags>/GATE_PASS_<track> exists, >= 90 paper days logged. Even
then the adapters are stubs, so no real order is sent. Own money only, not advice.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from typing import Mapping

import pandas as pd

from .. import costs, crypto_tax, risk
from ..strategies import weights
from . import broker as brk
from .guard import IST, GuardConfig, LiveGuard, next_open

PAPER_DAYS_MIN = 90
STCG_RATE = 0.20          # listed equity/ETF held < 12 months (PLAN.md §2 table)
TRACKS = {
    "A": {"market": "NSE", "symbol": "NIFTYBEES", "fractional": False, "slippage_bps": 10.0,
          "stop_pct": 0.20, "label": "NSE ETF trend", "broker": "fyers",
          "limits": "TRACK_A_LIMITS", "max_position_pct": 1.0},
    "B": {"market": "CRYPTO", "symbol": "BTCINR", "fractional": True, "slippage_bps": 20.0,
          "stop_pct": 0.10, "label": "Crypto trend", "broker": "delta",
          "limits": "LIMITS", "max_position_pct": 0.20},
}
STRATEGIES = ("tsmom", "tsmom_vt", "ma_filter_vt", "markov_regime", "hold")
# Track A idle money sits in a liquid ETF. LIQUIDBEES: 4.69%/yr since 2003 after its 0.69% fee
# (anandrathi.com, 1 Jun 2025). Paper mode credits this on idle cash; liquid-ETF gains are taxed
# at the slab rate (ignored here, so the paper number is slightly high on the cash leg).
CASH_RATE = {"A": 0.047, "B": 0.0}
LEDGER_COLUMNS = ["run_at_ist", "asof", "track", "mode", "strategy", "symbol", "side", "qty",
                  "value_pct_capital", "fee_inr", "tds_inr", "status", "reasons", "target_weight",
                  "bot_after_tax_inr", "bench_after_tax_inr", "bot_vs_bench_pct_pts"]


class LookAheadError(AssertionError):
    pass


# ---------------------------------------------------------------- no look-ahead
def visible_bars(bars: pd.DataFrame, decision_time) -> pd.DataFrame:
    """Only bars stamped at or before the decision time. A copy, so nothing later leaks."""
    cut = pd.Timestamp(decision_time)
    return bars.loc[bars.index <= cut].copy()


def decide(bars: pd.DataFrame, decision_time, strategy: str, **params) -> tuple[float, float, pd.Timestamp]:
    """Target weight at the decision time from visible bars only: (weight, close, bar ts)."""
    vis = visible_bars(bars.sort_index(), decision_time)
    if vis.empty:
        raise ValueError("no bars at or before the decision time")
    w = weights(strategy, vis["close"], **params)
    if w.index.max() > pd.Timestamp(decision_time):
        raise LookAheadError("strategy produced a weight after the decision time")
    return float(min(max(w.iloc[-1], 0.0), 1.0)), float(vis["close"].iloc[-1]), vis.index[-1]


def pick_params(close: pd.Series, strategy: str, decision_time, *, cash_rate: float = 0.0) -> dict:
    """Same rule as gate.walk_forward: the config with the best Sharpe over the last
    train_days visible bars. Uses only bars at or before the decision time."""
    from .. import backtest, metrics
    from ..gate import THRESHOLDS
    from ..strategies import param_grid
    vis = close.loc[close.index <= pd.Timestamp(decision_time)]
    grid = param_grid(strategy)
    if len(grid) == 1:
        return dict(grid[0])
    train = THRESHOLDS["train_days"]
    if len(vis) < train + 2:
        raise ValueError(f"need {train + 2} visible bars to pick params, got {len(vis)}")
    scores = []
    for p in grid:
        r = backtest.run(vis, weights(strategy, vis, **p), cash_rate=cash_rate).returns.iloc[-train:]
        scores.append(metrics.sharpe(r))
    best = max(range(len(grid)), key=lambda i: (scores[i], -i))
    return dict(grid[best])


def accrue_cash_interest(fb, last_day: str | None, today: date, rate: float) -> float:
    """Credit idle-cash interest for the calendar days since the last paper run."""
    if not rate or not last_day:
        return 0.0
    days = (today - date.fromisoformat(last_day)).days
    if days <= 0 or fb.cash() <= 0:
        return 0.0
    amt = fb.cash() * ((1 + rate) ** (days / 365) - 1)
    fb._cash += amt
    return amt


# ---------------------------------------------------------------- costs and tax
def fee_fn(track: str):
    if track == "A":
        return lambda side, v: costs.delivery(v if side == "buy" else 0.0, v if side == "sell" else 0.0).total
    return lambda side, v: crypto_tax.fee(v)


def liquidation_after_tax(track: str, cash: float, units: float, basis: float, px: float,
                          realised: list[float], tds_credit: float = 0.0) -> float:
    """Rupees left if everything were sold at px now, after sell costs and all tax.

    realised: gains of past sells. A: set-off allowed, 20% STCG (+cess) on the net.
    B: each gain taxed alone, losses ignored (no set-off); TDS withheld is a credit.
    """
    sell_val = units * px
    sell_cost = fee_fn(track)("sell", sell_val) if units > 0 else 0.0
    gains = realised + ([units * (px - basis)] if units > 0 else [])
    if track == "A":
        tax = max(0.0, sum(gains)) * STCG_RATE * (1 + crypto_tax.CESS)
        return cash + sell_val - sell_cost - tax
    tax = sum(crypto_tax.trade_tax(g) for g in gains)
    # TDS on this sale and all earlier TDS are credits against the tax, so they net out
    return cash + sell_val - sell_cost + tds_credit - tax


def trade_stats(pnl: list[float]) -> dict:
    """Win rate, average win / average loss (payoff ratio) and expectancy per closed sell.
    A strategy can earn with under 50% wins when winners are bigger than losers."""
    wins = [x for x in pnl if x > 0]
    losses = [x for x in pnl if x <= 0]
    n = len(pnl)
    avg_w = sum(wins) / len(wins) if wins else 0.0
    avg_l = -sum(losses) / len(losses) if losses else 0.0
    return {"trades": n, "win_rate": len(wins) / n if n else 0.0, "avg_win": avg_w, "avg_loss": avg_l,
            "payoff": (avg_w / avg_l) if avg_l > 0 else (math.inf if wins else 0.0),
            "expectancy": sum(pnl) / n if n else 0.0}


def _stats_line(pnl: list[float]) -> str:
    s = trade_stats(pnl)
    if not s["trades"]:
        return "Closed trades: 0 (win rate, payoff and expectancy after the first sell)"
    pay = "n/a (no losses)" if math.isinf(s["payoff"]) else f"{s['payoff']:.2f}"
    return (f"Closed trades: {s['trades']} · win rate {s['win_rate']:.0%} · avg win Rs {s['avg_win']:.2f} / "
            f"avg loss Rs {s['avg_loss']:.2f} (payoff {pay}) · expectancy Rs {s['expectancy']:+.2f}/trade")


# ---------------------------------------------------------------- state
def _new_state(capital: float) -> dict:
    return {"capital": capital, "broker": None, "stops": {}, "marks": {}, "traded": {},
            "paper_days": [], "realised": [], "trade_pnl": [], "bench": None}


def load_state(path: Path, capital: float) -> dict:
    if path.exists():
        st = json.loads(path.read_text(encoding="utf-8"))
        st.setdefault("trade_pnl", [])
        if abs(st["capital"] - capital) > 1e-9:
            raise SystemExit(f"state {path} was started with capital {st['capital']}; use that or a new --out")
        return st
    return _new_state(capital)


def live_blockers(track: str, state: dict, env: Mapping[str, str], flags: Path) -> list[str]:
    out = brk.go_blockers(env, flags / "GO")
    if (flags / "KILL").exists():
        out.append("kill switch file present")
    if not (flags / f"GATE_PASS_{track}").exists():
        out.append(f"no gate pass file GATE_PASS_{track} (gate.py verdict 'paper' + Akhil's sign-off)")
    n = len(state.get("paper_days", []))
    if n < PAPER_DAYS_MIN:
        out.append(f"only {n} of {PAPER_DAYS_MIN} paper days logged")
    return out


# ---------------------------------------------------------------- main run
def run_paper(bars: pd.DataFrame, *, track: str, strategy: str, capital: float, out: Path,
              flags: Path, asof=None, flatten: bool = False, stop_pct: float | None = None,
              symbol: str | None = None, params: dict | None = None,
              signal_bars: pd.DataFrame | None = None, cash_rate: float | None = None) -> dict:
    """bars = the traded instrument (fill price). signal_bars (optional) = a cleaner series the
    strategy reads, e.g. the Nifty 50 index for NIFTYBEES (the ETF's Yahoo history has an
    unadjusted 2019 split). params=None -> picked like the gate's walk-forward."""
    t = TRACKS[track]
    symbol = symbol or t["symbol"]
    stop_pct = stop_pct or t["stop_pct"]
    rate = CASH_RATE[track] if cash_rate is None else cash_rate
    bars = bars.sort_index()
    asof = pd.Timestamp(asof) if asof is not None else bars.index[-1]
    sig = signal_bars.sort_index() if signal_bars is not None else bars
    if params is None:
        params = pick_params(visible_bars(sig, asof)["close"], strategy, asof, cash_rate=rate)
    w, _, sig_ts = decide(sig, asof, strategy, **params)
    vis_px = visible_bars(bars, asof)
    if vis_px.empty:
        raise ValueError("no traded-instrument bars at or before the decision time")
    px, bar_ts = float(vis_px["close"].iloc[-1]), vis_px.index[-1]
    if signal_bars is not None and abs((bar_ts - sig_ts).days) > 4:
        raise ValueError(f"signal bar {sig_ts.date()} and price bar {bar_ts.date()} are too far apart")
    d = bar_ts.date()
    # simulated fill time: next NSE open after the close, or just after midnight for crypto
    if t["market"] == "NSE":
        at = next_open("NSE", datetime.combine(d, dtime(16, 0), IST))
    else:
        at = datetime.combine(d + timedelta(days=1), dtime(0, 5), IST)
    sim = [at]

    out.mkdir(parents=True, exist_ok=True)
    spath = out / f"state-{track}.json"
    st = load_state(spath, capital)
    if d.isoformat() in st["paper_days"] and not flatten:
        # same bar again (re-run, or an NSE holiday with no new bar): never trade or log twice
        text = f"Kalpa b7 · Track {track} · PAPER · {d.isoformat()} already done (no new market day). No action."
        return {"weight": w, "decisions": [], "bot": None, "bench": None, "summary": text, "state": st,
                "rows": [], "params": params, "interest": 0.0, "skipped": True}
    fb = brk.FakeBroker(starting_cash=capital, prices={symbol: px}, slippage_bps=t["slippage_bps"],
                        fee_fn=fee_fn(track), tds_rate=crypto_tax.TDS_RATE if track == "B" else 0.0,
                        fractional=t["fractional"], needs_daily_login=(track == "A"),
                        login_date=at.date(), name="paper")
    if st["broker"]:
        fb.load(st["broker"])
    interest = accrue_cash_interest(fb, st["paper_days"][-1] if st["paper_days"] else None, d, rate)
    st["interest"] = st.get("interest", 0.0) + interest
    book = risk.RiskBook(pot=capital, limits=dict(getattr(risk, t["limits"])))
    book.marks = {date.fromisoformat(k): v for k, v in st["marks"].items()}
    guard = LiveGuard(fb, book, GuardConfig(market=t["market"], capital=capital, kill_file=flags / "KILL",
                                                 max_position_pct=t["max_position_pct"]),
                      clock=lambda: sim[0], sleep=lambda s: sim.__setitem__(0, sim[0] + timedelta(seconds=s)),
                      traded={k: set(v) for k, v in st["traded"].items()})

    held = fb.positions().get(symbol, 0.0)
    guard.mark(fb.cash() + fb.tds_withheld + held * px)
    decisions = []
    if flatten:
        decisions += guard.flatten() if guard.kill_switch_on() else []
    elif held > 0 and symbol in st["stops"] and px <= st["stops"][symbol]:
        decisions.append(guard.submit(brk.OrderRequest(symbol, "sell", held, tag="stop")))
    else:
        base = min(capital, fb.cash() + held * px)
        raw = w * base / px
        target = math.floor(raw + 1e-9) if not t["fractional"] else math.floor(raw * 1e6) / 1e6
        diff = target - held
        if abs(diff) * px > 0.01 * capital:
            if diff > 0:
                stop = px * (1 - stop_pct)
                cap_risk = book.limits["per_trade_risk"] * capital / (px * stop_pct)
                cap_size = guard.config.max_position_pct * capital / px - held
                qty = min(diff, cap_risk, cap_size)
                qty = math.floor(qty + 1e-9) if not t["fractional"] else math.floor(qty * 1e6) / 1e6
                if qty > 0:
                    decisions.append(guard.submit(brk.OrderRequest(symbol, "buy", qty, stop_price=stop)))
            else:
                qty = held if target <= 0 else -diff
                decisions.append(guard.submit(brk.OrderRequest(symbol, "sell", qty)))

    # bookkeeping: realised gains, stops
    basis_before = st["broker"]["avg_cost"].get(symbol, 0.0) if st["broker"] else 0.0
    for dec in decisions:
        r = dec.result
        if r is None or r.status != "filled":
            continue
        if r.side == "sell":
            gain = r.qty * (r.avg_price - basis_before)      # cost of acquisition only
            st["realised"].append(gain)
            st["trade_pnl"].append(gain - r.fee)              # net of the sell fee, for stats
            if symbol not in fb.positions():
                st["stops"].pop(symbol, None)
        else:
            st["stops"][symbol] = dec.request.stop_price

    units = fb.positions().get(symbol, 0.0)
    bot = liquidation_after_tax(track, fb.cash(), units, fb.avg_cost.get(symbol, 0.0), px,
                                st["realised"], fb.tds_withheld)
    # buy-and-hold benchmark of the same asset from the first paper day, same costs/tax
    if st["bench"] is None:
        bpx = px * (1 + t["slippage_bps"] / 1e4)
        if t["fractional"]:
            bu = capital / (bpx * (1 + crypto_tax.EXCHANGE_FEE * (1 + crypto_tax.GST_ON_FEE)))
        else:
            bu = math.floor(capital / (bpx * 1.002))
        bcash = capital - bu * bpx - fee_fn(track)("buy", bu * bpx)
        st["bench"] = {"start": d.isoformat(), "units": bu, "basis": bpx, "cash": bcash}
    b = st["bench"]
    bench = liquidation_after_tax(track, b["cash"], b["units"], b["basis"], px * (1 - t["slippage_bps"] / 1e4), [])
    st["params"] = params

    st["broker"] = fb.to_dict()
    st["marks"] = {k.isoformat(): v for k, v in book.marks.items()}
    st["traded"] = {k: sorted(v) for k, v in guard.traded.items()}
    if d.isoformat() not in st["paper_days"]:
        st["paper_days"].append(d.isoformat())
    spath.write_text(json.dumps(st, indent=1), encoding="utf-8")

    rows = _ledger_rows(track, strategy, symbol, capital, d, at, w, decisions, bot, bench)
    _append_ledger(out / f"ledger-{track}.csv", rows)
    text = summary_text(track, strategy, symbol, capital, d, w, decisions, bot, bench, st, guard)
    (out / f"summary-{track}.txt").write_text(text + "\n", encoding="utf-8")
    return {"weight": w, "decisions": decisions, "bot": bot, "bench": bench, "summary": text,
            "state": st, "rows": rows, "params": params, "interest": interest}


def _ledger_rows(track, strategy, symbol, capital, d, at, w, decisions, bot, bench) -> list[list]:
    vs = round((bot - bench) / capital * 100, 2)
    common_tail = [round(w, 4), round(bot, 2), round(bench, 2), vs]
    if not decisions:
        return [[at.isoformat(), d.isoformat(), track, "paper", strategy, symbol, "hold", 0, 0.0,
                 0.0, 0.0, "no_change", ""] + common_tail]
    rows = []
    for dec in decisions:
        r, q = dec.result, dec.request
        val = (r.qty * r.avg_price / capital * 100) if r and r.avg_price else 0.0
        status = r.status if r else "blocked"
        rows.append([dec.at.isoformat(), d.isoformat(), track, "paper", strategy, symbol, q.side, q.qty,
                     round(val, 2), round(r.fee, 2) if r else 0.0, round(r.tds, 2) if r else 0.0,
                     status, ";".join(dec.reasons) or (r.reason if r else "")] + common_tail)
    return rows


def _append_ledger(path: Path, rows: list[list]) -> None:
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        if new:
            wr.writerow(LEDGER_COLUMNS)
        wr.writerows(rows)


def summary_text(track, strategy, symbol, capital, d, w, decisions, bot, bench, st, guard) -> str:
    t = TRACKS[track]
    if decisions:
        parts = []
        for dec in decisions:
            r = dec.result
            what = f"{dec.request.side.upper()} {dec.request.qty:g} {symbol}"
            parts.append(f"{what} -> {r.status}" + (f" (fee Rs {r.fee:.2f})" if r and r.status == "filled" else "")
                         if r else f"{what} -> BLOCKED ({', '.join(dec.reasons)})")
        order = "; ".join(parts)
    else:
        order = "no change"
    loss = [k for k in ("day", "week", "month") if guard.book.loss(k, guard.clock().astimezone(IST).date())
            >= guard.book.limits[f"{'daily' if k == 'day' else k + 'ly'}_loss"] - 1e-9]
    dd = guard.book.drawdown(guard.clock().astimezone(IST).date())
    paused = dd >= guard.book.limits["drawdown_stop"] - 1e-9
    return "\n".join([
        f"Kalpa b7 · Track {track} ({t['label']}) · PAPER · as of {d.isoformat()}",
        *([f"ALERT: PAUSED, {dd:.0%} below peak (limit {guard.book.limits['drawdown_stop']:.0%}). No new buys. Akhil decides."]
          if paused else []),
        f"{symbol} target {w:.0%} of Rs {capital:,.0f} ({strategy} {st.get('params') or ''})".rstrip(),
        f"Idle cash interest so far: Rs {st.get('interest', 0.0):,.2f} (liquid-ETF rate {CASH_RATE[track]:.1%}/yr)",
        f"Order: {order}",
        f"Bot after costs + tax: Rs {bot:,.2f} ({bot / capital - 1:+.2%})",
        f"Buy-and-hold {symbol} since {st['bench']['start']}: Rs {bench:,.2f} ({bench / capital - 1:+.2%}) "
        f"-> bot {(bot - bench) / capital * 100:+.2f} pts",
        _stats_line(st["trade_pnl"]),
        f"Fall from peak: {dd:.1%} (pause at {guard.book.limits['drawdown_stop']:.0%}) · "
        f"Paper days: {len(st['paper_days'])}/{PAPER_DAYS_MIN} · loss caps "
        f"{'HIT: ' + ', '.join(loss) if loss else 'OK'} · kill switch {'ON' if guard.kill_switch_on() else 'off'}",
        "Own money only. Not advice.",
    ])


def _load_bars(a) -> pd.DataFrame:
    from .. import data
    if a.bars:
        return data.normalise(pd.read_csv(a.bars, index_col=0, parse_dates=True))
    if a.synthetic:
        return data.synthetic_prices(900, seed=4 if a.track == "A" else 7,
                                     sigma=0.18 if a.track == "A" else 0.60, regime_days=120,
                                     regime_drift=0.3)
    if a.track == "A":
        return data.get_daily(a.symbol or TRACKS["A"]["symbol"], strict=False, refresh=True)
    raise SystemExit("track B needs --bars CSV or --synthetic (crypto data fetcher is a TODO)")


def main(argv: list[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env = os.environ if env is None else env
    p = argparse.ArgumentParser(description="b7 runner: guard -> broker. Paper by default.")
    p.add_argument("--track", choices=("A", "B"), required=True)
    p.add_argument("--mode", choices=("paper", "live"), default="paper")
    p.add_argument("--strategy", choices=STRATEGIES, default="tsmom_vt")
    p.add_argument("--symbol", default=None)
    p.add_argument("--capital", type=float, default=5_000.0)
    p.add_argument("--asof", default=None, help="decision date; later bars are invisible")
    p.add_argument("--bars", type=Path, default=None)
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--signal-symbol", default=None, help="read the signal from this series (e.g. ^NSEI)")
    p.add_argument("--signal-bars", type=Path, default=None, help="CSV for the signal series")
    p.add_argument("--out", type=Path, default=brk.LIVE_DIR / "out")
    p.add_argument("--flags", type=Path, default=brk.LIVE_DIR)
    p.add_argument("--broker", default=None, help="live adapter: fyers|dhan (A), delta|coindcx (B)")
    p.add_argument("--flatten", action="store_true", help="sell everything (only if KILL file exists)")
    a = p.parse_args(argv)
    try:
        GuardConfig(capital=a.capital)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2

    if a.mode == "live":
        st = load_state(a.out / f"state-{a.track}.json", a.capital) if (a.out / f"state-{a.track}.json").exists() \
            else _new_state(a.capital)
        blockers = live_blockers(a.track, st, env, a.flags)
        if blockers:
            print("LIVE REFUSED:\n  - " + "\n  - ".join(blockers), file=sys.stderr)
            return 2
        name = a.broker or TRACKS[a.track]["broker"]
        cls = brk.ADAPTERS[a.track].get(name)
        if cls is None:
            print(f"LIVE REFUSED: unknown broker {name} for track {a.track}", file=sys.stderr)
            return 2
        try:
            adapter = cls(env=env, go_file=a.flags / "GO")
            adapter.cash()
        except (brk.LiveRefused, NotImplementedError) as e:
            print(f"LIVE REFUSED: {e}", file=sys.stderr)
            return 3
        return 3   # unreachable while adapters are stubs

    sig = None
    if a.signal_bars:
        from .. import data
        sig = data.normalise(pd.read_csv(a.signal_bars, index_col=0, parse_dates=True))
    elif a.signal_symbol:
        from .. import data
        sig = data.get_daily(a.signal_symbol, strict=False, refresh=True)
    res = run_paper(_load_bars(a), track=a.track, strategy=a.strategy, capital=a.capital, out=a.out,
                    flags=a.flags, asof=a.asof, flatten=a.flatten, symbol=a.symbol, signal_bars=sig)
    print(res["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

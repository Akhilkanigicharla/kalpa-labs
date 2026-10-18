"""Paper Trader (Q7.9): end-of-day signals, simulated NEXT-OPEN fills, Indian delivery
costs, capital rules from src/risk.py. Makes no broker calls and holds no keys.

Timing matches the backtester: the weight decided at the close of day t is acted on
when it differs from day t-1 by more than 1% (the same rule backtest.py uses to count
trades). The paper fill happens at the OPEN of day t+1; if t is the last bar the order
stays "pending" until the next run has that open.

Sizing: target = weight x equity, then capped by the risk rules. Each buy carries a
stop STOP_PCT below entry, used for the 0.5%-of-pot per-trade risk budget (stops are
not simulated as exits; exits come only from the signal, so trades match the backtest).

The ledger holds no raw prices (NSE data terms): only quantities, % of pot, rupee costs
and status. Research code, paper only, not advice.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

from . import costs, risk
from .strategies import weights

STOP_PCT = 0.05            # research default for sizing; part of the Q7.8 sign-off
MIN_CHANGE = 0.01          # same threshold backtest.Result.trades uses
LEDGER_COLUMNS = ["date", "signal_date", "trial", "symbol", "side", "qty", "value_pct_pot",
                  "cost_inr", "equity_pct", "status", "reason"]


@dataclass
class Signal:
    signal_date: date
    side: str
    target_weight: float


@dataclass
class Fill:
    signal_date: date
    fill_date: date | None
    symbol: str
    side: str
    qty: int
    fill_price: float | None
    cost_inr: float
    status: str            # filled | blocked | skipped | pending
    reason: str = ""


@dataclass
class PaperRun:
    pot: float
    book: risk.RiskBook
    cash: float
    signals: list[Signal] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    equity: dict[date, float] = field(default_factory=dict)


def _qty_for_buy(target_qty: int, held: int, entry: float, pot: float, limits: dict) -> tuple[int, str]:
    want = max(0, target_qty - held)
    by_risk = math.floor(limits["per_trade_risk"] * pot / (entry * STOP_PCT) + 1e-9)
    by_size = math.floor(limits["position_size"] * pot / entry + 1e-9) - held
    qty = max(0, min(want, by_risk, by_size))
    why = "" if qty == want else ("capped by per-trade risk" if qty == by_risk else "capped by position size")
    return qty, why


def dry_run(bars: pd.DataFrame, strategy: str, *, days: int = 20, symbol: str = "NIFTYBEES",
            pot: float = 25_000.0, ledger: Path | None = None, trial: str = "dry-run",
            include_last: bool = False, breach_log: Path | None = None, **params) -> PaperRun:
    """Replay the last `days` signal days. With include_last=False the final bar is used only
    as the next open for the day before it (so every signal in the window can fill)."""
    bars = bars.sort_index()
    close, open_ = bars["close"], bars["open"]
    w = weights(strategy, close, **params).reindex(close.index).fillna(0.0).clip(0.0, 1.0)
    idx = close.index
    window = idx[-days:] if include_last else idx[-days - 1:-1]
    book = risk.RiskBook(pot=pot, breach_log=breach_log)
    run = PaperRun(pot=pot, book=book, cash=pot)
    for t in window:
        i = idx.get_loc(t)
        d = t.date()
        held = book.positions.get(symbol, 0)
        eq = run.cash + held * float(close.iloc[i])
        book.mark(d, eq)
        run.equity[d] = eq
        dw = float(w.iloc[i] - (w.iloc[i - 1] if i > 0 else 0.0))
        if abs(dw) <= MIN_CHANGE:
            continue
        side = "buy" if dw > 0 else "sell"
        run.signals.append(Signal(d, side, float(w.iloc[i])))
        entry = float(close.iloc[i])
        target_qty = math.floor(float(w.iloc[i]) * eq / entry + 1e-9)
        if side == "buy":
            qty, why = _qty_for_buy(target_qty, held, entry, pot, book.limits)
            stop = entry * (1 - STOP_PCT)
        else:
            qty, why, stop = (held if w.iloc[i] <= 0 else max(0, held - target_qty)), "", None
        if qty <= 0:
            run.fills.append(Fill(d, None, symbol, side, 0, None, 0.0, "skipped",
                                  why or ("target already held" if side == "buy" else
                                         "nothing held" if held == 0 else "holding already below target")))
            continue
        out = risk.submit(risk.Order(d, symbol, side, qty, entry, stop, "signal"), book)
        if out.blocked:
            run.fills.append(Fill(d, None, symbol, side, qty, None, 0.0, "blocked", ";".join(out.breaches)))
            continue
        if i + 1 >= len(idx):
            run.fills.append(Fill(d, None, symbol, side, qty, None, 0.0, "pending", "fills at next open"))
            continue
        px = float(open_.iloc[i + 1])
        value = qty * px
        c = costs.delivery(value if side == "buy" else 0.0, value if side == "sell" else 0.0).total
        run.cash += (-value if side == "buy" else value) - c
        run.fills.append(Fill(d, idx[i + 1].date(), symbol, side, qty, px, round(c, 2), "filled", why))
    if ledger is not None:
        write_ledger(run, ledger, trial)
    return run


def place_manual(run: PaperRun, bars: pd.DataFrame, symbol: str, side: str, qty: int) -> Fill:
    """A trade the signal didn't produce. Always goes through the Risk Warden (rule 7)."""
    t = bars.index[-1]
    px = float(bars["close"].iloc[-1])
    o = risk.Order(t.date(), symbol, side, qty, px, px * (1 - STOP_PCT) if side == "buy" else None, "manual")
    out = risk.submit(o, run.book)
    f = Fill(t.date(), None, symbol, side, qty, None, 0.0, "blocked" if out.blocked else "pending",
             ";".join(out.breaches))
    run.fills.append(f)
    return f


def write_ledger(run: PaperRun, path: Path, trial: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        wr = csv.writer(fh)
        if new:
            wr.writerow(LEDGER_COLUMNS)
        for f in run.fills:
            when = f.fill_date or f.signal_date
            eq = run.equity.get(f.signal_date, run.pot)
            val = (f.qty * f.fill_price / run.pot * 100) if f.fill_price else 0.0
            wr.writerow([when.isoformat(), f.signal_date.isoformat(), trial, f.symbol, f.side, f.qty,
                         round(val, 2), f.cost_inr, round((eq / run.pot - 1) * 100, 2), f.status, f.reason])


def main(argv: list[str] | None = None) -> int:
    import argparse
    from . import data
    p = argparse.ArgumentParser(description="Paper dry run over past days (no broker calls).")
    p.add_argument("--symbol", default="NIFTYBEES")
    p.add_argument("--strategy", default="sma_cross")
    p.add_argument("--days", type=int, default=20)
    p.add_argument("--pot", type=float, default=25_000.0)
    p.add_argument("--ledger", type=Path, default=None)
    p.add_argument("--synthetic", action="store_true")
    a = p.parse_args(argv)
    bars = data.synthetic_prices(900, seed=4) if a.synthetic else data.get_daily(a.symbol, strict=False)
    run = dry_run(bars, a.strategy, days=a.days, symbol=a.symbol, pot=a.pot, ledger=a.ledger)
    print(f"{len(run.signals)} signals in the last {a.days} days (capital rules {risk.LIMITS_STATUS})")
    for f in run.fills:
        print(f"  {f.signal_date} {f.side:4} qty {f.qty:4} {f.status:8} cost Rs {f.cost_inr:.2f} {f.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

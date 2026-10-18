"""Risk Warden (Q7.11): blocks paper "orders" that break the capital rules (PLAN.md §5a).

LIMITS ARE PENDING CEO SIGN-OFF (Q7.8, capital-rules.md). Paper only: nothing here
talks to a broker. Every blocked order is written to a breach log.

Rules enforced (fractions of the pot unless stated):
  per_trade_risk      a buy may risk at most 0.5% of the pot from entry to its stop
  no_stop             a buy must carry a stop below its entry price
  position_size       one position may be at most 20% of the pot
  max_open_positions  at most 3 open positions (Guard; §5a draft said 5)
  daily_loss          a loss of >= 1% today means no new buys today
  weekly_loss         >= 2% this ISO week: no new buys this week
  monthly_loss        >= 4% this month: no new buys for the rest of the month
  drawdown_stop       equity >= 10% below its peak: no new buys at all (back to research)
  override            any order not produced by the signal (rule 7)
  oversell            selling more than is held
Sells that only reduce a position are never blocked by the loss limits.
Research code, paper only, not advice.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

LIMITS = {
    "per_trade_risk": 0.005,
    "position_size": 0.20,
    "max_open_positions": 3,   # Guard: 3 open (stricter than §5a draft 5)
    "daily_loss": 0.01,
    "weekly_loss": 0.02,
    "monthly_loss": 0.04,
    "drawdown_stop": 0.10,
}
LIMITS_STATUS = "pending CEO sign-off (Q7.8)"
EPS = 1e-9


@dataclass
class Order:
    date: date
    symbol: str
    side: str              # "buy" or "sell"
    qty: int
    price: float           # expected entry/exit price (signal-day close for paper)
    stop: float | None     # required for buys
    source: str = "signal"


@dataclass
class Outcome:
    order: Order
    breaches: list[str]

    @property
    def blocked(self) -> bool:
        return bool(self.breaches)


@dataclass
class RiskBook:
    pot: float
    breach_log: Path | None = None
    limits: dict = field(default_factory=lambda: dict(LIMITS))
    positions: dict[str, int] = field(default_factory=dict)
    marks: dict[date, float] = field(default_factory=dict)   # equity at each close

    def mark(self, d: date, equity: float) -> None:
        self.marks[d] = float(equity)

    # equity helpers -------------------------------------------------------
    def _last_on_or_before(self, d: date) -> float:
        days = [k for k in self.marks if k <= d]
        return self.marks[max(days)] if days else self.pot

    def _last_before(self, d: date) -> float:
        days = [k for k in self.marks if k < d]
        return self.marks[max(days)] if days else self.pot

    def loss(self, period: str, d: date) -> float:
        """Loss in the period containing d, as a positive fraction of the pot."""
        now = self._last_on_or_before(d)
        if period == "day":
            if d not in self.marks:
                return 0.0
            ref = self._last_before(d)
        elif period == "week":
            iso = d.isocalendar()
            start = date.fromisocalendar(iso[0], iso[1], 1)
            ref = self._last_before(start)
        elif period == "month":
            ref = self._last_before(d.replace(day=1))
        else:
            raise ValueError(period)
        return max(0.0, (ref - now) / self.pot)

    def drawdown(self, d: date) -> float:
        hist = [v for k, v in self.marks.items() if k <= d] or [self.pot]
        peak = max(max(hist), self.pot)
        return max(0.0, (peak - self._last_on_or_before(d)) / peak)


def check(o: Order, b: RiskBook) -> list[str]:
    """Return the rules this order breaks (empty list = allowed). Does not change the book."""
    L, out = b.limits, []
    if o.source != "signal":
        out.append("override")
    if o.qty <= 0:
        out.append("bad_qty")
    held = b.positions.get(o.symbol, 0)
    if o.side == "sell":
        if o.qty > held:
            out.append("oversell")
        return out
    if o.side != "buy":
        return out + ["bad_side"]
    if o.stop is None or o.stop >= o.price:
        out.append("no_stop")
    elif o.qty * (o.price - o.stop) > L["per_trade_risk"] * b.pot + EPS:
        out.append("per_trade_risk")
    if (held + o.qty) * o.price > L["position_size"] * b.pot + EPS:
        out.append("position_size")
    if held == 0 and sum(1 for q in b.positions.values() if q > 0) >= L["max_open_positions"]:
        out.append("max_open_positions")
    if b.loss("day", o.date) >= L["daily_loss"] - EPS:
        out.append("daily_loss")
    if b.loss("week", o.date) >= L["weekly_loss"] - EPS:
        out.append("weekly_loss")
    if b.loss("month", o.date) >= L["monthly_loss"] - EPS:
        out.append("monthly_loss")
    if b.drawdown(o.date) >= L["drawdown_stop"] - EPS:
        out.append("drawdown_stop")
    return out


def submit(o: Order, b: RiskBook) -> Outcome:
    """Check an order; if allowed, apply it to the book's positions, else log the breach."""
    res = Outcome(o, check(o, b))
    if res.blocked:
        if b.breach_log is not None:
            new = not Path(b.breach_log).exists()
            Path(b.breach_log).parent.mkdir(parents=True, exist_ok=True)
            with open(b.breach_log, "a", newline="") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["date", "symbol", "side", "qty", "source", "breaches"])
                w.writerow([o.date.isoformat(), o.symbol, o.side, o.qty, o.source, ";".join(res.breaches)])
        return res
    sign = 1 if o.side == "buy" else -1
    b.positions[o.symbol] = b.positions.get(o.symbol, 0) + sign * o.qty
    if b.positions[o.symbol] == 0:
        del b.positions[o.symbol]
    return res

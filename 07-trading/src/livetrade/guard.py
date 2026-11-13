"""Live Guard (A153 §4.2): every order to any broker passes through here first.

Rules (all orders):
  rate_limit        at most 2 orders per rolling second (SEBI line: 10/s per exchange)
  market_closed     NSE: weekdays 09:15-15:30 IST, not on NSE_HOLIDAYS; crypto: 24x7
  login_required    Indian brokers need today's (IST) 2FA login before any order
  one_trade_per_day trend strategies: one signal order per symbol per IST day
                    (stop / flatten exits are exempt)
Rules (buys only):
  kill_switch       the kill-switch file exists: no buys at all; flatten() sells all
  no_stop           a buy must carry stop_price below the current quote
  max_position      symbol value after the buy <= max_position_pct x capital
  capital_cap       everything the bot holds after the buy <= capital (Rs 5,000 default,
                    hard max Rs 10,000, raised only by editing HARD_MAX_CAPITAL with Akhil)
  + every src/risk.py rule (daily 1% / weekly 2% / monthly 4% loss caps, drawdown stop,
    0.5% per-trade risk, max open positions, oversell, override)
Blocked orders never reach the broker. Own money only, not advice.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path
from typing import Callable

from .. import risk
from .broker import KILL_FILE, Broker, OrderRequest, OrderResult

IST = timezone(timedelta(hours=5, minutes=30))   # India has no DST
DEFAULT_CAPITAL = 5_000.0
HARD_MAX_CAPITAL = 10_000.0
MAX_ORDERS_PER_SEC = 2
NSE_OPEN, NSE_CLOSE = dtime(9, 15), dtime(15, 30)
# PLACEHOLDER: fill each year from the NSE trading-holiday circular (nseindia.com) and
# check it twice before live use. Empty = only weekends are treated as closed.
NSE_HOLIDAYS: frozenset[date] = frozenset()
EXEMPT_TAGS = ("stop", "flatten")


@dataclass
class GuardConfig:
    market: str = "NSE"                 # "NSE" | "CRYPTO"
    capital: float = DEFAULT_CAPITAL
    max_position_pct: float = 0.20
    max_orders_per_sec: int = MAX_ORDERS_PER_SEC
    one_trade_per_symbol_per_day: bool = True
    kill_file: Path = KILL_FILE
    holidays: frozenset[date] = NSE_HOLIDAYS

    def __post_init__(self):
        if self.market not in ("NSE", "CRYPTO"):
            raise ValueError("market must be NSE or CRYPTO")
        if not 0 < self.capital <= HARD_MAX_CAPITAL:
            raise ValueError(f"capital must be > 0 and <= hard max Rs {HARD_MAX_CAPITAL:,.0f}")
        if self.max_orders_per_sec > 9:
            raise ValueError("stay under SEBI's 10 orders/second")
        self.kill_file = Path(self.kill_file)


@dataclass
class Decision:
    request: OrderRequest
    at: datetime
    reasons: list[str]
    result: OrderResult | None = None

    @property
    def allowed(self) -> bool:
        return not self.reasons


def market_open(market: str, now: datetime, holidays: frozenset[date] = NSE_HOLIDAYS) -> bool:
    if market == "CRYPTO":
        return True
    t = now.astimezone(IST)
    return t.weekday() < 5 and t.date() not in holidays and NSE_OPEN <= t.time() <= NSE_CLOSE


def next_open(market: str, now: datetime, holidays: frozenset[date] = NSE_HOLIDAYS) -> datetime:
    """`now` if the market is open, else the next NSE session open (09:15 IST)."""
    if market_open(market, now, holidays):
        return now
    t = now.astimezone(IST)
    d = t.date() if t.time() < NSE_OPEN else t.date() + timedelta(days=1)
    while d.weekday() >= 5 or d in holidays:
        d += timedelta(days=1)
    return datetime.combine(d, NSE_OPEN, IST)


@dataclass
class LiveGuard:
    broker: Broker
    book: risk.RiskBook
    config: GuardConfig = field(default_factory=GuardConfig)
    clock: Callable[[], datetime] = lambda: datetime.now(IST)
    sleep: Callable[[float], None] = time.sleep
    traded: dict[str, set[str]] = field(default_factory=dict)   # IST date iso -> symbols
    log: list[Decision] = field(default_factory=list)
    _sent: list[datetime] = field(default_factory=list)

    def __post_init__(self):
        if abs(self.book.pot - self.config.capital) > 1e-9:
            raise ValueError("RiskBook pot must equal the guard capital")
        self.book.limits["position_size"] = min(self.book.limits["position_size"],
                                                self.config.max_position_pct)

    def kill_switch_on(self) -> bool:
        return self.config.kill_file.exists()

    def _rate_ok(self, now: datetime) -> bool:
        self._sent = [t for t in self._sent if (now - t).total_seconds() < 1.0]
        return len(self._sent) < self.config.max_orders_per_sec

    def mark(self, equity: float) -> None:
        self.book.mark(self.clock().astimezone(IST).date(), equity)

    def check(self, req: OrderRequest, now: datetime | None = None) -> list[str]:
        now = now or self.clock()
        today = now.astimezone(IST).date()
        out: list[str] = []
        cfg, b = self.config, self.broker
        if not self._rate_ok(now):
            out.append("rate_limit")
        if not market_open(cfg.market, now, cfg.holidays):
            out.append("market_closed")
        if b.needs_daily_login and b.login_date != today:
            out.append("login_required")
        if (cfg.one_trade_per_symbol_per_day and req.tag not in EXEMPT_TAGS
                and req.symbol in self.traded.get(today.isoformat(), set())):
            out.append("one_trade_per_day")
        try:
            px = b.quote(req.symbol)
        except Exception:
            return out + ["no_quote"]
        pos = b.positions()
        if req.side == "buy":
            if self.kill_switch_on():
                out.append("kill_switch")
            if req.stop_price is None or req.stop_price >= px:
                out.append("no_stop")
            held_val = pos.get(req.symbol, 0.0) * px
            if held_val + req.qty * px > cfg.max_position_pct * cfg.capital + 1e-9:
                out.append("max_position")
            try:
                exposure = sum(q * (px if s == req.symbol else b.quote(s)) for s, q in pos.items())
            except Exception:
                return out + ["no_quote"]
            if exposure + req.qty * px > cfg.capital + 1e-9:
                out.append("capital_cap")
        self.book.positions = {s: q for s, q in pos.items()}
        ro = risk.Order(today, req.symbol, req.side, req.qty, px, req.stop_price,
                        "signal" if req.tag in ("signal",) + EXEMPT_TAGS else req.tag)
        for r in risk.check(ro, self.book):
            if r not in out:
                out.append(r)
        return out

    def submit(self, req: OrderRequest) -> Decision:
        now = self.clock()
        d = Decision(req, now, self.check(req, now))
        if d.allowed:
            self._send(d, now)
        self.log.append(d)
        return d

    def _send(self, d: Decision, now: datetime) -> None:
        self._sent.append(now)
        d.result = self.broker.place_order(d.request)
        if d.result.status == "filled" and d.request.tag not in EXEMPT_TAGS:
            self.traded.setdefault(now.astimezone(IST).date().isoformat(), set()).add(d.request.symbol)

    def flatten(self) -> list[Decision]:
        """Sell every position (kill switch). Skips loss caps and the one-trade rule, but
        still respects the rate limit (waits) and market hours."""
        out = []
        for sym, qty in self.broker.positions().items():
            if qty <= 0:
                continue
            req = OrderRequest(sym, "sell", qty, tag="flatten")
            now = self.clock()
            while not self._rate_ok(now):
                self.sleep(0.25)
                now = self.clock()
            reasons = [] if market_open(self.config.market, now, self.config.holidays) else ["market_closed"]
            if self.broker.needs_daily_login and self.broker.login_date != now.astimezone(IST).date():
                reasons.append("login_required")
            d = Decision(req, now, reasons)
            if d.allowed:
                self._send(d, now)
            self.log.append(d)
            out.append(d)
        return out

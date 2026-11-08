"""Live Guard (A153): the ONLY path from a strategy to a real broker or exchange.

Akhil, 6 Nov 2026: the bot trades his own real money. This module makes that safe by construction:

  1. Dry run by default. Real orders need ALL of: env KL_LIVE=yes, a broker adapter with his keys
     (set by Akhil as GitHub secrets, never in code or chat), and the strategy's trial marked "pass"
     in research/trials.csv by the gate (PSR/DSR/PBO, walk-forward, paper run).
  2. Capital cap: the bot only ever sees KL_LIVE_CAPITAL (default ₹5,000) of the account, and only
     touches symbols in its universe, never Akhil's other holdings.
  3. Every order goes through risk.check (stop-loss on every buy, 0.5% risk per trade, daily/weekly/
     monthly loss caps, drawdown stop, max positions) before it can reach the broker.
  4. Kill switch: a file named KILL in 07-trading/ or env KL_KILL=1 cancels open orders, closes every
     position and stops. The daily loss cap does the same automatically.
  5. SEBI retail-algo limit: fewer than 10 orders per second (we cap at 5) and a daily order budget.
  6. Every order, block and kill is sent to Akhil's PRIVATE Telegram chat (never a channel id).

Strategy code never imports a broker: it returns target quantities; run_once turns them into orders.
"""
from __future__ import annotations

import csv
import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Protocol

from .risk import Order, RiskBook, check

HERE = Path(__file__).resolve().parent.parent
TRIALS = HERE / "research" / "trials.csv"
MAX_OPS = 5            # orders per second (SEBI threshold for unregistered personal algos is 10)
MAX_ORDERS_DAY = 20    # daily order budget (bug guard, A153 research)


class Broker(Protocol):
    name: str
    def cash(self) -> float: ...
    def positions(self) -> dict[str, int]: ...
    def ltp(self, symbol: str) -> float: ...
    def place(self, symbol: str, side: str, qty: int, stop: float | None) -> str: ...
    def cancel_all(self) -> None: ...


@dataclass
class DryRunBroker:
    """Simulated broker: fills at the given prices, no network. Used by default and in tests."""
    prices: dict[str, float]
    cash_inr: float = 5000.0
    held: dict[str, int] = field(default_factory=dict)
    orders: list[dict] = field(default_factory=list)
    name: str = "dry-run"

    def cash(self) -> float:
        return self.cash_inr

    def positions(self) -> dict[str, int]:
        return dict(self.held)

    def ltp(self, symbol: str) -> float:
        return self.prices[symbol]

    def place(self, symbol, side, qty, stop):
        px = self.prices[symbol]
        sign = 1 if side == "buy" else -1
        self.held[symbol] = self.held.get(symbol, 0) + sign * qty
        if self.held[symbol] == 0:
            del self.held[symbol]
        self.cash_inr -= sign * qty * px
        oid = f"DRY{len(self.orders) + 1}"
        self.orders.append({"id": oid, "symbol": symbol, "side": side, "qty": qty, "stop": stop, "px": px})
        return oid

    def cancel_all(self):
        pass


def trial_passed(trial_id: str, path: Path = TRIALS) -> bool:
    """True only if the gate recorded verdict 'pass' for this trial."""
    if not trial_id or not Path(path).exists():
        return False
    with open(path, newline="") as f:
        return any(r.get("trial_id") == trial_id and str(r.get("verdict", "")).strip().lower() == "pass"
                   for r in csv.DictReader(f))


def private_chat(chat_id: str) -> bool:
    return str(chat_id).isdigit()  # channels/groups are negative ids


def alert(text: str, env=os.environ, post=None) -> bool:
    """Send to Akhil's private Telegram chat. Returns True if sent. Never raises."""
    tok, chat = env.get("TELEGRAM_BOT_TOKEN"), env.get("CEO_CHAT_ID", "")
    if not tok or not private_chat(chat):
        print("ALERT (not sent):", text)
        return False
    body = json.dumps({"chat_id": chat, "text": text[:3900]}).encode()
    try:
        if post:
            return bool(post(f"https://api.telegram.org/bot{tok}/sendMessage", body))
        req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False


def kill_requested(env=os.environ, root: Path = HERE) -> bool:
    return env.get("KL_KILL") == "1" or (root / "KILL").exists()


@dataclass
class Guard:
    broker: Broker
    trial_id: str
    book: RiskBook
    env: dict = field(default_factory=lambda: dict(os.environ))
    trials_path: Path = TRIALS
    root: Path = HERE
    universe: tuple[str, ...] = ()   # the ONLY symbols this bot may touch (never Akhil's other holdings)
    sent_today: int = 0
    _day: date | None = None
    _stamps: list[float] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    post: object = None

    @property
    def live(self) -> bool:
        return (self.env.get("KL_LIVE") == "yes" and self.broker.name != "dry-run"
                and trial_passed(self.trial_id, self.trials_path))

    def _say(self, text: str) -> None:
        self.alerts.append(text)
        alert(f"[{'LIVE' if self.live else 'DRY'} {self.broker.name}] {text}", self.env, self.post)

    def _throttle(self) -> bool:
        now = time.monotonic()
        self._stamps = [t for t in self._stamps if now - t < 1.0]
        if len(self._stamps) >= MAX_OPS:
            time.sleep(1.0 - (now - self._stamps[0]) + 0.01)
        if self.sent_today >= MAX_ORDERS_DAY:
            return False
        self._stamps.append(time.monotonic())
        return True

    def _mine(self) -> dict[str, int]:
        """Broker positions limited to the bot's universe."""
        return {s: q for s, q in self.broker.positions().items() if s in self.universe}

    def flatten(self, reason: str) -> None:
        """Kill switch: cancel orders and sell the bot's own positions at market (only in live or dry-run)."""
        acting = self.live or self.broker.name == "dry-run"
        if acting:
            self.broker.cancel_all()
            for sym, qty in self._mine().items():
                if qty > 0:
                    self.broker.place(sym, "sell", qty, None)
        self._say(f"KILL SWITCH ({reason}): " + ("orders cancelled, bot positions closed. " if acting else "")
                  + "Bot stopped for today.")

    def run_once(self, targets: dict[str, tuple[int, float | None]], today: date | None = None) -> list[str]:
        """targets: {symbol: (target_qty, stop_price)}. Returns the broker order ids placed."""
        today = today or datetime.now(timezone.utc).date()
        if self._day != today:
            self._day, self.sent_today = today, 0
        unknown = [s for s in targets if s not in self.universe]
        if unknown:
            self._say(f"BLOCKED: {', '.join(unknown)} not in the bot's universe")
            targets = {s: v for s, v in targets.items() if s in self.universe}
        if kill_requested(self.env, self.root):
            self.flatten("kill switch on")
            return []
        cap = float(self.env.get("KL_LIVE_CAPITAL", "5000"))
        mine = self._mine()
        in_trades = sum(q * self.broker.ltp(s) for s, q in mine.items())
        equity = min(self.broker.cash(), max(0.0, cap - in_trades)) + in_trades
        if not self.book.marks:
            self.book.pot = min(equity, cap)   # starting pot, fixed: losses are measured against it
        self.book.positions = mine
        self.book.mark(today, equity)
        if self.book.loss("day", today) >= self.book.limits["daily_loss"]:
            self.flatten("daily loss cap hit")
            return []
        ids = []
        for sym, (target, stop) in targets.items():
            held = self.book.positions.get(sym, 0)
            delta = target - held
            if delta == 0:
                continue
            o = Order(date=today, symbol=sym, side="buy" if delta > 0 else "sell", qty=abs(delta),
                      price=self.broker.ltp(sym), stop=stop, source="signal")
            broken = check(o, self.book)
            if broken:
                self._say(f"BLOCKED {o.side} {o.qty} {sym}: {', '.join(broken)}")
                continue
            if not self._throttle():
                self._say("Daily order budget used up; no more orders today.")
                break
            if not self.live and self.broker.name != "dry-run":
                self._say(f"WOULD {o.side} {o.qty} {sym} @ {o.price} (live trading not switched on)")
                continue
            oid = self.broker.place(sym, o.side, o.qty, stop)
            self.sent_today += 1
            ids.append(oid)
            sign = 1 if o.side == "buy" else -1
            self.book.positions[sym] = held + sign * o.qty
            self._say(f"{o.side.upper()} {o.qty} {sym} @ {o.price} stop {stop} → order {oid}")
        return ids

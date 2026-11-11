"""Broker interface + FakeBroker (paper/tests) + real-adapter STUBS (A153 §4.1).

Safety contract for every real adapter:
  * keys come ONLY from environment variables (set by Akhil as secrets); they are
    never logged, printed or put in repr();
  * the adapter refuses to start unless env LIVE_TRADING=YES AND the go file exists
    and its first line is "go" (Akhil writes it himself);
  * no broker SDK is imported at module import time (tests run without them);
  * every method is a TODO stub that raises NotImplementedError, so no real order can
    be sent from this file as it stands.
SDKs named below are MIT per their PyPI metadata (checked 7 Nov 2026; confirm the repo
LICENSE file before adding). Never copy GPL/AGPL code (OpenAlgo is AGPL: only ever as a
separate unmodified service). Research code, own money only, not advice.
"""
from __future__ import annotations

import itertools
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Mapping

LIVE_DIR = Path(__file__).resolve().parents[2] / "data" / "live"   # git-ignored
GO_FILE = LIVE_DIR / "GO"
KILL_FILE = LIVE_DIR / "KILL"


class LiveRefused(RuntimeError):
    """Raised when live trading is asked for but a go condition is missing."""


@dataclass
class OrderRequest:
    symbol: str
    side: str                       # "buy" | "sell"
    qty: float                      # whole units on NSE, fractional for crypto
    order_type: str = "market"      # "market" | "limit"
    limit_price: float | None = None
    stop_price: float | None = None  # protective stop (mandatory for buys via the guard)
    tag: str = "signal"             # signal | stop | flatten


@dataclass
class OrderResult:
    order_id: str
    status: str                     # filled | open | rejected | cancelled
    symbol: str
    side: str
    qty: float = 0.0
    avg_price: float | None = None
    fee: float = 0.0
    tds: float = 0.0
    reason: str = ""


class Broker(ABC):
    name = "broker"
    needs_daily_login = False       # Indian brokers: True (daily 2FA, no overnight session)
    login_date: date | None = None

    @abstractmethod
    def place_order(self, req: OrderRequest) -> OrderResult: ...

    @abstractmethod
    def cancel(self, order_id: str) -> OrderResult: ...

    @abstractmethod
    def positions(self) -> dict[str, float]: ...

    @abstractmethod
    def cash(self) -> float: ...

    @abstractmethod
    def quote(self, symbol: str) -> float: ...


FeeFn = Callable[[str, float], float]   # (side, value) -> fee in rupees


@dataclass
class FakeBroker(Broker):
    """In-memory broker with deterministic fills. Used by tests and paper mode.

    Market orders fill at once at quote x (1 +/- slippage_bps/1e4). Limit orders fill
    only if the slipped price is no worse than the limit, else stay "open" until
    cancelled. Sells withhold `tds_rate` of the sale value (crypto 1% TDS).
    """
    starting_cash: float = 5_000.0
    prices: dict[str, float] = field(default_factory=dict)
    slippage_bps: float = 10.0
    fee_fn: FeeFn | None = None
    tds_rate: float = 0.0
    fractional: bool = False
    needs_daily_login: bool = False
    login_date: date | None = None
    name: str = "fake"

    def __post_init__(self):
        self._cash = float(self.starting_cash)
        self._pos: dict[str, float] = {}
        self.avg_cost: dict[str, float] = {}
        self.tds_withheld = 0.0
        self.orders: dict[str, OrderResult] = {}
        self._ids = itertools.count(1)

    # interface ---------------------------------------------------------------
    def quote(self, symbol: str) -> float:
        if symbol not in self.prices:
            raise KeyError(f"no quote for {symbol}")
        return float(self.prices[symbol])

    def cash(self) -> float:
        return self._cash

    def positions(self) -> dict[str, float]:
        return dict(self._pos)

    def cancel(self, order_id: str) -> OrderResult:
        r = self.orders.get(order_id)
        if r is None:
            return OrderResult(order_id, "rejected", "", "", reason="unknown order")
        if r.status == "open":
            r.status = "cancelled"
        return r

    def place_order(self, req: OrderRequest) -> OrderResult:
        oid = f"F{next(self._ids):05d}"
        rej = lambda why: self._store(OrderResult(oid, "rejected", req.symbol, req.side, reason=why))
        if req.side not in ("buy", "sell"):
            return rej("bad side")
        if req.qty <= 0 or (not self.fractional and float(req.qty) != int(req.qty)):
            return rej("bad qty")
        try:
            q = self.quote(req.symbol)
        except KeyError as e:
            return rej(str(e))
        slip = self.slippage_bps / 1e4
        px = q * (1 + slip) if req.side == "buy" else q * (1 - slip)
        if req.order_type == "limit":
            if req.limit_price is None:
                return rej("limit order without price")
            if (req.side == "buy" and px > req.limit_price) or (req.side == "sell" and px < req.limit_price):
                return self._store(OrderResult(oid, "open", req.symbol, req.side, req.qty))
        value = req.qty * px
        fee = float(self.fee_fn(req.side, value)) if self.fee_fn else 0.0
        held = self._pos.get(req.symbol, 0.0)
        if req.side == "buy":
            if value + fee > self._cash + 1e-9:
                return rej("insufficient cash")
            self._cash -= value + fee
            self.avg_cost[req.symbol] = (held * self.avg_cost.get(req.symbol, 0.0) + value) / (held + req.qty)
            self._pos[req.symbol] = held + req.qty
            tds = 0.0
        else:
            if req.qty > held + 1e-12:
                return rej("oversell")
            tds = self.tds_rate * value
            self._cash += value - fee - tds
            self.tds_withheld += tds
            left = held - req.qty
            if left <= 1e-12:
                self._pos.pop(req.symbol, None)
                self.avg_cost.pop(req.symbol, None)
            else:
                self._pos[req.symbol] = left
        return self._store(OrderResult(oid, "filled", req.symbol, req.side, req.qty, px, round(fee, 4), round(tds, 4)))

    def _store(self, r: OrderResult) -> OrderResult:
        self.orders[r.order_id] = r
        return r

    # persistence for paper mode ---------------------------------------------
    def to_dict(self) -> dict:
        return {"cash": self._cash, "positions": self._pos, "avg_cost": self.avg_cost,
                "tds_withheld": self.tds_withheld}

    def load(self, d: Mapping) -> "FakeBroker":
        self._cash = float(d["cash"])
        self._pos = {k: float(v) for k, v in d.get("positions", {}).items()}
        self.avg_cost = {k: float(v) for k, v in d.get("avg_cost", {}).items()}
        self.tds_withheld = float(d.get("tds_withheld", 0.0))
        return self


# ---------------------------------------------------------------------------------
# go conditions shared by adapters and the runner
def go_blockers(env: Mapping[str, str] | None = None, go_file: Path | None = None) -> list[str]:
    """Reasons live trading must NOT run (empty list = the two adapter flags hold)."""
    env = os.environ if env is None else env
    go_file = Path(go_file or GO_FILE)
    out = []
    if env.get("LIVE_TRADING") != "YES":
        out.append("env LIVE_TRADING is not YES")
    try:
        first = go_file.read_text().strip().splitlines()[0].strip().lower() if go_file.exists() else ""
    except (OSError, IndexError):
        first = ""
    if first != "go":
        out.append(f"go file missing or not 'go': {go_file}")
    return out


class _LiveAdapter(Broker):
    """Base for real adapters. Refuses to start without both go flags; reads keys from env."""
    ENV_KEYS: tuple[str, ...] = ()
    SDK = ""                      # pip name, imported lazily in _client()

    def __init__(self, env: Mapping[str, str] | None = None, go_file: Path | None = None):
        env = os.environ if env is None else env
        blockers = go_blockers(env, go_file)
        if blockers:
            raise LiveRefused("; ".join(blockers))
        missing = [k for k in self.ENV_KEYS if not env.get(k)]
        if missing:   # names only, never values
            raise LiveRefused(f"missing secret env vars: {', '.join(missing)}")
        self.__keys = {k: env[k] for k in self.ENV_KEYS}   # name-mangled, never logged

    def __repr__(self) -> str:   # never show keys
        return f"<{type(self).__name__} keys=hidden>"

    __str__ = __repr__

    def _key(self, name: str) -> str:
        return self.__keys[name]

    def _todo(self, what: str):
        raise NotImplementedError(f"{type(self).__name__}.{what}: TODO, adapter not built yet "
                                  f"(paper 90 days + gate pass + Akhil's go first)")

    def place_order(self, req):  return self._todo("place_order")
    def cancel(self, order_id):  return self._todo("cancel")
    def positions(self):         return self._todo("positions")
    def cash(self):              return self._todo("cash")
    def quote(self, symbol):     return self._todo("quote")


class FyersAdapter(_LiveAdapter):
    """Track A. FYERS API v3 (SDK `fyers-apiv3`, MIT per PyPI 7 Nov 2026).

    TODO: from fyers_apiv3 import fyersModel (inside _client only); FyersModel(client_id,
    token); place_order with productType "CNC", type 2 (market); orderbook/positions/funds;
    quotes. Orders must come from the static IP whitelisted in the FYERS dashboard; the
    access token expires daily (2FA login by Akhil each trading day).
    """
    name = "fyers"
    needs_daily_login = True
    ENV_KEYS = ("FYERS_CLIENT_ID", "FYERS_ACCESS_TOKEN")
    SDK = "fyers-apiv3"


class DhanAdapter(_LiveAdapter):
    """Track A. Dhan HQ API (SDK `dhanhq`, MIT per PyPI 7 Nov 2026).

    TODO: from dhanhq import dhanhq (inside _client only); place_order(security_id,
    exchange_segment NSE_EQ, transaction_type, quantity, order_type MARKET, product_type
    CNC); get_positions, get_fund_limits, quotes. Static IP whitelisting + daily token.
    """
    name = "dhan"
    needs_daily_login = True
    ENV_KEYS = ("DHAN_CLIENT_ID", "DHAN_ACCESS_TOKEN")
    SDK = "dhanhq"


class DeltaIndiaAdapter(_LiveAdapter):
    """Track B. Delta Exchange India (SDK `delta-rest-client`, MIT per PyPI 7 Nov 2026).

    TODO: from delta_rest_client import DeltaRestClient (inside _client only) with
    base_url https://api.india.delta.exchange (confirm in Delta docs); spot/linear only,
    leverage 1, no shorting; wallet balances, positions, ticker. 24x7 market.
    """
    name = "delta-india"
    ENV_KEYS = ("DELTA_API_KEY", "DELTA_API_SECRET")
    SDK = "delta-rest-client"


class CoinDCXAdapter(_LiveAdapter):
    """Track B. CoinDCX REST API (no official Python SDK: stdlib hmac/hashlib + urllib).

    TODO: HMAC-SHA256 signed JSON bodies (X-AUTH-APIKEY / X-AUTH-SIGNATURE headers per
    CoinDCX docs, confirm before building); /exchange/v1/orders/create (market_order),
    /exchange/v1/users/balances, public ticker. INR spot pairs only. 24x7 market.
    """
    name = "coindcx"
    ENV_KEYS = ("COINDCX_API_KEY", "COINDCX_API_SECRET")


ADAPTERS = {"A": {"fyers": FyersAdapter, "dhan": DhanAdapter},
            "B": {"delta": DeltaIndiaAdapter, "coindcx": CoinDCXAdapter}}

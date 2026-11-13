"""Broker interface + FakeBroker (paper/tests) + real-adapter STUBS (A153 §4.1).

Safety contract for every real adapter:
  * keys come ONLY from environment variables (set by Akhil as secrets); they are
    never logged, printed or put in repr();
  * the adapter refuses to start unless env LIVE_TRADING=YES AND the go file exists
    and its first line is "go" (Akhil writes it himself);
  * no broker SDK is imported at module import time (tests run without them);
  * DhanAdapter (track A) is real (14 Nov 2026); the FYERS, Delta and CoinDCX adapters
    are still stubs that raise NotImplementedError.
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
        first = go_file.read_text(encoding="utf-8").strip().splitlines()[0].strip().lower() if go_file.exists() else ""
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
    """Track A, REAL orders. DhanHQ API v2, plain HTTPS with the standard library (no SDK).

    Facts from Dhan's own docs, checked 14 Nov 2026 (dhanhq.co/docs/v2):
      * base https://api.dhan.co/v2, headers `access-token` + `Content-Type: application/json`;
      * POST /orders {dhanClientId, correlationId, transactionType BUY|SELL, exchangeSegment NSE_EQ,
        productType CNC, orderType MARKET|LIMIT, validity DAY, securityId, quantity, price}
        -> {orderId, orderStatus}; GET /orders/{id}; GET /orders/external/{correlationId};
        DELETE /orders/{id} -> 202; GET /holdings; GET /positions; GET /fundlimit (`availabelBalance`, sic);
      * order APIs need a whitelisted static IP, EXCEPT inside Dhan Cloud (Dhan FAQ);
      * security ids from Dhan's scrip master (images.dhan.co/api-data/api-scrip-master.csv, 14 Nov 2026).
    Safety: never logs the token; an order POST is never blindly retried (a lost reply is
    looked up by its correlationId first, so a network blip can't buy twice); GETs retry with backoff.
    """
    name = "dhan"
    needs_daily_login = True
    ENV_KEYS = ("DHAN_CLIENT_ID", "DHAN_ACCESS_TOKEN")
    BASE = "https://api.dhan.co/v2"
    SECURITY_IDS = {"NIFTYBEES": "10576", "GOLDBEES": "14428", "LIQUIDBEES": "11006"}   # NSE_EQ
    DONE = {"TRADED": "filled", "REJECTED": "rejected", "CANCELLED": "cancelled", "EXPIRED": "cancelled"}

    def __init__(self, env=None, go_file=None, *, http=None, quote_fn=None, sleep=None, poll_s: float = 1.0,
                 poll_max: int = 20, today=None):
        super().__init__(env=env, go_file=go_file)
        import time
        self._http = http or self._urllib
        self._quote_fn = quote_fn
        self._sleep = sleep or time.sleep
        self._poll_s, self._poll_max = poll_s, poll_max
        self.login_date = today or date.today()   # the daily token is fresh by definition when the run starts
        self.avg_cost: dict[str, float] = {}
        self.tds_withheld = 0.0                    # no TDS on NSE delivery
        self._seq = itertools.count(1)

    # -- HTTP -------------------------------------------------------------------
    def _urllib(self, method: str, url: str, headers: dict, body: bytes | None):
        import json, urllib.error, urllib.request
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read() or b"{}")
            except ValueError:
                return e.code, {}

    def _call(self, method: str, path: str, payload: dict | None = None, retry: bool = True):
        import json
        headers = {"access-token": self._key("DHAN_ACCESS_TOKEN"), "client-id": self._key("DHAN_CLIENT_ID"),
                   "Content-Type": "application/json", "Accept": "application/json"}
        body = json.dumps(payload).encode() if payload is not None else None
        tries = 4 if (retry and method == "GET") else 1
        last = None
        for i in range(tries):
            try:
                status, data = self._http(method, f"{self.BASE}{path}", headers, body)
            except OSError as e:          # timeout / DNS / connection reset
                last = (0, {"errorMessage": f"network: {type(e).__name__}"})
                if i < tries - 1:
                    self._sleep(2 ** i)
                    continue
                return last
            if status in (429, 500, 502, 503, 504) and i < tries - 1:
                self._sleep(2 ** i)
                continue
            return status, data
        return last

    @staticmethod
    def _why(status: int, data) -> str:
        if isinstance(data, dict):
            msg = data.get("errorMessage") or data.get("omsErrorDescription") or data.get("remarks") or ""
            code = data.get("errorCode") or data.get("omsErrorCode") or ""
            if msg or code:
                return f"dhan {status} {code} {msg}".strip()
        return f"dhan http {status}"

    def _sid(self, symbol: str) -> str:
        sid = self.SECURITY_IDS.get(symbol.upper())
        if not sid:
            raise LiveRefused(f"no Dhan security id for {symbol}; add it from the scrip master first")
        return sid

    # -- Broker API ---------------------------------------------------------------
    def cash(self) -> float:
        st, d = self._call("GET", "/fundlimit")
        if st != 200 or not isinstance(d, dict):
            raise LiveRefused(f"cannot read funds: {self._why(st, d)} (token expired? log in to Dhan and refresh it)")
        return float(d.get("availabelBalance", d.get("availableBalance", 0.0)) or 0.0)

    def positions(self) -> dict[str, float]:
        """Delivery holdings (settled + T1) plus today's net CNC trades, by NSE symbol."""
        names = {v: k for k, v in self.SECURITY_IDS.items()}
        out: dict[str, float] = {}
        st, hold = self._call("GET", "/holdings")
        if st == 200 and isinstance(hold, list):
            for h in hold:
                sym = names.get(str(h.get("securityId")), str(h.get("tradingSymbol", "")).upper())
                qty = float(h.get("totalQty", 0) or 0)
                if qty:
                    out[sym] = out.get(sym, 0.0) + qty
                    if h.get("avgCostPrice"):
                        self.avg_cost[sym] = float(h["avgCostPrice"])
        elif st not in (200, 404):     # Dhan answers "no holdings" with an error body on some accounts
            raise LiveRefused(f"cannot read holdings: {self._why(st, hold)}")
        st, pos = self._call("GET", "/positions")
        if st == 200 and isinstance(pos, list):
            for p in pos:
                if p.get("productType") != "CNC":
                    continue
                sym = names.get(str(p.get("securityId")), str(p.get("tradingSymbol", "")).upper())
                out[sym] = out.get(sym, 0.0) + float(p.get("netQty", 0) or 0)
                if float(p.get("buyQty", 0) or 0) > 0 and sym not in self.avg_cost and p.get("buyAvg"):
                    self.avg_cost[sym] = float(p["buyAvg"])
        elif st != 200:
            raise LiveRefused(f"cannot read positions: {self._why(st, pos)}")
        return {k: v for k, v in out.items() if abs(v) > 1e-9}

    def quote(self, symbol: str) -> float:
        """Live quotes are Dhan's paid Data API, so the price comes from quote_fn (yfinance by default)."""
        if self._quote_fn is not None:
            return float(self._quote_fn(symbol))
        from .. import data
        bars = data.get_daily(f"{symbol}.NS", strict=False, refresh=True)
        return float(bars["close"].iloc[-1])

    def cancel(self, order_id: str) -> OrderResult:
        st, d = self._call("DELETE", f"/orders/{order_id}", retry=False)
        ok = st in (200, 202)
        return OrderResult(order_id, "cancelled" if ok else "rejected", "", "", reason="" if ok else self._why(st, d))

    def place_order(self, req: OrderRequest) -> OrderResult:
        qty = int(req.qty)
        if qty <= 0 or qty != req.qty:
            return OrderResult("", "rejected", req.symbol, req.side, reason="NSE needs a whole number of units")
        corr = f"kalpa-{date.today():%Y%m%d}-{req.tag[:6]}-{next(self._seq)}"   # <= 30 chars, [A-Za-z0-9_-]
        body = {"dhanClientId": self._key("DHAN_CLIENT_ID"), "correlationId": corr,
                "transactionType": "BUY" if req.side == "buy" else "SELL", "exchangeSegment": "NSE_EQ",
                "productType": "CNC", "orderType": "LIMIT" if req.order_type == "limit" else "MARKET",
                "validity": "DAY", "securityId": self._sid(req.symbol), "quantity": qty,
                "price": float(req.limit_price or 0) if req.order_type == "limit" else 0}
        st, d = self._call("POST", "/orders", body, retry=False)
        oid = str(d.get("orderId", "")) if isinstance(d, dict) else ""
        if st == 0 or (st >= 500 and not oid):
            # reply lost: ask Dhan whether the order exists before doing anything else (never double-buy)
            self._sleep(1)
            st2, d2 = self._call("GET", f"/orders/external/{corr}")
            rec = d2[0] if isinstance(d2, list) and d2 else d2 if isinstance(d2, dict) else {}
            oid = str(rec.get("orderId", "")) if st2 == 200 else ""
            if not oid:
                return OrderResult("", "rejected", req.symbol, req.side, reason=f"order not confirmed ({self._why(st, d)}); nothing retried")
        elif st not in (200, 201) or not oid:
            return OrderResult(oid, "rejected", req.symbol, req.side, reason=self._why(st, d))
        return self._wait(oid, req)

    def _wait(self, oid: str, req: OrderRequest) -> OrderResult:
        rec: dict = {}
        for _ in range(self._poll_max):
            st, d = self._call("GET", f"/orders/{oid}")
            rec = (d[0] if isinstance(d, list) and d else d) if st == 200 else {}
            status = str(rec.get("orderStatus", "")).upper()
            if status in self.DONE:
                break
            self._sleep(self._poll_s)
        status = self.DONE.get(str(rec.get("orderStatus", "")).upper(), "open")
        filled = float(rec.get("filledQty", 0) or 0)
        px = float(rec.get("averageTradedPrice", 0) or 0) or None
        if status == "cancelled" and filled > 0:
            status = "filled"                          # part-filled then expired: keep what traded
        if status == "filled" and px and req.side == "buy" and req.symbol not in self.avg_cost:
            self.avg_cost[req.symbol] = px              # positions() refreshes the true average next run
        return OrderResult(oid, status, req.symbol, req.side, qty=filled, avg_price=px, fee=0.0,
                           reason="" if status != "rejected" else self._why(200, rec))

    # snapshot hooks so the runner can treat this like FakeBroker
    def to_dict(self) -> dict:
        return {"live": "dhan", "avg_cost": dict(self.avg_cost), "cash": None, "positions": {}, "tds_withheld": 0.0}

    def load(self, d) -> "DhanAdapter":
        self.avg_cost.update((d or {}).get("avg_cost", {}))
        return self


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


class ScopedBroker(Broker):
    """One strategy leg inside a shared real account (e.g. Nifty-trend Rs 5,000 + gold-hold Rs 5,000
    in one Dhan account). The leg sees only its own symbol and its own cash ledger, so each leg's
    guard enforces its own capital cap; cash() never exceeds what the real account actually has."""

    def __init__(self, real: Broker, symbol: str, cash: float, fee_fn: FeeFn | None = None):
        self.real, self.symbol, self.leg_cash = real, symbol.upper(), float(cash)
        self.fee_fn = fee_fn or (lambda side, v: 0.0)
        self.name = f"{getattr(real, 'name', 'broker')}:{self.symbol}"
        self.needs_daily_login = real.needs_daily_login
        self.login_date = real.login_date
        self.tds_withheld = 0.0

    @property
    def avg_cost(self) -> dict[str, float]:
        ac = getattr(self.real, "avg_cost", {})
        return {self.symbol: ac[self.symbol]} if self.symbol in ac else {}

    def quote(self, symbol: str) -> float: return self.real.quote(symbol)
    def cash(self) -> float: return max(0.0, min(self.leg_cash, self.real.cash()))
    def positions(self) -> dict[str, float]:
        q = self.real.positions().get(self.symbol, 0.0)
        return {self.symbol: q} if q else {}
    def cancel(self, order_id: str) -> OrderResult: return self.real.cancel(order_id)

    def place_order(self, req: OrderRequest) -> OrderResult:
        if req.symbol.upper() != self.symbol:
            return OrderResult("", "rejected", req.symbol, req.side, reason=f"leg {self.symbol} cannot trade {req.symbol}")
        r = self.real.place_order(req)
        if r.status == "filled" and r.qty and r.avg_price:
            value = r.qty * r.avg_price
            r.fee = r.fee or self.fee_fn(r.side, value)
            self.leg_cash += (-value if r.side == "buy" else value) - r.fee
        return r

    def to_dict(self) -> dict:
        return {"leg_cash": self.leg_cash, "avg_cost": self.avg_cost, "symbol": self.symbol}

    def load(self, d) -> "ScopedBroker":
        if d and "leg_cash" in d:
            self.leg_cash = float(d["leg_cash"])
        return self


ADAPTERS = {"A": {"fyers": FyersAdapter, "dhan": DhanAdapter},
            "B": {"delta": DeltaIndiaAdapter, "coindcx": CoinDCXAdapter}}

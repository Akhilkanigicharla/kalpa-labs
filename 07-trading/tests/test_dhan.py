"""DhanAdapter against a fake Dhan server that speaks the v2 shapes from dhanhq.co/docs/v2 (checked 14 Nov 2026).
No network, no real keys. Covers: auth headers, order body, fills, rejections, lost replies (no double buy),
retries on GET only, holdings + today's positions, the funds field typo, token never leaked, and the
two-leg ScopedBroker + full live runner path."""
import json
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from src.livetrade import broker as brk, runner
from src.livetrade.guard import IST

TOKEN, CLIENT = "tok-SECRET-123", "1000000003"


class FakeDhan:
    def __init__(self):
        self.calls, self.orders, self.fail = [], {}, []      # fail: queue of (method, path_prefix, status|"net")
        self.holdings = [{"exchange": "NSE", "tradingSymbol": "GOLDBEES", "securityId": "14428", "totalQty": 44,
                          "dpQty": 44, "t1Qty": 0, "availableQty": 44, "avgCostPrice": 112.5}]
        self.positions, self.cash, self.fill = [], 9_500.0, "TRADED"
        self.n = 0

    def __call__(self, method, url, headers, body):
        path = url.replace(brk.DhanAdapter.BASE, "")
        self.calls.append((method, path, headers, json.loads(body) if body else None))
        assert headers["access-token"] == TOKEN and headers["Content-Type"] == "application/json"
        for i, (m, pre, what) in enumerate(self.fail):
            if m == method and path.startswith(pre):
                self.fail.pop(i)
                if what == "net":
                    if method == "POST":                      # order reached Dhan, reply lost
                        self._create(json.loads(body))
                    raise TimeoutError("read timed out")
                return what, {"errorCode": "DH-904", "errorMessage": "busy"}
        if method == "GET" and path == "/fundlimit":
            return 200, {"dhanClientId": CLIENT, "availabelBalance": self.cash, "sodLimit": self.cash}
        if method == "GET" and path == "/holdings":
            return 200, self.holdings
        if method == "GET" and path == "/positions":
            return 200, self.positions
        if method == "POST" and path == "/orders":
            b = json.loads(body)
            if b["quantity"] > 1000:
                return 400, {"errorCode": "DH-905", "errorMessage": "Insufficient funds"}
            return 200, {"orderId": self._create(b), "orderStatus": "PENDING"}
        if method == "GET" and path.startswith("/orders/external/"):
            corr = path.rsplit("/", 1)[1]
            hit = [o for o in self.orders.values() if o["correlationId"] == corr]
            return (200, hit) if hit else (404, {"errorMessage": "not found"})
        if method == "GET" and path.startswith("/orders/"):
            return 200, self.orders[path.rsplit("/", 1)[1]]
        if method == "DELETE" and path.startswith("/orders/"):
            return 202, {"orderId": path.rsplit("/", 1)[1], "orderStatus": "CANCELLED"}
        return 404, {}

    def _create(self, b):
        self.n += 1
        oid = f"5{self.n:05d}"
        traded = self.fill == "TRADED"
        px = {"10576": 287.4, "14428": 112.8, "11006": 1000.0}[b["securityId"]]
        sym = {"10576": "NIFTYBEES", "14428": "GOLDBEES", "11006": "LIQUIDBEES"}[b["securityId"]]
        self.orders[oid] = {**b, "orderId": oid, "orderStatus": self.fill, "filledQty": b["quantity"] if traded else 0,
                            "averageTradedPrice": px if traded else 0, "omsErrorDescription": "" if traded else "RMS: price band"}
        if traded and b["transactionType"] == "BUY":
            self.positions.append({"securityId": b["securityId"], "tradingSymbol": sym, "productType": "CNC",
                                   "netQty": b["quantity"], "buyQty": b["quantity"], "buyAvg": px})
        return oid


def adapter(tmp_path, fake=None, quote=287.0):
    (tmp_path / "GO").write_text("go\n")
    env = {"LIVE_TRADING": "YES", "DHAN_CLIENT_ID": CLIENT, "DHAN_ACCESS_TOKEN": TOKEN}
    fake = fake or FakeDhan()
    a = brk.DhanAdapter(env=env, go_file=tmp_path / "GO", http=fake, quote_fn=lambda s: quote, sleep=lambda s: None)
    return a, fake


def test_buy_sends_exact_dhan_order_body_and_waits_for_the_fill(tmp_path):
    a, f = adapter(tmp_path)
    r = a.place_order(brk.OrderRequest("NIFTYBEES", "buy", 17, stop_price=230.0))
    assert (r.status, r.qty, r.avg_price) == ("filled", 17, 287.4)
    m, path, _, body = f.calls[0]
    assert (m, path) == ("POST", "/orders")
    assert body == {"dhanClientId": CLIENT, "correlationId": body["correlationId"], "transactionType": "BUY",
                    "exchangeSegment": "NSE_EQ", "productType": "CNC", "orderType": "MARKET", "validity": "DAY",
                    "securityId": "10576", "quantity": 17, "price": 0}
    assert len(body["correlationId"]) <= 30 and body["correlationId"].replace("-", "").isalnum()


def test_rejections_come_back_in_plain_words_never_as_crashes(tmp_path):
    a, f = adapter(tmp_path)
    r = a.place_order(brk.OrderRequest("NIFTYBEES", "buy", 5000))
    assert r.status == "rejected" and "Insufficient funds" in r.reason
    f.fill = "REJECTED"
    r = a.place_order(brk.OrderRequest("NIFTYBEES", "buy", 2))
    assert r.status == "rejected" and "price band" in r.reason
    assert a.place_order(brk.OrderRequest("NIFTYBEES", "buy", 2.5)).status == "rejected"      # whole units only
    with pytest.raises(brk.LiveRefused, match="security id"):
        a.place_order(brk.OrderRequest("RELIANCE", "buy", 1))


def test_lost_order_reply_is_looked_up_not_resent(tmp_path):
    """Network drops after Dhan accepted the order: must find it by correlationId, never place a second one."""
    a, f = adapter(tmp_path)
    f.fail.append(("POST", "/orders", "net"))
    r = a.place_order(brk.OrderRequest("NIFTYBEES", "buy", 3, stop_price=230.0))
    assert r.status == "filled" and len(f.orders) == 1
    assert sum(1 for c in f.calls if c[0] == "POST") == 1


def test_lost_reply_and_no_order_found_is_rejected_without_retry(tmp_path):
    a, f = adapter(tmp_path)
    f.fail.append(("POST", "/orders", 503))
    r = a.place_order(brk.OrderRequest("NIFTYBEES", "buy", 3))
    assert r.status == "rejected" and "nothing retried" in r.reason and not f.orders
    assert sum(1 for c in f.calls if c[0] == "POST") == 1


def test_reads_retry_on_busy_or_network_then_succeed(tmp_path):
    a, f = adapter(tmp_path)
    f.fail += [("GET", "/fundlimit", 503), ("GET", "/fundlimit", "net")]
    assert a.cash() == 9_500.0


def test_expired_token_gives_a_clear_message(tmp_path):
    a, f = adapter(tmp_path)
    f.fail += [("GET", "/fundlimit", 401)]
    with pytest.raises(brk.LiveRefused, match="token expired"):
        a.cash()


def test_positions_add_holdings_and_todays_cnc_trades(tmp_path):
    a, f = adapter(tmp_path)
    assert a.positions() == {"GOLDBEES": 44.0}
    a.place_order(brk.OrderRequest("NIFTYBEES", "buy", 17, stop_price=230.0))
    f.positions.append({"securityId": "10576", "productType": "INTRADAY", "netQty": 99})   # ignored
    assert a.positions() == {"GOLDBEES": 44.0, "NIFTYBEES": 17.0}
    assert a.avg_cost["GOLDBEES"] == 112.5


def test_token_never_appears_in_repr_results_or_reasons(tmp_path):
    a, f = adapter(tmp_path)
    f.fail.append(("POST", "/orders", 500))
    r = a.place_order(brk.OrderRequest("NIFTYBEES", "buy", 1))
    assert TOKEN not in repr(a) and TOKEN not in str(a) and TOKEN not in r.reason and TOKEN not in json.dumps(a.to_dict())


def test_cancel(tmp_path):
    a, _ = adapter(tmp_path)
    assert a.cancel("500001").status == "cancelled"


def test_scoped_leg_sees_only_its_symbol_and_its_cash(tmp_path):
    a, f = adapter(tmp_path)
    leg = brk.ScopedBroker(a, "NIFTYBEES", 5_000.0, fee_fn=lambda side, v: 0.0)
    assert leg.positions() == {} and leg.cash() == 5_000.0          # the gold holding belongs to the other leg
    r = leg.place_order(brk.OrderRequest("NIFTYBEES", "buy", 17, stop_price=230.0))
    assert r.status == "filled" and leg.positions() == {"NIFTYBEES": 17.0}
    assert leg.cash() == pytest.approx(5_000 - 17 * 287.4)
    assert leg.place_order(brk.OrderRequest("GOLDBEES", "sell", 44)).status == "rejected"
    f.cash = 100.0
    assert leg.cash() == 100.0                                       # never more than the real account has


def _bars(n=900, start=200.0, drift=0.001):
    idx = pd.bdate_range(end=pd.Timestamp("2026-11-13"), periods=n)
    px = start * np.exp(np.cumsum(np.full(n, drift)))
    return pd.DataFrame({"open": px, "high": px * 1.01, "low": px * 0.99, "close": px, "volume": 1e6}, index=idx)


def test_live_runner_end_to_end_buys_once_with_a_stop_and_never_twice(tmp_path, monkeypatch):
    """Uptrend -> strategy wants Nifty; the live run (morning, market open) buys whole units through Dhan,
    records a stop, and a second run the same day does nothing."""
    a, f = adapter(tmp_path, quote=287.0)
    monkeypatch.setattr(runner, "datetime", type("D", (datetime,), {"now": staticmethod(lambda tz=None: datetime(2026, 11, 16, 9, 20, tzinfo=IST))}))
    monkeypatch.setattr(a, "login_date", date(2026, 11, 16))
    bars = _bars(start=287.0 / np.exp(0.001 * 899))
    leg = brk.ScopedBroker(a, "NIFTYBEES", 5_000.0, runner.fee_fn("A"))
    leg.login_date = date(2026, 11, 16)
    res = runner.run_paper(bars, track="A", strategy="tsmom", capital=5_000.0, out=tmp_path / "out",
                           flags=tmp_path, broker=leg)
    buys = [d for d in res["decisions"] if d.result and d.result.status == "filled"]
    assert buys and buys[0].request.side == "buy" and buys[0].request.stop_price < 287.0
    assert "LIVE · NIFTYBEES" in res["summary"]
    assert (tmp_path / "out" / "state-A-NIFTYBEES-live.json").exists()
    n_posts = sum(1 for c in f.calls if c[0] == "POST")
    res2 = runner.run_paper(bars, track="A", strategy="tsmom", capital=5_000.0, out=tmp_path / "out",
                            flags=tmp_path, broker=leg)
    assert res2.get("skipped") and sum(1 for c in f.calls if c[0] == "POST") == n_posts


def test_live_cli_refuses_until_every_rule_holds(tmp_path):
    env = {"LIVE_TRADING": "YES", "DHAN_CLIENT_ID": CLIENT, "DHAN_ACCESS_TOKEN": TOKEN}
    rc = runner.main(["--track", "A", "--mode", "live", "--flags", str(tmp_path), "--out", str(tmp_path / "o"),
                      "--synthetic"], env=env)
    assert rc == 2          # no GO file, no gate pass, 0 paper days -> refused before any network call


def test_lost_state_rebuilds_the_stop_and_sells_below_it(tmp_path, monkeypatch):
    """Cloud run with no state file but units already held: stop comes back from Dhan's average cost,
    and a close below it sells everything (no position is ever left without a stop)."""
    a, f = adapter(tmp_path, quote=200.0)
    f.holdings.append({"securityId": "10576", "tradingSymbol": "NIFTYBEES", "totalQty": 17, "avgCostPrice": 287.4})
    monkeypatch.setattr(runner, "datetime", type("D", (datetime,), {"now": staticmethod(lambda tz=None: datetime(2026, 11, 16, 9, 20, tzinfo=IST))}))
    a.login_date = date(2026, 11, 16)
    bars = _bars(start=200.0)
    bars.iloc[-1, bars.columns.get_loc("close")] = 200.0          # 30% below cost, under the 20% stop
    leg = brk.ScopedBroker(a, "NIFTYBEES", 0.0, runner.fee_fn("A"))
    leg.login_date = date(2026, 11, 16)
    res = runner.run_paper(bars, track="A", strategy="tsmom", capital=5_000.0, out=tmp_path / "out2",
                           flags=tmp_path, broker=leg)
    sells = [d for d in res["decisions"] if d.request.side == "sell"]
    assert sells and sells[0].request.tag == "stop" and sells[0].request.qty == 17

"""A153 live-ready layer: FakeBroker, adapters, Live Guard, crypto tax, runner, markov_regime.
Synthetic data only, no network, no secrets, no real orders."""
import sys
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from src import crypto_tax as ct, data, gate, risk, strategies, trials
from src.live import broker as brk, runner
from src.live.guard import IST, GuardConfig, LiveGuard, market_open, next_open

MON_10 = datetime(2026, 11, 9, 10, 0, tzinfo=IST)     # Monday 10:00 IST


def fake(**kw):
    kw.setdefault("prices", {"NIFTYBEES": 100.0})
    return brk.FakeBroker(**kw)


def guard(tmp_path, b=None, market="NSE", capital=5_000.0, now=MON_10, **cfg):
    b = b or fake(slippage_bps=0)
    clock = [now]
    g = LiveGuard(b, risk.RiskBook(pot=capital),
                  GuardConfig(market=market, capital=capital, kill_file=tmp_path / "KILL", **cfg),
                  clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + timedelta(seconds=s)))
    return g, clock


def buy(qty=1, stop=95.0, sym="NIFTYBEES"):
    return brk.OrderRequest(sym, "buy", qty, stop_price=stop)


# ---------------- FakeBroker
def test_fakebroker_deterministic_fills_fees_and_rejections():
    b = fake(starting_cash=1_000, slippage_bps=50, fee_fn=lambda side, v: 1.0)
    r = b.place_order(brk.OrderRequest("NIFTYBEES", "buy", 2))
    assert r.status == "filled" and r.avg_price == pytest.approx(100.5) and r.fee == 1.0
    assert b.cash() == pytest.approx(1_000 - 201 - 1) and b.positions() == {"NIFTYBEES": 2}
    assert b.place_order(brk.OrderRequest("NIFTYBEES", "buy", 1.5)).reason == "bad qty"
    assert b.place_order(brk.OrderRequest("NIFTYBEES", "buy", 100)).reason == "insufficient cash"
    assert b.place_order(brk.OrderRequest("NIFTYBEES", "sell", 3)).reason == "oversell"
    assert b.place_order(brk.OrderRequest("XYZ", "buy", 1)).status == "rejected"
    s = b.place_order(brk.OrderRequest("NIFTYBEES", "sell", 2))
    assert s.avg_price == pytest.approx(99.5) and b.positions() == {}


def test_fakebroker_limit_cancel_tds_and_persistence():
    b = fake(prices={"BTCINR": 1_000.0}, slippage_bps=0, fractional=True, tds_rate=0.01)
    o = b.place_order(brk.OrderRequest("BTCINR", "buy", 0.5, "limit", limit_price=900))
    assert o.status == "open" and b.cancel(o.order_id).status == "cancelled"
    b.place_order(brk.OrderRequest("BTCINR", "buy", 0.5))
    s = b.place_order(brk.OrderRequest("BTCINR", "sell", 0.25))
    assert s.tds == pytest.approx(2.5) and b.tds_withheld == pytest.approx(2.5)
    b2 = fake(prices={"BTCINR": 1_000.0}).load(b.to_dict())
    assert b2.positions() == b.positions() and b2.cash() == b.cash()


# ---------------- adapters
@pytest.mark.parametrize("cls", [brk.FyersAdapter, brk.DhanAdapter, brk.DeltaIndiaAdapter, brk.CoinDCXAdapter])
def test_adapters_refuse_without_flags_and_hide_keys(tmp_path, cls):
    go = tmp_path / "GO"
    with pytest.raises(brk.LiveRefused, match="LIVE_TRADING"):
        cls(env={}, go_file=go)
    with pytest.raises(brk.LiveRefused, match="go file"):
        cls(env={"LIVE_TRADING": "YES"}, go_file=go)
    go.write_text("go\n")
    with pytest.raises(brk.LiveRefused, match="missing secret env vars") as e:
        cls(env={"LIVE_TRADING": "YES"}, go_file=go)
    secret = "s3cr3t-value-XYZ"
    env = {"LIVE_TRADING": "YES", **{k: secret for k in cls.ENV_KEYS}}
    a = cls(env=env, go_file=go)
    assert secret not in repr(a) and secret not in str(a) and secret not in str(e.value)
    for call in (lambda: a.place_order(buy()), lambda: a.cash(), lambda: a.quote("X"),
                 lambda: a.positions(), lambda: a.cancel("1")):
        with pytest.raises(NotImplementedError):
            call()


def test_no_sdk_imported_and_go_flag_needs_exact_go(tmp_path):
    for mod in ("fyers_apiv3", "dhanhq", "delta_rest_client"):
        assert mod not in sys.modules
    (tmp_path / "GO").write_text("yes please")
    assert len(brk.go_blockers({"LIVE_TRADING": "yes"}, tmp_path / "GO")) == 2


# ---------------- Live Guard
def test_guard_allows_a_clean_buy_and_records_it(tmp_path):
    g, _ = guard(tmp_path)
    d = g.submit(buy())
    assert d.allowed and d.result.status == "filled"


def test_guard_rate_limit_two_per_second(tmp_path):
    g, clock = guard(tmp_path, one_trade_per_symbol_per_day=False, max_position_pct=1.0)
    g.book.limits["per_trade_risk"] = 1.0
    assert [g.submit(buy()).allowed for _ in range(3)] == [True, True, False]
    assert "rate_limit" in g.log[-1].reasons
    clock[0] += timedelta(seconds=1.01)
    assert g.submit(buy()).allowed
    with pytest.raises(ValueError):
        GuardConfig(max_orders_per_sec=10)


def test_market_hours_nse_vs_crypto():
    sat = datetime(2026, 11, 7, 10, 0, tzinfo=IST)
    assert market_open("NSE", MON_10) and not market_open("NSE", sat)
    assert not market_open("NSE", MON_10.replace(hour=9, minute=14))
    assert not market_open("NSE", MON_10.replace(hour=15, minute=31))
    assert not market_open("NSE", MON_10, frozenset({MON_10.date()}))
    assert market_open("CRYPTO", sat)
    assert next_open("NSE", sat) == datetime(2026, 11, 9, 9, 15, tzinfo=IST)
    # 10:00 IST Monday expressed in UTC is still open
    assert market_open("NSE", MON_10.astimezone(__import__("datetime").timezone.utc))


def test_guard_blocks_closed_market_and_missing_login(tmp_path):
    g, _ = guard(tmp_path, now=datetime(2026, 11, 8, 11, 0, tzinfo=IST))
    assert "market_closed" in g.submit(buy()).reasons
    b = fake(slippage_bps=0, needs_daily_login=True, login_date=date(2026, 11, 6))
    g, _ = guard(tmp_path, b=b)
    assert "login_required" in g.submit(buy()).reasons
    b.login_date = MON_10.date()
    assert g.submit(buy()).allowed
    gc, _ = guard(tmp_path, market="CRYPTO", now=datetime(2026, 11, 8, 3, 0, tzinfo=IST))
    assert gc.submit(buy()).allowed


def test_guard_stop_position_and_capital_caps(tmp_path):
    g, _ = guard(tmp_path)
    assert "no_stop" in g.submit(buy(stop=None)).reasons
    assert "no_stop" in g.submit(buy(stop=101)).reasons
    assert "max_position" in g.submit(buy(qty=11, stop=99.9)).reasons   # 1,100 > 20% of 5,000
    b = fake(starting_cash=20_000, slippage_bps=0, prices={"A": 100.0, "B": 100.0, "C": 100.0, "D": 100.0, "E": 100.0, "F": 100.0})
    for s in "ABCDE":
        b.place_order(brk.OrderRequest(s, "buy", 10))      # 5,000 already held outside the guard
    g2, _ = guard(tmp_path, b=b, max_position_pct=1.0)
    assert "capital_cap" in g2.submit(buy(qty=1, stop=99, sym="F")).reasons
    with pytest.raises(ValueError, match="hard max"):
        GuardConfig(capital=10_001)


def test_guard_kill_switch_blocks_buys_and_flattens(tmp_path):
    b = fake(starting_cash=5_000, slippage_bps=0, prices={"NIFTYBEES": 100.0, "X": 50.0, "Y": 20.0})
    for s in ("NIFTYBEES", "X", "Y"):
        b.place_order(brk.OrderRequest(s, "buy", 2))
    g, _ = guard(tmp_path, b=b)
    (tmp_path / "KILL").write_text("stop")
    assert "kill_switch" in g.submit(buy()).reasons
    out = g.flatten()                         # 3 sells, rate limit makes it wait, all fill
    assert all(d.result.status == "filled" for d in out) and b.positions() == {}
    assert len({d.at for d in out}) >= 2


def test_guard_reuses_risk_loss_caps(tmp_path):
    g, _ = guard(tmp_path)
    g.book.mark(MON_10.date() - timedelta(days=3), 5_000)   # last Friday
    g.mark(4_940)                                            # -1.2% today
    assert "daily_loss" in g.submit(buy()).reasons
    sell = brk.OrderRequest("NIFTYBEES", "sell", 1)
    assert "daily_loss" not in g.check(sell)


def test_guard_one_trade_per_symbol_per_day_but_stops_exempt(tmp_path):
    g, clock = guard(tmp_path)
    assert g.submit(buy()).allowed
    clock[0] += timedelta(seconds=5)
    assert "one_trade_per_day" in g.submit(buy()).reasons
    assert g.submit(brk.OrderRequest("NIFTYBEES", "sell", 1, tag="stop")).allowed
    clock[0] += timedelta(days=1)
    assert g.submit(buy()).allowed


# ---------------- crypto tax maths
def test_crypto_tax_no_setoff_and_tds_is_credit():
    assert ct.trade_tax(-1_000, cess=0) == 0
    assert ct.trade_tax(1_000, cess=0) == pytest.approx(300)
    assert ct.trade_tax(1_000) == pytest.approx(312)                 # + 4% cess
    tb = ct.TaxBook(cess=0)
    tb.on_sell(1_000, ct.tds(10_000))
    tb.on_sell(-1_000, ct.tds(9_000))                                # loss: no set-off
    assert tb.tax_accrued == pytest.approx(300) and tb.tds_accrued == pytest.approx(190)
    assert tb.settle() == pytest.approx(110) and tb.tax_paid == pytest.approx(300)
    tb.on_sell(-500, ct.tds(5_000))
    assert tb.settle() == pytest.approx(-50)                         # refund of TDS


def test_crypto_backtest_after_tax():
    close = data.synthetic_prices(800, seed=3, sigma=0.6)["close"]
    cash = ct.backtest_after_tax(close, pd.Series(0.0, index=close.index))
    assert cash["after_tax_end"] == 5_000 and cash["trades"] == 0
    up = pd.Series(np.linspace(100, 200, 300), index=pd.bdate_range("2024-01-01", periods=300))
    r = ct.backtest_after_tax(up, pd.Series(1.0, index=up.index))
    assert r["after_tax_end"] < r["pre_tax_end"] and r["tax_paid"] > 0 and r["tds_withheld"] > 0
    assert r["after_tax_end"] == pytest.approx(r["bh_after_tax_end"], rel=0.02)
    gross = 5_000 * (200 / up.iloc[1] - 1)
    assert r["tax_paid"] == pytest.approx(gross * 0.312, rel=0.02)
    # flipping weights: each losing sell gets no relief, so tax > 31.2% of net gain
    flip = pd.Series(np.tile([1.0, 1.0, 0.0], 100)[:300], index=up.index)
    wavy = up * (1 + 0.05 * np.sin(np.arange(300)))
    f = ct.backtest_after_tax(wavy, flip)
    assert f["losing_sells"] > 0 and f["tax_paid"] > 0


# ---------------- runner
def bars(n=600, seed=4):
    return data.synthetic_prices(n, seed=seed, regime_days=120, regime_drift=0.3)


def test_no_lookahead_future_bars_cannot_change_the_signal():
    b = bars()
    t = b.index[400]
    w0 = runner.decide(b, t, "tsmom_vt", lookback=126)
    m = b.copy()
    m.loc[m.index > t, ["open", "high", "low", "close"]] *= 5.0       # wreck the future
    m.loc[m.index > t, "close"] *= np.random.default_rng(0).uniform(0.1, 3, (m.index > t).sum())
    assert runner.decide(m, t, "tsmom_vt", lookback=126) == w0
    assert runner.visible_bars(b, t).index.max() == t


def test_decide_rejects_a_strategy_that_peeks(monkeypatch):
    b = bars()
    def cheat(name, close, **p):
        idx = close.index.append(pd.DatetimeIndex([close.index[-1] + pd.Timedelta(days=1)]))
        return pd.Series(1.0, index=idx)
    monkeypatch.setattr(runner, "weights", cheat)
    with pytest.raises(runner.LookAheadError):
        runner.decide(b, b.index[300], "tsmom_vt")


@pytest.mark.parametrize("track", ["A", "B"])
def test_runner_paper_mode_over_many_days(tmp_path, track):
    b = data.synthetic_prices(700, seed=4 if track == "A" else 7, sigma=0.18 if track == "A" else 0.6,
                              regime_days=60, regime_drift=0.5)
    out, flags = tmp_path / "o", tmp_path / "f"
    for t in b.index[-120:]:
        res = runner.run_paper(b, track=track, strategy="tsmom_vt", capital=5_000, out=out, flags=flags,
                               asof=t, params={"lookback": 63})
    st = res["state"]
    assert len(st["paper_days"]) == 120
    led = pd.read_csv(out / f"ledger-{track}.csv")
    assert len(led) >= 120 and "bench_after_tax_inr" in led.columns
    assert set(led["status"]) <= {"filled", "blocked", "no_change", "rejected"}
    assert "filled" in set(led["status"])
    assert (led.loc[led.side == "buy", "value_pct_capital"] <= 20.01).all()    # max position 20%
    s = res["summary"]
    for needle in ("Buy-and-hold", "after costs + tax", "Closed trades", "Paper days: 120/90", "Not advice"):
        assert needle in s
    assert (out / f"summary-{track}.txt").exists()
    if track == "B":
        assert st["broker"]["tds_withheld"] >= 0


def test_runner_cli_paper_and_live_refusals(tmp_path, capsys):
    common = ["--out", str(tmp_path / "o"), "--flags", str(tmp_path / "f")]
    assert runner.main(["--track", "A", "--synthetic", *common], env={}) == 0
    assert "Buy-and-hold NIFTYBEES" in capsys.readouterr().out
    assert runner.main(["--track", "A", "--mode", "live", *common], env={}) == 2
    err = capsys.readouterr().err
    assert "LIVE REFUSED" in err and "LIVE_TRADING" in err and "paper days" in err
    assert runner.main(["--track", "A", "--capital", "20000", "--synthetic", *common], env={}) == 2


def test_live_refuses_even_with_all_flags_because_adapters_are_stubs(tmp_path, capsys):
    out, flags = tmp_path / "o", tmp_path / "f"
    flags.mkdir()
    (flags / "GO").write_text("go")
    (flags / "GATE_PASS_B").write_text("T0001")
    st = runner._new_state(5_000.0)
    st["paper_days"] = [str(date(2026, 1, 1) + timedelta(days=i)) for i in range(90)]
    out.mkdir()
    (out / "state-B.json").write_text(__import__("json").dumps(st))
    env = {"LIVE_TRADING": "YES", "DELTA_API_KEY": "k-SECRET", "DELTA_API_SECRET": "s-SECRET"}
    common = ["--track", "B", "--mode", "live", "--out", str(out), "--flags", str(flags)]
    assert runner.main(common, env=env) == 3
    cap = capsys.readouterr()
    assert "TODO" in cap.err and "SECRET" not in cap.err + cap.out
    (flags / "KILL").write_text("x")
    assert runner.main(common, env=env) == 2
    assert "kill switch" in capsys.readouterr().err


def test_trade_stats_can_earn_with_low_win_rate():
    s = runner.trade_stats([100, -20, -20, -20])
    assert s["win_rate"] == 0.25 and s["payoff"] == pytest.approx(5.0)
    assert s["expectancy"] == pytest.approx(10.0)
    assert runner.trade_stats([])["trades"] == 0
    assert "expectancy Rs +10.00" in runner._stats_line([100, -20, -20, -20])


# ---------------- markov_regime candidate
def test_markov_matrix_rows_sum_to_one():
    st = strategies.regime_states(bars()["close"], 20, 0.05)
    m = strategies.markov_matrix(st)
    assert m.shape == (3, 3) and np.allclose(m.sum(axis=1), 1.0)
    assert np.allclose(strategies.markov_matrix(pd.Series([1.0, 1.0])).sum(axis=1), 1.0)


def test_markov_regime_future_bars_do_not_change_past_signals():
    c = bars()["close"]
    w = strategies.markov_regime(c)
    assert ((w >= 0) & (w <= 1)).all() and w.iloc[:20].eq(0).all()
    c2 = c.copy()
    c2.iloc[350:] = c2.iloc[350:] * np.random.default_rng(1).uniform(0.3, 3, len(c2) - 350)
    w2 = strategies.markov_regime(c2)
    pd.testing.assert_series_equal(w.iloc[:350], w2.iloc[:350])
    assert w.equals(strategies.markov_regime(c.iloc[:]))       # deterministic
    pd.testing.assert_series_equal(strategies.markov_regime(c.iloc[:350]), w.iloc[:350])


def test_markov_regime_is_registered_and_goes_through_the_gate(tmp_path):
    assert len(strategies.param_grid("markov_regime")) == 4
    reg = tmp_path / "trials.csv"
    close = data.synthetic_prices(5040, seed=1)["close"]        # random walk: nothing to find
    tid = trials.log_trial("H4-markov", "markov_regime", strategies.REGISTRY["markov_regime"][1],
                           "synthetic random walk seed 1", 4, path=reg)
    v = gate.evaluate(close, "markov_regime", tid, registry=reg)
    assert v.verdict == "rejected", v.summary()

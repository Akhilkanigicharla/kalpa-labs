"""A26 (Q7.9 + Q7.11): paper trader and risk warden. Synthetic data only, no network."""
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src import backtest, data, paper, risk
from src.strategies import weights

POT = 25_000.0


def book(**kw):
    return risk.RiskBook(pot=POT, **kw)


def buy(qty=10, price=100.0, stop=95.0, d=date(2026, 10, 19), sym="NIFTYBEES", source="signal"):
    return risk.Order(d, sym, "buy", qty, price, stop, source)


# ---------- risk (Q7.11) ----------

def test_buy_within_limits_passes():
    assert risk.check(buy(), book()) == []        # risk 50 <= 125, value 1,000 <= 5,000


def test_forced_breach_per_trade_risk_is_blocked_and_logged(tmp_path: Path):
    log = tmp_path / "breaches.csv"
    b = book(breach_log=log)
    out = risk.submit(buy(qty=30, stop=95.0), b)   # risk 150 > 125
    assert out.blocked and "per_trade_risk" in out.breaches
    assert "per_trade_risk" in log.read_text()
    assert b.positions == {}


def test_position_size_cap():
    assert "position_size" in risk.check(buy(qty=60, price=100.0, stop=99.0), book())   # 6,000 > 5,000


def test_max_open_positions():
    b = book()
    for i in range(3):
        assert not risk.submit(buy(qty=1, sym=f"S{i}"), b).blocked
    assert "max_open_positions" in risk.check(buy(qty=1, sym="S3"), b)
    assert risk.check(buy(qty=1, sym="S0"), b) == []          # adding to an open one is fine


def test_limits_never_looser_than_guard():
    # Guard (b7 risk agent): 1% risk/trade, 5% daily stop, 3 open, stop mandatory.
    L = risk.LIMITS
    assert L["per_trade_risk"] <= 0.01 and L["daily_loss"] <= 0.05 and L["max_open_positions"] <= 3


def test_buy_needs_a_stop_below_entry():
    assert "no_stop" in risk.check(buy(stop=None), book())
    assert "no_stop" in risk.check(buy(stop=101.0), book())


def test_override_is_a_breach():
    assert "override" in risk.check(buy(source="manual"), book())
    assert "override" in risk.check(risk.Order(date(2026, 10, 19), "X", "sell", 1, 100.0, None, "manual"), book())


@pytest.mark.parametrize("marks,rule", [
    ([("2026-10-16", 25_000), ("2026-10-19", 24_700)], "daily_loss"),          # -1.2% today
    ([("2026-10-12", 25_000), ("2026-10-13", 24_800), ("2026-10-14", 24_600),
      ("2026-10-16", 24_500), ("2026-10-19", 24_500)], None),                  # last week, new week flat
    ([("2026-10-19", 25_000), ("2026-10-20", 24_850), ("2026-10-21", 24_700),
      ("2026-10-22", 24_550)], "weekly_loss"),                                 # -1.8% wk... see below
])
def test_loss_limits(marks, rule):
    b = book()
    for d, eq in marks:
        b.mark(date.fromisoformat(d), eq)
    d = date.fromisoformat(marks[-1][0])
    got = risk.check(buy(d=d), b)
    if rule is None:
        assert got == []
    elif rule == "weekly_loss":
        # 24,550 is -1.8% for the week: under 2%, and no single day lost 1%, so allowed
        assert got == []
        b.mark(d, 24_490)                       # now -2.04% for the week
        assert "weekly_loss" in risk.check(buy(d=d), b)
    else:
        assert rule in got


def test_monthly_pause_and_drawdown_stop():
    b = book()
    b.mark(date(2026, 10, 1), 25_000)
    b.mark(date(2026, 10, 8), 24_700)
    b.mark(date(2026, 10, 15), 24_400)
    b.mark(date(2026, 10, 22), 23_990)            # -4.04% month to date
    assert "monthly_loss" in risk.check(buy(d=date(2026, 10, 23)), b)
    assert "monthly_loss" not in risk.check(buy(d=date(2026, 11, 2)), b)   # new month
    b.mark(date(2026, 11, 3), 22_400)             # -10.4% from the 25,000 peak
    assert "drawdown_stop" in risk.check(buy(d=date(2026, 11, 4)), b)


def test_sells_that_cut_risk_are_never_blocked_by_loss_limits():
    b = book()
    risk.submit(buy(qty=10), b)
    b.mark(date(2026, 10, 16), 25_000)
    b.mark(date(2026, 10, 19), 24_000)            # -4% day
    sell = risk.Order(date(2026, 10, 19), "NIFTYBEES", "sell", 10, 100.0, None, "signal")
    assert risk.check(sell, b) == []
    assert "oversell" in risk.check(risk.Order(date(2026, 10, 19), "NIFTYBEES", "sell", 11, 100.0, None, "signal"), b)


def test_capital_rules_are_marked_pending():
    assert risk.LIMITS_STATUS == "pending CEO sign-off (Q7.8)"


# ---------- paper (Q7.9) ----------

def _bars(n=900, seed=11):
    return data.synthetic_prices(n, seed=seed)


def _backtest_trade_days(bars, strategy, last_days):
    close = bars["close"]
    w = weights(strategy, close).reindex(close.index).fillna(0.0).clip(0, 1)
    res = backtest.run(close, w)
    change = res.held.shift(-1).fillna(res.held.iloc[-1]) - res.held
    days = change[change.abs() > 0.01]
    window = close.index[-last_days - 1:-1]            # signal days that have a next open
    return [(d.date(), "buy" if days[d] > 0 else "sell") for d in days.index if d in window]


@pytest.mark.parametrize("strategy", ["sma_cross", "ma_filter", "tsmom"])
def test_dry_run_over_20_days_matches_backtest_trades(strategy, tmp_path: Path):
    bars = _bars()
    run = paper.dry_run(bars, strategy, days=20, symbol="SYNTH", pot=POT, ledger=tmp_path / "l.csv")
    want = _backtest_trade_days(bars, strategy, 20)
    got = [(s.signal_date, s.side) for s in run.signals]
    assert got == want


def test_dry_run_with_trades_matches_too(tmp_path: Path):
    # pick a window guaranteed to hold position changes
    bars = _bars(seed=4)
    for days in (60, 120):
        run = paper.dry_run(bars, "sma_cross", days=days, symbol="SYNTH", pot=POT, ledger=tmp_path / f"{days}.csv")
        assert [(s.signal_date, s.side) for s in run.signals] == _backtest_trade_days(bars, "sma_cross", days)
    assert len(run.signals) >= 4 and sum(f.status == "filled" for f in run.fills) >= 4


def test_fills_at_next_open_with_costs(tmp_path: Path):
    bars = _bars(seed=4)
    run = paper.dry_run(bars, "sma_cross", days=120, symbol="SYNTH", pot=POT, ledger=tmp_path / "l.csv")
    filled = [f for f in run.fills if f.status == "filled"]
    assert filled
    for f in filled:
        nxt = bars.index[bars.index.get_loc(pd.Timestamp(f.signal_date)) + 1]
        assert f.fill_date == nxt.date()
        assert f.fill_price == pytest.approx(bars.loc[nxt, "open"])
        assert f.cost_inr > 0


def test_risk_rules_shrink_or_block_orders(tmp_path: Path):
    bars = _bars(seed=4)
    run = paper.dry_run(bars, "sma_cross", days=120, symbol="SYNTH", pot=POT, ledger=tmp_path / "l.csv")
    for f in run.fills:
        if f.side == "buy" and f.status == "filled":
            assert f.qty * f.fill_price <= 0.20 * POT * 1.0001
    # forced breach: a manual order on top of the signals is blocked and logged
    blocked = paper.place_manual(run, bars, "SYNTH", "buy", 1)
    assert blocked.status == "blocked" and "override" in blocked.reason


def test_ledger_has_no_raw_prices(tmp_path: Path):
    led = tmp_path / "ledger.csv"
    paper.dry_run(_bars(seed=4), "sma_cross", days=120, symbol="SYNTH", pot=POT, ledger=led)
    df = pd.read_csv(led)
    assert list(df.columns) == paper.LEDGER_COLUMNS
    assert not {"open", "high", "low", "close", "price", "fill_price"} & set(df.columns)
    assert len(df) >= 1


def test_last_day_signal_stays_pending(tmp_path: Path):
    bars = _bars(seed=4)
    full = paper.dry_run(bars, "sma_cross", days=300, symbol="SYNTH", pot=POT, ledger=tmp_path / "a.csv")
    sig_day = [s.signal_date for s in full.signals if s.side == "buy"][-1]   # a fresh run holds nothing to sell
    cut = bars.loc[:pd.Timestamp(sig_day)]                      # today is the signal day
    run = paper.dry_run(cut, "sma_cross", days=5, symbol="SYNTH", pot=POT, ledger=tmp_path / "b.csv",
                        include_last=True)
    assert run.fills[-1].status == "pending" and run.fills[-1].signal_date == sig_day


def test_no_broker_or_network_code():
    for name in ("paper.py", "risk.py"):
        src = (Path(__file__).resolve().parents[1] / "src" / name).read_text()
        for bad in ("import requests", "urllib", "http", "kiteconnect", "dhanhq", "socket", "place_order("):
            assert bad not in src, f"{name} contains {bad}"

from datetime import date, timedelta

from src.bot import run, targets_for
from src.data import synthetic_prices
from src.risk import LIMITS


def bars(seed=0):
    df = synthetic_prices(400, seed=seed, mu=0.30, sigma=0.10)   # strong uptrend: ma_filter says "hold"
    return {"NIFTYBEES": df, "GOLDBEES": synthetic_prices(400, seed=seed + 1, mu=0.30, sigma=0.10)}


def test_targets_respect_risk_and_size():
    b = bars()
    tg, last = targets_for(b, "ma_filter", 5000, {})
    for sym, (q, stop) in tg.items():
        px = last[sym]
        assert stop < px
        assert q * (px - stop) <= LIMITS["per_trade_risk"] * 5000 + 1e-6
        assert q * px <= LIMITS["position_size"] * 5000 + 1e-6


def test_daily_run_keeps_state_and_is_dry(tmp_path):
    sp = tmp_path / "state.json"
    b = bars()
    g = run("ma_filter", "", ["NIFTYBEES", "GOLDBEES"], bars=b, env={"KL_LIVE_CAPITAL": "5000"},
            state_path=sp, today=date(2026, 11, 9))
    assert not g.live and sp.exists()
    first = dict(g.broker.positions())
    assert first, g.alerts   # it bought something within the limits
    g2 = run("ma_filter", "", ["NIFTYBEES", "GOLDBEES"], bars=b, env={"KL_LIVE_CAPITAL": "5000"},
             state_path=sp, today=date(2026, 11, 10))
    assert g2.broker.positions() == first        # same signal → no new orders
    assert len(g2.book.marks) == 2               # loss caps see yesterday


def test_short_history_never_trades(tmp_path):
    short = {"NIFTYBEES": synthetic_prices(24, seed=3)}
    g = run("ma_filter", "", ["NIFTYBEES"], bars=short, env={}, state_path=tmp_path / "s.json", today=date(2026, 11, 9))
    assert g.broker.positions() == {} and "too little price history" in g.alerts[0]

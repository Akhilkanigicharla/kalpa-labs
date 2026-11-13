import numpy as np
import pandas as pd
import pytest

from src import intraday as I


def day_bars(path, start="2026-11-12 09:15"):
    idx = pd.date_range(start, periods=len(path), freq="5min", tz="Asia/Kolkata")
    c = pd.Series(path, index=idx, dtype=float)
    o = c.shift(1).fillna(c.iloc[0])
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) + 0.05, "low": np.minimum(o, c) - 0.05, "close": c})


def session(n=75, seed=0, drift=0.0):
    r = np.random.default_rng(seed).normal(drift, 0.001, n)
    return day_bars(list(280 * np.cumprod(1 + r)))


def test_breakout_long_hits_target_and_pays_costs():
    path = [100, 100.4, 99.8, 100.1] + [100.6, 101.0, 101.5, 102.0, 102.5, 103.0] + [103.0] * 20
    tr = I.run_day(day_bars(path), "orb", 5_000, r=1.0)
    t = tr[0]
    assert t.side == 1 and t.reason == "target" and t.entry_at == "09:40"      # signal at 09:35 close -> next open
    assert t.cost > 0 and t.net < t.gross


def test_stop_counted_first_when_both_inside_one_bar():
    path = [100, 100.4, 99.8, 100.1, 100.6, 100.6]
    df = day_bars(path + [100.6] * 20)
    df.iloc[6, df.columns.get_loc("high")] = 110      # one wild bar touches target AND stop
    df.iloc[6, df.columns.get_loc("low")] = 90
    t = I.run_day(df, "orb", 5_000, r=1.0)[0]
    assert t.reason == "stop"


def test_forced_exit_by_1515_and_no_entry_after_1445():
    s = session(75, seed=3)
    for strat, grid in I.GRIDS.items():
        for p in grid:
            for t in I.run_day(s, strat, 5_000, **p):
                assert t.exit_at <= "15:25" and t.entry_at <= "14:45"
                assert t.reason in ("target", "stop", "eod")


def test_future_bars_cannot_change_earlier_trades():
    s = session(75, seed=5)
    cut = 40
    early = [t for t in I.run_day(s, "vwap", 5_000, stop=0.003, target=0.006) if t.exit_at < s.index[cut].strftime("%H:%M")]
    wrecked = s.copy()
    wrecked.iloc[cut + 1:] *= 1.5
    again = [t for t in I.run_day(wrecked, "vwap", 5_000, stop=0.003, target=0.006) if t.exit_at < s.index[cut].strftime("%H:%M")]
    assert [(t.entry_at, t.exit_at, t.reason) for t in early] == [(t.entry_at, t.exit_at, t.reason) for t in again]


def test_max_two_trades_a_day_and_verdict_rules():
    s = session(75, seed=9)
    assert all(len(I.run_day(s, k, 5_000, **g[0])) <= I.MAX_TRADES_PER_DAY for k, g in I.GRIDS.items())
    good = {"trades": 40, "net_rs": 100.0, "t_stat": 2.5}
    assert I.verdict(good, ({"net_rs": 1}, {"net_rs": 1}))[0] == "paper"
    assert I.verdict({**good, "trades": 10}, ({"net_rs": 1}, {"net_rs": 1}))[0] == "rejected"
    assert I.verdict(good, ({"net_rs": 1}, {"net_rs": -1}))[0] == "rejected"
    with pytest.raises(ValueError):
        I.signals(s, "nope")


def test_clean_keeps_session_only():
    idx = pd.date_range("2026-11-12 09:00", periods=90, freq="5min", tz="Asia/Kolkata")
    df = pd.DataFrame({"Open": 1.0, "High": 1.0, "Low": 1.0, "Close": 1.0}, index=idx)
    out = I.clean(df)
    assert out.index.min().strftime("%H:%M") == "09:15" and out.index.max().strftime("%H:%M") <= "15:25"


def test_paper_day_logs_once_and_store_accumulates(tmp_path):
    a = session(75, seed=11)
    b = day_bars(list(a["close"].values), start="2026-11-13 09:15")
    both = pd.concat([a, b])
    txt = I.paper_day(both, tmp_path / "p")
    assert "PAPER" in txt and "Running total" in txt and "Not advice" in txt
    led1 = (tmp_path / "p" / "trades.csv").read_text(encoding="utf-8")
    assert "Already done" in I.paper_day(both, tmp_path / "p")
    assert (tmp_path / "p" / "trades.csv").read_text(encoding="utf-8") == led1
    store = tmp_path / "bars.parquet"
    I.store_bars(a, store)
    out = I.store_bars(both, store)
    assert len(out) == len(I.clean(both)) and out.index.is_monotonic_increasing

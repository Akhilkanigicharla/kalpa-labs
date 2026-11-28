"""A307: hourly gold strategies vs prop rules. Synthetic bars only (no network)."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(R))
spec = importlib.util.spec_from_file_location("hourly_gold_prop", R / "hourly_gold_prop.py")
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)


def bars(day_paths):
    """day_paths: list of 24-item lists of (o, h, l, c), one list per UTC day."""
    rows, idx = [], []
    for k, path in enumerate(day_paths):
        for hr, b in enumerate(path):
            rows.append(b)
            idx.append(pd.Timestamp("2025-01-06", tz="UTC") + pd.Timedelta(days=k, hours=hr))
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=pd.DatetimeIndex(idx))


def flat_day(px=100.0):
    return [(px, px + 0.5, px - 0.5, px)] * 24


def test_breakout_long_hits_target():
    day = flat_day()                                   # Asian range 99.5..100.5
    day[8] = (100, 101.2, 99.9, 101)                   # 08:00 closes above 100.5 -> long at 09:00 open
    day[9] = (101, 101.1, 100.8, 101)
    day[10] = (101, 103, 100.9, 102.5)                 # target 101 + 1.5 * (101 - 99.5) = 103.25 not hit
    day[11] = (102.5, 104, 102.4, 103.9)               # target hit here
    t = H.trades(bars([day]), "breakout")
    assert len(t) == 1 and t[0]["side"] == 1 and t[0]["why"] == "target"
    assert t[0]["px_in"] == 101 and abs(t[0]["px_out"] - 103.25) < 1e-9 and t[0]["stop"] == 99.5


def test_breakout_stop_first_when_both_in_one_bar():
    day = flat_day()
    day[8] = (100, 101.2, 99.9, 101)
    day[9] = (101, 110, 90, 101)                       # stop and target in the same bar -> stop
    t = H.trades(bars([day]), "breakout")
    assert t[0]["why"] == "stop" and t[0]["px_out"] == 99.5


def test_breakout_one_trade_a_day_and_flat_by_16():
    day = flat_day()
    day[8] = (100, 101.2, 99.9, 101)                   # long, then drifts without stop or target
    for hr in range(9, 24):
        day[hr] = (101, 101.3, 100.8, 101.1)
    day[14] = (101, 101.2, 99.0, 99.2)                 # would be a short signal later: ignored (one per day)
    day[14] = (101, 101.3, 100.8, 101.1)
    t = H.trades(bars([day]), "breakout")
    assert len(t) == 1 and t[0]["why"] == "time"
    assert t[0]["exit"] == 16                          # closes on the 16:00 UTC bar


def test_no_signal_without_asian_range():
    day = flat_day()
    t = H.trades(bars([day]), "breakout")
    assert t == []


def test_pullback_needs_warmup_and_has_no_lookahead():
    rng = np.random.default_rng(1)
    days = []
    px = 100.0
    for _ in range(15):
        path = []
        for _ in range(24):
            o = px
            px = px * (1 + 0.001 + rng.normal(0, 0.002))
            path.append((o, max(o, px) + 0.05, min(o, px) - 0.05, px))
        days.append(path)
    d = bars(days)
    full = H.trades(d, "pullback")
    assert full and all(t["entry"] > 200 for t in full)
    cut = H.trades(d.iloc[:300], "pullback")
    early = [t for t in full if t["exit"] < 299]
    assert [(t["entry"], t["side"]) for t in cut if t["exit"] < 299] == [(t["entry"], t["side"]) for t in early]
    assert all(d.index[t["exit"]].hour <= 16 for t in full)


def test_random_baseline_same_size_and_one_at_a_time():
    rng = np.random.default_rng(2)
    days = [[(100 + rng.normal(0, 1),) * 4 for _ in range(24)] for _ in range(30)]
    days = [[(o, o + 1, o - 1, o) for (o, _, _, _) in day] for day in days]
    d = bars(days)
    like = [{"px_in": 100.0, "stop": 99.0, "exit": 0}] * 10
    r = H.random_like(d, like, "breakout", 0)
    assert 1 <= len(r) <= 10
    assert all(abs(abs(t["px_in"] - t["stop"]) / t["px_in"] - 0.01) < 1e-9 for t in r)
    assert all(r[k]["entry"] > r[k - 1]["exit"] for k in range(1, len(r)))


def test_daily_book_and_challenge_daily_loss():
    rule = H.gc.RULES["HF1"]
    t = {"entry": 0, "exit": 1, "side": 1, "px_in": 7000.0, "px_out": 6930.0, "stop": 6930.0, "why": "stop", "day": 1}
    d = pd.DataFrame({"open": [7000, 6990], "high": [7010, 6995], "low": [6990, 6920], "close": [6995, 6930]})
    book = H.daily_book(d, [t], rule["size"], 0.01)
    q = int(1000 // 70)                                # 14 grams
    w, c = book[1]
    assert abs(c - (-70 * q - H.COST * q * 7000)) < 1e-6 and w <= c
    st, _ = H.run_challenge([1], {1: (-6000.0, -6000.0)}, rule)
    assert st == "failed"                              # 6% > the 5% daily loss
    st, _ = H.run_challenge([1, 2], {1: (-100.0, 50.0)}, rule)
    assert st == "unfinished"


def test_to_inr_converts_and_uses_utc():
    idx = pd.date_range("2025-01-06 09:00", periods=3, freq="h", tz="America/New_York")
    g = pd.DataFrame({"Open": [2000.0] * 3, "High": [2001.0] * 3, "Low": [1999.0] * 3, "Close": [2000.0] * 3}, index=idx)
    fx = pd.Series([85.0], index=pd.DatetimeIndex(["2025-01-03"]))
    d = H.to_inr(g, fx)
    assert str(d.index.tz) == "UTC" and d.index[0].hour == 14
    assert abs(d["close"].iloc[0] - 2000 * 85 / 31.1035) < 1e-6


def test_day_numbers_work_for_second_resolution_index():
    idx = pd.DatetimeIndex(["2025-01-06 23:00", "2025-01-07 01:00"], tz="UTC").as_unit("s")
    assert list(H._days(idx)) == [20094, 20095]

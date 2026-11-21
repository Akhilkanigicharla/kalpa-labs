import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
import ea_design_gold as e  # noqa: E402


def test_align_uses_only_closed_higher_bars():
    h = pd.DataFrame({"v": [1, 2, 3]}, index=pd.date_range("2026-01-05 00:00", periods=3, freq="1h"))
    t = pd.Series(pd.to_datetime(["2026-01-05 00:45", "2026-01-05 01:00", "2026-01-05 01:59"]))
    v = e.align(t, h, pd.Timedelta("1h")).v.tolist()
    assert pd.isna(v[0]) and v[1] == 1 and v[2] == 1        # bar 01:00 closes at 02:00


def test_sessions_and_friday_cutoff():
    assert e.in_session(pd.Timestamp("2026-11-18 08:00"))         # Wed London
    assert not e.in_session(pd.Timestamp("2026-11-18 07:00"))     # first 30 min skipped
    assert not e.in_session(pd.Timestamp("2026-11-18 12:30"))     # lunch gap
    assert not e.in_session(pd.Timestamp("2026-11-21 09:00"))     # Saturday


def test_ladder_three_legs():
    import numpy as np
    n = 6
    close_t = pd.date_range("2026-01-05", periods=n, freq="1h")
    o = np.full(n, 100.0); c = o.copy()
    h = np.array([100, 111, 121, 131, 131, 131.0]); lo = np.array([99, 101, 111, 121, 121, 121.0])
    pnl, k, hits = e.ladder_exit(o, h, lo, c, close_t, 0, 1, 100.0, 10.0, 5.0)
    assert hits == 3 and pnl == 10 + 20 + 30                 # all three targets
    lo2 = np.array([99, 99, 99.5, 90, 90, 90.0]); h2 = np.array([100, 111, 105, 105, 105, 105.0])
    pnl, k, hits = e.ladder_exit(o, h2, lo2, c, close_t, 0, 1, 100.0, 10.0, 5.0)
    assert hits == 1 and abs(pnl - (10 + 2 * 0.2)) < 1e-9      # target 1, then out at breakeven + 0.2
    lo3 = np.array([89, 99, 99, 99, 99, 99.0])
    assert e.ladder_exit(o, h, lo3, c, close_t, 0, 1, 100.0, 10.0, 5.0)[0] == -30   # stop before targets


def test_ladder_run_sets_scaling_before_features(monkeypatch):
    seen = []
    monkeypatch.setattr(e, "h1_features", lambda h1: seen.append(e.SCALED) or pd.DataFrame(
        dict(trend=0, last_hi=0.0, last_lo=0.0), index=h1.index))
    monkeypatch.setattr(e, "h4_features", lambda h4, h1: pd.DataFrame(dict(regime=0, score=0), index=h4.index))
    e.SCALED = False
    idx = pd.date_range("2026-01-05", periods=300, freq="1h")
    h1 = pd.DataFrame(dict(open=1.0, high=1.1, low=0.9, close=1.0), index=idx)
    e.ladder_run(h1)
    assert seen == [True]

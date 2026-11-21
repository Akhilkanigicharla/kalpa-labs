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

"""A325: event times, no look-ahead in macro features, streak uses only closed trades."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import macro_layer_gold as ml  # noqa: E402


def test_event_times_utc():
    ev = ml.events_utc()
    assert pd.Timestamp("2026-11-10 13:30") in ev          # CPI 08:30 New York (EST) = 13:30 UTC
    assert pd.Timestamp("2026-07-29 18:00") in ev          # FOMC 14:00 New York (EDT) = 18:00 UTC
    assert "2025-08-22" not in ml.FOMC                     # Jackson Hole is not an FOMC meeting


def _mac():
    idx = pd.date_range("2025-01-01", periods=400, freq="D")
    v = np.linspace(10, 30, 400)
    return pd.DataFrame(dict(vix=v, gvz=v, tnx=v, dxy=v), index=idx)


def test_streak_uses_closed_trades_only():
    t0 = pd.Timestamp("2026-01-05 08:00")
    rows = [dict(t_in=t0 + pd.Timedelta(hours=10 * i), t_out=t0 + pd.Timedelta(hours=10 * i + 2), side=1, r=1.0, strategy="X")
            for i in range(6)]
    rows.append(dict(t_in=t0 + pd.Timedelta(hours=51), t_out=t0 + pd.Timedelta(hours=60), side=1, r=-1.0, strategy="X"))
    f = ml.features(pd.DataFrame(rows), _mac())
    # the trade entered at hour 51 sees 5 closed trades (hours 2..42); the one at 50 has not closed (t_out 52)
    assert f.loc[f.t_in == t0 + pd.Timedelta(hours=51), "last5"].iloc[0] == 5.0


def test_macro_uses_previous_day():
    t0 = pd.Timestamp("2025-12-01 10:00")
    f = ml.features(pd.DataFrame([dict(t_in=t0, t_out=t0 + pd.Timedelta(hours=1), side=1, r=0.5, strategy="X")]), _mac())
    assert bool(f.tnx_dn.iloc[0]) is False                 # rising series: yield not falling, from yesterday's value

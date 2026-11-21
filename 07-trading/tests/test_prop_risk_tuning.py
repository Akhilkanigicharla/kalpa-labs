"""A331: the challenge simulator passes steady winners and fails a -5% day."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
import prop_risk_tuning as pr  # noqa: E402

PLAN = dict(base=0.01, dd_ladder=False, finish=False, daystop=0.04, funded_mult=1.0)


def _t(rs, gap_h=24):
    t0 = pd.Timestamp("2025-01-06 08:00")
    return pd.DataFrame(dict(t_in=[t0 + pd.Timedelta(hours=gap_h * i) for i in range(len(rs))],
                             t_out=[t0 + pd.Timedelta(hours=gap_h * i + 2) for i in range(len(rs))],
                             r=rs, mult=1.0))


def test_steady_winner_gets_funded():
    res = pr.attempt(pr.arrays(_t([2.0] * 30)), pd.Timestamp("2025-01-06"), PLAN)
    assert res["funded"]


def test_big_losing_day_fails_step1():
    res = pr.attempt(pr.arrays(_t([-2.0, -2.0, -2.0], gap_h=1)), pd.Timestamp("2025-01-06"), PLAN)
    assert res["res"] == "failed step 1"

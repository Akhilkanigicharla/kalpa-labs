"""A326: funded-account simulator follows The5%ers High Stakes rules."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import funded_sim_gold as f  # noqa: E402


def _t(rs, gap_h=24):
    t0 = pd.Timestamp("2025-01-06 08:00")
    return pd.DataFrame(dict(t_in=[t0 + pd.Timedelta(hours=gap_h * i) for i in range(len(rs))],
                             t_out=[t0 + pd.Timedelta(hours=gap_h * i + 2) for i in range(len(rs))],
                             r=rs, w=1.0, strategy="X", side=1))


def test_needs_three_profitable_days():
    t = _t([11.0, 1.0, 1.0, 5.0, 1.0, 1.0, 1.0])            # 1% risk: +11% day 1, but only 1 profitable day
    res = f.run_attempt(t, t.t_in.min(), 0.01, 0.10, 0.05, t.t_out.max())
    assert res["outcome"] == "funded, still running"    # passes only after the 3rd profitable day of each step


def test_daily_loss_fails():
    t = _t([-3.0, -3.0], gap_h=1)                          # -6% in one day at 1% risk
    res = f.run_attempt(t, t.t_in.min(), 0.01, 0.10, 0.05, t.t_out.max())
    assert res["outcome"] == "failed step 1"

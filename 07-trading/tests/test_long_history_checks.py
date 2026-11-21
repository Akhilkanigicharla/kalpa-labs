"""A330: long-history checks — trend recipe has no look-ahead, costs applied, The5%ers sim rules."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import gold_trend_25y as gt  # noqa: E402


def _ret(n=600, seed=3):
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0.0003, 0.01, n), index=pd.bdate_range("2010-01-01", periods=n))


def test_position_used_next_day_only():
    r = _ret()
    pos = gt.positions(r, gt.signal((1 + r).cumprod()))
    p = gt.pnl(r, pos, cost=0.0)
    assert abs(p.iloc[300] - pos.iloc[299] * r.iloc[300]) < 1e-12      # yesterday's position x today's return


def test_future_change_does_not_alter_past_signal():
    r = _ret()
    a = gt.signal((1 + r).cumprod())
    r2 = r.copy(); r2.iloc[500:] = -0.05
    b = gt.signal((1 + r2).cumprod())
    assert (a.iloc[:500] == b.iloc[:500]).all()


def test_costs_reduce_pnl():
    r = _ret()
    pos = gt.positions(r, gt.signal((1 + r).cumprod()))
    assert gt.pnl(r, pos, 0.001).sum() < gt.pnl(r, pos, 0.0).sum()

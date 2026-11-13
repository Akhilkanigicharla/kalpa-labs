"""A281 Alpha Brain: inputs never see the future; walk-forward trains only on earlier years. Synthetic data."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(R))
spec = importlib.util.spec_from_file_location("a281", R / "a281_alpha_brain.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def _world(n=1600, k=12, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    px = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(3e-4, 0.015, (n, k)), axis=0)), index=idx,
                      columns=[f"S{i}" for i in range(k)])
    nifty = px.mean(axis=1)
    vix = pd.Series(15 + rng.normal(0, 2, n), index=idx)
    inr = pd.Series(80 + np.cumsum(rng.normal(0, 0.1, n)), index=idx)
    cpi = pd.Series(np.linspace(100, 150, 90), index=pd.date_range("2013-01-01", periods=90, freq="MS"))
    return px, nifty, vix, inr, cpi


def test_features_do_not_use_the_future():
    px, nifty, vix, inr, cpi = _world()
    d = px.index[1200]
    fut = px.copy()
    fut.iloc[1201:] *= 3.0
    a = B.panel(px, nifty, vix, inr, cpi, [d]).drop(columns=["y", "fwd"])
    b = B.panel(fut, nifty, vix, inr, cpi, [d]).drop(columns=["y", "fwd"])
    pd.testing.assert_frame_equal(a, b)


def test_walk_forward_trains_before_each_test_year():
    px, nifty, vix, inr, cpi = _world()
    dates = list(px.index[300::5])
    pn = B.panel(px, nifty, vix, inr, cpi, dates)
    B.FIRST_TEST = 2019
    pred = B.walk_forward(pn)
    assert pred.date.dt.year.min() == 2019
    assert pred.score.between(0, 1).all()
    assert pred.groupby("date").asset.nunique().min() >= 10


def test_picks_are_affordable_whole_shares():
    px, *_ = _world()
    d = px.index[-1]
    px.loc[d, "S0"] = 50_000.0                         # one share costs more than a 1/5 slice of Rs 10,000
    pred = pd.DataFrame({"date": d, "asset": px.columns, "score": np.linspace(1, 0, px.shape[1])})
    t = B.targets_from(pred, px, [d], 5)[d]
    assert "S0" not in t and len(t) == 5 and abs(sum(t.values()) - 1) < 1e-9

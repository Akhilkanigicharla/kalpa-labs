import numpy as np
import pandas as pd

from src import strategies as S


def _prices(n=400, seed=1):
    r = np.random.default_rng(seed).normal(0.0004, 0.01, n)
    return pd.Series(100 * np.exp(np.cumsum(r)), index=pd.bdate_range("2020-01-01", periods=n))


def test_registered_and_binary():
    assert "ema_cross" in S.REGISTRY
    w = S.ema_cross(_prices())
    assert set(w.unique()) <= {0.0, 1.0}
    assert (w.iloc[:21] == 0).all()  # warm-up stays in cash


def test_no_lookahead():
    p = _prices()
    w = S.ema_cross(p)
    q = p.copy()
    q.iloc[300:] *= 3  # change the future only
    assert w.iloc[:300].equals(S.ema_cross(q).iloc[:300])


def test_uptrend_is_long():
    p = pd.Series(np.linspace(100, 200, 200), index=pd.bdate_range("2021-01-01", periods=200))
    assert S.ema_cross(p).iloc[-1] == 1.0

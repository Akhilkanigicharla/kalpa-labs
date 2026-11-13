import numpy as np
import pandas as pd
import pytest

from src import kronos_paper as K


def bars(n=420, seed=0):
    idx = pd.bdate_range("2025-01-01", periods=n)
    c = 100 * np.cumprod(1 + np.random.default_rng(seed).normal(0.0005, 0.01, n))
    o = np.r_[c[0], c[:-1]] * 1.001
    return pd.DataFrame({"Open": o, "High": np.maximum(o, c) * 1.002, "Low": np.minimum(o, c) * 0.998,
                         "Close": c, "Volume": 1e6}, index=idx)


def test_books_open_to_open_with_no_lookahead_and_is_idempotent(tmp_path):
    b = bars()
    up = lambda df: float(df["close"].iloc[-1]) * 1.01       # always predicts up  # noqa: E731
    sp = tmp_path / "s.json"
    for k in range(400, 404):                                # four daily runs
        st = K.step(b.iloc[:k + 1], sp, up)
    assert len(st["decisions"]) == 4 and len(st["booked"]) == 2   # only decisions with open(t+2) known
    d0 = pd.Timestamp(st["decisions"][0]["day"])
    o = b["Open"]
    j = list(o.index).index(d0)
    first = o.iloc[j + 2] / o.iloc[j + 1] - 1 - K.SWITCH_COST      # first switch into the ETF pays cost
    assert st["booked"][0]["ret"] == pytest.approx(first)
    again = K.step(b.iloc[:404], sp, up)
    assert again.get("skipped") and len(again["decisions"]) == 4
    assert "PAPER" in K.summary(again) and "Not advice" in K.summary(again)


def test_down_prediction_parks_in_liquid_etf(tmp_path):
    b = bars(seed=1)
    down = lambda df: float(df["close"].iloc[-1]) * 0.99     # noqa: E731
    sp = tmp_path / "s.json"
    for k in range(400, 404):
        st = K.step(b.iloc[:k + 1], sp, down)
    daily_cash = (1 + K.CASH_RATE) ** (1 / 252) - 1
    assert all(r["ret"] == pytest.approx(daily_cash) for r in st["booked"])
    with pytest.raises(ValueError):
        K.step(b.iloc[:100], tmp_path / "x.json", down)


def test_model_is_pinned():
    assert len(K.MODEL[1]) == 40 and len(K.TOKENIZER[1]) == 40
    assert (K.VENDOR / "LICENSE").exists() and (K.VENDOR / "model" / "kronos.py").exists()

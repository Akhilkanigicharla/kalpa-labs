import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
import phase3_gate as p  # noqa: E402


def test_persistence_needs_two_strong_bars_and_three_weak():
    raw = pd.DataFrame(dict(score=[4, 1, 4, 4, 2, 2, 5, 1, 1, 1], dirn=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1]))
    assert p.persist(raw).tolist() == [0, 0, 0, 1, 1, 1, 1, 1, 1, 0]


def test_no_direct_flip_needs_ranging_first():
    raw = pd.DataFrame(dict(score=[5, 5, 5, 5], dirn=[1, 1, -1, -1]))
    assert p.persist(raw).tolist() == [0, 1, 1, 1]              # bull stays until 3 weak bars


def test_round_number_rule_always_hits_with_dollar_pips():
    idx = pd.date_range("2026-01-05", periods=40, freq="1h")
    c = 3500 + np.arange(40) * 3.7
    h1 = pd.DataFrame(dict(open=c, high=c + 1, low=c - 1, close=c), index=idx)
    assert (p.liquidity(h1) <= 0.75).all()

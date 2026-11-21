import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
import combo_gold as c  # noqa: E402
from src.smc import Zone  # noqa: E402


def _d(n=60):
    idx = pd.date_range("2025-01-01", periods=n, freq="h")
    x = 100 + np.sin(np.arange(n) / 3)
    return pd.DataFrame(dict(open=x, high=x + 0.5, low=x - 0.5, close=x), index=idx)


def test_confirm_needs_recent_overlapping_zone():
    d = _d()
    a = [Zone(40, 100.2, 99.8, 99.5, "a")]
    assert c.confirm(a, [Zone(35, 100.1, 99.9, 99.6, "b")], d, 12) == a        # recent + overlapping
    assert c.confirm(a, [Zone(20, 100.1, 99.9, 99.6, "b")], d, 12) == []       # too old
    assert c.confirm(a, [Zone(38, 110, 109, 108, "b")], d, 12) == []           # far away
    assert c.confirm(a, [Zone(41, 100.1, 99.9, 99.6, "b")], d, 12) == []       # from the future


def test_selection_rule():
    assert c.selected_ok(dict(n=30, r=0.10, p=0.04))
    assert not c.selected_ok(dict(n=29, r=0.5, p=0.0))
    assert not c.selected_ok(dict(n=50, r=0.09, p=0.0))
    assert not c.selected_ok(dict(n=50, r=0.5, p=0.05))

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
import msnr_gold_robust as m  # noqa: E402


def test_bh_matches_hand_calc():
    q = m.bh(np.array([0.01, 0.04, 0.03, 0.5]))
    assert np.allclose(q, [0.04, 0.0533333, 0.0533333, 0.5], atol=1e-6)


def test_verdict_needs_every_rule():
    base = dict(is_n=50, is_r=0.2, oos_n=40, oos_r=0.3, oos_r_2x=0.25, p=0.0001, placebo_r=0.0)
    a = dict(base, cfg=("1h", "fresh_v", "short", 2, False, True, True))
    b = dict(base, cfg=("1h", "fresh_v", "short", 5, False, True, True))
    assert all(r["pass"] for r in m.verdict([dict(a), dict(b)]))
    bad = dict(b, oos_r=-0.1)                            # neighbour k fails -> a cannot pass
    assert not m.verdict([dict(a), bad])[0]["pass"]
    thin = dict(a, oos_n=20)
    assert "oos<30" in m.verdict([thin, dict(b)])[0]["why"]


def test_level_filter_blocks_wrong_side():
    idx = pd.date_range("2026-01-01", periods=5, freq="h")
    real = pd.DataFrame(dict(open=[3000.0] * 5, high=[3001.0] * 5, low=[2999.0] * 5, close=[3000.0] * 5), index=idx)
    z = [m.Zone(3, 1 / 3000, 1 / 3001, 1 / 3010, "x")]
    assert m.filt(z, real, m.mirror(real), False, True, "short") == []      # below 3100: no shorts


def test_paper_kill(tmp_path):
    (tmp_path / "KILL").write_text("x")
    assert m.paper(tmp_path / "p", flags=tmp_path)["status"] == "killed"

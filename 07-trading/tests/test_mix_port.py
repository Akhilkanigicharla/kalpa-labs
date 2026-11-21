"""A327: the MT5 mix engine's logic (Python copy in research/mix_port.py) gives exactly the research setups."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import mix_port as mp  # noqa: E402
import gold_ema9_msnr as g  # noqa: E402
import msnr_gold_robust as mr  # noqa: E402
from src.msnr import SETUPS, mirror  # noqa: E402


def _walk(n=700, seed=4):
    rng = np.random.default_rng(seed)
    c = 3000 + np.cumsum(rng.normal(0, 6, n))
    o = np.r_[c[0], c[:-1]] + rng.normal(0, 1.5, n)
    idx = pd.date_range("2025-01-01", periods=n, freq="4h")
    d = pd.DataFrame(dict(open=o, high=np.maximum(o, c) + abs(rng.normal(0, 3, n)),
                          low=np.minimum(o, c) - abs(rng.normal(0, 3, n)), close=c), index=idx)
    return g.clean(d)


def _ref(df, d, setup, side):
    out = {}
    for z in mr.filt(SETUPS[setup](df, k=2, storyline_on=False), d, df, True, side):
        out.setdefault(z.known_at, (z.top, z.stop))
    return out


def _same(got, want):
    if got is None or want is None:
        return got is None and want is None
    return abs(got[0] - want[0]) < 1e-9 and abs(got[1] - want[1]) < 1e-6


def test_fresh_and_qm_match_research_both_sides():
    d = _walk()
    for side in ("long", "short"):
        df = mirror(d) if side == "short" else d
        for setup, fn in (("fresh_v", mp.fresh_last), ("qm", mp.qm_last)):
            ref = _ref(df, d, setup, side)
            ts = sorted(set(range(100, len(df), 7)) | set(ref))
            bad = [t for t in ts if t >= 100 and not _same(fn(mp.bars(df.iloc[:t + 1])), ref.get(t))]
            assert not bad, (setup, side, bad[:5])


def test_ema9_matches_research():
    d = _walk(seed=9)
    ref = {s["t"]: (s["side"], s["stop"]) for s in g.setups(d, g.bias_series(d, "both"), k=2)}
    for t in sorted(set(range(60, len(d) - 1, 5)) | set(ref)):
        got = mp.ema9_last(mp.bars(d.iloc[:t + 1]))
        want = ref.get(t)
        assert (got is None and want is None) or (got[0] == want[0] and abs(got[1] - want[1]) < 1e-6), t

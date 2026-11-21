"""A320: MSNR state used by the EA filter — flip/touch rules and no look-ahead."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research"))
import ea_msnr_gold as m  # noqa: E402
import ea_design_gold as e  # noqa: E402


def _bars(closes, start="2025-01-06 00:00", freq="1h"):
    c = np.array(closes, float)
    o = np.r_[c[0], c[:-1]]
    idx = pd.date_range(start, periods=len(c), freq=freq)
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) + 0.5, "low": np.minimum(o, c) - 0.5,
                         "close": c}, index=idx)


def _walk(n=600, seed=1):
    rng = np.random.default_rng(seed)
    return _bars(3000 + np.cumsum(rng.normal(0, 4, n)))


def test_no_lookahead_state_unchanged_by_future_bars():
    h1 = _walk()
    h4 = e.resample(h1, "4h")
    full = m.msnr_state(h1, h4)
    cut = h1.iloc[:400]
    part = m.msnr_state(cut, e.resample(cut, "4h"))
    # a still-forming last 4h bar in `cut` can only ADD info later, never change earlier rows
    a, b = full.iloc[:396], part.iloc[:396]
    pd.testing.assert_frame_equal(a, b)


def test_support_below_and_resistance_above_close():
    h1 = _walk(seed=3)
    st = m.msnr_state(h1, e.resample(h1, "4h"))
    ok = st.dropna(subset=["sup"])
    assert (ok.sup <= h1.close.loc[ok.index] + 1e-9).all()
    ok = st.dropna(subset=["res"])
    assert (ok.res >= h1.close.loc[ok.index] - 1e-9).all()


def test_fresh_filter_drops_signals_at_used_levels():
    h1 = _walk(seed=5)
    st = m.msnr_state(h1, e.resample(h1, "4h"))
    at = pd.Series(e.g.atr(h1), index=h1.index)
    story = pd.Series(0.0, index=h1.index)
    t = h1.index[200:260]
    sig = [dict(t_close=x + pd.Timedelta("1h"), side=1, trig=float(h1.high.loc[x]),
                swing=float(h1.low.loc[x]), atr=5.0) for x in t]
    kept = m.apply(sig, st, story, at, {"fresh"}, h1.index)
    pos = h1.index.get_indexer([s["t_close"] - pd.Timedelta("1h") for s in kept])
    assert all(st.sup_fresh.iloc[p] == 1.0 for p in pos)
    assert len(kept) <= len(sig)


def test_target_skips_trades_without_room():
    e.SCALED, e.LADDER = False, False
    h1 = _bars([3000 + i * 0.1 for i in range(80)])
    s = dict(t_close=h1.index[10] + pd.Timedelta("1h"), side=1, trig=float(h1.high.iloc[10]) - 5,
             swing=float(h1.low.iloc[10]) - 20, atr=10.0, tp2_level=float(h1.close.iloc[10]) + 1.0)
    t = e.simulate(h1, pd.Timedelta("1h"), [s], pd.Timedelta("2h"))
    assert t.empty

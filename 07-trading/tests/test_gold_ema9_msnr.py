import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
import gold_ema9_msnr as g  # noqa: E402


def _bars(closes, start="2026-01-01", freq="h"):
    c = np.array(closes, float)
    o = np.r_[c[0], c[:-1]]
    idx = pd.date_range(start, periods=len(c), freq=freq)
    return pd.DataFrame(dict(open=o, high=np.maximum(o, c) + 1, low=np.minimum(o, c) - 1, close=c), index=idx)


def _walk(n=600, seed=1, base=3500):
    r = np.random.default_rng(seed).normal(0, 4, n).cumsum()
    return _bars(base + r)


def test_level_bias_short_above_long_below():
    d = _bars([3200, 3150, 3101, 3100, 3050])
    assert list(g.bias_series(d, "level")) == [-1, -1, -1, 1, 1]


def test_setups_have_no_lookahead():
    d = _walk()
    full = g.setups(d, g.bias_series(d, "both"))
    cut = g.setups(d.iloc[:400], g.bias_series(d.iloc[:400], "both"))
    early = [(s["t"], s["side"]) for s in full if s["t"] < 398]
    assert early == [(s["t"], s["side"]) for s in cut if s["t"] < 398]


def test_bias_blocks_wrong_side():
    d = _walk(seed=3, base=4000)                     # all above 3100: shorts only
    assert all(s["side"] == -1 for s in g.setups(d, g.bias_series(d, "level")))


def test_stop_hit_before_target_counts_as_loss():
    d = _bars([100, 100, 100, 100])
    d.loc[d.index[2], ["high", "low"]] = [130, 70]   # both hit in one bar: worst case
    sig = [dict(t=0, side=1, stop=90.0, atr=5.0, level=95.0)]
    tr = g.run(d, sig, hold=5, cost=0)
    assert tr.why.iloc[0] == "stop" and tr.R.iloc[0] == -1


def test_topstep_breach_and_pass():
    t0 = pd.Timestamp("2026-02-02 10:00")
    loss = [dict(t_in=t0 + pd.Timedelta(days=i), t_out=t0 + pd.Timedelta(days=i, hours=2), side=1, risk=10.0,
                 R=-1.0, adverse=-10.0) for i in range(10)]
    assert g.topstep(pd.DataFrame(loss), t0 - pd.Timedelta(hours=1), 400)["result"] == "fail"
    win = [dict(t_in=t0 + pd.Timedelta(days=i), t_out=t0 + pd.Timedelta(days=i, hours=2), side=1, risk=10.0,
                R=2.0, adverse=0.0) for i in range(10)]
    r = g.topstep(pd.DataFrame(win), t0 - pd.Timedelta(hours=1), 400)
    assert r["result"] == "pass"                    # 4 days x $800 = $3,200, best day 25% < 50%


def test_paper_ignores_trades_before_start_and_kill(tmp_path):
    t = pd.DataFrame([dict(t_in=pd.Timestamp("2026-11-01"), t_out=pd.Timestamp("2026-11-01 05:00"), side=-1,
                           risk=10.0, R=2.0, adverse=0.0)])
    st = g.paper(tmp_path / "p", t)
    assert st["trades"] == 0 and st["balance_usd"] == 50000
    (tmp_path / "f").mkdir()
    (tmp_path / "f" / "KILL").write_text("x")
    assert g.paper(tmp_path / "p", t, flags=tmp_path / "f")["status"] == "killed"

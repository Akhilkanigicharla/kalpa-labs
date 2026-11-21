"""21 Nov 2026 EA options in ea_mix_backtest.portfolio: weights, max positions, no opposite, Friday cut, extra cost,
min stop / lot cap, equity day stop, equity floor."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import ea_mix_backtest as eb  # noqa: E402

FL = "MSNR fresh_v long 1h"


def _fr(close=None, spread=10.0):
    idx = pd.date_range("2025-01-01", periods=400, freq="h")             # Wed 1 Jan 2025
    c = pd.Series(3000.0, index=idx) if close is None else close.reindex(idx).ffill()
    d = pd.DataFrame(dict(open=c, high=c + spread, low=c - spread, close=c), index=idx)   # ATR = 2 x spread
    agg = dict(open="first", high="max", low="min", close="last")
    return {"1h": d, "2h": d.resample("2h").agg(agg), "4h": d.resample("4h").agg(agg)}


def _t(rows):
    return pd.DataFrame([dict(t_in=pd.Timestamp(a), t_out=pd.Timestamp(b), side=sd, r=r, strategy=s)
                         for a, b, sd, r, s in rows])


def test_weights_cut_and_half():
    t = _t([("2025-01-06 03:00", "2025-01-06 05:00", 1, 1.0, "EMA9 2h"),
            ("2025-01-06 03:00", "2025-01-06 05:00", 1, 1.0, "MSNR qm long 1h")])
    p = eb.portfolio(t, _fr(), 0.01, mix_risk=0.01, weights=eb.WEIGHTS_2026_11_21)
    # EMA9 2h is cut; qm long 1h at half: $50 target, stop 1.2 x $20 = $24 -> 0.02 lot
    assert list(p.strategy) == ["MSNR qm long 1h"] and abs(p.lot.iloc[0] - 0.02) < 1e-9


def test_max_positions_and_no_opposite():
    rows = [(f"2025-01-06 0{h}:00", "2025-01-07 00:00", 1, 1.0, FL) for h in range(1, 6)]
    assert len(eb.portfolio(_t(rows), _fr(), 0.0025, max_pos=3)) == 3
    t = _t([("2025-01-06 01:00", "2025-01-07 00:00", 1, 1.0, FL),
            ("2025-01-06 02:00", "2025-01-07 00:00", -1, 1.0, "MSNR fresh_v short 2h"),
            ("2025-01-07 02:00", "2025-01-07 05:00", -1, 1.0, "MSNR fresh_v short 2h")])
    p = eb.portfolio(t, _fr(), 0.0025, no_opposite=True)
    assert list(p.side) == [1, -1] and p.t_in.iloc[1] == pd.Timestamp("2025-01-07 02:00")


def test_extra_cost_min_stop_lot_cap():
    t = _t([("2025-01-06 03:00", "2025-01-06 05:00", 1, 1.0, FL)])
    p0 = eb.portfolio(t, _fr(spread=0.1), 0.0025, mix_risk=0.01)
    p1 = eb.portfolio(t, _fr(spread=0.1), 0.0025, mix_risk=0.01, min_stop=1.5, lot_cap=0.10, extra_cost=0.30)
    assert p0.lot.iloc[0] > 0.10                                      # $0.20 stop -> 5 lots uncapped
    assert abs(p1.lot.iloc[0] - 0.10) < 1e-9 and abs(p1.risk.iloc[0] - 0.10 * 1.5 * 100) < 1e-9
    assert abs(p1.pnl.iloc[0] - (1.0 * 15.0 - 0.30 * 100 * 0.10 * 2)) < 1e-9


def test_friday_cut_closes_losers_first():
    idx = pd.date_range("2025-01-01", periods=400, freq="h")
    close = pd.Series(np.where(idx >= pd.Timestamp("2025-01-03 12:00"), 3010.0, 3000.0), index=idx)
    t = _t([("2025-01-03 10:00", "2025-01-06 10:00", 1, 1.0, FL),          # Friday 3 Jan; long wins
            ("2025-01-03 10:00", "2025-01-06 10:00", -1, 1.0, "MSNR fresh_v short 2h")])   # short loses
    p = eb.portfolio(t, _fr(close), 0.0025, mix_risk=0.01, friday_cut=0.0125)
    s = p.set_index("side")
    assert s.loc[-1, "exit"] == "friday" and s.loc[-1, "t_close"] == pd.Timestamp("2025-01-03 22:00")
    assert s.loc[-1, "pnl"] < 0 and s.loc[1, "exit"] == "rule"
    assert eb.portfolio(t, _fr(close), 0.0025, mix_risk=0.01).exit.eq("rule").all()


def _crash():
    idx = pd.date_range("2025-01-01", periods=400, freq="h")
    close = pd.Series(np.where(idx >= pd.Timestamp("2025-01-02 10:00"), 2980.0, 3000.0), index=idx)
    t = _t([("2025-01-02 08:00", "2025-01-03 08:00", 1, -1.0, "EA+MSNR 1h (EA rules)"),
            ("2025-01-02 14:00", "2025-01-02 16:00", 1, 1.0, FL),
            ("2025-01-06 14:00", "2025-01-06 16:00", 1, 1.0, FL)])
    return t, _fr(close)


def test_equity_day_stop_closes_and_blocks_rest_of_day():
    t, fr = _crash()
    p = eb.portfolio(t, fr, 0.05, day_stop_eq=0.04)                 # EA 5% risk, -1R open -> -4.95% equity
    assert p.exit.iloc[0] == "daystop" and p.t_close.iloc[0] == pd.Timestamp("2025-01-02 11:00")
    assert list(p.t_in) == [pd.Timestamp("2025-01-02 08:00"), pd.Timestamp("2025-01-06 14:00")]
    assert len(eb.portfolio(t, fr, 0.05)) == 3                      # old closed-loss stop: no MTM close


def test_equity_floor_halts_for_good():
    t, fr = _crash()
    p, mt, ck = eb.portfolio(t, fr, 0.05, eq_floor=9_600.0, curve=True)
    assert list(p.exit) == ["floor"] and ck["eq"].min() <= 9_600.0 and len(mt) > 0

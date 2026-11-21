"""A329: portfolio rules of the EA backtest (lots, cap, news, daily stop, streak)."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import ea_mix_backtest as eb  # noqa: E402


def _fr():
    idx = pd.date_range("2025-01-01", periods=400, freq="h")
    d = pd.DataFrame(dict(open=3000.0, high=3010.0, low=2990.0, close=3000.0), index=idx)   # ATR = $20
    return {"1h": d, "2h": d.resample("2h").agg(dict(open="first", high="max", low="min", close="last")),
            "4h": d.resample("4h").agg(dict(open="first", high="max", low="min", close="last"))}


def _t(rows):
    return pd.DataFrame([dict(t_in=pd.Timestamp(a), t_out=pd.Timestamp(b), side=1, r=r, strategy=s) for a, b, r, s in rows])


def test_streak_and_fixed_sizing():
    t = _t([("2025-01-06 03:00", "2025-01-06 05:00", 2.0, "MSNR fresh_v long 1h"),
            ("2025-01-06 07:00", "2025-01-06 09:00", 1.0, "MSNR fresh_v long 1h")])
    p = eb.portfolio(t, _fr(), 0.0025)
    # $25 target, stop $20 -> 0.01 lot = $20 risk; after the win target $37.5 -> still 0.01 lot ($20)
    assert list(p.lot) == [0.01, 0.01] and abs(p.pnl.iloc[0] - 40.0) < 1e-9


def test_open_risk_cap_skips():
    rows = [(f"2025-01-06 {h:02d}:00", "2025-01-08 00:00", 1.0, f"MSNR fresh_v long 1h") for h in range(1, 23)]
    p = eb.portfolio(_t(rows), _fr(), 0.0025)
    assert p.risk.sum() <= 0.03 * eb.START + 1e-9 and len(p) < len(rows)


def test_news_blackout_skips():
    t = _t([("2026-11-10 13:00", "2026-11-10 15:00", 1.0, "MSNR fresh_v long 1h")])   # CPI 13:30 UTC
    assert eb.portfolio(t, _fr(), 0.0025).empty

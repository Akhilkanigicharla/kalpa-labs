"""A323: win/loss counting, account maths and The5%ers check for the combined strategy."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import best_combo_gold as b  # noqa: E402


def _t(rs):
    t0 = pd.Timestamp("2025-01-06 08:00")
    return pd.DataFrame(dict(t_in=[t0 + pd.Timedelta(hours=3 * i) for i in range(len(rs))],
                             t_out=[t0 + pd.Timedelta(hours=3 * i + 2) for i in range(len(rs))],
                             side=1, r=rs))


def test_count_win_loss_breakeven():
    c = b.count(_t([1.0, -1.0, 0.02, 2.0, -0.5]))
    assert (c["trades"], c["wins"], c["losses"], c["breakeven"]) == (5, 2, 2, 1)


def test_account_profit_and_overlap():
    b.RISK = 0.005
    a = b.account(_t([1.0, -1.0, 2.0]))
    assert a["profit_usd"] == 100.0 and a["max_open_together"] == 1


def test_the5ers_fails_on_daily_loss():
    b.RISK = 0.02
    res = b.the5ers(_t([-1.0, -1.0, -1.0]))       # -6% in one day
    b.RISK = 0.005
    assert res["fail"] == 1.0


def test_paper_ledger_is_append_only(tmp_path, monkeypatch):
    t0 = pd.Timestamp("2026-11-23 08:00")
    fr = {"1h": pd.DataFrame(index=pd.date_range(t0, periods=200, freq="h"))}
    first = pd.DataFrame(dict(t_in=[t0], t_out=[t0 + pd.Timedelta(hours=3)], side=[1], r=[1.0]))
    monkeypatch.setattr(b, "CHOSEN", ["X"])
    monkeypatch.setattr(b, "candidates", lambda fr: {"X": lambda: first})
    b.paper(tmp_path, fr=fr, today=pd.Timestamp("2026-11-24"))
    revised = first.assign(r=[-1.0])                       # later data revision must not change the record
    monkeypatch.setattr(b, "candidates", lambda fr: {"X": lambda: revised})
    st = b.paper(tmp_path, fr=fr, today=pd.Timestamp("2026-11-25"))
    assert st["trades"] == 1 and st["wins"] == 1


def test_paper_kill(tmp_path):
    (tmp_path / "KILL").write_text("x")
    assert b.paper(tmp_path / "o", flags=tmp_path)["status"] == "killed"


def test_layer_view_sizes_after_win():
    t0 = pd.Timestamp("2026-11-23 08:00")
    led = pd.DataFrame(dict(t_in=[t0, t0 + pd.Timedelta(hours=5)], t_out=[t0 + pd.Timedelta(hours=2), t0 + pd.Timedelta(hours=7)],
                            side=[1, 1], r=[1.0, 1.0], strategy=["X", "X"]))
    v = b.layer_view(led)
    assert v["streak_sized_total_r"] == 2.5          # 1.0 + 1.5 x 1.0

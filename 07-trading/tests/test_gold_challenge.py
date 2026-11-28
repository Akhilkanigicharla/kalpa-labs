"""A306: rule engine for the paper gold challenge (Hindustan 1-Step, Greenwick 2-Step). Paper only."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(R))
spec = importlib.util.spec_from_file_location("gold_challenge", R / "gold_challenge.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

HF1, GW2 = G.RULES["HF1"], G.RULES["GW2"]


def run(rule, days):
    c = G.Challenge(rule)
    for i, (worst, close) in enumerate(days):
        c.day(f"d{i}", worst, close)
    return c


def test_daily_loss_breach_uses_days_opening_balance():
    c = run(HF1, [(3000, 3000), (-5200, -1000)])            # opened at 103,000: floor 97,850
    assert c.status == "failed" and "daily loss" in c.reason
    ok = run(HF1, [(3000, 3000), (-5100, -1000)])           # -5,100 < 5% of 103,000 (5,150)
    assert ok.status == "active"


def test_trailing_max_loss_follows_high_water_mark_but_static_does_not():
    path = [(4000, 4000)] * 2 + [(-4000, -4000)] * 2 + [(-2500, -2500)]   # peak 108k, now 97.5k < 98k
    assert run(HF1, path).status == "failed" and "max loss" in run(HF1, path).reason
    gw = run(GW2, [(7000, 7000)] * 2 + [(-7000, -7000)] * 3)   # 193k: under a trailing 194k, over static 180k
    assert gw.status == "active"
    assert run(dict(GW2, trailing=True), [(7000, 7000)] * 2 + [(-7000, -7000)] * 3).status == "failed"
    assert run(GW2, [(-9000, -9000), (-9000, -9000), (-2500, -2500)]).status == "failed"


def test_pass_needs_min_days_flat_and_consistency():
    c = G.Challenge(HF1)
    for i in range(4):
        c.day(f"d{i}", 0, 2500)                             # 110,000 after 4 days: under min 5 days
    assert c.status == "active" and "min 5 days" in c.note
    c.day("d4", 0, 2500)                                    # 112,500, best day 2,500 = 20%: allowed
    assert c.status == "passed" and c.phase == 1
    open_pos = G.Challenge(HF1)
    for i in range(6):
        open_pos.day(f"d{i}", 0, 2000, flat=False)
    assert open_pos.status == "active" and "position open" in open_pos.note


def test_consistency_rule_blocks_pass_until_no_day_is_over_20pct():
    c = G.Challenge(HF1)
    for i, p in enumerate([9000, 300, 300, 300, 300]):     # +10.2k, best day 9k = 88%
        c.day(f"d{i}", 0, p)
    assert c.status == "active" and "consistency" in c.note
    for i in range(40):                                      # keep earning smaller days
        c.day(f"e{i}", 0, 1500)
        if c.status == "passed":
            break
    assert c.status == "passed"
    best = max(c.history_pnl)
    assert best <= 0.20 * (c.equity - c.base) + 1e-6


def test_greenwick_two_phases_reset_balance():
    c = G.Challenge(GW2)
    c.day("a", 0, 16_000)
    assert c.phase == 1 and c.equity == 200_000 and c.status == "active"
    c.day("b", 0, 10_000)
    assert c.status == "passed"
    assert run(GW2, [(0, 15_000)]).phase == 0            # 7.5% < 8%


def test_after_fail_nothing_changes():
    c = run(HF1, [(-6000, -6000)])
    eq = c.equity
    c.day("later", 0, 50_000)
    assert c.status == "failed" and c.equity == eq


def bars(n=320, drift=0.004, seed=1):
    rng = np.random.default_rng(seed)
    c = 7000 * np.cumprod(1 + drift + rng.normal(0, 0.006, n))
    idx = pd.bdate_range("2025-09-01", periods=n)
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.002, "low": np.minimum(o, c) * 0.998, "close": c}, index=idx)


def test_daily_pnl_one_position_and_no_trades_before_start():
    d = bars()
    start = d.index[260]
    rows = G.daily_pnl(d, start, HF1, risk=0.01)
    assert rows and rows[0]["date"] == str(start.date())
    assert all(r["worst"] <= r["close"] + 1e-9 for r in rows)
    assert sum(r["pos"] != 0 for r in rows) > 0               # steady uptrend: the trend rule goes long


def test_paper_writes_phone_status_and_respects_kill(tmp_path):
    d = bars()
    flags = tmp_path / "flags"
    flags.mkdir()
    st = G.paper(tmp_path / "out", d, flags=flags, start=str(d.index[260].date()))
    assert set(st["rules"]) == {"HF1", "GW2"}
    txt = (tmp_path / "out" / "latest.txt").read_text()
    assert "Hindustan" in txt and "Greenwick" in txt and "PAPER ONLY" in txt
    assert max(len(line) for line in txt.splitlines()) <= 80     # phone-readable lines
    saved = json.loads((tmp_path / "out" / "state.json").read_text())
    assert saved["start"] == str(d.index[260].date())
    (flags / "KILL").write_text("")
    k = G.paper(tmp_path / "out", d, flags=flags)
    assert k["status"] == "killed"
    assert "KILL" in (tmp_path / "out" / "latest.txt").read_text()


def test_start_date_is_kept_between_runs(tmp_path):
    d = bars()
    G.paper(tmp_path, d, start=str(d.index[300].date()))
    st = G.paper(tmp_path, d)                                # no start given: reuse the saved one
    assert st["start"] == str(d.index[300].date())


def test_bad_data_is_rejected(tmp_path):
    st = G.paper(tmp_path, bars().iloc[:0])
    assert st["status"] == "no-data"

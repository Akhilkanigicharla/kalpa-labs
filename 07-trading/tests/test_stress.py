"""A168: honest stress test of video ideas on Indian data (paper only).

Synthetic prices only (no market data). Positive control = planted trend regimes,
negative control = pure random walk. Run: python -m pytest -q tests/test_stress.py
"""
import numpy as np
import pandas as pd
import pytest

from src import backtest, data, paper, stress


def _pair(seed=1, regime_days=0, drift=0.0, n=2520):
    a = data.synthetic_prices(n, seed=seed, regime_days=regime_days, regime_drift=drift)["close"]
    b = data.synthetic_prices(n, seed=seed + 100, mu=0.07, sigma=0.12)["close"]
    return a, b


def test_pair_all_in_a_equals_a_with_no_switch_costs():
    a, b = _pair()
    res = stress.run_pair(a, b, pd.Series(1.0, index=a.index))
    r = a.pct_change().fillna(0.0)
    assert np.allclose(res.gross.iloc[2:], r.iloc[2:])
    assert res.trades <= 1 and res.total_cost < 0.003  # only the first entry is charged


def test_pair_switch_costs_both_legs_and_no_lookahead():
    a, b = _pair()
    w = pd.Series(0.0, index=a.index); w.iloc[500:] = 1.0            # switch B -> A once
    res = stress.run_pair(a, b, w)
    assert res.held.iloc[500] == 0.0 and res.held.iloc[501] == 1.0   # applied from the next bar
    one_way = sum(backtest.costs.delivery_side_rates())
    assert res.cost.iloc[500] == pytest.approx(one_way, rel=0.2)     # sell B + buy A, charged once
    with pytest.raises(ValueError):
        stress.run_pair(a, b, w, delay=0)


def test_regime_uses_only_past_data():
    a, _ = _pair()
    full = stress.regime(a, trend=100)
    cut = stress.regime(a.iloc[:1500], trend=100)
    assert full.iloc[:1500].equals(cut)                                # adding future bars changes nothing


def test_funnel_stages_shrink_and_holdout_is_last_two_years():
    a, b = _pair(seed=3, regime_days=120, drift=0.30)
    rep = stress.funnel(a, b, holdout_years=2)
    s = rep["stages"]
    assert s["variants"] >= s["enough_trades"] >= s["profitable"] >= s["sharpe_ok"]
    assert rep["holdout_start"] == a.index[-2 * 252]
    assert rep["train_end"] < rep["holdout_start"]
    assert 0.0 <= rep["pbo"] <= 1.0 and rep["n_trials"] == s["variants"]


def test_rotation_beats_random_on_planted_trend_not_on_noise():
    a, b = _pair(seed=5, regime_days=150, drift=0.35)
    planted = stress.funnel(a, b, holdout_years=2, random_draws=200)
    a2, b2 = _pair(seed=6)
    noise = stress.funnel(a2, b2, holdout_years=2, random_draws=200)
    assert planted["best_vs_random_pct"] >= 80
    assert noise["best_vs_random_pct"] < planted["best_vs_random_pct"]


def test_report_is_honest_markdown():
    a, b = _pair(seed=3, regime_days=120, drift=0.30)
    md = stress.report_md(stress.funnel(a, b, holdout_years=2), "NIFTYBEES", "GOLDBEES", "synthetic")
    for must in ("Paper only", "hold-out", "random", "PBO", "Not advice", "## Verdict"):
        assert must.lower() in md.lower()


def test_noise_never_passes_the_verdict():
    a, b = _pair(seed=11)
    ok, fails = stress.verdict(stress.funnel(a, b, holdout_years=2, random_draws=200))
    assert not ok and fails


@pytest.mark.parametrize("strategy", ["ma_filter", "tsmom", "regime_filter"])
def test_backtest_and_paper_trade_on_the_same_days(strategy):
    bars = data.synthetic_prices(1200, seed=9, regime_days=90, regime_drift=0.3)
    close = bars["close"]
    w = paper.weights(strategy, close).reindex(close.index).fillna(0.0).clip(0, 1)
    bt_days = set(close.index[(w.diff().abs() > paper.MIN_CHANGE)][-60:].date)
    run = paper.dry_run(bars, strategy, days=60, pot=10_000_000.0)
    paper_days = {s.signal_date for s in run.signals}
    window = set(close.index[-61:-1].date)
    assert paper_days == bt_days & window


def test_data_problem_blocks_pass_and_is_shown():
    a, b = _pair(seed=3, regime_days=120, drift=0.30)
    a = a.copy(); a.iloc[1000:] *= 10                                   # an unadjusted 1:10 split
    rep = stress.funnel(a, b, holdout_years=2)
    rep["jumps"] = {"NIFTYBEES": stress._jumps(a)}
    ok, fails = stress.verdict(rep)
    assert not ok and "DATA PROBLEM" in fails[0]
    assert "one-day move" in stress.report_md(rep, "NIFTYBEES", "GOLDBEES", "synthetic")


def test_repair_drops_wrong_scale_split_days_but_keeps_real_moves():
    df = data.synthetic_prices(300, seed=2)
    df.iloc[100:102, :4] = df.iloc[100:102, :4] / 10                       # 2 days stored at 1/10 scale
    df.iloc[150, :4] = 0.0                                                  # zero price row
    df.iloc[200:, :4] = df.iloc[200:, :4] * 0.5                             # a real, lasting halving
    fixed, dropped = data.repair_spikes(df)
    assert len(dropped) == 3 and len(fixed) == 297
    assert any("price <= 0" in d for d in dropped)
    assert fixed["close"].pct_change().abs().max() > 0.4                    # the lasting move stays

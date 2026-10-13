"""b7 Trading Lab tests. Synthetic data only; no network, no real prices.

Run: cd 07-trading && python -m pytest -q tests
"""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from src import backtest, costs, data, gate, metrics, strategies, trials


# ---------- costs (Q7.3) ----------

def test_delivery_contract_note_example():
    """Rs 1,00,000 buy + Rs 1,00,000 sell of one NSE stock, delivery, zero brokerage.

    Worked by hand from the published Zerodha charge list (checked 2026-10-13):
      STT 0.1% x 2,00,000 = 200.00; NSE 0.00307% x 2,00,000 = 6.14;
      SEBI Rs10/cr = 0.20; stamp 0.015% x 1,00,000 = 15.00;
      GST 18% x (6.14 + 0.20) = 1.14; DP 15.34  -> total 237.82
    """
    c = costs.delivery(100_000, 100_000).rounded()
    assert c["stt"] == 200.00 and c["exchange"] == 6.14 and c["sebi"] == 0.20
    assert c["stamp"] == 15.00 and abs(c["gst"] - 1.14) < 0.01 and c["dp"] == 15.34
    assert abs(c["total"] - 237.82) < 1.0  # PLAN check: within Rs 1


def test_intraday_futures_options_basics():
    i = costs.intraday(50_000, 50_000)
    assert i.brokerage == pytest.approx(30.0)                     # 0.03% = 15 per side, under the Rs 20 cap
    assert i.stt == pytest.approx(12.5)             # 0.025% on sell only
    big = costs.intraday(10_00_000, 10_00_000)
    assert big.brokerage == 40.0                    # capped at Rs 20 per order
    f = costs.futures(10_00_000, 10_00_000)
    assert f.stt == pytest.approx(500.0)            # 0.05% sell (Apr 2026 rate)
    o = costs.options(10_000, 12_000)
    assert o.stt == pytest.approx(18.0)             # 0.15% of sell premium
    assert o.brokerage == 40.0


def test_every_rate_has_source_and_is_fresh():
    for name, (val, note, src, checked) in costs.RATES.items():
        assert val > 0 and note and src.startswith("https://"), name
        date.fromisoformat(checked)
    assert costs.stale_rates(date(2026, 10, 13)) == []
    assert costs.stale_rates(date(2027, 3, 1))  # becomes stale after 90 days -> re-check


def test_delivery_side_rates_round_trip_about_0_22_pct():
    b, s = costs.delivery_side_rates()
    assert 0.0021 < b + s < 0.0023


# ---------- data (Q7.2) ----------

def test_synthetic_is_clean_and_reproducible():
    a, b = data.synthetic_prices(500, seed=3), data.synthetic_prices(500, seed=3)
    pd.testing.assert_frame_equal(a, b)
    assert data.validate(a) == []


def test_validate_catches_bad_data():
    df = data.synthetic_prices(300, seed=1)
    bad = df.copy()
    bad.iloc[10, bad.columns.get_loc("close")] = -1
    assert any("<= 0" in p for p in data.validate(bad))
    split = df.copy()
    split.iloc[150:, :4] = split.iloc[150:, :4] / 10      # unadjusted 1:10 split
    assert any("jump" in p for p in data.validate(split))
    gap = df.drop(df.index[100:110])
    assert any("gap" in p for p in data.validate(gap))
    dup = pd.concat([df.iloc[:5], df.iloc[4:6]])
    assert any("duplicate" in p for p in data.validate(dup))


def test_get_daily_caches_and_never_refetches(tmp_path):
    calls = []

    def fake(sym, start, end):
        calls.append(sym)
        return data.synthetic_prices(400, seed=5).rename(columns=str.capitalize)

    a = data.get_daily("TCS", cache_dir=tmp_path, fetcher=fake)
    b = data.get_daily("TCS", cache_dir=tmp_path, fetcher=fake)
    assert calls == ["TCS.NS"] and len(a) == len(b) == 400
    assert (tmp_path / "TCS.NS.parquet").exists()


def test_get_daily_uses_fallback_and_strict_mode(tmp_path):
    def broken(*_):
        raise ConnectionError("yahoo down")

    def fallback(*_):
        df = data.synthetic_prices(300, seed=2)
        df.iloc[200:, :4] /= 10
        return df

    with pytest.raises(data.DataError, match="jump"):
        data.get_daily("INFY", cache_dir=tmp_path, fetcher=broken, fallback=fallback)
    df = data.get_daily("INFY", cache_dir=tmp_path, fetcher=broken, fallback=fallback, strict=False)
    assert len(df) == 300


def test_symbols():
    assert data.nse_symbol("reliance") == "RELIANCE.NS"
    assert data.nse_symbol("^NSEI") == "^NSEI"
    assert data.nse_symbol("SBIN.BO") == "SBIN.BO"


def test_data_folder_is_git_ignored():
    import subprocess
    out = subprocess.run(["git", "check-ignore", "data/x.parquet"], capture_output=True, text=True)
    assert out.returncode == 0


# ---------- strategies + backtest ----------

def test_no_lookahead_signal_ignores_future():
    close = data.synthetic_prices(600, seed=4)["close"]
    for name in strategies.REGISTRY:
        p = strategies.param_grid(name)[0]
        full = strategies.weights(name, close, **p)
        cut = strategies.weights(name, close.iloc[:400], **p)
        pd.testing.assert_series_equal(full.iloc[:400], cut, check_names=False)


def test_grids_have_even_size_for_unbiased_pbo():
    for name in strategies.REGISTRY:
        n = len(strategies.param_grid(name))
        assert n >= 4 and n % 2 == 0, name


def test_backtest_refuses_lookahead_and_zero_cost():
    close = data.synthetic_prices(300, seed=1)["close"]
    w = strategies.sma_cross(close)
    with pytest.raises(ValueError):
        backtest.run(close, w, delay=0)
    with pytest.raises(ValueError):
        backtest.run(close, w, cost_mult=0)


def test_buy_and_hold_matches_price_and_costs_are_charged():
    close = data.synthetic_prices(500, seed=9)["close"]
    bh = backtest.buy_and_hold(close)
    gross = (1 + bh.gross).prod()
    assert gross == pytest.approx(close.iloc[-1] / close.iloc[0], rel=1e-9)
    res = backtest.run(close, strategies.sma_cross(close, 5, 50))
    assert res.total_cost > 0 and (1 + res.returns).prod() < (1 + res.gross).prod()


def test_vol_target_caps_and_bands():
    close = data.synthetic_prices(800, seed=6, sigma=0.35)["close"]
    w = strategies.tsmom_vt(close, 126, 0.10)
    assert w.max() <= 1.0 and w.min() >= 0.0
    assert w.diff().abs().gt(0).sum() < 0.25 * len(w)   # band keeps rebalancing rare


# ---------- metrics ----------

def test_sharpe_annualised_at_252():
    r = pd.Series([0.01, -0.005, 0.002, 0.004] * 63)
    assert metrics.sharpe(r) == pytest.approx(r.mean() / r.std() * np.sqrt(252))


def test_psr_and_dsr_behave():
    rng = np.random.default_rng(0)
    good = rng.normal(0.001, 0.01, 2000)
    noise = rng.normal(0.0, 0.01, 2000)
    assert metrics.psr(good) > 0.99
    assert metrics.psr(noise) < 0.95
    assert metrics.dsr(good, 1) == pytest.approx(metrics.psr(good))
    assert metrics.dsr(good, 1000) < metrics.dsr(good, 10) < metrics.psr(good)


def test_phi_inv_accuracy():
    for p, z in [(0.5, 0.0), (0.975, 1.959963984540054), (0.001, -3.090232306167813)]:
        assert metrics._phi_inv(p) == pytest.approx(z, abs=1e-9)


def test_pbo_low_for_real_skill_high_for_noise():
    rng = np.random.default_rng(1)
    noise = rng.normal(0, 0.01, (1600, 8))
    skill = noise.copy()
    skill[:, 0] += 0.002                               # one config is truly better
    assert metrics.pbo_cscv(skill) < 0.1
    assert 0.25 < metrics.pbo_cscv(noise) < 0.75      # pure noise: about a coin flip


# ---------- trials registry (Q7.5) + gate (Q7.4) ----------

def test_gate_refuses_unlogged_run(tmp_path):
    close = data.synthetic_prices(2000, seed=1)["close"]
    reg = tmp_path / "trials.csv"
    with pytest.raises(trials.TrialError):
        gate.evaluate(close, "sma_cross", None, registry=reg)
    with pytest.raises(trials.TrialError):
        gate.evaluate(close, "sma_cross", "T0099", registry=reg)


def test_gate_refuses_mismatched_trial(tmp_path):
    close = data.synthetic_prices(2000, seed=1)["close"]
    reg = tmp_path / "trials.csv"
    tid = trials.log_trial("H1", "tsmom", {}, "syn", 4, path=reg)
    with pytest.raises(gate.GateError):
        gate.evaluate(close, "sma_cross", tid, registry=reg)
    tid2 = trials.log_trial("H1", "sma_cross", {}, "syn", 3, path=reg)
    with pytest.raises(gate.GateError, match="n_configs"):
        gate.evaluate(close, "sma_cross", tid2, registry=reg)


def test_a8_sma_crossover_is_rejected(tmp_path):
    """PLAN Q7.4 regression: the a8 SMA crossover must be rejected on a random walk."""
    reg = tmp_path / "trials.csv"
    for seed in (1, 2, 3):
        close = data.synthetic_prices(5040, seed=seed)["close"]
        tid = trials.log_trial("H0-a8-sma", "sma_cross", strategies.REGISTRY["sma_cross"][1],
                               f"synthetic random walk seed {seed}", 6, path=reg)
        v = gate.evaluate(close, "sma_cross", tid, registry=reg)
        assert v.verdict == "rejected", v.summary()
        assert v.thresholds_status == "pending CEO approval"
    rows = trials._read(reg)
    assert [r["verdict"] for r in rows] == ["rejected"] * 3
    with pytest.raises(trials.TrialError, match="already"):
        trials.record_result(rows[0]["trial_id"], {"verdict": "paper"}, path=reg)


def test_gate_can_pass_a_planted_trend(tmp_path):
    """Positive control: the gate is not a rubber stamp for 'reject'."""
    reg = tmp_path / "trials.csv"
    close = data.synthetic_prices(5040, seed=2, regime_days=250, regime_drift=0.35)["close"]
    tid = trials.log_trial("H1-tsmom-vt", "tsmom_vt", {}, "synthetic planted trend", 4, path=reg)
    v = gate.evaluate(close, "tsmom_vt", tid, registry=reg)
    assert v.verdict == "paper", v.summary()
    assert v.numbers["oos_sharpe"] > v.numbers["bh_sharpe"]


def test_dsr_counts_every_config_ever_logged(tmp_path):
    reg = tmp_path / "trials.csv"
    trials.log_trial("H2", "tsmom", {}, "a", 4, path=reg)
    trials.log_trial("H2", "tsmom", {}, "b", 4, path=reg)
    trials.log_trial("H3", "tsmom", {}, "c", 4, path=reg)
    assert trials.configs_tried("H2", path=reg) == 8

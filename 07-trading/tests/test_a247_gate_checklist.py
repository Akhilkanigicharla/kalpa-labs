"""A247: DaviddTech validation checklist gaps in the gate (paper only).
(1) multi-asset basket, (2) no-repaint, (3) delay >= 1 look-ahead guard, (4) frozen config hash.
Synthetic data only; the real ETF basket run is `python3 -m src.gate` (reports/a247-basket-*.json)."""
import numpy as np
import pandas as pd
import pytest

from src import backtest, causal, data, gate, paper, strategies, trials


def _trend(seed):
    return data.synthetic_prices(5040, seed=seed, regime_days=250, regime_drift=0.35)["close"]


def _walk(seed):
    return data.synthetic_prices(5040, seed=seed)["close"]


# Deliberately broken rules the gate must catch.
def pivot_repaint(close, k=5):
    """Buys swing lows found with a CENTRED window: the classic repainting indicator. The pivot
    only appears k bars later, but is drawn (and traded) on the past bar."""
    low = close.rolling(2 * k + 1, center=True).min()
    return (close == low).astype(float).rolling(k, min_periods=1).max()


def peek_tomorrow(close, k=1):
    """Look-ahead cheat: long when tomorrow's close is higher (shift(-k))."""
    return (close.shift(-k) > close).astype(float)


def full_history_zscore(close, window=200):
    """Subtle look-ahead: normalises with the WHOLE series' mean and std."""
    z = (close - close.mean()) / close.std()
    return (z < window / 1000).astype(float)


@pytest.fixture
def cheats(monkeypatch):
    monkeypatch.setitem(strategies.REGISTRY, "pivot_repaint", (pivot_repaint, {"k": [3, 5, 7, 9]}))
    monkeypatch.setitem(strategies.REGISTRY, "peek_tomorrow", (peek_tomorrow, {"k": [1, 2, 3, 4]}))
    monkeypatch.setitem(strategies.REGISTRY, "full_zscore", (full_history_zscore, {"window": [100, 200, 300, 400]}))


# ---------------------------------------------------------------- (2) no-repaint
def test_every_registered_rule_never_repaints_or_looks_ahead():
    close = data.synthetic_prices(1500, seed=3)["close"]
    for name in strategies.REGISTRY:
        r = causal.check_strategy(name, close)
        assert r["ok"], (name, r)


def test_truncation_test_catches_a_repainting_pivot():
    close = _walk(1).iloc[:1500]
    assert causal.repaint_bars(pivot_repaint, close)
    assert causal.repaint_bars(peek_tomorrow, close)
    assert causal.repaint_bars(full_history_zscore, close)       # changes as new bars move the mean
    assert causal.repaint_bars(strategies.tsmom, close) == []


def test_future_scramble_catches_look_ahead_but_not_honest_rules():
    close = _walk(2).iloc[:1500]
    assert causal.lookahead_bars(peek_tomorrow, close)
    assert causal.lookahead_bars(full_history_zscore, close)
    assert causal.lookahead_bars(lambda c: strategies.turtle(c, 20, 10), close) == []
    assert causal.lookahead_bars(strategies.markov_regime, close) == []


def test_gate_rejects_repainting_and_look_ahead_rules_even_with_huge_sharpe(tmp_path, cheats):
    reg = tmp_path / "trials.csv"
    close = _walk(1)
    basket = {f"R{s}": _walk(s) for s in (1, 2, 3, 4)}
    for name in ("pivot_repaint", "peek_tomorrow", "full_zscore"):
        tid = trials.log_trial(f"H-cheat-{name}", name, strategies.REGISTRY[name][1], "synthetic", 4, path=reg)
        v = gate.evaluate(close, name, tid, registry=reg, basket=basket)
        assert v.verdict == "rejected", v.summary()
        assert v.checks["7 no repaint, no look-ahead, delay >= 1"] is False
        assert not v.causal["ok"]
    peek = trials._read(reg)[1]
    assert float(peek["oos_sharpe"]) > 3          # the cheat "looks" brilliant; check 7 still says no


# ---------------------------------------------------------------- (3) delay >= 1 guard
@pytest.mark.parametrize("bad", [0, -1, 0.5, 1.0, True, None, "1"])
def test_backtest_and_gate_refuse_delay_below_one_or_not_whole(bad):
    close = _walk(1).iloc[:1200]
    w = strategies.tsmom(close, 63)
    with pytest.raises(ValueError, match="delay"):
        backtest.run(close, w, delay=bad)
    with pytest.raises(gate.GateError, match="delay"):
        gate.walk_forward(close, "tsmom", delay=bad)


def test_delay_one_is_next_bar_and_delay_two_is_later():
    idx = pd.bdate_range("2024-01-01", periods=6)
    close = pd.Series([100, 101, 102, 103, 104, 105.0], index=idx)
    w = pd.Series([0, 1, 1, 1, 1, 1.0], index=idx)          # signal at bar 1's close
    assert backtest.run(close, w, delay=1).held.tolist() == [0, 0, 1, 1, 1, 1]
    assert backtest.run(close, w, delay=np.int64(2)).held.tolist() == [0, 0, 0, 1, 1, 1]


def test_gate_refuses_a_stress_delay_that_adds_no_bar(tmp_path, monkeypatch):
    reg = tmp_path / "trials.csv"
    tid = trials.log_trial("H", "tsmom", {}, "syn", 4, path=reg)
    monkeypatch.setitem(gate.THRESHOLDS, "stress_delay", 1)
    with pytest.raises(gate.GateError, match="stress_delay"):
        gate.evaluate(_walk(1), "tsmom", tid, registry=reg)


# ---------------------------------------------------------------- (1) multi-asset basket
def test_basket_is_the_four_etfs_and_most_means_more_than_half():
    assert gate.BASKET == ("NIFTYBEES", "BANKBEES", "GOLDBEES", "JUNIORBEES")
    assert [gate.basket_pass_min(n) for n in (1, 2, 3, 4, 5)] == [1, 2, 2, 3, 3]


def test_multi_asset_passes_3_of_4_planted_trends_and_fails_random_walks():
    good = gate.multi_asset({f"S{s}": _trend(s) for s in (2, 3, 4, 5)}, "tsmom_vt")
    assert good["passed"] == 3 and good["need"] == 3 and good["ok"]
    assert good["assets"]["S3"]["passed"] is False            # one weak asset is allowed
    bad = gate.multi_asset({f"R{s}": _walk(s) for s in (1, 2, 3, 4)}, "sma_cross")
    assert bad["passed"] < 3 and not bad["ok"]


def test_short_history_counts_as_a_fail_not_a_skip():
    r = gate.multi_asset({"A": _trend(2), "B": _trend(4), "SHORT": _trend(5).iloc[:500]}, "tsmom_vt")
    assert r["assets"]["SHORT"]["passed"] is False and "need at least" in r["assets"]["SHORT"]["why"]
    assert r["passed"] == 2 and r["ok"]                        # 2 of 3 is still "most"


def test_gate_needs_the_basket_to_say_paper(tmp_path):
    """Positive control: a planted trend passes all 8 only WITH a basket; without one, check 8 fails."""
    reg = tmp_path / "trials.csv"
    close = _trend(2)
    tid = trials.log_trial("H1-tsmom-vt", "tsmom_vt", {}, "synthetic planted trend", 4, path=reg)
    v = gate.evaluate(close, "tsmom_vt", tid, registry=reg,
                      basket={f"S{s}": _trend(s) for s in (2, 3, 4, 5)})
    assert v.verdict == "paper", v.summary()
    assert trials.get_trial(tid, path=reg)["basket"] == "3/4"
    tid2 = trials.log_trial("H1-tsmom-vt", "tsmom_vt", {}, "synthetic planted trend", 4, path=reg)
    v2 = gate.evaluate(close, "tsmom_vt", tid2, registry=reg)
    assert v2.verdict == "rejected" and v2.checks["8 passes on most of the ETF basket"] is False


def test_gate_rejects_when_the_basket_fails(tmp_path):
    reg = tmp_path / "trials.csv"
    tid = trials.log_trial("H1", "tsmom_vt", {}, "syn", 4, path=reg)
    v = gate.evaluate(_trend(2), "tsmom_vt", tid, registry=reg,
                      basket={f"R{s}": _walk(s) for s in (1, 3, 4, 5)})
    assert v.verdict == "rejected" and v.numbers["basket_passed"] < 3


def test_load_basket_reads_cache_and_repairs_split_rows(tmp_path):
    fake = data.synthetic_prices(1500, seed=7)
    fake.iloc[700:702] = fake.iloc[700:702] / 10              # a wrong-scale split block
    calls = []

    def fetch(sym, start, end):
        calls.append(sym)
        return fake

    for s in ("AAA", "BBB"):
        data.get_daily(s, cache_dir=tmp_path, fetcher=fetch, strict=False)
    import src.data as d
    orig = d.DATA_DIR
    d.DATA_DIR = tmp_path
    try:
        b = gate.load_basket(("AAA", "BBB"), start="2000-01-01")
    finally:
        d.DATA_DIR = orig
    assert calls == ["AAA.NS", "BBB.NS"] and set(b) == {"AAA", "BBB"}
    assert len(b["AAA"]) == 1498 and data.validate(pd.DataFrame(
        {"open": b["AAA"], "high": b["AAA"], "low": b["AAA"], "close": b["AAA"], "volume": 0.0})) == []


# ---------------------------------------------------------------- (4) frozen config hash
def _paper_trial(reg):
    tid = trials.log_trial("H-frz", "tsmom", strategies.REGISTRY["tsmom"][1], "syn", 4, path=reg)
    trials.record_result(tid, {"verdict": "paper"}, path=reg)
    return tid


def test_freeze_writes_hash_before_paper_and_paper_refuses_without_it(tmp_path):
    reg = tmp_path / "trials.csv"
    tid = _paper_trial(reg)
    bars = data.synthetic_prices(600, seed=4)
    with pytest.raises(trials.TrialError, match="not frozen"):
        paper.dry_run(bars, "tsmom", days=5, symbol="SYNTH", trial=tid, registry=reg, lookback=63)
    h = trials.freeze(tid, "tsmom", {"lookback": 63}, "synth", path=reg)
    row = trials.get_trial(tid, path=reg)
    assert row["config_hash"] == h and len(h) == 64 and row["frozen_ist"]
    assert '"lookback":63' in row["frozen_config"] and '"symbol":"SYNTH"' in row["frozen_config"]
    run = paper.dry_run(bars, "tsmom", days=5, symbol="SYNTH", trial=tid, registry=reg, lookback=63)
    assert run.pot > 0
    assert trials.freeze(tid, "tsmom", {"lookback": 63}, "SYNTH", path=reg) == h   # same config: idempotent


def test_frozen_trial_refuses_changed_params_symbol_or_refreeze(tmp_path):
    reg = tmp_path / "trials.csv"
    tid = _paper_trial(reg)
    trials.freeze(tid, "tsmom", {"lookback": 63}, "SYNTH", path=reg)
    bars = data.synthetic_prices(600, seed=4)
    with pytest.raises(trials.TrialError, match="changed"):
        paper.dry_run(bars, "tsmom", days=5, symbol="SYNTH", trial=tid, registry=reg, lookback=126)
    with pytest.raises(trials.TrialError, match="changed"):
        trials.verify_frozen(tid, "tsmom", {"lookback": 63}, "OTHER", path=reg)
    with pytest.raises(trials.TrialError, match="already frozen"):
        trials.freeze(tid, "tsmom", {"lookback": 126}, "SYNTH", path=reg)


def test_editing_the_rule_code_breaks_the_freeze(tmp_path, monkeypatch):
    reg = tmp_path / "trials.csv"
    tid = trials.log_trial("H-frz", "tsmom_vt", {}, "syn", 4, path=reg)
    trials.record_result(tid, {"verdict": "paper"}, path=reg)
    trials.freeze(tid, "tsmom_vt", {"lookback": 252, "target": 0.1}, "NIFTYBEES", path=reg)
    real = trials._code_of
    monkeypatch.setattr(trials, "_code_of", lambda fn, seen=None: real(fn, seen) + "# edited")
    with pytest.raises(trials.TrialError, match="code changed"):
        trials.verify_frozen(tid, "tsmom_vt", {"lookback": 252, "target": 0.1}, "NIFTYBEES", path=reg)


def test_hash_covers_called_helpers_and_only_paper_verdicts_freeze(tmp_path):
    code = trials._code_of(strategies.tsmom_vt)
    assert "def tsmom(" in code and "def vol_target(" in code
    reg = tmp_path / "trials.csv"
    tid = trials.log_trial("H", "tsmom", {}, "syn", 4, path=reg)
    with pytest.raises(trials.TrialError, match="only 'paper'"):
        trials.freeze(tid, "tsmom", {"lookback": 63}, "X", path=reg)
    trials.record_result(tid, {"verdict": "rejected"}, path=reg)
    with pytest.raises(trials.TrialError, match="only 'paper'"):
        trials.freeze(tid, "tsmom", {"lookback": 63}, "X", path=reg)
    with pytest.raises(trials.TrialError, match="unknown strategy"):
        trials.config_hash("nope", {}, "X")


def test_plain_dry_run_still_needs_no_trial(tmp_path):
    run = paper.dry_run(data.synthetic_prices(600, seed=4), "sma_cross", days=5, symbol="SYNTH")
    assert run.pot > 0

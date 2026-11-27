import numpy as np
import pandas as pd
import pytest

from src import kronos_score as ks


def test_prob_up_smoothed_and_ignores_nan():
    assert ks.prob_up(np.array([11, 12, 9, np.nan]), 10) == pytest.approx(2.5 / 4)
    assert 0 < ks.prob_up(np.array([1.0, 2.0]), 10) < 0.5
    assert 0.5 < ks.prob_up(np.array([11.0, 12.0]), 10) < 1
    with pytest.raises(ValueError):
        ks.prob_up(np.array([np.nan]), 10)


def test_brier_and_log_loss_known_values():
    y = np.array([1.0, 0.0])
    assert ks.brier(np.array([0.5, 0.5]), y) == pytest.approx(0.25)
    assert ks.log_loss(np.array([0.5, 0.5]), y) == pytest.approx(np.log(2))
    assert ks.brier(np.array([1.0, 0.0]), y) == 0
    # a confident miss is clipped, finite, and much worse than 0.5
    assert np.isfinite(ks.log_loss(np.array([0.0, 1.0]), y))
    assert ks.log_loss(np.array([0.0, 1.0]), y) > 5


@pytest.mark.parametrize("p,y", [([], []), ([0.5], [1, 0]), ([1.2], [1]), ([0.5], [2])])
def test_bad_inputs_rejected(p, y):
    with pytest.raises(ValueError):
        ks.brier(np.array(p, float), np.array(y, float))


def test_strategy_costs_on_switch_only():
    r = ks.strategy(np.array([0.6, 0.6, 0.4, 0.6]), np.array([0.01, 0.02, 0.03, 0.04]), 0.001)
    assert r == pytest.approx([0.009, 0.02, -0.001, 0.039])


def test_report_no_skill_model_does_not_pass():
    rng = np.random.default_rng(1)
    ret = rng.normal(0.0005, 0.01, 400)
    y = (ret > 0).astype(float)
    p = np.clip(rng.normal(0.5, 0.15, 400), 0.01, 0.99)  # noise, unrelated to y
    out = ks.report("noise", p, y, ret, base_rate=0.53, cost_side=0.0006)
    assert out["bars"] == 400
    assert out["brier"]["kronos"] > out["brier"]["random_walk"]
    assert not out["beats_baselines"] and not out["passes"]


def test_report_skilful_model_beats_baselines():
    rng = np.random.default_rng(2)
    ret = rng.normal(0, 0.01, 400)
    y = (ret > 0).astype(float)
    p = np.where(y == 1, 0.7, 0.3)
    out = ks.report("oracle-ish", p, y, ret, base_rate=0.5, cost_side=0.0006)
    assert out["beats_baselines"] and out["direction_accuracy"] == 1.0
    assert out["return_after_costs"] > out["return_hold"] and out["passes"]
    assert out["random_signals_beat_bot"] == 0.0


def test_report_length_mismatch():
    with pytest.raises(ValueError):
        ks.report("x", np.array([0.5]), np.array([1.0, 0.0]), np.array([0.1, 0.1]), 0.5, 0.0)


def test_frame_from_drops_missing():
    d = pd.DataFrame({"p_up": [0.6, 0.4, np.nan], "up": [1, 0, 1], "ret": [0.01, np.nan, 0.02]})
    p, y, r = ks.frame_from(d)
    assert list(p) == [0.6] and list(y) == [1.0] and list(r) == [0.01]

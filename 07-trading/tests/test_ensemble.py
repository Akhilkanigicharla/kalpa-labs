"""Darwinian ensemble (method from chrisworsey55/atlas-gic, MIT). Synthetic data only, paper only."""
import numpy as np
import pandas as pd
import pytest

from src import data, ensemble as E, strategies
from src.gate import Verdict

MEMBERS = ["tsmom_vt", "ma_filter_vt", "markov_regime", "sma_cross"]
PARAMS = {"tsmom_vt": {"lookback": 63}, "ma_filter_vt": {"window": 50}, "sma_cross": {"fast": 5, "slow": 50}}
PASS_ALL = {m: "paper" for m in MEMBERS}


@pytest.fixture(scope="module")
def close():
    return data.synthetic_prices(900, seed=11, regime_days=60, regime_drift=0.4)["close"]


def test_darwin_step_rule_and_bounds():
    w = {"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0, "e": 1.0, "f": 1.0, "g": 1.0, "h": 1.0}
    s = {k: i for i, k in enumerate(w)}                     # a worst ... h best
    new = E.darwin_step(w, s)
    assert new["a"] == new["b"] == pytest.approx(0.95)     # bottom quartile (8 // 4 = 2)
    assert new["g"] == new["h"] == pytest.approx(1.05)
    assert all(new[k] == 1.0 for k in "cdef")
    for _ in range(500):                                    # saturate both ends
        new = E.darwin_step(new, s)
    assert new["h"] == E.W_MAX and new["a"] == E.W_MIN
    # equal scores or a single scored member: nothing moves
    assert E.darwin_step({"a": 1.0, "b": 1.0}, {"a": 0.5, "b": 0.5}) == {"a": 1.0, "b": 1.0}
    assert E.darwin_step({"a": 1.0, "b": 1.0}, {"a": 0.5, "b": float("nan")}) == {"a": 1.0, "b": 1.0}


def test_combine_is_weighted_average_in_bounds():
    assert E.combine({"a": 1.0, "b": 0.0}, {"a": 2.5, "b": 0.3}) == pytest.approx(2.5 / 2.8)
    assert E.combine({"a": 1.0}, {"a": 0.0}) == 0.0          # nobody eligible -> cash
    assert 0.0 <= E.combine({"a": 7.0, "b": -3.0}, {"a": 1.0, "b": 1.0}) <= 1.0


def test_weights_stay_in_bounds_and_target_in_unit_interval(close):
    w, tgt = E.ensemble_path(close, MEMBERS, PASS_ALL, params=PARAMS, window=63)
    live = w[MEMBERS]
    assert ((live >= E.W_MIN - 1e-12) & (live <= E.W_MAX + 1e-12)).all().all()
    assert tgt.between(0.0, 1.0).all()
    assert (live.iloc[-1] != 1.0).any()                     # the rule actually moved something
    assert not live.iloc[:63].ne(1.0).any().any()           # no score before the window fills


def test_failed_gate_members_get_zero(close):
    from src.gate import THRESHOLDS_STATUS
    verdicts = {"tsmom_vt": Verdict("t1", "paper", {}, {}), "ma_filter_vt": "paper",
                "markov_regime": Verdict("t2", "rejected", {}, {}, thresholds_status=THRESHOLDS_STATUS)}
    # sma_cross has no verdict at all
    w, tgt = E.ensemble_path(close, MEMBERS, verdicts, params=PARAMS, window=63)
    assert (w["markov_regime"] == 0).all() and (w["sma_cross"] == 0).all()
    assert (w[["tsmom_vt", "ma_filter_vt"]] >= E.W_MIN).all().all()
    # the combined target never uses a failed member: equals the 2-member ensemble
    _, tgt2 = E.ensemble_path(close, ["tsmom_vt", "ma_filter_vt"], verdicts, params=PARAMS, window=63)
    pd.testing.assert_series_equal(tgt, tgt2)
    # nobody passes -> flat
    w0, t0 = E.ensemble_path(close, MEMBERS, {m: "rejected" for m in MEMBERS}, params=PARAMS)
    assert (w0 == 0).all().all() and (t0 == 0).all()


def test_no_lookahead_future_bars_do_not_change_past(close):
    w_full, t_full = E.ensemble_path(close, MEMBERS, PASS_ALL, params=PARAMS, window=63)
    for cut in (300, 555, 800):
        w_cut, t_cut = E.ensemble_path(close.iloc[:cut], MEMBERS, PASS_ALL, params=PARAMS, window=63)
        pd.testing.assert_frame_equal(w_cut, w_full.iloc[:cut])
        pd.testing.assert_series_equal(t_cut, t_full.iloc[:cut])
    # shocking the future leaves the past untouched too
    shocked = close.copy()
    shocked.iloc[600:] *= 3.0
    w_s, t_s = E.ensemble_path(shocked, MEMBERS, PASS_ALL, params=PARAMS, window=63)
    pd.testing.assert_frame_equal(w_s.iloc[:600], w_full.iloc[:600])
    pd.testing.assert_series_equal(t_s.iloc[:600], t_full.iloc[:600])


def test_paper_run_goes_through_live_guard(tmp_path):
    b = data.synthetic_prices(500, seed=4, regime_days=60, regime_drift=0.5)
    out, flags = tmp_path / "o", tmp_path / "f"
    for t in b.index[-15:]:
        res = E.run_paper_ensemble(b, track="A", members=MEMBERS[:2], verdicts=PASS_ALL, params=PARAMS,
                                   capital=5_000, out=out, flags=flags, asof=t, window=63)
    assert 0.0 <= res["weight"] <= 1.0
    led = pd.read_csv(out / "ledger-A.csv")
    assert set(led["strategy"]) == {"ensemble"} and "filled" in set(led["status"])
    assert (led.loc[led.side == "buy", "value_pct_capital"] <= 100.01).all()  # Live Guard max position (Track A: 100%, C66)
    assert "ensemble" not in strategies.REGISTRY                               # registration is temporary
    with pytest.raises(ValueError):
        E.run_paper_ensemble(b, track="A", members=MEMBERS, verdicts=PASS_ALL, capital=5_000,
                             out=out, flags=flags, mode="live")


def test_kill_switch_blocks_ensemble_buys(tmp_path):
    b = data.synthetic_prices(500, seed=4, regime_days=60, regime_drift=0.5)
    out, flags = tmp_path / "o", tmp_path / "f"
    flags.mkdir()
    (flags / "KILL").write_text("stop")
    for t in b.index[-10:]:
        E.run_paper_ensemble(b, track="A", members=MEMBERS[:2], verdicts=PASS_ALL, params=PARAMS,
                             capital=5_000, out=out, flags=flags, asof=t, window=63)
    led = pd.read_csv(out / "ledger-A.csv")
    buys = led.loc[led.side == "buy"]
    assert len(buys) and set(buys["status"]) == {"blocked"} and buys["reasons"].str.contains("kill_switch").all()


def test_verdicts_from_trials(tmp_path):
    p = tmp_path / "trials.csv"
    p.write_text("trial_id,strategy,verdict\nT1,tsmom_vt,rejected\nT2,tsmom_vt,paper\nT3,sma_cross,\n")
    v = E.verdicts_from_trials(p)
    assert v == {"tsmom_vt": "paper"}
    assert E.eligible(MEMBERS, v) == ["tsmom_vt"]

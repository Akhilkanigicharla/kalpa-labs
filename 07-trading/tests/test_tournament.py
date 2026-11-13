"""A279 tournament: 25 agents, master allocation, no-trade band, no look-ahead. Synthetic data only."""
import numpy as np
import pandas as pd

from src import data, tournament as T


def _px(n=900, seed=0):
    cols = {m: data.synthetic_prices(n, seed=seed + i, regime_days=120, regime_drift=0.3)["close"]
            for i, m in enumerate(T.MARKETS)}
    return pd.DataFrame(cols)


def test_25_unique_agents_on_known_markets():
    assert len(T.AGENTS) == 25
    assert len({a.name for a in T.AGENTS}) == 25
    assert {a.market for a in T.AGENTS} <= set(T.MARKETS)


def test_signals_are_long_only_and_bounded():
    sig = T.signals(_px())
    assert sig.shape[1] == 25
    assert sig.min().min() >= 0 and sig.max().max() <= 1


def test_no_look_ahead_in_signals_scores_and_weights():
    px = _px()
    cut = 600
    fut = px.copy()
    fut.iloc[cut:] *= np.linspace(1, 3, len(px) - cut)[:, None]  # change only the future
    a_sig, b_sig = T.signals(px), T.signals(fut)
    pd.testing.assert_frame_equal(a_sig.iloc[:cut], b_sig.iloc[:cut])
    a_sc = T.score(T.agent_returns(px, a_sig)).iloc[:cut]
    b_sc = T.score(T.agent_returns(fut, b_sig)).iloc[:cut]
    pd.testing.assert_frame_equal(a_sc, b_sc)


def test_allocate_caps_agent_and_market_and_benches_losers():
    sc = pd.Series({a.name: (5.0 if a.market == "NIFTYBEES" else -1.0) for a in T.AGENTS})
    w = T.allocate(sc)
    mk = pd.Series({a.name: a.market for a in T.AGENTS})
    assert (w <= T.CAP_AGENT + 1e-12).all()
    assert w[mk == "NIFTYBEES"].sum() <= T.CAP_MARKET + 1e-12
    assert (w[mk != "NIFTYBEES"] == 0).all()          # losing agents get no money
    assert T.allocate(sc * 0 - 1).sum() == 0          # all losing -> all cash


def test_band_skips_tiny_trades_but_always_allows_full_exit():
    idx = pd.RangeIndex(4)
    exp = pd.DataFrame({"A": [0.20, 0.22, 0.30, 0.0]}, index=idx)
    out = T.banded(exp, 0.05)["A"].tolist()
    assert out == [0.20, 0.20, 0.30, 0.0]


def test_master_runs_and_charges_are_positive():
    px = _px()
    sig = T.signals(px)
    rets = T.agent_returns(px, sig)
    acct, w = T.run_master(px, sig, rets)
    assert np.isfinite(acct["ret"]).all()
    assert (acct["cost"] >= 0).all() and acct["cost"].sum() > 0
    assert (w.iloc[:T.LOOKBACK] == 0).all().all()     # no money before the warm-up ends
    assert acct["invested"].max() <= 1 + 1e-9


def test_paper_run_writes_state_and_kill_blocks_new_buys(tmp_path, monkeypatch):
    import json
    px = _px()
    monkeypatch.setattr(T, "load_prices", lambda *a, **k: px)
    out, flags = tmp_path / "t", tmp_path / "flags"
    flags.mkdir()
    (flags / "KILL").write_text("")
    T.paper(out, flags)
    st = json.loads((out / "state.json").read_text())
    assert st["paper_only"] and st["kill"]
    assert all(v == 0 for v in st["positions_rs"].values())   # nothing held + KILL = no buys
    assert len(st["agents"]) == 25

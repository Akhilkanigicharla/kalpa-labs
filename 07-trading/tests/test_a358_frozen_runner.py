"""A358: the runner trades only a frozen trial config (or an explicit, labelled learning track),
and a one-day ETF price that disagrees with its index (bad tick) is caught."""
import json
from datetime import date, timedelta

import pandas as pd
import pytest

from src import data, trials
from src.livetrade import runner


def _registry(tmp_path, strategy="tsmom", verdict="paper"):
    reg = tmp_path / "trials.csv"
    tid = trials.log_trial("H-a358", strategy, [{"lookback": 63}], "synth", 1, path=reg)
    trials.record_result(tid, {"verdict": verdict}, path=reg)
    return reg, tid


def _frozen(tmp_path, symbol="NIFTYBEES", params=None):
    reg, tid = _registry(tmp_path)
    trials.freeze(tid, "tsmom", params or {"lookback": 63}, symbol, path=reg)
    return reg, tid


def _common(tmp_path, reg):
    return ["--track", "A", "--synthetic", "--strategy", "tsmom", "--out", str(tmp_path / "o"),
            "--flags", str(tmp_path / "f"), "--registry", str(reg)]


def test_paper_refuses_an_unfrozen_config(tmp_path, capsys):
    reg, _ = _registry(tmp_path)
    assert runner.main(_common(tmp_path, reg), env={}) == 2
    assert "frozen" in capsys.readouterr().err
    assert not (tmp_path / "o" / "state-A.json").exists()


def test_paper_refuses_a_logged_but_unfrozen_trial(tmp_path, capsys):
    reg, tid = _registry(tmp_path)
    assert runner.main([*_common(tmp_path, reg), "--trial", tid], env={}) == 2
    assert "not frozen" in capsys.readouterr().err


def test_frozen_trial_trades_the_frozen_params_and_never_re_picks(tmp_path, monkeypatch):
    reg, tid = _frozen(tmp_path, params={"lookback": 126})
    monkeypatch.setattr(runner, "pick_params", lambda *a, **k: pytest.fail("re-picked params"))
    assert runner.main([*_common(tmp_path, reg), "--trial", tid], env={}) == 0
    st = json.loads((tmp_path / "o" / "state-A.json").read_text())
    assert st["params"] == {"lookback": 126} and st["trial"] == tid
    assert f"trial {tid} (frozen)" in (tmp_path / "o" / "summary-A.txt").read_text()


def test_frozen_trial_refuses_another_strategy_or_symbol(tmp_path, capsys):
    reg, tid = _frozen(tmp_path)
    args = [*_common(tmp_path, reg), "--trial", tid]
    assert runner.main([*args, "--symbol", "GOLDBEES"], env={}) == 2
    assert runner.main([a if a != "tsmom" else "tsmom_vt" for a in args], env={}) == 2
    err = capsys.readouterr().err
    assert "symbol" in err and "strategy" in err


def test_learning_track_is_labelled_and_cannot_mix_with_a_trial_state(tmp_path):
    reg, tid = _frozen(tmp_path)
    assert runner.main([*_common(tmp_path, reg), "--learning"], env={}) == 0
    text = (tmp_path / "o" / "summary-A.txt").read_text()
    assert "LEARNING" in text and "never counts towards live" in text
    with pytest.raises(SystemExit, match="started for"):
        runner.main([*_common(tmp_path, reg), "--trial", tid], env={})


def test_live_refuses_without_trial_and_counts_only_that_trials_paper_days(tmp_path):
    reg, tid = _frozen(tmp_path)
    flags, out = tmp_path / "f", tmp_path / "o"
    flags.mkdir()
    (flags / "GO").write_text("go")
    (flags / "GATE_PASS_A").write_text("T9999\n")
    st = runner._new_state(5_000.0)
    st["paper_days"] = [str(date(2026, 1, 1) + timedelta(days=i)) for i in range(90)]
    st["trial"] = None                                  # 90 days, but all on the learning track
    b = runner.live_blockers("A", st, {"LIVE_TRADING": "YES"}, flags, trial=tid)
    assert any("no paper days" in x and tid in x for x in b)
    assert any("GATE_PASS_A" in x and tid in x for x in b)
    st["trial"] = tid
    (flags / "GATE_PASS_A").write_text(f"T9999\n{tid}\n")
    b = runner.live_blockers("A", st, {"LIVE_TRADING": "YES"}, flags, trial=tid)
    assert not any("paper days" in x or "GATE_PASS" in x for x in b)
    assert any("frozen trial" in x for x in runner.live_blockers("A", st, {}, flags, trial=None))
    (out).mkdir()
    (out / "state-A.json").write_text(json.dumps(st))
    assert runner.main(["--track", "A", "--mode", "live", "--synthetic", "--out", str(out), "--flags",
                        str(flags), "--registry", str(reg)], env={"LIVE_TRADING": "YES"}) == 2


# ---------------------------------------------------------------- bad ticks (NIFTYBEES 6-7 Oct 2010)
OCT_2010 = pd.DataFrame({          # Yahoo closes fetched 28 Nov 2026: NIFTYBEES.NS and ^NSEI
    "etf": [60.980, 60.200, 60.695, 60.150, 61.500, 61.980, 62.100, 52.500, 61.620, 61.300, 61.900],
    "idx": [6035.65, 6029.50, 5991.30, 6029.95, 6143.40, 6159.45, 6145.80, 6186.45, 6120.30, 6103.45, 6135.85],
}, index=pd.bdate_range("2010-09-27", periods=11))


def _bars(s):
    return pd.DataFrame({"open": s, "high": s, "low": s, "close": s, "volume": 1000.0})


def test_index_mismatch_finds_the_oct_2010_bad_tick_not_a_split():
    bad = data.index_mismatch(_bars(OCT_2010["etf"]), _bars(OCT_2010["idx"]))
    assert bad == [pd.Timestamp("2010-10-06")]           # one wrong close; the +17% next day is the snap back
    clean, dropped = data.drop_index_mismatch(_bars(OCT_2010["etf"]), _bars(OCT_2010["idx"]))
    assert len(clean) == 10 and "06 Oct 2010" in dropped[0]
    assert clean["close"].pct_change().abs().max() < 0.03


def test_index_mismatch_keeps_real_moves_that_the_index_also_made():
    etf, idx = OCT_2010["etf"].copy(), OCT_2010["idx"].copy()
    etf.iloc[7], idx.iloc[7] = 52.5, 6186.45 * 52.5 / 62.1    # index fell the same 15%: real crash
    assert data.index_mismatch(_bars(etf), _bars(idx)) == []


def test_runner_refuses_to_trade_on_a_price_that_disagrees_with_its_index(tmp_path):
    etf = _bars(OCT_2010["etf"].iloc[:8])                  # decision day = 6 Oct 2010, the bad close
    idx = _bars(OCT_2010["idx"].iloc[:8])
    with pytest.raises(ValueError, match="disagrees with the signal"):
        runner.run_paper(etf, track="A", strategy="hold", capital=5_000.0, out=tmp_path / "o",
                         flags=tmp_path / "f", signal_bars=idx, params={}, trial=None)
    assert not (tmp_path / "o" / "state-A.json").exists()

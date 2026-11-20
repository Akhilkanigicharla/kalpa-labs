import numpy as np
import pandas as pd

from src import msnr


def frame(rows):
    idx = pd.bdate_range("2024-01-01", periods=len(rows))
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)


def walk(n=600, seed=0, vol=0.012):
    rng = np.random.default_rng(seed)
    c = 100 * np.cumprod(1 + rng.normal(0.0003, vol, n))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, vol / 3, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, vol / 2, n)))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, vol / 2, n)))
    return frame(list(zip(o, h, lo, c)))


def test_a_and_v_levels_use_closes_not_wicks():
    rows = [(100, 103, 99, 102),     # green, close 102
            (102, 109, 98, 101),     # red  -> A level at 102 (not the 109 wick)
            (101, 101, 95, 99),      # red, close 99
            (99, 104, 90, 103)]      # green -> V level at 99 (not the 90 wick)
    lv = msnr.levels(frame(rows))
    assert [(x.kind, x.price, x.known_at) for x in lv] == [("A", 102.0, 1), ("V", 99.0, 3)]


def test_doji_forms_no_level():
    rows = [(100, 101, 99, 101), (101, 102, 100, 101), (101, 102, 99, 100)]
    assert msnr.levels(frame(rows)) == []


def test_key_levels_are_known_only_k_bars_later_and_ignore_the_future():
    df = walk()
    early = [(x.origin, x.known_at) for x in msnr.levels(df.iloc[:400], k=5)]
    full = [(x.origin, x.known_at) for x in msnr.levels(df, k=5) if x.known_at < 400 and x.origin + 5 < 400]
    assert early == full
    assert all(kn >= o + 5 for o, kn in full)


def test_fresh_unfresh_and_flip():
    lv = msnr.Level(known_at=0, price=100.0, kind="V", origin=0)
    rows = [(101, 102, 100.5, 101),
            (101, 101.5, 99.5, 100.8),   # wick touches, close holds -> unfresh
            (100.8, 101, 98, 98.5),      # close below -> flips to resistance, fresh again (SBR)
            (98.5, 100.2, 98, 99)]       # wick into it, close below -> unfresh resistance
    ev = msnr.track(frame(rows), lv)
    assert ev == [(0, "support", "fresh"), (1, "support", "unfresh"), (2, "resistance", "fresh"),
                  (3, "resistance", "unfresh")]


def test_storyline_never_uses_an_unfinished_week():
    df = walk(400, seed=3)
    s_full = msnr.storyline(df, k=2)
    s_cut = msnr.storyline(df.iloc[:250], k=2)
    # every day that falls in a week finished inside the cut must agree
    wk = df.index.to_period("W-FRI")
    finished = wk[:250][wk[:250] != wk[249]]
    n = len(finished)
    assert (s_full.iloc[:n].values == s_cut.iloc[:n].values).all()


def test_qm_zone_sits_at_the_v_level_with_stop_under_the_head():
    flat = [(100 + (i % 2) * 0.2, 101, 99.5, 100.2 - (i % 2) * 0.2) for i in range(20)]
    rows = flat + [
        (100, 100.5, 97.5, 98),       # red, close 98
        (98, 101, 97.8, 100.5),       # green -> V at 98
        (100.5, 104, 100, 103.5),     # green, close 103.5
        (103.5, 104, 101, 101.5),     # red -> A at 103.5
        (101.5, 102, 95, 95.5),       # red close below V 98 -> breakdown, head low 95
        (95.5, 99, 95.2, 98.8),       # green
        (98.8, 106, 98.5, 105)]       # green close above A 103.5 -> QM confirmed
    rows += [(105, 106, 104, 105.2)] * 5
    z = msnr.qm(frame(rows), k=0, storyline_on=False)
    mine = [x for x in z if x.top == 98.0]
    assert mine and mine[0].bottom == 95.0 and mine[0].stop < 95.0 and mine[0].known_at == 26


def test_setups_produce_zones_known_in_order_and_below_price():
    df = walk(800, seed=5)
    for name, fn in msnr.SETUPS.items():
        zs = fn(df, k=2, storyline_on=False)
        assert all(z.stop < z.bottom <= z.top for z in zs), name
        c = df.close.values
        assert all(z.top <= c[z.known_at] + 1e-9 for z in zs), name


def test_setups_ignore_the_future():
    df = walk(700, seed=7)
    for name, fn in msnr.SETUPS.items():
        early = [(z.known_at, round(z.top, 6)) for z in fn(df.iloc[:500], k=2, storyline_on=False)]
        full = [(z.known_at, round(z.top, 6)) for z in fn(df, k=2, storyline_on=False) if z.known_at < 500]
        assert set(early) <= set(full), name


def test_research_has_a_placebo_and_a_verdict():
    frames = {m: walk(1200, seed=i) for i, m in enumerate(["X", "Y"])}
    frames = {m: f.set_axis(pd.bdate_range("2014-01-01", periods=len(f))) for m, f in frames.items()}
    res = msnr.research(frames, split="2018-06-01", placebo_seeds=1)
    for s in msnr.SETUPS:
        assert res[s]["verdict"] in ("PASS", "FAIL")
        assert "placebo_test" in res[s] and len(res[s]["all_configs_in_sample"]) == 4


def test_paper_runs_only_passing_setups_and_kill_stops_new_entries(tmp_path):
    import json
    rep = tmp_path / "reports"
    rep.mkdir()
    (rep / "msnr-2026-01-01.json").write_text(json.dumps({
        "qm": {"config": {"k": 2, "storyline_on": False}, "verdict": "PASS"},
        "eq_sweep": {"config": {"k": 2, "storyline_on": False}, "verdict": "FAIL"}}))
    df = walk(900, seed=11).set_axis(pd.bdate_range("2020-01-01", periods=900))
    frames = {m: df for m in msnr.MARKETS[:1]}
    out = tmp_path / "paper"
    msg = msnr.paper(out, report_dir=rep, frames=frames, today="2020-06-01")
    assert "setups: qm" in msg and "eq_sweep" not in msg.split("setups:")[1].split(")")[0]
    led = pd.read_csv(out / "ledger.csv") if (out / "ledger.csv").stat().st_size > 1 else pd.DataFrame()
    assert led.empty or (pd.to_datetime(led.entry_date) > "2020-06-01").all()
    flags = tmp_path / "flags"
    flags.mkdir()
    (flags / "KILL").write_text("")
    msnr.paper(out, report_dir=rep, frames=frames, flags=flags, today="2021-01-01")
    st = json.loads((out / "state.json").read_text())
    assert st["start"] == "2020-06-01" and st["kill"] == "2021-01-01"
    led = pd.read_csv(out / "ledger.csv") if (out / "ledger.csv").stat().st_size > 1 else pd.DataFrame()
    assert led.empty or (pd.to_datetime(led.entry_date) <= "2021-01-01").all()

"""Q7.6 tear-sheet tests. Synthetic data only; no network."""
from pathlib import Path

import pandas as pd
import pytest

from src import data, tearsheet


def test_rows_include_buy_and_hold_and_each_strategy():
    close = data.synthetic_prices(1500, seed=3)["close"]
    rows = tearsheet.rows(close, ["tsmom", "sma_cross"])
    names = [r["name"] for r in rows]
    assert names[0] == "Buy and hold"
    assert any(n.startswith("tsmom") for n in names) and any(n.startswith("sma_cross") for n in names)
    for r in rows:
        assert set(r) >= {"name", "cagr", "sharpe", "max_dd", "trades", "cost", "equity"}
        assert r["max_dd"] <= 0
        assert len(r["equity"]) == len(close)


def test_html_is_self_contained_and_labelled(tmp_path: Path):
    close = data.synthetic_prices(1500, seed=4)["close"]
    html = tearsheet.render("SYNTH", close, tearsheet.rows(close, ["tsmom"]), source="synthetic")
    assert html.startswith("<!doctype html>")
    assert "<svg" in html and "polyline" in html
    assert "Paper only" in html and "not advice" in html
    assert "SYNTHETIC" in html                                 # never mistaken for real data
    assert "http://" not in html and "https://" not in html    # no external requests
    assert "--l7" in html and "prefers-color-scheme: dark" in html   # Kalpa tokens, light + dark


def test_cli_writes_report_offline(tmp_path: Path):
    code = tearsheet.main(["--synthetic", "--out", str(tmp_path), "--strategies", "tsmom,ma_filter"])
    assert code == 0
    files = list(tmp_path.glob("*.html"))
    assert len(files) == 1 and "Buy and hold" in files[0].read_text()


def test_failed_fetch_falls_back_to_marked_synthetic(tmp_path: Path, monkeypatch):
    def boom(*a, **k):
        raise data.DataError("network down")
    monkeypatch.setattr(data, "get_daily", boom)
    code = tearsheet.main(["--symbol", "^NSEI", "--out", str(tmp_path), "--cache", str(tmp_path / "c")])
    assert code == 0
    html = next(tmp_path.glob("*.html")).read_text()
    assert "SYNTHETIC" in html and "network down" in html


def test_unknown_strategy_is_an_error(tmp_path: Path):
    with pytest.raises(SystemExit):
        tearsheet.main(["--synthetic", "--out", str(tmp_path), "--strategies", "magic"])

"""A33 / F-17: daily budget + anomaly alerts. Synthetic usage_daily rows only.

Run: cd 06-finops && python -m pytest -q tests/test_alerts.py
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alerts import alerts  # noqa: E402

TODAY = date(2026, 10, 27)


def rows(series, feature="chat"):
    """series: list of rupees per day ending at TODAY."""
    n = len(series)
    return [{"day": (TODAY - timedelta(days=n - 1 - i)).isoformat(), "feature": feature,
             "customer_id_hash": None, "cost_paise": int(r * 100)} for i, r in enumerate(series)]


def test_spike_fires_anomaly():
    data = rows([100, 110, 95, 105, 98, 102, 107, 99, 101, 104, 96, 103, 100, 900])
    found = alerts.check(data, today=TODAY)
    kinds = {(a.kind, a.scope) for a in found}
    assert ("anomaly", "total") in kinds
    assert ("anomaly", "feature:chat") in kinds


def test_steady_usage_is_quiet():
    data = rows([100, 110, 95, 105, 98, 102, 107, 99, 101, 104, 96, 103, 100, 108])
    assert alerts.check(data, today=TODAY) == []


def test_budget_fires_without_history():
    found = alerts.check(rows([600]), today=TODAY, budget_paise=50000)
    assert [(a.kind, a.paise) for a in found] == [("budget", 60000)]


def test_short_history_gives_no_anomaly():
    assert alerts.check(rows([10, 10, 10, 500]), today=TODAY) == []


def test_flat_zero_history_then_spend_is_anomaly():
    data = rows([0] * 10 + [300])
    assert any(a.kind == "anomaly" for a in alerts.check(data, today=TODAY))


def test_small_absolute_change_ignored():
    # Rs 1 -> Rs 4 is 4x but below the Rs 50 floor: no noise for tiny tenants
    data = rows([1] * 10 + [4])
    assert alerts.check(data, today=TODAY) == []


def test_message_in_rupees_and_no_raw_ids():
    data = rows([100] * 10 + [900])
    data[-1]["customer_id_hash"] = "c_0123456789abcdef"
    text = alerts.format_message(alerts.check(data, today=TODAY, budget_paise=50000), TODAY)
    assert "₹900.00" in text and "2026-10-27" in text
    assert "budget" in text.lower()


def test_csv_loader(tmp_path):
    p = tmp_path / "u.csv"
    p.write_text("day,feature,customer_id_hash,cost_paise\n2026-10-27,chat,,1500\n2026-10-27,,,500\n")
    got = alerts.load_csv(p)
    assert sum(r["cost_paise"] for r in got) == 2000


def test_send_dry_run_without_webhook(monkeypatch, capsys):
    monkeypatch.delenv("LP_SLACK_WEBHOOK", raising=False)
    assert alerts.send("hello") == "dry-run"
    assert "hello" in capsys.readouterr().out


def test_send_rejects_non_slack_url(monkeypatch):
    monkeypatch.setenv("LP_SLACK_WEBHOOK", "http://evil.example/x")
    with pytest.raises(ValueError):
        alerts.send("hello")


def test_cli_exit_code(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("LP_SLACK_WEBHOOK", raising=False)
    p = tmp_path / "u.csv"
    lines = ["day,feature,customer_id_hash,cost_paise"]
    lines += [f"{(TODAY - timedelta(days=13 - i)).isoformat()},chat,,{10000 if i < 13 else 90000}" for i in range(14)]
    p.write_text("\n".join(lines) + "\n")
    assert alerts.main([str(p), "--today", TODAY.isoformat()]) == 1
    assert "spend spike" in capsys.readouterr().out.lower()

"""deploy/dhan-cloud/main.py: refuses unless every rule holds; with every rule holding it trades both legs through Dhan."""
import importlib.util
import json
from datetime import date, datetime
from pathlib import Path

import pytest

from src.livetrade import broker as brk, runner
from src.livetrade.guard import IST
from tests.test_dhan import CLIENT, TOKEN, FakeDhan, _bars

MAIN = Path(__file__).resolve().parents[1] / "deploy" / "dhan-cloud" / "main.py"


def load_main(tmp_path, monkeypatch, files: dict):
    monkeypatch.setenv("KALPA_WORK_DIR", str(tmp_path / "work"))
    spec = importlib.util.spec_from_file_location("dhan_cloud_main", MAIN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "fetch", lambda url: files.get(url.rsplit("/paper/", 1)[1]))
    return m


def paper(days: int) -> bytes:
    return json.dumps({**runner._new_state(5000.0), "paper_days": [f"d{i}" for i in range(days)]}).encode()


GOOD_ENV = {"LIVE_TRADING": "YES", "KALPA_GO": "go", "KALPA_GATE_PASS": "yes",
            "DHAN_CLIENT_ID": CLIENT, "DHAN_ACCESS_TOKEN": TOKEN}


def test_refuses_without_paper_records(tmp_path, monkeypatch):
    m = load_main(tmp_path, monkeypatch, {})
    assert m.main(GOOD_ENV) == 2


@pytest.mark.parametrize("drop", ["LIVE_TRADING", "KALPA_GO", "KALPA_GATE_PASS", "DHAN_ACCESS_TOKEN"])
def test_each_missing_rule_refuses_before_any_order(tmp_path, monkeypatch, drop):
    files = {"track-A/state-A.json": paper(90), "track-A-gold/state-A.json": paper(90)}
    m = load_main(tmp_path, monkeypatch, files)
    env = {k: v for k, v in GOOD_ENV.items() if k != drop}
    sent = []
    monkeypatch.setattr(brk.DhanAdapter, "_urllib", lambda self, *a: sent.append(a) or (500, {}))
    assert m.main(env) in (2, 3) and not [s for s in sent if s[0] == "POST"]


def test_too_few_paper_days_refuses(tmp_path, monkeypatch):
    m = load_main(tmp_path, monkeypatch, {"track-A/state-A.json": paper(10), "track-A-gold/state-A.json": paper(10)})
    assert m.main(GOOD_ENV) == 2


def test_phone_kill_switch_blocks_live(tmp_path, monkeypatch):
    files = {"track-A/state-A.json": paper(90), "track-A-gold/state-A.json": paper(90), "track-A/flags/KILL": b""}
    m = load_main(tmp_path, monkeypatch, files)
    assert m.main(GOOD_ENV) == 2


def test_all_rules_hold_trades_both_legs_through_dhan(tmp_path, monkeypatch):
    files = {"track-A/state-A.json": paper(90), "track-A-gold/state-A.json": paper(90)}
    m = load_main(tmp_path, monkeypatch, files)
    fake = FakeDhan(); fake.holdings = []; fake.cash = 10_000.0
    orig = brk.DhanAdapter.__init__

    def init(self, env=None, go_file=None, **kw):
        orig(self, env=env, go_file=go_file, http=fake, quote_fn=lambda s: 287.0 if s == "NIFTYBEES" else 112.7,
             sleep=lambda s: None, today=date(2026, 11, 16))
    monkeypatch.setattr(brk.DhanAdapter, "__init__", init)
    nb, gb = _bars(start=287.0 / 2.46), _bars(start=112.7 / 2.46)
    monkeypatch.setattr(runner, "_load_bars", lambda a: nb if (a.symbol or "NIFTYBEES") == "NIFTYBEES" else gb)
    monkeypatch.setattr(runner, "datetime", type("D", (datetime,), {"now": staticmethod(lambda tz=None: datetime(2026, 11, 16, 9, 20, tzinfo=IST))}))
    from src import data
    monkeypatch.setattr(data, "get_daily", lambda *a, **k: nb)
    assert m.main(GOOD_ENV) == 0
    bought = {o["securityId"]: o["quantity"] for o in fake.orders.values() if o["transactionType"] == "BUY"}
    assert set(bought) == {"10576", "14428"}                                  # NIFTYBEES and GOLDBEES
    spent = sum(o["quantity"] * o["averageTradedPrice"] for o in fake.orders.values())
    assert spent <= 10_000.0                                                  # never above the Rs 10,000 plan


def test_token_found_under_dhan_cloud_style_names_and_never_printed(tmp_path, monkeypatch, capsys):
    m = load_main(tmp_path, monkeypatch, {})
    env = m.resolve_keys({"access_token": TOKEN, "CLIENT_ID": CLIENT})
    assert (env["DHAN_ACCESS_TOKEN"], env["DHAN_CLIENT_ID"]) == (TOKEN, CLIENT)
    env = m.resolve_keys({"KALPA_TOKEN_VAR": "MyTok", "MyTok": "x1", "DHAN_ACCESS_TOKEN": "x2"})
    assert env["DHAN_ACCESS_TOKEN"] == "x1"
    m.main({"access_token": TOKEN})
    assert TOKEN not in capsys.readouterr().out

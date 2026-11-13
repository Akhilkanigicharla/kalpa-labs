from datetime import date, timedelta
from pathlib import Path

from src.live import DryRunBroker, Guard, alert, private_chat, trial_passed
from src.risk import RiskBook

D = date(2026, 11, 9)
HEAD = "trial_id,logged_ist,hypothesis_id,strategy,params,data,n_configs,is_sharpe,oos_sharpe,bh_sharpe,psr,dsr,pbo,oos_trades,stress_sharpe,verdict\n"


class RealishBroker(DryRunBroker):
    """Pretends to be a real broker so we can test the live switch without a network."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "zerodha-test"


def trials(tmp_path, verdict="pass"):
    p = tmp_path / "trials.csv"
    p.write_text(HEAD + f"T9,2026-11-09,H1,sma,{{}},nifty,4,1,1,0.5,0.97,0.96,0.1,40,0.8,{verdict}\n")
    return p


def guard(tmp_path, broker=None, env=None, verdict="pass"):
    b = broker or DryRunBroker(prices={"NIFTYBEES": 100.0, "GOLDBEES": 50.0}, cash_inr=5000)
    return Guard(broker=b, trial_id="T9", book=RiskBook(pot=5000), env=env or {"KL_LIVE_CAPITAL": "5000"},
                 trials_path=trials(tmp_path, verdict), root=tmp_path, universe=("NIFTYBEES", "GOLDBEES"))


def test_trial_gate(tmp_path):
    assert trial_passed("T9", trials(tmp_path, "pass"))
    assert not trial_passed("T9", trials(tmp_path, "fail"))
    assert not trial_passed("", trials(tmp_path))
    assert not trial_passed("T9", tmp_path / "missing.csv")


def test_dry_run_buys_within_risk(tmp_path):
    g = guard(tmp_path)
    ids = g.run_once({"NIFTYBEES": (5, 95.0)}, D)   # 5 x ₹5 risk = ₹25 = 0.5% of ₹5,000
    assert ids == ["DRY1"] and g.broker.positions() == {"NIFTYBEES": 5}


def test_buy_without_stop_or_too_big_is_blocked(tmp_path):
    g = guard(tmp_path)
    assert g.run_once({"NIFTYBEES": (5, None)}, D) == []
    assert "no_stop" in g.alerts[-1]
    assert g.run_once({"NIFTYBEES": (20, 90.0)}, D) == []   # ₹200 risk > ₹25
    assert "per_trade_risk" in g.alerts[-1]


def test_real_broker_never_trades_unless_all_three_switches_on(tmp_path):
    for env, verdict in [({}, "pass"), ({"KL_LIVE": "yes"}, "fail"), ({"KL_LIVE": "no"}, "pass")]:
        b = RealishBroker(prices={"NIFTYBEES": 100.0}, cash_inr=5000)
        g = guard(tmp_path, b, env, verdict)
        assert not g.live
        assert g.run_once({"NIFTYBEES": (5, 95.0)}, D) == []
        assert b.orders == [] and "WOULD buy" in g.alerts[-1]
    b = RealishBroker(prices={"NIFTYBEES": 100.0}, cash_inr=5000)
    g = guard(tmp_path, b, {"KL_LIVE": "yes"}, "pass")
    assert g.live and g.run_once({"NIFTYBEES": (5, 95.0)}, D) == ["DRY1"]


def test_capital_cap_limits_the_pot(tmp_path):
    b = DryRunBroker(prices={"NIFTYBEES": 100.0}, cash_inr=1_000_000)   # big account
    g = guard(tmp_path, b, {"KL_LIVE_CAPITAL": "5000"})
    g.run_once({"NIFTYBEES": (50, 99.0)}, D)   # ₹5,000 position = 100% of the capped pot
    assert g.book.pot == 5000 and b.orders == [] and "position_size" in g.alerts[-1]


def test_kill_file_flattens_only_bot_symbols(tmp_path):
    b = DryRunBroker(prices={"NIFTYBEES": 100.0, "TCS": 4000.0}, cash_inr=5000,
                     held={"NIFTYBEES": 5, "TCS": 2})   # TCS is Akhil's own holding
    g = guard(tmp_path, b)
    (tmp_path / "KILL").write_text("stop")
    assert g.run_once({"NIFTYBEES": (10, 95.0)}, D) == []
    assert b.positions() == {"TCS": 2} and "KILL SWITCH" in g.alerts[-1]


def test_env_kill_and_daily_loss_cap(tmp_path):
    g = guard(tmp_path, env={"KL_KILL": "1"})
    assert g.run_once({"NIFTYBEES": (5, 95.0)}, D) == [] and "kill switch on" in g.alerts[-1]
    g = guard(tmp_path)
    g.run_once({"NIFTYBEES": (5, 95.0)}, D - timedelta(days=1))
    g.broker.cash_inr -= 100     # ₹100 lost = 2% of pot > 1% daily cap
    assert g.run_once({"GOLDBEES": (2, 48.0)}, D) == []
    assert "daily loss cap" in g.alerts[-1] and g.broker.positions() == {}


def test_symbol_outside_universe_refused(tmp_path):
    g = guard(tmp_path)
    assert g.run_once({"ADANIENT": (1, 90.0)}, D) == []
    assert "not in the bot's universe" in g.alerts[0]


def test_currency_pairs_are_research_only(tmp_path):
    b = DryRunBroker(prices={"USDINR": 90.0, "NIFTYBEES": 100.0}, cash_inr=5000)
    g = Guard(broker=b, trial_id="T9", book=RiskBook(pot=5000), env={"KL_LIVE_CAPITAL": "5000"},
              trials_path=trials(tmp_path), root=tmp_path, universe=("USDINR", "NIFTYBEES"))
    assert g.run_once({"USDINR": (1, 85.0)}, D) == [] and b.orders == []
    assert "research only" in g.alerts[0]


def test_daily_order_budget_and_reset(tmp_path, monkeypatch):
    import src.live as L
    monkeypatch.setattr(L, "MAX_ORDERS_DAY", 1)
    g = guard(tmp_path)
    assert len(g.run_once({"NIFTYBEES": (2, 95.0), "GOLDBEES": (2, 48.0)}, D)) == 1
    assert "budget" in g.alerts[-1]
    assert len(g.run_once({"GOLDBEES": (2, 48.0)}, D + timedelta(days=1))) == 1


def test_alerts_only_to_private_chat():
    sent = []
    post = lambda url, body: sent.append(body) or True
    assert not alert("x", {"TELEGRAM_BOT_TOKEN": "t", "CEO_CHAT_ID": "-1001"}, post)
    assert alert("x", {"TELEGRAM_BOT_TOKEN": "t", "CEO_CHAT_ID": "1905524851"}, post) and len(sent) == 1
    assert private_chat("1905524851") and not private_chat("-42") and not private_chat("")

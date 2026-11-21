"""A335: the EA source enforces The5%ers High Stakes rules (static checks on the MQL5 code; no compiler here)."""
from pathlib import Path
EA = Path(__file__).resolve().parents[1] / "ea" / "phase5" / "EA_XAUUSD"


def src(rel):
    return (EA / rel).read_text()


def test_stage_targets_auto():
    c = src("Core/CConfig.mqh")
    assert "inp_ProfitTarget    = 0.0" in c and "STAGE_STEP2) ? 5.0" in c and "1e12" in c
    assert "inp_AccountSize * 0.91" in c


def test_three_profitable_days_gate():
    assert "CountProfitableDays() >= inp_MinProfitDays" in src("Guards/CPropFirmGuard.mqh")
    assert "StageRiskMult()" in src("Execution/CPositionSizer.mqh")
    assert "StageRiskMult()" in src("Execution/CMixEngine.mqh")


def test_day_uses_server_clock():
    assert "TimeToStruct(TimeTradeServer(), dt);" in src("Core/CDailyStats.mqh")


def test_gap_and_spike_safety():
    m = src("Execution/CMixEngine.mqh")
    assert "inp_MixMaxOpenRiskPct = 2.0" in m
    assert "if(!MarketCalm(why))" in m and "SpreadHardCap" in m


def test_daily_and_floor_stops_still_there():
    g = src("Guards/CGuardCoordinator.mqh")
    assert "inp_PropDailyStopPct = 4.0" in g and "Config.EquityFloor" in g

"""A335: the EA source enforces The5%ers High Stakes rules (static checks on the MQL5 code; no compiler here)."""
from pathlib import Path
EA = Path(__file__).resolve().parents[1] / "ea" / "phase5" / "EA_XAUUSD"


def src(rel):
    return (EA / rel).read_text()


def test_stage_targets_auto():
    c = src("Core/CConfig.mqh")
    assert "inp_ProfitTarget    = 0.0" in c and "STAGE_STEP2) ? 5.0" in c and "1e12" in c
    assert "inp_AccountSize * (1.0 - (FirmMaxPct - 1.0) / 100.0)" in c


def test_three_profitable_days_gate():
    assert "CountProfitableDays() >= inp_MinProfitDays" in src("Guards/CPropFirmGuard.mqh")
    assert "double StageRiskMult()" in src("Core/CDailyStats.mqh")
    assert "StageRiskMult()" in src("Execution/CPositionSizer.mqh")
    assert "StageRiskMult()" in src("Execution/CMixEngine.mqh")


def test_day_uses_server_clock():
    assert "TimeToStruct(TimeTradeServer(), dt);" in src("Core/CDailyStats.mqh")


def test_gap_and_spike_safety():
    m = src("Execution/CMixEngine.mqh")
    assert "inp_MixMaxOpenRiskPct = 2.0" in m
    assert "!MarketCalm(w2)" in m and "SpreadHardCap" in m


def test_daily_and_floor_stops_still_there():
    g = src("Guards/CGuardCoordinator.mqh")
    assert "Config.DailyStopPct" in g and "Config.EquityFloor" in g
    assert "inp_PropDailyStopPct     = 4.0" in src("Core/CConfig.mqh")


# ---------------- A336: live-safety fixes from the validation swarm ----------------
import re


def body(text, start, length=4000):
    i = text.index(start)
    return text[i:i + length]


def test_1_persistence_server_date_base_and_flag():
    p = src("Core/CPersistence.mqh")
    rd = body(p, "bool ReadDaily(")
    assert "TimeToStruct(TimeTradeServer(), today);" in rd and "TimeToStruct(TimeGMT()" not in rd
    assert '"forced_limit"' in p and '"start_balance"' in p
    d = src("Core/CDailyStats.mqh")
    assert "m_stats.forced_limit  = true;" in d and "RebuildToday(" in d
    assert "MathMax(file.open_equity, bal0)" in d


def test_2_friday_weekend_cut():
    c = src("Core/CConfig.mqh")
    assert "inp_FridayMaxOpenRiskPct = 1.25" in c and "inp_FridayCutHour        = 22" in c
    assert "bool WeekendCutActive()" in c and "TimeTradeServer()" in body(c, "bool WeekendCutActive()", 400)
    g = src("Guards/CGuardCoordinator.mqh")
    w = body(g, "void WeekendRiskCut()", 3000)
    assert 'CancelAllPendingOrders("friday_cut")' in w and "best_loss_tk" in w
    assert "AccountInfoDouble(ACCOUNT_EQUITY) * 0.01" in body(g, "double SelectedPositionRisk(", 800)
    assert "GuardCoordinator.WeekendRiskCut();" in src("EA_XAUUSD.mq5")
    assert "WeekendCutActive()" in body(src("Execution/CPositionSizer.mqh"), "bool NewEntryBlocked(", 500)


def test_3_4_no_round_up_lot_caps_spread():
    ps = src("Execution/CPositionSizer.mqh")
    assert "PriceUtils.ClampLot(" not in ps
    assert "<= 1.5 * dollar_risk" in ps and "GetSpreadPips()" in ps
    m = src("Execution/CMixEngine.mqh")
    assert "inp_MixMaxLot         = 0.10" in m and "inp_MinStopUsd        = 1.50" in m
    lot = body(m, "double Lot(int i", 2000)
    assert "MathMin(lot, inp_MixMaxLot)" in lot and "dist + spread" in lot and "inp_MinStopUsd" in lot


def test_5_terminal_states_keep_safety():
    ea = src("EA_XAUUSD.mq5")
    tick = body(ea, "void OnTick()", 1500)
    assert tick.index("FastSafetyCheck()") < tick.index("IsTerminal()")
    assert "void OnTerminalState()" in ea and "CloseAllOurPositions(" in ea
    h = src("Guards/CSystemHealthCheck.mqh")
    assert "m_symbol_fatal = true" not in h and "m_permissions_fatal = true" not in h
    assert "SUSPEND_SYSTEM_HEALTH" in body(h, "// A336 (#4): symbol + permissions, recoverable", 600)


def test_6_mix_passes_guards():
    m = src("Execution/CMixEngine.mqh")
    gate = body(m, "bool GateOk(string &why)", 2500)
    for g in ["GuardRollover.Evaluate", "SpreadGuard.Evaluate", "GuardCircuitBrk.Evaluate",
              "GuardNews.Evaluate", "GuardCooldown.Evaluate", "GuardSession.IsHardClosed",
              "NewsBlackout(", "MarketCalm(", "NewEntryBlocked("]:
        assert g in gate, g
    assert 'CancelPendings("gate:" + why)' in m
    assert "IsOurMagic(magic)" in src("EA_XAUUSD.mq5")             # daily limits: all our magics


def test_7_no_duplicate_pendings():
    m = src("Execution/CMixEngine.mqh")
    assert "Positions(i) > 0 || Pendings(i) > 0" in m and "PendingForBar(i, bar)" in m
    assert '"m%d|%.2f|%I64d"' in m
    assert "EAX_LOCK_" in src("EA_XAUUSD.mq5")


def test_8_day_base_max_balance_equity_snapped_each_second():
    d = src("Core/CDailyStats.mqh")
    assert "m_stats.open_equity     = MathMax(bal, eq);" in d
    roll = body(d, "void CheckDayRollover()", 400)
    assert "< 60" not in roll
    t = src("Core/CTimerSystem.mqh")
    assert "m_timer_interval_sec(1)" in t
    assert "DailyStats.CheckDayRollover();" in body(src("EA_XAUUSD.mq5"), "void OnTick()", 600)


def test_9_calendar_fails_closed():
    n = src("Intelligence/CMSNREngine.mqh")
    nb = body(n, "bool NewsBlackout(string &why)", 1500)
    assert "if(n < 0)" in nb and "return true;                                          // fail closed" in nb
    assert "CalendarSynced()" in nb and "inp_NewsBlockMin = 120" in n
    assert "MathMax(inp_NewsBlockMin, 3)" in nb


def test_10_rollover_in_server_time_before_session():
    s = src("Guards/CSessionGuard.mqh")
    assert "int sm = ServerMinuteOfDay();" in s
    c = src("Core/CConfig.mqh")
    assert "inp_RolloverStartHr = 23" in c and "inp_RolloverEndMn   = 20" in c
    ea = src("EA_XAUUSD.mq5")
    assert ea.index("RegisterGuard(&GuardRollover,    5)") < ea.index("RegisterGuard(&GuardSession,     6)")


def test_11_account_size_check_and_firm_limits_inputs():
    c = src("Core/CConfig.mqh")
    assert "> 0.15" in c and "AccountSizeOk" in c and "inp_Stage != STAGE_FUNDED" in c
    assert "inp_FirmDailyLossPct" in c and "inp_FirmMaxLossPct" in c
    assert "(inp_AccountSize >= 50000.0) ? 4.0 : 5.0" in c and "(inp_AccountSize >= 50000.0) ? 8.0 : 10.0" in c
    assert "MathMin(inp_PropDailyStopPct, FirmDailyPct - 1.0)" in c


def test_12_max_positions_and_no_opposite():
    c = src("Core/CConfig.mqh")
    assert "inp_MaxOpenPositions     = 0" in c and "inp_AllowOpposite        = true" in c   # quant re-test defaults
    assert "inp_MaxOpenPositions > 0 && n >= inp_MaxOpenPositions" in src("Execution/CPositionSizer.mqh")
    oa = body(src("Execution/CPositionSizer.mqh"), "bool OrderAllowed(", 1800)
    assert "inp_MaxOpenPositions" in oa and "inp_AllowOpposite" in oa
    assert "OrderAllowed(" in src("Execution/CEntryEngine.mqh") and "OrderAllowed(" in src("Execution/CMixEngine.mqh")


def test_13_dry_run_stops_mix_orders():
    m = src("Execution/CMixEngine.mqh")
    act = body(m, "void Act(int i, datetime bar)", 5000)
    for marker in ["m_trade.Buy(", "SendLimit("]:
        assert act.index("if(Config.DryRun)") < act.index(marker)
    assert act.count("if(Config.DryRun)") == 2


def test_14_profitable_days_official_formula():
    d = src("Core/CDailyStats.mqh")
    assert "MathMin(m_snap_eb[i], m_snap_ee[i]) - m_snap_sb[i] >= need" in d
    assert "AppendDaySnapshot(" in d and "CountHistoryFallback()" in d
    assert "int CountProfitableDays()" not in src("Core/CConfig.mqh")


def test_15_inactivity_watchdog():
    d = src("Core/CDailyStats.mqh")
    w = body(d, "void CheckInactivity()", 2000)
    assert "idle_days >= 25" in w and "DEAL_ENTRY_IN" in w
    assert "CheckInactivity()" in src("Core/CTimerSystem.mqh")


def test_16_margin_check():
    oa = body(src("Execution/CPositionSizer.mqh"), "bool OrderAllowed(", 1800)
    assert "OrderCalcMargin(" in oa and "/ inp_MetalLeverage" in oa and "0.5 * free_m" in oa


def test_17_medium_low_review_items():
    ea = src("EA_XAUUSD.mq5")
    assert "g_mng_partial" in ea and "SYMBOL_TRADE_FREEZE_LEVEL" in ea           # 12, 22
    assert 'StringFind(sym, "XAU")' in ea                                        # 19
    assert "IndicatorRelease(g_atr_m5)" in ea and "MixEngine.Shutdown()" in ea  # 28
    assert "RebuildMainStreak()" in ea and "RebuildStreaks()" in src("Execution/CMixEngine.mqh")  # 29
    e = src("Execution/CEntryEngine.mqh")
    assert "TRADE_RETCODE_TIMEOUT" in e and "magic=%I64d" in e                  # 13, 32
    assert "copied < VOL_STABILITY_WINDOW + 1" in src("Intelligence/CVolatilityEngine.mqh")  # 14
    assert "TimeTradeServer() - t.time" in src("Core/CTimerSystem.mqh")         # 15
    assert "Config.SpreadHardCap * 1.5" not in src("Guards/CSpreadGuard.mqh")   # 21
    m = src("Execution/CMixEngine.mqh")
    assert 'why = "atr_unavailable"; return false;' in m                         # 16
    assert "Throttled(tk)" in m and "TRADE_RETCODE_INVALID_FILL" in m            # 25, 26
    assert "m_fallback" not in src("Include/PriceUtils.mqh") and "tick_value <= 0" in src("Include/PriceUtils.mqh")  # 27
    assert "virtual void LoadState() override" in src("Guards/CNewsGuard.mqh")  # 31
    assert "EAGmtNow()" in src("Guards/GuardTypes.mqh")                         # 20


def test_balanced_braces_all_files():
    for f in EA.rglob("*.mq*"):
        t = re.sub(r'//[^\n]*|/\*.*?\*/|"(\\.|[^"\\])*"|\'(\\.|[^\'\\])*\'', " ", f.read_text(), flags=re.S)
        for o, c in ["{}", "()", "[]"]:
            assert t.count(o) == t.count(c), (f.name, o)


def test_inputs_declared_once():
    names = []
    for f in EA.rglob("*.mq*"):
        names += re.findall(r"^\s*input\s+\w+\s+(inp_\w+)", f.read_text(), flags=re.M)
    dups = {n for n in names if names.count(n) > 1}
    assert not dups, dups
    for n in ["inp_FridayMaxOpenRiskPct", "inp_FridayCutHour", "inp_MaxOpenPositions", "inp_AllowOpposite",
              "inp_MixMaxLot", "inp_MinStopUsd", "inp_FirmDailyLossPct", "inp_FirmMaxLossPct", "inp_NewsBlockMin",
              "inp_WeekendGapPct", "inp_WeekendLossBudgetPct", "inp_MainWeight"]:
        assert n in names, n


def test_weekend_gap_lot_based_budget():
    c = src("Core/CConfig.mqh")
    assert "inp_WeekendGapPct        = 3.75" in c and "inp_WeekendLossBudgetPct = 3.0" in c
    w = body(src("Guards/CGuardCoordinator.mqh"), "void WeekendRiskCut()", 5000)
    assert "inp_WeekendGapPct / 100.0 * cur * vol * vpp" in w
    assert "MathMax(r, gap_loss)" in w and "worst_total > budget" in w
    assert "MathMax(AccountInfoDouble(ACCOUNT_BALANCE), AccountInfoDouble(ACCOUNT_EQUITY))" in w
    assert "inp_FridayMaxOpenRiskPct" in w


def test_strategy_weights_scenario_g():
    m = src("Execution/CMixEngine.mqh")
    assert "inp_MixRiskPct        = 0.40" in m and "inp_MixMaxOpenRiskPct = 2.0" in m
    want = {"FreshLongH1": "1.0", "FreshLongH2": "1.0", "FreshShortH2": "1.0",
            "FreshLongH4": "0.5", "QmLongH1": "0.5", "QmLongH4": "0.5", "QmShortH1": "0.5",
            "Ema9H2": "0.0", "Ema9H4": "0.0", "QmLongH2": "0.0", "FreshShortH4": "0.0", "QmShortH4": "0.0"}
    for k, v in want.items():
        assert re.search(r"input double\s+inp_W_%s\s*=\s*%s;" % (k, re.escape(v)), m), k
        assert "inp_W_%s);" % k in m, k                                  # wired into Def()
    assert "m_s[i].weight" in body(m, "double Lot(int i", 600)
    assert "if(m_s[i].weight <= 0) continue;" in m
    ps = src("Execution/CPositionSizer.mqh")
    assert "inp_MainWeight   = 0.5" in ps and "Config.RiskPct * MathMax(0.0, inp_MainWeight)" in ps
    assert "inp_RiskPct         = 0.40" in src("Core/CConfig.mqh")


# --- A337: E8 Pro support -------------------------------------------------------------------------
def _ea(rel):
    import pathlib
    return (pathlib.Path(__file__).resolve().parents[1] / "ea/phase5" / rel).read_text(encoding="utf-8", errors="ignore")


def test_e8_daily_profit_cap_closes_and_stops_for_day():
    g = _ea("EA_XAUUSD/Guards/CGuardCoordinator.mqh")
    assert "inp_DailyProfitCapPct > 0.0" in g and 'EmergencyCloseAll("daily_profit_cap")' in g
    assert "ForceDailyLimit(StringFormat(\"profit cap" in g


def test_metal_leverage_is_an_input_used_for_margin():
    assert "input double   inp_MetalLeverage" in _ea("EA_XAUUSD/Core/CConfig.mqh")
    s = _ea("EA_XAUUSD/Execution/CPositionSizer.mqh")
    assert "/ inp_MetalLeverage" in s and "/ 25.0" not in s


def test_e8_preset_matches_verified_rules():
    kv = dict(l.split("=", 1) for l in _ea("presets/E8_Pro_10K_challenge.set").splitlines()
              if "=" in l and not l.startswith(";"))
    assert kv["inp_FirmDailyLossPct"] == "2.5" and kv["inp_FirmMaxLossPct"] == "8"
    assert float(kv["inp_PropDailyStopPct"]) < 2.5 and kv["inp_DailyProfitCapPct"] == "2.0"
    assert kv["inp_MetalLeverage"] == "15" and kv["inp_MinProfitDays"] == "0"


def test_e8_preset_uses_safer_risk_from_nearby_check():
    kv = dict(l.split("=", 1) for l in _ea("presets/E8_Pro_10K_challenge.set").splitlines()
              if "=" in l and not l.startswith(";"))
    assert kv["inp_MixRiskPct"] == "0.30" and kv["inp_RiskPct"] == "0.30"


//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Main File                               |
//| File: EA_XAUUSD.mq5                                               |
//| Version: 1.0.0 — Phase 1: Core Framework Only                    |
//| Target: The5%ers High Stakes $10K evaluation                      |
//| Symbol: XAUUSD | Broker: Any MT5 | Sessions: London + NY          |
//+------------------------------------------------------------------+
//
// PHASE 1 SCOPE:
//   - Full EA lifecycle (OnInit, OnTick, OnTimer, OnDeinit)
//   - State machine skeleton
//   - All singletons initialized in correct order
//   - Validation and halting on fatal config errors
//   - Heartbeat system running
//   - All logging operational
//   - File persistence operational
//   - Daily stats tracking operational
//   - NO guard logic (Phase 2)
//   - NO market analysis (Phase 3)
//   - NO entry/exit logic (Phases 4–6)
//   - NO recovery logic (Phase 7)
//
// ARCHITECTURE PRINCIPLE:
//   This file is an ORCHESTRATOR only.
//   It calls module methods. It contains no business logic.
//   Every decision is delegated to a named module.
//   If you find trading logic in this file, it is a bug.
//+------------------------------------------------------------------+

#property copyright "XAUUSD Institutional EA"
#property version   "1.00"
#property strict

//--- Include Phase 1 modules in dependency order
#include "Include/Defines.mqh"        // Enums + structs (no dependencies)
#include "Include/PriceUtils.mqh"     // Price math (depends: Defines)
#include <Trade/Trade.mqh>            // A320: CTrade for position management
#include "Core/CLogger.mqh"           // Logging (depends: Defines)
#include "Core/CConfig.mqh"           // Config (depends: Logger)
#include "Core/CPersistence.mqh"      // File I/O (depends: Logger)
#include "Core/CStateManager.mqh"     // State machine (depends: Logger)
#include "Core/CDailyStats.mqh"       // Daily tracking (depends: Logger, Persist, Config)
#include "Core/CTimerSystem.mqh"      // Timer (depends: all above)

//--- Phase 2 — Guard Layer (all modules)
#include "Guards/GuardTypes.mqh"
#include "Guards/CGuardCoordinator.mqh"
#include "Guards/CSystemHealthCheck.mqh"
#include "Guards/CPropFirmGuard.mqh"
#include "Guards/CEquityGuard.mqh"
#include "Guards/CDailyDrawdownGuard.mqh"
#include "Guards/CSessionGuard.mqh"    // Contains CSessionGuard + CRolloverGuard
#include "Guards/CSpreadGuard.mqh"
#include "Guards/CNewsGuard.mqh"
#include "Guards/CCircuitBreaker.mqh"
#include "Guards/CCooldownManager.mqh"

//--- Guard singletons (global — registered into coordinator in OnInit)
//--- A320 globals
int    g_atr_m5  = INVALID_HANDLE;
int    g_atr_m15 = INVALID_HANDLE;
CTrade g_mgr;                    // position management (partial close, stop moves)
bool   g_lock_owner = false;     // A336 (#7): this chart owns the single-instance lock
ulong  g_txn_pos  = 0;           // trade-transaction accumulator
double g_txn_pnl  = 0.0;
double g_txn_risk = 0.0;

CSystemHealthCheck  GuardSysHealth;
CPropFirmGuard      GuardPropFirm;
CEquityGuard        GuardEquity;
CDailyDrawdownGuard GuardDailyDD;
CSessionGuard       GuardSession;
CRolloverGuard      GuardRollover;
CNewsGuard          GuardNews;
CSpreadGuard        SpreadGuard;    // Also used by News + CircuitBreaker
CCircuitBreaker     GuardCircuitBrk;
CCooldownManager    GuardCooldown;

//--- Phase 3 — Intelligence Layer (engines built so far)
//    Order matters: CIntelligenceCoordinator transitively includes the engines.
#include "Intelligence/CIntelligenceCoordinator.mqh"

//--- Phase 3 future steps (will be uncommented as built)
// #include "Intelligence/CRegimePersistenceModel.mqh"
// #include "Intelligence/CTrendEngine.mqh"
// #include "Intelligence/CLiquidityEngine.mqh"  // Included via CIntelligenceCoordinator.mqh
#include "Intelligence/CMSNREngine.mqh"       // A320: MSNR levels + gate (before the scorer)
#include "Scoring/CTradeScorer.mqh"
#include "Execution/CPositionSizer.mqh"
#include "Execution/CTradeCalculator.mqh"
bool HasOpenPosition();   // A348: prototype - defined below, called from CEntryEngine
#include "Execution/CEntryEngine.mqh"
#include "Execution/CMixEngine.mqh"         // A327: the 12 extra strategies of the best gold mix
// #include "Execution/CRiskEngine.mqh"
// #include "Management/CTradeManager.mqh"
// #include "Recovery/CVPSHandler.mqh"
// #include "Analytics/CDashboard.mqh"

//+------------------------------------------------------------------+
//| EA INITIALIZATION                                                  |
//| Called once when EA starts or is reattached to chart              |
//+------------------------------------------------------------------+
int OnInit()
{
   //=================================================================
   // INIT ORDER IS CRITICAL — modules depend on earlier ones.
   // Logger MUST be first. Config MUST be before anything that uses it.
   // Persistence MUST be before DailyStats (loads from disk).
   // All modules MUST succeed — any failure halts EA.
   //=================================================================

   // --- Step 1: Logger (no dependencies)
   if(!Logger.Init(true, LOG_INFO))
   {
      // Cannot log the failure — Print is last resort
      Print("[FATAL] Logger init failed — EA cannot start");
      return INIT_FAILED;
   }

   Logger.Info("INIT", "=== EA INITIALIZATION STARTING ===",
      StringFormat("version=%s build=%s symbol=%s account=%lld",
                   EA_VERSION, EA_BUILD_DATE, Symbol(),
                   AccountInfoInteger(ACCOUNT_LOGIN)));

   // --- Step 2: Validate we are on a GOLD chart (A336 #19: EA_SYMBOL is _Symbol, so the old
   //     check could never fail; on EURUSD/US30 the EA would trade with gold pip maths)
   {
      string sym = _Symbol;
      StringToUpper(sym);
      if(StringFind(sym, "XAU") < 0 && StringFind(sym, "GOLD") < 0)
      {
         Logger.Fatal("INIT", StringFormat("Wrong symbol: %s is not gold (XAU/GOLD)", _Symbol));
         return INIT_FAILED;
      }
      double cs = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
      if(MathAbs(cs - 100.0) > 0.001)
         Logger.Warn("INIT", StringFormat("Contract size %.2f (expected 100 oz) - check sizing", cs));
   }

   // --- Step 2b (A336 #7): one instance per magic. A second chart with the same magic would
   //     double every order. The temp global variable holds the owning chart id.
   {
      string lock = StringFormat("EAX_LOCK_%I64d", inp_MagicNumber);
      if(GlobalVariableCheck(lock) && GlobalVariableGet(lock) != (double)(ChartID() & 0xFFFFFFFFFFFF))
      {
         Logger.Fatal("INIT", "Another chart already runs this EA with the same magic number - refusing to start");
         return INIT_FAILED;
      }
      GlobalVariableTemp(lock);
      GlobalVariableSet(lock, (double)(ChartID() & 0xFFFFFFFFFFFF));
      g_lock_owner = true;
   }

   // --- Step 3: Validate account type (must be able to hedge)
   ENUM_ACCOUNT_MARGIN_MODE margin_mode =
      (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   // Debug pass 26 Nov: before login (VPS reboot) ACCOUNT_MARGIN_MODE reads 0 = NETTING; only trust it once logged in
   if(margin_mode == ACCOUNT_MARGIN_MODE_RETAIL_NETTING && AccountInfoInteger(ACCOUNT_LOGIN) > 0)
   {
      Logger.Fatal("INIT",
         "Account is NETTING — EA requires HEDGING mode");
      return INIT_FAILED;
   }

   // --- Step 4: Price utilities (reads symbol specs from broker)
   if(!PriceUtils.Init(EA_SYMBOL))
   {
      Logger.Fatal("INIT", "PriceUtils init failed — bad symbol specs");
      return INIT_FAILED;
   }

   Logger.Info("INIT", "Symbol specs loaded",
      StringFormat("point=%.5f digits=%d pip_value=%.4f",
                   PriceUtils.Point(), PriceUtils.Digits(),
                   PriceUtils.PipValue()));

   // --- Step 5: Configuration (validates all inputs)
   if(!Config.Init())
   {
      Logger.Fatal("INIT", "Config validation failed — check input parameters");
      return INIT_FAILED;
   }

   // --- Step 6: Persistence layer
   if(!Persistence.Init())
   {
      Logger.Fatal("INIT", "Persistence layer init failed");
      return INIT_FAILED;
   }

   // --- Step 7: Daily stats (loads from disk or resets)
   if(!DailyStats.Init())
   {
      Logger.Fatal("INIT", "DailyStats init failed");
      return INIT_FAILED;
   }

   // --- Step 8: State manager — transition from INITIALIZING
   StateManager.Transition(STATE_GUARD_CHECK, "init_complete");

   // --- Step 9: Timer system (EventSetTimer)
   if(!TimerSystem.Init())
   {
      // Non-fatal: EA can run without timer (degraded mode)
      Logger.Warn("INIT", "Timer system failed — heartbeat and cleanup disabled");
   }

   // --- Phase 2: Guard Layer initialization (strict order)
   // SpreadGuard initialized first (provides data to News + CircuitBrk)
   if(!SpreadGuard.Init())
   { Logger.Fatal("INIT", "SpreadGuard init failed"); return INIT_FAILED; }

   if(!GuardSysHealth.Init())
   { Logger.Fatal("INIT", "SystemHealthCheck init failed"); return INIT_FAILED; }

   if(!GuardPropFirm.Init())
   { Logger.Fatal("INIT", "PropFirmGuard init failed"); return INIT_FAILED; }

   if(!GuardEquity.Init())
   { Logger.Fatal("INIT", "EquityGuard init failed"); return INIT_FAILED; }

   if(!GuardDailyDD.Init())
   { Logger.Fatal("INIT", "DailyDrawdownGuard init failed"); return INIT_FAILED; }

   if(!GuardSession.Init())
   { Logger.Fatal("INIT", "SessionGuard init failed"); return INIT_FAILED; }

   if(!GuardRollover.Init())
   { Logger.Fatal("INIT", "RolloverGuard init failed"); return INIT_FAILED; }

   // Inject SpreadGuard pointer into News + CircuitBreaker
   GuardNews.SetSpreadGuard(&SpreadGuard);
   GuardCircuitBrk.SetSpreadGuard(&SpreadGuard);

   if(!GuardNews.Init())
   { Logger.Fatal("INIT", "NewsGuard init failed"); return INIT_FAILED; }

   if(!GuardCircuitBrk.Init())
   { Logger.Fatal("INIT", "CircuitBreaker init failed"); return INIT_FAILED; }

   if(!GuardCooldown.Init())
   { Logger.Fatal("INIT", "CooldownManager init failed"); return INIT_FAILED; }

   // Register all guards into coordinator (in priority order)
   // Register guards FIRST, then Init() so slot validation is correct
   GuardCoordinator.RegisterGuard(&GuardSysHealth,   1);
   GuardCoordinator.RegisterGuard(&GuardPropFirm,    2);
   GuardCoordinator.RegisterGuard(&GuardEquity,      3);
   GuardCoordinator.RegisterGuard(&GuardDailyDD,     4);
   // A336 (#10): rollover BEFORE session, so the rollover window is seen even outside London/NY
   GuardCoordinator.RegisterGuard(&GuardRollover,    5);
   GuardCoordinator.RegisterGuard(&GuardSession,     6);
   GuardCoordinator.RegisterGuard(&GuardNews,        7);
   GuardCoordinator.RegisterGuard(&SpreadGuard,      8);
   GuardCoordinator.RegisterGuard(&GuardCircuitBrk,  9);
   GuardCoordinator.RegisterGuard(&GuardCooldown,    10);
   if(!GuardCoordinator.Init())
   { Logger.Fatal("INIT", "GuardCoordinator init failed"); return INIT_FAILED; }

   Logger.Info("INIT", "Phase 2 guard layer fully initialized");

   // --- Phase 3: Intelligence Layer initialization
   // Engines first (in dependency-free order — engine Init() does not call other engines).
   // Then coordinator, which verifies all are initialized.
   double pip_size = PriceUtils.PipSize();

   if(!StructureEngine.Init(EA_SYMBOL, pip_size))
   { Logger.Fatal("INIT", "StructureEngine init failed"); return INIT_FAILED; }

   if(!VolatilityEngine.Init(EA_SYMBOL, pip_size))
   { Logger.Fatal("INIT", "VolatilityEngine init failed"); return INIT_FAILED; }

   if(!RegimeEngine.Init(EA_SYMBOL, pip_size))
   { Logger.Fatal("INIT", "RegimeEngine init failed"); return INIT_FAILED; }

   if(!LiquidityEngine.Init(EA_SYMBOL, pip_size))
   { Logger.Fatal("INIT", "LiquidityEngine init failed"); return INIT_FAILED; }

   if(!RegimePersistenceModel.Init())
   { Logger.Fatal("INIT", "RegimePersistenceModel init failed"); return INIT_FAILED; }

   if(!TrendEngine.Init(EA_SYMBOL, pip_size))
   { Logger.Fatal("INIT", "TrendEngine init failed"); return INIT_FAILED; }

   if(!TradeScorer.Init(EA_SYMBOL))
   { Logger.Fatal("INIT", "TradeScorer init failed"); return INIT_FAILED; }

   if(!PositionSizer.Init())
   { Logger.Fatal("INIT", "PositionSizer init failed"); return INIT_FAILED; }

   if(!TradeCalculator.Init(EA_SYMBOL))
   { Logger.Fatal("INIT", "TradeCalculator init failed"); return INIT_FAILED; }

   if(!EntryEngine.Init(EA_SYMBOL))
   { Logger.Fatal("INIT", "EntryEngine init failed"); return INIT_FAILED; }

   // Register engines and SpreadGuard with coordinator
   IntelligenceCoordinator.RegisterStructure(&StructureEngine);
   IntelligenceCoordinator.RegisterVolatility(&VolatilityEngine);
   IntelligenceCoordinator.RegisterRegime(&RegimeEngine);
   IntelligenceCoordinator.RegisterLiquidity(&LiquidityEngine);
   IntelligenceCoordinator.RegisterPersistence(&RegimePersistenceModel);
   IntelligenceCoordinator.RegisterTrend(&TrendEngine);
   IntelligenceCoordinator.RegisterSpreadGuard(&SpreadGuard);

   if(!IntelligenceCoordinator.Init(EA_SYMBOL, pip_size, Config.MagicNumber))
   { Logger.Fatal("INIT", "IntelligenceCoordinator init failed"); return INIT_FAILED; }

   Logger.Info("INIT", "Phase 3 intelligence layer initialized (Structure + Volatility + Regime + Liquidity + Persistence + Trend)");

   // --- A320: MSNR engine (history may still be loading on first start; OnTimer retries)
   if(!MSNR.Init())
      Logger.Warn("INIT", "MSNR not ready yet — MSNR gate blocks entries until it is (retried every 60s)");

   // --- A327: strategy mix engine
   MixEngine.Init();

   // --- A320: ATR handles for spread calibration (M5) and the trailing stop (M15)
   g_atr_m5  = iATR(EA_SYMBOL, PERIOD_M5, 14);
   g_atr_m15 = iATR(EA_SYMBOL, PERIOD_M15, 14);
   if(g_atr_m5 == INVALID_HANDLE || g_atr_m15 == INVALID_HANDLE)
   { Logger.Fatal("INIT", "ATR handle creation failed"); return INIT_FAILED; }
   g_mgr.SetExpertMagicNumber(Config.MagicNumber);
   g_mgr.SetTypeFillingBySymbol(EA_SYMBOL);
   g_mgr.SetDeviationInPoints((ulong)MathMax(1.0, MathRound(Config.PipsToPoints(Config.SlippageMax))));
   g_mgr.LogLevel(0);

   // --- A336 (#29): streak sizing survives a restart (sign of the main strategy's last close)
   RebuildMainStreak();

   // --- Step 10: Check for orphaned position from previous session
   // (Phase 7 will implement full recovery — Phase 1 just detects)
   TradeState orphan;
   if(Persistence.ReadPosition(orphan))
   {
      Logger.Warn("INIT",
         "Orphaned position file found — recovery pending (Phase 7)",
         StringFormat("ticket=%llu entry=%.5f", orphan.ticket, orphan.entry_price));
      // Phase 7: OrphanedPositionRecovery.Recover(orphan)
      // For now: log and continue — state machine will detect open position
   }

   // --- Step 11: Log account state
   Logger.Info("INIT", "Account state at startup",
      StringFormat("balance=%.2f equity=%.2f "
                   "profitable_days=%d daily_trades=%d daily_pnl=%.2f",
                   AccountInfoDouble(ACCOUNT_BALANCE),
                   AccountInfoDouble(ACCOUNT_EQUITY),
                   DailyStats.GetProfitableDays(),
                   DailyStats.GetTradeCount(),
                   DailyStats.GetClosedPnL()));

   // --- A336 (G19): show the live limits so they can be confirmed on the chart
   Alert(EA_NAME, StringFormat(": stage=%d target=%.2f floor=%.2f daily stop=%.1f%% of day base (firm %.1f%%) dry_run=%d size_ok=%d",
                               (int)inp_Stage, Config.ProfitTarget, Config.EquityFloor, Config.DailyStopPct,
                               Config.FirmDailyPct, (int)Config.DryRun, (int)Config.AccountSizeOk));

   Logger.Info("INIT", "=== EA INITIALIZATION COMPLETE ===");

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| TICK HANDLER — main EA loop, runs on every price tick             |
//+------------------------------------------------------------------+
void OnTick()
{
   // --- Track tick timing (stale price detection)
   TimerSystem.OnTickFire();

   // --- A336 (#7/#8): server-day rollover on EVERY tick (base snapped at 00:00 server)
   DailyStats.CheckDayRollover();

   // --- Update equity tracking every tick
   DailyStats.UpdateEquity(AccountInfoDouble(ACCOUNT_EQUITY));

   // --- A320/A336: equity floor + daily stop on EVERY tick, in EVERY state (terminal included, #5)
   bool safe = GuardCoordinator.FastSafetyCheck();
   NewsDerisk();                                            // A346: cut the book before scheduled news

   // --- A336 (#2): Friday weekend-gap cut (cancel pendings, shrink open risk)
   GuardCoordinator.WeekendRiskCut();

   // --- A336 (#5): terminal states keep protecting and managing open positions
   if(StateManager.IsTerminal())
   {
      OnTerminalState();
      return;
   }

   if(!safe)
   {
      MixEngine.CancelPendings("safety_stop");
      MixEngine.Manage();
      return;
   }

   // --- Stale price guard (A336 #15: real quote age). No new entries; keep managing.
   if(TimerSystem.IsPriceStale())
   {
      MixEngine.Manage();
      if(HasOpenPosition()) ManageOpenPosition();
      return;
   }

   // --- Phase 3: Update intelligence layer
   // Fast on most ticks (bar boundary check + early return).
   // Slow path only on bar closes (engines run, packet rebuilt).
   IntelligenceCoordinator.Update();
   MSNR.Update();                                   // A320: cheap unless an H1/H4/W1 bar closed

   // A327: the mix runs beside the EA's own strategy. New orders only when the EA is not suspended,
   // stopped or at its target; while suspended it only does time exits and cancels pendings.
   // A336 (#5/#6): inside OnTick the mix passes its own guard gate before any order.
   if(StateManager.IsSuspended())
   {
      MixEngine.CancelPendings("suspended");
      MixEngine.Manage();
   }
   else
      MixEngine.OnTick();

   //=================================================================
   // MAIN STATE DISPATCH
   // Each state has its own handler.
   // No state's logic bleeds into another's handler.
   //=================================================================
   switch(StateManager.GetState())
   {
      case STATE_INITIALIZING:
         // Should never tick in this state — log anomaly
         Logger.Warn("TICK", "Tick received while INITIALIZING — skipping");
         break;

      case STATE_GUARD_CHECK:
         OnState_GuardCheck();
         break;

      case STATE_SEEK_ENTRY:
         OnState_SeekEntry();
         break;

      case STATE_MANAGE_TRADE:
         OnState_ManageTrade();
         break;

      case STATE_SUSPENDED:
         OnState_Suspended();
         break;

      case STATE_PROFIT_TARGET:
      case STATE_FATAL_ERROR:
         // A336: handled by OnTerminalState() above (never reached)
         break;

      default:
         Logger.Error("TICK",
            StringFormat("Unknown state %d — safety halt",
                         (int)StateManager.GetState()));
         StateManager.Transition(STATE_FATAL_ERROR, "unknown_state");
         break;
   }
}

//+------------------------------------------------------------------+
//| STATE HANDLERS — one per state, called from OnTick dispatch       |
//+------------------------------------------------------------------+

//--- A336 (#5): PROFIT_TARGET / FATAL no longer switch every safety check off.
//    FastSafetyCheck() already ran this tick. Here: no mix order may fill, mix time exits keep
//    running, the main trade keeps its breakeven/trailing, and at PROFIT_TARGET any position
//    still open is closed again every 5 s until flat.
void OnTerminalState()
{
   MixEngine.CancelPendings("terminal_state");
   MixEngine.Manage();
   if(StateManager.GetState() == STATE_PROFIT_TARGET)
   {
      if(GuardCoordinator.HasAnyOurPosition())
         GuardCoordinator.CloseAllOurPositions("profit_target_flatten");
      return;
   }
   if(HasOpenPosition()) ManageOpenPosition();
}

void OnState_GuardCheck()
{
   // Evaluate full guard chain through coordinator
   GuardEvalResult result = GuardCoordinator.Evaluate();

   if(result.status == GUARD_FATAL || result.status == GUARD_SUSPEND)
      return; // Coordinator already handled state transition

   if(result.status == GUARD_BLOCK)
      return; // Stay in GUARD_CHECK — try again next tick

   // All guards passed — route by position status
   if(HasOpenPosition())
      StateManager.Transition(STATE_MANAGE_TRADE, "guard_pass_has_position");
   else
      StateManager.Transition(STATE_SEEK_ENTRY, "guard_pass_no_position");
}

//--- Phase 4: last actionable decision, held for Phase 5 execution.
//    Phase 5 (EntryEngine) will read this when it exists. Until then,
//    a valid decision is logged and we return to guard check.
TradeDecision g_last_trade_decision;

void OnState_SeekEntry()
{
   //=================================================================
   // PHASE 4: Intelligence packet -> trade decision.
   //   1. Pull the assembled packet from the coordinator.
   //   2. Run the scorer (all gates: score, direction, persistence,
   //      volatility floor, pullback-resume trigger, sweep gate).
   //   3. Valid  -> hold decision for Phase 5, log, return to guard.
   //      Invalid -> return to guard check.
   //
   // Phase 5 will replace the "hold + return" with actual order
   // placement (EntryEngine.QueueEntry(decision)).
   //=================================================================

   IntelligencePacket pkt = IntelligenceCoordinator.GetPacket();

   TradeDecision decision = TradeScorer.Evaluate(pkt);
   g_last_trade_decision = decision;

   if(decision.valid)
   {
      //=================================================================
      // PHASE 5: build levels -> size -> execute.
      //   1. TradeCalculator: SL/TP prices + real-RR gate.
      //   2. PositionSizer: lot from risk + SL distance.
      //   3. EntryEngine: DryRun logs / live sends (2 retries, fill check).
      //   4. On confirmed fill (or DryRun) -> MANAGE_TRADE; else GUARD_CHECK.
      //=================================================================
      IntelligencePacket pkt2 = IntelligenceCoordinator.GetPacket();

      OrderPlan plan;
      ZeroMemory(plan);
      plan.valid      = false;
      plan.result     = EXEC_NONE;
      plan.planned_at = TimeCurrent();

      //--- 1. SL/TP levels + real-RR gate
      if(!TradeCalculator.BuildLevels(pkt2, decision, plan))
      {
         Logger.Info("SEEK_ENTRY",
            StringFormat("Levels/RR gate rejected setup (result=%d) — back to guard",
                          plan.result));
         StateManager.Transition(STATE_GUARD_CHECK, "phase5_levels_rejected");
         return;
      }

      //--- 2. Position sizing
      double risk_dollars = 0.0;
      double lot = PositionSizer.ComputeLot(plan.sl_pips, risk_dollars);
      if(lot <= 0.0)
      {
         Logger.Warn("SEEK_ENTRY", "Sizing refused (0 lot) — back to guard");
         StateManager.Transition(STATE_GUARD_CHECK, "phase5_sizing_refused");
         return;
      }
      plan.lot          = lot;
      plan.risk_dollars = risk_dollars;
      plan.valid        = true;

      //--- 3. Execute (DryRun logs / live sends)
      plan = EntryEngine.Execute(plan);

      //--- 4. Route on outcome
      if(plan.result == EXEC_PLACED)
      {
         Logger.Info("SEEK_ENTRY",
            StringFormat("LIVE FILL ticket=%I64u — entering MANAGE_TRADE", plan.ticket));
         StateManager.Transition(STATE_MANAGE_TRADE, "phase5_live_fill");
         return;
      }

      if(plan.result == EXEC_DRYRUN)
      {
         // DryRun: no real position. Stay in seek/guard cycle.
         Logger.Info("SEEK_ENTRY", "DRY-RUN order logged — no position opened");
         StateManager.Transition(STATE_GUARD_CHECK, "phase5_dryrun");
         return;
      }

      // Any rejection/failure — back to guard check
      Logger.Info("SEEK_ENTRY",
         StringFormat("Execution not completed (result=%d) — back to guard", plan.result));
      StateManager.Transition(STATE_GUARD_CHECK, "phase5_exec_incomplete");
      return;
   }

   // No actionable setup — back to guard check.
   StateManager.Transition(STATE_GUARD_CHECK, "phase4_no_setup");
}

void OnState_ManageTrade()
{
   //=================================================================
   // PHASE 1: Skeleton only.
   // Full management in Phase 6.
   //
   // PSEUDO-CODE for Phase 6:
   //   if EquityGuard.IsFloorBreached():  → EmergencyClose → GUARD_CHECK
   //   if ProfitGuard.IsTargetReached():  → CloseAll → PROFIT_TARGET
   //   TradeManager.Update()
   //     → BreakevenManager.Check()
   //     → PartialClose.Check()
   //     → TrailingManager.Check()
   //   if !HasOpenPosition():             → STATE_GUARD_CHECK
   //=================================================================

   // Phase 1: If somehow here with no position, return to guard
   if(!HasOpenPosition())
   {
      StateManager.Transition(STATE_GUARD_CHECK, "no_position_from_manage");
      return;
   }

   // A320 (P0-2): the full guard chain also runs while a trade is open. The coordinator acts on
   // the result itself (suspend, close_required -> close, fatal -> emergency close).
   GuardEvalResult gr = GuardCoordinator.Evaluate();
   if(gr.status == GUARD_FATAL || gr.status == GUARD_SUSPEND)
      return;

   // A320: the exits that were backtested (doc section 9, research/ea_design_gold.py):
   //   50% off at TP1 (1.5R) + stop to breakeven + $0.20; rest trails 0.75 x ATR(M15),
   //   clamped to [TrailMinPips, TrailMaxPips]; TP2 (2.5R) stays on the order.
   ManageOpenPosition();
}

//--- A320: per-position memory (re-derived after a restart from SL vs entry)
ulong  g_mng_ticket   = 0;
double g_mng_risk     = 0.0;     // initial SL distance (price)
bool   g_mng_half     = false;   // breakeven done (stop at/after entry)
bool   g_mng_partial  = false;   // A336 (#12): the TP1 half-close already went through

//--- A336 (#22): broker distance limit for stop moves = max(stops level, freeze level)
double StopMoveLimit()
{
   double pt  = SymbolInfoDouble(EA_SYMBOL, SYMBOL_POINT);
   long   lvl = SymbolInfoInteger(EA_SYMBOL, SYMBOL_TRADE_STOPS_LEVEL);
   long   fz  = SymbolInfoInteger(EA_SYMBOL, SYMBOL_TRADE_FREEZE_LEVEL);
   return (double)MathMax(lvl, fz) * pt;
}

void ManageOpenPosition()
{
   ulong ticket = GetOpenPositionTicket();
   if(ticket == 0 || !PositionSelectByTicket(ticket)) return;
   double open  = PositionGetDouble(POSITION_PRICE_OPEN);
   double sl    = PositionGetDouble(POSITION_SL);
   double tp    = PositionGetDouble(POSITION_TP);
   double vol   = PositionGetDouble(POSITION_VOLUME);
   bool   longp = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
   int    side  = longp ? 1 : -1;
   if(ticket != g_mng_ticket)
   {
      g_mng_ticket  = ticket;
      g_mng_risk    = MathAbs(open - sl);
      g_mng_half    = (sl > 0 && (sl - open) * side >= 0);     // stop already at/after entry
      g_mng_partial = g_mng_half;
      //--- debug pass 26 Nov: restart between the TP1 half-close and the breakeven move must not
      //    close half AGAIN. An OUT deal already on this position = the half-close went through.
      if(!g_mng_partial && HistorySelectByPosition(ticket))
         for(int d = HistoryDealsTotal() - 1; d >= 0; d--)
         {
            ulong dk = HistoryDealGetTicket(d);
            if(dk != 0 && HistoryDealGetInteger(dk, DEAL_ENTRY) == DEAL_ENTRY_OUT) { g_mng_partial = true; break; }
         }
      if(!PositionSelectByTicket(ticket)) return;               // re-select after the history call
   }
   if(g_mng_risk <= 0 || sl <= 0) return;
   MqlTick tk;
   if(!SymbolInfoTick(EA_SYMBOL, tk)) return;
   double px   = longp ? tk.bid : tk.ask;                    // the price we would close at
   double gain = (px - open) * side;
   double lim  = StopMoveLimit();

   //--- TP1: half off + breakeven
   if(!g_mng_half && (g_mng_partial || gain >= Config.TP1RR * g_mng_risk))
   {
      //--- A336 (#12): the half-close happens ONCE; a failed breakeven modify is retried alone
      if(!g_mng_partial)
      {
         double step = SymbolInfoDouble(EA_SYMBOL, SYMBOL_VOLUME_STEP);
         double vmin = SymbolInfoDouble(EA_SYMBOL, SYMBOL_VOLUME_MIN);
         double half = (step > 0) ? MathFloor(vol / 2.0 / step) * step : vol / 2.0;
         if(half >= vmin && vol - half >= vmin)
         {
            if(!g_mgr.PositionClosePartial(ticket, half) ||
               (g_mgr.ResultRetcode() != TRADE_RETCODE_DONE && g_mgr.ResultRetcode() != TRADE_RETCODE_DONE_PARTIAL))
               { Logger.Warn("MANAGE", StringFormat("partial close failed rc=%d", g_mgr.ResultRetcode())); return; }
            Logger.Info("MANAGE", StringFormat("TP1 hit: half closed (%.2f lots)", half));
         }
         g_mng_partial = true;
      }
      double be = PriceUtils.NormalizePrice(open + side * 0.20);
      if((px - be) * side <= lim) return;                     // A336 (#22): too close for the broker - retry later
      if(g_mgr.PositionModify(ticket, be, tp))
      {
         g_mng_half = true;
         Logger.Info("MANAGE", StringFormat("Stop to breakeven %.2f", be));
      }
      else
         Logger.Warn("MANAGE", StringFormat("breakeven modify failed rc=%d - retrying next tick (no new partial)", g_mgr.ResultRetcode()));
      return;
   }

   //--- trail the rest on each new closed M15 bar
   if(g_mng_half)
   {
      static datetime last_bar = 0;
      datetime bar = iTime(EA_SYMBOL, PERIOD_M15, 1);
      if(bar == 0 || bar == last_bar) return;
      double atr[1];
      if(CopyBuffer(g_atr_m15, 0, 1, 1, atr) != 1) return;
      double dist = Config.TrailAtrMult * atr[0];
      dist = MathMax(PriceUtils.PipsToPrice(Config.TrailMinPips), MathMin(PriceUtils.PipsToPrice(Config.TrailMaxPips), dist));
      double c1 = iClose(EA_SYMBOL, PERIOD_M15, 1);
      double nsl = PriceUtils.NormalizePrice(c1 - side * dist);
      double minmove = PriceUtils.PipsToPrice(TRAIL_STEP_MIN_PIPS) * 0.1;   // $0.50 at 1 pip = $1
      if((nsl - sl) * side > minmove)
      {
         //--- A336 (#22): freeze level too; the bar is marked done only after a successful modify
         if((px - nsl) * side > lim && g_mgr.PositionModify(ticket, nsl, tp))
            last_bar = bar;
      }
      else
         last_bar = bar;                                       // nothing to move on this bar
   }
}

void OnState_Suspended()
{
   // Delegate resume check to coordinator
   // Coordinator identifies the responsible guard and checks its conditions
   GuardCoordinator.CheckResume();

   // A320 (guard audit C1): FastSafetyCheck already ran in OnTick. If a position is still open
   // while suspended (a guard that pauses entries but does not require a close), keep managing it.
   if(StateManager.IsSuspended() && HasOpenPosition())
      ManageOpenPosition();

   // Also: add spread timer sample if we have a valid quote
   // (calibration continues even during suspension)
}

//+------------------------------------------------------------------+
//| TIMER HANDLER — fires every 60 seconds                            |
//+------------------------------------------------------------------+
void OnTimer()
{
   // A336: the timer fires every SECOND. Day rollover (inside OnTimerFire), the safety stops and
   //       the Friday cut run each second; the rest only on the minute tick.
   TimerSystem.OnTimerFire();
   GuardCoordinator.FastSafetyCheck();
   NewsDerisk();                                            // A346
   GuardCoordinator.WeekendRiskCut();
   if(!TimerSystem.IsMinuteTick()) return;

   // Phase 2: Spread calibration sampling (every 60s)
   GuardContext ctx;
   PopulateGuardContext(ctx, Config.MagicNumber, PriceUtils.PipSize());
   double atr_m5 = 0;                                  // A320: real ATR(M5) in pips (P1-1)
   double ab[1];
   if(g_atr_m5 != INVALID_HANDLE && CopyBuffer(g_atr_m5, 0, 1, 1, ab) == 1)
      atr_m5 = PriceUtils.PriceToPips(ab[0]);
   if(!MSNR.IsReady()) MSNR.Init();
   SpreadGuard.OnTimerSample(ctx, atr_m5);

   // Phase 2: Guard coordinator cache invalidation (ensure fresh eval)
   GuardCoordinator.InvalidateCache();

   // Phase 7: RetryManager.ProcessQueue() will go here
   // Phase 7: VPSHandler.CheckConnection() will go here
   // Phase 8: PerformanceMonitor.UpdateStats() will go here
   // Phase 8: Dashboard.Refresh() will go here
}

//+------------------------------------------------------------------+
//| TRADE TRANSACTION HANDLER                                          |
//| Fires when MT5 reports a change in order/position/deal state      |
//+------------------------------------------------------------------+
void OnTradeTransaction(
   const MqlTradeTransaction &trans,
   const MqlTradeRequest     &request,
   const MqlTradeResult      &result)
{
   // Phase 5: BrokerRejectionHandler will process failed transactions
   // Phase 6: TradeManager will process position changes
   // Phase 7: Recovery will detect unexpected closures

   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   MixEngine.OnTransaction(trans);                       // A327: mix streak sizing (own magics)
   Logger.Debug("TRANSACTION",
      StringFormat("Deal added: type=%s symbol=%s volume=%.2f price=%.5f",
                   EnumToString(trans.deal_type), trans.symbol, trans.volume, trans.price));

   //=================================================================
   // A320 (P0-3): feed every guard that counts trades. Before this,
   // DailyStats.OnTradeOpen/OnTradeClose had no callers, so the daily
   // loss limit, max 3 trades, 3-loss pause and cooldown never fired.
   // Partial closes are summed; the trade is "closed" when the
   // position is gone.
   //=================================================================
   if(trans.deal == 0 || !HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) != EA_SYMBOL) return;
   long   magic = HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
   if(!IsOurMagic(magic)) return;                       // A336 (#18): daily limits count ALL our magics
   bool   main_magic = (magic == Config.MagicNumber);
   long   entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   ulong  pos   = (ulong)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);

   if(entry == DEAL_ENTRY_IN)
   {
      if(main_magic)
      {
         g_txn_pos  = pos;
         double sl  = 0.0;
         if(PositionSelectByTicket(pos)) sl = PositionGetDouble(POSITION_SL);
         double vol = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);
         double tv  = SymbolInfoDouble(EA_SYMBOL, SYMBOL_TRADE_TICK_VALUE);
         double ts  = SymbolInfoDouble(EA_SYMBOL, SYMBOL_TRADE_TICK_SIZE);
         double px  = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
         g_txn_risk = (sl > 0 && ts > 0) ? MathAbs(px - sl) / ts * tv * vol : 0.0;
      }
      if(main_magic) DailyStats.OnTradeOpen();          // A347: the 3-trades/day cap is for the main strategy only
      long dt = HistoryDealGetInteger(trans.deal, DEAL_TYPE);
      GuardPropFirm.RecordTradeDirection(dt == DEAL_TYPE_BUY ? DIR_LONG : DIR_SHORT);
      return;
   }
   if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY || entry == DEAL_ENTRY_INOUT)
   {
      if(PositionSelectByTicket(pos)) return;          // partial close — wait for the rest
      //--- A336 (#18): whole-position P&L from history (several positions can be open at once)
      double pnl = 0.0, mix_risk = 0.0;
      if(HistorySelectByPosition(pos))
      {
         int nd = HistoryDealsTotal();
         for(int d = 0; d < nd; d++)
         {
            ulong dk = HistoryDealGetTicket(d);
            if(dk == 0) continue;
            pnl += HistoryDealGetDouble(dk, DEAL_PROFIT) + HistoryDealGetDouble(dk, DEAL_SWAP)
                 + HistoryDealGetDouble(dk, DEAL_COMMISSION);
            if(HistoryDealGetInteger(dk, DEAL_ENTRY) == DEAL_ENTRY_IN)
            {
               string parts[];
               if(StringSplit(HistoryDealGetString(dk, DEAL_COMMENT), StringGetCharacter("|", 0), parts) >= 2)
                  mix_risk = StringToDouble(parts[1]);
            }
         }
      }
      double risk = main_magic ? ((pos == g_txn_pos) ? g_txn_risk : 0.0) : mix_risk;
      double rr = (risk > 0) ? pnl / risk : 0.0;
      if(main_magic)
      {
         DailyStats.OnTradeClose(pnl, rr);
         GuardCooldown.OnTradeClosed(TimeCurrent());
      }
      else
         DailyStats.OnMixTradeClose(pnl);                  // A347: day P&L only, no streak/cooldown for the mix
      if(main_magic)
      {
         g_last_trade_r = (risk > 0) ? rr : (pnl > 0 ? 1.0 : -1.0);   // A325 streak sizing
         g_txn_pos = 0; g_txn_risk = 0.0;
      }
      Logger.Info("TRANSACTION", StringFormat("Trade closed pos=%I64u magic=%I64d pnl=%.2f R=%.2f", pos, magic, pnl, rr));
   }
}

//+------------------------------------------------------------------+
//| DEINIT HANDLER — EA is being removed or chart closed              |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Logger.Info("DEINIT",
      StringFormat("EA deinit called — reason=%d (%s)",
                   reason, GetDeInitReasonString(reason)));

   // Phase 3: Intelligence layer shutdown (release indicator handles)
   // Coordinator does NOT shut down engines — main EA owns lifecycle.
   IntelligenceCoordinator.Shutdown();
   EntryEngine.Shutdown();          // No handles — diagnostics only
   TradeCalculator.Shutdown();
   PositionSizer.Shutdown();
   TradeScorer.Shutdown();          // No handles — diagnostics only
   TrendEngine.Shutdown();          // Releases iMA H1 handles
   RegimePersistenceModel.Shutdown(); // Saves state to disk
   LiquidityEngine.Shutdown();      // No handles — clean state only
   RegimeEngine.Shutdown();         // Releases iMA handles
   VolatilityEngine.Shutdown();     // Releases iATR handles
   StructureEngine.Shutdown();      // No handles — clean state only

   // Phase 2: Guard layer shutdown (save persistent states)
   GuardCoordinator.Shutdown();
   SpreadGuard.Shutdown();
   GuardCircuitBrk.Shutdown();
   GuardCooldown.Shutdown();
   GuardNews.SaveState();

   // A336 (#28): release the indicator handles owned here and by the mix engine
   if(g_atr_m5  != INVALID_HANDLE) { IndicatorRelease(g_atr_m5);  g_atr_m5  = INVALID_HANDLE; }
   if(g_atr_m15 != INVALID_HANDLE) { IndicatorRelease(g_atr_m15); g_atr_m15 = INVALID_HANDLE; }
   MixEngine.Shutdown();

   // A336 (#7): release the single-instance lock
   if(g_lock_owner)
   {
      string lock = StringFormat("EAX_LOCK_%I64d", inp_MagicNumber);
      if(GlobalVariableCheck(lock) && GlobalVariableGet(lock) == (double)(ChartID() & 0xFFFFFFFFFFFF)) GlobalVariableDel(lock);
      g_lock_owner = false;
   }

   // Shutdown in reverse order of init
   TimerSystem.Shutdown();

   // Flush all pending writes to disk
   Persistence.Flush();
   Logger.Flush();

   // Final log line (goes to Experts tab since logger is shutting down)
   Logger.Info("DEINIT", "=== EA SHUTDOWN COMPLETE ===");
   Logger.Shutdown();
}

//+------------------------------------------------------------------+
//| UTILITY HELPERS                                                    |
//+------------------------------------------------------------------+

//--- Check if EA's own position is currently open
bool HasOpenPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == EA_SYMBOL &&
         PositionGetInteger(POSITION_MAGIC) == Config.MagicNumber)
         return true;
   }
   return false;
}

//--- Get the EA's open position ticket (0 if none)
ulong GetOpenPositionTicket()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == EA_SYMBOL &&
         PositionGetInteger(POSITION_MAGIC) == Config.MagicNumber)
         return ticket;
   }
   return 0;
}

//--- A336 (#29): main-strategy streak sizing after a restart = sign of its last closed trade
void RebuildMainStreak()
{
   if(!HistorySelect(TimeCurrent() - 60 * 86400, TimeCurrent() + 60)) return;
   datetime last_t = 0;
   int total = HistoryDealsTotal();
   for(int d = 0; d < total; d++)
   {
      ulong dk = HistoryDealGetTicket(d);
      if(dk == 0) continue;
      if(HistoryDealGetInteger(dk, DEAL_MAGIC) != Config.MagicNumber) continue;
      long en = HistoryDealGetInteger(dk, DEAL_ENTRY);
      if(en != DEAL_ENTRY_OUT && en != DEAL_ENTRY_OUT_BY) continue;
      datetime t = (datetime)HistoryDealGetInteger(dk, DEAL_TIME);
      if(t < last_t) continue;
      last_t = t;
      double pnl = HistoryDealGetDouble(dk, DEAL_PROFIT) + HistoryDealGetDouble(dk, DEAL_SWAP)
                 + HistoryDealGetDouble(dk, DEAL_COMMISSION);
      g_last_trade_r = (pnl > 0) ? 1.0 : -1.0;
   }
}

//--- Convert deinit reason code to human-readable string
string GetDeInitReasonString(int reason)
{
   switch(reason)
   {
      case REASON_PROGRAM:     return "PROGRAM";
      case REASON_REMOVE:      return "REMOVED_FROM_CHART";
      case REASON_RECOMPILE:   return "RECOMPILED";
      case REASON_CHARTCHANGE: return "CHART_SYMBOL_CHANGED";
      case REASON_CHARTCLOSE:  return "CHART_CLOSED";
      case REASON_PARAMETERS:  return "INPUT_PARAMS_CHANGED";
      case REASON_ACCOUNT:     return "ACCOUNT_CHANGED";
      case REASON_TEMPLATE:    return "TEMPLATE_APPLIED";
      case REASON_INITFAILED:  return "INIT_FAILED";
      case REASON_CLOSE:       return "TERMINAL_CLOSED";
      default: return StringFormat("UNKNOWN(%d)", reason);
   }
}

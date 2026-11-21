
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
#include "Scoring/CTradeScorer.mqh"
#include "Execution/CPositionSizer.mqh"
#include "Execution/CTradeCalculator.mqh"
#include "Execution/CEntryEngine.mqh"
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

   // --- Step 2: Validate we are on the correct symbol
   if(Symbol() != EA_SYMBOL)
   {
      Logger.Fatal("INIT",
         StringFormat("Wrong symbol: running on %s, required %s",
                      Symbol(), EA_SYMBOL));
      return INIT_FAILED;
   }

   // --- Step 3: Validate account type (must be able to hedge)
   ENUM_ACCOUNT_MARGIN_MODE margin_mode =
      (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   if(margin_mode == ACCOUNT_MARGIN_MODE_RETAIL_NETTING)
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
   GuardCoordinator.RegisterGuard(&GuardSession,     5);
   GuardCoordinator.RegisterGuard(&GuardRollover,    6);
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

   // --- Update equity tracking every tick
   DailyStats.UpdateEquity(AccountInfoDouble(ACCOUNT_EQUITY));

   // --- Terminal states: do nothing
   if(StateManager.IsTerminal())
      return;

   // --- Stale price guard
   if(TimerSystem.IsPriceStale())
   {
      // Phase 7 will handle VPS disconnect properly
      // For Phase 1: just don't execute on stale data
      return;
   }

   // --- Phase 3: Update intelligence layer
   // Fast on most ticks (bar boundary check + early return).
   // Slow path only on bar closes (engines run, packet rebuilt).
   IntelligenceCoordinator.Update();

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
         // Terminal — do nothing until manual restart
         break;

      case STATE_FATAL_ERROR:
         // Terminal — do nothing
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
   // Position management stub — will be replaced in Phase 6
}

void OnState_Suspended()
{
   // Delegate resume check to coordinator
   // Coordinator identifies the responsible guard and checks its conditions
   GuardCoordinator.CheckResume();

   // Also: add spread timer sample if we have a valid quote
   // (calibration continues even during suspension)
}

//+------------------------------------------------------------------+
//| TIMER HANDLER — fires every 60 seconds                            |
//+------------------------------------------------------------------+
void OnTimer()
{
   TimerSystem.OnTimerFire();

   // Phase 2: Spread calibration sampling (every 60s)
   GuardContext ctx;
   PopulateGuardContext(ctx, Config.MagicNumber, PriceUtils.PipSize());
   double atr_m5 = 0; // Phase 3 will provide real ATR — stub for now
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

   // Phase 1: Log significant transactions only
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      Logger.Debug("TRANSACTION",
         StringFormat("Deal added: type=%s symbol=%s volume=%.2f price=%.5f",
                      EnumToString(trans.deal_type),
                      trans.symbol,
                      trans.volume,
                      trans.price));
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

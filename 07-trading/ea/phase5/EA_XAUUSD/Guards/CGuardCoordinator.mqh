
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Guard Coordinator                       |
//| File: Guards/CGuardCoordinator.mqh                                |
//| Purpose: Central authority for all guard evaluation.              |
//|           Enforces deterministic order, fail-fast behavior,       |
//|           suspension routing, and emergency close logic.          |
//| Phase: 2 — Guard Layer / Step 2                                   |
//|                                                                    |
//| CRITICAL DESIGN RULES:                                            |
//|   1. This class contains NO trading logic                         |
//|   2. This class contains NO market analysis                       |
//|   3. It routes results — it does not produce them                 |
//|   4. State transitions ONLY through CStateManager                 |
//|   5. Emergency close is the ONLY broker action here               |
//|   6. Evaluation chain stops on first non-PASS result              |
//|   7. Same context input ALWAYS produces same routing output       |
//+------------------------------------------------------------------+
#ifndef CGUARDCOORDINATOR_MQH
#define CGUARDCOORDINATOR_MQH

#include "../Include/Defines.mqh"
#include "../Include/PriceUtils.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "../Core/CStateManager.mqh"
#include "../Core/CDailyStats.mqh"
#include "GuardTypes.mqh"

//--- Forward declarations for guard modules (implemented in later steps)
//    These will be replaced with actual includes as each step is built.
//    For Step 2: coordinator compiles with stub guard pointers.
class IGuard;  // Base interface from GuardTypes.mqh

//===================================================================
// EVALUATION THROTTLE
//
// PSEUDO-CODE RATIONALE:
//   OnTick() fires on every price change — potentially 10–50 per second
//   on XAUUSD during active sessions. Running the full guard chain
//   (10 guards, each with checks) on every single tick is wasteful
//   AND dangerous — it invites subtle timing bugs where guard state
//   changes between ticks during the same "logical moment".
//
//   THROTTLE RULE:
//     Full evaluation chain: maximum once per 200ms
//     (5 evaluations per second maximum)
//     Exception: FATAL conditions bypass throttle — always evaluated
//
//   The throttle does NOT apply when:
//     - EA is in STATE_SUSPENDED (must check resume conditions)
//     - PropFirmGuard equity check (account survival — always live)
//     - First tick after trade close (immediate re-evaluation needed)
//
//   Implementation: compare TimeCurrent() + GetMicrosecondCount()
//   MQL5 GetMicrosecondCount() returns microseconds since terminal start.
//   We track last_eval_microseconds and compare delta.
//===================================================================
#define EVAL_THROTTLE_MS  200   // Minimum ms between full evaluations
#define EQUITY_CHECK_MS   100   // Equity-only check can run faster

//===================================================================
// GUARD SLOT COUNT
//===================================================================
#define GUARD_COUNT 10

// A336: inp_PropDailyStopPct moved to Core/CConfig.mqh (capped by the firm limit as Config.DailyStopPct)

class CGuardCoordinator
{
private:
   //--- Guard registry (pointers — guards owned externally, registered here)
   IGuard*       m_guards[GUARD_COUNT];
   GuardMetadata m_meta[GUARD_COUNT];
   bool          m_initialized;

   //--- Last evaluation tracking
   GuardEvalResult m_last_result;
   datetime        m_last_eval_time;
   ulong           m_last_eval_microsec;
   int             m_eval_count;
   int             m_chain_stopped_at[GUARD_COUNT]; // How often each guard stopped chain

   //--- Duplicate transition prevention
   SUSPEND_REASON  m_last_suspend_reason;
   bool            m_suspend_logged;

   //--- Emergency close state
   bool            m_emergency_close_attempted;
   datetime        m_emergency_close_time;
   int             m_emergency_close_retries;

   //--- Manual suspend state (read from Config each tick)
   bool            m_manual_suspend_active;

   //=================================================================
   // INTERNAL: Execute the evaluation chain
   // Context must be pre-populated by caller.
   // Returns the first non-PASS result, or PASS if all 10 pass.
   //=================================================================
   GuardEvalResult RunEvaluationChain(const GuardContext &ctx)
   {
      // Check manual suspend first — before any guard
      if(Config.ManualSuspend)
      {
         if(!m_manual_suspend_active)
         {
            m_manual_suspend_active = true;
            Logger.Warn("GUARD_COORD",
               "Manual suspend activated via config input");
         }
         return GuardSuspend(GPRIO_SYSTEM_HEALTH, "MANUAL", 0,
                             SUSPEND_MANUAL,
                             "inp_ManualSuspend=true",
                             "Set inp_ManualSuspend=false + restart EA");
      }
      else
      {
         if(m_manual_suspend_active)
         {
            m_manual_suspend_active = false;
            Logger.Info("GUARD_COORD", "Manual suspend cleared");
         }
      }

      // Run guards in strict priority order
      for(int i = 0; i < GUARD_COUNT; i++)
      {
         if(m_guards[i] == NULL)
         {
            // Guard not yet registered (expected during phased build)
            // Log at DEBUG only — not an error during development
            Logger.Debug("GUARD_COORD",
               StringFormat("Guard slot %d not registered — skipping", i+1));
            continue;
         }

         if(!m_guards[i].IsEnabled())
         {
            Logger.Debug("GUARD_COORD",
               StringFormat("Guard %s disabled — skipping",
                            m_guards[i].GetName()));
            continue;
         }

         if(!m_guards[i].IsInitialized())
         {
            // Uninitialised guard in the chain is a fatal infrastructure error
            Logger.Fatal("GUARD_COORD",
               StringFormat("Guard %s not initialized — EA cannot operate safely",
                            m_guards[i].GetName()));
            return GuardFatal(GPRIO_SYSTEM_HEALTH, "GUARD_COORD", i+1,
                              SUSPEND_SYSTEM_HEALTH,
                              StringFormat("Uninitialized guard at slot %d: %s",
                                           i+1, m_guards[i].GetName()));
         }

         // Evaluate this guard
         GuardEvalResult result = m_guards[i].Evaluate(ctx);
         result.guard_index = i + 1;
         m_meta[i].eval_count++;

         if(result.status == GUARD_PASS)
         {
            // Accumulate size reduction if guard requests it
            if(result.size_reduced)
            {
               m_last_result.size_reduced     = true;
               m_last_result.size_multiplier  =
                  MathMin(m_last_result.size_multiplier, result.size_multiplier);
            }
            continue; // Move to next guard
         }

         // Non-PASS: record stop point and return immediately
         m_chain_stopped_at[i]++;
         m_meta[i].last_trigger = TimeCurrent();

         switch(result.status)
         {
            case GUARD_BLOCK:   m_meta[i].block_count++;   break;
            case GUARD_SUSPEND: m_meta[i].suspend_count++; break;
            case GUARD_FATAL:   m_meta[i].fatal_count++;   break;
            default: break;
         }

         return result;
      }

      // All guards passed
      return m_last_result; // Contains accumulated size modifiers
   }

   //=================================================================
   // INTERNAL: Act on a non-PASS result
   // This is where StateManager transitions happen.
   // The ONLY place in the guard layer that changes EA state.
   //=================================================================
   void ActOnResult(const GuardEvalResult &result)
   {
      switch(result.status)
      {
         //------------------------------------------------------------
         case GUARD_BLOCK:
            // BLOCK: no state change. EA stays in GUARD_CHECK.
            // Log only if this is a NEW block (not same reason as before)
            if(result.suspend_reason != m_last_suspend_reason ||
               !m_suspend_logged)
            {
               Logger.Debug("GUARD_COORD",
                  StringFormat("BLOCK from %s", result.guard_name),
                  StringFormat("detail=%s", result.detail));
               m_last_suspend_reason = result.suspend_reason;
               m_suspend_logged = true;
            }
            break;

         //------------------------------------------------------------
         case GUARD_SUSPEND:
         {
            // SPECIAL CASE: PROFIT_TARGET is a terminal state, not a suspension
            if(result.suspend_reason == SUSPEND_PROFIT_TARGET)
            {
               if(result.close_required)
                  CloseOpenPositionSafely("profit_target_close");
               Logger.Info("GUARD_COORD",
                  "CHALLENGE PROFIT TARGET REACHED — transitioning to terminal state");
               Alert(EA_NAME, ": CHALLENGE TARGET REACHED — EA suspending permanently.");
               StateManager.Transition(STATE_PROFIT_TARGET, "profit_target_guard");
               return;
            }

            SuspendDescriptor desc = GetSuspendDescriptor(result.suspend_reason);

            // Prevent duplicate suspension transitions
            if(StateManager.IsSuspended() &&
               StateManager.GetSuspendReason() == result.suspend_reason)
            {
               // Already suspended for this reason — don't log again
               break;
            }

            // Execute close if required BEFORE state transition
            if(result.close_required)
            {
               Logger.Critical("GUARD_COORD",
                  StringFormat("SUSPEND with close_required — closing position. "
                               "Guard=%s reason=%s",
                               result.guard_name,
                               desc.name));
               CloseOpenPositionSafely("suspend_close:" + result.guard_name);
            }

            if(result.cancel_pending)
               CancelAllPendingOrders("suspend_cancel:" + result.guard_name);

            // Log at appropriate severity
            Logger.Write(desc.severity, "GUARD_COORD",
               StringFormat("SUSPEND triggered by %s", result.guard_name),
               StringFormat("reason=%s detail=%s resume=%s",
                            desc.name, result.detail,
                            result.resume_condition));

            // Transition state
            StateManager.Suspend(result.suspend_reason,
               result.guard_name + ": " + result.detail);

            // Alert if required
            if(result.alert_trader || desc.alert_trader)
            {
               Alert(EA_NAME, " SUSPENDED: ", desc.name,
                     " — ", result.detail);
            }

            m_last_suspend_reason = result.suspend_reason;
            m_suspend_logged = true;
            break;
         }

         //------------------------------------------------------------
         case GUARD_FATAL:
         {
            Logger.Fatal("GUARD_COORD",
               StringFormat("FATAL result from %s", result.guard_name),
               StringFormat("reason=%s detail=%s",
                            EnumToString(result.suspend_reason),
                            result.detail));

            // Close position before halting
            if(result.close_required)
            {
               Logger.Critical("GUARD_COORD",
                  "FATAL: executing emergency close before halt");
               EmergencyCloseAll("fatal:" + result.guard_name);
            }

            if(result.cancel_pending)
               CancelAllPendingOrders("fatal_cancel");

            // Always alert on fatal
            Alert(EA_NAME, " FATAL ERROR: ", result.detail);

            // Terminal state — no recovery
            StateManager.Transition(STATE_FATAL_ERROR,
               "fatal_guard:" + result.guard_name);
            break;
         }

         default:
            break;
      }
   }

   //=================================================================
   // INTERNAL: Close open position safely (single attempt)
   // Returns true if closed successfully or no position to close.
   // Retry logic handled by RetryManager (Phase 7).
   // For Phase 2: up to 3 direct attempts with 2-second gaps.
   //=================================================================
   //--- A327 + guard audit C3: close EVERY position of ours (EA + mix), not just the first one found
   bool CloseOpenPositionSafely(string reason)
   {
      bool ok = true;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong t = PositionGetTicket(i);
         if(t == 0) continue;
         if(PositionGetString(POSITION_SYMBOL) != EA_SYMBOL) continue;
         if(!IsOurMagic(PositionGetInteger(POSITION_MAGIC))) continue;
         if(!ClosePositionByTicket(t, reason)) ok = false;
      }
      if(!ok) Logger.Error("GUARD_COORD", "CloseOpenPositionSafely: some positions did not close — " + reason);
      return ok;
   }

   //=================================================================
   // INTERNAL: Emergency close ALL positions with our magic number
   //=================================================================
   void EmergencyCloseAll(string reason)
   {
      if(m_emergency_close_attempted)
      {
         // Prevent duplicate emergency close calls in same session
         if(TimeCurrent() - m_emergency_close_time < 5)
         {
            Logger.Warn("GUARD_COORD",
               "EmergencyCloseAll called again within 5s — skipping duplicate");
            return;
         }
      }

      m_emergency_close_attempted = true;
      m_emergency_close_time      = TimeCurrent();

      Logger.Critical("GUARD_COORD",
         StringFormat("EMERGENCY CLOSE ALL — reason=%s", reason));

      int closed = 0;
      int failed = 0;

      // Iterate backwards (safe when closing modifies position list)
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0) continue;
         if(PositionGetString(POSITION_SYMBOL) != EA_SYMBOL) continue;
         if(!IsOurMagic(PositionGetInteger(POSITION_MAGIC))) continue;   // A327: EA + mix

         if(ClosePositionByTicket(ticket, reason))
            closed++;
         else
            failed++;
      }

      Logger.Critical("GUARD_COORD",
         StringFormat("Emergency close complete. closed=%d failed=%d",
                      closed, failed));

      //--- debug pass 26 Nov: market closed -> this repeats every 5 s; pop the Alert at most every 10 min
      static datetime last_alert = 0;
      if(failed > 0 && (last_alert == 0 || TimeCurrent() - last_alert >= 600))
      {
         last_alert = TimeCurrent();
         Alert(EA_NAME, " WARNING: ", failed,
               " position(s) could not be closed. Manual action required.");
      }
   }

   //--- Close a single position by ticket
   //--- A320 (guard audit C2): fresh tick each try, a filling mode the symbol accepts,
   //    deviation in real points, 3 tries; an emergency close may slip — it must not fail.
   bool ClosePositionByTicket(ulong ticket, string reason)
   {
      for(int attempt = 1; attempt <= 3; attempt++)
      {
         if(!PositionSelectByTicket(ticket)) return true;          // already gone = closed

         MqlTradeRequest req;
         MqlTradeResult  res;
         MqlTick         tk;
         ZeroMemory(req);
         ZeroMemory(res);
         req.action    = TRADE_ACTION_DEAL;
         req.position  = ticket;
         req.symbol    = PositionGetString(POSITION_SYMBOL);
         req.volume    = PositionGetDouble(POSITION_VOLUME);
         req.type      = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
                         ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
         if(!SymbolInfoTick(req.symbol, tk)) { Sleep(200); continue; }
         req.price     = (req.type == ORDER_TYPE_SELL) ? tk.bid : tk.ask;
         long fill     = SymbolInfoInteger(req.symbol, SYMBOL_FILLING_MODE);
         req.type_filling = ((fill & SYMBOL_FILLING_FOK) != 0) ? ORDER_FILLING_FOK
                          : (((fill & SYMBOL_FILLING_IOC) != 0) ? ORDER_FILLING_IOC : ORDER_FILLING_RETURN);
         req.deviation = (ulong)MathMax(50.0, MathRound(Config.PipsToPoints(Config.SlippageMax) * 4));
         req.magic     = (ulong)PositionGetInteger(POSITION_MAGIC);   // review 26 Nov: keep the position's own magic (mix streaks)
         req.comment   = "emergency_" + reason;

         bool ok = OrderSend(req, res);
         if(ok && (res.retcode == TRADE_RETCODE_DONE || res.retcode == TRADE_RETCODE_DONE_PARTIAL))
         {
            if(!PositionSelectByTicket(ticket)) return true;
         }
         Logger.Error("GUARD_COORD",
            StringFormat("CloseByTicket try %d failed. ticket=%llu retcode=%d", attempt, ticket, res.retcode));
         Sleep(300);
      }
      return !PositionSelectByTicket(ticket);
   }


   //--- Cancel all pending orders with our magic number
   void CancelAllPendingOrders(string reason)
   {
      for(int i = OrdersTotal() - 1; i >= 0; i--)
      {
         ulong ticket = OrderGetTicket(i);
         if(ticket == 0) continue;
         if(OrderGetString(ORDER_SYMBOL) != EA_SYMBOL) continue;
         if(!IsOurMagic(OrderGetInteger(ORDER_MAGIC))) continue;         // A327: EA + mix

         MqlTradeRequest req;
         MqlTradeResult  res;
         ZeroMemory(req);
         ZeroMemory(res);
         req.action = TRADE_ACTION_REMOVE;
         req.order  = ticket;

         if(OrderSend(req, res))
            Logger.Info("GUARD_COORD",
               StringFormat("Pending order cancelled. ticket=%llu reason=%s",
                            ticket, reason));
         else
            Logger.Error("GUARD_COORD",
               StringFormat("Cancel failed. ticket=%llu retcode=%d",
                            ticket, res.retcode));
      }
   }

   //--- Check whether throttle window has elapsed
   bool IsThrottleElapsed()
   {
      ulong now_us = GetMicrosecondCount();
      ulong delta_ms = (now_us - m_last_eval_microsec) / 1000;
      return (delta_ms >= EVAL_THROTTLE_MS);
   }

public:
   //===================================================================
   // A320 (P0-2, guard audit C1/H8): FAST SAFETY CHECK — every tick in
   // MANAGE_TRADE and SUSPENDED, not only in GUARD_CHECK.
   //   1. equity <= floor            -> close all, fatal lock
   //   2. The5%ers 5% daily loss: equity below day-open equity by
   //      inp_PropDailyStopPct (default 4%, 1% buffer) -> close all,
   //      suspend until the next day.
   // Returns false when it acted.
   //===================================================================
   //   A336: runs in EVERY state, terminal ones included (#5). The day base is
   //   MathMax(balance, equity) at 00:00 server (#8/G1); stop = Config.DailyStopPct.
   bool FastSafetyCheck()
   {
      double eq = AccountInfoDouble(ACCOUNT_EQUITY);
      // Review fix: equity 0 = account data not loaded yet (OnTimer can fire before login);
      // acting on it would close everything and latch FATAL. Nothing can be sent anyway.
      if(eq <= 0.0) return true;
      bool terminal = StateManager.IsTerminal();
      if(eq <= FloorNow())
      {
         if(!terminal)
         {
            GuardEvalResult fatal = GuardFatal(GPRIO_PROP_FIRM, "EQUITY_FAST_CHECK", 0,
               SUSPEND_PROP_FIRM_LOCK,
               StringFormat("equity=%.2f <= floor=%.2f", eq, Config.EquityFloor), true);
            ActOnResult(fatal);
         }
         if(HasAnyOurPosition()) EmergencyCloseAll("equity_floor");
         CancelAllPendingOrders("equity_floor");
         return false;
      }
      double day_base = DailyStats.GetDayBase();
      if(day_base > 0 && eq <= day_base * (1.0 - Config.DailyStopPct / 100.0))
      {
         if(HasAnyOurPosition()) EmergencyCloseAll("daily_loss_buffer");
         CancelAllPendingOrders("daily_loss_buffer");
         DailyStats.ForceDailyLimit(StringFormat("equity %.2f vs day base %.2f", eq, day_base));
         if(!terminal && !StateManager.IsSuspended())
            StateManager.Suspend(SUSPEND_DAILY_LIMIT,
               StringFormat("equity=%.2f day_base=%.2f stop=%.1f%%", eq, day_base, Config.DailyStopPct));
         return false;
      }
      //--- A337 (E8 Pro): only inp_DailyProfitCapPct of the initial balance per day counts toward target/payout,
      //    so once the day is that far up, bank it: close all and stop for the day.
      //    E8 measures the cap from the day's START BALANCE (help centre: day starts at $101,000 ->
      //    cap limit $103,000), so floating profit carried over midnight must not raise our line.
      double cap_base = DailyStats.GetStartBalance();
      if(cap_base <= 0.0) cap_base = day_base;
      if(inp_DailyProfitCapPct > 0.0 && cap_base > 0 &&
         eq >= cap_base + inp_DailyProfitCapPct / 100.0 * inp_AccountSize)
      {
         if(HasAnyOurPosition()) EmergencyCloseAll("daily_profit_cap");
         CancelAllPendingOrders("daily_profit_cap");
         DailyStats.ForceDailyLimit(StringFormat("profit cap: equity %.2f vs day base %.2f", eq, day_base));
         if(!terminal && !StateManager.IsSuspended())
            StateManager.Suspend(SUSPEND_DAILY_LIMIT,
               StringFormat("daily profit cap %.1f%% reached", inp_DailyProfitCapPct));
         return false;
      }
      return true;
   }

   //--- A336: any open position of ours (EA + mix magics)?
   bool HasAnyOurPosition()
   {
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong t = PositionGetTicket(i);
         if(t == 0) continue;
         if(PositionGetString(POSITION_SYMBOL) != EA_SYMBOL) continue;
         if(IsOurMagic(PositionGetInteger(POSITION_MAGIC))) return true;
      }
      return false;
   }

   //--- A336 (#5): public flatten for terminal states (PROFIT_TARGET keeps retrying every 5 s)
   bool CloseAllOurPositions(string reason)
   {
      static datetime last_try = 0;
      if(last_try != 0 && TimeCurrent() - last_try < 5) return false;
      last_try = TimeCurrent();
      return CloseOpenPositionSafely(reason);
   }

   void CancelAllOurPendings(string reason) { CancelAllPendingOrders(reason); }

   //--- A336 (#2): remaining risk of one selected position if its stop is hit.
   //    SL = 0 counts as 1% of equity; a stop at/beyond entry (profit locked) counts 0.
   double SelectedPositionRisk(double vpp)
   {
      double sl  = PositionGetDouble(POSITION_SL);
      double op  = PositionGetDouble(POSITION_PRICE_OPEN);
      double cur = PositionGetDouble(POSITION_PRICE_CURRENT);
      double vol = PositionGetDouble(POSITION_VOLUME);
      int side   = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 1 : -1;
      if(sl <= 0) return AccountInfoDouble(ACCOUNT_EQUITY) * 0.01;
      if((sl - op) * side >= 0) return 0.0;                       // stop at/beyond entry
      double d = (cur - sl) * side;                               // distance still to lose
      if(d <= 0) return 0.0;
      return d * vol * vpp;
   }

   //--- A336 (#2 CRITICAL): weekend gap protection. Friday from inp_FridayCutHour (server):
   //    cancel all our pendings; if total open risk > inp_FridayMaxOpenRiskPct of equity,
   //    close losing positions first (largest risk first), then the largest risk, until under.
   //    Then the lot-based gap check: worst case per position = max(SL risk, inp_WeekendGapPct
   //    of price x volume), stop assumed jumped; close losers first, then the largest volume,
   //    until the sum <= inp_WeekendLossBudgetPct x max(balance, equity).
   //    Called every tick and every second; runs at most every 10 s. New entries are blocked
   //    by WeekendCutActive() until Monday.
   void WeekendRiskCut()
   {
      if(!WeekendCutActive()) return;
      if(ServerDayOfWeek() != 5) return;                           // market closed Sat/Sun: nothing to send
      static datetime last_run = 0;
      if(last_run != 0 && TimeCurrent() - last_run < 10) return;
      last_run = TimeCurrent();

      CancelAllPendingOrders("friday_cut");

      double tv  = SymbolInfoDouble(EA_SYMBOL, SYMBOL_TRADE_TICK_VALUE);
      double ts  = SymbolInfoDouble(EA_SYMBOL, SYMBOL_TRADE_TICK_SIZE);
      double vpp = (ts > 0) ? tv / ts : 0.0;
      if(vpp <= 0) { Logger.Error("GUARD_COORD", "Friday cut: no tick value - closing all"); CloseOpenPositionSafely("friday_cut_no_tickvalue"); return; }
      double cap    = AccountInfoDouble(ACCOUNT_EQUITY) * inp_FridayMaxOpenRiskPct / 100.0;
      //--- lot-based gap budget: assume the weekend gap JUMPS every stop
      double budget = MathMax(AccountInfoDouble(ACCOUNT_BALANCE), AccountInfoDouble(ACCOUNT_EQUITY))
                    * inp_WeekendLossBudgetPct / 100.0;

      for(int guard = 0; guard < 50; guard++)
      {
         double total = 0.0, worst_total = 0.0, best_loss_risk = -1.0, best_risk = -1.0;
         double best_loss_vol = -1.0, best_vol = -1.0;
         ulong  best_loss_tk = 0, best_tk = 0, gap_loss_tk = 0, gap_vol_tk = 0;
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            ulong t = PositionGetTicket(i);
            if(t == 0) continue;
            if(PositionGetString(POSITION_SYMBOL) != EA_SYMBOL) continue;
            if(!IsOurMagic(PositionGetInteger(POSITION_MAGIC))) continue;
            double r   = SelectedPositionRisk(vpp);
            double vol = PositionGetDouble(POSITION_VOLUME);
            double cur = PositionGetDouble(POSITION_PRICE_CURRENT);
            // worst case = max(SL risk, gap% x price x volume x value per price unit); profit is NOT a cushion
            double gap_loss = inp_WeekendGapPct / 100.0 * cur * vol * vpp;
            worst_total += MathMax(r, gap_loss);
            total += r;
            double pl = PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
            if(pl < 0 && vol > best_loss_vol) { best_loss_vol = vol; gap_loss_tk = t; }
            if(vol > best_vol)                { best_vol = vol;      gap_vol_tk  = t; }
            if(r <= 0) continue;
            if(pl < 0 && r > best_loss_risk) { best_loss_risk = r; best_loss_tk = t; }
            if(r > best_risk) { best_risk = r; best_tk = t; }
         }
         ulong pick = 0;
         string rule = "";
         if(total > cap)                       // stop-risk cap: losers first (largest risk), then largest risk
         {
            pick = (best_loss_tk != 0) ? best_loss_tk : best_tk;
            rule = "stop_risk_cap";
         }
         else if(worst_total > budget)         // gap budget: losers first (largest volume), then largest volume
         {
            pick = (gap_loss_tk != 0) ? gap_loss_tk : gap_vol_tk;
            rule = "gap_budget";
         }
         if(pick == 0) return;
         Logger.Warn("GUARD_COORD", "Friday cut: weekend exposure too high - closing a position",
            StringFormat("rule=%s open_risk=%.2f cap=%.2f worst_gap_loss=%.2f budget=%.2f ticket=%I64u",
                         rule, total, cap, worst_total, budget, pick));
         if(!ClosePositionByTicket(pick, "friday_cut"))
         {
            Logger.Error("GUARD_COORD", StringFormat("Friday cut: close failed ticket=%I64u - retry in 10 s", pick));
            return;
         }
      }
   }

   //--- Constructor
   CGuardCoordinator() : m_initialized(false), m_eval_count(0),
      m_last_eval_time(0), m_last_eval_microsec(0),
      m_last_suspend_reason(SUSPEND_NONE), m_suspend_logged(false),
      m_emergency_close_attempted(false), m_emergency_close_time(0),
      m_emergency_close_retries(0), m_manual_suspend_active(false)
   {
      ArrayInitialize(m_chain_stopped_at, 0);
      for(int i = 0; i < GUARD_COUNT; i++) m_guards[i] = NULL;

      // Initialize last result to safe defaults
      m_last_result.status           = GUARD_PASS;
      m_last_result.size_multiplier  = 1.0;
      m_last_result.size_reduced     = false;
   }

   //--- Register a guard into a specific slot (1-based index matching priority)
   bool RegisterGuard(IGuard* guard, int slot_1based)
   {
      if(slot_1based < 1 || slot_1based > GUARD_COUNT)
      {
         Logger.Error("GUARD_COORD",
            StringFormat("RegisterGuard: invalid slot %d", slot_1based));
         return false;
      }
      int idx = slot_1based - 1;
      if(m_guards[idx] != NULL)
      {
         Logger.Warn("GUARD_COORD",
            StringFormat("RegisterGuard: replacing guard in slot %d", slot_1based));
      }
      m_guards[idx] = guard;
      Logger.Debug("GUARD_COORD",
         StringFormat("Guard registered: slot=%d name=%s",
                      slot_1based, guard.GetName()));
      return true;
   }

   //--- Initialize coordinator (after all guards registered)
   bool Init()
   {
      // Verify at least the critical guards are registered
      // Slots 1 (SystemHealth) and 2 (PropFirm) MUST be present
      bool critical_ok = true;
      if(m_guards[0] == NULL)
      {
         Logger.Error("GUARD_COORD",
            "Slot 1 (SystemHealth) not registered — critical");
         critical_ok = false;
      }
      if(m_guards[1] == NULL)
      {
         Logger.Error("GUARD_COORD",
            "Slot 2 (PropFirm) not registered — critical");
         critical_ok = false;
      }

      // During phased development: allow unregistered slots
      // In production: all 10 slots should be filled
      int registered = 0;
      for(int i = 0; i < GUARD_COUNT; i++)
         if(m_guards[i] != NULL) registered++;

      Logger.Info("GUARD_COORD",
         StringFormat("Initialized: %d/%d guards registered. critical_ok=%d",
                      registered, GUARD_COUNT, (int)critical_ok));

      m_initialized = true;
      return true; // Allow degraded operation during phased build
   }

   //===================================================================
   // PRIMARY ENTRY POINT — called from OnState_GuardCheck() every tick
   //
   // PSEUDO-CODE:
   //   1. Apply throttle (skip if < 200ms since last full evaluation)
   //      EXCEPTION: always run if equity is near the floor
   //   2. Populate fresh GuardContext from live broker data
   //   3. Reset size modifier accumulator
   //   4. Run evaluation chain (stops on first non-PASS)
   //   5. Act on result (state transitions, closes, alerts)
   //   6. Return result for EA main loop to inspect
   //===================================================================
   GuardEvalResult Evaluate()
   {
      if(!m_initialized)
      {
         Logger.Error("GUARD_COORD", "Evaluate() called before Init()");
         return GuardFatal(GPRIO_SYSTEM_HEALTH, "GUARD_COORD", 0,
                           SUSPEND_SYSTEM_HEALTH, "Coordinator not initialized");
      }

      // Fast equity check — always runs, bypasses throttle
      // This is our last line of defense against account termination
      double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
      if(current_equity <= FloorNow())
      {
         // Don't even wait for throttle — this is CRITICAL
         GuardEvalResult fatal = GuardFatal(GPRIO_PROP_FIRM, "EQUITY_FAST_CHECK", 0,
            SUSPEND_PROP_FIRM_LOCK,
            StringFormat("equity=%.2f <= floor=%.2f",
                         current_equity, Config.EquityFloor),
            true);
         ActOnResult(fatal);
         return fatal;
      }

      // Throttle check — skip full chain if called too recently
      if(!IsThrottleElapsed() && m_eval_count > 0)
      {
         // Return cached result — still valid within throttle window
         return m_last_result;
      }

      // Reset size accumulator before new evaluation
      m_last_result.status          = GUARD_PASS;
      m_last_result.size_multiplier = 1.0;
      m_last_result.size_reduced    = false;
      m_last_result.close_required  = false;

      // Build fresh context snapshot
      GuardContext ctx;
      PopulateGuardContext(ctx, Config.MagicNumber, PriceUtils.PipSize());

      // Run the evaluation chain
      GuardEvalResult result = RunEvaluationChain(ctx);

      // Update tracking
      m_last_eval_time      = TimeCurrent();
      m_last_eval_microsec  = GetMicrosecondCount();
      m_eval_count++;

      // Act on any non-PASS result
      if(result.status != GUARD_PASS)
         ActOnResult(result);
      else
      {
         // Guards passed — clear duplicate-log suppression if we were blocked
         if(m_suspend_logged &&
            StateManager.GetState() != STATE_SUSPENDED)
         {
            m_suspend_logged      = false;
            m_last_suspend_reason = SUSPEND_NONE;
         }
      }

      m_last_result = result;
      return result;
   }

   //===================================================================
   // RESUME CHECK — called every tick while in STATE_SUSPENDED
   //
   // PSEUDO-CODE:
   //   Identify which guard caused the current suspension.
   //   Ask that specific guard if its resume conditions are met.
   //   If yes: clear suspension, transition to GUARD_CHECK.
   //   Manual-reset suspensions: never auto-resume.
   //===================================================================
   void CheckResume()
   {
      if(!StateManager.IsSuspended()) return;

      SUSPEND_REASON reason = StateManager.GetSuspendReason();
      SuspendDescriptor desc = GetSuspendDescriptor(reason);

      // Manual reset required — never auto-resume
      if(desc.manual_reset_required)
      {
         // Log once per 10 minutes to remind operator
         if(((long)StateManager.GetStateAge()) % 600 == 0 &&
            StateManager.GetStateAge() > 0)
         {
            Logger.Warn("GUARD_COORD",
               StringFormat("Suspended for %s — manual reset required. "
                            "Duration: %ds",
                            desc.name,
                            (int)StateManager.GetStateAge()));
         }
         return;
      }

      // Find the guard responsible for this suspension reason
      // Map reason → guard slot
      int guard_slot = MapReasonToGuardSlot(reason);
      if(guard_slot < 0)
      {
         // Unknown reason — time-based fallback: 1 hour then try resume
         if(StateManager.GetStateAge() > 3600)
         {
            Logger.Warn("GUARD_COORD",
               StringFormat("Unknown suspend reason %s — forcing resume "
                            "after 1h safety timeout",
                            EnumToString(reason)));
            StateManager.Resume("safety_timeout_unknown_reason");
         }
         return;
      }

      IGuard* responsible_guard = m_guards[guard_slot];
      if(responsible_guard == NULL) return;

      // Build context for resume check
      GuardContext ctx;
      PopulateGuardContext(ctx, Config.MagicNumber, PriceUtils.PipSize());

      // A320 (guard audit H3): news/circuit-breaker states only advance inside Evaluate(),
      // so ask the guard to re-evaluate first; otherwise CheckResume() never sees them clear.
      responsible_guard.Evaluate(ctx);

      if(responsible_guard.CheckResume(ctx))
      {
         Logger.Info("GUARD_COORD",
            StringFormat("Resume condition met for %s after %ds",
                         desc.name,
                         (int)StateManager.GetStateAge()));
         StateManager.Resume("resume_" + responsible_guard.GetName());
         m_suspend_logged      = false;
         m_last_suspend_reason = SUSPEND_NONE;
      }
   }

   //--- Map a suspension reason to the guard slot responsible for it
   int MapReasonToGuardSlot(SUSPEND_REASON reason)
   {
      switch(reason)
      {
         case SUSPEND_SYSTEM_HEALTH:  return 0;  // Slot 1 = SystemHealth
         case SUSPEND_PROP_FIRM_LOCK:
         case SUSPEND_EQUITY_FLOOR:
         case SUSPEND_PROFIT_TARGET:  return 1;  // Slot 2 = PropFirm
         case SUSPEND_EQUITY_PROTECT: return 2;  // Slot 3 = Equity
         case SUSPEND_DAILY_LIMIT:
         case SUSPEND_MAX_TRADES:
         case SUSPEND_CONSEC_LOSSES:  return 3;  // Slot 4 = DailyDD
         case SUSPEND_ROLLOVER:       return 4;  // A336 (#10): Slot 5 = Rollover (before Session)
         case SUSPEND_SESSION_CLOSED: return 5;  // A336: Slot 6 = Session
         case SUSPEND_NEWS_WINDOW:    return 6;  // Slot 7 = News
         case SUSPEND_SPREAD_HIGH:    return 7;  // Slot 8 = Spread
         case SUSPEND_CIRCUIT_BREAKER:return 8;  // Slot 9 = CircuitBreaker
         case SUSPEND_MANUAL:         return -1; // Manual — no guard handles
         default:                     return -1;
      }
   }

   //--- Get the current size multiplier from last evaluation
   double GetSizeMultiplier() const
   {
      if(m_last_result.size_reduced)
         return MathMax(0.1, m_last_result.size_multiplier);
      return 1.0;
   }

   bool  IsSizeReduced()   const { return m_last_result.size_reduced; }
   bool  IsInitialized()   const { return m_initialized; }
   int   GetEvalCount()    const { return m_eval_count; }

   //--- Force invalidate throttle cache (call after trade close)
   void InvalidateCache()
   {
      m_last_eval_microsec = 0;
      m_last_eval_time     = 0;
   }

   //--- Diagnostic: log guard statistics
   void LogDiagnostics()
   {
      Logger.Info("GUARD_COORD", "Guard chain diagnostics:");
      for(int i = 0; i < GUARD_COUNT; i++)
      {
         if(m_guards[i] == NULL) continue;
         Logger.Info("GUARD_COORD",
            StringFormat("  Slot %d [%s]: evals=%d blocks=%d "
                         "suspends=%d fatals=%d chain_stops=%d",
                         i+1,
                         m_guards[i].GetName(),
                         m_meta[i].eval_count,
                         m_meta[i].block_count,
                         m_meta[i].suspend_count,
                         m_meta[i].fatal_count,
                         m_chain_stopped_at[i]));
      }
   }

   void Shutdown()
   {
      LogDiagnostics();
      m_initialized = false;
      Logger.Info("GUARD_COORD", "Guard coordinator shutdown");
   }
};

//--- Global singleton
CGuardCoordinator GuardCoordinator;

#endif // CGUARDCOORDINATOR_MQH

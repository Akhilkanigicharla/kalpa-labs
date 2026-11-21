
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Prop Firm Guard                         |
//| File: Guards/CPropFirmGuard.mqh                                   |
//| Purpose: The5%ers contractual rule enforcement.                   |
//|           Breach here = account termination. No second chances.   |
//| Phase: 2 — Guard Layer / Step 4                                   |
//|                                                                    |
//| GUARD SLOT: 2                                                      |
//| PRIORITY:   GPRIO_PROP_FIRM                                        |
//|                                                                    |
//| PERMANENT LOCK: Once triggered, lock persists to disk.            |
//|   EA will NOT resume without inp_ManualReset = true.              |
//|   This prevents accidental restart circumventing the protection.  |
//+------------------------------------------------------------------+
#ifndef CPROPFIRMGUARD_MQH
#define CPROPFIRMGUARD_MQH

#include "../Include/Defines.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "../Core/CPersistence.mqh"
#include "GuardTypes.mqh"

#define PROPFIRM_LOCK_FILE   "EA_XAUUSD_propfirm_lock.txt"
#define EQUITY_WARN_BUFFER   200.0  // Log warning when this close to floor
#define EQUITY_CHECK_EVERY   1      // Seconds between equity reads (always live)

class CPropFirmGuard : public IGuard
{
private:
   bool     m_lock_engaged;        // Permanent lock — set on floor breach
   bool     m_target_reached;      // Set when profit target hit
   bool     m_lock_file_written;   // Has lock been persisted to disk
   datetime m_lock_time;           // When lock was engaged
   double   m_lock_equity;         // Equity at time of lock
   int      m_warning_count;       // How many pre-floor warnings issued

   //--- One-sided exposure tracking
   int      m_long_trades;         // Cumulative long trades
   int      m_short_trades;        // Cumulative short trades
   datetime m_last_direction_check;

   //=================================================================
   // Write permanent lock to disk
   // Called IMMEDIATELY when floor is breached.
   // If file write fails: log CRITICAL but still enforce lock in memory.
   //=================================================================
   void WriteLockFile(string reason)
   {
      int h = FileOpen(PROPFIRM_LOCK_FILE,
                       FILE_WRITE|FILE_TXT|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE)
      {
         Logger.Critical("PROPFIRM",
            "FAILED to write lock file — lock active in memory only");
         return;
      }
      FileWriteString(h, "locked=1\n");
      FileWriteString(h, StringFormat("reason=%s\n", reason));
      FileWriteString(h, StringFormat("time=%s\n",
         TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS)));
      FileWriteString(h, StringFormat("equity=%.2f\n", m_lock_equity));
      FileWriteString(h, StringFormat("floor=%.2f\n", Config.EquityFloor));
      FileClose(h);
      m_lock_file_written = true;
      Logger.Critical("PROPFIRM",
         StringFormat("Lock file written: %s", PROPFIRM_LOCK_FILE));
   }

   //=================================================================
   // Read lock file on init — restore lock state across restarts
   //=================================================================
   bool ReadLockFile()
   {
      if(!FileIsExist(PROPFIRM_LOCK_FILE)) return false;

      int h = FileOpen(PROPFIRM_LOCK_FILE,
                       FILE_READ|FILE_TXT|FILE_SHARE_WRITE|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE) return false;

      bool found_locked = false;
      while(!FileIsEnding(h))
      {
         string line = FileReadString(h);
         StringTrimRight(line);
         StringTrimLeft(line);
         if(line == "locked=1") found_locked = true;
      }
      FileClose(h);

      if(found_locked)
      {
         Logger.Critical("PROPFIRM",
            StringFormat("Lock file found at startup (%s) — "
                         "EA is PERMANENTLY LOCKED. "
                         "Set inp_ManualReset=true to clear.",
                         PROPFIRM_LOCK_FILE));
      }
      return found_locked;
   }

   //=================================================================
   // Clear lock file (only when ManualReset explicitly requested)
   //=================================================================
   void ClearLockFile()
   {
      if(FileIsExist(PROPFIRM_LOCK_FILE))
      {
         FileDelete(PROPFIRM_LOCK_FILE);
         Logger.Critical("PROPFIRM",
            "Lock file cleared by manual reset — "
            "EA will attempt to resume. Verify account status first.");
      }
   }

public:
   CPropFirmGuard() :
      m_lock_engaged(false),
      m_target_reached(false),
      m_lock_file_written(false),
      m_lock_time(0),
      m_lock_equity(0),
      m_warning_count(0),
      m_long_trades(0),
      m_short_trades(0),
      m_last_direction_check(0)
   {
      m_meta.index       = 2;
      m_meta.priority    = GPRIO_PROP_FIRM;
      m_meta.name        = "PROP_FIRM";
      m_meta.description = "The5%ers contractual rule enforcement";
      m_meta.enabled     = true;
      m_meta.initialized = false;
   }

   virtual bool Init() override
   {
      // Handle manual reset request
      if(Config.ManualReset)
      {
         Logger.Critical("PROPFIRM",
            "ManualReset=true detected — clearing lock file if present");
         ClearLockFile();
         m_lock_engaged = false;
         // Warn operator: they must verify account is still valid
         Alert("PROPFIRM: Manual reset applied. "
               "Verify account equity before trading resumes.");
      }

      // Check for existing lock file (from previous session)
      if(ReadLockFile())
      {
         m_lock_engaged = true;
         m_lock_file_written = true;
         Logger.Critical("PROPFIRM",
            "Starting in LOCKED state — equity floor was breached "
            "in a previous session");
         // Don't return false — EA initializes but immediately suspends
      }

      m_meta.initialized = true;
      m_initialized      = true;

      Logger.Info("PROPFIRM",
         StringFormat("Initialized. floor=%.2f target=%.2f locked=%d",
                      Config.EquityFloor, Config.ProfitTarget,
                      (int)m_lock_engaged));
      return true;
   }

   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();

      //--- [P0] Restore permanent lock (survives restart)
      if(m_lock_engaged)
      {
         RecordTrigger(GUARD_FATAL);
         return GuardFatal(GPRIO_PROP_FIRM, m_meta.name, m_meta.index,
                           SUSPEND_PROP_FIRM_LOCK,
                           StringFormat("Permanent lock active. "
                                        "equity_at_lock=%.2f floor=%.2f "
                                        "Set inp_ManualReset=true to clear.",
                                        m_lock_equity, Config.EquityFloor),
                           false); // close_required=false: already closed when locked
      }

      //--- [P1] Hard equity floor — CRITICAL
      //    Use live equity from context (pre-populated this tick)
      if(ctx.equity <= Config.EquityFloor)
      {
         m_lock_engaged  = true;
         m_lock_time     = TimeCurrent();
         m_lock_equity   = ctx.equity;

         WriteLockFile(StringFormat("equity_%.2f_<=_floor_%.2f",
                                    ctx.equity, Config.EquityFloor));

         Logger.Critical("PROPFIRM",
            "HARD EQUITY FLOOR BREACHED — permanent lock engaged",
            StringFormat("equity=%.2f floor=%.2f balance=%.2f",
                         ctx.equity, Config.EquityFloor, ctx.balance));

         RecordTrigger(GUARD_FATAL);
         return GuardFatal(GPRIO_PROP_FIRM, m_meta.name, m_meta.index,
                           SUSPEND_PROP_FIRM_LOCK,
                           StringFormat("Equity %.2f breached floor %.2f",
                                        ctx.equity, Config.EquityFloor),
                           true); // close_required = true
      }

      //--- [P1a] Pre-floor warning (not a block — just early warning)
      if(ctx.equity <= Config.EquityFloor + EQUITY_WARN_BUFFER)
      {
         m_warning_count++;
         // Log every 10th warning to avoid spam
         if(m_warning_count % 10 == 1)
         {
            Logger.Critical("PROPFIRM",
               StringFormat("EQUITY DANGER ZONE: equity=%.2f "
                            "floor=%.2f buffer_remaining=%.2f",
                            ctx.equity, Config.EquityFloor,
                            ctx.equity - Config.EquityFloor));
         }
         // Not blocking — EquityGuard Tier 3 handles the close
         // PropFirmGuard only engages the permanent lock
      }

      //--- [P2] Profit target reached (use BALANCE — recognized profit)
      if(!m_target_reached && ctx.balance >= Config.ProfitTarget
         && CountProfitableDays() >= inp_MinProfitDays)          // A335: The5%ers also needs 3 profitable days
      {
         m_target_reached = true;
         Logger.Info("PROPFIRM",
            StringFormat("PROFIT TARGET REACHED: balance=%.2f target=%.2f",
                         ctx.balance, Config.ProfitTarget),
            "EA will close all positions and suspend");

         Alert(EA_NAME, ": PROFIT TARGET REACHED! balance=",
               DoubleToString(ctx.balance, 2),
               " — CHALLENGE PASSED. EA suspending.");

         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_PROP_FIRM, m_meta.name, m_meta.index,
                             SUSPEND_PROFIT_TARGET,
                             StringFormat("Balance %.2f >= target %.2f",
                                          ctx.balance, Config.ProfitTarget),
                             "Manual restart required",
                             true,   // close_required
                             true);  // alert_trader
      }

      //--- [P3] Multiple positions check (should never happen with our EA)
      if(ctx.open_positions > 1)
      {
         Logger.Critical("PROPFIRM",
            StringFormat("MULTIPLE POSITIONS DETECTED: count=%d magic=%lld "
                         "— The5%ers prohibits bulk trading",
                         ctx.open_positions, Config.MagicNumber),
            "Excess positions must be closed manually");
         // Don't block — log and let coordinator handle
         // Closing excess positions is done in coordinator
         // We return PASS here but the coordinator will see the alert
      }

      //--- [P4] Pending orders check
      //    Our EA never uses pending orders — if any exist, something went wrong
      int pending_count = 0;
      for(int i = OrdersTotal() - 1; i >= 0; i--)
      {
         ulong t = OrderGetTicket(i);
         if(t == 0) continue;
         if(OrderGetString(ORDER_SYMBOL)  == EA_SYMBOL &&
            OrderGetInteger(ORDER_MAGIC)  == Config.MagicNumber)
            pending_count++;
      }
      if(pending_count > 0)
      {
         Logger.Error("PROPFIRM",
            StringFormat("Pending order found: count=%d — "
                         "EA does not use pending orders. "
                         "Cancelling via coordinator.",
                         pending_count));
         // Return PASS — coordinator will cancel via cancel_pending flag
         // We set the flag in a modified result
         GuardEvalResult r = GuardPass(GPRIO_PROP_FIRM, m_meta.name, m_meta.index);
         r.cancel_pending = true;
         return r;
      }

      //--- [P5] One-sided exposure monitoring (every 60 seconds)
      if(TimeCurrent() - m_last_direction_check >= 60)
      {
         m_last_direction_check = TimeCurrent();
         int total = m_long_trades + m_short_trades;
         if(total >= 10)
         {
            double long_pct  = (total > 0) ? (double)m_long_trades/total : 0;
            double short_pct = 1.0 - long_pct;
            if(long_pct > 0.85 || short_pct > 0.85)
            {
               Logger.Warn("PROPFIRM",
                  StringFormat("One-sided exposure detected: "
                               "long=%.0f%% short=%.0f%% total_trades=%d "
                               "— monitor for The5%ers compliance",
                               long_pct*100, short_pct*100, total));
            }
         }
      }

      return GuardPass(GPRIO_PROP_FIRM, m_meta.name, m_meta.index);
   }

   //--- CheckResume: PropFirmLock requires manual reset — never auto-resumes
   virtual bool CheckResume(const GuardContext &ctx) override
   {
      if(m_lock_engaged)
      {
         // Only resumes if ManualReset was set AND equity is above floor
         if(Config.ManualReset && ctx.equity > Config.EquityFloor)
         {
            Logger.Critical("PROPFIRM",
               "Manual reset applied — resuming from prop firm lock. "
               "VERIFY ACCOUNT STATUS BEFORE TRADING.");
            m_lock_engaged = false;
            ClearLockFile();
            return true;
         }
         return false;
      }
      if(m_target_reached) return false; // Target = terminal
      return true;
   }

   //--- Called by TradeManager when trade direction is known
   void RecordTradeDirection(TRADE_DIR dir)
   {
      if(dir == DIR_LONG)  m_long_trades++;
      if(dir == DIR_SHORT) m_short_trades++;
   }

   bool IsLocked()        const { return m_lock_engaged; }
   bool IsTargetReached() const { return m_target_reached; }
};

#endif // CPROPFIRMGUARD_MQH

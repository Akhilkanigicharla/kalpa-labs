
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — System Health Check                     |
//| File: Guards/CSystemHealthCheck.mqh                               |
//| Purpose: Validate EA operating environment before any trading.    |
//|           Not market analysis — pure infrastructure safety.       |
//| Phase: 2 — Guard Layer / Step 3                                   |
//|                                                                    |
//| GUARD SLOT: 1 (highest priority — runs first)                     |
//| PRIORITY:   GPRIO_SYSTEM_HEALTH                                   |
//|                                                                    |
//| FATAL vs RECOVERABLE:                                             |
//|   FATAL:       Wrong symbol, no trade permissions, netting mode,  |
//|                bad config. These cannot be fixed without restart.  |
//|   RECOVERABLE: Disconnected (may reconnect), stale price,         |
//|                timer not yet fired (startup grace period).         |
//|                                                                    |
//| CACHING RULE:                                                      |
//|   Full check: maximum once every 30 seconds.                      |
//|   Connectivity check: maximum once every 5 seconds.               |
//|   Fatal checks (symbol, permissions): once at init, then cached.  |
//|   Rationale: Health checks involve TerminalInfoInteger etc —       |
//|   no need to call these on every tick.                            |
//+------------------------------------------------------------------+
#ifndef CSYSTEMHEALTHCHECK_MQH
#define CSYSTEMHEALTHCHECK_MQH

#include "../Include/Defines.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "../Core/CTimerSystem.mqh"
#include "GuardTypes.mqh"

#define HEALTH_FULL_CACHE_SEC    30   // Full check interval
#define HEALTH_CONN_CACHE_SEC     5   // Connectivity check interval
#define HEALTH_STARTUP_GRACE_SEC 90   // Grace period before timer check
#define HEALTH_PRICE_MIN        1000.0 // XAUUSD below this = data error
#define HEALTH_PRICE_MAX        5000.0 // XAUUSD above this = data error
#define HEALTH_CONSEC_DISC_MAX     2   // Consecutive disconnects before suspend

class CSystemHealthCheck : public IGuard
{
private:
   //--- Cached results
   HealthCheckResult  m_cached_result;
   datetime           m_last_full_check;
   datetime           m_last_conn_check;
   datetime           m_ea_start_time;

   //--- Fatal flags (set once, never cleared without restart)
   bool               m_symbol_fatal;
   bool               m_permissions_fatal;
   bool               m_account_mode_fatal;
   bool               m_config_fatal;

   //--- Connectivity tracking
   int                m_consec_disconnects;
   datetime           m_first_disconnect_time;
   bool               m_was_disconnected;

   //--- Timer health tracking
   bool               m_timer_ok_confirmed;

   //--- A336 (#4): recoverable symbol / permission state
   bool               m_symbol_bad;
   bool               m_perm_bad;
   datetime           m_last_recheck;

   //=================================================================
   // CHECK: Broker connectivity
   //=================================================================
   HEALTH_CHECK_STATUS CheckConnectivity()
   {
      bool connected = (bool)TerminalInfoInteger(TERMINAL_CONNECTED);

      if(!connected)
      {
         if(!m_was_disconnected)
         {
            m_was_disconnected      = true;
            m_first_disconnect_time = TimeCurrent();
            m_consec_disconnects    = 1;
            Logger.Warn("SYS_HEALTH",
               "Broker connectivity lost — monitoring");
         }
         else
         {
            m_consec_disconnects++;
         }

         Logger.Warn("SYS_HEALTH",
            StringFormat("Disconnected — consecutive_checks=%d",
                         m_consec_disconnects));

         if(m_consec_disconnects >= HEALTH_CONSEC_DISC_MAX)
            return HEALTH_FAILED; // Recoverable — may reconnect

         return HEALTH_DEGRADED; // First disconnect — give benefit of doubt
      }

      // Reconnected
      if(m_was_disconnected)
      {
         Logger.Info("SYS_HEALTH",
            StringFormat("Connectivity restored after %ds",
                         (int)(TimeCurrent() - m_first_disconnect_time)));
         m_was_disconnected   = false;
         m_consec_disconnects = 0;
      }
      return HEALTH_OK;
   }

   //=================================================================
   // CHECK: Symbol availability and trade mode
   //=================================================================
   //--- A336 (#4): a bid of 0 (quotes not synced after a Wine reconnect) or a trade-mode change
   //    is TRANSIENT: HEALTH_FAILED -> SUSPENDED, rechecked every minute. It no longer latches
   //    a FATAL state that switched off every safety check while positions were open.
   HEALTH_CHECK_STATUS CheckSymbol()
   {
      double bid = SymbolInfoDouble(EA_SYMBOL, SYMBOL_BID);
      long trade_mode = SymbolInfoInteger(EA_SYMBOL, SYMBOL_TRADE_MODE);
      bool bad = (bid <= 0 || trade_mode != SYMBOL_TRADE_MODE_FULL);
      if(bad && !m_symbol_bad)
         Logger.Error("SYS_HEALTH",
            StringFormat("Symbol %s not tradable (bid=%.2f trade_mode=%d) - suspending, rechecked every minute",
                         EA_SYMBOL, bid, (int)trade_mode));
      if(!bad && m_symbol_bad)
         Logger.Info("SYS_HEALTH", "Symbol tradable again");
      m_symbol_bad = bad;
      return bad ? HEALTH_FAILED : HEALTH_OK;
   }

   //=================================================================
   // CHECK: Trading permissions
   //=================================================================
   //--- A336 (#4): permissions can flip for a moment (terminal button, reconnect): recoverable
   HEALTH_CHECK_STATUS CheckTradePermissions()
   {
      bool account_trade = (bool)AccountInfoInteger(ACCOUNT_TRADE_ALLOWED);
      bool ea_trade      = (bool)AccountInfoInteger(ACCOUNT_TRADE_EXPERT);
      bool term_trade    = (bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);
      bool bad = (!account_trade || !ea_trade || !term_trade);
      if(bad && !m_perm_bad)
         Logger.Error("SYS_HEALTH",
            StringFormat("Trading not permitted (account=%d expert=%d terminal=%d) - suspending, rechecked every minute. "
                         "Enable 'Allow automated trading'.", (int)account_trade, (int)ea_trade, (int)term_trade));
      if(!bad && m_perm_bad)
         Logger.Info("SYS_HEALTH", "Trading permitted again");
      m_perm_bad = bad;
      return bad ? HEALTH_FAILED : HEALTH_OK;
   }

   //=================================================================
   // CHECK: Account margin mode (must be HEDGING)
   //=================================================================
   HEALTH_CHECK_STATUS CheckAccountMode()
   {
      if(m_account_mode_fatal) return HEALTH_FATAL;

      ENUM_ACCOUNT_MARGIN_MODE mode =
         (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);

      if(mode == ACCOUNT_MARGIN_MODE_RETAIL_NETTING)
      {
         Logger.Fatal("SYS_HEALTH",
            "Account is NETTING mode — EA requires HEDGING. "
            "The5%ers accounts should be hedging. Check broker settings.");
         m_account_mode_fatal = true;
         return HEALTH_FATAL;
      }

      return HEALTH_OK;
   }

   //=================================================================
   // CHECK: Timer activity
   //=================================================================
   HEALTH_CHECK_STATUS CheckTimer()
   {
      if(m_timer_ok_confirmed) return HEALTH_OK;

      int fires = TimerSystem.TimerFires();
      int elapsed = (int)(TimeCurrent() - m_ea_start_time);

      if(fires == 0 && elapsed > HEALTH_STARTUP_GRACE_SEC)
      {
         Logger.Warn("SYS_HEALTH",
            StringFormat("Timer has not fired after %ds — "
                         "heartbeat and cleanup may be disabled", elapsed));
         return HEALTH_DEGRADED; // Non-fatal: EA can trade without timer
      }

      if(fires > 0)
         m_timer_ok_confirmed = true;

      return HEALTH_OK;
   }

   //=================================================================
   // CHECK: Persistence write access
   //=================================================================
   HEALTH_CHECK_STATUS CheckPersistence()
   {
      // Lightweight: test if we can write a small file
      // If this fails, logging and state recovery won't work
      string test_file = "EA_XAUUSD_healthcheck.tmp";
      int h = FileOpen(test_file,
                       FILE_WRITE|FILE_TXT|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE)
      {
         Logger.Error("SYS_HEALTH",
            "Cannot write to MQL5 Files directory — persistence unavailable");
         return HEALTH_FAILED; // Recoverable if permissions restored
      }
      FileWriteString(h, "ok\n");
      FileClose(h);
      FileDelete(test_file);
      return HEALTH_OK;
   }

   //=================================================================
   // CHECK: Config integrity (redundant after Init but re-checked)
   //=================================================================
   HEALTH_CHECK_STATUS CheckConfig()
   {
      if(m_config_fatal) return HEALTH_FATAL;

      if(!Config.IsValid())
      {
         Logger.Fatal("SYS_HEALTH",
            "Config.IsValid() = false at runtime — critical init failure");
         m_config_fatal = true;
         return HEALTH_FATAL;
      }
      return HEALTH_OK;
   }

   //=================================================================
   // CHECK: Price sanity (XAUUSD should be 1000–5000)
   //=================================================================
   HEALTH_CHECK_STATUS CheckPriceSanity(const GuardContext &ctx)
   {
      if(ctx.current_bid < HEALTH_PRICE_MIN ||
         ctx.current_bid > HEALTH_PRICE_MAX)
      {
         Logger.Error("SYS_HEALTH",
            StringFormat("Price sanity failed: bid=%.5f "
                         "expected %.0f–%.0f",
                         ctx.current_bid,
                         HEALTH_PRICE_MIN, HEALTH_PRICE_MAX));
         return HEALTH_FAILED; // Recoverable — bad tick, not broken EA
      }
      return HEALTH_OK;
   }

   //=================================================================
   // Compute confidence score from check results
   //=================================================================
   int ComputeConfidence(const HealthCheckResult &r)
   {
      int score = 100;
      if(r.connectivity   == HEALTH_DEGRADED) score -= 10;
      if(r.connectivity   == HEALTH_FAILED)   score -= 30;
      if(r.timer_active   == HEALTH_DEGRADED) score -= 5;
      if(r.persistence    == HEALTH_FAILED)   score -= 15;
      if(r.price_sane     == HEALTH_FAILED)   score -= 20;
      // Fatal checks: score irrelevant — guard returns FATAL directly
      return MathMax(0, score);
   }

public:
   CSystemHealthCheck() :
      m_last_full_check(0),
      m_last_conn_check(0),
      m_ea_start_time(0),
      m_symbol_fatal(false),
      m_permissions_fatal(false),
      m_account_mode_fatal(false),
      m_config_fatal(false),
      m_consec_disconnects(0),
      m_first_disconnect_time(0),
      m_was_disconnected(false),
      m_timer_ok_confirmed(false),
      m_symbol_bad(false),
      m_perm_bad(false),
      m_last_recheck(0)
   {
      m_meta.index       = 1;
      m_meta.priority    = GPRIO_SYSTEM_HEALTH;
      m_meta.name        = "SYS_HEALTH";
      m_meta.description = "Infrastructure validation";
      m_meta.enabled     = true;
      m_meta.initialized = false;
   }

   //=================================================================
   // Init — run all fatal checks immediately at startup
   // If any fatal check fails: Init returns false → EA halts
   //=================================================================
   virtual bool Init() override
   {
      m_ea_start_time = TimeCurrent();
      Logger.Info("SYS_HEALTH", "Running startup health checks");

      // Fatal checks — run once and cache result.
      // A336 (#4): symbol/permission problems at startup are recoverable (the EA suspends and
      // rechecks every minute) so open positions are still managed; account mode stays fatal.
      if(CheckSymbol()           != HEALTH_OK) Logger.Warn("SYS_HEALTH", "Symbol not tradable at startup - EA starts SUSPENDED");
      if(CheckTradePermissions() != HEALTH_OK) Logger.Warn("SYS_HEALTH", "Trading not permitted at startup - EA starts SUSPENDED");
      if(CheckAccountMode()     == HEALTH_FATAL) return false;
      if(CheckConfig()          == HEALTH_FATAL) return false;

      // Non-fatal startup checks
      HEALTH_CHECK_STATUS conn_status = CheckConnectivity();
      if(conn_status == HEALTH_FATAL) return false;

      HEALTH_CHECK_STATUS persist_status = CheckPersistence();
      if(persist_status == HEALTH_FAILED)
         Logger.Warn("SYS_HEALTH",
            "Persistence unavailable — EA will run in degraded mode");

      // Cache initial result
      m_cached_result.connectivity = conn_status;
      m_cached_result.persistence  = persist_status;
      m_cached_result.symbol_valid = m_symbol_bad ? HEALTH_FAILED : HEALTH_OK;
      m_cached_result.trade_allowed = m_perm_bad ? HEALTH_FAILED : HEALTH_OK;
      m_cached_result.account_mode  = HEALTH_OK;
      m_cached_result.config_valid  = HEALTH_OK;
      m_cached_result.last_check_time = TimeCurrent();
      m_cached_result.confidence_score = ComputeConfidence(m_cached_result);

      m_meta.initialized = true;
      m_initialized      = true;

      Logger.Info("SYS_HEALTH",
         StringFormat("Startup checks passed. confidence=%d%%",
                      m_cached_result.confidence_score));
      return true;
   }

   //=================================================================
   // Evaluate — called every tick by coordinator
   //=================================================================
   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();
      datetime now = TimeCurrent();

      //--- Fast path: cached fatal conditions
      if(m_symbol_fatal || m_permissions_fatal ||
         m_account_mode_fatal || m_config_fatal)
      {
         RecordTrigger(GUARD_FATAL);
         return GuardFatal(GPRIO_SYSTEM_HEALTH, m_meta.name, m_meta.index,
                           SUSPEND_SYSTEM_HEALTH,
                           "Cached fatal: symbol/permissions/mode/config");
      }

      //--- Connectivity check (5-second cache)
      if((now - m_last_conn_check) >= HEALTH_CONN_CACHE_SEC)
      {
         m_last_conn_check = now;
         HEALTH_CHECK_STATUS conn = CheckConnectivity();
         m_cached_result.connectivity = conn;

         if(conn == HEALTH_FAILED)
         {
            RecordTrigger(GUARD_SUSPEND);
            return GuardSuspend(GPRIO_SYSTEM_HEALTH, m_meta.name, m_meta.index,
                                SUSPEND_SYSTEM_HEALTH,
                                StringFormat("Disconnected (%d consecutive checks)",
                                             m_consec_disconnects),
                                "Resumes on reconnect");
         }
      }

      //--- Full check (30-second cache)
      if((now - m_last_full_check) >= HEALTH_FULL_CACHE_SEC)
      {
         m_last_full_check = now;

         // A336 (#4): symbol + permissions, recoverable -> SUSPEND (not FATAL)
         HEALTH_CHECK_STATUS sym  = CheckSymbol();
         HEALTH_CHECK_STATUS perm = CheckTradePermissions();
         m_cached_result.symbol_valid  = sym;
         m_cached_result.trade_allowed = perm;
         if(sym != HEALTH_OK || perm != HEALTH_OK)
         {
            RecordTrigger(GUARD_SUSPEND);
            return GuardSuspend(GPRIO_SYSTEM_HEALTH, m_meta.name, m_meta.index,
                                SUSPEND_SYSTEM_HEALTH,
                                StringFormat("symbol_ok=%d trade_permitted=%d", (int)(sym == HEALTH_OK), (int)(perm == HEALTH_OK)),
                                "Rechecked every minute; resumes when quotes and permissions are back");
         }

         // Price sanity
         HEALTH_CHECK_STATUS price = CheckPriceSanity(ctx);
         m_cached_result.price_sane = price;
         if(price == HEALTH_FAILED)
         {
            RecordTrigger(GUARD_BLOCK);
            return GuardBlock(GPRIO_SYSTEM_HEALTH, m_meta.name, m_meta.index,
                              StringFormat("Price sanity fail: bid=%.5f",
                                           ctx.current_bid),
                              "Clears when price feed normalises");
         }

         // Timer check
         HEALTH_CHECK_STATUS timer = CheckTimer();
         m_cached_result.timer_active = timer;
         // Timer degraded = log only, not a block

         // Persistence check (lightweight — test write)
         HEALTH_CHECK_STATUS persist = CheckPersistence();
         m_cached_result.persistence = persist;
         // Persistence failed = degraded mode, not a block

         m_cached_result.confidence_score = ComputeConfidence(m_cached_result);
         m_cached_result.last_check_time  = now;

         // Log confidence if it changed significantly
         if(m_cached_result.confidence_score < 80)
         {
            Logger.Warn("SYS_HEALTH",
               StringFormat("Health confidence degraded: %d%%",
                            m_cached_result.confidence_score));
         }
      }

      return GuardPass(GPRIO_SYSTEM_HEALTH, m_meta.name, m_meta.index);
   }

   //=================================================================
   // CheckResume — called when suspended for SUSPEND_SYSTEM_HEALTH
   //=================================================================
   virtual bool CheckResume(const GuardContext &ctx) override
   {
      // Resume if connectivity restored
      bool connected = (bool)TerminalInfoInteger(TERMINAL_CONNECTED);
      if(!connected) return false;

      m_consec_disconnects = 0;
      m_was_disconnected   = false;

      // Also verify price is sane before resuming
      if(ctx.current_bid < HEALTH_PRICE_MIN ||
         ctx.current_bid > HEALTH_PRICE_MAX)
         return false;

      // A336 (#4): symbol + permissions rechecked at most once a minute while suspended
      if(m_symbol_bad || m_perm_bad)
      {
         if(m_last_recheck != 0 && TimeCurrent() - m_last_recheck < 60) return false;
         m_last_recheck = TimeCurrent();
         if(CheckSymbol() != HEALTH_OK)           return false;
         if(CheckTradePermissions() != HEALTH_OK) return false;
      }

      return true;
   }

   HealthCheckResult GetLastResult() const { return m_cached_result; }
};

#endif // CSYSTEMHEALTHCHECK_MQH

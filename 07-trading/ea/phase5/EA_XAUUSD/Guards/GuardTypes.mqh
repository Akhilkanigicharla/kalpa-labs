
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Guard Shared Types                      |
//| File: Guards/GuardTypes.mqh                                       |
//| Purpose: ALL guard-layer enums, result structs, metadata,         |
//|           priority definitions, and shared utility functions.     |
//|           NO business logic. NO market analysis. Pure types.      |
//| Phase: 2 — Guard Layer / Step 1                                   |
//|                                                                    |
//| DEPENDENCY RULE:                                                   |
//|   This file depends ONLY on Include/Defines.mqh                   |
//|   Every guard module includes this file.                          |
//|   This file includes nothing from the guard layer.                |
//+------------------------------------------------------------------+
#ifndef GUARDTYPES_MQH
#define GUARDTYPES_MQH

#include "../Include/Defines.mqh"
#include "../Core/CConfig.mqh"       // A336: EAGmtNow()

//===================================================================
// GUARD PRIORITY LEVELS
//
// PSEUDO-CODE RATIONALE:
//   Priority determines evaluation ORDER in the coordinator.
//   Lower number = evaluated first = higher authority.
//   A guard with priority 1 can halt ALL subsequent guards.
//   This ordering is non-negotiable and hard-coded by design.
//   If a prop-firm rule guard fails, there is no reason to
//   evaluate a session timing guard — the account is in danger.
//===================================================================
enum GUARD_PRIORITY
{
   GPRIO_SYSTEM_HEALTH   = 1,   // Infrastructure must work before anything
   GPRIO_PROP_FIRM       = 2,   // Contractual limits — account survival
   GPRIO_EQUITY          = 3,   // Capital protection — tiered
   GPRIO_DAILY_DRAWDOWN  = 4,   // Daily self-imposed limits
   GPRIO_SESSION         = 5,   // Time-based entry filtering
   GPRIO_ROLLOVER        = 6,   // Rollover blackout window
   GPRIO_NEWS            = 7,   // News signature detection
   GPRIO_SPREAD          = 8,   // Execution cost validation
   GPRIO_CIRCUIT_BREAKER = 9,   // Volatility anomaly protection
   GPRIO_COOLDOWN        = 10   // Behavioral cooldown enforcement
};

//===================================================================
// GUARD EVALUATION RESULT
//
// Every guard's Evaluate() method returns exactly one of these.
// The coordinator interprets these strictly:
//   GUARD_PASS:    This guard is satisfied. Continue to next guard.
//   GUARD_BLOCK:   Skip this tick. Stay in GUARD_CHECK. No state change.
//                  Use for: transient conditions that resolve themselves
//                  (spread spike, out-of-session, cooldown countdown).
//   GUARD_SUSPEND: Enter STATE_SUSPENDED with a specific reason.
//                  Use for: conditions requiring sustained blocking
//                  (daily limit hit, rollover window, circuit breaker).
//   GUARD_FATAL:   Unrecoverable. Halt EA immediately.
//                  Use for: contractual breach risk, infrastructure failure,
//                  equity floor breach.
//
// CRITICAL DISTINCTION — BLOCK vs SUSPEND:
//   BLOCK:   The condition may resolve on the NEXT TICK.
//            No StateManager transition. EA stays in GUARD_CHECK.
//            Examples: spread normalises in 1 tick, cooldown -1 second.
//   SUSPEND: The condition will NOT resolve on the next tick.
//            StateManager transitions to STATE_SUSPENDED.
//            Resume requires explicit condition check.
//            Examples: rollover (lasts 2.5 hours), daily limit (lasts until tomorrow).
//===================================================================
// NOTE: GUARD_RESULT is already defined in Include/Defines.mqh
// Reproduced here as a comment for reader clarity only:
//   GUARD_PASS    = 0
//   GUARD_BLOCK   = 1
//   GUARD_SUSPEND = 2
//   GUARD_FATAL   = 3

//===================================================================
// GUARD EVALUATION CONTEXT
//
// Snapshot of market/account state passed INTO each guard.
// Guards read from this context — they do NOT call broker APIs directly
// (with exceptions documented below).
// Populated by GuardCoordinator before the evaluation chain runs.
//
// RATIONALE:
//   If each guard independently calls SymbolInfoDouble(), AccountInfoDouble(),
//   etc., they may get slightly different values across the evaluation chain
//   (prices tick while guards run). One consistent snapshot prevents this.
//
// EXCEPTIONS (guards that MUST call broker API directly):
//   PropFirmGuard:  Position count must be live (PositionsTotal())
//   SystemHealth:   Connectivity must be live (TerminalInfoInteger)
//   These are documented in each guard's Evaluate() method.
//===================================================================
struct GuardContext
{
   // Account state
   double   equity;              // AccountInfoDouble(ACCOUNT_EQUITY)
   double   balance;             // AccountInfoDouble(ACCOUNT_BALANCE)
   double   floating_pnl;        // equity - balance

   // Market state
   double   current_bid;         // SymbolInfoDouble(SYMBOL_BID)
   double   current_ask;         // SymbolInfoDouble(SYMBOL_ASK)
   double   current_spread_pips; // (ask - bid) / pip_size

   // Time state
   datetime server_time;         // TimeCurrent()
   datetime gmt_time;            // TimeGMT()
   int      gmt_hour;            // Hour in GMT
   int      gmt_minute;          // Minute in GMT
   int      day_of_week;         // 0=Sun,1=Mon...6=Sat (GMT)

   // Position state
   int      open_positions;      // PositionsTotal() filtered by magic
   bool     has_our_position;    // True if EA has an open trade
   ulong    our_ticket;          // Ticket of our open position (0 if none)

   // Derived
   bool     is_weekend;          // day_of_week == 0 || == 6
   bool     is_friday;           // day_of_week == 5
   bool     is_monday;           // day_of_week == 1
};

//===================================================================
// GUARD EVALUATION RESULT STRUCT
//
// Richer than just the GUARD_RESULT enum — carries all context the
// coordinator needs to act on the result without calling back into guards.
//===================================================================
struct GuardEvalResult
{
   GUARD_RESULT     status;            // PASS / BLOCK / SUSPEND / FATAL

   // Populated when status != GUARD_PASS
   SUSPEND_REASON   suspend_reason;    // Which suspension category
   GUARD_PRIORITY   guard_priority;    // Which guard produced this result
   string           guard_name;        // Human-readable guard identifier
   string           detail;            // Specific reason (for logging)
   string           resume_condition;  // What must happen to resume

   // Action flags (coordinator acts on these)
   bool             close_required;    // TRUE = close open position immediately
   bool             cancel_pending;    // TRUE = cancel any pending orders
   bool             alert_trader;      // TRUE = send MT5 alert to trader

   // Sizing modifiers (aggregated across all passing guards)
   bool             size_reduced;      // TRUE = apply size_multiplier
   double           size_multiplier;   // 1.0 = normal, 0.5 = half, etc.

   // Diagnostic
   datetime         eval_time;         // When this result was produced
   int              guard_index;       // 1–10 (which step in chain)

   // Default constructor — initializes to a safe PASS state
   GuardEvalResult()
   {
      status          = GUARD_PASS;
      suspend_reason  = SUSPEND_NONE;
      guard_priority  = GPRIO_COOLDOWN;  // Lowest authority as default
      guard_name      = "";
      detail          = "";
      resume_condition = "";
      close_required  = false;
      cancel_pending  = false;
      alert_trader    = false;
      size_reduced    = false;
      size_multiplier = 1.0;
      eval_time       = 0;
      guard_index     = 0;
   }
};

//===================================================================
// GUARD HEALTH STATUS
// Used by SystemHealthCheck to report per-check results
// and by the coordinator to assess infrastructure confidence.
//===================================================================
enum HEALTH_CHECK_STATUS
{
   HEALTH_OK         = 0,   // Check passed cleanly
   HEALTH_DEGRADED   = 1,   // Check passed but with warnings
   HEALTH_FAILED     = 2,   // Check failed — recoverable
   HEALTH_FATAL      = 3    // Check failed — unrecoverable
};

struct HealthCheckResult
{
   HEALTH_CHECK_STATUS  connectivity;
   HEALTH_CHECK_STATUS  symbol_valid;
   HEALTH_CHECK_STATUS  trade_allowed;
   HEALTH_CHECK_STATUS  timer_active;
   HEALTH_CHECK_STATUS  persistence;
   HEALTH_CHECK_STATUS  config_valid;
   HEALTH_CHECK_STATUS  price_sane;
   HEALTH_CHECK_STATUS  account_mode;

   int                  confidence_score;  // 0–100 (100 = all checks green)
   bool                 has_fatal;         // Any single HEALTH_FATAL present
   bool                 has_failure;       // Any HEALTH_FAILED present
   string               failure_detail;    // First failure reason
   datetime             last_check_time;   // When this was evaluated

   HealthCheckResult()
   {
      connectivity   = HEALTH_OK;
      symbol_valid   = HEALTH_OK;
      trade_allowed  = HEALTH_OK;
      timer_active   = HEALTH_OK;
      persistence    = HEALTH_OK;
      config_valid   = HEALTH_OK;
      price_sane     = HEALTH_OK;
      account_mode   = HEALTH_OK;
      confidence_score = 100;
      has_fatal      = false;
      has_failure    = false;
      failure_detail = "";
      last_check_time = 0;
   }
};

//===================================================================
// CIRCUIT BREAKER STATE
// Separate from CBEvent (which is an event record) —
// this is the CURRENT state of the breaker mechanism.
//===================================================================
enum CB_STATE
{
   CB_NORMAL      = 0,   // No active breaker
   CB_ACTIVE      = 1,   // Breaker fired — in cooldown
   CB_RESETTING   = 2    // Cooldown elapsed — verifying conditions
};

//===================================================================
// SPREAD CALIBRATION CONFIDENCE
// Drives whether dynamic or fallback thresholds are used.
//===================================================================
enum SPREAD_CALIB_CONFIDENCE
{
   CALIB_NONE        = 0,   // No data — use hard cap
   CALIB_PARTIAL     = 1,   // < 3 days data — use partial + hard cap min
   CALIB_SUFFICIENT  = 2,   // >= 3 days — use dynamic threshold
   CALIB_OPTIMAL     = 3    // >= 7 days — maximum confidence
};

//===================================================================
// NEWS GUARD STATE
//===================================================================
enum NEWS_STATE
{
   NEWS_CLEAR         = 0,  // No news signature detected
   NEWS_SUSPECTED     = 1,  // One trigger fired — monitoring
   NEWS_ACTIVE        = 2,  // Multiple triggers or confirmed signature
   NEWS_COOLDOWN      = 3,  // Event passed — waiting for reset conditions
   NEWS_POST_COOLDOWN = 4   // Post-news 30-min additional buffer
};

//===================================================================
// EQUITY PROTECTION TIER
// Drives sizing reduction and potential suspension.
//===================================================================
enum EQUITY_TIER
{
   EQUITY_TIER_NORMAL   = 0,  // Above Tier 1 threshold — no action
   EQUITY_TIER_WARNING  = 1,  // Within 5% of floor — log only
   EQUITY_TIER_REDUCE   = 2,  // Within 7% of floor — 50% sizing
   EQUITY_TIER_PROTECT  = 3   // Within $200 of floor — close + suspend
};

//===================================================================
// GUARD METADATA
// Registered in GuardCoordinator to describe each guard.
// Used for logging, diagnostics, and initialization tracking.
//===================================================================
struct GuardMetadata
{
   int            index;          // 1–10 (execution order)
   GUARD_PRIORITY priority;       // Matches index in canonical order
   string         name;           // "PROP_FIRM", "EQUITY", etc.
   string         description;    // One-line purpose
   bool           initialized;    // Has Init() succeeded
   bool           enabled;        // Can be disabled for testing
   int            eval_count;     // Total evaluations since init
   int            block_count;    // Times it returned BLOCK
   int            suspend_count;  // Times it returned SUSPEND
   int            fatal_count;    // Times it returned FATAL
   datetime       last_trigger;   // When it last triggered (non-PASS)
};

//===================================================================
// SHARED GUARD UTILITY FUNCTIONS
//
// Pure functions — no state, no side effects.
// Used by multiple guards — defined once here.
//===================================================================

//--- Build a standard PASS result for a guard
GuardEvalResult GuardPass(GUARD_PRIORITY prio, string name, int index)
{
   GuardEvalResult r;
   r.status        = GUARD_PASS;
   r.guard_priority = prio;
   r.guard_name    = name;
   r.guard_index   = index;
   r.eval_time     = TimeCurrent();
   return r;
}

//--- Build a BLOCK result
GuardEvalResult GuardBlock(GUARD_PRIORITY prio, string name, int index,
                            string detail, string resume_cond = "")
{
   GuardEvalResult r;
   r.status          = GUARD_BLOCK;
   r.guard_priority  = prio;
   r.guard_name      = name;
   r.guard_index     = index;
   r.detail          = detail;
   r.resume_condition = resume_cond;
   r.eval_time       = TimeCurrent();
   return r;
}

//--- Build a SUSPEND result
GuardEvalResult GuardSuspend(GUARD_PRIORITY prio, string name, int index,
                              SUSPEND_REASON reason, string detail,
                              string resume_cond = "",
                              bool close_req = false,
                              bool alert = false)
{
   GuardEvalResult r;
   r.status          = GUARD_SUSPEND;
   r.guard_priority  = prio;
   r.guard_name      = name;
   r.guard_index     = index;
   r.suspend_reason  = reason;
   r.detail          = detail;
   r.resume_condition = resume_cond;
   r.close_required  = close_req;
   r.alert_trader    = alert;
   r.eval_time       = TimeCurrent();
   return r;
}

//--- Build a FATAL result
GuardEvalResult GuardFatal(GUARD_PRIORITY prio, string name, int index,
                            SUSPEND_REASON reason, string detail,
                            bool close_req = true)
{
   GuardEvalResult r;
   r.status          = GUARD_FATAL;
   r.guard_priority  = prio;
   r.guard_name      = name;
   r.guard_index     = index;
   r.suspend_reason  = reason;
   r.detail          = detail;
   r.close_required  = close_req;
   r.alert_trader    = true;    // FATAL always alerts
   r.eval_time       = TimeCurrent();
   return r;
}

//--- Build a PASS result with size reduction
GuardEvalResult GuardPassReduced(GUARD_PRIORITY prio, string name, int index,
                                  double mult, string detail)
{
   GuardEvalResult r = GuardPass(prio, name, index);
   r.size_reduced    = true;
   r.size_multiplier = mult;
   r.detail          = detail;
   return r;
}

//--- Convert GuardEvalResult to log-friendly string
string GuardResultToString(const GuardEvalResult &r)
{
   string status_str;
   switch(r.status)
   {
      case GUARD_PASS:    status_str = "PASS";    break;
      case GUARD_BLOCK:   status_str = "BLOCK";   break;
      case GUARD_SUSPEND: status_str = "SUSPEND"; break;
      case GUARD_FATAL:   status_str = "FATAL";   break;
      default:            status_str = "UNKNOWN"; break;
   }

   return StringFormat(
      "status=%s guard=%s index=%d reason=%s detail=%s",
      status_str,
      r.guard_name,
      r.guard_index,
      EnumToString(r.suspend_reason),
      r.detail
   );
}

//--- Populate a GuardContext from live broker data
//    Called ONCE per tick by GuardCoordinator before evaluation chain
void PopulateGuardContext(GuardContext &ctx, long magic_number, double pip_size)
{
   ctx.equity          = AccountInfoDouble(ACCOUNT_EQUITY);
   ctx.balance         = AccountInfoDouble(ACCOUNT_BALANCE);
   ctx.floating_pnl    = ctx.equity - ctx.balance;

   ctx.current_bid     = SymbolInfoDouble(EA_SYMBOL, SYMBOL_BID);
   ctx.current_ask     = SymbolInfoDouble(EA_SYMBOL, SYMBOL_ASK);
   ctx.current_spread_pips = (pip_size > 0)
                           ? (ctx.current_ask - ctx.current_bid) / pip_size
                           : 0.0;

   ctx.server_time     = TimeCurrent();
   ctx.gmt_time        = EAGmtNow();          // A336 (#20): real GMT live, server-offset GMT in the tester

   MqlDateTime gmt_dt;
   TimeToStruct(ctx.gmt_time, gmt_dt);
   ctx.gmt_hour        = gmt_dt.hour;
   ctx.gmt_minute      = gmt_dt.min;
   ctx.day_of_week     = gmt_dt.day_of_week;  // 0=Sun, 6=Sat

   ctx.is_weekend      = (ctx.day_of_week == 0 || ctx.day_of_week == 6);
   ctx.is_friday       = (ctx.day_of_week == 5);
   ctx.is_monday       = (ctx.day_of_week == 1);

   // Count positions with our magic number
   ctx.open_positions  = 0;
   ctx.has_our_position = false;
   ctx.our_ticket      = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == EA_SYMBOL &&
         PositionGetInteger(POSITION_MAGIC) == magic_number)
      {
         ctx.open_positions++;
         ctx.has_our_position = true;
         ctx.our_ticket = ticket;  // Keeps last found (should be only 1)
      }
   }
}

//===================================================================
// GUARD BASE INTERFACE
//
// MQL5 does not support true interfaces with pure virtual methods
// in the same way as C++. We use an abstract base class pattern
// with virtual methods that must be overridden.
//
// RULES FOR IMPLEMENTING CLASSES:
//   1. Override ALL virtual methods — never call base implementations
//   2. Init() must return false if the guard cannot safely operate
//   3. Evaluate() must ALWAYS return a GuardEvalResult — never throw
//   4. Evaluate() must be deterministic: same context = same result
//   5. Evaluate() must NOT modify external state (no StateManager calls)
//      Exception: only the coordinator calls StateManager
//   6. CheckResume() must be idempotent — safe to call every tick
//===================================================================
class IGuard
{
protected:
   GuardMetadata  m_meta;
   bool           m_initialized;

public:
   IGuard() : m_initialized(false) {}
   virtual ~IGuard() {}

   //--- Initialize the guard — called once at EA start
   //    Returns false if guard cannot operate (EA should halt or warn)
   virtual bool Init() = 0;

   //--- Evaluate current conditions — called every tick by coordinator
   //    Must NOT modify state. Must NOT log excessively (only on change).
   //    MUST return in microseconds — no blocking I/O inside Evaluate().
   virtual GuardEvalResult Evaluate(const GuardContext &ctx) = 0;

   //--- Check whether suspension resume conditions are met
   //    Called every tick when EA is in STATE_SUSPENDED
   //    Returns true = resume condition is satisfied
   //    Returns false = still suspended
   virtual bool CheckResume(const GuardContext &ctx) = 0;

   //--- Persist any guard state to disk (called from OnDeinit and timer)
   virtual void SaveState() {}

   //--- Load state from disk (called from Init after boot)
   virtual void LoadState() {}

   //--- Clean shutdown
   virtual void Shutdown() { m_initialized = false; }

   //--- Getters
   GuardMetadata GetMetadata()  const { return m_meta; }
   bool          IsInitialized() const { return m_initialized; }
   bool          IsEnabled()     const { return m_meta.enabled; }
   string        GetName()       const { return m_meta.name; }
   int           GetIndex()      const { return m_meta.index; }

protected:
   //--- Called by subclasses to record a non-PASS evaluation
   void RecordTrigger(GUARD_RESULT result)
   {
      m_meta.eval_count++;
      m_meta.last_trigger = TimeCurrent();
      switch(result)
      {
         case GUARD_BLOCK:   m_meta.block_count++;   break;
         case GUARD_SUSPEND: m_meta.suspend_count++; break;
         case GUARD_FATAL:   m_meta.fatal_count++;   break;
         default: break;
      }
   }

   void RecordEval() { m_meta.eval_count++; }
};

//===================================================================
// GUARD SUSPENSION DESCRIPTOR TABLE
//
// For each SUSPEND_REASON, defines:
//   - display name
//   - severity (LOG_LEVEL to use)
//   - whether manual reset is required
//   - whether position close is required
//   - alert trader flag
//
// Used by GuardCoordinator for consistent handling without
// duplicating this logic in each guard class.
//===================================================================
struct SuspendDescriptor
{
   SUSPEND_REASON reason;
   string         name;
   LOG_LEVEL      severity;
   bool           manual_reset_required;
   bool           close_position;
   bool           alert_trader;
   string         resume_description;
};

//--- Look up descriptor for a suspension reason (switch-based — MQL5 safe)
//    Replaces static array initializer which is not valid in MQL5
SuspendDescriptor GetSuspendDescriptor(SUSPEND_REASON reason)
{
   SuspendDescriptor d;
   d.reason = reason;

   switch(reason)
   {
      case SUSPEND_NONE:
         d.name="NONE"; d.severity=LOG_DEBUG;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="N/A"; break;

      case SUSPEND_SESSION_CLOSED:
         d.name="SESSION_CLOSED"; d.severity=LOG_INFO;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes when valid session begins"; break;

      case SUSPEND_ROLLOVER:
         d.name="ROLLOVER"; d.severity=LOG_INFO;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes after 00:15 GMT"; break;

      case SUSPEND_NEWS_WINDOW:
         d.name="NEWS_WINDOW"; d.severity=LOG_WARN;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes when ATR/spread normalise + 60min cooldown"; break;

      case SUSPEND_SPREAD_HIGH:
         d.name="SPREAD_HIGH"; d.severity=LOG_INFO;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes when spread normalises"; break;

      case SUSPEND_EQUITY_FLOOR:
         d.name="EQUITY_FLOOR"; d.severity=LOG_CRITICAL;
         d.manual_reset_required=true; d.close_position=true; d.alert_trader=true;
         d.resume_description="MANUAL RESET REQUIRED — equity floor breached"; break;

      case SUSPEND_DAILY_LIMIT:
         d.name="DAILY_LIMIT"; d.severity=LOG_WARN;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes at next GMT day rollover (00:01)"; break;

      case SUSPEND_MAX_TRADES:
         d.name="MAX_TRADES"; d.severity=LOG_INFO;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes at next GMT day rollover"; break;

      case SUSPEND_CONSEC_LOSSES:
         d.name="CONSEC_LOSSES"; d.severity=LOG_WARN;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes after 1-hour pause"; break;

      case SUSPEND_CIRCUIT_BREAKER:
         d.name="CIRCUIT_BREAKER"; d.severity=LOG_WARN;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes after cooldown + 5-condition reset"; break;

      case SUSPEND_PERF_CRITICAL:
         d.name="PERF_CRITICAL"; d.severity=LOG_ERROR;
         d.manual_reset_required=true; d.close_position=false; d.alert_trader=true;
         d.resume_description="MANUAL REVIEW REQUIRED — strategy edge degraded"; break;

      case SUSPEND_DISCONNECT:
         d.name="DISCONNECT"; d.severity=LOG_ERROR;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes after reconnect + state reconciliation"; break;

      case SUSPEND_MANUAL:
         d.name="MANUAL"; d.severity=LOG_WARN;
         d.manual_reset_required=true; d.close_position=false; d.alert_trader=false;
         d.resume_description="Resumes when inp_ManualSuspend=false + restart"; break;

      case SUSPEND_PROP_FIRM_LOCK:
         d.name="PROP_FIRM_LOCK"; d.severity=LOG_CRITICAL;
         d.manual_reset_required=true; d.close_position=true; d.alert_trader=true;
         d.resume_description="MANUAL RESET — prop firm hard floor triggered"; break;

      case SUSPEND_SYSTEM_HEALTH:
         d.name="SYSTEM_HEALTH"; d.severity=LOG_ERROR;
         d.manual_reset_required=false; d.close_position=false; d.alert_trader=true;
         d.resume_description="Resumes when all health checks pass"; break;

      case SUSPEND_EQUITY_PROTECT:
         d.name="EQUITY_PROTECT"; d.severity=LOG_CRITICAL;
         d.manual_reset_required=false; d.close_position=true; d.alert_trader=true;
         d.resume_description="Resumes when equity recovers above Tier 3 threshold"; break;

      case SUSPEND_PROFIT_TARGET:
         d.name="PROFIT_TARGET"; d.severity=LOG_INFO;
         d.manual_reset_required=true; d.close_position=true; d.alert_trader=true;
         d.resume_description="CHALLENGE COMPLETE — manual restart required"; break;

      default:
         d.name="UNKNOWN"; d.severity=LOG_ERROR;
         d.manual_reset_required=true; d.close_position=false; d.alert_trader=true;
         d.resume_description="Unknown suspension — manual review required"; break;
   }
   return d;
}


#endif // GUARDTYPES_MQH
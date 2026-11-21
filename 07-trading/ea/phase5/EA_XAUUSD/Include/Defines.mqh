
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Shared Definitions                      |
//| File: Include/Defines.mqh                                         |
//| Purpose: All enums, constants, and shared data structures         |
//| Phase: 1 — Core Framework                                         |
//| RULES: No trading logic. No indicator calls. Pure definitions.    |
//+------------------------------------------------------------------+
#ifndef DEFINES_MQH
#define DEFINES_MQH

//===================================================================
// VERSION & BUILD IDENTITY
//===================================================================
#define EA_NAME          "XAUUSD_INST_EA"
#define EA_VERSION       "1.0.0"
#define EA_BUILD_DATE    "2026.05.22"
#define EA_SYMBOL        _Symbol    // A320: chart symbol (brokers use XAUUSD.r, GOLD ...)

//===================================================================
// EA MASTER STATES
// PSEUDO-CODE RATIONALE:
//   State machine drives ALL behavior. Every action derives from state.
//   No logic should execute without first checking current state.
//   States are exclusive — EA is in exactly one state at all times.
//===================================================================
enum EA_STATE
{
   STATE_INITIALIZING    = 0,  // Boot phase — loading data, validating
   STATE_GUARD_CHECK     = 1,  // Guard layer evaluation each tick
   STATE_SEEK_ENTRY      = 2,  // No position — evaluating setup
   STATE_MANAGE_TRADE    = 3,  // Position open — managing it
   STATE_SUSPENDED       = 4,  // Blocked — sub-reason in SuspendReason
   STATE_PROFIT_TARGET   = 5,  // Terminal — target reached, await manual
   STATE_FATAL_ERROR     = 6   // Terminal — critical failure, EA halted
};

//===================================================================
// SUSPENSION SUBSTATES
// Reason WHY the EA is in STATE_SUSPENDED.
// Each has its own resume condition and no shared logic.
//===================================================================
enum SUSPEND_REASON
{
   SUSPEND_NONE             = 0,  // Not suspended
   SUSPEND_SESSION_CLOSED   = 1,  // Outside valid session window
   SUSPEND_ROLLOVER         = 2,  // 21:45–00:15 GMT blackout
   SUSPEND_NEWS_WINDOW      = 3,  // Near scheduled high-impact news
   SUSPEND_SPREAD_HIGH      = 4,  // Spread exceeds dynamic threshold
   SUSPEND_EQUITY_FLOOR     = 5,  // HARD STOP — equity <= $9,100
   SUSPEND_DAILY_LIMIT      = 6,  // Daily P&L <= -$300 (3% self-limit)
   SUSPEND_MAX_TRADES       = 7,  // 3 trades executed today
   SUSPEND_CONSEC_LOSSES    = 8,  // 3 consecutive losses — 1hr pause
   SUSPEND_CIRCUIT_BREAKER  = 9,  // Volatility event — timed cooldown
   SUSPEND_PERF_CRITICAL    = 10, // Performance degradation Level 3
   SUSPEND_DISCONNECT       = 11, // VPS/broker disconnected
   SUSPEND_MANUAL           = 12, // Manual override by trader
   // Phase 2 additions — guard-specific suspension reasons
   SUSPEND_PROP_FIRM_LOCK   = 13, // PropFirmGuard hard floor — PERMANENT
   SUSPEND_SYSTEM_HEALTH    = 14, // SystemHealthCheck infrastructure failure
   SUSPEND_EQUITY_PROTECT   = 15, // EquityGuard Tier 3 — close + suspend
   SUSPEND_PROFIT_TARGET    = 16  // Profit target reached — terminal
};

//===================================================================
// MARKET REGIME STATES
//===================================================================
enum REGIME_STATE
{
   REGIME_RANGING          = 0,  // Score < 3 — no entries
   REGIME_WEAK_BULL        = 1,  // Score 3–4, bullish
   REGIME_WEAK_BEAR        = 2,  // Score 3–4, bearish
   REGIME_TRENDING_BULL    = 3,  // Score 5–6, bullish
   REGIME_TRENDING_BEAR    = 4,  // Score 5–6, bearish
   REGIME_TRANSITIONING    = 5,  // Between states — reduced sizing
   REGIME_UNKNOWN          = 6   // Insufficient data (init period)
};

//===================================================================
// SESSION STATES
//===================================================================
enum SESSION_STATE
{
   SESSION_ASIAN          = 0,  // 00:15–05:00 GMT — no entries
   SESSION_PRE_LONDON     = 1,  // 05:00–07:00 GMT — prep, no entries
   SESSION_LONDON_PRIME   = 2,  // 07:00–12:00 GMT — primary window
   SESSION_INTER          = 3,  // 12:00–13:00 GMT — gap, no entries
   SESSION_NY_PRIME       = 4,  // 13:00–17:00 GMT — secondary window
   SESSION_POST_NY        = 5,  // 17:00–21:45 GMT — no entries
   SESSION_ROLLOVER       = 6,  // 21:45–00:15 GMT — HARD blackout
   SESSION_WEEKEND        = 7   // Saturday/Sunday — hard block
};

//===================================================================
// TRADE DIRECTION
//===================================================================
enum TRADE_DIR
{
   DIR_NONE  = 0,
   DIR_LONG  = 1,
   DIR_SHORT = -1
};

//===================================================================
// GUARD RESULTS — each guard returns one of these
//===================================================================
enum GUARD_RESULT
{
   GUARD_PASS    = 0,  // Allow processing to continue
   GUARD_BLOCK   = 1,  // Block entry this tick, but do not suspend
   GUARD_SUSPEND = 2,  // Suspend EA (set SUSPEND_REASON)
   GUARD_FATAL   = 3   // Unrecoverable — halt EA immediately
};

//===================================================================
// CIRCUIT BREAKER TRIGGER TYPES
//===================================================================
enum CB_TRIGGER
{
   CB_NONE              = 0,
   CB_ATR_SPIKE         = 1,  // Current range > 2.5× ATR
   CB_CONSEC_EXPANSION  = 2,  // 3 candles all > 1.8× ATR
   CB_PRICE_VELOCITY    = 3,  // 40+ pips in under 2 minutes
   CB_SPREAD_VOL_COMBO  = 4   // Spread spike + ATR spike together
};

//===================================================================
// LOG SEVERITY LEVELS
//===================================================================
enum LOG_LEVEL
{
   LOG_TRACE    = 0,   // Verbose debug — production OFF
   LOG_DEBUG    = 1,   // Dev/backtest only — production OFF
   LOG_INFO     = 2,   // Normal operational events
   LOG_WARN     = 3,   // Unexpected but non-critical
   LOG_ERROR    = 4,   // Failed operations needing attention
   LOG_CRITICAL = 5,   // Immediate attention — alert trader
   LOG_FATAL    = 6    // EA cannot continue — halt
};

//===================================================================
// TRADE CLOSE REASONS (written to trade_log.csv)
//===================================================================
enum CLOSE_REASON
{
   CLOSE_TP2              = 0,  // Full TP2 hit
   CLOSE_SL               = 1,  // Stop loss hit
   CLOSE_PARTIAL_TP1      = 2,  // Partial close at TP1
   CLOSE_BREAKEVEN        = 3,  // Trailing closed at breakeven
   CLOSE_TRAIL            = 4,  // Trailing stop triggered
   CLOSE_EMERGENCY_EQUITY = 5,  // Equity floor breach
   CLOSE_EMERGENCY_PERF   = 6,  // Performance degradation suspend
   CLOSE_MANUAL           = 7,  // Trader closed manually
   CLOSE_DISCONNECT_SAFE  = 8,  // Closed during VPS reconnect
   CLOSE_UNKNOWN          = 9   // Cannot determine (post-reconnect)
};

//===================================================================
// PERFORMANCE ALERT LEVELS
//===================================================================
enum PERF_ALERT_LEVEL
{
   PERF_NORMAL    = 0,  // Within expected parameters
   PERF_WARNING   = 1,  // Log warning, no restriction
   PERF_DEGRADED  = 2,  // Reduced sizing + higher threshold
   PERF_CRITICAL  = 3   // Suspend all entries
};

//===================================================================
// ORDER RETRY OPERATION TYPES
//===================================================================
enum RETRY_OP
{
   RETRY_ORDER_SEND    = 0,
   RETRY_SL_MODIFY     = 1,
   RETRY_TP_MODIFY     = 2,
   RETRY_PARTIAL_CLOSE = 3,
   RETRY_FULL_CLOSE    = 4
};

//===================================================================
// SHARED DATA STRUCTURES
//===================================================================

// Active trade state — written to disk for orphan recovery
struct TradeState
{
   ulong    ticket;           // MT5 position ticket
   TRADE_DIR direction;       // LONG or SHORT
   double   lot_size;         // Actual lot opened
   double   entry_price;      // Actual fill price
   double   sl_price;         // Current stop loss
   double   tp1_price;        // Partial close target (1.5R)
   double   tp2_price;        // Full close target (2.5R)
   double   sl_original;      // Original SL (never modified back)
   double   sl_pips;          // SL distance in pips at entry
   bool     partial_done;     // Has TP1 partial close been executed
   bool     trail_active;     // Is trailing stop active
   bool     at_breakeven;     // Has SL been moved to BE
   datetime open_time;        // Entry timestamp (server time)
   int      score;            // Trade score at entry (×10, e.g. 78 = 7.8)
   REGIME_STATE regime;       // Regime at time of entry
   SESSION_STATE session;     // Session at time of entry
};

// Daily statistics — reset at 00:01 GMT
struct DailyStatsData
{
   datetime reset_date;       // Date this struct covers
   double   open_equity;      // Equity at start of day
   double   closed_pnl;       // Sum of all closed P&L today
   double   peak_equity;      // Highest equity seen today
   double   min_equity;       // Lowest equity seen today
   int      trade_count;      // Trades opened today
   int      wins;             // Winning trades today
   int      losses;           // Losing trades today
   int      consec_losses;    // Current consecutive loss streak
   datetime last_close_time;  // When last trade closed
};

// Rolling performance window
struct PerfWindow
{
   int      window_size;      // 5 or 20
   int      trade_count;
   int      wins;
   double   total_rr;         // Sum of achieved RR
   double   gross_profit;
   double   gross_loss;
   double   win_rate;         // Computed: wins/trade_count
   double   profit_factor;    // Computed: gross_profit/gross_loss
   double   avg_rr;           // Computed: total_rr/trade_count
   PERF_ALERT_LEVEL alert_level;
};

// Retry queue entry
struct RetryEntry
{
   RETRY_OP   operation;
   ulong      ticket;
   double     param1;         // Context-dependent (new SL, lot, etc.)
   double     param2;
   int        attempts;
   int        max_attempts;
   datetime   next_retry_time;
   bool       active;
};

// Spread sample for dynamic spread model
struct SpreadSample
{
   double   min_spread;
   double   max_spread;
   double   avg_spread;
   double   p95_spread;       // 95th percentile
   int      sample_count;
   datetime last_updated;
};

// Circuit breaker event
struct CBEvent
{
   CB_TRIGGER   trigger_type;
   datetime     trigger_time;
   int          cooldown_seconds;
   datetime     resume_time;
   bool         active;
   double       atr_at_trigger;
   double       spread_at_trigger;
};

//===================================================================
// POOL_TYPE — categories of liquidity pools tracked by LiquidityEngine
//===================================================================
enum POOL_TYPE
{
   POOL_NONE           = 0,
   POOL_EQUAL_HIGHS    = 1,   // 2+ swing highs clustered — Tier 2
   POOL_EQUAL_LOWS     = 2,   // 2+ swing lows clustered — Tier 2
   POOL_PDH            = 3,   // Previous Day High — Tier 1
   POOL_PDL            = 4,   // Previous Day Low  — Tier 1
   POOL_ASIAN_HIGH     = 5,   // Asian session high — Tier 1
   POOL_ASIAN_LOW      = 6,   // Asian session low  — Tier 1
   POOL_ROUND          = 7    // Round number ($XX00 / $XX50) — Tier 3
};

//===================================================================
// SWEEP_STATE — per-pool sweep state machine
//===================================================================
enum SWEEP_STATE
{
   SWEEP_CLEAN           = 0,  // No interaction yet
   SWEEP_PIERCED         = 1,  // Wick crossed level this bar
   SWEEP_SWEPT_PENDING   = 2,  // Pierced earlier, in reclose window
   SWEEP_SWEPT_CONFIRMED = 3,  // Pierce + reclose within window
   SWEEP_BROKEN          = 4   // Window expired without reclose
};

//===================================================================
// LiquidityPool — a level where liquidity sits
//===================================================================
struct LiquidityPool
{
   POOL_TYPE     type;
   double        price_level;
   double        width_pips;         // Tolerance band width
   datetime      formed_at;
   int           touch_count;        // Times price has tested (max LIQ_TOUCH_COUNT_CAP)
   bool          is_upside;          // true = upside pool (highs); false = downside (lows)
   bool          active;             // Still relevant

   // Sweep state machine (per-pool)
   SWEEP_STATE   sweep_state;
   datetime      pierced_at;
   int           pierce_bar_idx;     // M15 bar # when pierced
   double        pierce_extreme;     // Wick extreme reached
   datetime      swept_at;

   // Decay tracking (Equal Highs/Lows only)
   int           decay_close_count;  // Consecutive closes beyond decay threshold
};

// Swing point (used by structure engine)
struct SwingPoint
{
   double   price;
   datetime time;
   bool     is_high;          // true = swing high, false = swing low
   bool     confirmed;        // Requires 2-candle right-side confirmation
   ENUM_TIMEFRAMES timeframe;
};

// Liquidity zone
struct LiqZone
{
   double   price_high;
   double   price_low;
   int      zone_type;        // 1=session HL, 2=swing pool, 3=round, 4=PDH/PDL
   datetime created;
   bool     active;
   string   label;
};

//===================================================================
// NUMERIC CONSTANTS — Risk parameters
// These are NOT optimization targets. They are structural constants
// derived from Gold's behavior and The5%ers rules.
// DO NOT optimize these against historical data.
//===================================================================
#define RISK_PCT_NORMAL       0.0075   // 0.75% equity per trade
#define RISK_PCT_DEGRADED     0.00375  // 50% when perf degraded
#define LOT_HARD_CAP          0.10     // Never exceed regardless of calc
#define LOT_MINIMUM           0.01

#define SL_PIPS_MIN           30.0     // Gold noise floor
#define SL_PIPS_MAX           80.0     // If wider needed, skip trade
#define SL_ATR_MULT           1.5      // SL = ATR × this multiplier
#define SL_STRUCT_BUFFER_PIPS 15.0     // Pips beyond swing structure
#define BREAKEVEN_OFFSET_PIPS 2.0      // SL moved to entry + this

#define TP1_RR                1.5      // Partial close at 1.5R
#define TP2_RR                2.5      // Full close at 2.5R
#define PARTIAL_CLOSE_PCT     0.50     // Close 50% at TP1

#define TRAIL_ATR_MULT        0.75     // Trail = ATR × this
#define TRAIL_MIN_PIPS        20.0     // Minimum trail distance
#define TRAIL_MAX_PIPS        50.0     // Maximum trail distance
#define TRAIL_STEP_MIN_PIPS   5.0      // Minimum SL move to bother modifying

#define EQUITY_FLOOR          9100.0   // Hard close level ($10K account)
#define EQUITY_TARGET         11000.0  // Challenge target ($10K + 10%)
#define DAILY_LOSS_LIMIT      300.0    // Own daily limit (3% of $10K)

#define MAX_DAILY_TRADES      3
#define CONSEC_LOSS_LIMIT     3        // Trigger 1hr pause
#define CONSEC_LOSS_PAUSE_SEC 3600     // 1 hour in seconds
#define MIN_TRADE_DURATION    300      // 5 minutes minimum

#define SPREAD_HARD_CAP_PIPS  0.80      // Fallback if no calibration data
#define SPREAD_REAL_RR_MIN    1.5      // Minimum real RR after spread
#define SPREAD_SPIKE_RATIO    3.0      // Ratio to average = spike
#define SPREAD_CALIBRATION_DAYS 3      // Days before dynamic threshold

#define ATR_TOO_QUIET_PIPS    5.0      // Below this: skip
#define ATR_NEWS_SPIKE_PIPS   40.0     // Above this: unconditionally unsafe (absolute override)
#define ATR_CB_SPIKE_MULT     2.5      // CB: range > this × ATR14
#define ATR_CB_EXPAND_MULT    1.8      // CB: consec expansion trigger

// RegimeEngine scoring constants
// DO NOT optimize — these are structural constants derived from Gold behavior
#define REGIME_EMA50_SLOPE_MIN    2.0    // Pips/bar minimum for directional slope
#define REGIME_EMA200_BUFFER      50.0   // Pips buffer: price must be this far from EMA200
#define REGIME_ATR_EXPAND_RATIO   1.10   // ATR ratio above this = expanding (component pass)
#define REGIME_ATR_CONTRACT_RATIO 0.80   // ATR ratio below this = contracting (penalty)
#define REGIME_STRUCT_CLARITY_MIN 0.50   // Min H4 clarity for structure component pass
#define REGIME_INSIDE_BAR_MAX     1      // Max inside bars in last 5 H4 bars before penalty
#define REGIME_INSIDE_BAR_WINDOW  5      // H4 bars examined for inside bar check
#define REGIME_LOOKBACK_H4        20     // H4 bars minimum before regime is valid
#define REGIME_EMA_SLOPE_WINDOW   3      // H4 bars to measure EMA50 slope over
#define REGIME_AGING_BARS         12     // H4 bars = 48 hours — aging flag threshold
#define REGIME_STALE_SEC          20000  // > ~5.5 H4 bars without update = stale

// VolatilityEngine ATR ratio thresholds
// VolatilityEngine ATR ratio thresholds (primary classifier)
// Ratio = current ATR / session_baseline_ATR
// All thresholds derived from Gold behavior — do NOT optimize
#define VOL_RATIO_TOO_QUIET   0.40     // < 0.40: below spread cost viability
#define VOL_RATIO_SUPPRESSED  0.70     // 0.40–0.70: below normal baseline
#define VOL_RATIO_NORMAL_HI   1.40     // 0.70–1.40: ideal conditions
#define VOL_RATIO_ELEVATED_HI 2.20     // 1.40–2.20: above average
                                       // > 2.20: spike territory
#define VOL_RATIO_SPIKE       2.20     // >= this: VOL_SPIKE
#define VOL_RANGE_SPIKE_MULT  2.50     // Last candle range > this × ATR = NEWS_SPIKE
#define VOL_BASELINE_FALLBACK 7.5      // Pips: used when SpreadGuard uncalibrated
#define VOL_STABILITY_WINDOW  5        // M15 bars for ATR trend (expanding/contracting)
#define VOL_ATR_PERIOD        14       // ATR period (matches Config.ATRPeriod default)
#define VOL_LOOKBACK_M15      50       // M15 bars for ATR calculation
#define VOL_LOOKBACK_M5       20       // M5 bars for range tracking
#define VOL_STALE_SEC         3600     // > 1 hour without update = stale result

#define ENTRY_JITTER_MIN_SEC  12       // Minimum randomization delay
#define ENTRY_JITTER_MAX_SEC  90       // Maximum randomization delay
#define LOT_VARIATION_MIN     0.95     // Lot micro-variation lower bound
#define LOT_VARIATION_MAX     1.05     // Lot micro-variation upper bound

#define STALE_PRICE_SEC       30       // No tick for this long = stale
#define SLIPPAGE_MAX_PIPS     0.50      // Max acceptable entry slippage

#define SWING_CONFIRM_BARS    2        // Bars right of swing for confirm
#define SWING_POOL_PIPS       20.0     // Swings within this = a "pool"

// Minimum swing size per timeframe (below this = noise, not structure)
// Calibrated to Gold's structural behavior — do NOT optimize these.
#define SWING_MIN_PIPS_H4     150.0    // H4: 150 pip minimum swing
#define SWING_MIN_PIPS_H1      60.0    // H1:  60 pip minimum swing
#define SWING_MIN_PIPS_M15     25.0    // M15: 25 pip minimum swing

// Maximum lookback bars per timeframe for structure detection
#define SWING_LOOKBACK_H4      50      // H4 candles (200 hours)
#define SWING_LOOKBACK_H1     100      // H1 candles (100 hours)
#define SWING_LOOKBACK_M15    100      // M15 candles (25 hours)
#define PRICE_BUFFER_MAX      100     // Max lookback across all TF — size price buffers to this

// Minimum confirmed swings required before structure is considered valid
#define SWING_MIN_CONFIRMED     2      // Per timeframe
#define ROUND_NUM_STEP        50.0     // Round number interval ($50)
#define ROUND_NUM_PROXIMITY   25.0     // "Near" a round number (pips)

// LiquidityEngine constants
// Pool detection
#define LIQ_ACTIVE_POOLS_MAX      16    // Max simultaneous active pools
#define LIQ_EQUAL_PIPS_TOL         3.0  // Swings within N pips = same cluster
#define LIQ_EQUAL_MIN_SWINGS       2    // Min swings for Equal Highs/Lows pool
#define LIQ_POOL_PROXIMITY_PIPS   30.0  // "Near a pool" threshold (pips)
#define LIQ_ROUND_LOOKUP_RANGE   200.0  // Round numbers within N pips of price
#define LIQ_TOUCH_TOL_PIPS         5.0  // Wick within N pips = counted as touch
#define LIQ_TOUCH_COUNT_CAP        10   // Max touch_count for any pool
#define LIQ_DECAY_PIPS            30.0  // Decay: closes N pips beyond level
#define LIQ_DECAY_BARS             2    // Decay: N consecutive closes required

// Asian session (22:00 GMT — 06:00 GMT next day)
#define LIQ_ASIAN_START_HR        22   // Asian session start (GMT hour)
#define LIQ_ASIAN_END_HR           6   // Asian session end (GMT hour)
#define LIQ_ASIAN_M1_LOOKBACK    480   // M1 bars covered (8h * 60min)

// Sweep window per tier (M15 candles)
#define LIQ_SWEEP_WINDOW_TIER1     3   // PDH, PDL, Asian H/L
#define LIQ_SWEEP_WINDOW_TIER2     2   // Equal Highs, Equal Lows
#define LIQ_SWEEP_WINDOW_TIER3     1   // Round Numbers
#define LIQ_SWEEP_RELEVANCE_BARS   5   // Sweep events fresh for N M15 bars
#define LIQ_SWEEP_EVENT_BUFFER     5   // Ring buffer size for recent sweeps
#define LIQ_WICK_MIN_PIP_NOISE     1.0 // Wicks under N pips = noise, not pierce
#define LIQ_ATR_FALLBACK_PIPS      7.5 // Fallback ATR if not injected

#define LIQ_STALE_SEC           2700   // > 3 M15 bars without update = stale

// RegimePersistenceModel constants
#define PERSIST_STARTUP_CONFIRM_BARS  2   // H4 bars before first regime adoption
#define PERSIST_TREND_TO_RANGE_BARS   3   // H4 bars to confirm trend -> range
#define PERSIST_RANGE_TO_TREND_BARS   2   // H4 bars to confirm range -> trend
#define PERSIST_TRANSITION_MAX_BARS   3   // Max H4 bars in TRANSITIONING state
#define PERSIST_NORMAL_SIZING       1.0   // Confirmed: full size
#define PERSIST_TRANSITION_SIZING   0.5   // Transitioning: half size
#define PERSIST_THRESHOLD_NORMAL    0.0   // Confirmed: no threshold adjustment
#define PERSIST_THRESHOLD_TRANSITION 1.0  // Transitioning: +1.0 score threshold
#define PERSIST_HISTORY_MAX         20    // H4 bar score history retained
#define PERSIST_FILE_NAME           "EA_XAUUSD_regime_persist.txt"
#define PERSIST_FILE_MAX_AGE_SEC    28800 // 8 hours - discard older state

// TrendEngine constants
#define TREND_EMA_MIN_SEP_PIPS     10.0  // Minimum EMA20-EMA50 gap for alignment
#define TREND_POSITION_MIN_PIPS     5.0  // Price-EMA20 distance for alignment
#define TREND_CROSS_LOOKBACK         3   // H1 bars to check for recent EMA cross
#define TREND_LOOKBACK_H1            5   // EMA buffer depth
#define TREND_CANDLE_BUFFER          4   // H1 candles for engulfing detection
#define TREND_ENGULF_WINDOW          3   // Recent H1 bars examined for engulfing
#define TREND_ENGULF_CONF_PENALTY  0.10  // Confidence reduction on opposing engulf
#define TREND_STRONG_CONF_BONUS    0.10  // Confidence bonus for 3-of-3 alignment
#define TREND_W_EMA                0.40  // EMA alignment weight
#define TREND_W_STRUCTURE          0.35  // Swing structure weight
#define TREND_W_POSITION           0.25  // Price position weight
#define TREND_EMA_FULL_SEP_PIPS    30.0  // EMA sep = full observation score
#define TREND_POSITION_FULL_PIPS   30.0  // Position distance = full score
#define TREND_STALE_SEC           7200   // > 2 H1 bars without update = stale
#define TREND_ASIAN_CONF_SCALE     0.80  // Confidence x this during Asian session

#define SCORE_THRESHOLD_NORMAL     6.5
#define SCORE_THRESHOLD_CONSERV    7.5  // Used in transitioning/degraded
#define SCORE_SIZE_BOOST_1         7.5  // Score above this = +10% size
#define SCORE_SIZE_BOOST_2         8.5  // Score above this = +20% size

#define LIQUIDITY_SCORE_MIN   0.50     // Below this: skip trade
#define SESSION_LEVEL_PIPS    15.0     // Near session H/L zone

#define TRADE_COOLDOWN_SEC    900      // 15 minutes between trades
#define PERF_WINDOW_SHORT     5        // Short rolling window size
#define PERF_WINDOW_LONG      20       // Long rolling window size
#define PERF_MIN_TRADES       5        // Minimum before monitoring

#define LOG_FILE_MAX_BYTES    10485760 // 10MB before rotation
#define LOG_FILE_KEEP_COUNT   5        // Rotated files to retain
#define SPREAD_DB_HOURS       168      // 7 days × 24 hours
#define SWING_ARRAY_MAX       50       // Pre-allocated swing buffer
#define REGIME_HISTORY_MAX    20       // Pre-allocated regime history
#define SCORE_LOG_MAX         100      // Rolling score log buffer
#define CB_EVENT_MAX          10       // Circuit breaker event buffer
#define CB_ATR_BARS           14       // M5 bars for circuit-breaker ATR calc
#define RETRY_QUEUE_MAX       8        // Max concurrent retry operations

#define H4_SECONDS            14400    // Seconds per H4 candle
#define H1_SECONDS            3600
#define M15_SECONDS           900
#define M5_SECONDS            300
#define M1_SECONDS            60

// GMT offset input maps to broker server time
// Broker EET (UTC+3): offset = 3
// Broker UTC:         offset = 0
// Must be set correctly in EA inputs


//===================================================================
// DETERMINISTIC RANDOM UTILITY
// Replaces MathSrand/MathRand to avoid global seed corruption.
// Same seed always produces same value — no global state affected.
// Safe to call from any module at any time.
//===================================================================
int DeterministicRand(int seed, int range_min, int range_max)
{
   // Integer hash (xorshift variant) — no global state
   int h = (int)(seed + 0x9e3779b9);
   h ^= (h << 13);
   h ^= (h >> 17);
   h ^= (h << 5);
   h  = MathAbs(h);
   int range = MathMax(1, range_max - range_min + 1);
   return range_min + (h % range);
}


//===================================================================
// PHASE 4 — Trade Scoring & Decision
//===================================================================

// Entry trigger types (Option A: pullback-and-resume, sweep-gated)
enum ENTRY_TRIGGER
{
   TRIG_NONE              = 0,  // No valid trigger this evaluation
   TRIG_PULLBACK_RESUME   = 1   // Pullback to EMA20 + resumption candle
};

// Why a decision was rejected (for logging + dashboard)
enum DECISION_REASON
{
   DEC_VALID              = 0,  // Setup passed all gates
   DEC_PACKET_INVALID     = 1,  // Intelligence packet not usable
   DEC_SCORE_BELOW_MIN    = 2,  // Quality score under threshold
   DEC_NO_DIRECTION       = 3,  // Regime/Trend disagree (trend veto)
   DEC_PERSIST_BLOCKED    = 4,  // Startup warmup or forced-range
   DEC_VOL_TOO_LOW        = 5,  // Volatility floor — dead range
   DEC_NO_TRIGGER         = 6,  // Pullback-resume did not fire
   DEC_SWEEP_GATE         = 7,  // Blocked by opposing fresh sweep
   DEC_PULLBACK_TOO_FAR   = 8,  // Price not near EMA20 (no pullback context)
   DEC_MSNR_GATE          = 9   // A320: MSNR level not fresh / storyline against
};

// Phase 4 tuning constants
#define TS_RESUME_MIN_BODY_PIPS   5.0   // Min resumption candle body (pips)
#define TS_SWEEP_FRESH_BARS       3     // Sweep is "fresh" if within N M15 bars
#define TS_VOL_FLOOR_RATIO        0.60  // ATR ratio below this = dead range
#define TS_SCORE_TRANSITION_ADD   10    // +N to threshold during regime transition

//--- TradeDecision: the verdict Phase 4 hands to Phase 5
//    Scorer decides WHETHER + HOW GOOD. It does NOT set SL/TP/lot.
struct TradeDecision
{
   bool             valid;              // true = actionable setup
   DECISION_REASON  reason;             // Why (valid or which gate failed)
   TRADE_DIR        direction;          // DIR_LONG / DIR_SHORT / DIR_NONE
   ENTRY_TRIGGER    trigger;            // Which trigger fired
   int              trade_score;        // 0-100 final quality score
   int              threshold_used;     // Effective threshold (with penalties)

   double           entry_ref_price;    // Reference price at decision (mid)
   double           ema20_ref;          // EMA20 at decision (Phase 5 SL context)
   double           pullback_pips;      // How far price was from EMA20

   bool             sweep_aligned;      // A sweep supported this direction
   double           sweep_strength;     // 0-1 if aligned sweep present

   datetime         decided_at;
   string           detail;             // Human-readable summary for logs
};


//===================================================================
// PHASE 5 — Execution Layer
//===================================================================

// Why an execution attempt ended the way it did
enum EXEC_RESULT
{
   EXEC_NONE              = 0,  // No attempt made
   EXEC_PLACED            = 1,  // Order placed + fill confirmed
   EXEC_DRYRUN            = 2,  // DryRun — logged, not sent
   EXEC_REJECTED_RR       = 3,  // Real-RR gate failed
   EXEC_REJECTED_SIZING   = 4,  // Lot size invalid / equity floor
   EXEC_REJECTED_EXISTING = 5,  // Position already open (one-position rule)
   EXEC_REJECTED_SL       = 6,  // SL could not be established (never naked)
   EXEC_REJECTED_SPREAD   = 7,  // Spread too wide at execution
   EXEC_SEND_FAILED       = 8,  // Broker rejected after all retries
   EXEC_ERROR             = 9   // Unexpected error
};

// Phase 5 execution constants
#define EXEC_MAX_RETRIES        2     // Retries on requote/rejection, then abort
#define EXEC_RETRY_WAIT_MS      300   // Pause between retries (ms)

//--- OrderPlan: fully-specified intended order (built before sending)
//    This is what DryRun logs and what EntryEngine sends.
struct OrderPlan
{
   bool             valid;             // Plan passed all pre-send gates
   EXEC_RESULT      result;            // Outcome after execution attempt
   TRADE_DIR        direction;         // DIR_LONG / DIR_SHORT

   double           lot;               // Final normalized lot size
   double           entry_price;       // Intended entry (market ref)
   double           sl_price;          // Stop loss (mandatory, normalized)
   double           tp_price;          // Take profit at TP2RR (normalized)

   double           sl_pips;           // SL distance in pips
   double           tp_pips;           // TP distance in pips
   double           real_rr;           // RR after spread subtracted
   double           spread_pips;       // Spread at plan time
   double           risk_dollars;      // Intended $ risk

   // Fill confirmation (populated after live send)
   ulong            ticket;            // Position ticket (0 if none)
   double           fill_price;        // Actual fill (live only)
   double           slippage_pips;     // Actual - intended

   datetime         planned_at;
   string           detail;            // Human-readable summary for logs
};

#endif // DEFINES_MQH


//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Intelligence Layer Types                |
//| File: Intelligence/IntelligenceTypes.mqh                          |
//| Purpose: ALL enums, result structs, IntelligencePacket, and       |
//|           MarketQualityScore for the Market Intelligence Layer.    |
//|           No analytical logic. Pure type definitions.             |
//| Phase: 3 — Step 1 Foundation                                      |
//|                                                                    |
//| DEPENDENCY RULE:                                                   |
//|   Depends ONLY on: Include/Defines.mqh                            |
//|   REGIME_STATE, SwingPoint, LiqZone reused from Defines.mqh.      |
//|   No guard layer types. No execution types.                       |
//|   No MQL5 broker API calls anywhere in this file.                 |
//+------------------------------------------------------------------+
#ifndef INTELLIGENCETYPES_MQH
#define INTELLIGENCETYPES_MQH

#include "../Include/Defines.mqh"

//===================================================================
// DESIGN NOTES
//
// PSEUDO-CODE RATIONALE FOR ALL STRUCTS:
//   All result structs are value types (no pointers, no dynamic
//   allocation). They are copied by value between modules and into
//   the IntelligencePacket. This is intentional:
//
//   1. No dangling pointer risk across tick boundaries
//   2. Predictable memory layout — no heap fragmentation
//   3. Safe to pass through the IntelligencePacket by value
//   4. Easy to zero-initialize (ZeroMemory safe on POD structs)
//   5. MQL5 struct copy is memcpy-equivalent — fast
//
//   Fixed-size arrays inside structs:
//   MQL5 structs can contain fixed-size arrays declared with
//   literal integer constants or #define constants.
//   We use SWING_ARRAY_MAX (=50) from Defines.mqh.
//   These arrays are always fully allocated — unused slots
//   are identified by their 'confirmed' flag or zero price.
//
//   "confidence" fields range 0.0 to 1.0 throughout.
//   Never use raw indicator values as confidence — always normalize.
//===================================================================

//===================================================================
// NEW ENUMS — Not defined in Defines.mqh
// REGIME_STATE is already in Defines.mqh — not redefined here.
//===================================================================

//--- Overall status of the Intelligence Layer itself
enum INTELLIGENCE_STATUS
{
   INTEL_INITIALIZING  = 0,  // Still warming up — not enough bar history
   INTEL_DEGRADED      = 1,  // One or more engines unavailable — reduced confidence
   INTEL_OPERATIONAL   = 2,  // All engines running normally
   INTEL_STALE         = 3,  // Last evaluation too old to trust (stale market data)
   INTEL_ERROR         = 4   // Critical error — coordinator cannot produce valid packet
};

//--- Volatility environment classification
//    Derived from ATR ratio (current / session baseline).
//    Absolute ATR thresholds are secondary safeguards only.
enum VOLATILITY_STATE
{
   VOL_UNKNOWN      = 0,  // Insufficient data (< 14 M15 bars for ATR)
   VOL_TOO_QUIET    = 1,  // ATR ratio < 0.40 OR absolute < 5 pips
                          // Below spread cost — no tradeable edge
   VOL_SUPPRESSED   = 2,  // ATR ratio 0.40–0.70 — below normal baseline
                          // Tradeable but expect tight ranges
   VOL_NORMAL       = 3,  // ATR ratio 0.70–1.40 — ideal conditions
   VOL_ELEVATED     = 4,  // ATR ratio 1.40–2.20 — above average, watch SL
   VOL_SPIKE        = 5,  // ATR ratio >= 2.20 OR absolute >= 40 pips (via ATR_NEWS_SPIKE_PIPS)
                          // Hard skip — feeds Circuit Breaker trigger
   VOL_NEWS_SPIKE   = 6   // Last M15 candle range > 2.5 × ATR14
                          // Suspected unscheduled news event
};

//--- Structural clarity of swing pattern on a given timeframe
enum STRUCTURE_STATE
{
   STRUCT_UNKNOWN     = 0,  // Insufficient confirmed swings (< 2)
   STRUCT_MIXED       = 1,  // Conflicting pattern — no reliable direction
   STRUCT_WEAK_BULL   = 2,  // 1 conforming bull swing — low conviction
   STRUCT_WEAK_BEAR   = 3,  // 1 conforming bear swing — low conviction
   STRUCT_CLEAR_BULL  = 4,  // 2+ consecutive HH+HL — clean bull structure
   STRUCT_CLEAR_BEAR  = 5   // 2+ consecutive LH+LL — clean bear structure
};

//--- H1 trend signal quality
enum TREND_STATE
{
   TREND_UNKNOWN      = 0,  // Cannot determine (insufficient data or conflicted)
   TREND_RANGING      = 1,  // EMAs converging or crossed recently — no bias
   TREND_WEAK_BULL    = 2,  // EMA alignment bullish but structure incomplete
   TREND_WEAK_BEAR    = 3,  // EMA alignment bearish but structure incomplete
   TREND_STRONG_BULL  = 4,  // EMA aligned + HH/HL structure + price position
   TREND_STRONG_BEAR  = 5   // EMA aligned + LH/LL structure + price position
};

//--- Liquidity environment quality
enum LIQUIDITY_STATE
{
   LIQ_UNKNOWN      = 0,  // Insufficient session history (< 3 sessions)
   LIQ_DANGEROUS    = 1,  // Multiple liquidity zones within reach — score < 0.30
   LIQ_UNFAVORABLE  = 2,  // One major zone nearby — score 0.30–0.55
   LIQ_NEUTRAL      = 3,  // Minor zone proximity — score 0.55–0.75
   LIQ_CLEAN        = 4,  // No significant zones nearby — score > 0.75
   LIQ_POST_SWEEP   = 5   // Liquidity was just taken — reversal bonus active
};

//===================================================================
// INTELLIGENCE CONTEXT
//
// PSEUDO-CODE:
//   Analogous to GuardContext in the guard layer.
//   Populated ONCE per tick by the coordinator before engines run.
//   All engines read from this snapshot — they do NOT call
//   broker APIs inside their Evaluate() methods.
//
//   This ensures all engines see consistent market data even if
//   price ticks between engine evaluations within the same tick.
//
//   Exceptions (engines that MUST read live data):
//   - StructureEngine: needs iTime() to detect new candles
//   - VolatilityEngine: needs iATR() handle reads
//   These are documented in each engine's header.
//===================================================================
struct IntelligenceContext
{
   // Current price snapshot
   double      bid;                 // Current bid price
   double      ask;                 // Current ask price
   double      spread_pips;         // Current spread in pips
   double      mid_price;           // (bid + ask) / 2

   // Time context
   datetime    server_time;         // TimeCurrent()
   datetime    gmt_time;            // TimeGMT()
   int         gmt_hour;
   int         gmt_minute;
   int         day_of_week;         // 0=Sun … 6=Sat

   // Session context (from SessionGuard — passed in)
   bool        in_london_session;
   bool        in_ny_session;
   bool        in_active_session;   // Either London or NY

   // Spread Guard context (passed in — avoids re-calling SpreadGuard)
   double      session_avg_spread_pips;
   double      session_avg_atr_pips;
   bool        spread_calibrated;

   // Candle boundary flags (set by coordinator)
   bool        new_m5_bar;          // M5 bar just closed this tick
   bool        new_m15_bar;         // M15 bar just closed this tick
   bool        new_h1_bar;          // H1 bar just closed this tick
   bool        new_h4_bar;          // H4 bar just closed this tick
};

//===================================================================
// PER-TIMEFRAME STRUCTURE SNAPSHOT
//
// PSEUDO-CODE:
//   StructureEngine fills one of these per timeframe.
//   Fixed arrays — unused slots identified by confirmed=false
//   and price=0. Array size = SWING_ARRAY_MAX (50).
//   Circular write pattern: oldest entries overwritten first.
//===================================================================
struct StructureSnapshot
{
   ENUM_TIMEFRAMES   timeframe;

   // Confirmed swings (circular buffer — newest at index write_idx)
   SwingPoint    confirmed_highs[SWING_ARRAY_MAX];
   SwingPoint    confirmed_lows[SWING_ARRAY_MAX];
   int           high_count;          // Valid entries in confirmed_highs
   int           low_count;           // Valid entries in confirmed_lows

   // Pattern recognition results
   STRUCTURE_STATE  state;
   bool          hh_hl;               // Higher highs and higher lows
   bool          lh_ll;               // Lower highs and lower lows
   double        structure_clarity;   // 0.0 (chaotic) to 1.0 (clean)

   // Most recent confirmed levels (convenience — mirrors last array entry)
   double        last_high;
   double        last_low;
   double        prev_high;           // Second-to-last (for HH/LL comparison)
   double        prev_low;

   // Pending (unconfirmed) swings — tracked but never used for decisions
   SwingPoint    pending_high;
   SwingPoint    pending_low;
   bool          has_pending_high;
   bool          has_pending_low;

   datetime      last_updated;
};

//===================================================================
// MODULE RESULT STRUCTS
// One per intelligence engine. All value types.
//===================================================================

//--- RegimeEngine output
struct RegimeResult
{
   REGIME_STATE     regime;             // Primary output
   int              raw_score;          // 0–6 component sum
   double           confidence;         // 0.0–1.0
   TRADE_DIR        direction;          // DIR_LONG, DIR_SHORT, DIR_NONE

   // EMA levels (for dashboard + persistence)
   double           ema50;
   double           ema200;
   double           ema50_slope_pips;   // Pips per H4 bar (signed)
   double           ema_separation_pips;// abs(ema50 - ema200) in pips

   // ATR context
   double           atr_pips;           // ATR in pips (currently M15 — to be H4 in future)
   double           atr_ratio;          // ATR ratio vs session baseline (currently M15-derived)

   // Score component breakdown (for logging/debugging)
   bool             comp_slope;         // Component 1: EMA slope
   bool             comp_ema_side;      // Component 2: Price vs 200 EMA
   bool             comp_atr_expand;    // Component 3: ATR expanding
   bool             comp_structure;     // Component 4: Clean swing structure
   bool             comp_no_inside;     // Component 5: No inside bars
   bool             comp_session;       // Component 6: Session active
   int              penalty_points;     // Sum of penalties applied

   // Flags
   bool             is_aging;           // Regime > 48 hours
   bool             ema_near_200;       // Price within 50 pips of 200 EMA

   datetime         evaluated_at;
   bool             is_valid;           // False = insufficient data
   string           invalid_reason;
};

//--- RegimePersistenceModel output
struct RegimePersistenceResult
{
   REGIME_STATE     confirmed_regime;   // Persistence-filtered regime
   REGIME_STATE     raw_regime;         // Direct from RegimeEngine (may differ)
   TRADE_DIR        confirmed_direction;

   bool             in_transition;      // TRANSITIONING state active
   int              transition_bars;    // H4 bars spent in transition
   int              regime_age_bars;    // H4 bars in current confirmed regime
   int              regime_age_hours;

   bool             is_aging;           // > 48 hours = flag
   bool             just_changed;       // First bar of new confirmed regime
   bool             direction_flipped;  // Direction changed this evaluation

   double           sizing_multiplier;  // 1.0 normal, 0.5 transitioning
   double           score_threshold_adj;// Added to base score threshold (0.0 or +1.0)

   datetime         evaluated_at;
   bool             is_valid;
};

//--- TrendEngine output
struct TrendResult
{
   TREND_STATE      state;              // Primary classification
   TRADE_DIR        direction;          // DIR_LONG, DIR_SHORT, DIR_NONE
   double           confidence;         // 0.0–1.0

   // EMA state
   double           ema20;
   double           ema50;
   bool             ema_aligned;        // 20 EMA on correct side of 50 EMA
   double           ema_separation_pips;
   double           ema_alignment_score;// 0.0–1.0 component

   // Structure state
   bool             swing_valid;        // At least 2 conforming swings
   int              conforming_swings;  // Count of consecutive conforming swings
   double           structure_score;    // 0.0–1.0 component
   double           last_swing_high;
   double           last_swing_low;

   // Price position
   double           price_to_ema20_pips;// Signed: positive = above EMA (bull)
   double           position_score;     // 0.0–1.0 component

   // Engulfing modifier (REVISION: confidence modifier only — not invalidator)
   bool             bearish_engulf_present; // In last 3 H1 bars
   bool             bullish_engulf_present;
   double           engulf_confidence_adj;  // Negative adjustment to confidence

   // Regime alignment
   bool             agrees_with_regime; // TrendEngine direction == RegimeEngine direction

   datetime         evaluated_at;
   bool             is_valid;
   string           invalid_reason;
};

//--- VolatilityEngine output
struct VolatilityResult
{
   VOLATILITY_STATE state;             // Primary classification

   // ATR values
   double           atr_m15_pips;      // ATR(14) on M15 in pips
   double           atr_m5_pips;       // ATR(14) on M5 in pips
   double           atr_m15_ratio;     // Primary: current / session_baseline
   double           atr_baseline_pips; // Session average ATR (from SpreadGuard)

   // Directional ATR behavior
   bool             atr_expanding;     // ATR trending up over last 5 M15 bars
   bool             atr_contracting;   // ATR trending down over last 5 M15 bars

   // Last candle analysis
   double           last_candle_range_pips; // Most recent complete M15 range
   double           range_atr_ratio;        // last_range / atr_m15

   // SL/TP parameters (derived — ready for use by PositionSizer in Phase 5)
   double           recommended_stop_pips;    // ATR × SLAtrMult, clamped [SLMin, SLMax]
   double           recommended_stop_price;   // recommended_stop_pips × pip_size
   double           recommended_target1_pips; // stop × TP1RR (1.5R distance)
   double           recommended_target2_pips; // stop × TP2RR (2.5R distance)
   bool             stop_distance_in_range;   // False if stop exceeds SLPipsMax

   // Quality assessment
   double           volatility_quality;// 0.0–1.0 for MarketQualityScore contribution

   datetime         evaluated_at;
   bool             is_valid;
   string           invalid_reason;
};

//--- LiquidityEngine output
struct LiquidityResult
{
   LIQUIDITY_STATE  state;             // Primary classification
   double           score;             // 0.0–1.0 environment quality (Phase 4 uses)

   // === POOL OBSERVATIONS (static levels where liquidity sits) ===
   bool             pool_detected;             // ≥1 pool within proximity threshold
   int              pool_count;                // Active pools tracked
   double           distance_to_nearest_pool;  // Pips to closest pool of any type
   POOL_TYPE        nearest_pool_type;         // Type of nearest pool
   int              nearest_pool_touches;      // Touch count of nearest pool
   double           nearest_pool_price;        // Price of nearest pool

   // Nearest structural levels for TP targeting (used by Phase 4/5)
   double           nearest_resistance_pips;   // Pips to nearest upside pool
   double           nearest_support_pips;      // Pips to nearest downside pool
   double           nearest_resistance_price;
   double           nearest_support_price;

   // Full active pool list (Phase 4 can inspect)
   LiquidityPool    active_pools[LIQ_ACTIVE_POOLS_MAX];

   // === SWEEP EVENT OBSERVATIONS (dynamic events, distinct from pools) ===
   bool             sweep_detected;      // A confirmed sweep occurred recently
   TRADE_DIR        sweep_direction;     // Reversal direction (LONG=bull reversal after bear-side sweep)
   double           sweep_strength;      // 0.0–1.0 quality
   int              sweep_candles_ago;   // 0 = this M15, 1 = prior, ...
   POOL_TYPE        swept_pool_type;     // Type of pool that was swept
   double           swept_pool_price;    // Level that was swept

   datetime         evaluated_at;
   bool             is_valid;
   string           invalid_reason;
};

//--- StructureEngine output (wraps all three timeframe snapshots)
struct StructureResult
{
   StructureSnapshot h4;
   StructureSnapshot h1;
   StructureSnapshot m15;

   // Cross-timeframe agreement
   bool             h4_h1_agree;       // Both point same direction
   bool             h1_m15_agree;      // Both point same direction
   bool             all_agree;         // All three timeframes aligned

   TRADE_DIR        consensus_direction; // Direction all agree on (DIR_NONE if conflict)

   // Availability flags (REVISION: Structure unavailable reduces confidence,
   //   does NOT hard-invalidate other engines)
   bool             h4_available;
   bool             h1_available;
   bool             m15_available;
   bool             any_available;     // True if at least one TF has valid structure

   datetime         evaluated_at;
   bool             is_valid;
   string           invalid_reason;
};

//===================================================================
// MARKET QUALITY SCORE
//
// PSEUDO-CODE:
//   Replaces the hard entry_environment_ok boolean gate (REVISION).
//   Range: 0–100 integer score.
//   Phase 4 TradeScorer decides the minimum acceptable quality.
//   The Intelligence Layer computes it. Phase 4 interprets it.
//
//   Component contributions (sum to 100):
//     Regime confidence:    0–25  (25 × regime.confidence)
//     Trend confidence:     0–25  (25 × trend.confidence)
//     Structure clarity:    0–20  (20 × structure_avg_clarity)
//     Volatility quality:   0–15  (15 × volatility.volatility_quality)
//     Liquidity quality:    0–15  (15 × liquidity.score)
//
//   Severe penalty conditions (reduce score heavily but never force to zero):
//     REGIME_RANGING:    -40 penalty  (market not directional)
//     REGIME_UNKNOWN:    -35 penalty  (insufficient data)
//     VOL_NEWS_SPIKE:    -35 penalty  (abnormal event — unreliable structure)
//     VOL_SPIKE (no trend): -25 penalty (volatility without direction)
//     These are penalties, NOT disqualifications.
//     Phase 4 TradeScorer decides whether residual score is sufficient.
//     Intelligence Layer produces the score. Phase 4 interprets it.
//===================================================================
struct MarketQualityScore
{
   int              total;             // 0–100 final score

   // Component scores (for logging and dashboard)
   int              regime_component;  // 0–25
   int              trend_component;   // 0–25
   int              structure_component; // 0–20
   int              volatility_component; // 0–15
   int              liquidity_component;  // 0–15

   // Severe penalty tracking (for logging — Phase 4 uses total score only)
   int              penalty_applied;    // Sum of all penalties deducted
   string           penalty_reasons;    // Semicolon-separated list of penalties

   // Direction consensus check
   bool             direction_consensus; // Regime + Trend agree on direction
   TRADE_DIR        consensus_direction;

   datetime         computed_at;
};

//===================================================================
// INTELLIGENCE PACKET
//
// PSEUDO-CODE:
//   The single output object of the entire Intelligence Layer.
//   Passed by value to Phase 4 TradeScorer.
//   TradeScorer NEVER calls individual engine methods directly.
//   All access goes through this struct.
//
//   Validity levels:
//     is_valid = false:       Coordinator had a critical error.
//                             TradeScorer must treat as market_quality = 0.
//     intel_status = DEGRADED: One or more engines unavailable.
//                             TradeScorer may proceed with reduced confidence.
//                             Engines that ARE available still populate their fields.
//     intel_status = OPERATIONAL: All engines contributed normally.
//
//   "available_engines" bitmask (for Phase 4 diagnostics):
//     bit 0: StructureEngine
//     bit 1: RegimeEngine
//     bit 2: RegimePersistenceModel
//     bit 3: TrendEngine
//     bit 4: VolatilityEngine
//     bit 5: LiquidityEngine
//===================================================================
struct IntelligencePacket
{
   //--- Packet metadata
   datetime             generated_at;
   INTELLIGENCE_STATUS  intel_status;
   bool                 is_valid;
   string               invalid_reason;
   int                  available_engines;    // Bitmask (see above)
   int                  evaluation_count;     // Total packets generated since init

   //--- Module outputs (by value — full copies)
   RegimeResult          regime;
   RegimePersistenceResult persistence;
   TrendResult           trend;
   VolatilityResult      volatility;
   LiquidityResult       liquidity;
   StructureResult       structure;

   //--- Coordinator-derived summary (computed AFTER all engines run)
   MarketQualityScore    quality;

   //--- Convenience accessors (mirrors of key fields — avoid deep derefs in Phase 4)
   REGIME_STATE         confirmed_regime;     // = persistence.confirmed_regime
   TRADE_DIR            consensus_direction;  // = quality.consensus_direction
   double               layer_confidence;     // = quality.total / 100.0
   bool                 direction_valid;      // Regime AND Trend agree on direction
   bool                 structure_available;  // At least one TF structure valid
};

//===================================================================
// ENGINE METADATA
// Analogous to GuardMetadata in GuardTypes.mqh.
// One per engine — tracks initialization state and diagnostics.
//===================================================================
enum ENGINE_ID
{
   ENG_STRUCTURE    = 0,
   ENG_VOLATILITY   = 1,
   ENG_REGIME       = 2,
   ENG_PERSISTENCE  = 3,
   ENG_TREND        = 4,
   ENG_LIQUIDITY    = 5,
   ENG_COUNT        = 6   // Sentinel — total number of engines
};

struct EngineMetadata
{
   ENGINE_ID        id;
   string           name;
   string           description;
   bool             initialized;
   bool             enabled;
   bool             available;          // Can produce output this tick
   int              eval_count;         // Total evaluations since init
   int              valid_count;        // Evaluations that produced valid output
   int              error_count;        // Evaluations that returned invalid
   double           last_confidence;    // Most recent confidence value
   datetime         last_eval_time;     // When last evaluated
   datetime         last_valid_time;    // When last produced valid output
   string           last_error;         // Most recent error description
};

//===================================================================
// UTILITY: Zero-initialize an IntelligencePacket to safe defaults
// Called by coordinator before populating each tick.
//===================================================================
void InitPacket(IntelligencePacket &pkt)
{
   ZeroMemory(pkt);
   pkt.generated_at      = TimeCurrent();
   pkt.intel_status      = INTEL_INITIALIZING;
   pkt.is_valid          = false;
   pkt.invalid_reason    = "not_yet_evaluated";
   pkt.available_engines = 0;
   pkt.evaluation_count  = 0;

   // Safe defaults for result structs
   pkt.regime.regime        = REGIME_UNKNOWN;
   pkt.regime.direction     = DIR_NONE;
   pkt.regime.is_valid      = false;

   pkt.persistence.confirmed_regime  = REGIME_UNKNOWN;
   pkt.persistence.sizing_multiplier = 0.5;   // Conservative until confirmed
   pkt.persistence.is_valid          = false;

   pkt.trend.state        = TREND_UNKNOWN;
   pkt.trend.direction    = DIR_NONE;
   pkt.trend.confidence   = 0.0;
   pkt.trend.is_valid     = false;

   pkt.volatility.state   = VOL_UNKNOWN;
   pkt.volatility.is_valid = false;
   pkt.volatility.recommended_stop_pips  = 0.0;

   pkt.liquidity.state    = LIQ_UNKNOWN;
   pkt.liquidity.score    = 0.0;
   pkt.liquidity.is_valid = false;

   pkt.structure.any_available = false;
   pkt.structure.h4_available  = false;
   pkt.structure.h1_available  = false;
   pkt.structure.m15_available = false;
   pkt.structure.is_valid      = false;
   pkt.structure.consensus_direction = DIR_NONE;

   pkt.quality.total              = 0;
   pkt.quality.penalty_applied    = 0;
   pkt.quality.penalty_reasons    = "";
   pkt.quality.direction_consensus = false;
   pkt.quality.consensus_direction = DIR_NONE;

   pkt.confirmed_regime     = REGIME_UNKNOWN;
   pkt.consensus_direction  = DIR_NONE;
   pkt.layer_confidence     = 0.0;
   pkt.direction_valid      = false;
   pkt.structure_available  = false;
}

//===================================================================
// UTILITY: Human-readable summary of IntelligencePacket
// Used for logging. Returns single formatted string.
//===================================================================
string PacketSummary(const IntelligencePacket &pkt)
{
   return StringFormat(
      "status=%s regime=%s dir=%s trend=%s vol=%s liq=%.2f quality=%d valid=%d",
      EnumToString(pkt.intel_status),
      EnumToString(pkt.confirmed_regime),
      EnumToString(pkt.consensus_direction),
      EnumToString(pkt.trend.state),
      EnumToString(pkt.volatility.state),
      pkt.liquidity.score,
      pkt.quality.total,
      (int)pkt.is_valid
   );
}

#endif // INTELLIGENCETYPES_MQH
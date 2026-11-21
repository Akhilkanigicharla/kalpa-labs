# Phase 3 — Market Intelligence Layer: Architecture Design
## XAUUSD Institutional EA — Pre-Code Design Document
### No MQL5 code. Pure architecture.

---

## FOUNDATIONAL PRINCIPLE

The Intelligence Layer answers ONE question per tick:

  "What is the market doing right now, and how confident are we?"

It does NOT answer: "Should we trade?" That belongs to the Scoring Engine (Phase 4).
It does NOT answer: "How do we trade?" That belongs to the Execution Layer (Phase 5).

Every module in this layer is a READ-ONLY observer of market conditions.
No module writes a position, sends an order, or modifies trade state.
Every module produces a structured output object. That object is the only
thing passed downstream.

---

## MODULE 1: RegimeEngine

### Purpose
Classify the current H4 market environment into one of five discrete regimes.
A regime is the broadest possible answer to "is Gold trending or not?"
All other intelligence modules operate within this regime context.

### Inputs
  Source timeframe: H4
  Lookback: 20 H4 candles minimum (80 hours of history)

  Price data:
    - OHLC for last 20 H4 candles
    - Current incomplete H4 candle (for ATR only — not for structural decisions)

  Derived indicators (calculated internally, not externally injected):
    - 50-period EMA of H4 close prices
    - 200-period EMA of H4 close prices
    - ATR(14) on H4
    - Rolling 20-period ATR average on H4

  From RegimePersistenceModel (sibling module):
    - Current persisted regime state
    - Regime duration in hours
    - Consecutive H4 bars at current score

### Outputs — RegimeResult struct
  REGIME_STATE     current_regime       // RANGING / WEAK_BULL / WEAK_BEAR /
                                        // TRENDING_BULL / TRENDING_BEAR / TRANSITIONING
  int              raw_score            // 0–6 (component sum)
  double           confidence           // 0.0–1.0 (how clean the regime signal is)
  TRADE_DIR        regime_direction     // DIR_LONG, DIR_SHORT, DIR_NONE
  double           ema50_value          // Current 50 EMA level
  double           ema200_value         // Current 200 EMA level
  double           ema50_slope          // Pips per bar (positive = rising)
  double           atr_h4              // Current H4 ATR(14) in pips
  double           atr_ratio           // Current ATR / 20-period ATR average
  bool             is_aging            // Regime > 48 hours = flag
  datetime         evaluated_at        // Timestamp of evaluation
  string           rejection_reason    // Why score is low (for logging)

### Internal Scoring Model — 6-point system
  +1: 50 EMA slope > +2.0 pips/bar (bullish) or < -2.0 pips/bar (bearish)
      → Confirms directional momentum exists
  +1: Price on correct side of 200 EMA by > 50 pips
      → Long-term trend alignment. Buffer prevents noise near the EMA.
  +1: ATR ratio > 1.1 (current ATR above 20-period average)
      → Volatility expansion = trending behavior
  +1: Clean swing structure confirmed (see StructureEngine output)
      → Institutional participation leaves footprints in structure
  +1: No more than 1 inside bar in last 5 H4 candles
      → Inside bars = compression = no conviction
  +1: Session context: London or NY active (ATR proxy)
      → Session-weighted participation signal

  Penalty rules (these override scoring):
    -2: Mixed swing structure (HH then LL within last 5 bars) → instant RANGING
    -1: ATR ratio < 0.8 (volatility contraction) → trending unlikely
    -1: Price within 50 pips of 200 EMA → indecision zone

  Score interpretation:
    0–2: RANGING
    3–4: WEAK_BULL or WEAK_BEAR (direction from EMA slope)
    5–6: TRENDING_BULL or TRENDING_BEAR

  Confidence calculation:
    confidence = (raw_score / 6.0) × structure_clarity × ema_separation_factor
    structure_clarity = StructureEngine.GetH4Clarity() (0.0–1.0)
    ema_separation_factor = min(1.0, abs(price - ema200) / 200.0)

### Internal States
  m_last_h4_bar_time   — tracks H4 candle boundary for update throttling
  m_score_history[20]  — rolling 20-score buffer for persistence model
  m_ema50[200]         — pre-allocated EMA buffer (circular)
  m_ema200[200]        — pre-allocated EMA buffer (circular)
  m_atr_h4[20]         — pre-allocated ATR buffer
  m_initialized        — ensures Init() called before Evaluate()

### Update Trigger
  Recalculates on each new H4 candle close only.
  Between H4 bars: returns cached RegimeResult.
  Detection: iTime(SYMBOL, PERIOD_H4, 0) != m_last_h4_bar_time

### Failure Modes
  Insufficient history: < 20 H4 bars available
    → Return REGIME_UNKNOWN with confidence = 0.0
    → Caller (TradeScorer) treats UNKNOWN as RANGING (no trade)

  EMA calculation error: all-zero price data
    → Log ERROR, return REGIME_UNKNOWN

  StructureEngine unavailable: null pointer
    → Proceed without structure bonus (max score = 5 instead of 6)
    → Log WARN once

### Persistence Requirements
  None. Regime state is fully reconstructable from price history.
  RegimePersistenceModel handles state continuity separately.

### Computational Cost
  H4 recalculation: ~0.5ms (EMA + ATR over 200 bars, done once per 4 hours)
  Per-tick (cached return): < 0.01ms
  Memory: ~5KB (price buffers)

### MQL5 Considerations
  Use CopyClose/CopyHigh/CopyLow with H4 period constant.
  iMA() handle with PERIOD_H4 — create once at Init(), reuse.
  iATR() handle with PERIOD_H4 — create once, reuse.
  IndicatorRelease() all handles in Shutdown().
  Do NOT recalculate inside OnTick() — only on H4 bar close.
  iTime(SYMBOL, PERIOD_H4, 0) is the canonical H4 bar detection.

---

## MODULE 2: RegimePersistenceModel

### Purpose
Prevent whipsaw regime changes. A single H4 candle with a weak score should
not immediately flip the regime from TRENDING to RANGING. This module
enforces minimum confirmation requirements for regime transitions and
maintains regime history for aging detection.

### Inputs
  From RegimeEngine each H4 bar:
    - new_score (int, 0–6)
    - new_direction (TRADE_DIR)
    - new_raw_regime (REGIME_STATE before persistence filtering)

  Internally maintained:
    - regime_history[REGIME_HISTORY_MAX] (circular buffer of RegimeHistoryEntry)
    - current_confirmed_regime (REGIME_STATE)
    - bars_at_current_score (int)
    - transition_candidate (REGIME_STATE)
    - transition_candidate_bars (int)

### Outputs — RegimePersistenceResult struct
  REGIME_STATE     confirmed_regime      // What the persistence model accepts
  REGIME_STATE     raw_regime            // What RegimeEngine said (may differ)
  bool             in_transition         // Transitioning state active
  int              regime_age_bars       // H4 bars in current regime
  int              regime_age_hours      // Converted to hours
  bool             is_aging              // > 48 hours = flag
  bool             just_changed          // First bar of a new confirmed regime
  double           sizing_multiplier     // 1.0 normal, 0.5 transitioning

### Transition Rules

  TRENDING → RANGING:
    Requires 3 consecutive H4 bars with score < 3 before confirming.
    After 1 weak bar: enter TRANSITIONING (size 0.5×, score threshold +1.0)
    After 3 weak bars: confirm RANGING

  RANGING → TRENDING:
    Requires 2 consecutive H4 bars with score >= 4
    AND direction must be consistent (not flip between bars)
    After 1 strong bar: flag as candidate
    After 2 strong bars: confirm TRENDING

  TRENDING_BULL → TRENDING_BEAR (direct reversal):
    Must pass through RANGING first — no direct flip allowed
    Rationale: a Bull→Bear transition in one bar is almost always noise

  TRANSITIONING state behavior:
    ScoreThreshold used by TradeScorer increases by 1.0
    PositionSizer multiplier reduced to 0.5
    Maximum duration: 3 H4 bars. If unresolved → defaults to RANGING.

### Internal States
  RegimeHistoryEntry regime_history[20]:
    { timestamp, raw_score, raw_regime, confirmed_regime, direction }
  Circular buffer: write_idx = (write_idx + 1) % 20
  transition_start_time — for transition duration enforcement

### Failure Modes
  Corrupt history (all zeros): treat as REGIME_UNKNOWN on next regime eval.
  Persistence model called before first RegimeEngine output:
    → Return REGIME_UNKNOWN, sizing_multiplier = 0.5 (conservative)

### Persistence Requirements
  Persist to disk: regime_persistence.txt
  Written on each regime state change (not every bar)
  Fields: confirmed_regime, bars_at_regime, direction, last_write_time
  Read on Init() to restore across restarts.
  If file data is > 8 hours old: discard (regime may have changed while offline)

### Computational Cost
  Per H4 bar: < 0.1ms (array writes + comparisons)
  Per-tick: < 0.01ms (cached return)
  Memory: ~2KB

---

## MODULE 3: TrendEngine

### Purpose
Determine the H1-timeframe directional bias and swing structure quality.
While RegimeEngine answers "is Gold trending?" at the macro level,
TrendEngine answers "in what direction is the H1 structure aligned?"
This is the primary direction filter for entry decisions.

### Inputs
  Source timeframe: H1
  Lookback: 50 H1 candles minimum (50 hours)

  Price data:
    - OHLC for last 50 H1 candles

  Derived (internal):
    - 20-period EMA of H1 close (fast EMA)
    - 50-period EMA of H1 close (slow EMA)
    - Confirmed swing highs and lows (from StructureEngine — H1 tier)

  From RegimePersistenceModel:
    - confirmed_regime (required — TrendEngine output only valid if regime is trending)

### Outputs — TrendResult struct
  TRADE_DIR        direction             // DIR_LONG, DIR_SHORT, DIR_NONE
  double           confidence            // 0.0–1.0
  double           ema20_value           // Current H1 20 EMA
  double           ema50_value           // Current H1 50 EMA
  bool             ema_aligned           // 20 EMA above 50 EMA (bull) or below (bear)
  double           ema_separation_pips   // Distance between EMAs in pips
  bool             swing_structure_valid // HH+HL or LH+LL confirmed
  int              consecutive_structure // How many consecutive conforming swings
  double           last_swing_high       // Most recent confirmed swing high
  double           last_swing_low        // Most recent confirmed swing low
  bool             engulf_warning        // Opposing engulfing in last 3 H1 bars
  datetime         evaluated_at

### Direction Logic
  BULLISH (DIR_LONG):
    ✓ H1 20 EMA > H1 50 EMA (bull cross)
    ✓ Last 2 confirmed swing lows are higher (HL pattern)
    ✓ Price currently above H1 20 EMA
    ✗ No bearish engulfing candle in last 3 H1 bars

  BEARISH (DIR_SHORT):
    ✓ H1 20 EMA < H1 50 EMA (bear cross)
    ✓ Last 2 confirmed swing highs are lower (LH pattern)
    ✓ Price currently below H1 20 EMA
    ✗ No bullish engulfing candle in last 3 H1 bars

  NEUTRAL (DIR_NONE):
    If any single condition above fails.
    If regime direction conflicts with H1 direction.

### Confidence Scoring
  confidence = ema_alignment_score × structure_score × position_score

  ema_alignment_score:
    EMA separation > 30 pips: 1.0
    EMA separation 15–30 pips: 0.7
    EMA separation 5–15 pips: 0.4
    EMA separation < 5 pips: 0.1 (approaching crossover = unreliable)

  structure_score:
    3+ consecutive conforming swings: 1.0
    2 consecutive swings: 0.7
    1 swing only: 0.4
    No confirmed swings: 0.0

  position_score:
    Price > 20 pips from 20 EMA (on correct side): 1.0
    Price 5–20 pips from 20 EMA: 0.7
    Price 0–5 pips from 20 EMA: 0.3 (too close — EMA test zone)

### Update Trigger
  Recalculates on each new H1 candle close.
  Between H1 bars: returns cached TrendResult.
  Detection: iTime(SYMBOL, PERIOD_H1, 0) != m_last_h1_bar_time

### Failure Modes
  Insufficient history (< 50 H1 bars): return DIR_NONE, confidence = 0.0
  EMA crossover in last 3 bars: return DIR_NONE (conflicted signal)
  StructureEngine returns no confirmed swings: downgrade confidence to 0.3 max

### Persistence Requirements
  None. Fully reconstructable from price data.

### Computational Cost
  Per H1 bar: ~0.2ms (EMA calc + swing detection)
  Per-tick: < 0.01ms (cached)
  Memory: ~3KB

---

## MODULE 4: VolatilityEngine

### Purpose
Characterize current volatility conditions on M15 and produce ATR-based
parameters used for stop loss sizing, entry filtering, and circuit breaker
context. This module does NOT make entry decisions — it provides the
volatility environment within which entries are evaluated.

### Inputs
  Source timeframes: M15 (primary), M5 (secondary — velocity tracking)
  Lookback: 50 M15 candles minimum

  Price data:
    - OHLC for last 50 M15 candles
    - High/Low for last 20 M5 candles (range tracking)

  External inputs:
    - SpreadGuard.GetSessionAvgATR() — baseline for ratio calculation

### Outputs — VolatilityResult struct
  VOLATILITY_STATE vol_state           // TOO_QUIET / NORMAL / ELEVATED / SPIKE / NEWS_SPIKE
  double           atr_m15_pips       // Current ATR(14) on M15 in pips
  double           atr_m15_ratio      // atr_m15 / session_baseline_atr
  double           atr_m5_pips        // ATR(14) on M5 in pips
  double           sl_distance_pips   // Recommended SL distance (ATR × 1.5)
  double           sl_distance_price  // sl_distance in price points
  double           tp1_pips           // SL × TP1_RR
  double           tp2_pips           // SL × TP2_RR
  bool             atr_expanding      // ATR trending upward over last 5 bars
  bool             atr_contracting    // ATR trending downward over last 5 bars
  double           last_candle_range  // Most recent complete M15 candle range
  double           range_atr_ratio    // last_candle_range / atr_m15
  datetime         evaluated_at

### Volatility State Classification
  TOO_QUIET:   ATR < 5 pips (below spread cost — not worth trading)
  NORMAL:      ATR 5–20 pips (ideal entry conditions)
  ELEVATED:    ATR 20–30 pips (tradeable — widen SL expectations)
  SPIKE:       ATR 30–40 pips (caution — only in strong trend)
  NEWS_SPIKE:  ATR > 40 pips OR last candle range > 2.5 × ATR
               (hard skip — feeds into Circuit Breaker trigger)

### SL Distance Calculation
  Base:     ATR_M15 × Config.SLAtrMult (1.5)
  Floor:    max(base, Config.SLPipsMin)    (30 pip minimum)
  Ceiling:  min(base, Config.SLPipsMax)   (80 pip maximum)
  If base > SLPipsMax: skip signal (vol_state = SPIKE or NEWS_SPIKE)

  TP levels derived from final SL:
    tp1_pips = sl × Config.TP1RR    (1.5R)
    tp2_pips = sl × Config.TP2RR    (2.5R)

### Update Trigger
  Full recalculation: on each new M15 candle close
  Lightweight M5 range update: on each M5 candle close
  Per-tick: return cached values

### Failure Modes
  No M15 data: return VOLATILITY_STATE = TOO_QUIET with all zeros
  ATR = 0 (bad data): log ERROR, return TOO_QUIET
  sl_distance > SLPipsMax: return valid struct but set out-of-range flag

### Persistence Requirements
  None. Fully reconstructable.

### Computational Cost
  Per M15 bar: ~0.1ms
  Per-tick: < 0.01ms
  Memory: ~2KB

---

## MODULE 5: LiquidityEngine

### Purpose
Map where resting orders likely sit in the market and whether the current
price environment is clean or congested. This module does NOT predict
moves — it identifies structural price levels that attract institutional
attention and adjusts the liquidity score passed to the scoring engine.

### Core Concept
Institutional traders cannot hide their footprints completely.
Large orders leave identifiable signatures: equal highs/lows (stop pools),
price reactions at round numbers, rejection wicks at session extremes.
The LiquidityEngine maps these zones and tells the scoring engine whether
a potential entry is in a clean environment or is inside a danger zone.

### Inputs
  Source timeframes: H1 (zone detection), M15 (proximity calculation)
  Lookback: 10 trading sessions (H1 session highs/lows buffer)

  Price levels (maintained internally):
    - Session highs/lows: last 5 London + last 5 NY sessions
    - Previous day's high and low (PDH/PDL)
    - Identified round number levels (every $50 interval)
    - Swing pool zones (from StructureEngine H1 output)

  Current price (from GuardContext — passed in at evaluation)

### Outputs — LiquidityResult struct
  double           liquidity_score         // 0.0–1.0 (higher = cleaner)
  bool             near_session_level      // Within 15 pips of session H/L
  bool             near_swing_pool         // Within 20 pips of swing H/L cluster
  bool             near_round_number       // Within 25 pips of $50 level
  bool             pdh_pdl_proximity       // Within 10 pips of PDH or PDL
  bool             sweep_detected          // Post-sweep flag (bonus signal)
  double           nearest_resistance_pips // Distance to nearest resistance above
  double           nearest_support_pips    // Distance to nearest support below
  double           nearest_resistance_price
  double           nearest_support_price
  datetime         evaluated_at

  LiqZone          active_zones[8]         // Pre-allocated zone array
  int              zone_count

### Liquidity Score Calculation
  Start: 1.0 (clean)
  -0.25: near_session_level = true
  -0.25: near_swing_pool = true
  -0.25: near_round_number = true
  -0.25: pdh_pdl_proximity = true
  +0.20: sweep_detected = true (bonus: liquidity was taken, reversal more likely)
  Clamp: [0.0, 1.0]

### Session Level Tracking
  On each London session close (12:00 GMT): record session_high, session_low
  On each NY session close (17:00 GMT): record session_high, session_low
  Rolling buffer: keep last 5 of each
  Session high/low identified as: highest high and lowest low during session hours

### PDH/PDL Tracking
  Reset at 00:01 GMT daily
  Track: max(high) and min(low) over current calendar day
  Previous day values frozen at day rollover

### Round Number Detection
  Gold round numbers: every $50 (1900, 1950, 2000, etc.)
  Sub-levels: every $10 within 30 pips of current price
  "Near" definition: abs(current_price - level) / pip_size < proximity_threshold

### Sweep Detection
  Sweep criteria (same as CNewsGuard concept but for structure, not news):
    1. Price exceeded a known swing level by 5–15 pips
    2. M15 candle CLOSED back on the original side of the level
    3. Wick-to-body ratio > 2.5 (wick dominant)
    4. No more than 3 M15 candles since sweep (still relevant)
  When sweep detected:
    sweep_detected = true for 3 M15 candles
    Provides +0.20 bonus to liquidity score
    Direction signal: entry in sweep reversal direction gets extra weight

### Update Trigger
  Zone map: rebuilt once per day at rollover (session levels change)
  Proximity check: on every M15 candle close (15-minute resolution sufficient)
  Per-tick: return cached proximity result

### Failure Modes
  Insufficient session history (< 3 sessions): return score = 0.5 (neutral)
  Price outside expected Gold range: log WARN, return score = 0.0 (unsafe)

### Persistence Requirements
  Persist session levels to disk: session_levels.txt
  Written at each session close. Read on Init().
  If file is > 48 hours old: discard and rebuild from price history.

### Computational Cost
  Daily zone rebuild: ~1ms (small array operations)
  Per M15 bar: ~0.05ms (proximity comparisons only)
  Per-tick: < 0.01ms (cached)
  Memory: ~3KB (zone arrays)

---

## MODULE 6: StructureEngine

### Purpose
Identify and track confirmed swing highs and lows across H4, H1, and M15
timeframes. Provide the structural context that all other modules reference.
This is the lowest-level analytical building block — it processes raw price
into meaningful structural reference points.

### Core Rule
A swing is only confirmed when 2 candles on the RIGHT SIDE of the swing
point have been completed (2-bar lookback confirmation). Unconfirmed swings
are tracked but never used for trading decisions.

### Inputs
  Source timeframes: H4, H1, M15
  Lookback per timeframe:
    H4: 50 candles (200 hours)
    H1: 100 candles (100 hours)
    M15: 100 candles (25 hours)

  Price data: High and Low of each candle

### Outputs — StructureResult struct
  Per timeframe (H4, H1, M15):
    SwingPoint    highs[SWING_ARRAY_MAX]   // Last N confirmed swing highs
    SwingPoint    lows[SWING_ARRAY_MAX]    // Last N confirmed swing lows
    int           high_count
    int           low_count
    bool          hh_hl_pattern            // Bullish structure
    bool          lh_ll_pattern            // Bearish structure
    double        structure_clarity        // 0.0–1.0 (how clean the swings are)
    double        last_confirmed_high
    double        last_confirmed_low
    double        last_confirmed_high_prev // Second-to-last (for HH/LL comparison)
    double        last_confirmed_low_prev

  Cross-timeframe:
    bool          h4_h1_structure_agree    // Both point same direction
    bool          h1_m15_structure_agree

### Swing Detection Algorithm
  For swing HIGH detection:
    candidate = bar[i] where high[i] > high[i-1] AND high[i] > high[i+1]
    confirmation: high[i+1] < high[i] AND high[i+2] < high[i] (2-bar right side)
    minimum size: abs(high[i] - prior_swing_low) >= SWING_MIN_SIZE[timeframe]
      H4 minimum: 150 pips
      H1 minimum: 60 pips
      M15 minimum: 25 pips

  For swing LOW detection: mirror of above

  Unconfirmed swings: stored in pending_highs[], pending_lows[]
  Confirmed swings: promoted to confirmed arrays, oldest dropped if array full

### Structure Pattern Recognition
  HH+HL (bullish):
    confirmed_highs[-1] > confirmed_highs[-2]  (higher high)
    AND confirmed_lows[-1] > confirmed_lows[-2] (higher low)

  LH+LL (bearish):
    confirmed_highs[-1] < confirmed_highs[-2]  (lower high)
    AND confirmed_lows[-1] < confirmed_lows[-2] (lower low)

  Mixed (no pattern): flag as structure_clarity = 0.0

### Structure Clarity Score
  clarity = 1.0 base
  For each of last 3 swing pairs:
    If pattern matches expected direction: +0.0 (already 1.0)
    If pattern breaks: -0.33
  Result: 0.0 (all broken) to 1.0 (all conforming)

### Update Trigger
  H4 update: on H4 candle close
  H1 update: on H1 candle close
  M15 update: on M15 candle close
  Per-tick: return cached result
  All three timeframes checked each tick via iTime() comparison.

### Failure Modes
  Insufficient bars for minimum swing detection: return empty arrays
  Only 1 confirmed swing: hh_hl and lh_ll both false, clarity = 0.0
  All swings at same level: clarity = 0.0 (ranging market at structure level)

### Persistence Requirements
  None. Swing history reconstructable from OHLC data on restart.
  Note: restart causes 2-bar confirmation delay on the most recent swing.
  This is acceptable — no half-confirmed swings from before restart.

### Computational Cost
  Per bar (any timeframe): ~0.3ms (scan 100 bars for swings)
  Per-tick: < 0.01ms (cached)
  Memory: ~8KB (swing arrays for 3 timeframes × 50 entries each)

---

## INTELLIGENCE OUTPUT SCHEMA

All 6 modules produce outputs that are collected into a single
IntelligencePacket struct, consumed by TradeScorer (Phase 4).

```
struct IntelligencePacket
{
  // Source metadata
  datetime          generated_at;
  bool              is_valid;              // All modules returned usable data
  string            invalidation_reason;   // Why is_valid = false

  // Module outputs (by value — no pointers)
  RegimeResult      regime;
  RegimePersistenceResult persistence;
  TrendResult       trend;
  VolatilityResult  volatility;
  LiquidityResult   liquidity;
  StructureResult   structure;

  // Derived cross-module fields (computed by IntelligenceLayer coordinator)
  bool              all_agree_direction;   // Regime + Trend + Structure all aligned
  TRADE_DIR         consensus_direction;   // Direction all three agree on
  double            layer_confidence;      // Weighted average of module confidences
  bool              entry_environment_ok;  // True if layer passes basic threshold
}
```

### Layer-level Validity Gate
The IntelligenceLayer coordinator computes entry_environment_ok:
  TRUE if ALL of:
    - regime.current_regime != RANGING
    - regime.current_regime != REGIME_UNKNOWN
    - trend.direction != DIR_NONE
    - trend.direction == regime.regime_direction (alignment)
    - volatility.vol_state != TOO_QUIET
    - volatility.vol_state != NEWS_SPIKE
    - liquidity.liquidity_score >= 0.50
    - structure.h4_h1_structure_agree == true

If entry_environment_ok = false: TradeScorer returns score = 0.0 immediately.
No individual component scores are calculated. This is a fast-fail gate.

---

## CROSS-MODULE DEPENDENCY AUDIT

```
MODULE              DEPENDS ON                    DEPENDENCY TYPE
─────────────────────────────────────────────────────────────────────
StructureEngine     (none — reads raw price only)  Independent
VolatilityEngine    SpreadGuard.GetSessionAvgATR   Data query (not control)
RegimeEngine        StructureEngine (H4 clarity)   Data query
                    RegimePersistenceModel          Data query
TrendEngine         StructureEngine (H1 swings)    Data query
                    RegimePersistenceModel          Data query (for direction filter)
LiquidityEngine     StructureEngine (swing pools)  Data query
RegimePersistence   RegimeEngine (raw score)        Data query (fed by coordinator)
IntelligenceLayer   All 6 modules                  Aggregation

EVALUATION ORDER (enforced by IntelligenceLayer coordinator):
  1. StructureEngine.Evaluate()    — no dependencies
  2. VolatilityEngine.Evaluate()   — needs session ATR (from SpreadGuard, always ready)
  3. RegimeEngine.Evaluate()       — needs StructureEngine result
  4. RegimePersistenceModel.Update() — needs RegimeEngine result
  5. TrendEngine.Evaluate()        — needs StructureEngine + RegimePersistence
  6. LiquidityEngine.Evaluate()    — needs StructureEngine (swing pools)
  7. IntelligenceLayer.Aggregate() — collects all, computes consensus
```

---

## OVERFITTING RISK ASSESSMENT

### Risk Category 1: SCORE THRESHOLDS (LOW-MEDIUM RISK)
  RegimeEngine score 0–6: each component is structurally derived.
  The thresholds (>=3 = trending, >=5 = strong) are round numbers by design —
  they should NOT be optimized against historical data.
  Risk: Developer temptation to test "what if threshold = 3.5 instead of 3?"
  Mitigation: Document thresholds as structural constants, not parameters.

### Risk Category 2: ATR MULTIPLIERS (LOW RISK)
  SLAtrMult = 1.5, TrailAtrMult = 0.75, CB thresholds = 2.5×/1.8×.
  These come from Gold's observed behavior characteristics, not optimization.
  Risk: Low — these would need to be egregiously wrong to cause failure.

### Risk Category 3: SWING SIZE MINIMUMS (MEDIUM RISK)
  H4: 150 pips, H1: 60 pips, M15: 25 pips.
  These filter noise below the meaningful structural level for Gold.
  Risk: If Gold volatility regime changes significantly (e.g. VIX-driven
  compression), these minimums could filter out all valid swings.
  Mitigation: Monitor VolatilityEngine ATR ratio. If consistently below
  baseline, consider reducing minimums — but only with evidence.

### Risk Category 4: LIQUIDITY ZONE PROXIMITY (LOW-MEDIUM RISK)
  Session level: 15 pips, Swing pool: 20 pips, Round number: 25 pips.
  These are educated approximations of where institutional orders cluster.
  Risk: Too tight = filter too many valid entries.
        Too loose = fail to filter enough dangerous zones.
  Mitigation: Log every BLOCK decision with proximity distances.
  After 20+ trades, analyze whether blocked trades were actually avoided
  losses or missed profits.

### Risk Category 5: CONFIRMATION COUNTS (LOW RISK)
  2-bar swing confirmation, 2 consecutive H4 bars for regime transition.
  These prevent single-bar whipsaw without introducing significant lag.
  Risk: Very low — lag is acceptable and intentional.

### GENERAL OVERFITTING GUARDRAILS:
  - No parameters in this layer should be optimized via MT5 Optimizer.
  - All values derive from market structure theory, not historical curve-fit.
  - If a parameter "feels wrong," analyze why structurally — don't just
    run an optimization pass.
  - The test: would a professional institutional trader recognize and agree
    with this logic? If yes, it is structural. If no, it may be overfit.

---

## XAUUSD-SPECIFIC BEHAVIOR CONSIDERATIONS

### 1. Gold Is Not A Forex Pair
  Gold trades in USD/oz. It has no "base currency" dynamics.
  Dollar strength correlation: inverse (strong USD → lower Gold typically).
  This correlation is unreliable intraday — do not use it for entries.
  The Intelligence Layer reads PRICE BEHAVIOR only — no correlation signals.

### 2. Session Behavior Asymmetry
  Asian session: Gold ranges. Structure forms but volatility is low.
    → RegimeEngine may score 3–4 (weak trend) during Asian but this
      is unreliable. SessionGuard blocks entries — correct behavior.

  London open (first 30 minutes): Volatility spikes, spreads widen.
    → VolatilityEngine will see ATR spike. SpreadGuard blocks entries.
    → Intelligence Layer continues evaluating — output is stored but
      not acted on until spread normalizes.

  London mid-session: Best structural behavior. EMAs, swing structure,
    and regime all most reliable during this window.

  NY open (13:00–14:30 GMT): Can reverse London trend OR accelerate it.
    → TrendEngine should flag low confidence during this transition.
    → Wait for M15 candle close confirmation after NY open before entry.

### 3. Round Number Magnetic Behavior
  Gold has pronounced round number magnetism ($2000, $2050, $2100, etc.).
  LiquidityEngine captures this — near-round-number entries get penalized.
  However: breakouts FROM round numbers are high-quality setups.
  The Intelligence Layer does not distinguish approach vs. breakout — the
  TradeScorer (Phase 4) uses TP placement relative to round numbers.

### 4. ATR Regime Sensitivity
  Gold's ATR is highly sensitive to macro events.
  During calm periods: M15 ATR might be 8–12 pips.
  During volatility events: M15 ATR can reach 40–80 pips.
  VolatilityEngine must track session BASELINE, not absolute ATR.
  Always use the ratio (current / baseline), not the raw value.

### 5. Swing Structure Size Thresholds
  The minimum swing sizes (H4: 150 pips, H1: 60 pips, M15: 25 pips)
  are calibrated to Gold's typical range:
    - A 150-pip H4 swing = meaningful structural event for Gold
    - A 25-pip M15 swing = minimum meaningful pullback
  These minimums prevent micro-structure noise from polluting structural analysis.
  They should be reviewed if Gold enters an extended low-volatility period.

### 6. The 200 EMA On H4
  Gold respects the H4 200 EMA as a major institutional reference level.
  Price within 50 pips of the 200 EMA = regime score penalty applied.
  Price crossing the 200 EMA = potential regime shift — do not enter
  in either direction until the cross is confirmed by 2+ bars.

---

## COMPUTATIONAL BUDGET SUMMARY

```
MODULE                  PER TICK    PER M5 BAR   PER M15 BAR   PER H1 BAR   PER H4 BAR
─────────────────────────────────────────────────────────────────────────────────────────
StructureEngine         <0.01ms     0.1ms         0.3ms         0.3ms         0.3ms
VolatilityEngine        <0.01ms     0.05ms        0.1ms         —             —
RegimeEngine            <0.01ms     —             —             —             0.5ms
RegimePersistence       <0.01ms     —             —             —             0.1ms
TrendEngine             <0.01ms     —             —             0.2ms         —
LiquidityEngine         <0.01ms     0.05ms        0.05ms        —             —
IntelligenceLayer       <0.01ms     —             —             —             —
─────────────────────────────────────────────────────────────────────────────────────────
TOTAL PER TICK:         <0.07ms     (cached returns)
TOTAL WORST CASE H4:    ~1.5ms      (full recalculation — happens every 4 hours)
```

Gold during London session: ~3–8 ticks per second.
At 5 ticks/sec, total intelligence compute: 0.35ms/sec = 0.035% of 1-second budget.
Well within VPS performance envelope.

---

## PHASE 3 → PHASE 4 INTERFACE CONTRACT

The IntelligenceLayer exports one function to the TradeScorer:

  IntelligencePacket IntelligenceLayer.GetCurrentPacket()

TradeScorer reads this packet and computes a composite score (Phase 4).
TradeScorer NEVER calls individual intelligence modules directly.
All access goes through IntelligenceLayer.GetCurrentPacket().

This enforces the boundary: intelligence = observation, scoring = evaluation.

---
*Phase 3 Architecture Design — Complete*
*Ready for review before MQL5 implementation*
*No code generated in this document*


//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Regime Engine                           |
//| File: Intelligence/CRegimeEngine.mqh                              |
//| Purpose: Classify the H4 market environment into a regime state  |
//|           and score (0–6). Primary macro-level filter for all    |
//|           downstream intelligence and scoring modules.            |
//| Phase: 3 — Step 4                                                 |
//|                                                                    |
//| ENGINE ID:  ENG_REGIME                                            |
//|                                                                    |
//| INPUTS:                                                            |
//|   H4 price data (CopyClose, iMA handles)                          |
//|   StructureResult.h4 (clarity + pattern — contributes to         |
//|     confidence ONLY, never invalidates RegimeEngine)              |
//|   VolatilityResult (ATR ratio, expansion/contraction state)       |
//|                                                                    |
//| OUTPUT:  RegimeResult (cached, O(1) per tick)                     |
//|                                                                    |
//| STRICT BOUNDARIES:                                                 |
//|   - No persistence logic (RegimePersistenceModel handles that)    |
//|   - No sizing logic                                               |
//|   - No trade decisions                                            |
//|   - Structure unavailability reduces confidence, never blocks     |
//+------------------------------------------------------------------+
#ifndef CREGIMEENGINE_MQH
#define CREGIMEENGINE_MQH

#include "IIntelligenceEngine.mqh"

//===================================================================
// SCORING MODEL — Full Specification
//
// PSEUDO-CODE — 6-component additive scoring with penalties:
//
// RAW SCORE (sum of 6 binary components, each worth 1 point):
//
//   C1: EMA50 SLOPE
//       Slope = (ema50[0] - ema50[REGIME_EMA_SLOPE_WINDOW]) / WINDOW
//       Pass if abs(slope) >= REGIME_EMA50_SLOPE_MIN (2 pips/bar)
//       Direction set: slope > 0 → BULL, slope < 0 → BEAR
//
//   C2: EMA200 SIDE + BUFFER
//       Pass if current_price > ema200 + REGIME_EMA200_BUFFER (bull) OR
//               current_price < ema200 - REGIME_EMA200_BUFFER (bear)
//       Must agree with C1 direction. If C1 says BULL but price below
//       EMA200 → C2 = 0 regardless.
//
//   C3: ATR EXPANSION
//       Uses VolatilityResult.atr_m15_ratio
//       Pass if ratio >= REGIME_ATR_EXPAND_RATIO (1.10)
//       Rationale: trending markets attract volume → ATR expands
//
//   C4: STRUCTURE CLARITY (optional — degrades gracefully)
//       Uses StructureResult.h4.structure_clarity (if available)
//       Pass if clarity >= REGIME_STRUCT_CLARITY_MIN (0.50)
//       If StructureEngine H4 unavailable:
//         C4 = 0 (not passed), max_score = 5, confidence adjusted
//
//   C5: INSIDE BAR ABSENCE
//       Count inside bars in last REGIME_INSIDE_BAR_WINDOW (5) H4 bars.
//       An "inside bar" = candle whose high/low range is entirely inside
//         the prior candle's high/low range.
//       Pass if count <= REGIME_INSIDE_BAR_MAX (1)
//       Rationale: inside bars = compression = no conviction
//
//   C6: SESSION ACTIVITY
//       Uses IntelligenceContext.in_active_session
//       Pass if currently in London or NY session.
//       Rationale: regime signals in Asian session have low participation.
//
// PENALTIES (applied after summing components, before clamping):
//
//   P1: MIXED STRUCTURE (-2)
//       StructureResult.h4.hh_hl == true AND h4.lh_ll == true
//       Mathematically impossible in clean data, but can occur with
//       noisy short-timeframe overlapping swings.
//       Signals extremely chaotic market — harsh penalty.
//       Only applies if StructureEngine is available.
//
//   P2: ATR CONTRACTING (-1)
//       VolatilityResult.atr_contracting == true
//       (ATR trending down > 10% over last 5 M15 bars)
//       Contraction precedes regime breakdown.
//
//   P3: EMA200 PROXIMITY (-1)
//       abs(current_price - ema200) < REGIME_EMA200_BUFFER (50 pips)
//       Price wrestling with the 200 EMA = institutional indecision.
//       Note: this partially overlaps with C2 (which also uses the buffer),
//       but P3 is a penalty regardless of which side price is on —
//       even if C2 passed, being too close to EMA200 reduces conviction.
//
// FINAL SCORE = clamp(raw_score - sum(penalties), 0, 6)
//
// INTERPRETATION:
//   0–2: RANGING    (no directional bias detectable)
//   3–4: WEAK_BULL or WEAK_BEAR  (directional but low conviction)
//   5–6: TRENDING_BULL or TRENDING_BEAR (strong conviction)
//
// DIRECTION ASSIGNMENT:
//   Primary source: EMA50 slope sign
//   Tie-break (slope near zero): EMA50 vs EMA200 cross position
//   If both ambiguous: DIR_NONE → regime = RANGING regardless of score
//===================================================================

class CRegimeEngine : public IIntelligenceEngine
{
private:
   //--- MT5 indicator handles (H4 timeframe)
   int      m_ema50_h4_handle;    // iMA(symbol, H4, Config.EMA_Slow, 0, MODE_EMA, PRICE_CLOSE)
   int      m_ema200_h4_handle;   // iMA(symbol, H4, Config.EMA_200,  0, MODE_EMA, PRICE_CLOSE)

   //--- EMA value buffers (index 0 = most recent closed bar)
   //    Size: REGIME_LOOKBACK_H4 + REGIME_EMA_SLOPE_WINDOW + margin
   double   m_ema50_buf[];      // Last 30 H4 bars of EMA50 values (dynamic)
   double   m_ema200_buf[];     // Last 10 H4 bars of EMA200 values (dynamic)

   //--- H4 OHLC for inside bar detection
   double   m_h4_highs[REGIME_INSIDE_BAR_WINDOW + 2];
   double   m_h4_lows[REGIME_INSIDE_BAR_WINDOW + 2];

   //--- Last H4 bar boundary
   datetime m_last_h4_bar;

   //--- Cached results
   RegimeResult   m_cached;
   bool           m_cache_valid;

   //--- Dependency inputs (set by coordinator before Evaluate)
   //    These are copies — not pointers — to avoid lifetime issues.
   StructureResult  m_last_structure;
   VolatilityResult m_last_volatility;
   bool             m_structure_provided;
   bool             m_volatility_provided;

   //===================================================================
   // BUFFER REFRESH
   //
   // PSEUDO-CODE:
   //   CopyBuffer: shift=1 to skip incomplete current H4 bar.
   //   EMA50: need REGIME_EMA_SLOPE_WINDOW bars back for slope calc.
   //   EMA200: only need current value (bar[0] after shift).
   //   H4 OHLC: need REGIME_INSIDE_BAR_WINDOW + 1 bars.
   //
   //   Failure of EMA50 = engine cannot function → RecordError, return false.
   //   Failure of EMA200 = engine degraded → continue with EMA50 only.
   //   Failure of H4 OHLC = C5 (inside bar) cannot score → score as 0.
   //===================================================================
   bool RefreshEMA50()
   {
      ArraySetAsSeries(m_ema50_buf, true);
      int n = REGIME_EMA_SLOPE_WINDOW + REGIME_LOOKBACK_H4;
      int copied = CopyBuffer(m_ema50_h4_handle, 0, 1, n, m_ema50_buf);
      if(copied < REGIME_EMA_SLOPE_WINDOW + 1)
      {
         //--- audit 27 Nov: a short copy shrinks the dynamic array; restore it so [0]/[window] reads
         //    elsewhere (Init log, slope, BuildResult) never go out of range (= EA stopped by MT5)
         ArrayResize(m_ema50_buf, 30);
         ArrayInitialize(m_ema50_buf, 0.0);
         Logger.Error("REGIME",
            StringFormat("EMA50 H4 buffer failed: copied=%d need=%d err=%d",
                          copied, REGIME_EMA_SLOPE_WINDOW+1, GetLastError()));
         return false;
      }
      return true;
   }

   bool RefreshEMA200()
   {
      ArraySetAsSeries(m_ema200_buf, true);
      int copied = CopyBuffer(m_ema200_h4_handle, 0, 1,
                               ArraySize(m_ema200_buf), m_ema200_buf);
      if(copied < 1)
      {
         Logger.Warn("REGIME",
            StringFormat("EMA200 H4 buffer failed: copied=%d — C2 will score 0",
                          copied));
         ArrayResize(m_ema200_buf, 10);                 // audit 27 Nov: never leave it at size 0
         ArrayInitialize(m_ema200_buf, 0.0);
         return false;
      }
      return true;
   }

   bool RefreshH4OHLC()
   {
      int n = REGIME_INSIDE_BAR_WINDOW + 2;
      double tmp_h[], tmp_l[];
      ArraySetAsSeries(tmp_h, true);
      ArraySetAsSeries(tmp_l, true);

      int ch = CopyHigh(m_symbol, PERIOD_H4, 1, n, tmp_h);
      int cl = CopyLow(m_symbol,  PERIOD_H4, 1, n, tmp_l);

      if(ch < n || cl < n)
      {
         Logger.Debug("REGIME",
            StringFormat("H4 OHLC partial: highs=%d lows=%d — C5 scores 0", ch, cl));
         ArrayInitialize(m_h4_highs, 0.0);
         ArrayInitialize(m_h4_lows,  0.0);
         return false;
      }

      for(int i = 0; i < n; i++)
      {
         m_h4_highs[i] = tmp_h[i];
         m_h4_lows[i]  = tmp_l[i];
      }
      return true;
   }

   //===================================================================
   // EMA50 SLOPE CALCULATION
   //
   // PSEUDO-CODE:
   //   Slope = (ema50[0] - ema50[WINDOW]) / WINDOW  in price units
   //   Convert to pips: slope_pips = slope_price / pip_size
   //   Sign preserved: positive = rising, negative = falling
   //
   //   WINDOW = REGIME_EMA_SLOPE_WINDOW (3 bars)
   //   Using 3-bar window balances between too-noisy (1 bar) and
   //   too-lagged (10 bars). On H4, 3 bars = 12 hours.
   //===================================================================
   double ComputeEMA50Slope() const
   {
      int window = REGIME_EMA_SLOPE_WINDOW;
      if(ArraySize(m_ema50_buf) <= window) return 0.0;   // audit 27 Nov: bounds
      if(m_ema50_buf[0] <= 0 || m_ema50_buf[window] <= 0) return 0.0;
      double delta_price = m_ema50_buf[0] - m_ema50_buf[window];
      return PriceToPips(MathAbs(delta_price)) *
             (delta_price >= 0 ? 1.0 : -1.0) / window;
   }

   //===================================================================
   // INSIDE BAR COUNT
   //
   // PSEUDO-CODE:
   //   An inside bar: bar[i].high <= bar[i-1].high AND
   //                  bar[i].low  >= bar[i-1].low
   //   Check bars at index 0..WINDOW-1 (most recent WINDOW closed bars).
   //   Each bar is compared to the bar at index+1 (its predecessor).
   //   Count how many qualify.
   //
   //   Index mapping:
   //   m_h4_highs[0] = most recent closed H4 bar
   //   m_h4_highs[1] = one bar before that
   //   etc.
   //   So bar[i] vs bar[i+1]: highs[i] <= highs[i+1] AND lows[i] >= lows[i+1]
   //===================================================================
   int CountInsideBars() const
   {
      if(m_h4_highs[0] <= 0) return 0; // No data

      int count  = 0;
      int window = REGIME_INSIDE_BAR_WINDOW;
      for(int i = 0; i < window; i++)
      {
         if(m_h4_highs[i+1] <= 0) break; // Ran out of data
         if(m_h4_highs[i] <= m_h4_highs[i+1] &&
            m_h4_lows[i]  >= m_h4_lows[i+1])
            count++;
      }
      return count;
   }

   //===================================================================
   // REGIME DIRECTION FROM EMA SLOPE
   //
   // PSEUDO-CODE:
   //   If slope > +SLOPE_MIN: BULL
   //   If slope < -SLOPE_MIN: BEAR
   //   If near zero: check EMA50 vs EMA200 position as tie-break
   //     EMA50 > EMA200 + 20 pips → tentative BULL
   //     EMA50 < EMA200 - 20 pips → tentative BEAR
   //     Otherwise: DIR_NONE (ambiguous)
   //===================================================================
   TRADE_DIR DetermineDirection(double slope_pips) const
   {
      if(slope_pips >= REGIME_EMA50_SLOPE_MIN)  return DIR_LONG;
      if(slope_pips <= -REGIME_EMA50_SLOPE_MIN) return DIR_SHORT;

      // Slope is near-zero — use EMA cross position as tie-break
      if(m_ema50_buf[0] > 0 && m_ema200_buf[0] > 0)
      {
         double cross_dist = PriceToPips(m_ema50_buf[0] - m_ema200_buf[0]);
         if(cross_dist >  20.0) return DIR_LONG;
         if(cross_dist < -20.0) return DIR_SHORT;
      }

      return DIR_NONE;
   }

   //===================================================================
   // CORE SCORING
   //
   // PSEUDO-CODE:
   //   Execute components C1–C6 in order.
   //   Each component sets its bool flag and contributes 1 if passed.
   //   Apply penalties.
   //   Clamp to [0, 6].
   //   Set direction. If DIR_NONE → force score to 0 (no direction = ranging).
   //===================================================================
   void ScoreRegime(double current_price, RegimeResult &r) const
   {
      // ---- Component 1: EMA50 slope ----
      double slope = ComputeEMA50Slope();
      r.ema50_slope_pips = slope;
      r.comp_slope = (MathAbs(slope) >= REGIME_EMA50_SLOPE_MIN);

      // ---- Direction from slope ----
      TRADE_DIR dir = DetermineDirection(slope);
      r.direction = dir;

      // ---- Component 2: EMA200 side + buffer ----
      double ema200 = m_ema200_buf[0];
      r.ema200     = ema200;
      r.ema_near_200 = false;
      r.comp_ema_side = false;

      if(ema200 > 0)
      {
         double dist_pips = PriceToPips(current_price - ema200); // signed
         r.ema_separation_pips = MathAbs(dist_pips);
         r.ema_near_200 = (r.ema_separation_pips < REGIME_EMA200_BUFFER);

         if(dir == DIR_LONG  && dist_pips >= REGIME_EMA200_BUFFER)
            r.comp_ema_side = true;
         else if(dir == DIR_SHORT && dist_pips <= -REGIME_EMA200_BUFFER)
            r.comp_ema_side = true;
      }

      // ---- Component 3: ATR expansion ----
      r.comp_atr_expand = false;
      r.atr_ratio    = 0.0;
      if(m_volatility_provided && m_last_volatility.is_valid)
      {
         r.atr_ratio    = m_last_volatility.atr_m15_ratio;
         r.atr_pips     = m_last_volatility.atr_m15_pips;
         r.comp_atr_expand = (m_last_volatility.atr_m15_ratio >= REGIME_ATR_EXPAND_RATIO);
      }

      // ---- Component 4: Structure clarity (optional) ----
      r.comp_structure = false;
      if(m_structure_provided &&
         m_last_structure.h4_available &&
         m_last_structure.h4.structure_clarity >= REGIME_STRUCT_CLARITY_MIN)
      {
         r.comp_structure = true;
      }
      // If structure unavailable: comp_structure=false, max_score effectively 5

      // ---- Component 5: Inside bar absence ----
      int inside_count = CountInsideBars();
      r.comp_no_inside = (inside_count <= REGIME_INSIDE_BAR_MAX);

      // ---- Component 6: Session activity ----
      // Note: IntelligenceContext is not directly stored —
      // We use a cached flag updated when Evaluate() was last called.
      // See m_last_session_active below.
      r.comp_session = m_last_session_active;

      // ---- Raw score ----
      int raw = (int)r.comp_slope +
                (int)r.comp_ema_side +
                (int)r.comp_atr_expand +
                (int)r.comp_structure +
                (int)r.comp_no_inside +
                (int)r.comp_session;

      // ---- Penalties ----
      r.penalty_points = 0;

      // P1: Mixed structure
      if(m_structure_provided &&
         m_last_structure.h4_available &&
         m_last_structure.h4.hh_hl &&
         m_last_structure.h4.lh_ll)
      {
         r.penalty_points += 2;
         Logger.Warn("REGIME", "Mixed H4 structure detected — -2 penalty");
      }

      // P2: ATR contracting
      if(m_volatility_provided && m_last_volatility.is_valid &&
         m_last_volatility.atr_contracting)
         r.penalty_points += 1;

      // P3: Near EMA200
      if(r.ema_near_200)
         r.penalty_points += 1;

      r.raw_score = MathMax(0, MathMin(6, raw - r.penalty_points));
   }

   //===================================================================
   // REGIME CLASSIFICATION FROM SCORE
   //===================================================================
   REGIME_STATE ClassifyRegime(int score, TRADE_DIR dir) const
   {
      if(dir == DIR_NONE) return REGIME_RANGING;

      if(score <= 2) return REGIME_RANGING;
      if(score <= 4)
         return (dir == DIR_LONG) ? REGIME_WEAK_BULL : REGIME_WEAK_BEAR;
      // score 5 or 6
      return (dir == DIR_LONG) ? REGIME_TRENDING_BULL : REGIME_TRENDING_BEAR;
   }

   //===================================================================
   // CONFIDENCE SCORING
   //
   // PSEUDO-CODE:
   //   Confidence = how reliable is this regime classification?
   //   Depends on:
   //     (A) Score strength:    score/6 × 0.50
   //     (B) Structure quality: if available and clear → +0.20
   //                            if available but mixed → +0.00
   //                            if unavailable → +0.10 (not penalised heavily)
   //     (C) EMA separation:   larger gap from EMA200 = higher conviction
   //                            capped at +0.20
   //     (D) ATR alignment:    if expanding (trend in motion) → +0.10
   //                            if contracting → +0.00
   //
   //   Final: clamp [0.0, 1.0]
   //===================================================================
   double ComputeConfidence(const RegimeResult &r) const
   {
      // (A) Score component (0.0–0.50)
      double score_a = (r.raw_score / 6.0) * 0.50;

      // (B) Structure quality (0.0–0.20)
      double score_b = 0.10; // Default: structure unavailable (not zero)
      if(m_structure_provided && m_last_structure.h4_available)
      {
         double clarity = m_last_structure.h4.structure_clarity;
         if(m_last_structure.h4.hh_hl && m_last_structure.h4.lh_ll)
            score_b = 0.00; // Mixed — no structure contribution
         else
            score_b = clarity * 0.20;
      }

      // (C) EMA200 separation (0.0–0.20)
      // separation_pips → normalise: 200+ pips = max, 0 = zero
      double score_c = MathMin(0.20, r.ema_separation_pips / 200.0 * 0.20);

      // (D) ATR alignment (0.0–0.10)
      double score_d = 0.0;
      if(m_volatility_provided && m_last_volatility.is_valid)
         score_d = m_last_volatility.atr_expanding ? 0.10 : 0.00;

      return MathMin(1.0, score_a + score_b + score_c + score_d);
   }

   //===================================================================
   // BUILD FULL RegimeResult
   //===================================================================
   bool BuildResult(const IntelligenceContext &ctx)
   {
      RegimeResult r;
      ZeroMemory(r);
      r.is_valid     = false;
      r.evaluated_at = TimeCurrent();

      // Current price from context
      double price = ctx.mid_price;
      if(price <= 0) price = ctx.bid;
      if(price <= 0)
      {
         r.invalid_reason = "no_price_data";
         m_cached = r;
         RecordError("no_price_data");
         return false;
      }

      // EMA50 value
      r.ema50 = (m_ema50_buf[0] > 0) ? m_ema50_buf[0] : 0.0;
      r.ema200 = (m_ema200_buf[0] > 0) ? m_ema200_buf[0] : 0.0;

      // Require minimum history
      if(m_ema50_buf[0] <= 0)
      {
         r.invalid_reason  = "ema50_unavailable";
         r.regime          = REGIME_UNKNOWN;
         r.direction       = DIR_NONE;
         m_cached = r;
         RecordError("ema50_unavailable");
         return false;
      }

      // Score all components and penalties
      ScoreRegime(price, r);

      // Classify
      r.regime = ClassifyRegime(r.raw_score, r.direction);

      // Aging flag
      if(m_last_h4_bar > 0)
      {
         int age_bars = (int)((TimeCurrent() - m_last_h4_bar) / H4_SECONDS);
         r.is_aging = (age_bars >= REGIME_AGING_BARS);
      }

      // Confidence
      double conf = ComputeConfidence(r);

      r.is_valid = true;

      // Detailed log on state change only
      if(r.regime != m_cached.regime || r.direction != m_cached.direction)
      {
         Logger.Info("REGIME",
            StringFormat("Regime changed: %s → %s dir=%s score=%d conf=%.2f",
                          EnumToString(m_cached.regime),
                          EnumToString(r.regime),
                          EnumToString(r.direction),
                          r.raw_score,
                          conf),
            StringFormat("slope=%.1f ema_sep=%.0f penalty=%d "
                          "c1=%d c2=%d c3=%d c4=%d c5=%d c6=%d",
                          r.ema50_slope_pips,
                          r.ema_separation_pips,
                          r.penalty_points,
                          (int)r.comp_slope,
                          (int)r.comp_ema_side,
                          (int)r.comp_atr_expand,
                          (int)r.comp_structure,
                          (int)r.comp_no_inside,
                          (int)r.comp_session));
      }

      m_cached      = r;
      m_cache_valid = true;
      RecordSuccess(conf);
      return true;
   }

   //--- Session flag cached between Evaluate calls
   bool m_last_session_active;

public:
   //===================================================================
   // CONSTRUCTOR
   //===================================================================
   CRegimeEngine() :
      m_ema50_h4_handle(INVALID_HANDLE),
      m_ema200_h4_handle(INVALID_HANDLE),
      m_last_h4_bar(0),
      m_cache_valid(false),
      m_structure_provided(false),
      m_volatility_provided(false),
      m_last_session_active(false)
   {
      ArrayInitialize(m_ema50_buf,  0.0);
      ArrayInitialize(m_ema200_buf, 0.0);
      ArrayInitialize(m_h4_highs,   0.0);
      ArrayInitialize(m_h4_lows,    0.0);

      m_meta.id          = ENG_REGIME;
      m_meta.name        = "REGIME";
      m_meta.description = "H4 regime scoring (0-6) with direction and confidence";
      m_meta.enabled     = true;
      m_meta.initialized = false;
      m_meta.available   = false;

      ZeroMemory(m_cached);
      ZeroMemory(m_last_structure);
      ZeroMemory(m_last_volatility);
      m_cached.regime    = REGIME_UNKNOWN;
      m_cached.direction = DIR_NONE;
      m_cached.is_valid  = false;
   }

   //===================================================================
   // SET DEPENDENCY INPUTS
   // Called by coordinator BEFORE Evaluate() each H4 bar close.
   // RegimeEngine does not hold pointers to other engines —
   // the coordinator copies the latest results in.
   //===================================================================
   void SetStructureResult(const StructureResult &sr)
   {
      m_last_structure   = sr;
      m_structure_provided = true;
   }

   void SetVolatilityResult(const VolatilityResult &vr)
   {
      m_last_volatility   = vr;
      m_volatility_provided = true;
   }

   //===================================================================
   // INIT
   //===================================================================
   virtual bool Init(string symbol, double pip_size) override
   {
      m_symbol   = symbol;
      m_pip_size = pip_size;

      if(pip_size <= 0)
      {
         Logger.Fatal("REGIME", "Init: pip_size <= 0");
         return false;
      }

      ArrayResize(m_ema50_buf,  30);
      ArrayResize(m_ema200_buf, 10);

      Logger.Info("REGIME",
         StringFormat("Initializing. symbol=%s ema50_period=%d ema200_period=%d",
                       symbol, Config.EMA_Slow, Config.EMA_200));

      // Create EMA handles
      m_ema50_h4_handle = iMA(symbol, PERIOD_H4, Config.EMA_Slow,
                               0, MODE_EMA, PRICE_CLOSE);
      if(m_ema50_h4_handle == INVALID_HANDLE)
      {
         Logger.Fatal("REGIME",
            StringFormat("iMA EMA50 H4 failed. error=%d", GetLastError()));
         return false; // EMA50 is essential — slope is primary component
      }

      m_ema200_h4_handle = iMA(symbol, PERIOD_H4, Config.EMA_200,
                                0, MODE_EMA, PRICE_CLOSE);
      if(m_ema200_h4_handle == INVALID_HANDLE)
      {
         // EMA200 failure is degraded but not fatal
         // C2 (EMA200 side) will always score 0, reducing max achievable to 5
         Logger.Warn("REGIME",
            StringFormat("iMA EMA200 H4 failed — C2 disabled. error=%d",
                          GetLastError()));
      }

      // Initial buffer fill (may return insufficient data on first run — OK)
      RefreshEMA50();
      RefreshEMA200();
      RefreshH4OHLC();

      m_last_h4_bar = iTime(symbol, PERIOD_H4, 1);

      m_meta.initialized = true;
      m_initialized      = true;
      m_meta.available   = (m_ema50_buf[0] > 0);

      Logger.Info("REGIME",
         StringFormat("Init complete. ema50=%.5f ema200=%.5f available=%d",
                       m_ema50_buf[0], m_ema200_buf[0],
                       (int)m_meta.available));
      return true;
   }

   //===================================================================
   // EVALUATE — called by coordinator on H4 bar close
   //
   // PSEUDO-CODE:
   //   1. Coordinator has already called SetStructureResult() and
   //      SetVolatilityResult() with current data.
   //   2. Cache session flag from context.
   //   3. Refresh all H4 buffers (EMA50, EMA200, OHLC).
   //   4. Build full result.
   //   5. Return true if valid.
   //
   //   Called ONLY when ctx.new_h4_bar = true.
   //   Between H4 bars: GetCached() returns last result (O(1)).
   //===================================================================
   virtual bool Evaluate(const IntelligenceContext &ctx) override
   {
      if(!m_initialized) return false;
      if(!ctx.new_h4_bar && m_cache_valid) return m_cached.is_valid;

      // Cache session flag
      m_last_session_active = ctx.in_active_session;

      // Refresh buffers
      bool ema50_ok  = RefreshEMA50();
      bool ema200_ok = RefreshEMA200();
      RefreshH4OHLC(); // Non-fatal if fails — C5 scores 0

      if(!ema50_ok)
      {
         m_cached.is_valid       = false;
         m_cached.regime         = REGIME_UNKNOWN;
         m_cached.direction      = DIR_NONE;
         m_cached.invalid_reason = "ema50_refresh_failed";
         RecordError("ema50_refresh_failed");
         return false;
      }

      m_last_h4_bar = iTime(m_symbol, PERIOD_H4, 1);

      return BuildResult(ctx);
   }

   //===================================================================
   // GET CACHED RESULT (O(1))
   //===================================================================
   RegimeResult GetCached() const { return m_cached; }

   //===================================================================
   // RESET
   //===================================================================
   virtual void Reset() override
   {
      m_last_h4_bar         = 0;
      m_cache_valid         = false;
      m_structure_provided  = false;
      m_volatility_provided = false;
      m_last_session_active = false;
      ArrayInitialize(m_ema50_buf,  0.0);
      ArrayInitialize(m_ema200_buf, 0.0);
      ArrayInitialize(m_h4_highs,   0.0);
      ArrayInitialize(m_h4_lows,    0.0);
      ZeroMemory(m_cached);
      m_cached.regime    = REGIME_UNKNOWN;
      m_cached.direction = DIR_NONE;
      m_cache_valid      = false;
      m_initialized      = false;
      m_meta.available   = false;
      Logger.Info("REGIME", "Engine reset");
   }

   //===================================================================
   // SHUTDOWN — release indicator handles
   //===================================================================
   virtual void Shutdown() override
   {
      if(m_ema50_h4_handle != INVALID_HANDLE)
      {
         if(!IndicatorRelease(m_ema50_h4_handle))
            Logger.Warn("REGIME",
               StringFormat("IndicatorRelease EMA50 failed: err=%d",
                             GetLastError()));
         m_ema50_h4_handle = INVALID_HANDLE;
      }
      if(m_ema200_h4_handle != INVALID_HANDLE)
      {
         if(!IndicatorRelease(m_ema200_h4_handle))
            Logger.Warn("REGIME",
               StringFormat("IndicatorRelease EMA200 failed: err=%d",
                             GetLastError()));
         m_ema200_h4_handle = INVALID_HANDLE;
      }

      Logger.Info("REGIME",
         StringFormat("Shutdown. evals=%d errors=%d last_regime=%s",
                       m_meta.eval_count, m_meta.error_count,
                       EnumToString(m_cached.regime)));

      IIntelligenceEngine::Shutdown();
   }

   //--- Convenience accessors
   REGIME_STATE GetRegime()    const { return m_cached.regime; }
   TRADE_DIR    GetDirection() const { return m_cached.direction; }
   int          GetScore()     const { return m_cached.raw_score; }
   bool         IsTrending()   const
   {
      return (m_cached.regime == REGIME_TRENDING_BULL ||
              m_cached.regime == REGIME_TRENDING_BEAR);
   }
   bool         IsRanging()    const
   {
      return (m_cached.regime == REGIME_RANGING ||
              m_cached.regime == REGIME_UNKNOWN);
   }
};

//--- Global singleton
CRegimeEngine RegimeEngine;

#endif // CREGIMEENGINE_MQH

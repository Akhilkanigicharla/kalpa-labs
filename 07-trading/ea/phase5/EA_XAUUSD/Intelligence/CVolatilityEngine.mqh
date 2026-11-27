
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Volatility Engine                       |
//| File: Intelligence/CVolatilityEngine.mqh                          |
//| Purpose: Characterise current volatility environment on M15/M5.   |
//|           ATR ratio is the PRIMARY classifier.                    |
//|           Absolute ATR thresholds are secondary safety checks.    |
//|           Produces SL/TP distances for downstream use.            |
//| Phase: 3 — Step 3                                                 |
//|                                                                    |
//| ENGINE ID:  ENG_VOLATILITY                                        |
//|                                                                    |
//| PRIMARY INPUT:  ctx.session_avg_atr_pips (baseline from SpreadGuard)|
//| SECONDARY:      iATR() handles on M15 and M5                      |
//|                                                                    |
//| OUTPUT:    VolatilityResult (cached, O(1) per tick)               |
//|                                                                    |
//| DESIGN PRINCIPLE:                                                  |
//|   ATR ratio = current_ATR / session_baseline_ATR                  |
//|   This is market-context-aware: an ATR of 20 pips means           |
//|   something different in a 10-pip-baseline session vs a           |
//|   30-pip-baseline session. The ratio normalises for this.         |
//|                                                                    |
//|   Absolute thresholds (VOL_TOO_QUIET < 5 pips, SPIKE >= 40 pips) |
//|   act as hard floors/ceilings that override ratio logic only      |
//|   at extreme values — protecting against bad baselines.           |
//+------------------------------------------------------------------+
#ifndef CVOLATILITYENGINE_MQH
#define CVOLATILITYENGINE_MQH

#include "IIntelligenceEngine.mqh"

class CVolatilityEngine : public IIntelligenceEngine
{
private:
   //--- MT5 indicator handles (created at Init, released at Shutdown)
   int      m_atr_m15_handle;   // iATR(symbol, PERIOD_M15, 14)
   int      m_atr_m5_handle;    // iATR(symbol, PERIOD_M5,  14)

   //--- Cached indicator results (refreshed on bar close)
   double   m_atr_m15_buf[]; // M15 ATR values, [0]=most recent (dynamic)
   double   m_atr_m5_buf[];   // M5 ATR values (dynamic)

   //--- Last known good ATR values (survive one missed bar)
   double   m_last_atr_m15_pips;
   double   m_last_atr_m5_pips;
   double   m_last_baseline_pips;  // Session ATR baseline from SpreadGuard

   //--- Bar boundary tracking
   datetime m_last_m15_bar;
   datetime m_last_m5_bar;

   //--- Stability tracking (rolling ATR direction over VOL_STABILITY_WINDOW bars)
   double   m_atr_stability_buf[]; // Last N+1 ATR values (dynamic)
   int      m_stability_write;   // Circular write index

   //--- Cached result
   VolatilityResult m_cached;
   bool             m_cache_valid;

   //===================================================================
   // INDICATOR BUFFER REFRESH
   //
   // PSEUDO-CODE:
   //   CopyBuffer(handle, buffer_index, start_pos, count, dest_array)
   //   buffer_index = 0 for standard iATR (single buffer)
   //   start_pos    = 1 (skip incomplete current bar, same as CopyHigh)
   //   Returns bars copied. Must be > 0 to be valid.
   //   ArraySetAsSeries ensures index 0 = most recent completed bar.
   //===================================================================
   bool RefreshM15ATR()
   {
      if(m_atr_m15_handle == INVALID_HANDLE) return false;

      ArraySetAsSeries(m_atr_m15_buf, true);
      int copied = CopyBuffer(m_atr_m15_handle, 0, 1,
                              VOL_LOOKBACK_M15, m_atr_m15_buf);
      // A336 (#14): a partial copy shrinks the dynamic array; AnalyseStability reads index
      //             VOL_STABILITY_WINDOW, so anything shorter would be "array out of range"
      if(copied < VOL_STABILITY_WINDOW + 1)
      {
         ArrayResize(m_atr_m15_buf, VOL_LOOKBACK_M15);            // audit 27 Nov: restore size after a short copy
         ArrayInitialize(m_atr_m15_buf, 0.0);
         Logger.Error("VOLATILITY",
            StringFormat("CopyBuffer M15 ATR failed: copied=%d error=%d",
                          copied, GetLastError()));
         return false;
      }

      // Convert price distance to pips (ATR is in price units, not pips)
      // Store the current value — rest of buffer used for stability
      double raw_atr = m_atr_m15_buf[0];
      if(raw_atr <= 0)
      {
         Logger.Warn("VOLATILITY", "M15 ATR[0] = 0 — bad indicator data");
         return false;
      }

      m_last_atr_m15_pips = PriceToPips(raw_atr);

      // Convert all buffer values to pips for stability calculation
      for(int i = 0; i < MathMin(copied, VOL_LOOKBACK_M15); i++)
         m_atr_m15_buf[i] = PriceToPips(m_atr_m15_buf[i]);

      return true;
   }

   bool RefreshM5ATR()
   {
      if(m_atr_m5_handle == INVALID_HANDLE) return false;

      ArraySetAsSeries(m_atr_m5_buf, true);
      int copied = CopyBuffer(m_atr_m5_handle, 0, 1,
                              VOL_LOOKBACK_M5, m_atr_m5_buf);
      if(copied <= 0) return false;

      double raw_atr = m_atr_m5_buf[0];
      if(raw_atr <= 0) return false;

      m_last_atr_m5_pips = PriceToPips(raw_atr);

      for(int i = 0; i < MathMin(copied, VOL_LOOKBACK_M5); i++)
         m_atr_m5_buf[i] = PriceToPips(m_atr_m5_buf[i]);

      return true;
   }

   //===================================================================
   // BASELINE RESOLUTION
   //
   // PSEUDO-CODE:
   //   Priority order:
   //   1. ctx.session_avg_atr_pips (calibrated from SpreadGuard) — use if > 0
   //   2. m_last_baseline_pips (from last valid context) — use if SpreadGuard
   //      not yet calibrated but we've seen at least one good value
   //   3. VOL_BASELINE_FALLBACK (15 pips) — last resort
   //
   //   The baseline MUST be positive and sane.
   //   A baseline of 0 would produce divide-by-zero in ratio calculation.
   //   A baseline > 100 pips suggests bad data — fall back to hardcoded.
   //===================================================================
   double ResolveBaseline(const IntelligenceContext &ctx)
   {
      double baseline = ctx.session_avg_atr_pips;

      if(baseline > 0 && baseline < 100.0)
      {
         // Cache this valid baseline for next call
         m_last_baseline_pips = baseline;
         return baseline;
      }

      if(m_last_baseline_pips > 0 && m_last_baseline_pips < 100.0)
         return m_last_baseline_pips;

      return VOL_BASELINE_FALLBACK;
   }

   //===================================================================
   // VOLATILITY STATE CLASSIFICATION
   //
   // PSEUDO-CODE:
   //   Step 1: Calculate ratio = current_atr_m15 / baseline
   //   Step 2: Apply ratio thresholds (primary)
   //   Step 3: Apply absolute thresholds (secondary override)
   //   Step 4: Check last-candle range for NEWS_SPIKE
   //
   //   The ratio is always calculated and stored regardless of state.
   //   Absolute thresholds override ratio ONLY at extremes:
   //     - current_atr < ATR_TOO_QUIET_PIPS (5): force TOO_QUIET
   //       regardless of ratio (prevents a "normal ratio from tiny baseline"
   //       making an effectively zero-ATR session look tradeable)
   //     - current_atr >= ATR_NEWS_SPIKE_PIPS (40): elevate to at least SPIKE
   //       regardless of ratio (protects against under-estimated baseline)
   //
   //   NEWS_SPIKE detection (most severe — checked last):
   //     last_candle_range > VOL_RANGE_SPIKE_MULT × atr_m15
   //     This detects single-candle explosions (news releases, flash events)
   //     even when the rolling ATR hasn't yet caught up.
   //===================================================================
   VOLATILITY_STATE ClassifyVolState(double atr_m15, double baseline,
                                      double last_range, double &ratio_out) const
   {
      // Guard against bad inputs
      if(atr_m15 <= 0)   return VOL_UNKNOWN;
      if(baseline <= 0)  return VOL_UNKNOWN;

      double ratio = atr_m15 / baseline;
      ratio_out = ratio;

      VOLATILITY_STATE state;

      // Primary: ratio-based classification
      if     (ratio < VOL_RATIO_TOO_QUIET)   state = VOL_TOO_QUIET;
      else if(ratio < VOL_RATIO_SUPPRESSED)  state = VOL_SUPPRESSED;
      else if(ratio < VOL_RATIO_NORMAL_HI)   state = VOL_NORMAL;
      else if(ratio < VOL_RATIO_ELEVATED_HI) state = VOL_ELEVATED;
      else                                    state = VOL_SPIKE;

      // Secondary override 1: absolute floor — too quiet regardless of ratio
      // Example: baseline=3 pips (bad calibration), ATR=4 pips, ratio=1.33→NORMAL
      // But 4 pips absolute is below spread cost — must be TOO_QUIET
      if(atr_m15 < ATR_TOO_QUIET_PIPS)
         state = VOL_TOO_QUIET;

      // Secondary override 2: absolute ceiling — spike regardless of ratio
      // Example: baseline=30 pips, ATR=38 pips, ratio=1.27→NORMAL
      // But 38 pips absolute is news-spike territory for Gold
      if(atr_m15 > ATR_NEWS_SPIKE_PIPS)
         state = (state < VOL_SPIKE) ? VOL_SPIKE : state;

      // News spike: last candle explosion — most severe, always wins
      if(last_range > 0 && atr_m15 > 0 &&
         last_range > (VOL_RANGE_SPIKE_MULT * atr_m15))
         state = VOL_NEWS_SPIKE;

      return state;
   }

   //===================================================================
   // SL/TP DISTANCE CALCULATION
   //
   // PSEUDO-CODE:
   //   Base SL = atr_m15 × Config.SLAtrMult    (1.5)
   //   Floor:  max(base, Config.SLPipsMin)       (30 pips minimum)
   //   Ceiling: min(floored, Config.SLPipsMax)   (80 pips maximum)
   //
   //   If base SL > SLPipsMax: SL is out of range.
   //     Set sl_in_range = false.
   //     Still populate sl_pips (clamped value) for informational use.
   //     Downstream: TradeScorer will reject if sl_in_range = false.
   //
   //   TP levels are derived from final clamped SL:
   //     tp1 = sl × TP1RR   (1.5R)
   //     tp2 = sl × TP2RR   (2.5R)
   //
   //   Why clamp AFTER ratio classification?
   //     We want the state (VOL_SPIKE, etc.) to reflect actual ATR.
   //     SL clamping is a risk management decision, not a classification one.
   //     A SPIKE state with a clamped SL is still a SPIKE.
   //===================================================================
   void CalculateSLTP(double atr_m15, VolatilityResult &result) const
   {
      double base_sl = atr_m15 * Config.SLAtrMult;

      // Record raw ATR-derived SL before clamping
      double sl_raw = base_sl;

      // Apply floor
      double sl_floored = MathMax(base_sl, Config.SLPipsMin);

      // Detect out-of-range BEFORE applying ceiling
      result.stop_distance_in_range = (sl_raw <= Config.SLPipsMax);

      // Apply ceiling (always — even if out of range, give a valid number)
      double sl_final = MathMin(sl_floored, Config.SLPipsMax);

      result.recommended_stop_pips          = sl_final;
      result.recommended_stop_price = PipsToPrice(sl_final);
      result.recommended_target1_pips          = sl_final * Config.TP1RR;
      result.recommended_target2_pips          = sl_final * Config.TP2RR;
   }

   //===================================================================
   // ATR STABILITY ANALYSIS
   //
   // PSEUDO-CODE:
   //   Examine ATR(14) values over last VOL_STABILITY_WINDOW (5) M15 bars.
   //   "Expanding": last value > first value by > 10% (upward trend)
   //   "Contracting": last value < first value by > 10% (downward trend)
   //   Neither: stable / flat (10% tolerance band)
   //
   //   Uses the raw m_atr_m15_buf (already in pips after RefreshM15ATR).
   //   buf[0] = most recent, buf[N-1] = oldest in window.
   //
   //   Note: this is ATR stability, not price stability.
   //   Contracting ATR = volatility declining = compression = often precedes expansion.
   //   Expanding ATR = volatility growing = trending activity in motion.
   //===================================================================
   void AnalyseStability(VolatilityResult &result) const
   {
      int window = VOL_STABILITY_WINDOW;
      if(ArraySize(m_atr_m15_buf) <= window)                       // A336 (#14)
      {
         result.atr_expanding   = false;
         result.atr_contracting = false;
         return;
      }
      if(m_atr_m15_buf[0] <= 0 || m_atr_m15_buf[window] <= 0)
      {
         result.atr_expanding   = false;
         result.atr_contracting = false;
         return;
      }

      double newest = m_atr_m15_buf[0];
      double oldest = m_atr_m15_buf[window]; // window bars ago

      if(oldest <= 0)
      {
         result.atr_expanding   = false;
         result.atr_contracting = false;
         return;
      }

      double change_pct = (newest - oldest) / oldest; // signed percentage change

      result.atr_expanding   = (change_pct >  0.10); // > +10%
      result.atr_contracting = (change_pct < -0.10); // < -10%
   }

   //===================================================================
   // LAST M15 CANDLE RANGE
   //
   // PSEUDO-CODE:
   //   Range = High[1] - Low[1] (most recent CLOSED M15 candle).
   //   Shift=1 to skip incomplete current bar.
   //   Returns 0 if data unavailable.
   //===================================================================
   double GetLastM15Range() const
   {
      double h[], l[];
      ArrayResize(h, 1); ArrayResize(l, 1);
      ArraySetAsSeries(h, true);
      ArraySetAsSeries(l, true);

      if(CopyHigh(m_symbol, PERIOD_M15, 1, 1, h) <= 0) return 0.0;
      if(CopyLow(m_symbol,  PERIOD_M15, 1, 1, l) <= 0) return 0.0;

      return PriceToPips(h[0] - l[0]);
   }

   //===================================================================
   // VOLATILITY CONFIDENCE SCORING
   //
   // PSEUDO-CODE:
   //   Confidence = how reliable is the volatility estimate?
   //   High when: NORMAL state, calibrated baseline, stable ATR
   //   Low when:  UNKNOWN, uncalibrated baseline, extreme state
   //
   //   Components:
   //   [A] State quality      (0.0–0.5):
   //       NORMAL:    0.50
   //       SUPPRESSED or ELEVATED: 0.35
   //       TOO_QUIET or SPIKE: 0.10
   //       NEWS_SPIKE: 0.00
   //       UNKNOWN:   0.00
   //
   //   [B] Baseline quality   (0.0–0.30):
   //       Calibrated (SpreadGuard 3+ days data): 0.30
   //       Uncalibrated (using fallback):         0.10
   //
   //   [C] ATR stability      (0.0–0.20):
   //       Neither expanding nor contracting (flat/stable): 0.20
   //       Expanding (trend in motion — predictable):       0.15
   //       Contracting (compression — state may flip):      0.05
   //
   //   Final: sum [A]+[B]+[C], clamped [0.0, 1.0]
   //===================================================================
   double ComputeConfidence(const VolatilityResult &result,
                             bool baseline_calibrated) const
   {
      double score_a = 0.0;
      switch(result.state)
      {
         case VOL_NORMAL:     score_a = 0.50; break;
         case VOL_SUPPRESSED:
         case VOL_ELEVATED:   score_a = 0.35; break;
         case VOL_TOO_QUIET:
         case VOL_SPIKE:      score_a = 0.10; break;
         case VOL_NEWS_SPIKE: score_a = 0.00; break;
         case VOL_UNKNOWN:
         default:             score_a = 0.00; break;
      }

      double score_b = baseline_calibrated ? 0.30 : 0.10;

      double score_c = 0.0;
      if(!result.atr_expanding && !result.atr_contracting) score_c = 0.20;
      else if(result.atr_expanding)                         score_c = 0.15;
      else                                                  score_c = 0.05;

      return MathMin(1.0, score_a + score_b + score_c);
   }

   //===================================================================
   // VOLATILITY QUALITY (0.0–1.0) for MarketQualityScore contribution
   //
   // PSEUDO-CODE:
   //   Measures "how good is the volatility environment for trading?"
   //   Distinct from confidence (which measures "how reliable is the estimate?")
   //
   //   Quality is highest in NORMAL state — the sweet spot for entries.
   //   SUPPRESSED is acceptable but expect tighter range.
   //   ELEVATED is tradeable but risky — SL must be wider.
   //   TOO_QUIET and SPIKE are unsuitable — quality near zero.
   //
   //   Also incorporates ratio distance from ideal (ratio=1.0):
   //     Penalty = abs(ratio - 1.0) × 0.1 (small continuous adjustment)
   //===================================================================
   double ComputeQuality(const VolatilityResult &result) const
   {
      double base_quality = 0.0;
      switch(result.state)
      {
         case VOL_NORMAL:     base_quality = 1.00; break;
         case VOL_SUPPRESSED: base_quality = 0.65; break;
         case VOL_ELEVATED:   base_quality = 0.50; break;
         case VOL_TOO_QUIET:  base_quality = 0.10; break;
         case VOL_SPIKE:      base_quality = 0.10; break;
         case VOL_NEWS_SPIKE: base_quality = 0.00; break;
         case VOL_UNKNOWN:
         default:             base_quality = 0.00; break;
      }

      // Small continuous penalty for distance from ideal ratio (1.0)
      double ratio = result.atr_m15_ratio;
      double ideal_penalty = MathMin(0.20, MathAbs(ratio - 1.0) * 0.10);

      // Penalty for out-of-range SL (signals extreme volatility)
      double sl_penalty = result.stop_distance_in_range ? 0.0 : 0.15;

      return MathMax(0.0, base_quality - ideal_penalty - sl_penalty);
   }

   //===================================================================
   // BUILD: Populate complete VolatilityResult
   //===================================================================
   bool BuildResult(const IntelligenceContext &ctx)
   {
      VolatilityResult r;
      ZeroMemory(r);

      double baseline = ResolveBaseline(ctx);
      bool   baseline_cal = (ctx.session_avg_atr_pips > 0 &&
                              ctx.spread_calibrated);

      r.atr_baseline_pips = baseline;

      // ATR values
      r.atr_m15_pips = m_last_atr_m15_pips;
      r.atr_m5_pips  = m_last_atr_m5_pips;

      if(r.atr_m15_pips <= 0)
      {
         r.is_valid        = false;
         r.invalid_reason  = "atr_m15_zero";
         r.state           = VOL_UNKNOWN;
         r.volatility_quality = 0.0;
         r.evaluated_at    = TimeCurrent();
         m_cached          = r;
         RecordError("atr_m15_zero");
         return false;
      }

      // Last candle range
      r.last_candle_range_pips = GetLastM15Range();
      r.range_atr_ratio = (r.atr_m15_pips > 0)
                          ? r.last_candle_range_pips / r.atr_m15_pips
                          : 0.0;

      // Primary classification (ATR ratio model)
      double ratio = 0.0;
      r.state = ClassifyVolState(r.atr_m15_pips, baseline,
                                  r.last_candle_range_pips, ratio);
      r.atr_m15_ratio = ratio;

      // Stability
      AnalyseStability(r);

      // SL/TP distances
      CalculateSLTP(r.atr_m15_pips, r);

      // Scoring
      double conf    = ComputeConfidence(r, baseline_cal);
      r.volatility_quality = ComputeQuality(r);

      r.evaluated_at = TimeCurrent();
      r.is_valid     = true;

      m_cached     = r;
      m_cache_valid = true;

      RecordSuccess(conf);
      return true;
   }

public:
   //===================================================================
   // CONSTRUCTOR
   //===================================================================
   CVolatilityEngine() :
      m_atr_m15_handle(INVALID_HANDLE),
      m_atr_m5_handle(INVALID_HANDLE),
      m_last_atr_m15_pips(0.0),
      m_last_atr_m5_pips(0.0),
      m_last_baseline_pips(VOL_BASELINE_FALLBACK),
      m_last_m15_bar(0),
      m_last_m5_bar(0),
      m_stability_write(0),
      m_cache_valid(false)
   {
      ArrayInitialize(m_atr_m15_buf,      0.0);
      ArrayInitialize(m_atr_m5_buf,       0.0);
      ArrayInitialize(m_atr_stability_buf, 0.0);

      m_meta.id          = ENG_VOLATILITY;
      m_meta.name        = "VOLATILITY";
      m_meta.description = "ATR ratio volatility classification + SL/TP";
      m_meta.enabled     = true;
      m_meta.initialized = false;
      m_meta.available   = false;

      ZeroMemory(m_cached);
      m_cached.is_valid = false;
      m_cached.state    = VOL_UNKNOWN;
   }

   //===================================================================
   // INIT
   //
   // PSEUDO-CODE:
   //   1. Create iATR handles for M15 and M5.
   //      Period = Config.ATRPeriod (default 14).
   //   2. Perform initial buffer fill to check data availability.
   //   3. If M15 handle invalid: engine unavailable (non-fatal).
   //   4. If M5 handle invalid: log warning, continue with M15 only.
   //      M5 data is secondary — engine can degrade without it.
   //===================================================================
   virtual bool Init(string symbol, double pip_size) override
   {
      m_symbol   = symbol;
      m_pip_size = pip_size;

      if(pip_size <= 0)
      {
         Logger.Fatal("VOLATILITY", "Init: pip_size <= 0");
         return false;
      }

      ArrayResize(m_atr_m15_buf, VOL_LOOKBACK_M15);
      ArrayResize(m_atr_m5_buf,  VOL_LOOKBACK_M5);
      ArrayResize(m_atr_stability_buf, VOL_STABILITY_WINDOW + 1);

      Logger.Info("VOLATILITY",
         StringFormat("Initializing. symbol=%s atr_period=%d pip_size=%.5f",
                       symbol, Config.ATRPeriod, pip_size));

      // Create M15 ATR handle
      m_atr_m15_handle = iATR(symbol, PERIOD_M15, Config.ATRPeriod);
      if(m_atr_m15_handle == INVALID_HANDLE)
      {
         Logger.Error("VOLATILITY",
            StringFormat("iATR M15 failed. error=%d", GetLastError()));
         return false; // M15 ATR is essential — cannot operate without it
      }

      // Create M5 ATR handle (non-essential)
      m_atr_m5_handle = iATR(symbol, PERIOD_M5, Config.ATRPeriod);
      if(m_atr_m5_handle == INVALID_HANDLE)
      {
         Logger.Warn("VOLATILITY",
            "iATR M5 failed — M5 ATR unavailable. Continuing with M15 only.");
         // Not fatal — m_last_atr_m5_pips stays 0
      }

      // MT5 indicators need a warm-up period before data is available.
      // First few calls to CopyBuffer return 0 bars.
      // This is normal — engine will produce VOL_UNKNOWN until data arrives.
      // We attempt an initial fill but don't fail if it returns 0.
      RefreshM15ATR();
      if(m_atr_m5_handle != INVALID_HANDLE) RefreshM5ATR();

      m_meta.initialized = true;
      m_initialized      = true;
      m_meta.available   = (m_last_atr_m15_pips > 0);

      Logger.Info("VOLATILITY",
         StringFormat("Init complete. m15_atr=%.1f pips available=%d",
                       m_last_atr_m15_pips, (int)m_meta.available));
      return true;
   }

   //===================================================================
   // EVALUATE — called by coordinator on M15 or M5 bar close
   //
   // PSEUDO-CODE:
   //   Coordinator sets ctx.new_m15_bar / ctx.new_m5_bar.
   //   On M15 bar close: refresh M15 ATR, rebuild full result.
   //   On M5 bar close only: refresh M5 ATR for range tracking.
   //     Do NOT rebuild full result on M5 alone — M15 ATR is canonical.
   //   Return true if result is valid.
   //
   //   IMPORTANT: even if ctx.new_m15_bar=false, the coordinator
   //   calls Evaluate() at least once per M15 period (when M15 fires).
   //   This ensures result is never more than one M15 bar old.
   //===================================================================
   virtual bool Evaluate(const IntelligenceContext &ctx) override
   {
      if(!m_initialized) return false;

      bool need_rebuild = false;

      // M5 bar close — refresh M5 ATR (range tracking only)
      if(ctx.new_m5_bar)
      {
         if(m_atr_m5_handle != INVALID_HANDLE)
            RefreshM5ATR();
      }

      // M15 bar close — full refresh and rebuild
      if(ctx.new_m15_bar)
      {
         if(!RefreshM15ATR())
         {
            // M15 refresh failed — try to use last known good value
            if(m_last_atr_m15_pips <= 0)
            {
               RecordError("m15_atr_refresh_failed");
               m_cached.is_valid    = false;
               m_cached.state       = VOL_UNKNOWN;
               m_cached.invalid_reason = "m15_refresh_failed";
               return false;
            }
            Logger.Warn("VOLATILITY",
               "M15 ATR refresh failed — using last known value");
         }
         need_rebuild = true;
      }

      // Rebuild result if M15 data changed OR first evaluation
      if(need_rebuild || !m_cache_valid)
         return BuildResult(ctx);

      // No new M15 bar — update baseline in cached result if context changed
      // (SpreadGuard may have recalibrated since last M15 close)
      if(ctx.session_avg_atr_pips > 0 && m_cache_valid)
      {
         double new_baseline = ResolveBaseline(ctx);
         if(MathAbs(new_baseline - m_cached.atr_baseline_pips) > 1.0)
         {
            // Baseline shifted significantly — reclassify with same ATR
            return BuildResult(ctx);
         }
      }

      return m_cached.is_valid;
   }

   //===================================================================
   // GET CACHED RESULT (O(1) — called every tick)
   //===================================================================
   VolatilityResult GetCached() const { return m_cached; }

   //===================================================================
   // RESET
   //===================================================================
   virtual void Reset() override
   {
      m_last_atr_m15_pips  = 0.0;
      m_last_atr_m5_pips   = 0.0;
      m_last_baseline_pips = VOL_BASELINE_FALLBACK;
      m_last_m15_bar       = 0;
      m_last_m5_bar        = 0;
      m_cache_valid        = false;
      m_initialized        = false;
      m_meta.available     = false;
      ArrayInitialize(m_atr_m15_buf,      0.0);
      ArrayInitialize(m_atr_m5_buf,       0.0);
      ArrayInitialize(m_atr_stability_buf, 0.0);
      ZeroMemory(m_cached);
      m_cached.state    = VOL_UNKNOWN;
      m_cached.is_valid = false;
      Logger.Info("VOLATILITY", "Engine reset");
   }

   //===================================================================
   // SHUTDOWN — release MT5 indicator handles
   //
   // PSEUDO-CODE:
   //   CRITICAL: every handle created with iATR() MUST be released.
   //   Unreleased handles accumulate per EA restart cycle.
   //   MT5 does not auto-release when EA is removed from chart.
   //   IndicatorRelease() returns true on success, false if handle invalid.
   //===================================================================
   virtual void Shutdown() override
   {
      if(m_atr_m15_handle != INVALID_HANDLE)
      {
         if(!IndicatorRelease(m_atr_m15_handle))
            Logger.Warn("VOLATILITY",
               StringFormat("IndicatorRelease M15 failed: handle=%d error=%d",
                             m_atr_m15_handle, GetLastError()));
         m_atr_m15_handle = INVALID_HANDLE;
      }
      if(m_atr_m5_handle != INVALID_HANDLE)
      {
         if(!IndicatorRelease(m_atr_m5_handle))
            Logger.Warn("VOLATILITY",
               StringFormat("IndicatorRelease M5 failed: handle=%d error=%d",
                             m_atr_m5_handle, GetLastError()));
         m_atr_m5_handle = INVALID_HANDLE;
      }

      Logger.Info("VOLATILITY",
         StringFormat("Shutdown. evals=%d errors=%d last_atr_m15=%.1f",
                       m_meta.eval_count, m_meta.error_count,
                       m_last_atr_m15_pips));

      IIntelligenceEngine::Shutdown();
   }

   //--- Convenience accessors for other engines (coordinator, SpreadGuard hook)
   double GetATRM15Pips()   const { return m_last_atr_m15_pips; }
   double GetATRM5Pips()    const { return m_last_atr_m5_pips; }
   VOLATILITY_STATE GetState() const { return m_cached.state; }
   bool   IsTradeable()     const
   {
      return (m_cached.is_valid &&
              m_cached.state != VOL_TOO_QUIET &&
              m_cached.state != VOL_NEWS_SPIKE &&
              m_cached.state != VOL_UNKNOWN);
   }
};

//--- Global singleton
CVolatilityEngine VolatilityEngine;

#endif // CVOLATILITYENGINE_MQH

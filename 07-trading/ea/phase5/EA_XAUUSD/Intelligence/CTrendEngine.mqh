
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA - Trend Engine                            |
//| File: Intelligence/CTrendEngine.mqh                               |
//| Purpose: Classify the H1 directional trend with confidence.       |
//|           EMA alignment + swing structure (H1) + price position.  |
//| Phase: 3 - Step 6                                                 |
//|                                                                    |
//| ENGINE ID: ENG_TREND                                             |
//| INPUTS: H1 OHLC, iMA H1 EMA20/EMA50, StructureResult.h1 (inj),   |
//|         RegimeResult (inj, for agreement check only)              |
//|                                                                    |
//| REVISIONS: engulfing = confidence modifier only; structure        |
//|   unavailability degrades not blocks; Asian session conf x 0.80.  |
//| BOUNDARIES: no execution, no signals, no scoring logic.           |
//+------------------------------------------------------------------+
#ifndef CTRENDENGINE_MQH
#define CTRENDENGINE_MQH

#include "IIntelligenceEngine.mqh"

class CTrendEngine : public IIntelligenceEngine
{
private:
   int      m_ema20_handle;
   int      m_ema50_handle;

   double   m_ema20_buf[];
   double   m_ema50_buf[];

   double   m_h1_opens[];
   double   m_h1_highs[];
   double   m_h1_lows[];
   double   m_h1_closes[];

   datetime m_last_h1_bar;

   TrendResult  m_cached;
   bool         m_cache_valid;

   StructureResult  m_last_structure;
   RegimeResult     m_last_regime;
   bool             m_structure_provided;
   bool             m_regime_provided;

   bool             m_last_in_active_session;

   //--- Buffer refresh
   bool RefreshEMABuffers()
   {
      ArraySetAsSeries(m_ema20_buf, true);
      ArraySetAsSeries(m_ema50_buf, true);
      int c20 = CopyBuffer(m_ema20_handle, 0, 1, TREND_LOOKBACK_H1, m_ema20_buf);
      int c50 = CopyBuffer(m_ema50_handle, 0, 1, TREND_LOOKBACK_H1, m_ema50_buf);
      if(c20 < 2 || c50 < 2)
      {
         Logger.Error("TREND",
            StringFormat("EMA buffer refresh failed: c20=%d c50=%d err=%d",
                          c20, c50, GetLastError()));
         return false;
      }
      return true;
   }

   bool RefreshH1Candles()
   {
      double tmp_o[], tmp_h[], tmp_l[], tmp_c[];
      ArraySetAsSeries(tmp_o, true);
      ArraySetAsSeries(tmp_h, true);
      ArraySetAsSeries(tmp_l, true);
      ArraySetAsSeries(tmp_c, true);

      int co = CopyOpen(m_symbol,  PERIOD_H1, 1, TREND_CANDLE_BUFFER, tmp_o);
      int ch = CopyHigh(m_symbol,  PERIOD_H1, 1, TREND_CANDLE_BUFFER, tmp_h);
      int cl = CopyLow(m_symbol,   PERIOD_H1, 1, TREND_CANDLE_BUFFER, tmp_l);
      int cc = CopyClose(m_symbol, PERIOD_H1, 1, TREND_CANDLE_BUFFER, tmp_c);

      if(co < TREND_CANDLE_BUFFER || ch < TREND_CANDLE_BUFFER ||
         cl < TREND_CANDLE_BUFFER || cc < TREND_CANDLE_BUFFER)
      {
         ArrayInitialize(m_h1_opens,  0.0);
         ArrayInitialize(m_h1_highs,  0.0);
         ArrayInitialize(m_h1_lows,   0.0);
         ArrayInitialize(m_h1_closes, 0.0);
         return false;
      }
      for(int i = 0; i < TREND_CANDLE_BUFFER; i++)
      {
         m_h1_opens[i]  = tmp_o[i];
         m_h1_highs[i]  = tmp_h[i];
         m_h1_lows[i]   = tmp_l[i];
         m_h1_closes[i] = tmp_c[i];
      }
      return true;
   }

   //--- EMA cross detection
   bool CheckRecentCross() const
   {
      int lookback = MathMin(TREND_CROSS_LOOKBACK, TREND_LOOKBACK_H1 - 1);
      for(int i = 0; i < lookback; i++)
      {
         if(m_ema20_buf[i] <= 0 || m_ema50_buf[i] <= 0) continue;
         if(m_ema20_buf[i+1] <= 0 || m_ema50_buf[i+1] <= 0) continue;
         double curr_diff = m_ema20_buf[i]   - m_ema50_buf[i];
         double prev_diff = m_ema20_buf[i+1] - m_ema50_buf[i+1];
         if((curr_diff > 0 && prev_diff < 0) ||
            (curr_diff < 0 && prev_diff > 0))
            return true;
      }
      return false;
   }

   //--- Engulfing detection
   bool DetectBullishEngulfingAt(int idx) const
   {
      if(idx < 0 || idx >= TREND_CANDLE_BUFFER - 1) return false;
      if(m_h1_opens[idx] <= 0 || m_h1_opens[idx+1] <= 0) return false;
      double prev_o = m_h1_opens[idx+1];
      double prev_c = m_h1_closes[idx+1];
      double curr_o = m_h1_opens[idx];
      double curr_c = m_h1_closes[idx];
      bool prev_bearish = (prev_c < prev_o);
      bool curr_bullish = (curr_c > curr_o);
      bool body_engulfs = (curr_c >= prev_o) && (curr_o <= prev_c);
      return prev_bearish && curr_bullish && body_engulfs;
   }

   bool DetectBearishEngulfingAt(int idx) const
   {
      if(idx < 0 || idx >= TREND_CANDLE_BUFFER - 1) return false;
      if(m_h1_opens[idx] <= 0 || m_h1_opens[idx+1] <= 0) return false;
      double prev_o = m_h1_opens[idx+1];
      double prev_c = m_h1_closes[idx+1];
      double curr_o = m_h1_opens[idx];
      double curr_c = m_h1_closes[idx];
      bool prev_bullish = (prev_c > prev_o);
      bool curr_bearish = (curr_c < curr_o);
      bool body_engulfs = (curr_c <= prev_o) && (curr_o >= prev_c);
      return prev_bullish && curr_bearish && body_engulfs;
   }

   bool HasBullishEngulfInWindow() const
   {
      int window = MathMin(TREND_ENGULF_WINDOW, TREND_CANDLE_BUFFER - 1);
      for(int i = 0; i < window; i++)
         if(DetectBullishEngulfingAt(i)) return true;
      return false;
   }

   bool HasBearishEngulfInWindow() const
   {
      int window = MathMin(TREND_ENGULF_WINDOW, TREND_CANDLE_BUFFER - 1);
      for(int i = 0; i < window; i++)
         if(DetectBearishEngulfingAt(i)) return true;
      return false;
   }

   //--- Observation scoring
   struct ObservationResult
   {
      bool   ema_bull;
      bool   ema_bear;
      bool   swing_bull;
      bool   swing_bear;
      bool   position_bull;
      bool   position_bear;
      double ema_score;
      double swing_score;
      double position_score;
      double ema_sep_pips;
      double price_to_ema20_pips;
   };

   void ScoreObservations(double current_price, ObservationResult &obs) const
   {
      ZeroMemory(obs);
      double ema20 = m_ema20_buf[0];
      double ema50 = m_ema50_buf[0];

      // Observation 1: EMA alignment
      if(ema20 > 0 && ema50 > 0)
      {
         double sep_price = ema20 - ema50;
         obs.ema_sep_pips = PriceToPips(MathAbs(sep_price));
         double min_sep_price = PipsToPrice(TREND_EMA_MIN_SEP_PIPS);
         obs.ema_bull = (sep_price >=  min_sep_price);
         obs.ema_bear = (sep_price <= -min_sep_price);
         obs.ema_score = MathMin(1.0, obs.ema_sep_pips / TREND_EMA_FULL_SEP_PIPS);
      }

      // Observation 2: Swing structure (optional)
      if(m_structure_provided && m_last_structure.h1_available)
      {
         obs.swing_bull = m_last_structure.h1.hh_hl;
         obs.swing_bear = m_last_structure.h1.lh_ll;
         obs.swing_score = m_last_structure.h1.structure_clarity;
      }

      // Observation 3: Price position vs EMA20
      if(ema20 > 0 && current_price > 0)
      {
         double dist_price = current_price - ema20;
         obs.price_to_ema20_pips = PriceToPips(MathAbs(dist_price)) *
                                    (dist_price >= 0 ? 1.0 : -1.0);
         double min_pos_price = PipsToPrice(TREND_POSITION_MIN_PIPS);
         obs.position_bull = (dist_price >=  min_pos_price);
         obs.position_bear = (dist_price <= -min_pos_price);
         obs.position_score = MathMin(1.0,
            MathAbs(obs.price_to_ema20_pips) / TREND_POSITION_FULL_PIPS);
      }
   }

   //--- State classification
   void ClassifyState(const ObservationResult &obs, bool cross_detected,
                       TREND_STATE &state_out, TRADE_DIR &dir_out,
                       int &conforming_swings_out) const
   {
      int bull_count = (int)obs.ema_bull + (int)obs.swing_bull + (int)obs.position_bull;
      int bear_count = (int)obs.ema_bear + (int)obs.swing_bear + (int)obs.position_bear;

      int aligned = 0;
      if(bull_count > bear_count)
      {
         dir_out  = DIR_LONG;
         aligned  = bull_count;
         conforming_swings_out = obs.swing_bull ? 1 : 0;
      }
      else if(bear_count > bull_count)
      {
         dir_out  = DIR_SHORT;
         aligned  = bear_count;
         conforming_swings_out = obs.swing_bear ? 1 : 0;
      }
      else
      {
         dir_out  = DIR_NONE;
         aligned  = 0;
         conforming_swings_out = 0;
      }

      if(cross_detected)
      {
         state_out = TREND_RANGING;
         return;
      }
      if(aligned == 0 || aligned == 1) state_out = TREND_UNKNOWN;
      else if(aligned == 2)
         state_out = (dir_out == DIR_LONG) ? TREND_WEAK_BULL : TREND_WEAK_BEAR;
      else
         state_out = (dir_out == DIR_LONG) ? TREND_STRONG_BULL : TREND_STRONG_BEAR;
   }

   //--- Confidence (session-aware)
   double ComputeConfidence(TREND_STATE state, TRADE_DIR direction,
                             const ObservationResult &obs, double engulf_adj) const
   {
      if(state == TREND_UNKNOWN || state == TREND_RANGING) return 0.0;
      double base = (obs.ema_score      * TREND_W_EMA) +
                    (obs.swing_score    * TREND_W_STRUCTURE) +
                    (obs.position_score * TREND_W_POSITION);
      if(state == TREND_STRONG_BULL || state == TREND_STRONG_BEAR)
         base += TREND_STRONG_CONF_BONUS;
      base += engulf_adj;
      if(!m_last_in_active_session)
         base *= TREND_ASIAN_CONF_SCALE;
      return MathMax(0.0, MathMin(1.0, base));
   }

   //--- Build result
   bool BuildResult(const IntelligenceContext &ctx)
   {
      TrendResult r;
      ZeroMemory(r);
      r.evaluated_at = TimeCurrent();
      r.is_valid     = false;

      m_last_in_active_session = ctx.in_active_session;

      double current_price = ctx.mid_price;
      if(current_price <= 0) current_price = ctx.bid;
      if(current_price <= 0)
      {
         r.state = TREND_UNKNOWN; r.direction = DIR_NONE;
         r.invalid_reason = "no_price_data";
         m_cached = r; RecordError("no_price_data");
         return false;
      }

      r.ema20 = (m_ema20_buf[0] > 0) ? m_ema20_buf[0] : 0.0;
      r.ema50 = (m_ema50_buf[0] > 0) ? m_ema50_buf[0] : 0.0;
      if(r.ema20 <= 0 || r.ema50 <= 0)
      {
         r.state = TREND_UNKNOWN; r.direction = DIR_NONE;
         r.invalid_reason = "ema_data_unavailable";
         m_cached = r; RecordError("ema_data_unavailable");
         return false;
      }

      ObservationResult obs;
      ScoreObservations(current_price, obs);

      bool cross = CheckRecentCross();

      int conforming = 0;
      ClassifyState(obs, cross, r.state, r.direction, conforming);

      r.bullish_engulf_present = HasBullishEngulfInWindow();
      r.bearish_engulf_present = HasBearishEngulfInWindow();

      double engulf_adj = 0.0;
      if(r.bullish_engulf_present && r.direction == DIR_SHORT)
         engulf_adj -= TREND_ENGULF_CONF_PENALTY;
      if(r.bearish_engulf_present && r.direction == DIR_LONG)
         engulf_adj -= TREND_ENGULF_CONF_PENALTY;
      r.engulf_confidence_adj = engulf_adj;

      r.confidence = ComputeConfidence(r.state, r.direction, obs, engulf_adj);

      r.ema_aligned         = obs.ema_bull || obs.ema_bear;
      r.ema_separation_pips = obs.ema_sep_pips;
      r.ema_alignment_score = obs.ema_score;
      r.swing_valid         = obs.swing_bull || obs.swing_bear;
      r.conforming_swings   = conforming;
      r.structure_score     = obs.swing_score;
      if(m_structure_provided && m_last_structure.h1_available)
      {
         r.last_swing_high = m_last_structure.h1.last_high;
         r.last_swing_low  = m_last_structure.h1.last_low;
      }
      r.price_to_ema20_pips = obs.price_to_ema20_pips;
      r.position_score      = obs.position_score;

      r.agrees_with_regime = false;
      if(m_regime_provided && m_last_regime.is_valid &&
         r.direction != DIR_NONE && m_last_regime.direction != DIR_NONE &&
         r.direction == m_last_regime.direction)
      {
         r.agrees_with_regime = true;
      }

      r.is_valid = true;

      if(r.state != m_cached.state || r.direction != m_cached.direction)
      {
         Logger.Info("TREND",
            StringFormat("Trend changed: %s -> %s dir=%s conf=%.2f",
                          EnumToString(m_cached.state), EnumToString(r.state),
                          EnumToString(r.direction), r.confidence),
            StringFormat("ema_sep=%.1f price_ema20=%.1f clarity=%.2f engulf=%.2f "
                          "agrees=%d cross=%d asian=%d",
                          r.ema_separation_pips, r.price_to_ema20_pips,
                          r.structure_score, r.engulf_confidence_adj,
                          (int)r.agrees_with_regime, (int)cross,
                          (int)(!m_last_in_active_session)));
      }

      m_cached      = r;
      m_cache_valid = true;
      RecordSuccess(r.confidence);
      return true;
   }

public:
   CTrendEngine() :
      m_ema20_handle(INVALID_HANDLE),
      m_ema50_handle(INVALID_HANDLE),
      m_last_h1_bar(0),
      m_cache_valid(false),
      m_structure_provided(false),
      m_regime_provided(false),
      m_last_in_active_session(true)
   {
      ArrayInitialize(m_ema20_buf,  0.0);
      ArrayInitialize(m_ema50_buf,  0.0);
      ArrayInitialize(m_h1_opens,   0.0);
      ArrayInitialize(m_h1_highs,   0.0);
      ArrayInitialize(m_h1_lows,    0.0);
      ArrayInitialize(m_h1_closes,  0.0);

      m_meta.id          = ENG_TREND;
      m_meta.name        = "TREND";
      m_meta.description = "H1 trend classification with 3-observation scoring";
      m_meta.enabled     = true;
      m_meta.initialized = false;
      m_meta.available   = false;

      ZeroMemory(m_cached);
      ZeroMemory(m_last_structure);
      ZeroMemory(m_last_regime);
      m_cached.state     = TREND_UNKNOWN;
      m_cached.direction = DIR_NONE;
      m_cached.is_valid  = false;
   }

   void SetStructureResult(const StructureResult &sr)
   {
      m_last_structure     = sr;
      m_structure_provided = true;
   }
   void SetRegimeResult(const RegimeResult &rr)
   {
      m_last_regime     = rr;
      m_regime_provided = true;
   }

   virtual bool Init(string symbol, double pip_size) override
   {
      m_symbol   = symbol;
      m_pip_size = pip_size;
      if(pip_size <= 0)
      {
         Logger.Fatal("TREND", "Init: pip_size <= 0");
         return false;
      }
      ArrayResize(m_ema20_buf, TREND_LOOKBACK_H1);
      ArrayResize(m_ema50_buf, TREND_LOOKBACK_H1);
      ArrayResize(m_h1_opens,  TREND_CANDLE_BUFFER);
      ArrayResize(m_h1_highs,  TREND_CANDLE_BUFFER);
      ArrayResize(m_h1_lows,   TREND_CANDLE_BUFFER);
      ArrayResize(m_h1_closes, TREND_CANDLE_BUFFER);

      Logger.Info("TREND",
         StringFormat("Initializing. symbol=%s ema_fast=%d ema_slow=%d",
                       symbol, Config.EMA_Fast, Config.EMA_Slow));

      m_ema20_handle = iMA(symbol, PERIOD_H1, Config.EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
      if(m_ema20_handle == INVALID_HANDLE)
      {
         Logger.Fatal("TREND", StringFormat("iMA EMA20 H1 failed. err=%d", GetLastError()));
         return false;
      }
      m_ema50_handle = iMA(symbol, PERIOD_H1, Config.EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
      if(m_ema50_handle == INVALID_HANDLE)
      {
         Logger.Fatal("TREND", StringFormat("iMA EMA50 H1 failed. err=%d", GetLastError()));
         IndicatorRelease(m_ema20_handle);
         m_ema20_handle = INVALID_HANDLE;
         return false;
      }

      RefreshEMABuffers();
      RefreshH1Candles();
      m_last_h1_bar = iTime(symbol, PERIOD_H1, 1);

      m_meta.initialized = true;
      m_initialized      = true;
      m_meta.available   = (m_ema20_buf[0] > 0 && m_ema50_buf[0] > 0);

      Logger.Info("TREND",
         StringFormat("Init complete. ema20=%.5f ema50=%.5f available=%d",
                       m_ema20_buf[0], m_ema50_buf[0], (int)m_meta.available));
      return true;
   }

   virtual bool Evaluate(const IntelligenceContext &ctx) override
   {
      if(!m_initialized) return false;
      if(!ctx.new_h1_bar && m_cache_valid) return m_cached.is_valid;

      bool ema_ok = RefreshEMABuffers();
      RefreshH1Candles();
      if(!ema_ok)
      {
         m_cached.is_valid  = false;
         m_cached.state     = TREND_UNKNOWN;
         m_cached.direction = DIR_NONE;
         m_cached.invalid_reason = "ema_refresh_failed";
         RecordError("ema_refresh_failed");
         return false;
      }
      m_last_h1_bar = iTime(m_symbol, PERIOD_H1, 1);
      return BuildResult(ctx);
   }

   TrendResult GetCached() const { return m_cached; }

   virtual void Reset() override
   {
      m_last_h1_bar        = 0;
      m_cache_valid        = false;
      m_structure_provided = false;
      m_regime_provided    = false;
      ArrayInitialize(m_ema20_buf,  0.0);
      ArrayInitialize(m_ema50_buf,  0.0);
      ArrayInitialize(m_h1_opens,   0.0);
      ArrayInitialize(m_h1_highs,   0.0);
      ArrayInitialize(m_h1_lows,    0.0);
      ArrayInitialize(m_h1_closes,  0.0);
      ZeroMemory(m_cached);
      m_cached.state     = TREND_UNKNOWN;
      m_cached.direction = DIR_NONE;
      m_cached.is_valid  = false;
      m_initialized      = false;
      m_meta.available   = false;
      Logger.Info("TREND", "Engine reset");
   }

   virtual void Shutdown() override
   {
      if(m_ema20_handle != INVALID_HANDLE)
      {
         if(!IndicatorRelease(m_ema20_handle))
            Logger.Warn("TREND", StringFormat("Release EMA20 failed: err=%d", GetLastError()));
         m_ema20_handle = INVALID_HANDLE;
      }
      if(m_ema50_handle != INVALID_HANDLE)
      {
         if(!IndicatorRelease(m_ema50_handle))
            Logger.Warn("TREND", StringFormat("Release EMA50 failed: err=%d", GetLastError()));
         m_ema50_handle = INVALID_HANDLE;
      }
      Logger.Info("TREND",
         StringFormat("Shutdown. evals=%d errors=%d final_state=%s",
                       m_meta.eval_count, m_meta.error_count,
                       EnumToString(m_cached.state)));
      IIntelligenceEngine::Shutdown();
   }

   TREND_STATE GetState()        const { return m_cached.state; }
   TRADE_DIR   GetDirection()    const { return m_cached.direction; }
   double      GetTrendConf()    const { return m_cached.confidence; }
   bool        AgreesWithRegime() const { return m_cached.agrees_with_regime; }
   bool        IsTrending()      const
   {
      return (m_cached.state == TREND_STRONG_BULL ||
              m_cached.state == TREND_STRONG_BEAR ||
              m_cached.state == TREND_WEAK_BULL   ||
              m_cached.state == TREND_WEAK_BEAR);
   }
};

//--- Global singleton
CTrendEngine TrendEngine;

#endif // CTRENDENGINE_MQH

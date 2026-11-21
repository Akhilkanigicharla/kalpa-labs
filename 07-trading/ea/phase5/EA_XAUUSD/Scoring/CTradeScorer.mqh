//+------------------------------------------------------------------+
//| XAUUSD Institutional EA - Trade Scorer & Decision Engine          |
//| File: Scoring/CTradeScorer.mqh                                    |
//| Purpose: Turn the IntelligencePacket into a concrete trade        |
//|          decision. Option A: score-gated entry with a             |
//|          pullback-and-resume trigger, sweep-gated for Gold.       |
//| Phase: 4                                                          |
//|                                                                    |
//| DECISION PIPELINE (all must pass):                                |
//|   1. Packet valid + not degraded                                  |
//|   2. Quality score >= threshold (+ transition penalty)            |
//|   3. direction_valid (regime & trend agree — trend veto)          |
//|   4. Not in blocked persistence state                             |
//|   5. Volatility floor (avoid dead range)                          |
//|   6. Pullback-and-resume trigger fires on M15                     |
//|   7. Sweep gate — not entering into opposing fresh sweep          |
//|                                                                    |
//| OUTPUT: TradeDecision (by value). Scorer decides WHETHER +        |
//|         HOW GOOD. It does NOT set SL/TP/lot (Phase 5 owns that).  |
//|                                                                    |
//| STRICT BOUNDARIES: no OrderSend, no position mutation,            |
//|   no sizing. Reads packet + M15 candles only.                     |
//+------------------------------------------------------------------+
#ifndef CTRADESCORER_MQH
#define CTRADESCORER_MQH

#include "../Include/Defines.mqh"
#include "../Include/PriceUtils.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "../Intelligence/IntelligenceTypes.mqh"

class CTradeScorer
{
private:
   string           m_symbol;
   bool             m_initialized;

   //--- Cached last decision (for logging / dashboard)
   TradeDecision    m_last_decision;

   //--- Diagnostics
   int              m_eval_count;
   int              m_valid_count;
   int              m_reject_counts[9];   // Indexed by DECISION_REASON

   //===================================================================
   // M15 CANDLE FETCH (dynamic arrays — MQL5 requires for series)
   //
   // Returns the last closed M15 candle's OHLC via out-params.
   // idx 0 = most recent CLOSED bar (shift 1 from current).
   //===================================================================
   bool GetLastM15(double &o, double &h, double &l, double &c)
   {
      double bo[], bh[], bl[], bc[];
      ArrayResize(bo, 2); ArrayResize(bh, 2);
      ArrayResize(bl, 2); ArrayResize(bc, 2);
      ArraySetAsSeries(bo, true);
      ArraySetAsSeries(bh, true);
      ArraySetAsSeries(bl, true);
      ArraySetAsSeries(bc, true);

      int no = CopyOpen(m_symbol,  PERIOD_M15, 1, 2, bo);
      int nh = CopyHigh(m_symbol,  PERIOD_M15, 1, 2, bh);
      int nl = CopyLow(m_symbol,   PERIOD_M15, 1, 2, bl);
      int nc = CopyClose(m_symbol, PERIOD_M15, 1, 2, bc);

      if(no < 1 || nh < 1 || nl < 1 || nc < 1)
      {
         Logger.Debug("TRADE_SCORER",
            StringFormat("M15 fetch partial: o=%d h=%d l=%d c=%d", no, nh, nl, nc));
         return false;
      }

      o = bo[0]; h = bh[0]; l = bl[0]; c = bc[0];
      return true;
   }

   //===================================================================
   // VOLATILITY FLOOR
   //
   // Reject when ATR ratio shows a dead range — RR dies in chop.
   // Uses the VolatilityResult already in the packet.
   //===================================================================
   bool VolatilityOK(const IntelligencePacket &pkt) const
   {
      if(!pkt.volatility.is_valid) return false;
      // Dead range: current ATR well below session baseline
      if(pkt.volatility.atr_m15_ratio > 0 &&
         pkt.volatility.atr_m15_ratio < TS_VOL_FLOOR_RATIO)
         return false;
      // Reject dead-range states (no tradeable edge)
      if(pkt.volatility.state == VOL_TOO_QUIET) return false;
      if(pkt.volatility.state == VOL_UNKNOWN)   return false;
      // Reject dangerous spike states (news / circuit-breaker territory)
      if(pkt.volatility.state == VOL_SPIKE)      return false;
      if(pkt.volatility.state == VOL_NEWS_SPIKE) return false;
      return true;
   }

   //===================================================================
   // PERSISTENCE BLOCK CHECK
   //
   // Block during startup warmup (persistence not valid) and while the
   // regime is in a forced-range/transition that shouldn't trade.
   //===================================================================
   bool PersistenceBlocked(const IntelligencePacket &pkt) const
   {
      if(!pkt.persistence.is_valid) return true;   // startup warmup
      // confirmed_regime UNKNOWN = not yet adopted
      if(pkt.persistence.confirmed_regime == REGIME_UNKNOWN) return true;
      return false;
   }

   //===================================================================
   // PULLBACK-AND-RESUME TRIGGER (M15)
   //
   // Context: H4/H1 direction already agreed (dir). We want price to
   // have retraced toward EMA20, then printed a resumption candle in
   // the trend direction on the last closed M15 bar.
   //
   //   LONG:  price near/above EMA20 after dip; last M15 closes bullish
   //          with body >= TS_RESUME_MIN_BODY_PIPS
   //   SHORT: mirror
   //
   // pullback distance measured from packet.trend.ema20 to price.
   //===================================================================
   bool PullbackResume(const IntelligencePacket &pkt, TRADE_DIR dir,
                       double o, double h, double l, double c,
                       double &pullback_pips_out)
   {
      double ema20 = pkt.trend.ema20;
      if(ema20 <= 0) return false;

      double ref_price = c;  // last closed M15 close as the working price

      double dist_pips = PriceUtils.PriceToPips(MathAbs(ref_price - ema20));
      pullback_pips_out = dist_pips;

      // Must be within pullback proximity of EMA20 (a real pullback context)
      if(dist_pips > Config.PullbackMaxPips) return false;

      double body_pips = PriceUtils.PriceToPips(MathAbs(c - o));
      if(body_pips < TS_RESUME_MIN_BODY_PIPS) return false;

      if(dir == DIR_LONG)
      {
         // Resumption candle bullish, closing back above/near EMA20
         bool bullish = (c > o);
         bool reclaim = (c >= ema20 - PriceUtils.PipsToPrice(TS_RESUME_MIN_BODY_PIPS));
         return bullish && reclaim;
      }
      else if(dir == DIR_SHORT)
      {
         bool bearish = (c < o);
         bool reject  = (c <= ema20 + PriceUtils.PipsToPrice(TS_RESUME_MIN_BODY_PIPS));
         return bearish && reject;
      }
      return false;
   }

   //===================================================================
   // SWEEP GATE
   //
   // On Gold, a pullback that "resumes" is often a liquidity sweep about
   // to reverse. Block entry when a FRESH sweep points AGAINST our
   // intended direction. Reward (but don't require) a sweep that points
   // WITH our direction.
   //
   //   Returns false  => gate blocks the trade
   //   aligned_out    => true if a fresh sweep supports our direction
   //   strength_out   => that sweep's strength (0 if none)
   //===================================================================
   bool SweepGate(const IntelligencePacket &pkt, TRADE_DIR dir,
                  bool &aligned_out, double &strength_out)
   {
      aligned_out  = false;
      strength_out = 0.0;

      if(!Config.SweepGateOn) return true;         // gate disabled
      if(!pkt.liquidity.is_valid) return true;     // no data — don't block
      if(!pkt.liquidity.sweep_detected) return true; // no sweep — nothing to gate

      // Only consider FRESH sweeps
      if(pkt.liquidity.sweep_candles_ago > TS_SWEEP_FRESH_BARS) return true;

      TRADE_DIR sweep_dir = pkt.liquidity.sweep_direction;

      if(sweep_dir == dir)
      {
         // Sweep reversal supports our direction — good context
         aligned_out  = true;
         strength_out = pkt.liquidity.sweep_strength;
         return true;
      }

      if(sweep_dir != DIR_NONE && sweep_dir != dir)
      {
         // Fresh sweep points AGAINST us — this is the trap. Block.
         return false;
      }

      return true;
   }

   //===================================================================
   // BUILD + CACHE A REJECTION
   //===================================================================
   TradeDecision Reject(DECISION_REASON reason, TRADE_DIR dir, string detail)
   {
      TradeDecision d;
      ZeroMemory(d);
      d.valid          = false;
      d.reason         = reason;
      d.direction      = dir;
      d.trigger        = TRIG_NONE;
      d.trade_score    = 0;
      d.decided_at     = TimeCurrent();
      d.detail         = detail;

      if(reason >= 0 && reason < 9) m_reject_counts[reason]++;
      m_last_decision = d;
      return d;
   }

public:
   CTradeScorer() :
      m_symbol(""),
      m_initialized(false),
      m_eval_count(0),
      m_valid_count(0)
   {
      ArrayInitialize(m_reject_counts, 0);
      ZeroMemory(m_last_decision);
      m_last_decision.valid  = false;
      m_last_decision.reason = DEC_PACKET_INVALID;
   }

   bool Init(string symbol)
   {
      m_symbol = symbol;
      m_initialized = true;
      m_eval_count = 0;
      m_valid_count = 0;
      ArrayInitialize(m_reject_counts, 0);
      Logger.Info("TRADE_SCORER",
         StringFormat("Initialized. threshold=%d pullback_max=%.1f sweep_gate=%s",
                       Config.TradeScoreMin, Config.PullbackMaxPips,
                       Config.SweepGateOn ? "on" : "off"));
      return true;
   }

   //===================================================================
   // EVALUATE — the single entry point. Returns a TradeDecision by value.
   //===================================================================
   TradeDecision Evaluate(const IntelligencePacket &pkt)
   {
      m_eval_count++;

      //--- Gate 1: packet usable
      if(!pkt.is_valid || pkt.intel_status == INTEL_INITIALIZING)
         return Reject(DEC_PACKET_INVALID, DIR_NONE, "packet_invalid_or_initializing");

      //--- Gate 4 (early): persistence block
      if(PersistenceBlocked(pkt))
         return Reject(DEC_PERSIST_BLOCKED, DIR_NONE, "persistence_warmup_or_unknown");

      //--- Gate 3: direction consensus (trend veto)
      if(!pkt.direction_valid)
         return Reject(DEC_NO_DIRECTION, DIR_NONE, "regime_trend_disagree");

      TRADE_DIR dir = pkt.consensus_direction;
      if(dir == DIR_NONE)
         return Reject(DEC_NO_DIRECTION, DIR_NONE, "no_consensus_direction");

      //--- Gate 2: quality score threshold (+ transition penalty)
      int threshold = Config.TradeScoreMin;
      if(pkt.persistence.in_transition)
         threshold += TS_SCORE_TRANSITION_ADD;

      int score = pkt.quality.total;
      if(score < threshold)
         return Reject(DEC_SCORE_BELOW_MIN, dir,
            StringFormat("score_%d_below_%d", score, threshold));

      //--- Gate 5: volatility floor
      if(!VolatilityOK(pkt))
         return Reject(DEC_VOL_TOO_LOW, dir, "volatility_dead_range");

      //--- Gate 6: pullback-and-resume trigger
      double o, h, l, c;
      if(!GetLastM15(o, h, l, c))
         return Reject(DEC_NO_TRIGGER, dir, "m15_data_unavailable");

      double pullback_pips = 0.0;
      bool trigger_fired = PullbackResume(pkt, dir, o, h, l, c, pullback_pips);

      if(pullback_pips > Config.PullbackMaxPips)
         return Reject(DEC_PULLBACK_TOO_FAR, dir,
            StringFormat("pullback_%.1f_gt_%.1f", pullback_pips, Config.PullbackMaxPips));

      if(!trigger_fired)
         return Reject(DEC_NO_TRIGGER, dir, "pullback_resume_no_fire");

      //--- Gate 7: sweep gate
      bool sweep_aligned = false;
      double sweep_strength = 0.0;
      if(!SweepGate(pkt, dir, sweep_aligned, sweep_strength))
         return Reject(DEC_SWEEP_GATE, dir, "opposing_fresh_sweep");

      //--- ALL GATES PASSED — build the valid decision
      TradeDecision d;
      ZeroMemory(d);
      d.valid           = true;
      d.reason          = DEC_VALID;
      d.direction       = dir;
      d.trigger         = TRIG_PULLBACK_RESUME;
      d.trade_score     = score;
      d.threshold_used  = threshold;
      d.entry_ref_price = c;
      d.ema20_ref       = pkt.trend.ema20;
      d.pullback_pips   = pullback_pips;
      d.sweep_aligned   = sweep_aligned;
      d.sweep_strength  = sweep_strength;
      d.decided_at      = TimeCurrent();
      d.detail          = StringFormat(
         "VALID %s score=%d thr=%d pullback=%.1f sweep_aligned=%s",
         (dir == DIR_LONG ? "LONG" : "SHORT"),
         score, threshold, pullback_pips,
         sweep_aligned ? "yes" : "no");

      m_valid_count++;
      m_last_decision = d;

      Logger.Info("TRADE_SCORER", d.detail);
      return d;
   }

   //--- Accessors
   TradeDecision GetLastDecision() const { return m_last_decision; }
   bool   IsInitialized()  const { return m_initialized; }
   int    GetEvalCount()   const { return m_eval_count; }
   int    GetValidCount()  const { return m_valid_count; }

   void Shutdown()
   {
      Logger.Info("TRADE_SCORER",
         StringFormat("Shutdown. evals=%d valid=%d rejects[score=%d dir=%d trig=%d sweep=%d vol=%d]",
                       m_eval_count, m_valid_count,
                       m_reject_counts[DEC_SCORE_BELOW_MIN],
                       m_reject_counts[DEC_NO_DIRECTION],
                       m_reject_counts[DEC_NO_TRIGGER],
                       m_reject_counts[DEC_SWEEP_GATE],
                       m_reject_counts[DEC_VOL_TOO_LOW]));
      m_initialized = false;
   }
};

//--- Global singleton
CTradeScorer TradeScorer;

#endif // CTRADESCORER_MQH

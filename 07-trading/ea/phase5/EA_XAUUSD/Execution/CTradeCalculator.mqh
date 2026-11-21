//+------------------------------------------------------------------+
//| XAUUSD Institutional EA - Trade Calculator                        |
//| File: Execution/CTradeCalculator.mqh                              |
//| Purpose: Compute SL and TP price levels for a decision, and       |
//|          enforce the real-RR gate (RR after spread).              |
//| Phase: 5                                                          |
//|                                                                    |
//| SL: from VolatilityResult.recommended_stop_pips (already ATR x    |
//|     SLAtrMult, clamped [SLPipsMin, SLPipsMax] by the engine).     |
//|     Fallback to Config clamp if the packet value is unusable.     |
//| TP: at Config.TP2RR (2.0) times the SL distance (1:2 base case).  |
//|     TP1 partial + Marubozu trail are Phase 6, NOT here.           |
//|                                                                    |
//| REAL-RR GATE: after subtracting spread from the reward side,      |
//|   if RR < Config.RealRRMin (1.5) the trade is refused.            |
//|                                                                    |
//| All prices normalized to symbol digits. SL is MANDATORY — if it   |
//| cannot be set, the plan is invalid (never a naked position).      |
//|                                                                    |
//| BOUNDARIES: no sizing, no order placement. Pure price math.       |
//+------------------------------------------------------------------+
#ifndef CTRADECALCULATOR_MQH
#define CTRADECALCULATOR_MQH

#include "../Include/Defines.mqh"
#include "../Include/PriceUtils.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "../Intelligence/IntelligenceTypes.mqh"

class CTradeCalculator
{
private:
   string m_symbol;
   bool   m_initialized;

   //--- Resolve the SL distance in pips from the packet, with fallback
   double ResolveStopPips(const IntelligencePacket &pkt)
   {
      double sl = pkt.volatility.recommended_stop_pips;

      // Fallback if the engine value is unusable
      if(sl <= 0.0 || !pkt.volatility.is_valid)
      {
         // Use midpoint of the configured clamp as a safe default
         sl = (Config.SLPipsMin + Config.SLPipsMax) / 2.0;
         Logger.Warn("TRADE_CALC",
            StringFormat("recommended_stop_pips unusable — fallback SL=%.1f", sl));
      }

      // Enforce the clamp regardless (defense in depth)
      if(sl < Config.SLPipsMin) sl = Config.SLPipsMin;
      if(sl > Config.SLPipsMax) sl = Config.SLPipsMax;
      return sl;
   }

public:
   CTradeCalculator() : m_symbol(""), m_initialized(false) {}

   bool Init(string symbol)
   {
      m_symbol = symbol;
      m_initialized = true;
      Logger.Info("TRADE_CALC",
         StringFormat("Initialized. TP2RR=%.1f RealRRMin=%.2f SL_clamp=[%.0f,%.0f]",
                       Config.TP2RR, Config.RealRRMin,
                       Config.SLPipsMin, Config.SLPipsMax));
      return true;
   }

   //===================================================================
   // COMPUTE SL/TP into an OrderPlan (partially fills the plan).
   //
   // Fills: direction, entry_price, sl_price, tp_price, sl_pips,
   //        tp_pips, real_rr, spread_pips.
   // Does NOT fill: lot, risk_dollars (PositionSizer), ticket/fill.
   //
   // Returns false (and sets plan.result) if the real-RR gate fails
   // or SL cannot be established.
   //===================================================================
   bool BuildLevels(const IntelligencePacket &pkt, const TradeDecision &dec,
                    OrderPlan &plan)
   {
      if(!m_initialized)
      {
         Logger.Error("TRADE_CALC", "BuildLevels before Init");
         plan.result = EXEC_ERROR;
         return false;
      }

      plan.direction = dec.direction;

      //--- Current market prices
      double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
      double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
      if(ask <= 0 || bid <= 0)
      {
         Logger.Error("TRADE_CALC",
            StringFormat("Invalid market prices ask=%.5f bid=%.5f", ask, bid));
         plan.result = EXEC_ERROR;
         return false;
      }

      double spread_pips = PriceUtils.PriceToPips(ask - bid);
      plan.spread_pips = spread_pips;

      //--- Spread sanity gate
      if(spread_pips > Config.SpreadHardCap)
      {
         Logger.Warn("TRADE_CALC",
            StringFormat("Spread %.1f > cap %.1f — refusing",
                          spread_pips, Config.SpreadHardCap));
         plan.result = EXEC_REJECTED_SPREAD;
         return false;
      }

      //--- Entry price = the side we cross (market order)
      double entry = (dec.direction == DIR_LONG) ? ask : bid;
      plan.entry_price = PriceUtils.NormalizePrice(entry);

      //--- SL distance
      double sl_pips = ResolveStopPips(pkt);
      plan.sl_pips = sl_pips;
      double sl_dist = PriceUtils.PipsToPrice(sl_pips);

      //--- SL price on the correct side (MANDATORY)
      double sl_price;
      if(dec.direction == DIR_LONG)
         sl_price = entry - sl_dist;
      else
         sl_price = entry + sl_dist;
      plan.sl_price = PriceUtils.NormalizePrice(sl_price);

      if(plan.sl_price <= 0.0)
      {
         Logger.Error("TRADE_CALC", "SL price computed <= 0 — refusing (no naked position)");
         plan.result = EXEC_REJECTED_SL;
         return false;
      }

      //--- TP distance at TP2RR (1:2 base case)
      double tp_pips = sl_pips * Config.TP2RR;
      plan.tp_pips = tp_pips;
      double tp_dist = PriceUtils.PipsToPrice(tp_pips);

      double tp_price;
      if(dec.direction == DIR_LONG)
         tp_price = entry + tp_dist;
      else
         tp_price = entry - tp_dist;
      plan.tp_price = PriceUtils.NormalizePrice(tp_price);

      //--- REAL-RR GATE: subtract spread from the reward side.
      // Effective reward = tp_pips - spread; effective risk = sl_pips + spread
      // (spread hurts both entry and exit on a round trip; conservative).
      double eff_reward = tp_pips - spread_pips;
      double eff_risk   = sl_pips + spread_pips;
      double real_rr    = (eff_risk > 0) ? (eff_reward / eff_risk) : 0.0;
      plan.real_rr = real_rr;

      if(real_rr < Config.RealRRMin)
      {
         Logger.Info("TRADE_CALC",
            StringFormat("Real-RR %.2f < min %.2f (tp=%.1f sl=%.1f spread=%.1f) — refusing",
                          real_rr, Config.RealRRMin, tp_pips, sl_pips, spread_pips));
         plan.result = EXEC_REJECTED_RR;
         return false;
      }

      Logger.Debug("TRADE_CALC",
         StringFormat("Levels: %s entry=%.2f sl=%.2f(%.1fp) tp=%.2f(%.1fp) rr=%.2f spread=%.1f",
                       (dec.direction == DIR_LONG ? "LONG" : "SHORT"),
                       plan.entry_price, plan.sl_price, sl_pips,
                       plan.tp_price, tp_pips, real_rr, spread_pips));
      return true;
   }

   bool IsInitialized() const { return m_initialized; }

   void Shutdown()
   {
      Logger.Info("TRADE_CALC", "Shutdown");
      m_initialized = false;
   }
};

//--- Global singleton
CTradeCalculator TradeCalculator;

#endif // CTRADECALCULATOR_MQH

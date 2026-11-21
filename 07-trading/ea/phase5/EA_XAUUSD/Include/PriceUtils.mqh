
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Price Utilities                         |
//| File: Include/PriceUtils.mqh                                      |
//| Purpose: XAUUSD-specific pip/point math.                          |
//|           Centralised so conversion never diverges between modules.|
//| Phase: 1 — Core Framework                                         |
//+------------------------------------------------------------------+
#ifndef PRICEUTILS_MQH
#define PRICEUTILS_MQH
#include "Defines.mqh"

//===================================================================
// PSEUDO-CODE RATIONALE
//
// XAUUSD on MT5 has Digits = 2 (price quoted to 2 decimal places,
// e.g. 2345.67). 1 pip = 0.01 = 1 * _Point on a 2-digit symbol.
//
// This is DIFFERENT from Forex where:
//   - 5-digit EURUSD: 1 pip = 10 * _Point
//   - Gold CFD: 1 pip = 1 * _Point (since Digits=2)
//
// CRITICAL: Every module must use these helpers.
//   Never hardcode 0.01 or _Point throughout the code.
//   Broker point size must be read from symbol info at runtime.
//
// PipValue ($ per pip per 1.0 lot) is also calculated here.
//   For XAUUSD: 1 pip move on 1 lot = $1.00 (standard)
//   But always confirm from SymbolInfoDouble — broker-specific.
//===================================================================

//--- A320 (P0-1): one pip definition for the whole EA. The design's thresholds (SL 30-80 pips,
//    swings 150/60/25, ATR spike 40, M15 ATR 8-35) only fit 1 pip = $1.00 of gold price; the
//    backtest (research/ea_design_gold.py) uses the same reading. Old code used 1 pip = 1 point
//    ($0.01), which marked every bar a volatility spike and blocked every trade.
input double   inp_PipSizePrice    = 1.0;    // 1 pip in price units ($1.00 on XAUUSD)

class CPriceUtils
{
private:
   string   m_symbol;
   double   m_point;          // Smallest price increment
   int      m_digits;         // Decimal places in price
   double   m_pip_size;       // 1 pip = this many price units
   double   m_pip_value;      // $ per pip per 1.0 lot
   bool     m_initialized;

public:
   CPriceUtils() : m_initialized(false), m_point(0.01),
                   m_digits(2), m_pip_size(0.01), m_pip_value(1.0) {}

   bool Init(string symbol)
   {
      m_symbol = symbol;

      // Read actual values from broker
      m_point   = SymbolInfoDouble(symbol, SYMBOL_POINT);
      m_digits  = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

      // For XAUUSD Digits=2: pip = 1 point = 0.01
      // For XAUUSD Digits=3: pip = 1 point = 0.001 (some brokers)
      // We treat 1 pip = 1 point regardless — confirmed by digits check
      m_pip_size = inp_PipSizePrice;
      if(m_pip_size < m_point || m_pip_size > 10.0)
      {
         Print("[PRICEUTILS FATAL] inp_PipSizePrice=", m_pip_size, " outside [point, 10]");
         return false;
      }

      // Pip value = tick value × (pip_size / tick_size)
      double tick_value = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
      double tick_size  = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
      if(tick_size > 0)
         m_pip_value = tick_value * (m_pip_size / tick_size);
      else
         m_pip_value = 1.0; // Fallback: $1/pip/lot for XAUUSD

      // Validate this is actually XAUUSD
      if(symbol != "XAUUSD" && StringFind(symbol, "XAU") < 0 &&
         StringFind(symbol, "GOLD") < 0)
      {
         // Warn but allow — broker may use alternate name
         Print("[PRICEUTILS WARN] Symbol ", symbol, " may not be Gold");
      }

      if(m_point <= 0 || m_pip_value <= 0)
      {
         Print("[PRICEUTILS FATAL] Invalid symbol parameters — halting");
         return false;
      }

      m_initialized = true;
      return true;
   }

   //--- Convert pips to price distance
   double PipsToPrice(double pips) const
   {
      return pips * m_pip_size;
   }

   //--- Convert price distance to pips
   double PriceToPips(double price_distance) const
   {
      if(m_pip_size <= 0) return 0;
      return MathAbs(price_distance) / m_pip_size;
   }

   //--- Normalize price to symbol digits
   double NormalizePrice(double price) const
   {
      return NormalizeDouble(price, m_digits);
   }

   //--- Normalize lot to broker lot step
   double NormalizeLot(double lot) const
   {
      double step = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP);
      if(step <= 0) step = 0.01;
      lot = MathFloor(lot / step) * step;
      double min_lot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
      double max_lot = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MAX);
      lot = MathMax(lot, min_lot);
      lot = MathMin(lot, max_lot);
      return NormalizeDouble(lot, 2);
   }

   //--- Calculate dollar risk for given lot + SL pips
   double CalcRiskDollars(double lot, double sl_pips) const
   {
      return lot * sl_pips * m_pip_value;
   }

   //--- Calculate lot size for given risk dollars + SL pips
   double CalcLotFromRisk(double risk_dollars, double sl_pips) const
   {
      if(sl_pips <= 0 || m_pip_value <= 0) return 0;
      return risk_dollars / (sl_pips * m_pip_value);
   }

   //--- Get current spread in pips
   double GetSpreadPips() const
   {
      long spread_points = SymbolInfoInteger(m_symbol, SYMBOL_SPREAD);
      return PriceToPips((double)spread_points * m_point);
   }

   //--- Clamp lot to [min, hardcap]
   double ClampLot(double lot, double hard_cap) const
   {
      lot = NormalizeLot(lot);
      return MathMin(MathMax(lot, LOT_MINIMUM), hard_cap);
   }

   //--- Getters
   double PipSize()  const { return m_pip_size; }
   double PipValue() const { return m_pip_value; }
   double Point()    const { return m_point; }
   int    Digits()   const { return m_digits; }
   bool   IsReady()  const { return m_initialized; }
};

//--- Global singleton
CPriceUtils PriceUtils;

#endif // PRICEUTILS_MQH

//+------------------------------------------------------------------+
//| XAUUSD Institutional EA - Position Sizer                          |
//| File: Execution/CPositionSizer.mqh                                |
//| Purpose: Convert risk % + SL distance into a safe lot size.       |
//| Phase: 5                                                          |
//|                                                                    |
//| Wraps the PROVEN PriceUtils.CalcLotFromRisk + ClampLot rather     |
//| than reinventing the math. Adds the safety envelope:              |
//|   - Hard lot cap (Config.LotHardCap, e.g. 0.10)                   |
//|   - Equity floor check (never size when balance under floor)      |
//|   - Broker min/step normalization (via PriceUtils.NormalizeLot)   |
//|   - Sanity clamps (reject zero / absurd sizes)                    |
//|                                                                    |
//| Risk base: Config.RiskPct is a FRACTION (0.0075 for 0.75%).       |
//|   dollar_risk = account_equity * RiskPct                          |
//|   lot         = dollar_risk / (sl_pips * pip_value)               |
//|                                                                    |
//| BOUNDARIES: no order placement, no SL/TP calc (that's the         |
//|   TradeCalculator). Pure sizing.                                  |
//+------------------------------------------------------------------+
#ifndef CPOSITIONSIZER_MQH
#define CPOSITIONSIZER_MQH

#include "../Include/Defines.mqh"
#include "../Include/PriceUtils.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"

class CPositionSizer
{
private:
   bool   m_initialized;

public:
   CPositionSizer() : m_initialized(false) {}

   bool Init()
   {
      m_initialized = true;
      Logger.Info("POS_SIZER",
         StringFormat("Initialized. risk=%.4f (%.2f%%) lot_cap=%.2f equity_floor=%.2f",
                       Config.RiskPct, Config.RiskPct * 100.0,
                       Config.LotHardCap, Config.EquityFloor));
      return true;
   }

   //===================================================================
   // COMPUTE LOT SIZE
   //
   // Returns a broker-normalized, capped lot size, or 0.0 if sizing
   // must be refused (equity floor breach, invalid SL, absurd result).
   //
   //   sl_pips        : stop distance in pips (must be > 0)
   //   out_risk_dollars : the actual $ risk at the returned lot
   //===================================================================
   double ComputeLot(double sl_pips, double &out_risk_dollars)
   {
      out_risk_dollars = 0.0;

      if(!m_initialized)
      {
         Logger.Error("POS_SIZER", "ComputeLot before Init");
         return 0.0;
      }

      if(sl_pips <= 0.0)
      {
         Logger.Error("POS_SIZER",
            StringFormat("Invalid sl_pips=%.2f — refusing to size", sl_pips));
         return 0.0;
      }

      //--- Equity floor: never open a new trade below the floor
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      if(equity <= Config.EquityFloor)
      {
         Logger.Warn("POS_SIZER",
            StringFormat("Equity %.2f <= floor %.2f — refusing to size",
                          equity, Config.EquityFloor));
         return 0.0;
      }

      //--- Risk dollars from equity * risk fraction
      double dollar_risk = equity * Config.RiskPct;
      if(dollar_risk <= 0.0)
      {
         Logger.Error("POS_SIZER",
            StringFormat("Non-positive dollar_risk=%.2f", dollar_risk));
         return 0.0;
      }

      //--- Use PROVEN PriceUtils math
      double raw_lot = PriceUtils.CalcLotFromRisk(dollar_risk, sl_pips);
      if(raw_lot <= 0.0)
      {
         Logger.Error("POS_SIZER",
            StringFormat("CalcLotFromRisk returned %.4f (risk=%.2f sl=%.1f)",
                          raw_lot, dollar_risk, sl_pips));
         return 0.0;
      }

      //--- Clamp to hard cap + broker min/step
      double lot = PriceUtils.ClampLot(raw_lot, Config.LotHardCap);

      //--- Sanity: after clamps, must be positive and not above cap
      if(lot <= 0.0 || lot > Config.LotHardCap + 0.0000001)
      {
         Logger.Error("POS_SIZER",
            StringFormat("Lot %.4f outside sane range (cap=%.2f) — refusing",
                          lot, Config.LotHardCap));
         return 0.0;
      }

      //--- Report actual risk at the final (clamped) lot
      out_risk_dollars = PriceUtils.CalcRiskDollars(lot, sl_pips);

      Logger.Debug("POS_SIZER",
         StringFormat("lot=%.2f (raw=%.4f) sl_pips=%.1f dollar_risk=%.2f actual_risk=%.2f equity=%.2f",
                       lot, raw_lot, sl_pips, dollar_risk, out_risk_dollars, equity));

      return lot;
   }

   bool IsInitialized() const { return m_initialized; }

   void Shutdown()
   {
      Logger.Info("POS_SIZER", "Shutdown");
      m_initialized = false;
   }
};

//--- Global singleton
CPositionSizer PositionSizer;

#endif // CPOSITIONSIZER_MQH

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
#include "../Core/CDailyStats.mqh"    // A336: NewEntryBlocked()

input bool     inp_StreakSizing = true;   // A325: 1.5x risk after a win, 0.75x after a loss
input double   inp_MainWeight   = 0.5;    // A336: main EA risk weight (inp_RiskPct x weight; 0 = main strategy off; quant re-test scenario G)
double         g_last_trade_r   = 0.0;    // set by OnTradeTransaction when a trade closes (0 = none yet)

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
      if(equity <= FloorNow())
      {
         Logger.Warn("POS_SIZER",
            StringFormat("Equity %.2f <= floor %.2f — refusing to size",
                          equity, Config.EquityFloor));
         return 0.0;
      }

      //--- Risk dollars from equity * risk fraction
      double dollar_risk = equity * Config.RiskPct * MathMax(0.0, inp_MainWeight);   // A336 weight
      if(dollar_risk <= 0.0) { Logger.Info("POS_SIZER", "Main strategy weight is 0 - no entry"); return 0.0; }
      //--- A325 "take more like the winners": 1.5x after a winning trade, 0.75x after a loss
      //    (2y test: +0.164R -> +0.168R a trade, worst drop 6.5% -> 5.5%; later part +0.143 -> +0.153)
      dollar_risk *= StageRiskMult();                    // A335: small size while waiting for profitable days
      if(inp_StreakSizing && g_last_trade_r > 0.05)       dollar_risk *= 1.5;
      else if(inp_StreakSizing && g_last_trade_r < -0.05) dollar_risk *= 0.75;
      if(dollar_risk <= 0.0)
      {
         Logger.Error("POS_SIZER",
            StringFormat("Non-positive dollar_risk=%.2f", dollar_risk));
         return 0.0;
      }

      //--- A336 (#3): the spread is paid on entry, so it is part of the risk
      double eff_pips = sl_pips + PriceUtils.GetSpreadPips();

      //--- Use PROVEN PriceUtils math
      double raw_lot = PriceUtils.CalcLotFromRisk(dollar_risk, eff_pips);
      if(raw_lot <= 0.0)
      {
         Logger.Error("POS_SIZER",
            StringFormat("CalcLotFromRisk returned %.4f (risk=%.2f sl=%.1f)",
                          raw_lot, dollar_risk, eff_pips));
         return 0.0;
      }

      //--- A336 (#3): never round UP past the risk budget. Floor to the step; below the
      //    broker minimum, take the minimum only if its risk stays <= 1.5x target, else skip.
      double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
      double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
      if(step <= 0) step = 0.01;
      double lot = MathFloor(raw_lot / step + 1e-9) * step;
      if(lot < vmin)
      {
         if(PriceUtils.CalcRiskDollars(vmin, eff_pips) <= 1.5 * dollar_risk) lot = vmin;
         else
         {
            Logger.Info("POS_SIZER",
               StringFormat("Skip: min lot %.2f risks %.2f > 1.5x target %.2f",
                            vmin, PriceUtils.CalcRiskDollars(vmin, eff_pips), dollar_risk));
            return 0.0;
         }
      }
      lot = MathMin(lot, Config.LotHardCap);                 // hard cap (always rounds DOWN)
      if(vmax > 0) lot = MathMin(lot, vmax);
      lot = NormalizeDouble(MathFloor(lot / step + 1e-9) * step, 2);

      //--- Sanity: after clamps, must be positive and not above cap
      if(lot <= 0.0 || lot < vmin || lot > Config.LotHardCap + 0.0000001)
      {
         Logger.Error("POS_SIZER",
            StringFormat("Lot %.4f outside sane range (cap=%.2f) — refusing",
                          lot, Config.LotHardCap));
         return 0.0;
      }

      //--- Report actual risk at the final lot (spread included)
      out_risk_dollars = PriceUtils.CalcRiskDollars(lot, eff_pips);

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

//+------------------------------------------------------------------+
//| A336: order checks shared by the main entry and the mix engine     |
//+------------------------------------------------------------------+

//--- (#11 / G10) count our open positions + pendings, and whether any is on the other side
void OurBook(int &count, bool &has_long, bool &has_short)
{
   count = 0; has_long = false; has_short = false;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(!IsOurMagic(PositionGetInteger(POSITION_MAGIC))) continue;
      count++;
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) has_long = true; else has_short = true;
   }
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      if(!IsOurMagic(OrderGetInteger(ORDER_MAGIC))) continue;
      count++;
      long ot = OrderGetInteger(ORDER_TYPE);
      if(ot == ORDER_TYPE_BUY_LIMIT || ot == ORDER_TYPE_BUY_STOP || ot == ORDER_TYPE_BUY_STOP_LIMIT) has_long = true;
      else has_short = true;
   }
}

//--- (#2, #10, #9) conditions that block EVERY new entry, main and mix
bool NewEntryBlocked(string &why)
{
   why = "";
   if(!Config.AccountSizeOk)
   {
      //--- Review fix: Init may have read balance 0 (account not loaded yet) -> re-check live
      double b = AccountInfoDouble(ACCOUNT_BALANCE);
      if(b > 0.0 && (inp_Stage == STAGE_FUNDED || MathAbs(b - inp_AccountSize) / inp_AccountSize <= 0.15))
         Config.AccountSizeOk = true;
      else { why = "account_size_mismatch"; return true; }
   }
   if(WeekendCutActive())     { why = "friday_cut_weekend";    return true; }
   if(DailyStats.IsDailyLimitHit()) { why = "daily_limit";     return true; }
   return false;
}

//--- (#11, #15 / G10, G11) final check right before any order is sent.
//    side +1 long / -1 short; price = intended entry price.
bool OrderAllowed(int side, double lot, double price, string &why)
{
   why = "";
   if(NewEntryBlocked(why)) return false;
   int n = 0; bool hl = false, hs = false;
   OurBook(n, hl, hs);
   if(inp_MaxOpenPositions > 0 && n >= inp_MaxOpenPositions)  { why = StringFormat("max_open_positions %d", n); return false; }
   if(!inp_AllowOpposite && ((side > 0 && hs) || (side < 0 && hl))) { why = "opposite_position_open"; return false; }

   //--- margin: broker figure, and never less than notional / inp_MetalLeverage (The5%ers 1:25, E8 Pro 1:15)
   double margin = 0.0;
   ENUM_ORDER_TYPE ot = (side > 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!OrderCalcMargin(ot, _Symbol, lot, price, margin) || margin <= 0)
   {
      why = StringFormat("OrderCalcMargin failed err=%d", GetLastError());
      return false;
   }
   double contract = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
   double m25 = (contract > 0) ? lot * contract * price / inp_MetalLeverage : 0.0;
   margin = MathMax(margin, m25);
   //--- audit 27 Nov: our resting limit orders take margin only when they fill. Several of them can
   //    fill in one fast move, so count their 1:inp_MetalLeverage margin as already used.
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t == 0 || OrderGetString(ORDER_SYMBOL) != _Symbol || !IsOurMagic(OrderGetInteger(ORDER_MAGIC))) continue;
      if(contract > 0) margin += OrderGetDouble(ORDER_VOLUME_CURRENT) * contract * OrderGetDouble(ORDER_PRICE_OPEN) / inp_MetalLeverage;
   }
   double free_m = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(margin > 0.5 * free_m)
   {
      why = StringFormat("margin %.2f > 50%% of free margin %.2f", margin, free_m);
      return false;
   }
   return true;
}

#endif // CPOSITIONSIZER_MQH

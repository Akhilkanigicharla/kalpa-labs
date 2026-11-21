//+------------------------------------------------------------------+
//| XAUUSD Institutional EA - Entry Engine                            |
//| File: Execution/CEntryEngine.mqh                                  |
//| Purpose: Place the market order for a validated OrderPlan.        |
//| Phase: 5                                                          |
//|                                                                    |
//| USES CTrade (MQL5 standard library) — handles filling modes and   |
//| most broker quirks. Market orders only (per design).              |
//|                                                                    |
//| SAFETY MECHANICS (this is the money-touching file):               |
//|   - DryRun mode: logs the full intended order, does NOT send.     |
//|   - One-position rule: checks existing position on symbol+magic   |
//|     BEFORE and AFTER send (idempotency vs network hiccups).       |
//|   - SL is MANDATORY: never sends without a stop.                  |
//|   - Max EXEC_MAX_RETRIES (2) on requote/rejection, fresh price    |
//|     each attempt, then abort.                                     |
//|   - Slippage guard: fill worse than Config.SlippageMax logged.    |
//|   - Every order tagged with Config.MagicNumber.                   |
//|                                                                    |
//| BOUNDARIES: no sizing (PositionSizer), no SL/TP calc              |
//|   (TradeCalculator), no trade management (Phase 6).               |
//+------------------------------------------------------------------+
#ifndef CENTRYENGINE_MQH
#define CENTRYENGINE_MQH

#include <Trade/Trade.mqh>
#include "../Include/Defines.mqh"
#include "../Include/PriceUtils.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"

class CEntryEngine
{
private:
   string   m_symbol;
   bool     m_initialized;
   CTrade   m_trade;

   int      m_orders_placed;
   int      m_orders_dryrun;
   int      m_orders_failed;

   //===================================================================
   // ONE-POSITION CHECK — is there already a position on this
   // symbol with our magic number?
   //===================================================================
   bool HasOpenPosition()
   {
      int total = PositionsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0) continue;
         if(!PositionSelectByTicket(ticket)) continue;
         string psym = PositionGetString(POSITION_SYMBOL);
         long   pmagic = PositionGetInteger(POSITION_MAGIC);
         if(psym == m_symbol && pmagic == Config.MagicNumber)
            return true;
      }
      return false;
   }

   //===================================================================
   // FIND our position ticket (after a send, to confirm fill)
   //===================================================================
   ulong FindOurPositionTicket()
   {
      int total = PositionsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0) continue;
         if(!PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL) == m_symbol &&
            PositionGetInteger(POSITION_MAGIC) == Config.MagicNumber)
            return ticket;
      }
      return 0;
   }

   //===================================================================
   // LOG THE INTENDED ORDER (used by DryRun and before every live send)
   //===================================================================
   void LogIntendedOrder(const OrderPlan &plan, string mode)
   {
      Logger.Info("ENTRY_ENGINE",
         StringFormat("[%s] %s %.2f lots @ %.2f | SL %.2f (%.1fp) | TP %.2f (%.1fp) | RR %.2f | spread %.1fp | risk $%.2f",
                       mode,
                       (plan.direction == DIR_LONG ? "BUY" : "SELL"),
                       plan.lot, plan.entry_price,
                       plan.sl_price, plan.sl_pips,
                       plan.tp_price, plan.tp_pips,
                       plan.real_rr, plan.spread_pips,
                       plan.risk_dollars));
   }

public:
   CEntryEngine() :
      m_symbol(""),
      m_initialized(false),
      m_orders_placed(0),
      m_orders_dryrun(0),
      m_orders_failed(0)
   {}

   bool Init(string symbol)
   {
      m_symbol = symbol;

      m_trade.SetExpertMagicNumber(Config.MagicNumber);
      m_trade.SetTypeFillingBySymbol(symbol);   // pick a valid filling mode
      m_trade.SetDeviationInPoints((ulong)MathMax(1.0, MathRound(Config.PipsToPoints(Config.SlippageMax)))); // A320
      m_trade.LogLevel(0);                       // we do our own logging

      m_initialized = true;
      Logger.Info("ENTRY_ENGINE",
         StringFormat("Initialized. magic=%I64d dry_run=%s slippage_max=%.1fp",
                       Config.MagicNumber,
                       Config.DryRun ? "ON" : "OFF",
                       Config.SlippageMax));
      if(Config.DryRun)
         Logger.Warn("ENTRY_ENGINE",
            "DRY-RUN ACTIVE — orders will be logged but NOT sent. "
            "Flip inp_DryRun=false to trade live.");
      return true;
   }

   //===================================================================
   // EXECUTE a validated + sized OrderPlan.
   //
   // Preconditions (asserted): plan.valid, plan.lot > 0, plan.sl_price
   // set. Returns the plan with .result and (live) fill fields set.
   //===================================================================
   OrderPlan Execute(OrderPlan &plan)
   {
      if(!m_initialized)
      {
         Logger.Error("ENTRY_ENGINE", "Execute before Init");
         plan.result = EXEC_ERROR;
         return plan;
      }

      //--- Mandatory SL check (never a naked position)
      if(plan.sl_price <= 0.0)
      {
         Logger.Error("ENTRY_ENGINE", "No SL on plan — refusing (no naked position)");
         plan.result = EXEC_REJECTED_SL;
         m_orders_failed++;
         return plan;
      }

      //--- Lot sanity
      if(plan.lot <= 0.0)
      {
         Logger.Error("ENTRY_ENGINE",
            StringFormat("Invalid lot %.2f — refusing", plan.lot));
         plan.result = EXEC_REJECTED_SIZING;
         m_orders_failed++;
         return plan;
      }

      //--- ONE-POSITION RULE (before send)
      if(HasOpenPosition())
      {
         Logger.Warn("ENTRY_ENGINE",
            "Position already open on symbol+magic — refusing (one-position rule)");
         plan.result = EXEC_REJECTED_EXISTING;
         return plan;
      }

      //--- A336 (#2, #10, #11, #15): weekend cut, account-size check, max positions,
      //    no opposite positions, margin (1:25 metals) - same checks as the mix engine
      {
         int    side0 = (plan.direction == DIR_LONG) ? 1 : -1;
         double px0   = (side0 > 0) ? SymbolInfoDouble(m_symbol, SYMBOL_ASK) : SymbolInfoDouble(m_symbol, SYMBOL_BID);
         string why0;
         if(!OrderAllowed(side0, plan.lot, px0, why0))
         {
            Logger.Info("ENTRY_ENGINE", "Order refused by live-safety checks: " + why0);
            plan.result = EXEC_REJECTED_EXISTING;
            return plan;
         }
      }

      //--- DRY RUN: log + stop, no send
      if(Config.DryRun)
      {
         LogIntendedOrder(plan, "DRY-RUN");
         plan.result = EXEC_DRYRUN;
         plan.ticket = 0;
         m_orders_dryrun++;
         return plan;
      }

      //--- LIVE: log intent, then attempt send with retries
      LogIntendedOrder(plan, "LIVE");

      bool sent = false;
      int  side = (plan.direction == DIR_LONG) ? 1 : -1;
      double tp_dist = (plan.tp_price > 0 && plan.entry_price > 0) ? MathAbs(plan.tp_price - plan.entry_price) : 0.0;
      for(int attempt = 1; attempt <= EXEC_MAX_RETRIES + 1; attempt++)
      {
         //--- A320: a "failed" send can still have filled (timeout) — never open a duplicate
         if(attempt > 1 && HasOpenPosition())
         {
            Logger.Warn("ENTRY_ENGINE", "Position appeared after a failed attempt — not resending");
            sent = true;
            break;
         }
         //--- Refresh price each attempt (market moved)
         double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
         double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
         double price = (plan.direction == DIR_LONG) ? ask : bid;
         price = PriceUtils.NormalizePrice(price);
         //--- A336 (#13): on a retry the price moved - rebuild SL/TP from the NEW price so the
         //    risk stays what was sized (sl_pips), instead of reusing the old SL
         if(attempt > 1)
         {
            plan.sl_price = PriceUtils.NormalizePrice(price - side * PriceUtils.PipsToPrice(plan.sl_pips));
            if(tp_dist > 0) plan.tp_price = PriceUtils.NormalizePrice(price + side * tp_dist);
         }

         bool ok;
         if(plan.direction == DIR_LONG)
            ok = m_trade.Buy(plan.lot, m_symbol, price, plan.sl_price, plan.tp_price,
                             "XAUUSD_EA");
         else
            ok = m_trade.Sell(plan.lot, m_symbol, price, plan.sl_price, plan.tp_price,
                              "XAUUSD_EA");

         uint retcode = m_trade.ResultRetcode();

         if(ok && (retcode == TRADE_RETCODE_DONE ||
                   retcode == TRADE_RETCODE_DONE_PARTIAL ||
                   retcode == TRADE_RETCODE_PLACED))
         {
            sent = true;
            Logger.Info("ENTRY_ENGINE",
               StringFormat("Order sent OK on attempt %d. retcode=%d deal=%I64u",
                             attempt, retcode, m_trade.ResultDeal()));
            break;
         }

         Logger.Warn("ENTRY_ENGINE",
            StringFormat("Send attempt %d failed. retcode=%d (%s)",
                          attempt, retcode, m_trade.ResultRetcodeDescription()));

         //--- A336 (#13): a timeout / no reply may already be FILLED on the server. Poll up to
         //    3 s for the position and never resend.
         if(retcode == TRADE_RETCODE_TIMEOUT || retcode == TRADE_RETCODE_CONNECTION || retcode == 0)
         {
            for(int w = 0; w < 10 && !HasOpenPosition(); w++) Sleep(300);
            if(HasOpenPosition()) { sent = true; Logger.Warn("ENTRY_ENGINE", "Order filled despite timeout - not resending"); }
            break;
         }
         //--- Retry ONLY on price-kind rejections
         if(retcode != TRADE_RETCODE_REQUOTE && retcode != TRADE_RETCODE_PRICE_CHANGED &&
            retcode != TRADE_RETCODE_PRICE_OFF)
            break;

         if(attempt <= EXEC_MAX_RETRIES)
            Sleep(EXEC_RETRY_WAIT_MS);
      }

      if(!sent)
      {
         Logger.Error("ENTRY_ENGINE",
            StringFormat("All %d attempts failed — aborting order", EXEC_MAX_RETRIES + 1));
         plan.result = EXEC_SEND_FAILED;
         m_orders_failed++;
         return plan;
      }

      //--- CONFIRM FILL (one-position check AFTER send = idempotency)
      ulong ticket = FindOurPositionTicket();
      if(ticket == 0)
      {
         // Sent OK but no position found — log loudly, treat as error
         Logger.Error("ENTRY_ENGINE",
            "Send reported success but no position found — MANUAL CHECK NEEDED");
         plan.result = EXEC_ERROR;
         m_orders_failed++;
         return plan;
      }

      plan.ticket = ticket;

      //--- Slippage check
      if(PositionSelectByTicket(ticket))
      {
         double fill = PositionGetDouble(POSITION_PRICE_OPEN);
         plan.fill_price = fill;
         double slip_pips = PriceUtils.PriceToPips(MathAbs(fill - plan.entry_price));
         plan.slippage_pips = slip_pips;

         if(slip_pips > Config.SlippageMax)
            Logger.Warn("ENTRY_ENGINE",
               StringFormat("Slippage %.1fp > max %.1fp (intended %.2f, fill %.2f)",
                             slip_pips, Config.SlippageMax, plan.entry_price, fill));
         else
            Logger.Info("ENTRY_ENGINE",
               StringFormat("Fill confirmed. ticket=%I64u fill=%.2f slippage=%.1fp",
                             ticket, fill, slip_pips));
      }

      plan.result = EXEC_PLACED;
      m_orders_placed++;
      return plan;
   }

   bool IsInitialized() const { return m_initialized; }
   int  GetOrdersPlaced() const { return m_orders_placed; }
   int  GetOrdersDryRun() const { return m_orders_dryrun; }
   int  GetOrdersFailed() const { return m_orders_failed; }

   void Shutdown()
   {
      Logger.Info("ENTRY_ENGINE",
         StringFormat("Shutdown. placed=%d dryrun=%d failed=%d",
                       m_orders_placed, m_orders_dryrun, m_orders_failed));
      m_initialized = false;
   }
};

//--- Global singleton
CEntryEngine EntryEngine;

#endif // CENTRYENGINE_MQH

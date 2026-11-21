
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Daily Drawdown Guard                    |
//| File: Guards/CDailyDrawdownGuard.mqh                              |
//| Purpose: Self-imposed daily loss limit, trade count cap,          |
//|           consecutive loss pause. Delegates data to CDailyStats.  |
//| Phase: 2 — Guard Layer / Step 5                                   |
//|                                                                    |
//| GUARD SLOT: 4                                                      |
//| KEY DESIGN: This guard is STATELESS by itself — all state lives   |
//|   in CDailyStats. This guard only reads and decides.              |
//|   Separation: CDailyStats tracks, CDailyDrawdownGuard enforces.   |
//+------------------------------------------------------------------+
#ifndef CDAILYDRAWDOWNGUARD_MQH
#define CDAILYDRAWDOWNGUARD_MQH

#include "../Include/Defines.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "../Core/CDailyStats.mqh"
#include "../Core/CStateManager.mqh"  // Required for CheckResume StateManager access
#include "GuardTypes.mqh"

class CDailyDrawdownGuard : public IGuard
{
private:
   //--- Last logged state (to prevent log spam on every tick)
   bool  m_daily_limit_logged;
   bool  m_max_trades_logged;
   bool  m_consec_pause_logged;
   bool  m_cooldown_logged;

public:
   CDailyDrawdownGuard() :
      m_daily_limit_logged(false),
      m_max_trades_logged(false),
      m_consec_pause_logged(false),
      m_cooldown_logged(false)
   {
      m_meta.index       = 4;
      m_meta.priority    = GPRIO_DAILY_DRAWDOWN;
      m_meta.name        = "DAILY_DD";
      m_meta.description = "Daily self-imposed drawdown and trade limits";
      m_meta.enabled     = true;
   }

   virtual bool Init() override
   {
      m_meta.initialized = true;
      m_initialized      = true;
      Logger.Info("DAILY_DD",
         StringFormat("Initialized. daily_limit=%.2f max_trades=%d "
                      "consec_loss_limit=%d cooldown=%ds",
                      Config.DailyLossLimit,
                      Config.MaxDailyTrades,
                      CONSEC_LOSS_LIMIT,
                      TRADE_COOLDOWN_SEC));
      return true;
   }

   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();

      //--- [D1] Daily loss limit
      if(DailyStats.IsDailyLimitHit())
      {
         if(!m_daily_limit_logged)
         {
            m_daily_limit_logged = true;
            Logger.Warn("DAILY_DD",
               StringFormat("Daily loss limit hit: pnl=%.2f limit=%.2f",
                            DailyStats.GetClosedPnL(),
                            -Config.DailyLossLimit));
         }
         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_DAILY_DRAWDOWN, m_meta.name, m_meta.index,
                             SUSPEND_DAILY_LIMIT,
                             StringFormat("Daily P&L %.2f <= -%.2f limit",
                                          DailyStats.GetClosedPnL(),
                                          Config.DailyLossLimit),
                             "Resets at 00:00 server time");
      }

      //--- [D2] Max daily trades
      if(DailyStats.IsMaxTradesHit())
      {
         if(!m_max_trades_logged)
         {
            m_max_trades_logged = true;
            Logger.Info("DAILY_DD",
               StringFormat("Max daily trades reached: %d/%d",
                            DailyStats.GetTradeCount(),
                            Config.MaxDailyTrades));
         }
         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_DAILY_DRAWDOWN, m_meta.name, m_meta.index,
                             SUSPEND_MAX_TRADES,
                             StringFormat("Trades today=%d max=%d",
                                          DailyStats.GetTradeCount(),
                                          Config.MaxDailyTrades),
                             "Resets at 00:00 server time");
      }

      //--- [D3] Consecutive loss pause (1-hour)
      if(DailyStats.IsConsecLossPaused())
      {
         if(!m_consec_pause_logged)
         {
            m_consec_pause_logged = true;
            Logger.Warn("DAILY_DD",
               StringFormat("Consecutive loss pause active: "
                            "streak=%d limit=%d — 1hr pause",
                            DailyStats.GetConsecLosses(),
                            CONSEC_LOSS_LIMIT));
         }
         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_DAILY_DRAWDOWN, m_meta.name, m_meta.index,
                             SUSPEND_CONSEC_LOSSES,
                             StringFormat("%d consecutive losses — cooling down",
                                          DailyStats.GetConsecLosses()),
                             "Resumes after 1-hour pause");
      }

      //--- [D4] Post-trade cooldown (15 min — returns BLOCK not SUSPEND)
      if(DailyStats.IsCooldownActive())
      {
         int remaining = TRADE_COOLDOWN_SEC -
            (int)(TimeCurrent() - DailyStats.GetLastClose());
         remaining = MathMax(0, remaining);

         if(!m_cooldown_logged)
         {
            m_cooldown_logged = true;
            Logger.Debug("DAILY_DD",
               StringFormat("Post-trade cooldown active: %ds remaining",
                            remaining));
         }
         RecordTrigger(GUARD_BLOCK);
         return GuardBlock(GPRIO_DAILY_DRAWDOWN, m_meta.name, m_meta.index,
                           StringFormat("Post-trade cooldown: %ds remaining",
                                        remaining),
                           "Clears automatically after cooldown expires");
      }

      // All checks passed — reset log suppression for next trigger
      m_daily_limit_logged  = false;
      m_max_trades_logged   = false;
      m_consec_pause_logged = false;
      m_cooldown_logged     = false;

      return GuardPass(GPRIO_DAILY_DRAWDOWN, m_meta.name, m_meta.index);
   }

   virtual bool CheckResume(const GuardContext &ctx) override
   {
      SUSPEND_REASON reason = StateManager.GetSuspendReason();

      switch(reason)
      {
         case SUSPEND_DAILY_LIMIT:
         case SUSPEND_MAX_TRADES:
            // Resumes at day rollover (CDailyStats.CheckDayRollover resets flags)
            return (!DailyStats.IsDailyLimitHit() && !DailyStats.IsMaxTradesHit());

         case SUSPEND_CONSEC_LOSSES:
            return (!DailyStats.IsConsecLossPaused());

         default:
            return false;
      }
   }
};

#endif // CDAILYDRAWDOWNGUARD_MQH

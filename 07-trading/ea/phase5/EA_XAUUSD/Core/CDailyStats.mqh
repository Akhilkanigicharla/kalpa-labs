
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Daily Statistics Tracker               |
//| File: Core/CDailyStats.mqh                                        |
//| Purpose: Tracks all per-day metrics. Resets at 00:01 GMT daily.  |
//|           Source of truth for daily trade count, P&L, DD.        |
//| Phase: 1 — Core Framework                                         |
//+------------------------------------------------------------------+
#ifndef CDAILYSTATS_MQH
#define CDAILYSTATS_MQH
#include "../Include/Defines.mqh"
#include "CLogger.mqh"
#include "CPersistence.mqh"

//===================================================================
// PSEUDO-CODE DESIGN
//
// DailyStats resets at 00:01 GMT every calendar day.
// The "day" boundary is GMT-based — not broker server time.
// This matters because The5%ers uses GMT for their rules.
//
// Profitable day counter:
//   A day is "profitable" if closed_pnl > 0 when day ends.
//   Counter is cumulative (never decrements).
//   Displayed on dashboard — tracks progress to 3-day minimum.
//
// The CDailyStats class:
//   - Loads from disk on init (handles EA restart mid-day)
//   - Writes to disk after every trade close
//   - Provides query interface for guard layer
//   - Raises event when daily limits are hit
//===================================================================

class CDailyStats
{
private:
   DailyStatsData  m_stats;
   int         m_profitable_days;   // Cumulative — never reset
   bool        m_initialized;
   bool        m_daily_limit_hit;
   bool        m_max_trades_hit;
   datetime    m_last_reset_check;

   //--- Get current GMT date as midnight timestamp
   datetime TodayGMT() const
   {
      MqlDateTime dt;
      TimeToStruct(TimeGMT(), dt);
      dt.hour = 0; dt.min = 0; dt.sec = 0;
      return StructToTime(dt);
   }

   void ResetForNewDay()
   {
      // Before resetting, check if yesterday was profitable
      if(m_stats.closed_pnl > 0 && m_stats.trade_count > 0)
      {
         m_profitable_days++;
         Logger.Info("STATS",
            StringFormat("Profitable day confirmed — total profitable days: %d",
                         m_profitable_days));
      }

      double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);

      m_stats.reset_date      = TodayGMT();
      m_stats.open_equity     = current_equity;
      m_stats.closed_pnl      = 0.0;
      m_stats.peak_equity     = current_equity;
      m_stats.min_equity      = current_equity;
      m_stats.trade_count     = 0;
      m_stats.wins            = 0;
      m_stats.losses          = 0;
      m_stats.consec_losses   = 0;
      m_stats.last_close_time = 0;

      m_daily_limit_hit = false;
      m_max_trades_hit  = false;

      Persistence.WriteDaily(m_stats);

      Logger.Info("STATS", "Daily stats reset for new GMT day",
         StringFormat("date=%s open_equity=%.2f",
                      TimeToString(m_stats.reset_date, TIME_DATE),
                      m_stats.open_equity));
   }

public:
   CDailyStats() :
      m_profitable_days(0),
      m_initialized(false),
      m_daily_limit_hit(false),
      m_max_trades_hit(false),
      m_last_reset_check(0)
   {
      ZeroMemory(m_stats);
   }

   bool Init()
   {
      // Try to load from disk first (handles EA restart mid-day)
      if(!Persistence.ReadDaily(m_stats))
      {
         // No valid file for today — start fresh
         ResetForNewDay();
      }
      else
      {
         // Restore flags from loaded stats
         m_daily_limit_hit = (m_stats.closed_pnl <= -(Config.DailyLossLimit));
         m_max_trades_hit  = (m_stats.trade_count >= Config.MaxDailyTrades);
      }

      m_last_reset_check = TimeCurrent();
      m_initialized = true;

      Logger.Info("STATS", "Daily stats initialized",
         StringFormat("trades=%d pnl=%.2f limit_hit=%d max_hit=%d",
                      m_stats.trade_count,
                      m_stats.closed_pnl,
                      (int)m_daily_limit_hit,
                      (int)m_max_trades_hit));
      return true;
   }

   //--- Check for day rollover — call from OnTimer or OnTick
   void CheckDayRollover()
   {
      // Don't check more than once per minute
      if(TimeCurrent() - m_last_reset_check < 60) return;
      m_last_reset_check = TimeCurrent();

      datetime today = TodayGMT();
      if(today > m_stats.reset_date)
         ResetForNewDay();
   }

   //--- Record a trade open
   void OnTradeOpen()
   {
      m_stats.trade_count++;
      if(m_stats.trade_count >= Config.MaxDailyTrades)
      {
         m_max_trades_hit = true;
         Logger.Info("STATS",
            StringFormat("Max daily trades reached: %d", m_stats.trade_count));
      }
      Persistence.WriteDaily(m_stats);
   }

   //--- Record a trade close
   void OnTradeClose(double pnl, double rr_achieved)
   {
      m_stats.closed_pnl    += pnl;
      m_stats.last_close_time = TimeCurrent();

      if(pnl > 0)
      {
         m_stats.wins++;
         m_stats.consec_losses = 0; // Reset streak on win
      }
      else
      {
         m_stats.losses++;
         m_stats.consec_losses++;
      }

      // Check daily loss limit
      if(m_stats.closed_pnl <= -(Config.DailyLossLimit) && !m_daily_limit_hit)
      {
         m_daily_limit_hit = true;
         Logger.Warn("STATS", "Daily loss limit reached",
            StringFormat("closed_pnl=%.2f limit=%.2f",
                         m_stats.closed_pnl, Config.DailyLossLimit));
      }

      Persistence.WriteDaily(m_stats);

      Logger.Info("STATS", "Trade close recorded",
         StringFormat("pnl=%.2f rr=%.2f day_pnl=%.2f "
                      "trades=%d wins=%d losses=%d consec_loss=%d",
                      pnl, rr_achieved, m_stats.closed_pnl,
                      m_stats.trade_count, m_stats.wins,
                      m_stats.losses, m_stats.consec_losses));
   }

   //--- Update equity tracking (call every tick when equity changes)
   void UpdateEquity(double current_equity)
   {
      if(current_equity > m_stats.peak_equity)
         m_stats.peak_equity = current_equity;
      if(current_equity < m_stats.min_equity)
         m_stats.min_equity = current_equity;
   }

   //--- Query methods (used by guards)
   bool IsDailyLimitHit()   const { return m_daily_limit_hit; }
   bool IsMaxTradesHit()    const { return m_max_trades_hit; }
   int  GetTradeCount()     const { return m_stats.trade_count; }
   int  GetConsecLosses()   const { return m_stats.consec_losses; }
   double GetClosedPnL()    const { return m_stats.closed_pnl; }
   double GetOpenEquity()   const { return m_stats.open_equity; }
   int  GetProfitableDays() const { return m_profitable_days; }
   datetime GetLastClose()  const { return m_stats.last_close_time; }

   //--- Cooldown check: enough time since last trade closed?
   bool IsCooldownActive() const
   {
      if(m_stats.last_close_time == 0) return false;
      return (TimeCurrent() - m_stats.last_close_time) < TRADE_COOLDOWN_SEC;
   }

   //--- Consecutive loss pause check
   bool IsConsecLossPaused() const
   {
      if(m_stats.consec_losses < Config.MaxDailyTrades) return false;
      // Check if pause has expired
      if(m_stats.last_close_time == 0) return false;
      datetime pause_end = m_stats.last_close_time + CONSEC_LOSS_PAUSE_SEC;
      return (TimeCurrent() < pause_end);
   }

   //--- Manual reset (for testing only — logs clearly)
   void ForceReset(string reason)
   {
      Logger.Warn("STATS",
         StringFormat("FORCED RESET — reason: %s", reason));
      ResetForNewDay();
   }

   bool IsReady() const { return m_initialized; }
};

//--- Global singleton
CDailyStats DailyStats;

#endif // CDAILYSTATS_MQH

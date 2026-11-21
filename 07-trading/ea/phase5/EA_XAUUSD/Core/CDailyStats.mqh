
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Daily Statistics Tracker               |
//| File: Core/CDailyStats.mqh                                        |
//| Purpose: Tracks all per-day metrics. Resets at 00:00 SERVER time.|
//|           Source of truth for daily trade count, P&L, DD.        |
//| Phase: 1 — Core Framework                                         |
//+------------------------------------------------------------------+
#ifndef CDAILYSTATS_MQH
#define CDAILYSTATS_MQH
#include "../Include/Defines.mqh"
#include "CLogger.mqh"
#include "CPersistence.mqh"
#include "CConfig.mqh"          // review fix: uses Config, inp_*, IsOurMagic

//===================================================================
// DESIGN (A336)
//
// The day is the broker SERVER day (The5%ers: daily loss recalculated at
// 00:00 server time, GMT+2 winter / GMT+3 summer).
//
// Day base = MathMax(balance, equity) snapped at the server-day change.
// The rollover is checked on every tick and every second from OnTimer.
// The EA's daily stop (Config.DailyStopPct, default 4%) is measured from it.
//
// Restart safety: the base, the forced daily-stop flag and the day's start
// balance are saved. On init the start balance is rebuilt from deal history
// (balance - today's closed P&L) and the base is never lowered below it.
//
// Profitable day (official): min(midnight balance, midnight equity) -
// previous day's end balance >= inp_ProfitDayPct % of inp_AccountSize.
// A snapshot per closed day is written at rollover. Days before the EA
// first recorded a snapshot fall back to the closed-P&L method (logged).
//===================================================================

class CDailyStats
{
private:
   DailyStatsData  m_stats;
   bool        m_initialized;
   bool        m_daily_limit_hit;
   bool        m_max_trades_hit;

   //--- A336 (#13) profitable-day snapshots
   datetime    m_snap_day[];
   double      m_snap_sb[];
   double      m_snap_eb[];
   double      m_snap_ee[];
   int         m_snap_n;
   int         m_hist_days;          // closed-P&L fallback count for days before the first snapshot
   int         m_snap_days;          // official count from snapshots

   //--- A336 (#14) inactivity watchdog
   datetime    m_last_inactivity_check;
   datetime    m_inactivity_warned_day;

   //--- Current trading-day start: broker SERVER date
   datetime TodayServer() const
   {
      MqlDateTime dt;
      TimeToStruct(TimeTradeServer(), dt);
      dt.hour = 0; dt.min = 0; dt.sec = 0;
      return StructToTime(dt);
   }

   //--- A336 (#1): today's closed trading P&L of the whole account, and our magics' opens/closes
   bool RebuildToday(datetime d0, double &acct_closed, double &our_closed, int &our_opens)
   {
      acct_closed = 0.0; our_closed = 0.0; our_opens = 0;
      if(!HistorySelect(d0, TimeCurrent() + 60)) return false;
      int total = HistoryDealsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong t = HistoryDealGetTicket(i);
         if(t == 0) continue;
         long ty = HistoryDealGetInteger(t, DEAL_TYPE);
         if(ty != DEAL_TYPE_BUY && ty != DEAL_TYPE_SELL) continue;          // deposits/credits are not P&L
         double v = HistoryDealGetDouble(t, DEAL_PROFIT) + HistoryDealGetDouble(t, DEAL_SWAP)
                  + HistoryDealGetDouble(t, DEAL_COMMISSION);
         acct_closed += v;
         if(HistoryDealGetString(t, DEAL_SYMBOL) != EA_SYMBOL) continue;
         if(!IsOurMagic(HistoryDealGetInteger(t, DEAL_MAGIC))) continue;
         our_closed += v;
         if(HistoryDealGetInteger(t, DEAL_ENTRY) == DEAL_ENTRY_IN) our_opens++;
      }
      return true;
   }

   //--- A336 (#13): official count from the snapshots
   void RecountSnapshots()
   {
      double need = inp_AccountSize * inp_ProfitDayPct / 100.0;
      int c = 0;
      for(int i = 0; i < m_snap_n; i++)
         if(m_snap_sb[i] > 0 && MathMin(m_snap_eb[i], m_snap_ee[i]) - m_snap_sb[i] >= need) c++;
      m_snap_days = c;
   }

   //--- A336 (#13): closed-P&L fallback for server days before the first snapshot (EA not running then)
   void CountHistoryFallback()
   {
      m_hist_days = 0;
      datetime limit = (m_snap_n > 0) ? m_snap_day[0] : TodayServer();
      if(!HistorySelect(0, limit)) return;                     // deals strictly before `limit`
      double   day_sum[];
      datetime day_key[];
      int n = 0;
      int total = HistoryDealsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong d = HistoryDealGetTicket(i);
         if(d == 0) continue;
         long type = HistoryDealGetInteger(d, DEAL_TYPE);
         if(type != DEAL_TYPE_BUY && type != DEAL_TYPE_SELL) continue;
         datetime t = (datetime)HistoryDealGetInteger(d, DEAL_TIME);       // server time
         if(t >= limit) continue;
         double v = HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_SWAP)
                  + HistoryDealGetDouble(d, DEAL_COMMISSION);
         datetime k = t - (t % 86400);
         int j = -1;
         for(int q = 0; q < n; q++) if(day_key[q] == k) { j = q; break; }
         if(j < 0) { ArrayResize(day_sum, n + 1); ArrayResize(day_key, n + 1); day_key[n] = k; day_sum[n] = 0; j = n; n++; }
         day_sum[j] += v;
      }
      double need = inp_AccountSize * inp_ProfitDayPct / 100.0;
      for(int q = 0; q < n; q++) if(day_sum[q] >= need) m_hist_days++;
      if(n > 0)
         Logger.Warn("STATS", "Profitable days before the EA's first midnight snapshot use the closed-P&L fallback (floating P&L at midnight unknown)",
            StringFormat("fallback_days=%d before=%s", m_hist_days, TimeToString(limit, TIME_DATE)));
   }

   //--- Start a new server day. record_prev = a snapshot of the day that just ended is written.
   void ResetForNewDay(bool record_prev)
   {
      double bal = AccountInfoDouble(ACCOUNT_BALANCE);
      double eq  = AccountInfoDouble(ACCOUNT_EQUITY);
      datetime today = TodayServer();

      if(record_prev && m_stats.reset_date > 0 && m_stats.reset_date < today && m_stats.start_balance > 0)
      {
         Persistence.AppendDaySnapshot(m_stats.reset_date, m_stats.start_balance, bal, eq);
         ArrayResize(m_snap_day, m_snap_n + 1); ArrayResize(m_snap_sb, m_snap_n + 1);
         ArrayResize(m_snap_eb, m_snap_n + 1);  ArrayResize(m_snap_ee, m_snap_n + 1);
         m_snap_day[m_snap_n] = m_stats.reset_date; m_snap_sb[m_snap_n] = m_stats.start_balance;
         m_snap_eb[m_snap_n]  = bal;                m_snap_ee[m_snap_n] = eq;
         m_snap_n++;
         RecountSnapshots();
         double gain = MathMin(bal, eq) - m_stats.start_balance;
         Logger.Info("STATS", "Day closed (The5%ers profitable-day formula)",
            StringFormat("day=%s min(bal,eq)-prev_bal=%.2f need=%.2f profitable_days=%d",
                         TimeToString(m_stats.reset_date, TIME_DATE), gain,
                         inp_AccountSize * inp_ProfitDayPct / 100.0, GetProfitableDays()));
      }

      m_stats.reset_date      = today;
      m_stats.open_equity     = MathMax(bal, eq);       // A336 (#8/G1): firm's day base
      m_stats.start_balance   = bal;
      m_stats.forced_limit    = false;
      m_stats.closed_pnl      = 0.0;
      m_stats.peak_equity     = eq;
      m_stats.min_equity      = eq;
      m_stats.trade_count     = 0;
      m_stats.wins            = 0;
      m_stats.losses          = 0;
      m_stats.consec_losses   = 0;
      m_stats.last_close_time = 0;

      m_daily_limit_hit = false;
      m_max_trades_hit  = false;

      Persistence.WriteDaily(m_stats);

      Logger.Info("STATS", "Daily stats reset for new SERVER day",
         StringFormat("date=%s day_base=%.2f (balance=%.2f equity=%.2f) stop_line=%.2f",
                      TimeToString(m_stats.reset_date, TIME_DATE),
                      m_stats.open_equity, bal, eq,
                      m_stats.open_equity * (1.0 - Config.DailyStopPct / 100.0)));
   }

public:
   CDailyStats() :
      m_initialized(false),
      m_daily_limit_hit(false),
      m_max_trades_hit(false),
      m_snap_n(0),
      m_hist_days(0),
      m_snap_days(0),
      m_last_inactivity_check(0),
      m_inactivity_warned_day(0)
   {
      ZeroMemory(m_stats);
   }

   bool Init()
   {
      //--- snapshots first (profitable days)
      m_snap_n = Persistence.ReadDaySnapshots(m_snap_day, m_snap_sb, m_snap_eb, m_snap_ee);
      RecountSnapshots();
      CountHistoryFallback();

      datetime today = TodayServer();
      double bal = AccountInfoDouble(ACCOUNT_BALANCE);
      double eq  = AccountInfoDouble(ACCOUNT_EQUITY);
      double acct_closed = 0.0, our_closed = 0.0;
      int    our_opens = 0;
      bool   hist_ok = RebuildToday(today, acct_closed, our_closed, our_opens);
      double bal0 = hist_ok ? bal - acct_closed : bal;          // balance at 00:00 server

      DailyStatsData file;
      ZeroMemory(file);
      if(Persistence.ReadDaily(file))
      {
         //--- same server day: restore, but never lower the base below the rebuilt midnight balance
         m_stats = file;
         m_stats.open_equity   = MathMax(file.open_equity, bal0);
         if(m_stats.start_balance <= 0) m_stats.start_balance = bal0;
      }
      else
      {
         //--- no file for today (first start today, or the file was lost): rebuild.
         //    Midnight equity is unknown; MathMax(midnight balance, current equity) is used.
         bool had_old = (file.reset_date > 0 && file.reset_date < today);
         if(had_old)
            Logger.Warn("STATS", "EA was not running at the last server midnight - that day is NOT counted as a profitable day (midnight equity unknown)",
               StringFormat("last_file_day=%s", TimeToString(file.reset_date, TIME_DATE)));
         ZeroMemory(m_stats);
         m_stats.reset_date    = today;
         m_stats.open_equity   = MathMax(bal0, eq);
         m_stats.start_balance = bal0;
         m_stats.forced_limit  = false;
         m_stats.peak_equity   = eq;
         m_stats.min_equity    = eq;
      }
      if(hist_ok)
      {
         m_stats.closed_pnl  = our_closed;                      // authoritative: all our magics
         m_stats.trade_count = MathMax(m_stats.trade_count, our_opens);
      }

      //--- restore the day's stop flags
      double stop_line = m_stats.open_equity * (1.0 - Config.DailyStopPct / 100.0);
      m_daily_limit_hit = m_stats.forced_limit
                       || (m_stats.closed_pnl <= -(Config.DailyLossLimit))
                       || (eq <= stop_line);
      m_max_trades_hit  = (m_stats.trade_count >= Config.MaxDailyTrades);
      Persistence.WriteDaily(m_stats);

      m_initialized = true;

      Logger.Info("STATS", "Daily stats initialized",
         StringFormat("day=%s base=%.2f bal0=%.2f stop_line=%.2f trades=%d pnl=%.2f limit_hit=%d forced=%d max_hit=%d profitable_days=%d (snap=%d hist=%d)",
                      TimeToString(m_stats.reset_date, TIME_DATE), m_stats.open_equity, bal0, stop_line,
                      m_stats.trade_count, m_stats.closed_pnl,
                      (int)m_daily_limit_hit, (int)m_stats.forced_limit, (int)m_max_trades_hit,
                      GetProfitableDays(), m_snap_days, m_hist_days));
      return true;
   }

   //--- A336 (#8/G1/G2): check for the server-day change on EVERY tick and every second (OnTimer).
   //    A cheap date compare; the base is snapped the moment the day changes.
   void CheckDayRollover()
   {
      if(!m_initialized) return;
      datetime today = TodayServer();
      if(today > m_stats.reset_date)
         ResetForNewDay(true);
      //--- Review fix: Init ran before the account was loaded (balance 0) -> base 0 would switch
      //    the daily stop off for the whole day. Snap it as soon as real figures arrive.
      if(m_stats.open_equity <= 0.0)
      {
         double b = AccountInfoDouble(ACCOUNT_BALANCE), e = AccountInfoDouble(ACCOUNT_EQUITY);
         if(b > 0.0)
         {
            m_stats.open_equity = MathMax(b, e);
            if(m_stats.start_balance <= 0.0) m_stats.start_balance = b;
            Persistence.WriteDaily(m_stats);
            Logger.Warn("STATS", "Day base was 0 at init (account not loaded) - snapped now",
               StringFormat("base=%.2f", m_stats.open_equity));
         }
      }
   }

   //--- Record a trade open (any of our magics, A336 #18)
   void OnTradeOpen()
   {
      m_stats.trade_count++;
      if(m_stats.trade_count >= Config.MaxDailyTrades && !m_max_trades_hit)
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
   //--- A320/A336: equity-based daily stop locks the day; the flag is SAVED so a restart keeps it
   void ForceDailyLimit(string why)
   {
      if(m_daily_limit_hit && m_stats.forced_limit) return;
      m_daily_limit_hit     = true;
      m_stats.forced_limit  = true;
      Persistence.WriteDaily(m_stats);
      Logger.Warn("STATS", "Daily limit forced (saved)", why);
   }
   bool IsMaxTradesHit()    const { return m_max_trades_hit; }
   int  GetTradeCount()     const { return m_stats.trade_count; }
   int  GetConsecLosses()   const { return m_stats.consec_losses; }
   double GetClosedPnL()    const { return m_stats.closed_pnl; }
   double GetOpenEquity()   const { return m_stats.open_equity; }   // = day base (A336)
   double GetDayBase()      const { return m_stats.open_equity; }
   double GetStartBalance() const { return m_stats.start_balance; }
   int  GetProfitableDays() const { return m_snap_days + m_hist_days; }
   datetime GetLastClose()  const { return m_stats.last_close_time; }

   //--- Cooldown check: enough time since last trade closed?
   bool IsCooldownActive() const
   {
      if(m_stats.last_close_time == 0) return false;
      return (TimeCurrent() - m_stats.last_close_time) < TRADE_COOLDOWN_SEC;
   }

   //--- Consecutive loss pause check (A336 #18: uses CONSEC_LOSS_LIMIT, not MaxDailyTrades)
   bool IsConsecLossPaused() const
   {
      if(m_stats.consec_losses < CONSEC_LOSS_LIMIT) return false;
      // Check if pause has expired
      if(m_stats.last_close_time == 0) return false;
      datetime pause_end = m_stats.last_close_time + CONSEC_LOSS_PAUSE_SEC;
      return (TimeCurrent() < pause_end);
   }

   //--- A336 (#14 / G14): The5%ers expires an account after 30 days with no NEW trade opened.
   //    Checked hourly from the timer; a loud warning once per server day from day 25. Never trades.
   void CheckInactivity()
   {
      if(MQLInfoInteger(MQL_TESTER)) return;
      if(m_last_inactivity_check != 0 && TimeCurrent() - m_last_inactivity_check < 3600) return;
      m_last_inactivity_check = TimeCurrent();
      datetime from = TimeCurrent() - 60 * 86400;
      if(!HistorySelect(from, TimeCurrent() + 60)) return;
      datetime last_open = 0, first_deal = 0;
      int total = HistoryDealsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong t = HistoryDealGetTicket(i);
         if(t == 0) continue;
         datetime dt = (datetime)HistoryDealGetInteger(t, DEAL_TIME);
         if(first_deal == 0 || dt < first_deal) first_deal = dt;
         long ty = HistoryDealGetInteger(t, DEAL_TYPE);
         if((ty == DEAL_TYPE_BUY || ty == DEAL_TYPE_SELL) && HistoryDealGetInteger(t, DEAL_ENTRY) == DEAL_ENTRY_IN)
            if(dt > last_open) last_open = dt;
      }
      datetime ref = (last_open > 0) ? last_open : ((first_deal > 0) ? first_deal : from);
      int idle_days = (int)((TimeCurrent() - ref) / 86400);
      if(idle_days >= 25 && m_inactivity_warned_day != TodayServer())
      {
         m_inactivity_warned_day = TodayServer();
         Logger.Critical("STATS", "INACTIVITY WARNING: no new trade opened for 25+ days - The5%ers expires the account at 30 days",
            StringFormat("idle_days=%d last_open=%s", idle_days, TimeToString(ref, TIME_DATE|TIME_MINUTES)));
         Alert(EA_NAME, ": no new trade for ", idle_days, " days. The5%ers expires the account after 30 days without a new trade.");
      }
   }

   //--- Manual reset (for testing only — logs clearly)
   void ForceReset(string reason)
   {
      Logger.Warn("STATS",
         StringFormat("FORCED RESET — reason: %s", reason));
      ResetForNewDay(false);
   }

   bool IsReady() const { return m_initialized; }
};

//--- Global singleton
CDailyStats DailyStats;

//--- A336 (#13 / G5): profitable days the official The5%ers way (see CDailyStats).
int CountProfitableDays()
{
   return DailyStats.GetProfitableDays();
}

//--- A335: risk multiplier. Target reached but fewer than the required profitable days -> keep trading
//    at 40% size until the day count is met (The5%ers needs both).
double StageRiskMult()
{
   if(inp_MinProfitDays <= 0) return 1.0;
   if(AccountInfoDouble(ACCOUNT_BALANCE) >= Config.ProfitTarget && CountProfitableDays() < inp_MinProfitDays) return 0.4;
   return 1.0;
}

#endif // CDAILYSTATS_MQH

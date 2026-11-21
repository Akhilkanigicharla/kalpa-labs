
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Timer System                            |
//| File: Core/CTimerSystem.mqh                                       |
//| Purpose: Orchestrate all timer-driven tasks.                      |
//|           Runs every 60 seconds via MT5 OnTimer().                |
//|           Separates tick-frequency tasks from minute-frequency.   |
//| Phase: 1 — Core Framework                                         |
//+------------------------------------------------------------------+
#ifndef CTIMERSYSTEM_MQH
#define CTIMERSYSTEM_MQH
#include "../Include/Defines.mqh"
#include "CLogger.mqh"
#include "CPersistence.mqh"
#include "CDailyStats.mqh"
#include "CStateManager.mqh"

//===================================================================
// PSEUDO-CODE DESIGN
//
// MT5 EventSetTimer(60) runs OnTimer() every 60 seconds.
// Not every task should run every second on every tick.
// Timer-driven tasks:
//
//   Every tick (OnTick):
//     - Guard layer
//     - Market intelligence
//     - Entry evaluation
//     - Trade management
//     - Equity update
//
//   Every 60 seconds (OnTimer / CTimerSystem):
//     - Heartbeat file write
//     - Day rollover check
//     - VPS disconnect check
//     - Retry queue processing (delegated to Recovery module)
//     - Memory cleanup scheduler
//     - Performance stats update
//     - Stale price detection
//
//   Every 60 minutes (via OnTimer counter):
//     - Full memory cleanup
//     - Spread database pruning
//
// This approach keeps tick processing lean.
// Heavy disk/array operations stay in the timer path.
//===================================================================

class CTimerSystem
{
private:
   bool     m_initialized;
   int      m_timer_interval_sec;  // Registered timer interval
   int      m_tick_count;          // Ticks since last timer
   int      m_timer_fire_count;    // Total MINUTE-level runs since init (A336: timer is 1 s)
   int      m_second_count;        // A336: 1-second timer fires since init
   bool     m_minute_tick;         // A336: true during a fire that ran the 60 s tasks
   datetime m_last_minute_run;     // A336
   datetime m_last_tick_time;      // For stale price detection
   datetime m_last_price;          // Price at last tick (velocity check)
   double   m_last_bid;

   // Delegate pointers — set in Phase 7 when recovery module exists
   // For Phase 1: just heartbeat + day check
   bool     m_disconnect_handler_active; // Phase 7 will set this

public:
   CTimerSystem() :
      m_initialized(false),
      m_timer_interval_sec(1),
      m_tick_count(0),
      m_timer_fire_count(0),
      m_second_count(0),
      m_minute_tick(false),
      m_last_minute_run(0),
      m_last_tick_time(0),
      m_last_price(0),
      m_last_bid(0),
      m_disconnect_handler_active(false)
   {}

   bool Init()
   {
      // A336 (#8): timer fires every SECOND so the day base is snapped right at server midnight
      //            and the Friday cut runs on time; heavier tasks still run every 60 s.
      if(!EventSetTimer(m_timer_interval_sec))
      {
         Logger.Error("TIMER", "EventSetTimer() failed — timer tasks disabled");
         return false;
      }

      m_initialized = true;
      Logger.Info("TIMER", "Timer system initialized",
         StringFormat("interval=%ds", m_timer_interval_sec));
      return true;
   }

   //--- Called from EA OnTimer() (every second)
   void OnTimerFire()
   {
      if(!m_initialized) return;
      m_second_count++;
      m_minute_tick = false;

      // --- Every second: server-day rollover (snaps the day base at 00:00 server)
      DailyStats.CheckDayRollover();

      if(m_last_minute_run != 0 && (TimeLocal() - m_last_minute_run) < 60) return;
      m_last_minute_run = TimeLocal();
      m_minute_tick = true;
      m_timer_fire_count++;

      double   equity = AccountInfoDouble(ACCOUNT_EQUITY);

      // --- Task 1: Heartbeat write (every timer fire)
      Persistence.WriteHeartbeat(
         StateManager.GetState(),
         equity,
         StateManager.GetSuspendReason()
      );

      // --- Task 2: Day rollover check (also every second above, and every tick)
      DailyStats.CheckDayRollover();
      DailyStats.CheckInactivity();          // A336 (#14): hourly inside

      // --- Task 3: Equity tracker update
      DailyStats.UpdateEquity(equity);

      // --- Task 4: Stale price detection (A336 #15: from the tick's own time)
      if(IsPriceStale() && IsMarketOpenNow())
      {
         Logger.Warn("TIMER", "Stale price detected - no new entries until quotes resume",
            StringFormat("last_tick=%ds ago", SecondsSinceLastTick()));
      }

      // --- Task 5: Hourly cleanup (every 60 timer fires = ~60 min)
      if(m_timer_fire_count % 60 == 0)
      {
         Logger.Debug("TIMER", "Hourly cleanup trigger",
            StringFormat("fires=%d", m_timer_fire_count));
         // Phase 7 memory cleanup module will hook here
      }

      // --- Task 6: Log timer health at INFO level (every 10 fires)
      if(m_timer_fire_count % 10 == 0)
      {
         Logger.Info("TIMER", "Heartbeat OK",
            StringFormat("equity=%.2f state=%s fires=%d",
                         equity,
                         EnumToString(StateManager.GetState()),
                         m_timer_fire_count));
      }
   }

   //--- Called from EA OnTick() — track tick timing
   void OnTickFire()
   {
      MqlTick t;
      if(SymbolInfoTick(EA_SYMBOL, t)) { m_last_tick_time = t.time; m_last_bid = t.bid; }
      m_tick_count++;
   }

   //--- A336 (#15): stale = the symbol's last quote is older than STALE_PRICE_SEC by the
   //    trade-server clock. (Before, OnTickFire set the time to "now" right before the check,
   //    so it could never fire.)
   bool IsPriceStale() const
   {
      MqlTick t;
      if(!SymbolInfoTick(EA_SYMBOL, t) || t.time == 0) return true;
      return ((TimeTradeServer() - t.time) > STALE_PRICE_SEC);
   }

   //--- Market should be quoting now (server Mon-Fri, outside the rollover gap); used for logging only
   bool IsMarketOpenNow() const
   {
      MqlDateTime s;
      TimeToStruct(TimeTradeServer(), s);
      if(s.day_of_week == 0 || s.day_of_week == 6) return false;
      int m = s.hour * 60 + s.min;
      return (m >= 70 && m <= 23 * 60 + 50);               // The5%ers metals 01:05-23:50 server (EET)
   }

   //--- Get seconds since last tick
   int SecondsSinceLastTick() const
   {
      MqlTick t;
      if(!SymbolInfoTick(EA_SYMBOL, t) || t.time == 0) return 0;
      return (int)(TimeTradeServer() - t.time);
   }

   bool   IsMinuteTick() const { return m_minute_tick; }   // A336: 60 s tasks ran in this fire

   double LastBid() const { return m_last_bid; }
   int    TickCount() const { return m_tick_count; }
   int    TimerFires() const { return m_timer_fire_count; }
   bool   IsReady()  const { return m_initialized; }

   void Shutdown()
   {
      if(m_initialized)
      {
         EventKillTimer();
         Logger.Info("TIMER", "Timer system shutdown");
         m_initialized = false;
      }
   }
};

//--- Global singleton
CTimerSystem TimerSystem;

#endif // CTIMERSYSTEM_MQH

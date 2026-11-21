
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
   int      m_timer_fire_count;    // Total timer fires since init
   datetime m_last_tick_time;      // For stale price detection
   datetime m_last_price;          // Price at last tick (velocity check)
   double   m_last_bid;

   // Delegate pointers — set in Phase 7 when recovery module exists
   // For Phase 1: just heartbeat + day check
   bool     m_disconnect_handler_active; // Phase 7 will set this

public:
   CTimerSystem() :
      m_initialized(false),
      m_timer_interval_sec(60),
      m_tick_count(0),
      m_timer_fire_count(0),
      m_last_tick_time(0),
      m_last_price(0),
      m_last_bid(0),
      m_disconnect_handler_active(false)
   {}

   bool Init()
   {
      // Register MT5 timer — fires OnTimer() every 60 seconds
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

   //--- Called from EA OnTimer()
   void OnTimerFire()
   {
      if(!m_initialized) return;
      m_timer_fire_count++;

      datetime now = TimeCurrent();
      double   equity = AccountInfoDouble(ACCOUNT_EQUITY);

      // --- Task 1: Heartbeat write (every timer fire)
      Persistence.WriteHeartbeat(
         StateManager.GetState(),
         equity,
         StateManager.GetSuspendReason()
      );

      // --- Task 2: Day rollover check
      DailyStats.CheckDayRollover();

      // --- Task 3: Equity tracker update
      DailyStats.UpdateEquity(equity);

      // --- Task 4: Stale price detection
      if(m_last_tick_time > 0)
      {
         int seconds_since_tick = (int)(now - m_last_tick_time);
         if(seconds_since_tick > STALE_PRICE_SEC)
         {
            Logger.Warn("TIMER", "Stale price detected",
               StringFormat("last_tick=%ds ago", seconds_since_tick));
            // Phase 7 will trigger VPS disconnect handling here
         }
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
      m_last_tick_time = TimeCurrent();
      m_last_bid       = SymbolInfoDouble(EA_SYMBOL, SYMBOL_BID);
      m_tick_count++;
   }

   //--- Check if price feed is stale
   bool IsPriceStale() const
   {
      if(m_last_tick_time == 0) return false;
      return ((TimeCurrent() - m_last_tick_time) > STALE_PRICE_SEC);
   }

   //--- Get seconds since last tick
   int SecondsSinceLastTick() const
   {
      if(m_last_tick_time == 0) return 0;
      return (int)(TimeCurrent() - m_last_tick_time);
   }

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

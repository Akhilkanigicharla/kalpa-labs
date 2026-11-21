
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — News Guard                              |
//| File: Guards/CNewsGuard.mqh                                       |
//| Purpose: Detect news events via behavioral signature (no API).    |
//|           ATR spike + spread spike + velocity = news signature.   |
//| Phase: 2 — Guard Layer / Step 8                                   |
//| GUARD SLOT: 7                                                      |
//+------------------------------------------------------------------+
#ifndef CNEWSGUARD_MQH
#define CNEWSGUARD_MQH

#include "../Include/Defines.mqh"
#include "../Include/PriceUtils.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "GuardTypes.mqh"
#include "CSpreadGuard.mqh"   // For session avg spread + ATR access

#define NEWS_COOLDOWN_SEC       3600   // 60 minutes
#define NEWS_MAX_COOLDOWN_SEC   5400   // 90 minutes hard cap
#define NEWS_POST_BUFFER_SEC    1800   // 30 minutes post-news buffer
#define NEWS_VELOCITY_WINDOW    120    // Seconds for velocity check
#define NEWS_RESET_CANDLES      3      // M5 candles needed for reset
#define NEWS_CIRCUIT_FILE       "EA_XAUUSD_news_state.txt"

//--- Forward declare CSpreadGuard (already included)
extern CSpreadGuard SpreadGuard;

class CNewsGuard : public IGuard
{
private:
   NEWS_STATE  m_state;
   datetime    m_trigger_time;
   int         m_cooldown_sec;
   int         m_triggers_fired;   // Bitmask: bit0=ATR, bit1=spread, bit2=velocity

   //--- Price velocity tracking
   double      m_price_history[4];  // Last 4 prices at 30-second intervals
   datetime    m_price_times[4];
   int         m_price_idx;

   //--- M5 candle tracking (for reset condition)
   datetime    m_last_m5_time;
   int         m_m5_candles_since_trigger;

   //--- Post-news buffer
   datetime    m_cooldown_end_time;
   datetime    m_post_buffer_end_time;

   //--- Reset condition checklist
   bool ResetConditionsMet(const GuardContext &ctx,
                            CSpreadGuard* spread_guard)
   {
      if(spread_guard == NULL) return false;

      // 1. Cooldown elapsed
      if(TimeCurrent() < m_cooldown_end_time) return false;

      // 2. ATR normalised (< 1.5× session avg)
      double avg_atr  = spread_guard.GetSessionAvgATR(ctx);
      double curr_atr = spread_guard.GetLastATR();
      if(avg_atr > 0 && curr_atr > avg_atr * 1.5) return false;

      // 3. Spread normalised (< 1.5× session avg)
      double avg_sp  = spread_guard.GetSessionAvgSpread(ctx);
      double curr_sp = ctx.current_spread_pips;
      if(avg_sp > 0 && curr_sp > avg_sp * 1.5) return false;

      // 4. No velocity breach in last 5 minutes
      if(!CheckVelocityClear()) return false;

      // 5. Minimum M5 candles formed since trigger
      if(m_m5_candles_since_trigger < NEWS_RESET_CANDLES) return false;

      return true;
   }

   bool CheckVelocityClear() const
   {
      // No price history yet — assume clear
      if(m_price_history[0] == 0) return true;

      // Check max movement in any 2-minute window in history
      for(int i = 0; i < 3; i++)
      {
         if(m_price_times[i] == 0) continue;
         for(int j = i+1; j < 4; j++)
         {
            if(m_price_times[j] == 0) continue;
            int time_diff = (int)MathAbs(m_price_times[i] - m_price_times[j]);
            if(time_diff > NEWS_VELOCITY_WINDOW) continue;
            double move = MathAbs(m_price_history[i] - m_price_history[j]);
            double move_pips = move / PriceUtils.PipSize();
            if(move_pips >= Config.CBVelocityPips) return false;
         }
      }
      return true;
   }

   void UpdatePriceHistory(double price)
   {
      m_price_idx = (m_price_idx + 1) % 4;
      m_price_history[m_price_idx] = price;
      m_price_times[m_price_idx]   = TimeCurrent();
   }

   bool CheckVelocityBreach(double current_price) const
   {
      for(int i = 0; i < 4; i++)
      {
         if(m_price_times[i] == 0) continue;
         int elapsed = (int)(TimeCurrent() - m_price_times[i]);
         if(elapsed > NEWS_VELOCITY_WINDOW) continue;
         double move_pips = MathAbs(current_price - m_price_history[i])
                            / PriceUtils.PipSize();
         if(move_pips >= Config.CBVelocityPips) return true;
      }
      return false;
   }

   public:
   virtual void SaveState() override
   {
      int h = FileOpen(NEWS_CIRCUIT_FILE,
                       FILE_WRITE|FILE_TXT|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE) return;
      FileWriteString(h, StringFormat("state=%d\n",         (int)m_state));
      FileWriteString(h, StringFormat("trigger_time=%d\n",  (long)m_trigger_time));
      FileWriteString(h, StringFormat("cooldown_end=%d\n",  (long)m_cooldown_end_time));
      FileWriteString(h, StringFormat("post_end=%d\n",      (long)m_post_buffer_end_time));
      FileClose(h);
   }

   // A336 (#31): overrides a PUBLIC virtual of IGuard, so it stays public
   virtual void LoadState() override
   {
      if(!FileIsExist(NEWS_CIRCUIT_FILE)) return;
      int h = FileOpen(NEWS_CIRCUIT_FILE,
                       FILE_READ|FILE_TXT|FILE_SHARE_WRITE|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE) return;
      while(!FileIsEnding(h))
      {
         string line = FileReadString(h);
         StringTrimRight(line);
         StringTrimLeft(line);
         if(StringFind(line, "state=")        == 0)
            m_state = (NEWS_STATE)(int)StringToInteger(StringSubstr(line,6));
         if(StringFind(line, "trigger_time=") == 0)
            m_trigger_time = (datetime)StringToInteger(StringSubstr(line,13));
         if(StringFind(line, "cooldown_end=") == 0)
            m_cooldown_end_time = (datetime)StringToInteger(StringSubstr(line,13));
         if(StringFind(line, "post_end=")     == 0)
            m_post_buffer_end_time = (datetime)StringToInteger(StringSubstr(line,9));
      }
      FileClose(h);

      if(m_state != NEWS_CLEAR)
         Logger.Info("NEWS",
            StringFormat("Restored state=%s cooldown_end=%s",
                         EnumToString(m_state),
                         TimeToString(m_cooldown_end_time, TIME_DATE|TIME_SECONDS)));
   }

private:
   //--- Pointer to SpreadGuard (injected after both are initialized)
   CSpreadGuard* m_spread_guard;

public:
   CNewsGuard() :
      m_state(NEWS_CLEAR),
      m_trigger_time(0),
      m_cooldown_sec(NEWS_COOLDOWN_SEC),
      m_triggers_fired(0),
      m_price_idx(0),
      m_last_m5_time(0),
      m_m5_candles_since_trigger(0),
      m_cooldown_end_time(0),
      m_post_buffer_end_time(0),
      m_spread_guard(NULL)
   {
      ArrayInitialize(m_price_history, 0);
      ArrayInitialize(m_price_times,   0);
      m_meta.index       = 7;
      m_meta.priority    = GPRIO_NEWS;
      m_meta.name        = "NEWS";
      m_meta.description = "Behavioral news signature detection";
      m_meta.enabled     = true;
   }

   void SetSpreadGuard(CSpreadGuard* sg) { m_spread_guard = sg; }

   virtual bool Init() override
   {
      LoadState();
      // If cooldown already elapsed since save: clear state
      if(m_state != NEWS_CLEAR && TimeCurrent() > m_post_buffer_end_time + 3600)
      {
         Logger.Info("NEWS",
            "Stale news state cleared on init (expired during offline period)");
         m_state = NEWS_CLEAR;
      }
      m_meta.initialized = true;
      m_initialized      = true;
      Logger.Info("NEWS",
         StringFormat("Initialized. state=%s cooldown=%ds",
                      EnumToString(m_state), NEWS_COOLDOWN_SEC));
      return true;
   }

   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();

      // Track M5 candle closes (for reset condition)
      datetime m5_bar = iTime(EA_SYMBOL, PERIOD_M5, 0);
      if(m5_bar != m_last_m5_time && m_last_m5_time != 0)
      {
         if(m_state != NEWS_CLEAR)
            m_m5_candles_since_trigger++;
         m_last_m5_time = m5_bar;
      }
      else if(m_last_m5_time == 0)
         m_last_m5_time = m5_bar;

      // Update price velocity buffer every call
      UpdatePriceHistory(ctx.current_bid);

      //--- Active cooldown or post-buffer
      if(m_state == NEWS_COOLDOWN || m_state == NEWS_ACTIVE)
      {
         // Hard cap: 90 min regardless of reset conditions
         if(TimeCurrent() >= m_trigger_time + NEWS_MAX_COOLDOWN_SEC)
         {
            Logger.Info("NEWS",
               "News cooldown hard cap elapsed — forcing clear");
            m_state = NEWS_POST_COOLDOWN;
            m_post_buffer_end_time = TimeCurrent() + NEWS_POST_BUFFER_SEC;
         }
         else if(m_spread_guard != NULL &&
                 ResetConditionsMet(ctx, m_spread_guard))
         {
            Logger.Info("NEWS",
               StringFormat("News reset conditions met after %ds",
                            (int)(TimeCurrent() - m_trigger_time)));
            m_state = NEWS_POST_COOLDOWN;
            m_post_buffer_end_time = TimeCurrent() + NEWS_POST_BUFFER_SEC;
            SaveState();
         }

         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_NEWS, m_meta.name, m_meta.index,
                             SUSPEND_NEWS_WINDOW,
                             StringFormat("News event active. "
                                          "cooldown_remaining=%ds",
                                          (int)MathMax(0,
                                          m_cooldown_end_time - TimeCurrent())),
                             "Resumes after ATR/spread normalise + cooldown");
      }

      if(m_state == NEWS_POST_COOLDOWN)
      {
         if(TimeCurrent() >= m_post_buffer_end_time)
         {
            m_state = NEWS_CLEAR;
            m_m5_candles_since_trigger = 0;
            Logger.Info("NEWS", "Post-news buffer cleared — trading resumed");
            SaveState();
         }
         else
         {
            RecordTrigger(GUARD_BLOCK);
            return GuardBlock(GPRIO_NEWS, m_meta.name, m_meta.index,
                              StringFormat("Post-news buffer: %ds remaining",
                                           (int)(m_post_buffer_end_time
                                                 - TimeCurrent())));
         }
      }

      //--- Detection: check for news signature triggers
      if(m_state == NEWS_CLEAR || m_state == NEWS_SUSPECTED)
      {
         int new_triggers = 0;

         // N1: ATR spike
         if(m_spread_guard != NULL)
         {
            double avg_atr = m_spread_guard.GetSessionAvgATR(ctx);
            double cur_atr = m_spread_guard.GetLastATR();
            if(avg_atr > 0 && cur_atr > avg_atr * Config.CBSpikeMultATR)
               new_triggers |= 1;

            // N2: Spread spike
            if(m_spread_guard.IsSpikingNow())
               new_triggers |= 2;
         }

         // N3: Velocity
         if(CheckVelocityBreach(ctx.current_bid))
            new_triggers |= 4;

         // Trigger logic:
         // Single trigger → SUSPECTED
         // Two+ triggers  → ACTIVE (full suspension)
         int total_triggers = 0;
         for(int b = 0; b < 3; b++)
            if(((new_triggers >> b) & 1) != 0) total_triggers++;

         if(total_triggers >= 2 && m_state != NEWS_ACTIVE)
         {
            m_state              = NEWS_ACTIVE;
            m_trigger_time       = TimeCurrent();
            m_triggers_fired     = new_triggers;
            m_cooldown_sec       = NEWS_COOLDOWN_SEC;
            m_cooldown_end_time  = m_trigger_time + m_cooldown_sec;
            m_m5_candles_since_trigger = 0;
            Logger.Warn("NEWS",
               StringFormat("NEWS EVENT DETECTED (multi-trigger): "
                            "triggers=0x%02X atr=%d spread=%d velocity=%d",
                            new_triggers,
                            ((new_triggers & 1) != 0) ? 1 : 0,
                            ((new_triggers & 2) != 0) ? 1 : 0,
                            ((new_triggers & 4) != 0) ? 1 : 0));
            SaveState();

            RecordTrigger(GUARD_SUSPEND);
            return GuardSuspend(GPRIO_NEWS, m_meta.name, m_meta.index,
                                SUSPEND_NEWS_WINDOW,
                                StringFormat("News detected: triggers=0x%02X",
                                             new_triggers),
                                "Resumes after 60min + 5 reset conditions");
         }
         else if(total_triggers == 1 && m_state == NEWS_CLEAR)
         {
            m_state = NEWS_SUSPECTED;
            Logger.Debug("NEWS",
               StringFormat("News suspected (single trigger=0x%02X) — monitoring",
                            new_triggers));
         }
         else if(total_triggers == 0 && m_state == NEWS_SUSPECTED)
         {
            m_state = NEWS_CLEAR; // Single trigger cleared without second
         }
      }

      return GuardPass(GPRIO_NEWS, m_meta.name, m_meta.index);
   }

   virtual bool CheckResume(const GuardContext &ctx) override
   {
      if(m_state == NEWS_CLEAR) return true;
      if(m_state == NEWS_POST_COOLDOWN)
         return (TimeCurrent() >= m_post_buffer_end_time);
      return false;
   }
};

#endif // CNEWSGUARD_MQH

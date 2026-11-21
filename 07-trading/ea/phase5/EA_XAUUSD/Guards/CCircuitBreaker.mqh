//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Circuit Breaker Guard                   |
//| File: Guards/CCircuitBreaker.mqh                                  |
//| Purpose: Volatility anomaly protection — ATR spike, velocity,     |
//|           expansion sequence, spread+vol combo triggers.          |
//| Phase: 2 — Guard Layer / Step 8 (split from CNewsGuard.mqh)       |
//| GUARD SLOT: 9                                                      |
//+------------------------------------------------------------------+
#ifndef CCIRCUITBREAKER_MQH
#define CCIRCUITBREAKER_MQH

#include "../Include/Defines.mqh"
#include "../Include/PriceUtils.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "GuardTypes.mqh"
#include "CSpreadGuard.mqh"

#define CB_FILE                 "EA_XAUUSD_cb_state.txt"

class CCircuitBreaker : public IGuard
{
private:
   CB_STATE   m_state;
   CB_TRIGGER m_trigger_type;
   datetime   m_trigger_time;
   datetime   m_resume_time;
   int        m_cooldown_sec;

   //--- M5 range buffer for ATR calculation (pre-allocated)
   double     m_m5_ranges[CB_ATR_BARS];
   int        m_range_idx;
   int        m_range_count;
   datetime   m_last_m5_time;

   //--- Price velocity (shared with NewsGuard concept)
   double     m_price_120s_ago;
   datetime   m_price_120s_time;

   //--- Reset confirmation
   int        m_reset_confirm_ticks;
   CSpreadGuard* m_spread_guard;

   double GetCurrentATR() const
   {
      if(m_range_count < 3) return 15.0; // Fallback
      double sum = 0;
      int n = MathMin(m_range_count, CB_ATR_BARS);
      for(int i = 0; i < n; i++) sum += m_m5_ranges[i];
      return sum / n;
   }

   void UpdateM5Buffer()
   {
      datetime bar_time = iTime(EA_SYMBOL, PERIOD_M5, 0);
      if(bar_time == m_last_m5_time) return;
      m_last_m5_time = bar_time;

      double high = iHigh(EA_SYMBOL, PERIOD_M5, 1);
      double low  = iLow(EA_SYMBOL,  PERIOD_M5, 1);
      double range_pips = (high - low) / PriceUtils.PipSize();

      m_range_idx = (m_range_idx + 1) % CB_ATR_BARS;
      m_m5_ranges[m_range_idx] = range_pips;
      m_range_count = MathMin(m_range_count + 1, CB_ATR_BARS);
   }

   bool CheckResetConditions(const GuardContext &ctx) const
   {
      if(TimeCurrent() < m_resume_time) return false;

      double atr = GetCurrentATR();
      double avg_atr = (m_spread_guard != NULL)
                       ? m_spread_guard.GetSessionAvgATR(ctx) : 15.0;
      if(avg_atr > 0 && atr > avg_atr * 1.5) return false;

      double avg_sp = (m_spread_guard != NULL)
                      ? m_spread_guard.GetSessionAvgSpread(ctx) : 15.0;
      if(avg_sp > 0 && ctx.current_spread_pips > avg_sp * 1.5) return false;

      return true;
   }

   int GetCooldown(CB_TRIGGER trig) const
   {
      switch(trig)
      {
         case CB_ATR_SPIKE:        return 1200; // 20 min
         case CB_CONSEC_EXPANSION: return 1800; // 30 min
         case CB_PRICE_VELOCITY:   return 2700; // 45 min
         case CB_SPREAD_VOL_COMBO: return 3600; // 60 min
         default:                  return 1200;
      }
   }

   void Trigger(CB_TRIGGER trig, string detail)
   {
      int cooldown = GetCooldown(trig);
      // Use longest cooldown if already active
      if(m_state == CB_ACTIVE)
         cooldown = MathMax(cooldown, (int)(m_resume_time - TimeCurrent()));

      m_state        = CB_ACTIVE;
      m_trigger_type = trig;
      m_trigger_time = TimeCurrent();
      m_cooldown_sec = cooldown;
      m_resume_time  = m_trigger_time + cooldown;
      m_reset_confirm_ticks = 0;

      Logger.Warn("CIRCUIT_BRK",
         StringFormat("TRIGGERED: %s cooldown=%ds detail=%s",
                      EnumToString(trig), cooldown, detail));
      SaveState();
   }

   void WriteCBStateToDisk()
   {
      int h = FileOpen(CB_FILE, FILE_WRITE|FILE_TXT|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE) return;
      FileWriteString(h, StringFormat("cb_state=%d\n",    (int)m_state));
      FileWriteString(h, StringFormat("trigger=%d\n",     (int)m_trigger_type));
      FileWriteString(h, StringFormat("trigger_time=%d\n",(long)m_trigger_time));
      FileWriteString(h, StringFormat("resume_time=%d\n", (long)m_resume_time));
      FileClose(h);
   }

   void LoadState()
   {
      if(!FileIsExist(CB_FILE)) return;
      int h = FileOpen(CB_FILE,
                       FILE_READ|FILE_TXT|FILE_SHARE_WRITE|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE) return;
      while(!FileIsEnding(h))
      {
         string line = FileReadString(h);
         StringTrimRight(line);
         StringTrimLeft(line);
         if(StringFind(line, "cb_state=")     == 0)
            m_state = (CB_STATE)(int)StringToInteger(StringSubstr(line,9));
         if(StringFind(line, "trigger=")      == 0)
            m_trigger_type = (CB_TRIGGER)(int)StringToInteger(StringSubstr(line,8));
         if(StringFind(line, "trigger_time=") == 0)
            m_trigger_time = (datetime)StringToInteger(StringSubstr(line,13));
         if(StringFind(line, "resume_time=")  == 0)
            m_resume_time  = (datetime)StringToInteger(StringSubstr(line,12));
      }
      FileClose(h);

      if(m_state == CB_ACTIVE)
      {
         if(TimeCurrent() >= m_resume_time)
         {
            Logger.Info("CIRCUIT_BRK",
               "CB elapsed while offline — clearing on restart");
            m_state = CB_NORMAL;
         }
         else
         {
            Logger.Warn("CIRCUIT_BRK",
               StringFormat("CB active from previous session. "
                            "resume_in=%ds trigger=%s",
                            (int)(m_resume_time - TimeCurrent()),
                            EnumToString(m_trigger_type)));
         }
      }
   }

public:
   CCircuitBreaker() :
      m_state(CB_NORMAL),
      m_trigger_type(CB_NONE),
      m_trigger_time(0),
      m_resume_time(0),
      m_cooldown_sec(0),
      m_range_idx(0),
      m_range_count(0),
      m_last_m5_time(0),
      m_price_120s_ago(0),
      m_price_120s_time(0),
      m_reset_confirm_ticks(0),
      m_spread_guard(NULL)
   {
      ArrayInitialize(m_m5_ranges, 0);
      m_meta.index       = 9;
      m_meta.priority    = GPRIO_CIRCUIT_BREAKER;
      m_meta.name        = "CIRCUIT_BRK";
      m_meta.description = "Volatility anomaly circuit breaker";
      m_meta.enabled     = true;
   }

   void SetSpreadGuard(CSpreadGuard* sg) { m_spread_guard = sg; }

   virtual bool Init() override
   {
      LoadState();
      m_meta.initialized = true;
      m_initialized      = true;
      Logger.Info("CIRCUIT_BRK",
         StringFormat("Initialized. state=%s", EnumToString(m_state)));
      return true;
   }

   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();
      UpdateM5Buffer();

      // Update 120-second price reference
      if(m_price_120s_time == 0 ||
         TimeCurrent() - m_price_120s_time >= 120)
      {
         m_price_120s_ago  = ctx.current_bid;
         m_price_120s_time = TimeCurrent();
      }

      //--- Active breaker
      if(m_state == CB_ACTIVE)
      {
         if(CheckResetConditions(ctx))
         {
            m_reset_confirm_ticks++;
            if(m_reset_confirm_ticks >= 2)
            {
               m_state = CB_NORMAL;
               Logger.Info("CIRCUIT_BRK",
                  StringFormat("Circuit breaker cleared after %ds",
                               (int)(TimeCurrent() - m_trigger_time)));
               SaveState();
            }
         }
         else
         {
            m_reset_confirm_ticks = 0;
         }

         if(m_state == CB_ACTIVE)
         {
            RecordTrigger(GUARD_SUSPEND);
            return GuardSuspend(GPRIO_CIRCUIT_BREAKER, m_meta.name, m_meta.index,
                                SUSPEND_CIRCUIT_BREAKER,
                                StringFormat("CB active: %s remaining=%ds",
                                             EnumToString(m_trigger_type),
                                             (int)MathMax(0,
                                             m_resume_time - TimeCurrent())),
                                "Resumes after cooldown + 5-condition reset");
         }
      }

      // Normal state — check for new triggers
      double atr     = GetCurrentATR();
      double avg_atr = (m_spread_guard != NULL)
                       ? m_spread_guard.GetSessionAvgATR(ctx) : atr;

      // CB1: ATR spike (last M5 candle range)
      double last_range = (m_range_count > 0) ? m_m5_ranges[m_range_idx] : 0;
      if(atr > 0 && last_range > atr * Config.CBSpikeMultATR)
      {
         bool spread_also_spiking = (m_spread_guard != NULL &&
                                     m_spread_guard.IsSpikingNow());
         CB_TRIGGER trig = spread_also_spiking
                           ? CB_SPREAD_VOL_COMBO : CB_ATR_SPIKE;
         Trigger(trig,
            StringFormat("range=%.1f atr=%.1f mult=%.1f spread_spike=%d",
                         last_range, atr, Config.CBSpikeMultATR,
                         (int)spread_also_spiking));
      }

      // CB2: Consecutive expansion (last 3 candles all > 1.8× ATR)
      else if(m_range_count >= 3 && atr > 0)
      {
         bool all_expand = true;
         for(int i = 0; i < 3; i++)
         {
            int back_idx = (m_range_idx - i + CB_ATR_BARS) % CB_ATR_BARS;
            if(m_m5_ranges[back_idx] <= atr * Config.CBExpandMultATR)
            {
               all_expand = false;
               break;
            }
         }
         if(all_expand)
            Trigger(CB_CONSEC_EXPANSION,
               StringFormat("3 consecutive candles > %.1f× ATR",
                            Config.CBExpandMultATR));
      }

      // CB3: Price velocity — A320: own check (was an unreachable else-if behind CB1/CB2)
      if(m_state != CB_ACTIVE && m_price_120s_ago > 0)
      {
         double velocity_pips = MathAbs(ctx.current_bid - m_price_120s_ago)
                                / PriceUtils.PipSize();
         if(velocity_pips >= Config.CBVelocityPips)
            Trigger(CB_PRICE_VELOCITY,
               StringFormat("velocity=%.1f pips in 120s", velocity_pips));
      }

      if(m_state == CB_ACTIVE)
      {
         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_CIRCUIT_BREAKER, m_meta.name, m_meta.index,
                             SUSPEND_CIRCUIT_BREAKER,
                             StringFormat("CB just triggered: %s",
                                          EnumToString(m_trigger_type)),
                             "Resumes after cooldown + 5-condition reset");
      }

      return GuardPass(GPRIO_CIRCUIT_BREAKER, m_meta.name, m_meta.index);
   }

   virtual bool CheckResume(const GuardContext &ctx) override
   {
      return (m_state == CB_NORMAL);
   }

   virtual void SaveState() override { WriteCBStateToDisk(); }
   virtual void Shutdown()  override { WriteCBStateToDisk(); m_initialized = false; }
};

#endif // CCIRCUITBREAKER_MQH

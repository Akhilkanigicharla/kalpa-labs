
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Cooldown Manager                        |
//| File: Guards/CCooldownManager.mqh                                 |
//| Purpose: Post-trade and post-loss cooldown enforcement.           |
//|           Adaptive scaling. Deterministic per-day jitter.         |
//| Phase: 2 — Guard Layer / Step 9                                   |
//| GUARD SLOT: 10 (last in chain)                                    |
//+------------------------------------------------------------------+
#ifndef CCOOLDOWNMANAGER_MQH
#define CCOOLDOWNMANAGER_MQH

#include "../Include/Defines.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "../Core/CDailyStats.mqh"
#include "GuardTypes.mqh"

#define COOLDOWN_FILE        "EA_XAUUSD_cooldown.txt"
#define BASE_COOLDOWN_SEC    900     // 15 minutes
#define LOSS_ADDON_1         300     // +5 min after 1st loss
#define LOSS_ADDON_2         600     // +10 min after 2nd loss
#define POST_NEWS_COOLDOWN   1800    // 30 min after news clears
#define JITTER_MAX_PCT       0.20    // ±20% randomization

class CCooldownManager : public IGuard
{
private:
   //--- Trade cooldown state
   datetime  m_trade_close_time;      // When last trade closed
   int       m_trade_cooldown_sec;    // Actual cooldown (with adaptive + jitter)
   bool      m_trade_cooldown_active;

   //--- Post-news cooldown (activated when news guard clears)
   datetime  m_post_news_start;
   bool      m_post_news_active;

   //--- Logging suppression
   bool      m_cooldown_logged;
   bool      m_post_news_logged;

   //=================================================================
   // DETERMINISTIC JITTER
   //
   // RATIONALE: Pure random jitter would produce different values each
   // time Evaluate() is called, causing non-determinism.
   // Instead: jitter is seeded from the trade close TIMESTAMP.
   // Same timestamp = same jitter = deterministic across ticks.
   // Result: cooldown duration is fixed once the trade closes,
   // but varies from trade to trade (looks human).
   //=================================================================
   int ComputeJitteredCooldown(int base_sec, datetime seed_time)
   {
      // Seed from close timestamp — deterministic per trade
      int seed = (int)(seed_time % 100000);
      // Use DeterministicRand — no global MathSrand side effects

      // Jitter: ±JITTER_MAX_PCT of base
      int jitter_range = (int)(base_sec * JITTER_MAX_PCT);
      int jitter       = DeterministicRand(seed, -jitter_range, jitter_range);

      return MathMax(60, base_sec + jitter); // Minimum 60 seconds always
   }

   //--- Calculate adaptive cooldown based on consecutive losses
   int AdaptiveCooldown(datetime close_time)
   {
      int consec = DailyStats.GetConsecLosses();
      int base   = BASE_COOLDOWN_SEC;

      if(consec >= 2) base += LOSS_ADDON_2;
      else if(consec == 1) base += LOSS_ADDON_1;

      return ComputeJitteredCooldown(base, close_time);
   }

   void WriteCooldownStateToDisk()
   {
      int h = FileOpen(COOLDOWN_FILE,
                       FILE_WRITE|FILE_TXT|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE) return;
      FileWriteString(h, StringFormat("trade_close=%d\n",
                                       (long)m_trade_close_time));
      FileWriteString(h, StringFormat("trade_cooldown=%d\n",
                                       m_trade_cooldown_sec));
      FileWriteString(h, StringFormat("trade_active=%d\n",
                                       (int)m_trade_cooldown_active));
      FileWriteString(h, StringFormat("post_news_start=%d\n",
                                       (long)m_post_news_start));
      FileWriteString(h, StringFormat("post_news_active=%d\n",
                                       (int)m_post_news_active));
      FileClose(h);
   }

   void LoadState()
   {
      if(!FileIsExist(COOLDOWN_FILE)) return;
      int h = FileOpen(COOLDOWN_FILE,
                       FILE_READ|FILE_TXT|FILE_SHARE_WRITE|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE) return;
      while(!FileIsEnding(h))
      {
         string line = FileReadString(h);
         StringTrimRight(line);
         StringTrimLeft(line);
         if(StringFind(line, "trade_close=")     == 0)
            m_trade_close_time = (datetime)StringToInteger(StringSubstr(line,12));
         if(StringFind(line, "trade_cooldown=")  == 0)
            m_trade_cooldown_sec = (int)StringToInteger(StringSubstr(line,15));
         if(StringFind(line, "trade_active=")    == 0)
            m_trade_cooldown_active = (StringSubstr(line,13) == "1");
         if(StringFind(line, "post_news_start=") == 0)
            m_post_news_start = (datetime)StringToInteger(StringSubstr(line,16));
         if(StringFind(line, "post_news_active=")== 0)
            m_post_news_active = (StringSubstr(line,17) == "1");
      }
      FileClose(h);

      // Validate: if cooldown already expired during offline, clear it
      if(m_trade_cooldown_active)
      {
         datetime end = m_trade_close_time + m_trade_cooldown_sec;
         if(TimeCurrent() >= end)
         {
            Logger.Info("COOLDOWN",
               "Trade cooldown elapsed while offline — cleared on restart");
            m_trade_cooldown_active = false;
         }
         else
         {
            Logger.Info("COOLDOWN",
               StringFormat("Trade cooldown restored: %ds remaining",
                            (int)(end - TimeCurrent())));
         }
      }

      if(m_post_news_active)
      {
         datetime end = m_post_news_start + POST_NEWS_COOLDOWN;
         if(TimeCurrent() >= end)
         {
            m_post_news_active = false;
            Logger.Info("COOLDOWN",
               "Post-news cooldown elapsed while offline — cleared");
         }
      }
   }

public:
   CCooldownManager() :
      m_trade_close_time(0),
      m_trade_cooldown_sec(BASE_COOLDOWN_SEC),
      m_trade_cooldown_active(false),
      m_post_news_start(0),
      m_post_news_active(false),
      m_cooldown_logged(false),
      m_post_news_logged(false)
   {
      m_meta.index       = 10;
      m_meta.priority    = GPRIO_COOLDOWN;
      m_meta.name        = "COOLDOWN";
      m_meta.description = "Post-trade and post-loss behavioral cooldown";
      m_meta.enabled     = true;
   }

   virtual bool Init() override
   {
      LoadState();
      m_meta.initialized = true;
      m_initialized      = true;
      Logger.Info("COOLDOWN",
         StringFormat("Initialized. base=%ds active=%d post_news=%d",
                      BASE_COOLDOWN_SEC,
                      (int)m_trade_cooldown_active,
                      (int)m_post_news_active));
      return true;
   }

   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();
      datetime now = TimeCurrent();

      //--- Post-news cooldown (runs before trade cooldown — more restrictive)
      if(m_post_news_active)
      {
         datetime end = m_post_news_start + POST_NEWS_COOLDOWN;
         if(now >= end)
         {
            m_post_news_active = false;
            m_post_news_logged = false;
            Logger.Info("COOLDOWN", "Post-news cooldown expired");
            WriteCooldownStateToDisk();
         }
         else
         {
            int remaining = (int)(end - now);
            if(!m_post_news_logged)
            {
               m_post_news_logged = true;
               Logger.Debug("COOLDOWN",
                  StringFormat("Post-news cooldown: %ds remaining", remaining));
            }
            RecordTrigger(GUARD_BLOCK);
            return GuardBlock(GPRIO_COOLDOWN, m_meta.name, m_meta.index,
                              StringFormat("Post-news buffer: %ds remaining",
                                           remaining),
                              "Clears automatically");
         }
      }

      //--- Trade cooldown
      if(m_trade_cooldown_active)
      {
         datetime end = m_trade_close_time + m_trade_cooldown_sec;
         if(now >= end)
         {
            m_trade_cooldown_active = false;
            m_cooldown_logged       = false;
            Logger.Debug("COOLDOWN",
               StringFormat("Trade cooldown expired after %ds",
                            m_trade_cooldown_sec));
            WriteCooldownStateToDisk();
         }
         else
         {
            int remaining = (int)(end - now);
            if(!m_cooldown_logged)
            {
               m_cooldown_logged = true;
               Logger.Debug("COOLDOWN",
                  StringFormat("Trade cooldown: %ds remaining "
                               "(adaptive=%d consec_losses=%d)",
                               remaining, m_trade_cooldown_sec,
                               DailyStats.GetConsecLosses()));
            }
            RecordTrigger(GUARD_BLOCK);
            return GuardBlock(GPRIO_COOLDOWN, m_meta.name, m_meta.index,
                              StringFormat("Trade cooldown: %ds remaining",
                                           remaining),
                              "Clears automatically");
         }
      }

      return GuardPass(GPRIO_COOLDOWN, m_meta.name, m_meta.index);
   }

   virtual bool CheckResume(const GuardContext &ctx) override
   {
      if(m_trade_cooldown_active)
      {
         return (TimeCurrent() >= m_trade_close_time + m_trade_cooldown_sec);
      }
      return true;
   }

   //=================================================================
   // PUBLIC: Called by TradeManager when trade closes
   //=================================================================
   void OnTradeClosed(datetime close_time)
   {
      m_trade_close_time      = close_time;
      m_trade_cooldown_sec    = AdaptiveCooldown(close_time);
      m_trade_cooldown_active = true;
      m_cooldown_logged       = false;

      Logger.Info("COOLDOWN",
         StringFormat("Trade close cooldown started: %ds "
                      "(adaptive for consec_losses=%d)",
                      m_trade_cooldown_sec,
                      DailyStats.GetConsecLosses()));
      WriteCooldownStateToDisk();
   }

   //=================================================================
   // PUBLIC: Called when NewsGuard clears after a news event
   //=================================================================
   void OnNewsCleared()
   {
      m_post_news_start  = TimeCurrent();
      m_post_news_active = true;
      m_post_news_logged = false;
      Logger.Info("COOLDOWN",
         StringFormat("Post-news cooldown started: %ds", POST_NEWS_COOLDOWN));
      WriteCooldownStateToDisk();
   }

   virtual void SaveState() override { WriteCooldownStateToDisk(); }
   virtual void Shutdown() override { WriteCooldownStateToDisk(); m_initialized = false; }
};

#endif // CCOOLDOWNMANAGER_MQH

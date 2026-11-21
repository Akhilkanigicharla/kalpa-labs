
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Session Guard                           |
//| File: Guards/CSessionGuard.mqh                                    |
//| Purpose: Restrict entries to London and NY sessions only.         |
//|           Weekend/Friday lock. GMT validation. Soft boundaries.   |
//| Phase: 2 — Guard Layer / Step 6                                   |
//| GUARD SLOT: 5                                                      |
//+------------------------------------------------------------------+
#ifndef CSESSIONGUARD_MQH
#define CSESSIONGUARD_MQH

#include "../Include/Defines.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "GuardTypes.mqh"

#define SESSION_LONDON_BUFFER_MIN  30   // Skip first 30min of London (spread)
#define FRIDAY_CUTOFF_GMT_HOUR     20   // No entries after 20:00 GMT Friday
#define MONDAY_GRACE_GMT_HOUR       8   // No entries before 08:00 GMT Monday

class CSessionGuard : public IGuard
{
private:
   //--- Soft boundary values (computed once per day)
   int      m_london_end_min_soft;    // London end in minutes-since-midnight
   int      m_ny_start_min_soft;      // NY start in minutes-since-midnight
   int      m_ny_end_min_soft;        // NY end in minutes-since-midnight
   datetime m_soft_boundaries_date;  // Date when soft values were computed
   bool     m_gmt_drift_warned;

   void ComputeSoftBoundaries()
   {
      // Called once per day at day rollover
      // Softens session window edges by a small random amount
      // Seed from current date to be deterministic per day
      MqlDateTime dt;
      TimeToStruct(TimeGMT(), dt);
      int seed = dt.year * 10000 + dt.mon * 100 + dt.day;
      // Use DeterministicRand — no global MathSrand side effects

      int london_end_base = Config.LondonEndHr * 60;
      int ny_start_base   = Config.NyStartHr   * 60;
      int ny_end_base     = Config.NyEndHr     * 60;

      // London end: -15 to +5 minutes (seed+1 for each value to get different sequences)
      m_london_end_min_soft = london_end_base + DeterministicRand(seed+1, -15, 5);
      // NY start: -5 to +15 minutes
      m_ny_start_min_soft   = ny_start_base   + DeterministicRand(seed+2, -5,  15);
      // NY end: -10 to 0 minutes
      m_ny_end_min_soft     = ny_end_base     + DeterministicRand(seed+3, -10, 0);

      m_soft_boundaries_date = TimeGMT();
      Logger.Debug("SESSION",
         StringFormat("Soft boundaries set: "
                      "london_end=%d:%02d ny_start=%d:%02d ny_end=%d:%02d",
                      m_london_end_min_soft/60, m_london_end_min_soft%60,
                      m_ny_start_min_soft/60,   m_ny_start_min_soft%60,
                      m_ny_end_min_soft/60,     m_ny_end_min_soft%60));
   }

   bool IsInSession(int gmt_hour, int gmt_min) const
   {
      int current_min = gmt_hour * 60 + gmt_min;

      // London prime: (start + 30min buffer) to soft end
      int london_start_min = Config.LondonStartHr * 60 + SESSION_LONDON_BUFFER_MIN;
      if(current_min >= london_start_min && current_min < m_london_end_min_soft)
         return true;

      // NY prime: soft start to soft end
      if(current_min >= m_ny_start_min_soft && current_min < m_ny_end_min_soft)
         return true;

      return false;
   }

   void ValidateGMTOffset()
   {
      // Cross-check broker time vs GMT
      int expected_offset = Config.GmtOffset * 3600;
      int actual_offset   = (int)(TimeCurrent() - TimeGMT());
      int drift           = MathAbs(actual_offset - expected_offset);

      if(drift > 3600 && !m_gmt_drift_warned)
      {
         m_gmt_drift_warned = true;
         Logger.Warn("SESSION",
            StringFormat("GMT offset drift detected: "
                         "config_offset=%dh actual_offset=%ds drift=%ds — "
                         "check inp_GmtOffset setting (DST?)",
                         Config.GmtOffset, actual_offset, drift));
      }
   }

public:
   CSessionGuard() :
      m_london_end_min_soft(720),   // Default 12:00
      m_ny_start_min_soft(780),     // Default 13:00
      m_ny_end_min_soft(1020),      // Default 17:00
      m_soft_boundaries_date(0),
      m_gmt_drift_warned(false)
   {
      m_meta.index       = 5;
      m_meta.priority    = GPRIO_SESSION;
      m_meta.name        = "SESSION";
      m_meta.description = "London/NY session filtering";
      m_meta.enabled     = true;
   }

   virtual bool Init() override
   {
      ComputeSoftBoundaries();
      ValidateGMTOffset();
      m_meta.initialized = true;
      m_initialized      = true;
      Logger.Info("SESSION",
         StringFormat("Initialized. london=%d:%02d–%d:%02d ny=%d:%02d–%d:%02d GMT",
                      Config.LondonStartHr, SESSION_LONDON_BUFFER_MIN,
                      m_london_end_min_soft/60, m_london_end_min_soft%60,
                      m_ny_start_min_soft/60, m_ny_start_min_soft%60,
                      m_ny_end_min_soft/60, m_ny_end_min_soft%60));
      return true;
   }

   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();

      // Refresh soft boundaries once per day
      MqlDateTime bd;
      TimeToStruct(m_soft_boundaries_date, bd);
      MqlDateTime td;
      TimeToStruct(ctx.gmt_time, td);
      if(td.day != bd.day || td.mon != bd.mon)
         ComputeSoftBoundaries();

      //--- [S1] Weekend lock
      if(ctx.is_weekend)
      {
         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_SESSION, m_meta.name, m_meta.index,
                             SUSPEND_SESSION_CLOSED,
                             "Weekend — market closed",
                             "Resumes Monday after 08:00 GMT");
      }

      //--- [S2] Monday early morning restriction
      if(ctx.is_monday && ctx.gmt_hour < MONDAY_GRACE_GMT_HOUR)
      {
         RecordTrigger(GUARD_BLOCK);
         return GuardBlock(GPRIO_SESSION, m_meta.name, m_meta.index,
                           StringFormat("Monday pre-open: %02d:%02d GMT, "
                                        "waiting for %d:00",
                                        ctx.gmt_hour, ctx.gmt_minute,
                                        MONDAY_GRACE_GMT_HOUR));
      }

      //--- [S3] Friday late cutoff
      if(ctx.is_friday && ctx.gmt_hour >= FRIDAY_CUTOFF_GMT_HOUR)
      {
         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_SESSION, m_meta.name, m_meta.index,
                             SUSPEND_SESSION_CLOSED,
                             StringFormat("Friday after %d:00 GMT — "
                                          "no new entries before weekend",
                                          FRIDAY_CUTOFF_GMT_HOUR),
                             "Resumes Monday 08:00 GMT");
      }

      //--- [S4] Valid session check
      if(!IsInSession(ctx.gmt_hour, ctx.gmt_minute))
      {
         // BLOCK not SUSPEND — session will open again
         RecordTrigger(GUARD_BLOCK);
         return GuardBlock(GPRIO_SESSION, m_meta.name, m_meta.index,
                           StringFormat("Outside session: %02d:%02d GMT",
                                        ctx.gmt_hour, ctx.gmt_minute),
                           "London 07:30–12:xx or NY 13:xx–17:xx GMT");
      }

      return GuardPass(GPRIO_SESSION, m_meta.name, m_meta.index);
   }

   virtual bool CheckResume(const GuardContext &ctx) override
   {
      if(ctx.is_weekend) return false;
      if(ctx.is_monday && ctx.gmt_hour < MONDAY_GRACE_GMT_HOUR) return false;
      if(ctx.is_friday && ctx.gmt_hour >= FRIDAY_CUTOFF_GMT_HOUR) return false;
      return IsInSession(ctx.gmt_hour, ctx.gmt_minute);
   }
};

//+------------------------------------------------------------------+
//| CRolloverGuard — 21:45 to 00:15 GMT blackout                      |
//| File: Guards/CSessionGuard.mqh (combined for brevity)             |
//| GUARD SLOT: 6                                                      |
//+------------------------------------------------------------------+
class CRolloverGuard : public IGuard
{
private:
   int  m_rollover_start_min; // e.g. 21*60+45 = 1305
   int  m_rollover_end_min;   // e.g. 0*60+15  = 15
   int  m_pre_rollover_min;   // 15 min before start = suppression buffer

   bool IsInRolloverWindow(int gmt_hour, int gmt_min) const
   {
      int current_min = gmt_hour * 60 + gmt_min;
      // Window spans midnight: either >= start OR <= end
      return (current_min >= m_rollover_start_min ||
              current_min <= m_rollover_end_min);
   }

   bool IsPreRollover(int gmt_hour, int gmt_min) const
   {
      int current_min = gmt_hour * 60 + gmt_min;
      int pre_start   = m_rollover_start_min - m_pre_rollover_min;
      return (current_min >= pre_start &&
              current_min < m_rollover_start_min);
   }

public:
   CRolloverGuard() :
      m_rollover_start_min(1305),  // 21:45
      m_rollover_end_min(15),      // 00:15
      m_pre_rollover_min(15)
   {
      m_meta.index       = 6;
      m_meta.priority    = GPRIO_ROLLOVER;
      m_meta.name        = "ROLLOVER";
      m_meta.description = "Rollover blackout 21:45–00:15 GMT";
      m_meta.enabled     = true;
   }

   virtual bool Init() override
   {
      m_rollover_start_min = Config.RolloverStartHr * 60 + Config.RolloverStartMn;
      m_rollover_end_min   = Config.RolloverEndHr   * 60 + Config.RolloverEndMn;

      m_meta.initialized = true;
      m_initialized      = true;
      Logger.Info("ROLLOVER",
         StringFormat("Blackout: %d:%02d – %d:%02d GMT",
                      Config.RolloverStartHr, Config.RolloverStartMn,
                      Config.RolloverEndHr, Config.RolloverEndMn));
      return true;
   }

   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();

      if(IsInRolloverWindow(ctx.gmt_hour, ctx.gmt_minute))
      {
         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_ROLLOVER, m_meta.name, m_meta.index,
                             SUSPEND_ROLLOVER,
                             StringFormat("Rollover blackout: %02d:%02d GMT",
                                          ctx.gmt_hour, ctx.gmt_minute),
                             StringFormat("Resumes after %d:%02d GMT",
                                          Config.RolloverEndHr,
                                          Config.RolloverEndMn));
      }

      if(IsPreRollover(ctx.gmt_hour, ctx.gmt_minute))
      {
         RecordTrigger(GUARD_BLOCK);
         return GuardBlock(GPRIO_ROLLOVER, m_meta.name, m_meta.index,
                           StringFormat("Pre-rollover buffer: %02d:%02d GMT "
                                        "(rollover starts %d:%02d)",
                                        ctx.gmt_hour, ctx.gmt_minute,
                                        Config.RolloverStartHr,
                                        Config.RolloverStartMn));
      }

      return GuardPass(GPRIO_ROLLOVER, m_meta.name, m_meta.index);
   }

   virtual bool CheckResume(const GuardContext &ctx) override
   {
      return (!IsInRolloverWindow(ctx.gmt_hour, ctx.gmt_minute) &&
              !IsPreRollover(ctx.gmt_hour, ctx.gmt_minute));
   }
};

#endif // CSESSIONGUARD_MQH


//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Spread Guard                            |
//| File: Guards/CSpreadGuard.mqh                                     |
//| Purpose: Dynamic spread threshold calibration, real RR check,    |
//|           spike detection. Provides spread data to NewsGuard.     |
//| Phase: 2 — Guard Layer / Step 7                                   |
//| GUARD SLOT: 8                                                      |
//|                                                                    |
//| THREE STAGES:                                                      |
//|   Stage 1: Hard cap fallback (always available, 25 pips)          |
//|   Stage 2: Dynamic threshold = session_p95 × 1.3 (after 3 days)  |
//|   Stage 3: Real RR gate (requires SL/TP from entry engine)        |
//|                                                                    |
//| CALIBRATION:                                                       |
//|   Spread sampled every 60s via timer → OnTimer() hook             |
//|   7-day rolling database, per session per hour                    |
//|   Persisted to spread_calibration.txt on shutdown                 |
//+------------------------------------------------------------------+
#ifndef CSPREADGUARD_MQH
#define CSPREADGUARD_MQH

#include "../Include/Defines.mqh"
#include "../Include/PriceUtils.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "GuardTypes.mqh"

#define SPREAD_CALIB_FILE      "EA_XAUUSD_spread_calib.txt"
#define SPREAD_SESSION_COUNT   6    // SESSION_ASIAN through SESSION_ROLLOVER
#define SPREAD_HOUR_COUNT      24
#define SPREAD_WARMUP_DAYS     3
#define SPREAD_SPIKE_LOG_MIN   30   // Only log spike if lasts > 30 seconds
#define SPREAD_P95_PERCENTILE  0.95

class CSpreadGuard : public IGuard
{
private:
   //--- Calibration database: [session_index][hour] = sample data
   //    Pre-allocated fixed arrays — no dynamic resize during runtime
   double   m_sum_spread[SPREAD_SESSION_COUNT][SPREAD_HOUR_COUNT];
   double   m_sum_sq_spread[SPREAD_SESSION_COUNT][SPREAD_HOUR_COUNT];
   double   m_min_spread[SPREAD_SESSION_COUNT][SPREAD_HOUR_COUNT];
   double   m_max_spread[SPREAD_SESSION_COUNT][SPREAD_HOUR_COUNT];
   int      m_sample_count[SPREAD_SESSION_COUNT][SPREAD_HOUR_COUNT];
   datetime m_first_sample_time; // When calibration started

   //--- Dynamic threshold (computed from calibration)
   double   m_dynamic_threshold;
   bool     m_calibrated;
   SPREAD_CALIB_CONFIDENCE m_confidence;

   //--- Spike tracking
   double   m_last_spread;
   datetime m_spike_start;
   bool     m_spike_active;
   bool     m_spike_logged;

   //--- Real RR gate (set by entry engine before guard runs)
   double   m_pending_sl_pips;
   double   m_pending_tp2_pips;
   bool     m_rr_check_pending;

   //--- ATR tracking (for NewsGuard access)
   double   m_sum_atr[SPREAD_SESSION_COUNT][SPREAD_HOUR_COUNT];
   int      m_atr_count[SPREAD_SESSION_COUNT][SPREAD_HOUR_COUNT];
   double   m_last_atr_m5;

   //--- Get session index from SESSION_STATE enum (0-based)
   int SessionIndex(SESSION_STATE sess) const
   {
      int idx = (int)sess;
      return (idx >= 0 && idx < SPREAD_SESSION_COUNT) ? idx : 0;
   }

   //--- Compute p95 from running stats (approximate using max and avg)
   //    True p95 requires storing all samples — we use a reasonable approximation:
   //    p95 ≈ avg + 1.65 × stddev (assuming roughly normal distribution)
   double ComputeP95(int sess, int hour) const
   {
      int n = m_sample_count[sess][hour];
      if(n < 2) return m_max_spread[sess][hour];

      double avg = m_sum_spread[sess][hour] / n;
      double variance = (m_sum_sq_spread[sess][hour] / n) - (avg * avg);
      double stddev = (variance > 0) ? MathSqrt(variance) : 0;
      double p95 = avg + 1.65 * stddev;

      // Cap at max observed (p95 can't exceed what we've seen)
      return MathMin(p95, m_max_spread[sess][hour]);
   }

   //--- Get session and hour from context
   void GetSessionHour(const GuardContext &ctx,
                       int &sess_idx, int &hour) const
   {
      // Derive SESSION_STATE from time — simplified version
      // Full SessionGuard handles this properly; here we just need the bucket
      int gmt_min = ctx.gmt_hour * 60 + ctx.gmt_minute;
      SESSION_STATE sess;
      if(gmt_min >= 1305 || gmt_min <= 15) sess = SESSION_ROLLOVER;
      else if(gmt_min <= 300)              sess = SESSION_ASIAN;
      else if(gmt_min <= 420)             sess = SESSION_PRE_LONDON;
      else if(gmt_min <= 720)             sess = SESSION_LONDON_PRIME;
      else if(gmt_min <= 780)             sess = SESSION_INTER;
      else if(gmt_min <= 1020)            sess = SESSION_NY_PRIME;
      else                                 sess = SESSION_POST_NY;

      sess_idx = SessionIndex(sess);
      hour     = ctx.gmt_hour;
   }

   //--- Update dynamic threshold from current session's calibration
   void UpdateDynamicThreshold(int sess_idx, int hour)
   {
      double p95 = ComputeP95(sess_idx, hour);
      if(p95 > 0 && p95 < 200) // Sanity bounds
      {
         // A336 (#21): calibration may only TIGHTEN the cap. Old code floored at 10 pips ($10 on
         // gold) and capped at 1.5x the hard cap, so once calibrated it was always 1.5x looser.
         m_dynamic_threshold = MathMin(MathMax(p95 * 1.3, 0.2), Config.SpreadHardCap);
      }
      else
      {
         m_dynamic_threshold = Config.SpreadHardCap;
      }
   }

   //--- Check calibration confidence
   void UpdateConfidence()
   {
      if(m_first_sample_time == 0)
      {
         m_confidence  = CALIB_NONE;
         m_calibrated  = false;
         return;
      }

      int days_of_data = (int)((TimeCurrent() - m_first_sample_time) / 86400);

      if(days_of_data >= 7)       m_confidence = CALIB_OPTIMAL;
      else if(days_of_data >= 3)  m_confidence = CALIB_SUFFICIENT;
      else if(days_of_data >= 1)  m_confidence = CALIB_PARTIAL;
      else                         m_confidence = CALIB_NONE;

      m_calibrated = (m_confidence >= CALIB_SUFFICIENT);
   }

   //=================================================================
   // PERSISTENCE: Save calibration to disk
   //=================================================================
   void SaveCalibration()
   {
      int h = FileOpen(SPREAD_CALIB_FILE,
                       FILE_WRITE|FILE_TXT|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE)
      {
         Logger.Warn("SPREAD", "Cannot save spread calibration");
         return;
      }

      // Header
      FileWriteString(h, StringFormat("first_sample=%d\n",
                                       (long)m_first_sample_time));

      // Data rows: sess,hour,n,sum,sum_sq,min,max,sum_atr,atr_n
      for(int s = 0; s < SPREAD_SESSION_COUNT; s++)
      {
         for(int hr = 0; hr < SPREAD_HOUR_COUNT; hr++)
         {
            if(m_sample_count[s][hr] == 0) continue;
            FileWriteString(h, StringFormat(
               "d,%d,%d,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%d\n",
               s, hr,
               m_sample_count[s][hr],
               m_sum_spread[s][hr],
               m_sum_sq_spread[s][hr],
               m_min_spread[s][hr],
               m_max_spread[s][hr],
               m_sum_atr[s][hr],
               m_atr_count[s][hr]
            ));
         }
      }
      FileClose(h);
      Logger.Debug("SPREAD", "Calibration saved");
   }

   void LoadCalibration()
   {
      if(!FileIsExist(SPREAD_CALIB_FILE)) return;

      int h = FileOpen(SPREAD_CALIB_FILE,
                       FILE_READ|FILE_TXT|FILE_SHARE_WRITE|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE) return;

      int loaded = 0;
      while(!FileIsEnding(h))
      {
         string line = FileReadString(h);
         StringTrimRight(line);
         StringTrimLeft(line);
         if(StringLen(line) == 0) continue;

         if(StringFind(line, "first_sample=") == 0)
         {
            m_first_sample_time = (datetime)StringToInteger(
               StringSubstr(line, 13));
            continue;
         }

         if(line[0] != 'd') continue;

         string parts[];
         int n_parts = StringSplit(line, ',', parts);
         if(n_parts < 10) continue;

         int s    = (int)StringToInteger(parts[1]);
         int hr   = (int)StringToInteger(parts[2]);
         if(s < 0 || s >= SPREAD_SESSION_COUNT) continue;
         if(hr < 0 || hr >= SPREAD_HOUR_COUNT)  continue;

         m_sample_count[s][hr]   = (int)StringToInteger(parts[3]);
         m_sum_spread[s][hr]     = StringToDouble(parts[4]);
         m_sum_sq_spread[s][hr]  = StringToDouble(parts[5]);
         m_min_spread[s][hr]     = StringToDouble(parts[6]);
         m_max_spread[s][hr]     = StringToDouble(parts[7]);
         m_sum_atr[s][hr]        = StringToDouble(parts[8]);
         m_atr_count[s][hr]      = (int)StringToInteger(parts[9]);
         loaded++;
      }
      FileClose(h);

      if(loaded > 0)
      {
         UpdateConfidence();
         Logger.Info("SPREAD",
            StringFormat("Calibration loaded: %d cells, confidence=%s",
                         loaded, EnumToString(m_confidence)));
      }
   }

public:
   CSpreadGuard() :
      m_dynamic_threshold(25.0),
      m_calibrated(false),
      m_confidence(CALIB_NONE),
      m_first_sample_time(0),
      m_last_spread(0),
      m_spike_start(0),
      m_spike_active(false),
      m_spike_logged(false),
      m_pending_sl_pips(0),
      m_pending_tp2_pips(0),
      m_rr_check_pending(false),
      m_last_atr_m5(0)
   {
      // Zero all calibration arrays
      ArrayInitialize(m_sum_spread,    0);
      ArrayInitialize(m_sum_sq_spread, 0);
      ArrayInitialize(m_min_spread,    999);
      ArrayInitialize(m_max_spread,    0);
      ArrayInitialize(m_sample_count,  0);
      ArrayInitialize(m_sum_atr,       0);
      ArrayInitialize(m_atr_count,     0);

      m_meta.index       = 8;
      m_meta.priority    = GPRIO_SPREAD;
      m_meta.name        = "SPREAD";
      m_meta.description = "Dynamic spread calibration and real RR validation";
      m_meta.enabled     = true;
   }

   virtual bool Init() override
   {
      LoadCalibration();
      m_meta.initialized = true;
      m_initialized      = true;
      Logger.Info("SPREAD",
         StringFormat("Initialized. hard_cap=%.1f calibrated=%d "
                      "confidence=%s dynamic_threshold=%.1f",
                      Config.SpreadHardCap, (int)m_calibrated,
                      EnumToString(m_confidence), m_dynamic_threshold));
      return true;
   }

   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();
      double spread = ctx.current_spread_pips;

      int sess_idx, hour;
      GetSessionHour(ctx, sess_idx, hour);
      UpdateDynamicThreshold(sess_idx, hour);

      //--- Determine applicable threshold
      double threshold = m_calibrated
                         ? m_dynamic_threshold
                         : Config.SpreadHardCap;

      //--- Spike detection (track duration)
      double session_avg = GetSessionAvgSpread(ctx);
      bool is_spike = (session_avg > 0 &&
                       spread > (session_avg * SPREAD_SPIKE_RATIO));

      if(is_spike && !m_spike_active)
      {
         m_spike_active = true;
         m_spike_start  = TimeCurrent();
         m_spike_logged = false;
      }
      else if(!is_spike && m_spike_active)
      {
         int duration = (int)(TimeCurrent() - m_spike_start);
         if(duration >= SPREAD_SPIKE_LOG_MIN)
         {
            Logger.Warn("SPREAD",
               StringFormat("Spread spike ended: duration=%ds peak=%.1f avg=%.1f",
                            duration, m_last_spread, session_avg));
         }
         m_spike_active = false;
         m_spike_logged = false;
      }

      if(m_spike_active)
      {
         int spike_dur = (int)(TimeCurrent() - m_spike_start);
         if(!m_spike_logged && spike_dur >= SPREAD_SPIKE_LOG_MIN)
         {
            m_spike_logged = true;
            Logger.Warn("SPREAD",
               StringFormat("SPREAD_SPIKE: current=%.1f avg=%.1f "
                            "ratio=%.1f duration=%ds",
                            spread, session_avg,
                            (session_avg > 0) ? spread/session_avg : 0,
                            spike_dur));
         }
      }

      m_last_spread = spread;

      //--- Stage 1 + 2: Spread threshold check
      if(spread > threshold)
      {
         RecordTrigger(GUARD_BLOCK);
         return GuardBlock(GPRIO_SPREAD, m_meta.name, m_meta.index,
                           StringFormat("Spread %.1f pips > threshold %.1f "
                                        "(calibrated=%d)",
                                        spread, threshold,
                                        (int)m_calibrated),
                           "Clears when spread normalises");
      }

      //--- Stage 3: Real RR validation (only when entry engine has set values)
      if(m_rr_check_pending && m_pending_sl_pips > 0 && m_pending_tp2_pips > 0)
      {
         double real_rr = RealRR(spread, m_pending_sl_pips, m_pending_tp2_pips);
         if(real_rr < Config.RealRRMin)
         {
            RecordTrigger(GUARD_BLOCK);
            return GuardBlock(GPRIO_SPREAD, m_meta.name, m_meta.index,
                              StringFormat("Real RR %.2f < min %.2f "
                                           "(spread=%.1f sl=%.1f tp2=%.1f)",
                                           real_rr, Config.RealRRMin,
                                           spread,
                                           m_pending_sl_pips,
                                           m_pending_tp2_pips),
                              "Clears when spread reduces or setup changes");
         }
         // Clear the pending check after evaluation
         m_rr_check_pending = false;
      }

      return GuardPass(GPRIO_SPREAD, m_meta.name, m_meta.index);
   }

   virtual bool CheckResume(const GuardContext &ctx) override
   {
      double threshold = m_calibrated
                         ? m_dynamic_threshold
                         : Config.SpreadHardCap;
      return (ctx.current_spread_pips <= threshold);
   }

   //=================================================================
   // OnTimer hook — called every 60 seconds to sample spread + ATR
   //=================================================================
   void OnTimerSample(const GuardContext &ctx, double atr_m5_pips)
   {
      if(ctx.is_weekend) return;

      int sess_idx, hour;
      GetSessionHour(ctx, sess_idx, hour);

      double spread = ctx.current_spread_pips;
      if(spread <= 0 || spread > 200) return; // Reject bad samples

      if(m_first_sample_time == 0)
         m_first_sample_time = TimeCurrent();

      // Update running statistics
      m_sample_count[sess_idx][hour]++;
      m_sum_spread[sess_idx][hour]    += spread;
      m_sum_sq_spread[sess_idx][hour] += spread * spread;
      m_min_spread[sess_idx][hour]    = MathMin(m_min_spread[sess_idx][hour],
                                                 spread);
      m_max_spread[sess_idx][hour]    = MathMax(m_max_spread[sess_idx][hour],
                                                 spread);

      // ATR tracking (for NewsGuard)
      if(atr_m5_pips > 0 && atr_m5_pips < 200)
      {
         m_sum_atr[sess_idx][hour]  += atr_m5_pips;
         m_atr_count[sess_idx][hour]++;
         m_last_atr_m5 = atr_m5_pips;
      }

      // Update confidence periodically
      if(m_sample_count[sess_idx][hour] % 60 == 0)
         UpdateConfidence();
   }

   //=================================================================
   // PUBLIC INTERFACE for NewsGuard and CircuitBreaker
   //=================================================================
   double GetSessionAvgSpread(const GuardContext &ctx) const
   {
      int sess_idx, hour;
      GetSessionHour(ctx, sess_idx, hour);
      int n = m_sample_count[sess_idx][hour];
      if(n == 0) return Config.SpreadHardCap / 2.0; // Fallback estimate
      return m_sum_spread[sess_idx][hour] / n;
   }

   double GetSessionAvgATR(const GuardContext &ctx) const
   {
      int sess_idx, hour;
      GetSessionHour(ctx, sess_idx, hour);
      int n = m_atr_count[sess_idx][hour];
      if(n == 0) return 15.0; // Fallback: assume 15-pip ATR
      return m_sum_atr[sess_idx][hour] / n;
   }

   bool IsSpikingNow() const { return m_spike_active; }
   bool IsCalibrated() const { return m_calibrated; }
   SPREAD_CALIB_CONFIDENCE GetConfidence() const { return m_confidence; }
   double GetDynamicThreshold() const { return m_dynamic_threshold; }
   double GetLastATR() const { return m_last_atr_m5; }

   //--- Called by EntryEngine before guard evaluation to enable Stage 3
   void SetPendingRRCheck(double sl_pips, double tp2_pips)
   {
      m_pending_sl_pips  = sl_pips;
      m_pending_tp2_pips = tp2_pips;
      m_rr_check_pending = (sl_pips > 0 && tp2_pips > 0);
   }

   //--- Real RR calculation (static utility — also used by EntryEngine)
   static double RealRR(double spread_pips, double sl_pips, double tp2_pips)
   {
      double real_sl  = sl_pips  + spread_pips;  // Spread widens loss side
      double real_tp2 = tp2_pips - spread_pips;  // Spread narrows gain side
      if(real_sl <= 0) return 0;
      return real_tp2 / real_sl;
   }

   virtual void SaveState() override { SaveCalibration(); }
   virtual void LoadState() override { LoadCalibration(); }

   virtual void Shutdown() override
   {
      SaveCalibration();
      m_initialized = false;
   }
};

#endif // CSPREADGUARD_MQH


//+------------------------------------------------------------------+
//| XAUUSD Institutional EA - Regime Persistence Model                |
//| File: Intelligence/CRegimePersistenceModel.mqh                    |
//| Purpose: Anti-whipsaw filter on RegimeEngine output. Enforces     |
//|           confirmation requirements before adopting regime changes.|
//|           Maintains regime age, transition state, sizing hints.   |
//| Phase: 3 - Step 5                                                 |
//|                                                                    |
//| THIS IS NOT AN ENGINE.                                            |
//|   It consumes one RegimeResult, produces one RegimePersistenceResult.|
//|   Its own Update(regime_result) signature, not Evaluate(ctx).     |
//|                                                                    |
//| TRANSITION RULES:                                                  |
//|   Startup:              2 consecutive H4 bars before first adopt  |
//|   Trending -> Ranging:  3 consecutive H4 bars weak score          |
//|   Ranging  -> Trending: 2 consecutive H4 bars strong score        |
//|   BULL <-> BEAR direct: FORBIDDEN - forced pass-through RANGING   |
//|   Transition timeout:   3 H4 bars max, defaults to RANGING        |
//|                                                                    |
//| OUTPUT (sizing/threshold are POLICY RECOMMENDATIONS, Phase 4/5    |
//|   may override):                                                  |
//|   sizing_multiplier:    1.0 confirmed, 0.5 transitioning          |
//|   score_threshold_adj:  0.0 confirmed, +1.0 transitioning         |
//|                                                                    |
//| STRICT BOUNDARIES: no broker calls, no sizing decisions,          |
//|   no execution, no trade signals.                                 |
//+------------------------------------------------------------------+
#ifndef CREGIMEPERSISTENCEMODEL_MQH
#define CREGIMEPERSISTENCEMODEL_MQH

#include "IntelligenceTypes.mqh"
#include "../Core/CLogger.mqh"

//===================================================================
// TRANSITION_STATE - internal state machine
//===================================================================
enum TRANSITION_STATE
{
   TRANS_CONFIRMED       = 0,
   TRANS_PENDING_RANGE   = 1,
   TRANS_PENDING_TREND   = 2,
   TRANS_FORCED_RANGE    = 3
};

class CRegimePersistenceModel
{
private:
   REGIME_STATE     m_confirmed_regime;
   TRADE_DIR        m_confirmed_direction;
   datetime         m_regime_anchor_time;
   int              m_regime_age_bars;

   TRANSITION_STATE m_transition_state;
   REGIME_STATE     m_transition_target;
   TRADE_DIR        m_transition_target_dir;
   int              m_transition_bar_count;
   datetime         m_transition_start_time;

   int              m_score_history[PERSIST_HISTORY_MAX];
   REGIME_STATE     m_regime_history[PERSIST_HISTORY_MAX];
   int              m_history_write_idx;
   int              m_history_count;

   datetime         m_last_processed_h4_bar;

   RegimePersistenceResult m_cached;
   bool             m_cache_valid;

   bool             m_initialized;
   int              m_update_count;
   int              m_confirmed_changes;
   int              m_blocked_flips;

   double           m_stability_score;

   REGIME_STATE     m_startup_pending_regime;
   TRADE_DIR        m_startup_pending_direction;
   int              m_startup_confirmation_bars;

   //--- Classification helpers
   bool IsTrending(REGIME_STATE r) const
   { return (r == REGIME_TRENDING_BULL || r == REGIME_TRENDING_BEAR); }
   bool IsRanging(REGIME_STATE r) const
   { return (r == REGIME_RANGING || r == REGIME_UNKNOWN); }
   bool IsWeak(REGIME_STATE r) const
   { return (r == REGIME_WEAK_BULL || r == REGIME_WEAK_BEAR); }
   bool IsBullish(REGIME_STATE r) const
   { return (r == REGIME_TRENDING_BULL || r == REGIME_WEAK_BULL); }
   bool IsBearish(REGIME_STATE r) const
   { return (r == REGIME_TRENDING_BEAR || r == REGIME_WEAK_BEAR); }
   bool IsDirectFlip(REGIME_STATE from, REGIME_STATE to) const
   {
      if(IsBullish(from) && IsBearish(to)) return true;
      if(IsBearish(from) && IsBullish(to)) return true;
      return false;
   }
   bool ScoreSupportsTrending(int raw_score) const { return (raw_score >= 4); }
   bool ScoreSupportsRanging(int raw_score) const { return (raw_score <= 2); }

   //--- Explicit enum validation
   bool IsValidRegimeValue(int v) const
   {
      switch(v)
      {
         case REGIME_RANGING:
         case REGIME_WEAK_BULL:
         case REGIME_WEAK_BEAR:
         case REGIME_TRENDING_BULL:
         case REGIME_TRENDING_BEAR:
         case REGIME_TRANSITIONING:
         case REGIME_UNKNOWN:
            return true;
         default: return false;
      }
   }
   bool IsValidDirectionValue(int v) const
   {
      switch(v)
      {
         case DIR_LONG:
         case DIR_SHORT:
         case DIR_NONE:
            return true;
         default: return false;
      }
   }
   bool IsValidTransitionState(int v) const
   {
      switch(v)
      {
         case TRANS_CONFIRMED:
         case TRANS_PENDING_RANGE:
         case TRANS_PENDING_TREND:
         case TRANS_FORCED_RANGE:
            return true;
         default: return false;
      }
   }

   void PushHistory(int raw_score, REGIME_STATE raw_regime)
   {
      m_score_history[m_history_write_idx]  = raw_score;
      m_regime_history[m_history_write_idx] = raw_regime;
      m_history_write_idx = (m_history_write_idx + 1) % PERSIST_HISTORY_MAX;
      if(m_history_count < PERSIST_HISTORY_MAX) m_history_count++;
   }

   double ComputeStabilityScore() const
   {
      if(m_history_count < 2) return 0.0;
      int examined = MathMin(m_history_count, 10);
      int matches = 0;
      for(int i = 0; i < examined; i++)
      {
         int idx = (m_history_write_idx - 1 - i + PERSIST_HISTORY_MAX) % PERSIST_HISTORY_MAX;
         REGIME_STATE r = m_regime_history[idx];
         if(IsBullish(r) && IsBullish(m_confirmed_regime)) matches++;
         else if(IsBearish(r) && IsBearish(m_confirmed_regime)) matches++;
         else if(IsRanging(r) && IsRanging(m_confirmed_regime)) matches++;
      }
      return (double)matches / (double)examined;
   }

   void BuildResult(const RegimeResult &raw, bool just_changed, bool direction_flipped)
   {
      RegimePersistenceResult r;
      ZeroMemory(r);
      r.confirmed_regime    = m_confirmed_regime;
      r.raw_regime          = raw.regime;
      r.confirmed_direction = m_confirmed_direction;
      r.in_transition       = (m_transition_state != TRANS_CONFIRMED);
      r.transition_bars     = m_transition_bar_count;
      r.regime_age_bars     = m_regime_age_bars;
      r.regime_age_hours    = m_regime_age_bars * 4;
      r.is_aging            = (m_regime_age_bars >= REGIME_AGING_BARS);
      r.just_changed        = just_changed;
      r.direction_flipped   = direction_flipped;

      if(r.in_transition)
      {
         r.sizing_multiplier   = PERSIST_TRANSITION_SIZING;
         r.score_threshold_adj = PERSIST_THRESHOLD_TRANSITION;
      }
      else
      {
         r.sizing_multiplier   = PERSIST_NORMAL_SIZING;
         r.score_threshold_adj = PERSIST_THRESHOLD_NORMAL;
      }

      r.evaluated_at = TimeCurrent();
      r.is_valid     = (m_confirmed_regime != REGIME_UNKNOWN) || just_changed;

      m_cached      = r;
      m_cache_valid = true;
   }

   void ConfirmRegime(REGIME_STATE new_regime, TRADE_DIR new_dir, string reason)
   {
      REGIME_STATE old = m_confirmed_regime;
      m_confirmed_regime       = new_regime;
      m_confirmed_direction    = new_dir;
      m_regime_anchor_time     = TimeCurrent();
      m_regime_age_bars        = 0;
      m_transition_state       = TRANS_CONFIRMED;
      m_transition_target      = new_regime;
      m_transition_target_dir  = new_dir;
      m_transition_bar_count   = 0;
      m_transition_start_time  = 0;
      m_confirmed_changes++;
      Logger.Info("REGIME_PERSIST",
         StringFormat("REGIME CONFIRMED: %s -> %s (%s). reason=%s",
                       EnumToString(old), EnumToString(new_regime),
                       EnumToString(new_dir), reason));
      SaveState();
   }

   void StartTransition(TRANSITION_STATE state, REGIME_STATE target,
                        TRADE_DIR target_dir, string reason)
   {
      m_transition_state      = state;
      m_transition_target     = target;
      m_transition_target_dir = target_dir;
      m_transition_bar_count  = 1;
      m_transition_start_time = TimeCurrent();
      Logger.Info("REGIME_PERSIST",
         StringFormat("TRANSITION STARTED: state=%s target=%s reason=%s",
                       EnumToString(state), EnumToString(target), reason));
   }

   void AbortTransition(string reason)
   {
      Logger.Debug("REGIME_PERSIST",
         StringFormat("Transition aborted after %d bars. reason=%s",
                       m_transition_bar_count, reason));
      m_transition_state      = TRANS_CONFIRMED;
      m_transition_bar_count  = 0;
      m_transition_start_time = 0;
   }

   void SaveState()
   {
      int h = FileOpen(PERSIST_FILE_NAME, FILE_WRITE|FILE_TXT|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE)
      {
         Logger.Warn("REGIME_PERSIST",
            StringFormat("SaveState: cannot open %s. err=%d",
                          PERSIST_FILE_NAME, GetLastError()));
         return;
      }
      FileWriteString(h, StringFormat("confirmed_regime=%d\n", (int)m_confirmed_regime));
      FileWriteString(h, StringFormat("confirmed_direction=%d\n", (int)m_confirmed_direction));
      FileWriteString(h, StringFormat("anchor_time=%d\n", (long)m_regime_anchor_time));
      FileWriteString(h, StringFormat("age_bars=%d\n", m_regime_age_bars));
      FileWriteString(h, StringFormat("transition_state=%d\n", (int)m_transition_state));
      FileWriteString(h, StringFormat("transition_target=%d\n", (int)m_transition_target));
      FileWriteString(h, StringFormat("transition_target_dir=%d\n", (int)m_transition_target_dir));
      FileWriteString(h, StringFormat("transition_bar_count=%d\n", m_transition_bar_count));
      FileWriteString(h, StringFormat("last_processed_h4_bar=%d\n", (long)m_last_processed_h4_bar));
      FileWriteString(h, StringFormat("saved_at=%d\n", (long)TimeCurrent()));
      FileClose(h);
   }

   void LoadState()
   {
      if(!FileIsExist(PERSIST_FILE_NAME))
      {
         Logger.Info("REGIME_PERSIST", "No prior state file - starting fresh");
         return;
      }
      int h = FileOpen(PERSIST_FILE_NAME,
                        FILE_READ|FILE_TXT|FILE_SHARE_WRITE|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE)
      {
         Logger.Warn("REGIME_PERSIST",
            StringFormat("LoadState: cannot open %s. err=%d",
                          PERSIST_FILE_NAME, GetLastError()));
         return;
      }

      int tmp_regime = (int)REGIME_UNKNOWN;
      int tmp_dir    = (int)DIR_NONE;
      datetime tmp_anchor = 0;
      int tmp_age = 0;
      int tmp_trans_state = (int)TRANS_CONFIRMED;
      int tmp_trans_target = (int)REGIME_UNKNOWN;
      int tmp_trans_target_dir = (int)DIR_NONE;
      int tmp_trans_count = 0;
      datetime tmp_last_bar = 0;
      datetime tmp_saved_at = 0;

      while(!FileIsEnding(h))
      {
         string line = FileReadString(h);
         StringTrimRight(line);
         StringTrimLeft(line);
         if(StringLen(line) == 0) continue;
         if(StringFind(line, "confirmed_regime=") == 0)
            tmp_regime = (int)StringToInteger(StringSubstr(line, 17));
         else if(StringFind(line, "confirmed_direction=") == 0)
            tmp_dir = (int)StringToInteger(StringSubstr(line, 20));
         else if(StringFind(line, "anchor_time=") == 0)
            tmp_anchor = (datetime)StringToInteger(StringSubstr(line, 12));
         else if(StringFind(line, "age_bars=") == 0)
            tmp_age = (int)StringToInteger(StringSubstr(line, 9));
         else if(StringFind(line, "transition_state=") == 0)
            tmp_trans_state = (int)StringToInteger(StringSubstr(line, 17));
         else if(StringFind(line, "transition_target_dir=") == 0)
            tmp_trans_target_dir = (int)StringToInteger(StringSubstr(line, 22));
         else if(StringFind(line, "transition_target=") == 0)
            tmp_trans_target = (int)StringToInteger(StringSubstr(line, 18));
         else if(StringFind(line, "transition_bar_count=") == 0)
            tmp_trans_count = (int)StringToInteger(StringSubstr(line, 21));
         else if(StringFind(line, "last_processed_h4_bar=") == 0)
            tmp_last_bar = (datetime)StringToInteger(StringSubstr(line, 22));
         else if(StringFind(line, "saved_at=") == 0)
            tmp_saved_at = (datetime)StringToInteger(StringSubstr(line, 9));
      }
      FileClose(h);

      int file_age = (int)(TimeCurrent() - tmp_saved_at);
      if(tmp_saved_at == 0 || file_age > PERSIST_FILE_MAX_AGE_SEC)
      {
         Logger.Warn("REGIME_PERSIST",
            StringFormat("State file age=%ds > max=%ds - discarding",
                          file_age, PERSIST_FILE_MAX_AGE_SEC));
         return;
      }

      if(!IsValidRegimeValue(tmp_regime)) { Logger.Warn("REGIME_PERSIST", "Bad regime val"); return; }
      if(!IsValidDirectionValue(tmp_dir)) { Logger.Warn("REGIME_PERSIST", "Bad dir val"); return; }
      if(!IsValidTransitionState(tmp_trans_state)) { Logger.Warn("REGIME_PERSIST", "Bad trans state"); return; }
      if(!IsValidRegimeValue(tmp_trans_target)) { Logger.Warn("REGIME_PERSIST", "Bad trans target"); return; }
      if(!IsValidDirectionValue(tmp_trans_target_dir)) { Logger.Warn("REGIME_PERSIST", "Bad trans dir"); return; }
      if(tmp_age < 0 || tmp_age > 10000) { Logger.Warn("REGIME_PERSIST", "Bad age"); return; }
      if(tmp_trans_count < 0 || tmp_trans_count > 100) { Logger.Warn("REGIME_PERSIST", "Bad count"); return; }

      m_confirmed_regime       = (REGIME_STATE)tmp_regime;
      m_confirmed_direction    = (TRADE_DIR)tmp_dir;
      m_regime_anchor_time     = tmp_anchor;
      m_regime_age_bars        = tmp_age;
      m_transition_state       = (TRANSITION_STATE)tmp_trans_state;
      m_transition_target      = (REGIME_STATE)tmp_trans_target;
      m_transition_target_dir  = (TRADE_DIR)tmp_trans_target_dir;
      m_transition_bar_count   = tmp_trans_count;
      m_last_processed_h4_bar  = tmp_last_bar;

      Logger.Info("REGIME_PERSIST",
         StringFormat("State restored: regime=%s dir=%s age=%d trans=%s file_age=%ds",
                       EnumToString(m_confirmed_regime),
                       EnumToString(m_confirmed_direction),
                       m_regime_age_bars,
                       EnumToString(m_transition_state), file_age));
   }

public:
   CRegimePersistenceModel() :
      m_confirmed_regime(REGIME_UNKNOWN),
      m_confirmed_direction(DIR_NONE),
      m_regime_anchor_time(0),
      m_regime_age_bars(0),
      m_transition_state(TRANS_CONFIRMED),
      m_transition_target(REGIME_UNKNOWN),
      m_transition_target_dir(DIR_NONE),
      m_transition_bar_count(0),
      m_transition_start_time(0),
      m_history_write_idx(0),
      m_history_count(0),
      m_last_processed_h4_bar(0),
      m_cache_valid(false),
      m_initialized(false),
      m_update_count(0),
      m_confirmed_changes(0),
      m_blocked_flips(0),
      m_stability_score(0.0),
      m_startup_pending_regime(REGIME_UNKNOWN),
      m_startup_pending_direction(DIR_NONE),
      m_startup_confirmation_bars(0)
   {
      ArrayInitialize(m_score_history, 0);
      for(int i = 0; i < PERSIST_HISTORY_MAX; i++)
         m_regime_history[i] = REGIME_UNKNOWN;
      ZeroMemory(m_cached);
      m_cached.confirmed_regime    = REGIME_UNKNOWN;
      m_cached.confirmed_direction = DIR_NONE;
      m_cached.sizing_multiplier   = PERSIST_TRANSITION_SIZING;
      m_cached.score_threshold_adj = PERSIST_THRESHOLD_TRANSITION;
      m_cached.is_valid            = false;
   }

   bool Init()
   {
      LoadState();
      m_initialized  = true;
      m_update_count = 0;
      Logger.Info("REGIME_PERSIST",
         StringFormat("Initialized. confirmed=%s dir=%s age=%d startup_bars=%d",
                       EnumToString(m_confirmed_regime),
                       EnumToString(m_confirmed_direction),
                       m_regime_age_bars,
                       PERSIST_STARTUP_CONFIRM_BARS));
      return true;
   }

   void Update(const RegimeResult &raw)
   {
      if(!m_initialized)
      {
         Logger.Warn("REGIME_PERSIST", "Update called before Init");
         return;
      }
      m_update_count++;

      if(!raw.is_valid)
      {
         BuildResult(raw, false, false);
         return;
      }
      if(m_last_processed_h4_bar == raw.evaluated_at && raw.evaluated_at > 0)
      {
         BuildResult(raw, false, false);
         return;
      }
      m_last_processed_h4_bar = raw.evaluated_at;

      PushHistory(raw.raw_score, raw.regime);

      REGIME_STATE new_regime = raw.regime;
      TRADE_DIR    new_dir    = raw.direction;
      bool just_changed      = false;
      bool direction_flipped = false;

      //--- Startup confirmation mode
      if(m_confirmed_regime == REGIME_UNKNOWN)
      {
         bool same_dir =
            (IsBullish(new_regime) && IsBullish(m_startup_pending_regime)) ||
            (IsBearish(new_regime) && IsBearish(m_startup_pending_regime)) ||
            (IsRanging(new_regime) && IsRanging(m_startup_pending_regime));

         if(m_startup_pending_regime == REGIME_UNKNOWN)
         {
            m_startup_pending_regime    = new_regime;
            m_startup_pending_direction = new_dir;
            m_startup_confirmation_bars = 1;
            Logger.Info("REGIME_PERSIST",
               StringFormat("Startup bar 1/%d: candidate=%s - withholding",
                             PERSIST_STARTUP_CONFIRM_BARS, EnumToString(new_regime)));
            m_stability_score = ComputeStabilityScore();
            BuildResult(raw, false, false);
            return;
         }
         else if(same_dir)
         {
            m_startup_confirmation_bars++;
            if(m_startup_confirmation_bars >= PERSIST_STARTUP_CONFIRM_BARS)
            {
               ConfirmRegime(new_regime, new_dir,
                  StringFormat("startup_confirmed_%d_bars", m_startup_confirmation_bars));
               m_startup_pending_regime = REGIME_UNKNOWN;
               m_startup_confirmation_bars = 0;
               just_changed = true;
               m_stability_score = ComputeStabilityScore();
               BuildResult(raw, just_changed, direction_flipped);
               return;
            }
            Logger.Info("REGIME_PERSIST",
               StringFormat("Startup bar %d/%d: still withholding",
                             m_startup_confirmation_bars, PERSIST_STARTUP_CONFIRM_BARS));
            m_stability_score = ComputeStabilityScore();
            BuildResult(raw, false, false);
            return;
         }
         else
         {
            Logger.Info("REGIME_PERSIST",
               StringFormat("Startup dir change: %s -> %s. Restart warmup.",
                             EnumToString(m_startup_pending_regime),
                             EnumToString(new_regime)));
            m_startup_pending_regime    = new_regime;
            m_startup_pending_direction = new_dir;
            m_startup_confirmation_bars = 1;
            m_stability_score = ComputeStabilityScore();
            BuildResult(raw, false, false);
            return;
         }
      }

      //--- Direct BULL<->BEAR flip - forbidden
      if(IsDirectFlip(m_confirmed_regime, new_regime))
      {
         m_blocked_flips++;
         Logger.Warn("REGIME_PERSIST",
            StringFormat("BLOCKED direct flip: %s -> %s. Forcing RANGING.",
                          EnumToString(m_confirmed_regime), EnumToString(new_regime)));
         m_confirmed_regime      = REGIME_RANGING;
         m_confirmed_direction   = DIR_NONE;
         m_regime_anchor_time    = TimeCurrent();
         m_regime_age_bars       = 0;
         m_transition_state      = TRANS_FORCED_RANGE;
         m_transition_target     = new_regime;
         m_transition_target_dir = new_dir;
         m_transition_bar_count  = 0;
         m_transition_start_time = TimeCurrent();
         m_confirmed_changes++;
         direction_flipped = true;
         just_changed = true;
         SaveState();
         m_stability_score = ComputeStabilityScore();
         BuildResult(raw, just_changed, direction_flipped);
         return;
      }

      //--- Transition state processing
      switch(m_transition_state)
      {
         case TRANS_CONFIRMED:
         {
            bool same_direction =
               (IsBullish(new_regime) && IsBullish(m_confirmed_regime)) ||
               (IsBearish(new_regime) && IsBearish(m_confirmed_regime)) ||
               (IsRanging(new_regime) && IsRanging(m_confirmed_regime));

            if(same_direction || new_regime == m_confirmed_regime)
            {
               m_regime_age_bars++;
               if(IsTrending(new_regime) && IsWeak(m_confirmed_regime))
               {
                  m_confirmed_regime = new_regime;
                  m_confirmed_direction = new_dir;
                  Logger.Info("REGIME_PERSIST",
                     StringFormat("Strength upgrade: %s", EnumToString(new_regime)));
                  SaveState();
               }
               break;
            }
            if(IsTrending(m_confirmed_regime) &&
               (IsRanging(new_regime) || ScoreSupportsRanging(raw.raw_score)))
            {
               StartTransition(TRANS_PENDING_RANGE, new_regime, new_dir, "trend_to_range_pending");
            }
            else if(IsRanging(m_confirmed_regime) && IsTrending(new_regime) &&
                     ScoreSupportsTrending(raw.raw_score))
            {
               StartTransition(TRANS_PENDING_TREND, new_regime, new_dir, "range_to_trend_pending");
            }
            else
            {
               m_regime_age_bars++;
            }
            break;
         }

         case TRANS_PENDING_RANGE:
         {
            bool still_ranging = IsRanging(new_regime) ||
                                  ScoreSupportsRanging(raw.raw_score) ||
                                  IsWeak(new_regime);
            if(still_ranging)
            {
               m_transition_bar_count++;
               if(m_transition_bar_count >= PERSIST_TREND_TO_RANGE_BARS)
               {
                  ConfirmRegime(new_regime, new_dir,
                     StringFormat("trend_to_range_confirmed_%d", m_transition_bar_count));
                  just_changed = true;
               }
            }
            else
            {
               AbortTransition("trend_resumed");
               m_regime_age_bars++;
            }
            if(m_transition_state != TRANS_CONFIRMED &&
               m_transition_bar_count >= PERSIST_TRANSITION_MAX_BARS)
            {
               Logger.Warn("REGIME_PERSIST", "Timeout - default RANGING");
               ConfirmRegime(REGIME_RANGING, DIR_NONE, "transition_timeout");
               just_changed = true;
            }
            break;
         }

         case TRANS_PENDING_TREND:
         {
            bool still_trending = IsTrending(new_regime) &&
                                   ScoreSupportsTrending(raw.raw_score) &&
                                   (new_dir == m_transition_target_dir);
            if(still_trending)
            {
               m_transition_bar_count++;
               if(m_transition_bar_count >= PERSIST_RANGE_TO_TREND_BARS)
               {
                  ConfirmRegime(new_regime, new_dir,
                     StringFormat("range_to_trend_confirmed_%d", m_transition_bar_count));
                  just_changed = true;
               }
            }
            else
            {
               AbortTransition("trend_failed_to_confirm");
               m_regime_age_bars++;
            }
            if(m_transition_state != TRANS_CONFIRMED &&
               m_transition_bar_count >= PERSIST_TRANSITION_MAX_BARS)
            {
               Logger.Warn("REGIME_PERSIST", "Timeout - stay RANGING");
               AbortTransition("transition_timeout");
            }
            break;
         }

         case TRANS_FORCED_RANGE:
         {
            m_transition_bar_count++;
            m_regime_age_bars++;
            if(m_transition_bar_count >= 1)
            {
               if(IsTrending(new_regime) && ScoreSupportsTrending(raw.raw_score))
               {
                  StartTransition(TRANS_PENDING_TREND, new_regime, new_dir, "post_flip_trend");
               }
               else if(IsRanging(new_regime))
               {
                  ConfirmRegime(REGIME_RANGING, DIR_NONE, "forced_range_confirmed");
                  just_changed = true;
               }
            }
            break;
         }
      }

      m_stability_score = ComputeStabilityScore();
      BuildResult(raw, just_changed, direction_flipped);
   }

   RegimePersistenceResult GetCached() const { return m_cached; }
   bool IsInitialized()            const { return m_initialized; }
   REGIME_STATE GetConfirmedRegime() const { return m_confirmed_regime; }
   TRADE_DIR GetConfirmedDirection() const { return m_confirmed_direction; }
   int  GetRegimeAgeBars()        const { return m_regime_age_bars; }
   bool IsInTransition()          const { return (m_transition_state != TRANS_CONFIRMED); }
   double GetStabilityScore()     const { return m_stability_score; }
   int  GetUpdateCount()          const { return m_update_count; }
   int  GetConfirmedChanges()     const { return m_confirmed_changes; }
   int  GetBlockedFlips()         const { return m_blocked_flips; }

   void Reset()
   {
      m_confirmed_regime          = REGIME_UNKNOWN;
      m_confirmed_direction       = DIR_NONE;
      m_regime_anchor_time        = 0;
      m_regime_age_bars           = 0;
      m_transition_state          = TRANS_CONFIRMED;
      m_transition_target         = REGIME_UNKNOWN;
      m_transition_target_dir     = DIR_NONE;
      m_transition_bar_count      = 0;
      m_transition_start_time     = 0;
      m_history_write_idx         = 0;
      m_history_count             = 0;
      m_last_processed_h4_bar     = 0;
      m_cache_valid               = false;
      m_stability_score           = 0.0;
      m_startup_pending_regime    = REGIME_UNKNOWN;
      m_startup_pending_direction = DIR_NONE;
      m_startup_confirmation_bars = 0;
      ArrayInitialize(m_score_history, 0);
      for(int i = 0; i < PERSIST_HISTORY_MAX; i++)
         m_regime_history[i] = REGIME_UNKNOWN;
      ZeroMemory(m_cached);
      m_cached.confirmed_regime = REGIME_UNKNOWN;
      Logger.Info("REGIME_PERSIST", "Model reset");
   }

   void Shutdown()
   {
      if(m_initialized) SaveState();
      Logger.Info("REGIME_PERSIST",
         StringFormat("Shutdown. updates=%d changes=%d blocked_flips=%d final=%s age=%d",
                       m_update_count, m_confirmed_changes, m_blocked_flips,
                       EnumToString(m_confirmed_regime), m_regime_age_bars));
      m_initialized = false;
   }
};

//--- Global singleton
CRegimePersistenceModel RegimePersistenceModel;

#endif // CREGIMEPERSISTENCEMODEL_MQH

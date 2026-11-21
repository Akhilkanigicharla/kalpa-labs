
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — State Manager                           |
//| File: Core/CStateManager.mqh                                      |
//| Purpose: Owns EA master state and all transitions.                |
//|           Nothing changes state except this class.                |
//|           All transitions are logged with reason.                 |
//| Phase: 1 — Core Framework                                         |
//+------------------------------------------------------------------+
#ifndef CSTATEMANAGER_MQH
#define CSTATEMANAGER_MQH
#include "../Include/Defines.mqh"
#include "CLogger.mqh"

//===================================================================
// PSEUDO-CODE DESIGN
//
// PROBLEM: If state is a plain variable anyone can set, bugs arise
//   where state gets set from a corner case and never resets.
//   "Hidden state changes" = #8 in prohibited patterns list.
//
// SOLUTION: CStateManager is the only entity that changes m_state.
//   All transitions go through Transition() which:
//   1. Validates the transition is legal (no impossible jumps)
//   2. Logs the transition with full context
//   3. Records entry time (for duration analysis)
//   4. Maintains transition history (last 10)
//
// LEGAL TRANSITIONS:
//   INITIALIZING → GUARD_CHECK (on successful init only)
//   GUARD_CHECK  → SEEK_ENTRY, MANAGE_TRADE, SUSPENDED
//   SEEK_ENTRY   → GUARD_CHECK (setup not ready), MANAGE_TRADE (order placed)
//   MANAGE_TRADE → GUARD_CHECK (trade closed)
//   SUSPENDED    → GUARD_CHECK (resume conditions met)
//   Any state   → PROFIT_TARGET, FATAL_ERROR (emergency)
//
// ILLEGAL (logged as ERROR if attempted):
//   INITIALIZING → MANAGE_TRADE (can't have a trade before init done)
//   PROFIT_TARGET → anything (terminal)
//   FATAL_ERROR  → anything (terminal)
//===================================================================

struct StateTransition
{
   EA_STATE      from_state;
   EA_STATE      to_state;
   SUSPEND_REASON suspend_reason;
   datetime      transition_time;
   string        reason_text;
};

class CStateManager
{
private:
   EA_STATE       m_state;
   EA_STATE       m_prev_state;
   SUSPEND_REASON m_suspend_reason;
   datetime       m_state_entry_time;

   StateTransition m_history[10];
   int            m_history_idx;
   int            m_history_count;

   bool IsTerminalState(EA_STATE s) const
   {
      return (s == STATE_PROFIT_TARGET || s == STATE_FATAL_ERROR);
   }

   bool IsLegalTransition(EA_STATE from, EA_STATE to) const
   {
      // Terminal states cannot transition to anything
      if(IsTerminalState(from)) return false;

      switch(from)
      {
         case STATE_INITIALIZING:
            return (to == STATE_GUARD_CHECK ||
                    to == STATE_FATAL_ERROR);

         case STATE_GUARD_CHECK:
            return (to == STATE_SEEK_ENTRY   ||
                    to == STATE_MANAGE_TRADE ||
                    to == STATE_SUSPENDED    ||
                    to == STATE_PROFIT_TARGET||
                    to == STATE_FATAL_ERROR);

         case STATE_SEEK_ENTRY:
            return (to == STATE_GUARD_CHECK  ||
                    to == STATE_MANAGE_TRADE ||
                    to == STATE_SUSPENDED    ||
                    to == STATE_PROFIT_TARGET||
                    to == STATE_FATAL_ERROR);

         case STATE_MANAGE_TRADE:
            return (to == STATE_GUARD_CHECK  ||
                    to == STATE_SUSPENDED    ||
                    to == STATE_PROFIT_TARGET||
                    to == STATE_FATAL_ERROR);

         case STATE_SUSPENDED:
            return (to == STATE_GUARD_CHECK  ||
                    to == STATE_FATAL_ERROR  ||
                    to == STATE_PROFIT_TARGET);

         default:
            return false;
      }
   }

   void RecordHistory(EA_STATE from, EA_STATE to,
                      SUSPEND_REASON reason, string text)
   {
      m_history_idx = (m_history_idx + 1) % 10;
      m_history[m_history_idx].from_state      = from;
      m_history[m_history_idx].to_state        = to;
      m_history[m_history_idx].suspend_reason  = reason;
      m_history[m_history_idx].transition_time = TimeCurrent();
      m_history[m_history_idx].reason_text     = text;
      m_history_count = MathMin(m_history_count + 1, 10);
   }

public:
   CStateManager() :
      m_state(STATE_INITIALIZING),
      m_prev_state(STATE_INITIALIZING),
      m_suspend_reason(SUSPEND_NONE),
      m_state_entry_time(0),
      m_history_idx(-1),
      m_history_count(0)
   {
      // Clear transition history (struct array — init each field)
      for(int i = 0; i < 10; i++)
      {
         m_history[i].from_state      = STATE_INITIALIZING;
         m_history[i].to_state        = STATE_INITIALIZING;
         m_history[i].transition_time = 0;
      }
   }

   //--- Attempt a state transition
   //    Returns true if transition was accepted and applied
   bool Transition(EA_STATE new_state,
                   string reason,
                   SUSPEND_REASON suspend_reason = SUSPEND_NONE)
   {
      if(m_state == new_state && new_state != STATE_GUARD_CHECK)
      {
         // Same state: only log at DEBUG level — not interesting
         // Exception: GUARD_CHECK loops every tick — don't log it
         return true;
      }

      if(!IsLegalTransition(m_state, new_state))
      {
         Logger.Error("STATE",
            StringFormat("ILLEGAL transition %s → %s rejected",
                         EnumToString(m_state), EnumToString(new_state)),
            StringFormat("reason=%s", reason));
         return false;
      }

      m_prev_state    = m_state;
      m_state         = new_state;
      m_suspend_reason = suspend_reason;
      m_state_entry_time = TimeCurrent();

      RecordHistory(m_prev_state, m_state, suspend_reason, reason);

      // Log all state changes except the routine GUARD_CHECK loop
      LOG_LEVEL lvl = LOG_INFO;
      if(new_state == STATE_FATAL_ERROR)    lvl = LOG_FATAL;
      if(new_state == STATE_SUSPENDED &&
         suspend_reason == SUSPEND_EQUITY_FLOOR) lvl = LOG_CRITICAL;

      if(new_state != STATE_GUARD_CHECK &&
         m_prev_state != STATE_GUARD_CHECK)
      {
         Logger.Write(lvl, "STATE",
            StringFormat("%s → %s",
                         EnumToString(m_prev_state),
                         EnumToString(new_state)),
            StringFormat("reason=%s suspend=%s",
                         reason, EnumToString(suspend_reason)));
      }

      return true;
   }

   //--- Convenience: suspend with specific reason
   bool Suspend(SUSPEND_REASON reason, string detail = "")
   {
      return Transition(STATE_SUSPENDED,
         detail == "" ? EnumToString(reason) : detail,
         reason);
   }

   //--- Convenience: resume from suspension (back to guard check)
   bool Resume(string reason = "resume_conditions_met")
   {
      if(m_state != STATE_SUSPENDED)
      {
         Logger.Warn("STATE", "Resume called but not suspended");
         return false;
      }
      return Transition(STATE_GUARD_CHECK, reason);
   }

   //--- Getters
   EA_STATE      GetState()         const { return m_state; }
   EA_STATE      GetPrevState()     const { return m_prev_state; }
   SUSPEND_REASON GetSuspendReason() const { return m_suspend_reason; }
   datetime      GetStateAge()      const
   {
      return (m_state_entry_time > 0)
             ? (TimeCurrent() - m_state_entry_time)
             : 0;
   }

   bool IsSuspended()     const { return m_state == STATE_SUSPENDED; }
   bool IsTerminal()      const { return IsTerminalState(m_state); }
   bool IsOperational()   const
   {
      return (m_state == STATE_GUARD_CHECK ||
              m_state == STATE_SEEK_ENTRY  ||
              m_state == STATE_MANAGE_TRADE);
   }

   //--- Check if enough time has elapsed in current suspension
   bool SuspensionExpired(int cooldown_sec) const
   {
      return (m_state == STATE_SUSPENDED &&
              GetStateAge() >= (datetime)cooldown_sec);
   }
};

//--- Global singleton
CStateManager StateManager;

#endif // CSTATEMANAGER_MQH

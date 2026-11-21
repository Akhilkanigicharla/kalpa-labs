
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Intelligence Engine Interface           |
//| File: Intelligence/IIntelligenceEngine.mqh                        |
//| Purpose: Abstract base interface all 6 intelligence engines       |
//|           must implement. Mirrors IGuard pattern from Phase 2     |
//|           but tailored to read-only market analysis.              |
//| Phase: 3 — Step 1 Foundation                                      |
//|                                                                    |
//| DEPENDENCY RULE:                                                   |
//|   Depends on: IntelligenceTypes.mqh only                          |
//|   No guard types. No execution types. No broker API calls.        |
//|                                                                    |
//| IMPLEMENTATION CONTRACT for all subclasses:                       |
//|   1. Init()     — called ONCE at EA start. Load handles/history.  |
//|   2. Evaluate() — called on relevant bar close (NOT every tick).  |
//|                   Coordinator detects new bars and calls engines. |
//|   3. GetCached()— called every tick. Returns last result fast.    |
//|   4. Reset()    — clear all state (for testing/restart recovery). |
//|   5. Shutdown() — release indicator handles, clean up.            |
//|                                                                    |
//|   CRITICAL RULES (must never be violated):                        |
//|   - Evaluate() MUST be deterministic: same bars = same output     |
//|   - Evaluate() MUST NOT call OrderSend, PositionClose, etc.       |
//|   - Evaluate() MUST NOT modify GuardLayer state                   |
//|   - Evaluate() MUST NOT log on every call (only on state change)  |
//|   - GetCached() MUST be O(1) — no calculations allowed            |
//+------------------------------------------------------------------+
#ifndef IINTELLIGENCEENGINE_MQH
#define IINTELLIGENCEENGINE_MQH

#include "IntelligenceTypes.mqh"
#include "../Core/CLogger.mqh"

//===================================================================
// ABSTRACT BASE CLASS: IIntelligenceEngine
//
// PSEUDO-CODE DESIGN:
//   Every intelligence engine follows this lifecycle:
//
//   STARTUP:
//     Init(symbol, pip_size) → creates indicator handles, loads
//     historical bars, warms up internal state. Returns false if
//     the engine cannot safely operate (e.g. no price history).
//
//   PER RELEVANT BAR CLOSE (not per tick):
//     Coordinator detects new H4/H1/M15 bar via iTime() comparison.
//     Coordinator calls Evaluate(context) on affected engines only.
//     Engine recalculates, updates internal cached result.
//     Returns bool: true = valid output, false = degraded/error.
//
//   PER TICK (fast path):
//     Coordinator calls GetCached() to read last result.
//     No calculation. O(1) copy return.
//
//   SHUTDOWN:
//     Shutdown() releases all MT5 indicator handles.
//     IMPORTANT: IndicatorRelease() must be called for every
//     handle created via iMA(), iATR(), etc.
//     Failure to release = handle leak = MT5 memory leak.
//
//   ERROR HANDLING:
//     If Evaluate() encounters bad data (zero prices, no bars):
//       - Set is_valid = false in result struct
//       - Set appropriate invalid_reason string
//       - Update m_meta.error_count
//       - Return false (NOT a crash — graceful degradation)
//     The coordinator treats false return as engine unavailable.
//     Other engines that depend on this engine get a reduced
//     confidence score but continue operating.
//===================================================================

class IIntelligenceEngine
{
protected:
   EngineMetadata   m_meta;
   bool             m_initialized;
   string           m_symbol;
   double           m_pip_size;    // Cached from PriceUtils at Init()

public:
   IIntelligenceEngine() : m_initialized(false), m_pip_size(0.01) {}
   virtual ~IIntelligenceEngine() {}

   //--- Initialize engine
   //    symbol:   trading symbol (always EA_SYMBOL in production)
   //    pip_size: from PriceUtils.PipSize() — cached to avoid repeated calls
   //    Returns false if engine cannot operate (EA logs warning, continues)
   virtual bool Init(string symbol, double pip_size) = 0;

   //--- Evaluate on bar close
   //    ctx: market snapshot pre-populated by coordinator
   //    Called ONLY when the relevant timeframe bar has closed.
   //    Updates internal cached result.
   //    Returns true if output is valid, false if degraded/unavailable.
   virtual bool Evaluate(const IntelligenceContext &ctx) = 0;

   //--- Get cached result (called every tick — must be O(1))
   //    DO NOT override with calculation logic.
   //    Each engine defines its own typed GetCached() that returns
   //    its specific result struct. This base version provides the
   //    metadata check.
   virtual bool IsCacheValid() const
   {
      return (m_initialized && m_meta.available);
   }

   //--- Reset all internal state (for testing and orphan recovery)
   //    Does NOT release indicator handles — call Shutdown() for that.
   virtual void Reset() = 0;

   //--- Release all MT5 indicator handles and clean up
   virtual void Shutdown()
   {
      m_initialized = false;
      m_meta.initialized = false;
      m_meta.available   = false;
   }

   //--- Get current confidence estimate
   //    Returns 0.0 if not initialized or last result invalid.
   virtual double GetConfidence() const
   {
      if(!m_initialized || !m_meta.available) return 0.0;
      return m_meta.last_confidence;
   }

   //--- When was this engine last successfully evaluated?
   virtual datetime GetLastEvaluationTime() const
   {
      return m_meta.last_eval_time;
   }

   //--- Is the cached result still considered fresh?
   //    max_age_seconds: caller specifies how old is acceptable
   virtual bool IsFresh(int max_age_seconds) const
   {
      if(!m_initialized || m_meta.last_eval_time == 0) return false;
      return ((TimeCurrent() - m_meta.last_eval_time) <= max_age_seconds);
   }

   //--- Accessors
   EngineMetadata GetMetadata()    const { return m_meta; }
   bool   IsInitialized()          const { return m_initialized; }
   bool   IsAvailable()            const { return m_meta.available; }
   bool   IsEnabled()              const { return m_meta.enabled; }
   string GetName()                const { return m_meta.name; }
   ENGINE_ID GetID()               const { return m_meta.id; }
   int    GetEvalCount()           const { return m_meta.eval_count; }
   int    GetErrorCount()          const { return m_meta.error_count; }

protected:
   //--- Called by subclasses on each successful evaluation
   void RecordSuccess(double confidence)
   {
      m_meta.eval_count++;
      m_meta.valid_count++;
      m_meta.last_confidence  = confidence;
      m_meta.last_eval_time   = TimeCurrent();
      m_meta.last_valid_time  = TimeCurrent();
      m_meta.available        = true;
      m_meta.last_error       = "";
   }

   //--- Called by subclasses when evaluation produces invalid output
   void RecordError(string reason)
   {
      m_meta.eval_count++;
      m_meta.error_count++;
      m_meta.last_error       = reason;
      m_meta.last_eval_time   = TimeCurrent();
      m_meta.available        = false;
      m_meta.last_confidence  = 0.0;
   }

   //--- Convert price distance to pips using cached pip_size
   double PriceToPips(double price_distance) const
   {
      if(m_pip_size <= 0) return 0.0;
      return MathAbs(price_distance) / m_pip_size;
   }

   //--- Convert pips to price distance
   double PipsToPrice(double pips) const
   {
      return pips * m_pip_size;
   }
};

#endif // IINTELLIGENCEENGINE_MQH

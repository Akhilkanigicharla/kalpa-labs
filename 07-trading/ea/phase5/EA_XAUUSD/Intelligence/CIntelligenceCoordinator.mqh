
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Intelligence Coordinator                |
//| File: Intelligence/CIntelligenceCoordinator.mqh                   |
//| Purpose: Sole runtime owner of the Intelligence Layer.            |
//|           Detects bar boundaries, populates IntelligenceContext,  |
//|           orchestrates engine evaluations in dependency order,    |
//|           assembles the IntelligencePacket, monitors staleness.   |
//| Phase: 3 — Priority Fix (originally Step 1)                       |
//|                                                                    |
//| RESPONSIBILITIES:                                                  |
//|   1. Single owner of all intelligence engines                     |
//|   2. Sole caller of engine.Evaluate() and engine.GetCached()      |
//|   3. Bar boundary detection via iTime() comparisons               |
//|   4. IntelligenceContext population from broker + SpreadGuard     |
//|   5. Packet assembly with MarketQualityScore                      |
//|   6. Staleness monitoring per engine                              |
//|   7. Diagnostic logging on state changes                          |
//|                                                                    |
//| EXPLICITLY NOT RESPONSIBLE FOR:                                   |
//|   - Trade decisions (Phase 4 TradeScorer)                         |
//|   - Order placement (Phase 5 ExecutionLayer)                      |
//|   - Position management (Phase 6)                                  |
//|   - State machine transitions (CStateManager handles these)       |
//|   - Guard enforcement (CGuardCoordinator handles these)           |
//|                                                                    |
//| ZERO-COPY PACKET ACCESS:                                          |
//|   GetPacket() returns const reference — no struct copy.           |
//|   Downstream modules (TradeScorer) read from the reference.       |
//|   This eliminates ~8.6 KB copy-per-tick cost identified in audit. |
//+------------------------------------------------------------------+
#ifndef CINTELLIGENCECOORDINATOR_MQH
#define CINTELLIGENCECOORDINATOR_MQH

#include "IntelligenceTypes.mqh"
#include "IIntelligenceEngine.mqh"
#include "CStructureEngine.mqh"
#include "CVolatilityEngine.mqh"
#include "CRegimeEngine.mqh"
#include "CRegimePersistenceModel.mqh"
#include "CTrendEngine.mqh"
#include "CLiquidityEngine.mqh"
#include "../Core/CConfig.mqh"
#include "../Core/CLogger.mqh"
#include "../Include/PriceUtils.mqh"
#include "../Guards/GuardTypes.mqh"
#include "../Guards/CSpreadGuard.mqh"

//===================================================================
// FORWARD REFERENCES TO GLOBAL SINGLETONS
// These are declared by their respective files. The coordinator
// references them at call sites — it does not own them.
//===================================================================
// extern CStructureEngine  StructureEngine;   (declared in CStructureEngine.mqh)
// extern CVolatilityEngine VolatilityEngine;  (declared in CVolatilityEngine.mqh)
// extern CRegimeEngine     RegimeEngine;      (declared in CRegimeEngine.mqh)
// extern CSpreadGuard      SpreadGuard;       (declared in CSpreadGuard.mqh)

//===================================================================
// MARKETQUALITYSCORE COMPUTATION CONSTANTS
//
// REVISION (from Step 1 approval): no hard-zero conditions.
// Severe penalties only — Phase 4 decides sufficiency.
//===================================================================
#define MQS_REGIME_WEIGHT      25  // Max contribution from regime
#define MQS_TREND_WEIGHT       25  // Max from trend (placeholder until Step 6)
#define MQS_STRUCTURE_WEIGHT   20  // Max from structure clarity
#define MQS_VOLATILITY_WEIGHT  15  // Max from volatility quality
#define MQS_LIQUIDITY_WEIGHT   15  // Max from liquidity (placeholder until Step 7)
// Sum = 100

// Severe penalty values (deducted from total — never below 0)
#define MQS_PENALTY_RANGING       40
#define MQS_PENALTY_REGIME_UNKNOWN 35
#define MQS_PENALTY_NEWS_SPIKE    35
#define MQS_PENALTY_SPIKE_NO_TREND 25

//===================================================================
// THROTTLE
//
// PSEUDO-CODE:
//   The coordinator is called every tick from OnTick().
//   On most ticks: no bar has closed, no work to do.
//   The cheap check is: detect bar boundary flags.
//   If none set: skip all engine calls, return immediately.
//
//   Cost on a non-boundary tick:
//     - 4× iTime() calls (M5, M15, H1, H4)
//     - 4× datetime comparisons
//     - early return
//   Total: < 0.005 ms per tick. Acceptable.
//
//   No microsecond throttle needed — bar boundary check is the throttle.
//===================================================================

class CIntelligenceCoordinator
{
private:
   //--- Engine pointers (NOT owned — references to global singletons)
   //    The coordinator does not construct or destroy engines.
   //    It uses pointers to enable null-checking and future
   //    engine swapping for testing.
   CStructureEngine*   m_structure;
   CVolatilityEngine*  m_volatility;
   CRegimeEngine*      m_regime;
   CLiquidityEngine*        m_liquidity;
   CRegimePersistenceModel* m_persistence;
   CTrendEngine*            m_trend;

   //--- SpreadGuard reference (for session_avg_atr_pips and session_avg_spread)
   CSpreadGuard*       m_spread_guard;

   //--- Bar boundary tracking
   //    Each engine timeframe gets its own last-seen bar timestamp.
   //    iTime(symbol, tf, 1) returns the timestamp of the most recent
   //    CLOSED bar. When that changes, a new bar has closed.
   datetime            m_last_m5_bar;
   datetime            m_last_m15_bar;
   datetime            m_last_h1_bar;
   datetime            m_last_h4_bar;

   //--- Cached intelligence packet (THE shared output)
   //    Accessed via GetPacket() const reference — no copy on read.
   IntelligencePacket  m_packet;
   bool                m_packet_valid;

   //--- Lifecycle state
   bool                m_initialized;
   bool                m_first_tick;       // Force evaluation on first Update
   int                 m_update_count;      // Total Update() calls
   int                 m_assembly_count;    // Times packet was rebuilt
   datetime            m_last_log_time;     // For periodic diagnostics

   //--- Symbol + pip size (cached from Config + PriceUtils)
   string              m_symbol;
   double              m_pip_size;
   long                m_magic;

   //===================================================================
   // INTERNAL: detect new bar closures via iTime comparison
   //
   // PSEUDO-CODE:
   //   iTime(sym, tf, 1) returns timestamp of most recent CLOSED bar.
   //   Compare to stored last_*_bar. If different → new bar closed.
   //   Update stored timestamp only AFTER engine has consumed the flag.
   //   That ordering: detect → set ctx flag → engine runs → update last_*_bar.
   //
   //   First tick edge case: m_last_*_bar is 0 (uninitialized).
   //   Comparison against any real timestamp triggers a "new bar" event,
   //   which is correct — we want engines to run on first tick.
   //   The m_first_tick flag is a redundant safeguard.
   //===================================================================
   void DetectBarBoundaries(IntelligenceContext &ctx)
   {
      datetime t_m5  = iTime(m_symbol, PERIOD_M5,  1);
      datetime t_m15 = iTime(m_symbol, PERIOD_M15, 1);
      datetime t_h1  = iTime(m_symbol, PERIOD_H1,  1);
      datetime t_h4  = iTime(m_symbol, PERIOD_H4,  1);

      // First-tick safety: if iTime returns 0 (no bars available),
      // do not flag a boundary — engines would refresh against empty data.
      ctx.new_m5_bar  = (t_m5  > 0 && t_m5  != m_last_m5_bar);
      ctx.new_m15_bar = (t_m15 > 0 && t_m15 != m_last_m15_bar);
      ctx.new_h1_bar  = (t_h1  > 0 && t_h1  != m_last_h1_bar);
      ctx.new_h4_bar  = (t_h4  > 0 && t_h4  != m_last_h4_bar);

      // First-tick force: ensure engines run at least once after init
      if(m_first_tick)
      {
         ctx.new_m5_bar  = (t_m5  > 0);
         ctx.new_m15_bar = (t_m15 > 0);
         ctx.new_h1_bar  = (t_h1  > 0);
         ctx.new_h4_bar  = (t_h4  > 0);
      }

      // Stash candidate timestamps — updated AFTER engines run
      m_pending_m5  = t_m5;
      m_pending_m15 = t_m15;
      m_pending_h1  = t_h1;
      m_pending_h4  = t_h4;
   }

   //--- Pending bar timestamps (set during DetectBarBoundaries,
   //    committed to m_last_*_bar after engines complete)
   datetime  m_pending_m5;
   datetime  m_pending_m15;
   datetime  m_pending_h1;
   datetime  m_pending_h4;

   void CommitBarBoundaries()
   {
      if(m_pending_m5  > 0) m_last_m5_bar  = m_pending_m5;
      if(m_pending_m15 > 0) m_last_m15_bar = m_pending_m15;
      if(m_pending_h1  > 0) m_last_h1_bar  = m_pending_h1;
      if(m_pending_h4  > 0) m_last_h4_bar  = m_pending_h4;
   }

   //===================================================================
   // INTERNAL: populate IntelligenceContext from broker + Guards
   //
   // PSEUDO-CODE:
   //   The coordinator is the SINGLE writer of IntelligenceContext.
   //   Engines only READ from it. This guarantees consistency across
   //   the engine evaluation chain in a single tick — even if price
   //   ticks again mid-evaluation, the context snapshot is frozen.
   //
   //   Fields populated here:
   //     - Price (bid/ask/spread/mid)
   //     - Time (server/GMT/hour/minute/day-of-week)
   //     - Session flags (London/NY/active)
   //     - SpreadGuard baselines (session_avg_atr/spread, calibration)
   //     - new_*_bar flags (set by DetectBarBoundaries before this)
   //===================================================================
   void PopulateContext(IntelligenceContext &ctx)
   {
      // --- Price snapshot ---
      ctx.bid          = SymbolInfoDouble(m_symbol, SYMBOL_BID);
      ctx.ask          = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
      ctx.mid_price    = (ctx.bid + ctx.ask) * 0.5;
      ctx.spread_pips  = (m_pip_size > 0)
                         ? (ctx.ask - ctx.bid) / m_pip_size
                         : 0.0;

      // --- Time ---
      ctx.server_time  = TimeCurrent();
      ctx.gmt_time     = EAGmtNow();      // A336 (#20)
      MqlDateTime gdt;
      TimeToStruct(ctx.gmt_time, gdt);
      ctx.gmt_hour     = gdt.hour;
      ctx.gmt_minute   = gdt.min;
      ctx.day_of_week  = gdt.day_of_week;  // 0=Sun, 6=Sat

      // --- Session flags ---
      // Computed inline from GMT time and Config session boundaries.
      // SessionGuard does not expose separate London/NY flag accessors,
      // so we reproduce the same boundary check here.
      bool weekend     = (ctx.day_of_week == 0 || ctx.day_of_week == 6);
      bool in_london   = (!weekend &&
                          ctx.gmt_hour >= Config.LondonStartHr &&
                          ctx.gmt_hour <  Config.LondonEndHr);
      bool in_ny       = (!weekend &&
                          ctx.gmt_hour >= Config.NyStartHr &&
                          ctx.gmt_hour <  Config.NyEndHr);
      ctx.in_london_session  = in_london;
      ctx.in_ny_session      = in_ny;
      ctx.in_active_session  = (in_london || in_ny);

      // --- SpreadGuard baselines ---
      // SpreadGuard.GetSessionAvgATR takes GuardContext, so we build one.
      // PopulateGuardContext is a free function in GuardTypes.mqh.
      GuardContext gctx;
      PopulateGuardContext(gctx, m_magic, m_pip_size);

      if(m_spread_guard != NULL && m_spread_guard.IsInitialized())
      {
         ctx.session_avg_atr_pips    = m_spread_guard.GetSessionAvgATR(gctx);
         ctx.session_avg_spread_pips = m_spread_guard.GetSessionAvgSpread(gctx);
         ctx.spread_calibrated       = m_spread_guard.IsCalibrated();
      }
      else
      {
         ctx.session_avg_atr_pips    = 0.0;  // VolatilityEngine has fallback
         ctx.session_avg_spread_pips = 0.0;
         ctx.spread_calibrated       = false;
      }

      // new_*_bar flags were set by DetectBarBoundaries before this call.
      // We do not overwrite them here.
   }

   //===================================================================
   // INTERNAL: should the engine chain run on this tick?
   //
   // Returns true if ANY relevant bar boundary fired OR first tick.
   // On a quiet tick (no boundary), returns false — coordinator
   // returns the cached packet unchanged. Cost: just the boundary check.
   //===================================================================
   bool ShouldEvaluateChain(const IntelligenceContext &ctx) const
   {
      return (ctx.new_m5_bar  ||
              ctx.new_m15_bar ||
              ctx.new_h1_bar  ||
              ctx.new_h4_bar  ||
              m_first_tick);
   }

   //===================================================================
   // INTERNAL: run engines in dependency order
   //
   // PSEUDO-CODE — strict ordering enforced:
   //
   //   StructureEngine — independent. Reads price directly.
   //     Triggers: any new M15/H1/H4 bar (it tracks all three).
   //
   //   VolatilityEngine — independent. Reads ATR via own iATR handles.
   //     Triggers: new M5 or M15 bar.
   //
   //   RegimeEngine — depends on Structure + Volatility outputs.
   //     Triggers: only new H4 bar (regime updates on H4 cadence).
   //     Before Evaluate: inject latest Structure + Volatility results.
   //
   //   Future Step 5: RegimePersistenceModel — after RegimeEngine.
   //   Future Step 6: TrendEngine — after RegimePersistenceModel.
   //   Future Step 7: LiquidityEngine — after StructureEngine (parallel
   //                  to RegimeEngine but slots in at output level).
   //===================================================================
   void EvaluateChain(const IntelligenceContext &ctx)
   {
      //--- 1. StructureEngine (no deps)
      // Runs if ANY structural timeframe closed
      if(m_structure != NULL &&
         (ctx.new_m15_bar || ctx.new_h1_bar || ctx.new_h4_bar || m_first_tick))
      {
         m_structure.Evaluate(ctx);
      }

      //--- 2. VolatilityEngine (independent, but uses session_avg_atr from ctx)
      if(m_volatility != NULL &&
         (ctx.new_m5_bar || ctx.new_m15_bar || m_first_tick))
      {
         m_volatility.Evaluate(ctx);
      }

      //--- 3. RegimeEngine (depends on Structure + Volatility)
      // Runs only on H4 bar close. Inject latest results first.
      if(m_regime != NULL && (ctx.new_h4_bar || m_first_tick))
      {
         // Inject dependency inputs — value copies of latest results
         if(m_structure != NULL && m_structure.IsInitialized())
         {
            StructureResult sr = m_structure.GetCached();
            m_regime.SetStructureResult(sr);
         }
         if(m_volatility != NULL && m_volatility.IsInitialized())
         {
            VolatilityResult vr = m_volatility.GetCached();
            m_regime.SetVolatilityResult(vr);
         }
         m_regime.Evaluate(ctx);
      }

      //--- 3b. RegimePersistenceModel (depends on RegimeEngine)
      // Runs after RegimeEngine on H4 bar close. Anti-whipsaw filter.
      if(m_persistence != NULL && m_persistence.IsInitialized() &&
         (ctx.new_h4_bar || m_first_tick))
      {
         if(m_regime != NULL && m_regime.IsInitialized())
         {
            RegimeResult rr = m_regime.GetCached();
            m_persistence.Update(rr);
         }
      }

      //--- 3c. TrendEngine (depends on Structure + Regime)
      // Runs on H1 bar close. Inject latest Structure + Regime results.
      if(m_trend != NULL && m_trend.IsInitialized() &&
         (ctx.new_h1_bar || m_first_tick))
      {
         if(m_structure != NULL && m_structure.IsInitialized())
         {
            StructureResult sr = m_structure.GetCached();
            m_trend.SetStructureResult(sr);
         }
         if(m_regime != NULL && m_regime.IsInitialized())
         {
            RegimeResult rr = m_regime.GetCached();
            m_trend.SetRegimeResult(rr);
         }
         m_trend.Evaluate(ctx);
      }

      //--- 4. LiquidityEngine (depends on StructureEngine + VolatilityEngine)
      // Runs on M15 bar close. Inject latest Structure + Volatility results.
      if(m_liquidity != NULL && m_liquidity.IsInitialized() &&
         (ctx.new_m15_bar || m_first_tick))
      {
         if(m_structure != NULL && m_structure.IsInitialized())
         {
            StructureResult sr = m_structure.GetCached();
            m_liquidity.SetStructureResult(sr);
         }
         if(m_volatility != NULL && m_volatility.IsInitialized())
         {
            VolatilityResult vr = m_volatility.GetCached();
            m_liquidity.SetVolatilityResult(vr);
         }
         m_liquidity.Evaluate(ctx);
      }
   }

   //===================================================================
   // INTERNAL: assemble the IntelligencePacket from engine outputs
   //
   // PSEUDO-CODE:
   //   1. Zero-init packet to known-safe defaults
   //   2. Copy engine cached results into packet
   //   3. Compute available_engines bitmask
   //   4. Compute MarketQualityScore (component sum minus penalties)
   //   5. Derive convenience fields (confirmed_regime, etc.)
   //   6. Set intel_status based on availability and validity
   //
   //   This is the only place packet contents are written.
   //   Downstream readers see consistent state.
   //===================================================================
   void AssemblePacket()
   {
      InitPacket(m_packet);
      m_packet.generated_at     = TimeCurrent();
      m_packet.evaluation_count = m_assembly_count + 1;

      int  bitmask = 0;
      int  available_count = 0;

      //--- Copy engine results into packet (by value — unavoidable here)
      if(m_structure != NULL && m_structure.IsInitialized())
      {
         m_packet.structure = m_structure.GetCached();
         if(m_packet.structure.is_valid && m_packet.structure.any_available)
         {
            bitmask |= (1 << ENG_STRUCTURE);
            available_count++;
         }
      }

      if(m_volatility != NULL && m_volatility.IsInitialized())
      {
         m_packet.volatility = m_volatility.GetCached();
         if(m_packet.volatility.is_valid)
         {
            bitmask |= (1 << ENG_VOLATILITY);
            available_count++;
         }
      }

      if(m_regime != NULL && m_regime.IsInitialized())
      {
         m_packet.regime = m_regime.GetCached();
         if(m_packet.regime.is_valid)
         {
            bitmask |= (1 << ENG_REGIME);
            available_count++;
         }
      }

      if(m_liquidity != NULL && m_liquidity.IsInitialized())
      {
         m_packet.liquidity = m_liquidity.GetCached();
         if(m_packet.liquidity.is_valid)
         {
            bitmask |= (1 << ENG_LIQUIDITY);
            available_count++;
         }
      }

      if(m_persistence != NULL && m_persistence.IsInitialized())
      {
         m_packet.persistence = m_persistence.GetCached();
         if(m_packet.persistence.is_valid)
         {
            bitmask |= (1 << ENG_PERSISTENCE);
            available_count++;
         }
      }

      if(m_trend != NULL && m_trend.IsInitialized())
      {
         m_packet.trend = m_trend.GetCached();
         if(m_packet.trend.is_valid)
         {
            bitmask |= (1 << ENG_TREND);
            available_count++;
         }
      }

      m_packet.available_engines = bitmask;

      //--- Compute MarketQualityScore
      ComputeQualityScore();

      //--- Derive convenience fields (mirror packet sub-structs)
      // Persistence is authoritative for confirmed_regime (anti-whipsaw filter).
      // Fall back to raw regime during startup warmup when persistence not yet valid.
      if(m_packet.persistence.is_valid)
      {
         m_packet.confirmed_regime    = m_packet.persistence.confirmed_regime;
         m_packet.consensus_direction = m_packet.persistence.confirmed_direction;
      }
      else
      {
         m_packet.confirmed_regime    = m_packet.regime.regime;
         m_packet.consensus_direction = m_packet.regime.direction;
      }
      m_packet.layer_confidence    = m_packet.quality.total / 100.0;
      m_packet.direction_valid     = (m_packet.regime.direction != DIR_NONE);
      m_packet.structure_available = (m_packet.structure.any_available);

      //--- Determine overall intel_status
      if(available_count == 0)
      {
         m_packet.intel_status   = INTEL_INITIALIZING;
         m_packet.is_valid       = false;
         m_packet.invalid_reason = "no_engines_available";
      }
      else if(available_count < 6)
      {
         m_packet.intel_status   = INTEL_DEGRADED;
         m_packet.is_valid       = true;
         m_packet.invalid_reason = StringFormat("only_%d_of_6_engines_available",
                                                  available_count);
      }
      else
      {
         m_packet.intel_status = INTEL_OPERATIONAL;
         m_packet.is_valid     = true;
         m_packet.invalid_reason = "";
      }

      m_packet_valid = true;
      m_assembly_count++;
   }

   //===================================================================
   // INTERNAL: compute MarketQualityScore for the current packet
   //
   // PSEUDO-CODE (per Step 1 revision — no hard zeros, penalties only):
   //
   //   Components (sum to max 100):
   //     Regime confidence    × 25
   //     Trend confidence     × 25   (placeholder 0 until Step 6)
   //     Structure clarity    × 20   (use H4 clarity as proxy)
   //     Volatility quality   × 15
   //     Liquidity quality    × 15   (placeholder 0 until Step 7)
   //
   //   Severe penalties (deducted from total, never below 0):
   //     RANGING regime:        -40
   //     UNKNOWN regime:        -35
   //     NEWS_SPIKE volatility: -35
   //     SPIKE without trend:   -25
   //
   //   Direction consensus check:
   //     Set when regime direction is valid (DIR_LONG or DIR_SHORT)
   //     and not RANGING/UNKNOWN. Phase 4 uses this.
   //===================================================================
   void ComputeQualityScore()
   {
      MarketQualityScore q;
      ZeroMemory(q);
      q.computed_at = TimeCurrent();

      //--- Component scoring (only contribute if engine available)
      double regime_conf = m_packet.regime.is_valid
                            ? m_regime.GetConfidence() : 0.0;
      q.regime_component = (int)(regime_conf * MQS_REGIME_WEIGHT);

      // Trend component (Step 6 complete) — confidence x weight
      double trend_conf = (m_trend != NULL && m_packet.trend.is_valid)
                          ? m_trend.GetTrendConf() : 0.0;
      q.trend_component = (int)(trend_conf * MQS_TREND_WEIGHT);

      // Structure: use H4 clarity directly (most relevant for macro context)
      double struct_clarity = 0.0;
      if(m_packet.structure.is_valid && m_packet.structure.h4_available)
         struct_clarity = m_packet.structure.h4.structure_clarity;
      q.structure_component = (int)(struct_clarity * MQS_STRUCTURE_WEIGHT);

      // Volatility quality
      double vol_quality = m_packet.volatility.is_valid
                           ? m_packet.volatility.volatility_quality : 0.0;
      q.volatility_component = (int)(vol_quality * MQS_VOLATILITY_WEIGHT);

      // Liquidity component (now real — Step 7 complete)
      double liq_score = m_packet.liquidity.is_valid ? m_packet.liquidity.score : 0.0;
      q.liquidity_component = (int)(liq_score * MQS_LIQUIDITY_WEIGHT);

      int raw = q.regime_component + q.trend_component + q.structure_component +
                q.volatility_component + q.liquidity_component;

      //--- Severe penalties
      int penalty = 0;
      string reasons = "";

      REGIME_STATE rs = m_packet.regime.regime;
      if(rs == REGIME_RANGING)
      {
         penalty += MQS_PENALTY_RANGING;
         reasons += "ranging(-40);";
      }
      else if(rs == REGIME_UNKNOWN)
      {
         penalty += MQS_PENALTY_REGIME_UNKNOWN;
         reasons += "regime_unknown(-35);";
      }

      VOLATILITY_STATE vs = m_packet.volatility.state;
      if(vs == VOL_NEWS_SPIKE)
      {
         penalty += MQS_PENALTY_NEWS_SPIKE;
         reasons += "news_spike(-35);";
      }
      else if(vs == VOL_SPIKE &&
               rs != REGIME_TRENDING_BULL && rs != REGIME_TRENDING_BEAR)
      {
         penalty += MQS_PENALTY_SPIKE_NO_TREND;
         reasons += "spike_no_trend(-25);";
      }

      q.penalty_applied = penalty;
      q.penalty_reasons = reasons;
      q.total = MathMax(0, MathMin(100, raw - penalty));

      //--- Direction consensus
      q.direction_consensus = (rs != REGIME_RANGING &&
                                rs != REGIME_UNKNOWN &&
                                m_packet.regime.direction != DIR_NONE);
      q.consensus_direction = m_packet.regime.direction;

      m_packet.quality = q;
   }

   //===================================================================
   // INTERNAL: monitor engine staleness
   //
   // PSEUDO-CODE:
   //   For each engine, compute age = now - last_eval_time.
   //   Compare against engine-specific threshold.
   //   If exceeded:
   //     - Clear the engine's bit in available_engines bitmask
   //     - Log warning (once per stale episode, not per tick)
   //     - If a critical engine is stale, set intel_status = INTEL_STALE
   //
   //   "Critical engines" for staleness escalation:
   //     - StructureEngine H4 → if stale, regime + trend become unreliable
   //     - RegimeEngine → primary macro context
   //
   //   Non-critical staleness:
   //     - VolatilityEngine → downstream uses last known good value
   //     - StructureEngine H1/M15 → less critical than H4
   //===================================================================
   void CheckStaleness()
   {
      datetime now = TimeCurrent();
      bool any_critical_stale = false;
      bool any_stale = false;
      string stale_reasons = "";

      // Structure staleness — three timeframes, each with own threshold
      if(m_structure != NULL && m_structure.IsInitialized())
      {
         StructureResult sr = m_packet.structure;
         if(sr.h4_available)
         {
            int age = (int)(now - sr.h4.last_updated);
            if(sr.h4.last_updated > 0 && age > STRUCT_STALE_H4_SEC)
            {
               m_packet.available_engines &= ~(1 << ENG_STRUCTURE);
               any_critical_stale = true;
               any_stale = true;
               stale_reasons += StringFormat("struct_h4_stale(%ds);", age);
            }
         }
      }

      // Volatility staleness
      if(m_volatility != NULL && m_volatility.IsInitialized())
      {
         datetime last = m_volatility.GetLastEvaluationTime();
         if(last > 0)
         {
            int age = (int)(now - last);
            if(age > VOL_STALE_SEC)
            {
               m_packet.available_engines &= ~(1 << ENG_VOLATILITY);
               any_stale = true;
               stale_reasons += StringFormat("vol_stale(%ds);", age);
               // Non-critical — does not escalate intel_status
            }
         }
      }

      // Regime staleness
      if(m_regime != NULL && m_regime.IsInitialized())
      {
         datetime last = m_regime.GetLastEvaluationTime();
         if(last > 0)
         {
            int age = (int)(now - last);
            if(age > REGIME_STALE_SEC)
            {
               m_packet.available_engines &= ~(1 << ENG_REGIME);
               any_critical_stale = true;
               any_stale = true;
               stale_reasons += StringFormat("regime_stale(%ds);", age);
            }
         }
      }

      if(any_critical_stale)
      {
         m_packet.intel_status   = INTEL_STALE;
         m_packet.invalid_reason = "critical_stale:" + stale_reasons;
      }
      else if(any_stale && m_packet.intel_status == INTEL_OPERATIONAL)
      {
         // Non-critical staleness downgrades to DEGRADED, not STALE
         m_packet.intel_status   = INTEL_DEGRADED;
         m_packet.invalid_reason = "partial_stale:" + stale_reasons;
      }
   }

   //===================================================================
   // INTERNAL: log packet state changes
   // Avoids spam — only logs when regime, direction, or status changes.
   //===================================================================
   REGIME_STATE       m_last_logged_regime;
   TRADE_DIR          m_last_logged_direction;
   INTELLIGENCE_STATUS m_last_logged_status;
   int                m_last_logged_quality;

   void LogIfChanged()
   {
      bool regime_changed   = (m_packet.confirmed_regime != m_last_logged_regime);
      bool dir_changed      = (m_packet.consensus_direction != m_last_logged_direction);
      bool status_changed   = (m_packet.intel_status != m_last_logged_status);
      bool quality_jumped   = (MathAbs(m_packet.quality.total - m_last_logged_quality) >= 15);

      if(regime_changed || dir_changed || status_changed || quality_jumped)
      {
         Logger.Info("INTEL_COORD",
            StringFormat("regime=%s dir=%s status=%s quality=%d/100",
               EnumToString(m_packet.confirmed_regime),
               EnumToString(m_packet.consensus_direction),
               EnumToString(m_packet.intel_status),
               m_packet.quality.total),
            StringFormat("vol=%s stop_rec=%.1f available=0x%02X penalty=%d",
               EnumToString(m_packet.volatility.state),
               m_packet.volatility.recommended_stop_pips,
               m_packet.available_engines,
               m_packet.quality.penalty_applied));

         m_last_logged_regime    = m_packet.confirmed_regime;
         m_last_logged_direction = m_packet.consensus_direction;
         m_last_logged_status    = m_packet.intel_status;
         m_last_logged_quality   = m_packet.quality.total;
      }
   }

public:
   //===================================================================
   // CONSTRUCTOR
   //===================================================================
   CIntelligenceCoordinator() :
      m_structure(NULL),
      m_volatility(NULL),
      m_regime(NULL),
      m_liquidity(NULL),
      m_persistence(NULL),
      m_trend(NULL),
      m_spread_guard(NULL),
      m_last_m5_bar(0),
      m_last_m15_bar(0),
      m_last_h1_bar(0),
      m_last_h4_bar(0),
      m_pending_m5(0),
      m_pending_m15(0),
      m_pending_h1(0),
      m_pending_h4(0),
      m_packet_valid(false),
      m_initialized(false),
      m_first_tick(true),
      m_update_count(0),
      m_assembly_count(0),
      m_last_log_time(0),
      m_symbol(""),
      m_pip_size(0.01),
      m_magic(0),
      m_last_logged_regime(REGIME_UNKNOWN),
      m_last_logged_direction(DIR_NONE),
      m_last_logged_status(INTEL_INITIALIZING),
      m_last_logged_quality(0)
   {
      InitPacket(m_packet);
   }

   //===================================================================
   // REGISTRATION — coordinator does NOT construct engines
   // Main EA constructs global engine singletons, then registers them here.
   // This enables engine swapping for testing and clear ownership.
   //===================================================================
   void RegisterStructure(CStructureEngine* eng)   { m_structure  = eng; }
   void RegisterVolatility(CVolatilityEngine* eng) { m_volatility = eng; }
   void RegisterRegime(CRegimeEngine* eng)         { m_regime     = eng; }
   void RegisterLiquidity(CLiquidityEngine* eng)   { m_liquidity  = eng; }
   void RegisterPersistence(CRegimePersistenceModel* p) { m_persistence = p; }
   void RegisterTrend(CTrendEngine* eng)           { m_trend      = eng; }
   void RegisterSpreadGuard(CSpreadGuard* sg)      { m_spread_guard = sg; }

   //===================================================================
   // INIT
   //
   // PSEUDO-CODE:
   //   Called once after all engines have been Init()'d by main EA.
   //   Verifies all required engines are registered AND initialized.
   //   Caches symbol/pip_size/magic for use in Update().
   //   Forces first_tick = true so engines run on first Update.
   //===================================================================
   bool Init(string symbol, double pip_size, long magic)
   {
      m_symbol   = symbol;
      m_pip_size = pip_size;
      m_magic    = magic;

      if(pip_size <= 0)
      {
         Logger.Fatal("INTEL_COORD", "Init: pip_size <= 0");
         return false;
      }

      // Verify required engines are registered AND initialized
      bool ok = true;
      if(m_structure == NULL)
      {
         Logger.Error("INTEL_COORD", "Init: StructureEngine not registered");
         ok = false;
      }
      else if(!m_structure.IsInitialized())
      {
         Logger.Error("INTEL_COORD",
            "Init: StructureEngine registered but not initialized — "
            "main EA must call StructureEngine.Init() before coordinator init");
         ok = false;
      }

      if(m_volatility == NULL)
      {
         Logger.Error("INTEL_COORD", "Init: VolatilityEngine not registered");
         ok = false;
      }
      else if(!m_volatility.IsInitialized())
      {
         Logger.Error("INTEL_COORD",
            "Init: VolatilityEngine registered but not initialized");
         ok = false;
      }

      if(m_regime == NULL)
      {
         Logger.Error("INTEL_COORD", "Init: RegimeEngine not registered");
         ok = false;
      }
      else if(!m_regime.IsInitialized())
      {
         Logger.Error("INTEL_COORD",
            "Init: RegimeEngine registered but not initialized");
         ok = false;
      }

      if(m_liquidity == NULL)
      {
         Logger.Error("INTEL_COORD", "Init: LiquidityEngine not registered");
         ok = false;
      }
      else if(!m_liquidity.IsInitialized())
      {
         Logger.Error("INTEL_COORD",
            "Init: LiquidityEngine registered but not initialized");
         ok = false;
      }

      if(m_persistence == NULL)
      {
         Logger.Error("INTEL_COORD", "Init: RegimePersistenceModel not registered");
         ok = false;
      }
      else if(!m_persistence.IsInitialized())
      {
         Logger.Error("INTEL_COORD",
            "Init: RegimePersistenceModel registered but not initialized");
         ok = false;
      }

      if(m_trend == NULL)
      {
         Logger.Error("INTEL_COORD", "Init: TrendEngine not registered");
         ok = false;
      }
      else if(!m_trend.IsInitialized())
      {
         Logger.Error("INTEL_COORD",
            "Init: TrendEngine registered but not initialized");
         ok = false;
      }

      if(m_spread_guard == NULL)
      {
         Logger.Warn("INTEL_COORD",
            "Init: SpreadGuard not registered — VolatilityEngine will use "
            "fallback baseline");
         // Non-fatal — VolatilityEngine has VOL_BASELINE_FALLBACK
      }

      if(!ok)
      {
         Logger.Fatal("INTEL_COORD",
            "Required engines not ready — coordinator cannot operate");
         return false;
      }

      m_first_tick   = true;
      m_initialized  = true;
      m_update_count = 0;

      Logger.Info("INTEL_COORD",
         StringFormat("Initialized. symbol=%s pip=%.5f magic=%lld",
                       symbol, pip_size, magic));
      return true;
   }

   //===================================================================
   // UPDATE — called every tick from OnTick()
   //
   // PSEUDO-CODE — the hot path:
   //   if not initialized: return early
   //   detect bar boundaries (4× iTime + 4× datetime compare)
   //   if no boundaries and not first tick:
   //       return early — packet stays the same
   //   populate context
   //   run engine chain (in dependency order)
   //   assemble packet
   //   check staleness
   //   commit bar boundary timestamps
   //   log if state changed
   //   clear first_tick flag
   //===================================================================
   void Update()
   {
      if(!m_initialized) return;

      m_update_count++;

      // Build context shell — flags filled by DetectBarBoundaries
      IntelligenceContext ctx;
      ZeroMemory(ctx);

      DetectBarBoundaries(ctx);

      // Fast path: no bar closed and not first tick → return early.
      // Cached packet remains valid; downstream code reads what's there.
      if(!ShouldEvaluateChain(ctx)) return;

      // Slow path: at least one bar closed (or first tick).
      // Populate full context once — engines read from this snapshot.
      PopulateContext(ctx);

      // Run engines in dependency order
      EvaluateChain(ctx);

      // Assemble packet from engine outputs
      AssemblePacket();

      // Watchdog: mark engines stale if their last_eval_time is too old
      CheckStaleness();

      // Commit bar boundary timestamps now that engines have consumed them
      CommitBarBoundaries();

      // Log if anything important changed
      LogIfChanged();

      m_first_tick = false;
   }

   //===================================================================
   // GETPACKET — const reference accessor (ZERO copy)
   //
   // CRITICAL: returns reference, not value.
   // Phase 4 TradeScorer can read packet fields without paying
   // a ~8.6 KB struct copy on every read.
   //===================================================================
   IntelligencePacket GetPacket() const { return m_packet; }

   //===================================================================
   // ACCESSORS
   //===================================================================
   bool IsInitialized()           const { return m_initialized; }
   bool IsOperational()            const
   {
      return (m_packet_valid &&
              m_packet.intel_status == INTEL_OPERATIONAL);
   }
   int  GetUpdateCount()           const { return m_update_count; }
   int  GetAssemblyCount()         const { return m_assembly_count; }
   INTELLIGENCE_STATUS GetStatus() const { return m_packet.intel_status; }

   //===================================================================
   // SHUTDOWN
   //
   // PSEUDO-CODE:
   //   The coordinator does NOT shut down engines — main EA owns them
   //   and is responsible for engine lifecycle. Coordinator only clears
   //   its own state and logs final diagnostics.
   //===================================================================
   void Shutdown()
   {
      Logger.Info("INTEL_COORD",
         StringFormat("Shutdown. updates=%d assemblies=%d final_status=%s "
                       "final_regime=%s",
                       m_update_count, m_assembly_count,
                       EnumToString(m_packet.intel_status),
                       EnumToString(m_packet.confirmed_regime)));

      m_initialized  = false;
      m_packet_valid = false;
      // Do NOT call engine.Shutdown() here — main EA owns engine lifecycle
   }
};

//--- Global singleton
CIntelligenceCoordinator IntelligenceCoordinator;

#endif // CINTELLIGENCECOORDINATOR_MQH

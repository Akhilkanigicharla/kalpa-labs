
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Liquidity Engine                        |
//| File: Intelligence/CLiquidityEngine.mqh                           |
//| Purpose: Detect liquidity pools (Equal H/L, PDH/PDL, Asian H/L,   |
//|           Round Numbers) and per-pool sweep events. Two-layer     |
//|           design: pool detection + sweep state machine.           |
//| Phase: 3 — Step 7                                                 |
//|                                                                    |
//| ENGINE ID:  ENG_LIQUIDITY                                         |
//|                                                                    |
//| CORE DESIGN — Pools vs Sweeps ARE SEPARATE CONCEPTS:              |
//|   Pool = static price level where liquidity sits                  |
//|   Sweep = dynamic event requiring pierce + reclose in window      |
//|                                                                    |
//| POOL TYPES (7 kinds, 3 tiers):                                    |
//|   Tier 1 (window=3 M15): PDH, PDL, Asian High, Asian Low          |
//|   Tier 2 (window=2 M15): Equal Highs, Equal Lows                  |
//|   Tier 3 (window=1 M15): Round Numbers                            |
//|                                                                    |
//| SWEEP STATE MACHINE (per pool):                                   |
//|   CLEAN → PIERCED → SWEPT_PENDING → SWEPT_CONFIRMED               |
//|                              or → BROKEN (window expired)         |
//|                                                                    |
//| POOL DECAY (Equal H/L only, per requirement):                     |
//|   Two consecutive M15 closes > 30 pips beyond level → inactive    |
//|                                                                    |
//| TOUCH COUNTING:                                                    |
//|   Wick within 5 pips of level, without breach → touch++            |
//|   Sweeps do NOT count as touches (separate event)                  |
//|                                                                    |
//| VOLUME: NOT USED — price and structure only per user requirement  |
//|                                                                    |
//| STRICT BOUNDARIES:                                                 |
//|   - Observations only. No entries. No exits.                      |
//|   - No trade decisions. No scoring adjustments.                   |
//|   - Phase 4 owns all decision-making.                             |
//+------------------------------------------------------------------+
#ifndef CLIQUIDITYENGINE_MQH
#define CLIQUIDITYENGINE_MQH

#include "IIntelligenceEngine.mqh"

//===================================================================
// INTERNAL: Sweep Event Record
//
// Used for the ring buffer of recent confirmed sweeps.
// Not exposed to LiquidityResult directly — Result exposes only the
// most recent event's fields.
//===================================================================
struct SweepEventRecord
{
   POOL_TYPE     pool_type;
   double        pool_price;
   TRADE_DIR     reversal_direction;
   double        strength;
   datetime      occurred_at;
   int           pierce_bar_idx;   // M15 bar # of pierce
   int           swept_bar_idx;    // M15 bar # of confirmed reclose
   double        wick_extreme;
};

class CLiquidityEngine : public IIntelligenceEngine
{
private:
   //--- Active pool list (fixed-size, LRU eviction on overflow)
   LiquidityPool    m_pools[LIQ_ACTIVE_POOLS_MAX];
   int              m_pool_count;

   //--- Sweep event ring buffer (recent confirmed sweeps)
   SweepEventRecord m_sweep_buffer[LIQ_SWEEP_EVENT_BUFFER];
   int              m_sweep_write_idx;
   int              m_sweep_count;   // Total events since init (for wrap-safety)

   //--- Bar boundary tracking (avoid double-processing)
   datetime         m_last_processed_m15_bar;
   int              m_current_m15_bar_idx;   // Monotonic counter for window math

   //--- Daily / session tracking
   MqlDateTime      m_last_day_processed;    // For PDH/PDL daily refresh
   datetime         m_last_asian_computed;   // For Asian H/L session refresh
   double           m_asian_high;
   double           m_asian_low;
   bool             m_asian_valid;

   //--- Injected dependency inputs (copies, not pointers)
   StructureResult  m_last_structure;
   VolatilityResult m_last_volatility;
   bool             m_structure_provided;
   bool             m_volatility_provided;

   //--- Cached result
   LiquidityResult  m_cached;
   bool             m_cache_valid;

   //--- Diagnostics
   int              m_pools_added_total;
   int              m_pools_decayed_total;
   int              m_sweeps_confirmed_total;
   int              m_sweeps_broken_total;

   //===================================================================
   // POOL LIST MANAGEMENT
   //===================================================================

   //--- Find existing pool of the same type at approximately the same price
   //    Returns index or -1 if not found. Matches within LIQ_EQUAL_PIPS_TOL for
   //    price-based clusters, tighter for exact-level types (PDH/PDL/Round).
   int FindExistingPool(POOL_TYPE type, double price) const
   {
      double tol_pips = (type == POOL_EQUAL_HIGHS || type == POOL_EQUAL_LOWS)
                         ? LIQ_EQUAL_PIPS_TOL
                         : 1.0;  // very tight for exact levels

      double tol_price = PipsToPrice(tol_pips);

      for(int i = 0; i < m_pool_count; i++)
      {
         if(!m_pools[i].active) continue;
         if(m_pools[i].type != type) continue;
         if(MathAbs(m_pools[i].price_level - price) <= tol_price) return i;
      }
      return -1;
   }

   //--- Add new pool OR update existing one at same level
   //    LRU eviction if list full: remove pool with lowest touch_count and oldest formed_at
   void AddOrUpdatePool(POOL_TYPE type, double price, int initial_touches, bool is_upside)
   {
      // 1) Try to update existing pool at same level
      int existing = FindExistingPool(type, price);
      if(existing >= 0)
      {
         // Refresh: bump touch count if not already tracked as a fresh detection
         // For rediscovery of same level, we don't force touch increment —
         // that comes from actual price interaction in UpdateTouchCounts
         return;
      }

      // 2) Find a free slot (inactive or unused)
      int slot = -1;
      for(int i = 0; i < LIQ_ACTIVE_POOLS_MAX; i++)
      {
         if(i >= m_pool_count || !m_pools[i].active)
         {
            slot = i;
            break;
         }
      }

      // 3) No free slot — LRU eviction
      if(slot < 0)
      {
         int victim = FindEvictionCandidate();
         if(victim < 0)
         {
            Logger.Warn("LIQUIDITY",
               "Pool list full and no eviction candidate — dropping new pool");
            return;
         }
         Logger.Debug("LIQUIDITY",
            StringFormat("Evicting pool: type=%s price=%.5f touches=%d",
                          EnumToString(m_pools[victim].type),
                          m_pools[victim].price_level,
                          m_pools[victim].touch_count));
         slot = victim;
      }

      // 4) Populate the slot
      LiquidityPool p;
      ZeroMemory(p);
      p.type              = type;
      p.price_level       = price;
      p.width_pips        = (type == POOL_EQUAL_HIGHS || type == POOL_EQUAL_LOWS)
                             ? LIQ_EQUAL_PIPS_TOL : 1.0;
      p.formed_at         = TimeCurrent();
      p.touch_count       = MathMax(1, MathMin(initial_touches, LIQ_TOUCH_COUNT_CAP));
      p.is_upside         = is_upside;
      p.active            = true;
      p.sweep_state       = SWEEP_CLEAN;
      p.pierced_at        = 0;
      p.pierce_bar_idx    = -1;
      p.pierce_extreme    = 0.0;
      p.swept_at          = 0;
      p.decay_close_count = 0;

      m_pools[slot] = p;
      if(slot >= m_pool_count) m_pool_count = slot + 1;
      m_pools_added_total++;

      Logger.Debug("LIQUIDITY",
         StringFormat("Pool added: type=%s price=%.5f touches=%d upside=%d",
                       EnumToString(type), price, p.touch_count, (int)is_upside));
   }

   //--- LRU eviction: lowest touch_count, then oldest formed_at, prefer non-Tier 1
   int FindEvictionCandidate() const
   {
      int best = -1;
      int best_touches = 999;
      datetime best_formed = TimeCurrent();

      for(int i = 0; i < m_pool_count; i++)
      {
         if(!m_pools[i].active) continue;
         // Prefer to keep Tier 1 pools (PDH/PDL/Asian) — evict others first
         bool is_tier1 = IsTier1(m_pools[i].type);
         if(is_tier1 && best >= 0 && !IsTier1(m_pools[best].type)) continue;

         if(m_pools[i].touch_count < best_touches ||
            (m_pools[i].touch_count == best_touches && m_pools[i].formed_at < best_formed))
         {
            best = i;
            best_touches = m_pools[i].touch_count;
            best_formed  = m_pools[i].formed_at;
         }
      }
      return best;
   }

   //--- Compact pool array by removing inactive entries
   //    Called periodically to keep m_pool_count meaningful
   void CompactPools()
   {
      int write = 0;
      for(int read = 0; read < m_pool_count; read++)
      {
         if(m_pools[read].active)
         {
            if(write != read) m_pools[write] = m_pools[read];
            write++;
         }
      }
      // Clear tail
      for(int i = write; i < m_pool_count; i++)
      {
         ZeroMemory(m_pools[i]);
      }
      m_pool_count = write;
   }

   //--- Tier classification (drives sweep window)
   bool IsTier1(POOL_TYPE t) const
   {
      return (t == POOL_PDH || t == POOL_PDL ||
              t == POOL_ASIAN_HIGH || t == POOL_ASIAN_LOW);
   }
   bool IsTier2(POOL_TYPE t) const
   {
      return (t == POOL_EQUAL_HIGHS || t == POOL_EQUAL_LOWS);
   }
   bool IsTier3(POOL_TYPE t) const { return (t == POOL_ROUND); }

   int GetSweepWindow(POOL_TYPE t) const
   {
      if(IsTier1(t)) return LIQ_SWEEP_WINDOW_TIER1;
      if(IsTier2(t)) return LIQ_SWEEP_WINDOW_TIER2;
      return LIQ_SWEEP_WINDOW_TIER3;
   }

   //===================================================================
   // POOL DETECTION — TIER 1: PDH / PDL
   //
   // PSEUDO-CODE:
   //   Called once per day at 00:00 GMT crossing (or on first tick).
   //   iHigh(D1, 1) = high of prior calendar day.
   //   iLow(D1, 1)  = low  of prior calendar day.
   //===================================================================
   void DetectPDH_PDL()
   {
      double pdh[], pdl[];
      ArrayResize(pdh, 1); ArrayResize(pdl, 1);
      ArraySetAsSeries(pdh, true);
      ArraySetAsSeries(pdl, true);

      int nh = CopyHigh(m_symbol, PERIOD_D1, 1, 1, pdh);
      int nl = CopyLow(m_symbol,  PERIOD_D1, 1, 1, pdl);

      if(nh <= 0 || nl <= 0 || pdh[0] <= 0 || pdl[0] <= 0)
      {
         Logger.Debug("LIQUIDITY", "PDH/PDL detection: D1 data unavailable");
         return;
      }

      // Deactivate any prior-day PDH/PDL pools (they've expired at day rollover)
      for(int i = 0; i < m_pool_count; i++)
      {
         if(m_pools[i].active &&
            (m_pools[i].type == POOL_PDH || m_pools[i].type == POOL_PDL))
         {
            m_pools[i].active = false;
         }
      }

      AddOrUpdatePool(POOL_PDH, pdh[0], 1, true);
      AddOrUpdatePool(POOL_PDL, pdl[0], 1, false);

      Logger.Info("LIQUIDITY",
         StringFormat("PDH/PDL refreshed: PDH=%.5f PDL=%.5f", pdh[0], pdl[0]));
   }

   //===================================================================
   // POOL DETECTION — TIER 1: Asian High / Low
   //
   // PSEUDO-CODE:
   //   Asian session: 22:00 GMT prior day → 06:00 GMT current day.
   //   Called when 06:00 GMT boundary is crossed (or on first tick if
   //   we're currently after 06:00).
   //
   //   Scan M1 bars over the last 8 hours (480 M1 bars).
   //   Filter to only those within the Asian window by GMT hour.
   //   High/Low = extremes across the filtered set.
   //===================================================================
   void DetectAsianHighLow()
   {
      double highs[], lows[];
      datetime times[];
      ArraySetAsSeries(highs, true);
      ArraySetAsSeries(lows,  true);
      ArraySetAsSeries(times, true);

      int nh = CopyHigh(m_symbol, PERIOD_M1, 1, LIQ_ASIAN_M1_LOOKBACK, highs);
      int nl = CopyLow(m_symbol,  PERIOD_M1, 1, LIQ_ASIAN_M1_LOOKBACK, lows);
      int nt = CopyTime(m_symbol, PERIOD_M1, 1, LIQ_ASIAN_M1_LOOKBACK, times);

      int n = MathMin(MathMin(nh, nl), nt);
      if(n < 60)
      {
         Logger.Debug("LIQUIDITY",
            StringFormat("Asian H/L detection: insufficient M1 data (n=%d)", n));
         return;
      }

      double ah = 0.0, al = 0.0;
      bool have_data = false;

      for(int i = 0; i < n; i++)
      {
         MqlDateTime tm;
         TimeToStruct(times[i], tm);
         // Convert to GMT: TimeGMT may not equal server time.
         // We assume broker time approximates GMT+offset. For now,
         // use TimeGMT approximation via TimeCurrent-TimeGMT delta.
         // Simpler + acceptable: server bars are used, and Asian range on
         // GOLD is 22:00–06:00 server-side for most brokers using UTC+0/+2.
         // We use raw hour from bar time — this is broker-server hour.
         // Full GMT alignment is done via the Session detection code elsewhere.
         int hr = tm.hour;

         // Asian window: hour >= 22 OR hour < 6
         bool in_asian = (hr >= LIQ_ASIAN_START_HR || hr < LIQ_ASIAN_END_HR);
         if(!in_asian) continue;

         if(!have_data)
         {
            ah = highs[i];
            al = lows[i];
            have_data = true;
         }
         else
         {
            if(highs[i] > ah) ah = highs[i];
            if(lows[i]  < al) al = lows[i];
         }
      }

      if(!have_data || ah <= 0 || al <= 0)
      {
         Logger.Debug("LIQUIDITY", "Asian H/L detection: no bars matched window");
         return;
      }

      // Deactivate prior Asian pools
      for(int i = 0; i < m_pool_count; i++)
      {
         if(m_pools[i].active &&
            (m_pools[i].type == POOL_ASIAN_HIGH || m_pools[i].type == POOL_ASIAN_LOW))
         {
            m_pools[i].active = false;
         }
      }

      AddOrUpdatePool(POOL_ASIAN_HIGH, ah, 1, true);
      AddOrUpdatePool(POOL_ASIAN_LOW,  al, 1, false);
      m_asian_high  = ah;
      m_asian_low   = al;
      m_asian_valid = true;

      Logger.Info("LIQUIDITY",
         StringFormat("Asian H/L refreshed: high=%.5f low=%.5f", ah, al));
   }

   //===================================================================
   // POOL DETECTION — TIER 2: Equal Highs / Equal Lows
   //
   // PSEUDO-CODE:
   //   Uses injected StructureResult.
   //   For each timeframe (H1, M15):
   //     Iterate confirmed swing highs — cluster within LIQ_EQUAL_PIPS_TOL (3 pips)
   //     For any cluster of size >= LIQ_EQUAL_MIN_SWINGS (2):
   //       Compute cluster average price
   //       Add/update pool with touch_count = cluster size
   //     Mirror for swing lows.
   //
   //   Access pattern: StructureResult exposes h1 and m15 snapshots each
   //   containing confirmed_highs[] and confirmed_lows[] arrays.
   //===================================================================
   void DetectEqualHighsLows()
   {
      if(!m_structure_provided) return;

      // Process H1 timeframe
      if(m_last_structure.h1_available)
      {
         DetectEqualsForSnapshot(m_last_structure.h1, true);   // highs
         DetectEqualsForSnapshot(m_last_structure.h1, false);  // lows
      }
      // Process M15 timeframe
      if(m_last_structure.m15_available)
      {
         DetectEqualsForSnapshot(m_last_structure.m15, true);
         DetectEqualsForSnapshot(m_last_structure.m15, false);
      }
   }

   //--- Cluster swings within tolerance, create pools for clusters >= min size
   void DetectEqualsForSnapshot(const StructureSnapshot &snap, bool for_highs)
   {
      int count = for_highs ? snap.high_count : snap.low_count;
      if(count < LIQ_EQUAL_MIN_SWINGS) return;

      // Read only the most recent 20 swings — older ones are irrelevant
      int scan_max = MathMin(count, 20);
      double tol_price = PipsToPrice(LIQ_EQUAL_PIPS_TOL);

      // For each swing, count how many other swings are within tolerance
      // This detects clusters. A single swing being "close to" many others
      // means it's part of a cluster.
      for(int i = 0; i < scan_max; i++)
      {
         double p_i = for_highs ? snap.confirmed_highs[i].price
                                 : snap.confirmed_lows[i].price;
         if(p_i <= 0) continue;

         int in_cluster = 1;
         double sum = p_i;

         for(int j = 0; j < scan_max; j++)
         {
            if(i == j) continue;
            double p_j = for_highs ? snap.confirmed_highs[j].price
                                    : snap.confirmed_lows[j].price;
            if(p_j <= 0) continue;
            if(MathAbs(p_i - p_j) <= tol_price)
            {
               in_cluster++;
               sum += p_j;
            }
         }

         if(in_cluster >= LIQ_EQUAL_MIN_SWINGS)
         {
            double avg = sum / (double)in_cluster;
            POOL_TYPE ptype = for_highs ? POOL_EQUAL_HIGHS : POOL_EQUAL_LOWS;
            // Cap touches at LIQ_TOUCH_COUNT_CAP inside AddOrUpdatePool
            AddOrUpdatePool(ptype, avg, in_cluster, for_highs);
         }
      }
   }

   //===================================================================
   // POOL DETECTION — TIER 3: Round Numbers
   //
   // PSEUDO-CODE:
   //   Round numbers are $XX00 and $XX50 levels (ROUND_NUM_STEP = 50).
   //   Compute levels within LIQ_ROUND_LOOKUP_RANGE (200 pips) of current price.
   //   Deactivate round pools outside range, add new ones inside.
   //===================================================================
   void UpdateRoundNumbers(double current_price)
   {
      if(current_price <= 0) return;

      double range_price = PipsToPrice(LIQ_ROUND_LOOKUP_RANGE);
      double step_price  = PipsToPrice(ROUND_NUM_STEP);
      double lo = current_price - range_price;
      double hi = current_price + range_price;

      // Deactivate round pools outside range
      for(int i = 0; i < m_pool_count; i++)
      {
         if(m_pools[i].active && m_pools[i].type == POOL_ROUND)
         {
            if(m_pools[i].price_level < lo || m_pools[i].price_level > hi)
            {
               m_pools[i].active = false;
            }
         }
      }

      // Add round levels within range
      // First round level at or below lo
      double first_level = MathFloor(lo / step_price) * step_price;
      double level = first_level;
      int guard = 0;
      while(level <= hi && guard < 20)
      {
         if(level >= lo && level > 0)
         {
            bool is_upside = (level >= current_price);
            AddOrUpdatePool(POOL_ROUND, level, 1, is_upside);
         }
         level += step_price;
         guard++;
      }
   }

   //===================================================================
   // TOUCH COUNTING
   //
   // PSEUDO-CODE:
   //   For each active pool, check if last M15 bar's wick approached the level.
   //   Touch = wick within LIQ_TOUCH_TOL_PIPS but did NOT breach the level.
   //   Note: breach = wick past level. That's a pierce (sweep state machine),
   //         not a touch.
   //   Touches cap at LIQ_TOUCH_COUNT_CAP.
   //   Called per M15 close AFTER new bar detected.
   //===================================================================
   void UpdateTouchCounts(double last_high, double last_low)
   {
      if(last_high <= 0 || last_low <= 0) return;
      double tol = PipsToPrice(LIQ_TOUCH_TOL_PIPS);

      for(int i = 0; i < m_pool_count; i++)
      {
         if(!m_pools[i].active) continue;

         double lvl = m_pools[i].price_level;

         if(m_pools[i].is_upside)
         {
            // Wick approached from below without breaching
            if(last_high >= lvl - tol && last_high < lvl)
            {
               if(m_pools[i].touch_count < LIQ_TOUCH_COUNT_CAP)
                  m_pools[i].touch_count++;
            }
         }
         else
         {
            // Wick approached from above without breaching
            if(last_low <= lvl + tol && last_low > lvl)
            {
               if(m_pools[i].touch_count < LIQ_TOUCH_COUNT_CAP)
                  m_pools[i].touch_count++;
            }
         }
      }
   }

   //===================================================================
   // POOL DECAY (Equal Highs/Lows only, per requirement)
   //
   // PSEUDO-CODE:
   //   Two consecutive M15 closes more than LIQ_DECAY_PIPS beyond level.
   //   For upside pools: closes ABOVE level + 30 pips = decay
   //   For downside pools: closes BELOW level - 30 pips = decay
   //
   //   Uses decay_close_count counter — resets if a close is within the level.
   //===================================================================
   void DecayPools(double last_close, double prev_close)
   {
      if(last_close <= 0 || prev_close <= 0) return;
      double decay_price = PipsToPrice(LIQ_DECAY_PIPS);

      for(int i = 0; i < m_pool_count; i++)
      {
         if(!m_pools[i].active) continue;
         // Only Equal H/L decay this way — others expire on cadence
         if(m_pools[i].type != POOL_EQUAL_HIGHS &&
            m_pools[i].type != POOL_EQUAL_LOWS) continue;

         double lvl = m_pools[i].price_level;
         bool beyond_last, beyond_prev;

         if(m_pools[i].is_upside)
         {
            beyond_last = (last_close > lvl + decay_price);
            beyond_prev = (prev_close > lvl + decay_price);
         }
         else
         {
            beyond_last = (last_close < lvl - decay_price);
            beyond_prev = (prev_close < lvl - decay_price);
         }

         if(beyond_last && beyond_prev)
         {
            m_pools[i].active = false;
            m_pools_decayed_total++;
            Logger.Debug("LIQUIDITY",
               StringFormat("Pool decayed (2 closes beyond): type=%s price=%.5f",
                             EnumToString(m_pools[i].type), lvl));
         }
      }
   }

   //===================================================================
   // SWEEP STATE MACHINE
   //
   // PSEUDO-CODE:
   //   For each active pool, advance state based on last M15 candle.
   //   State transitions:
   //     CLEAN → PIERCED  (wick crossed level, pierce > noise threshold)
   //     PIERCED → SWEPT_CONFIRMED  (close back inside range, same bar)
   //     PIERCED → SWEPT_PENDING    (wick, no reclose yet, still in window)
   //     SWEPT_PENDING → SWEPT_CONFIRMED  (reclose inside window)
   //     SWEPT_PENDING → BROKEN     (window expired without reclose)
   //     SWEPT_CONFIRMED → BROKEN   (subsequent close beyond level)
   //     BROKEN = terminal
   //
   //   Bull-side sweep: upside pool, wick above level, reclose below.
   //   Reversal direction after bull-side sweep = DIR_SHORT (bearish reversal).
   //   Bear-side sweep: downside pool, wick below level, reclose above.
   //   Reversal direction after bear-side sweep = DIR_LONG (bullish reversal).
   //===================================================================
   void AdvanceSweepStates(double last_h, double last_l, double last_c,
                            int current_bar_idx)
   {
      if(last_h <= 0 || last_l <= 0 || last_c <= 0) return;
      double noise = PipsToPrice(LIQ_WICK_MIN_PIP_NOISE);

      for(int i = 0; i < m_pool_count; i++)
      {
         if(!m_pools[i].active) continue;
         if(m_pools[i].sweep_state == SWEEP_BROKEN) continue;

         double lvl    = m_pools[i].price_level;
         int    window = GetSweepWindow(m_pools[i].type);

         if(m_pools[i].is_upside)
         {
            bool wicked_through = (last_h > lvl + noise);
            bool closed_below   = (last_c < lvl);
            bool closed_above   = (last_c > lvl);

            switch(m_pools[i].sweep_state)
            {
               case SWEEP_CLEAN:
                  if(wicked_through)
                  {
                     m_pools[i].sweep_state    = SWEEP_PIERCED;
                     m_pools[i].pierced_at     = TimeCurrent();
                     m_pools[i].pierce_bar_idx = current_bar_idx;
                     m_pools[i].pierce_extreme = last_h;

                     if(closed_below)
                     {
                        // Same-bar pierce + reclose → confirmed sweep
                        ConfirmSweep(i, current_bar_idx);
                     }
                  }
                  break;

               case SWEEP_PIERCED:
               case SWEEP_SWEPT_PENDING:
                  {
                     // Update pierce extreme if this bar wicked further
                     if(wicked_through && last_h > m_pools[i].pierce_extreme)
                        m_pools[i].pierce_extreme = last_h;

                     int bars_since = current_bar_idx - m_pools[i].pierce_bar_idx;

                     if(closed_below)
                     {
                        ConfirmSweep(i, current_bar_idx);
                     }
                     else if(bars_since >= window)
                     {
                        m_pools[i].sweep_state = SWEEP_BROKEN;
                        m_sweeps_broken_total++;
                        Logger.Debug("LIQUIDITY",
                           StringFormat("Pool BROKEN (window expired): type=%s price=%.5f bars=%d",
                                         EnumToString(m_pools[i].type), lvl, bars_since));
                     }
                     else
                     {
                        m_pools[i].sweep_state = SWEEP_SWEPT_PENDING;
                     }
                  }
                  break;

               case SWEEP_SWEPT_CONFIRMED:
                  // Already swept — check if genuine break follows
                  if(closed_above && last_c > lvl + PipsToPrice(LIQ_DECAY_PIPS))
                  {
                     m_pools[i].sweep_state = SWEEP_BROKEN;
                     Logger.Debug("LIQUIDITY",
                        StringFormat("Post-sweep break: type=%s price=%.5f",
                                      EnumToString(m_pools[i].type), lvl));
                  }
                  break;

               default: break;
            }
         }
         else  // downside pool
         {
            bool wicked_through = (last_l < lvl - noise);
            bool closed_above   = (last_c > lvl);
            bool closed_below   = (last_c < lvl);

            switch(m_pools[i].sweep_state)
            {
               case SWEEP_CLEAN:
                  if(wicked_through)
                  {
                     m_pools[i].sweep_state    = SWEEP_PIERCED;
                     m_pools[i].pierced_at     = TimeCurrent();
                     m_pools[i].pierce_bar_idx = current_bar_idx;
                     m_pools[i].pierce_extreme = last_l;

                     if(closed_above)
                        ConfirmSweep(i, current_bar_idx);
                  }
                  break;

               case SWEEP_PIERCED:
               case SWEEP_SWEPT_PENDING:
                  {
                     if(wicked_through && last_l < m_pools[i].pierce_extreme)
                        m_pools[i].pierce_extreme = last_l;

                     int bars_since = current_bar_idx - m_pools[i].pierce_bar_idx;

                     if(closed_above)
                     {
                        ConfirmSweep(i, current_bar_idx);
                     }
                     else if(bars_since >= window)
                     {
                        m_pools[i].sweep_state = SWEEP_BROKEN;
                        m_sweeps_broken_total++;
                     }
                     else
                     {
                        m_pools[i].sweep_state = SWEEP_SWEPT_PENDING;
                     }
                  }
                  break;

               case SWEEP_SWEPT_CONFIRMED:
                  if(closed_below && last_c < lvl - PipsToPrice(LIQ_DECAY_PIPS))
                  {
                     m_pools[i].sweep_state = SWEEP_BROKEN;
                  }
                  break;

               default: break;
            }
         }
      }
   }

   //--- Confirm sweep on pool at index i
   void ConfirmSweep(int i, int current_bar_idx)
   {
      m_pools[i].sweep_state = SWEEP_SWEPT_CONFIRMED;
      m_pools[i].swept_at    = TimeCurrent();
      m_sweeps_confirmed_total++;

      // Record event
      SweepEventRecord ev;
      ZeroMemory(ev);
      ev.pool_type          = m_pools[i].type;
      ev.pool_price         = m_pools[i].price_level;
      // Reversal direction is OPPOSITE of the sweep side:
      //   upside pool wicked = bull-side sweep → bear reversal → DIR_SHORT
      //   downside pool wicked = bear-side sweep → bull reversal → DIR_LONG
      ev.reversal_direction = m_pools[i].is_upside ? DIR_SHORT : DIR_LONG;
      ev.occurred_at        = TimeCurrent();
      ev.pierce_bar_idx     = m_pools[i].pierce_bar_idx;
      ev.swept_bar_idx      = current_bar_idx;
      ev.wick_extreme       = m_pools[i].pierce_extreme;
      ev.strength           = ComputeSweepStrength(m_pools[i], ev);

      // Push into ring buffer
      m_sweep_buffer[m_sweep_write_idx] = ev;
      m_sweep_write_idx = (m_sweep_write_idx + 1) % LIQ_SWEEP_EVENT_BUFFER;
      m_sweep_count++;

      Logger.Info("LIQUIDITY",
         StringFormat("SWEEP CONFIRMED: type=%s price=%.5f dir=%s strength=%.2f",
                       EnumToString(ev.pool_type), ev.pool_price,
                       EnumToString(ev.reversal_direction), ev.strength));
   }

   //===================================================================
   // SWEEP STRENGTH
   //
   // PSEUDO-CODE:
   //   sweep_strength = (wick_depth × 0.40) +
   //                    (close_speed × 0.30) +
   //                    (pool_quality × 0.30)
   //
   //   wick_depth: (wick past pool in pips) / ATR_M15_pips.
   //     Clamp to [0, 2] then divide by 2 → normalized [0, 1].
   //     A 2×ATR pierce = full 1.0.
   //   close_speed:
   //     candles_to_reclose = swept_bar - pierce_bar
   //     0 or 1 → 1.0 (same-bar or immediate next-bar reclose)
   //     2      → 0.5
   //     3+     → 0.33
   //   pool_quality: from ComputePoolQuality (touch-count adjusted)
   //
   //   Fallback: if ATR unavailable, use LIQ_ATR_FALLBACK_PIPS (15).
   //===================================================================
   double ComputeSweepStrength(const LiquidityPool &pool, const SweepEventRecord &ev) const
   {
      // Wick depth
      double wick_pips = pool.is_upside
                         ? PriceToPips(ev.wick_extreme - pool.price_level)
                         : PriceToPips(pool.price_level - ev.wick_extreme);
      double atr_pips = (m_volatility_provided && m_last_volatility.is_valid &&
                         m_last_volatility.atr_m15_pips > 0)
                        ? m_last_volatility.atr_m15_pips
                        : LIQ_ATR_FALLBACK_PIPS;
      double wick_norm = MathMax(0.0, MathMin(2.0, wick_pips / atr_pips)) / 2.0;

      // Close speed
      int candles = ev.swept_bar_idx - ev.pierce_bar_idx;
      double close_speed;
      if(candles <= 1)      close_speed = 1.0;
      else if(candles == 2) close_speed = 0.5;
      else                  close_speed = 0.33;

      // Pool quality
      double pool_q = ComputePoolQuality(pool);

      return (wick_norm * 0.40) + (close_speed * 0.30) + (pool_q * 0.30);
   }

   //===================================================================
   // POOL QUALITY (0.0–1.0) — factors in touch_count
   //
   // PSEUDO-CODE:
   //   Base by type, bonus per touch above baseline, capped:
   //     PDH/PDL:          base=0.85, +0.05 per touch, cap=1.00
   //     Asian H/L:        base=0.75, +0.05 per touch, cap=0.95
   //     Equal H/L:        base=0.55, +0.10 per touch above 2, cap=0.95
   //     Round Numbers:    base=0.40, +0.05 per touch, cap=0.70
   //===================================================================
   double ComputePoolQuality(const LiquidityPool &pool) const
   {
      double base = 0.0, bonus_per = 0.0, cap = 1.0;
      int touches_over_base = MathMax(0, pool.touch_count - 1);

      switch(pool.type)
      {
         case POOL_PDH:
         case POOL_PDL:
            base = 0.85; bonus_per = 0.05; cap = 1.00; break;
         case POOL_ASIAN_HIGH:
         case POOL_ASIAN_LOW:
            base = 0.75; bonus_per = 0.05; cap = 0.95; break;
         case POOL_EQUAL_HIGHS:
         case POOL_EQUAL_LOWS:
            base = 0.55; bonus_per = 0.10; cap = 0.95;
            touches_over_base = MathMax(0, pool.touch_count - 2);
            break;
         case POOL_ROUND:
            base = 0.40; bonus_per = 0.05; cap = 0.70; break;
         default:
            return 0.0;
      }

      double q = base + (bonus_per * (double)touches_over_base);
      return MathMin(cap, q);
   }

   //===================================================================
   // CADENCE HELPERS
   //===================================================================

   //--- Has calendar day changed since m_last_day_processed?
   bool IsNewCalendarDay(datetime now) const
   {
      MqlDateTime cur;
      TimeToStruct(now, cur);
      return (cur.day != m_last_day_processed.day ||
              cur.mon != m_last_day_processed.mon ||
              cur.year != m_last_day_processed.year);
   }

   //--- Has Asian session just ended (06:00 GMT crossed since last computed)?
   bool ShouldRecomputeAsian(datetime now) const
   {
      MqlDateTime cur;
      TimeToStruct(now, cur);
      // Cross the 06:00 boundary at least once per day
      if(m_last_asian_computed == 0) return true;
      int hours_since = (int)((now - m_last_asian_computed) / 3600);
      if(hours_since < 12) return false;  // Once per 12h at most
      // Prefer recomputation shortly after 06:00 GMT
      return (cur.hour >= LIQ_ASIAN_END_HR && cur.hour < LIQ_ASIAN_END_HR + 3);
   }

   //===================================================================
   // RESULT BUILDER
   //===================================================================
   void BuildResult(double current_price)
   {
      LiquidityResult r;
      ZeroMemory(r);
      r.evaluated_at = TimeCurrent();

      // Compact and count
      CompactPools();
      r.pool_count = m_pool_count;

      // Find nearest pool of any type, plus nearest resistance/support
      double nearest_dist  = 1e18;
      int    nearest_idx   = -1;
      double nearest_res   = 1e18;  // upside distance (pips)
      double nearest_sup   = 1e18;  // downside distance (pips)
      int    nearest_res_i = -1;
      int    nearest_sup_i = -1;

      for(int i = 0; i < m_pool_count; i++)
      {
         if(!m_pools[i].active) continue;
         double d_pips = PriceToPips(MathAbs(m_pools[i].price_level - current_price));
         if(d_pips < nearest_dist)
         {
            nearest_dist = d_pips;
            nearest_idx  = i;
         }
         if(m_pools[i].is_upside && m_pools[i].price_level > current_price)
         {
            if(d_pips < nearest_res) { nearest_res = d_pips; nearest_res_i = i; }
         }
         if(!m_pools[i].is_upside && m_pools[i].price_level < current_price)
         {
            if(d_pips < nearest_sup) { nearest_sup = d_pips; nearest_sup_i = i; }
         }
      }

      r.distance_to_nearest_pool = (nearest_idx >= 0) ? nearest_dist : 0.0;
      r.pool_detected = (nearest_idx >= 0 && nearest_dist <= LIQ_POOL_PROXIMITY_PIPS);
      if(nearest_idx >= 0)
      {
         r.nearest_pool_type    = m_pools[nearest_idx].type;
         r.nearest_pool_touches = m_pools[nearest_idx].touch_count;
         r.nearest_pool_price   = m_pools[nearest_idx].price_level;
      }
      else
      {
         r.nearest_pool_type    = POOL_NONE;
         r.nearest_pool_touches = 0;
         r.nearest_pool_price   = 0.0;
      }

      r.nearest_resistance_pips  = (nearest_res_i >= 0) ? nearest_res : 0.0;
      r.nearest_support_pips     = (nearest_sup_i >= 0) ? nearest_sup : 0.0;
      r.nearest_resistance_price = (nearest_res_i >= 0)
                                    ? m_pools[nearest_res_i].price_level : 0.0;
      r.nearest_support_price    = (nearest_sup_i >= 0)
                                    ? m_pools[nearest_sup_i].price_level : 0.0;

      // Copy active pool list (up to LIQ_ACTIVE_POOLS_MAX)
      for(int i = 0; i < LIQ_ACTIVE_POOLS_MAX; i++)
      {
         if(i < m_pool_count) r.active_pools[i] = m_pools[i];
         else                 ZeroMemory(r.active_pools[i]);
      }

      // Most recent confirmed sweep within relevance window
      r.sweep_detected = false;
      int events_to_check = MathMin(m_sweep_count, LIQ_SWEEP_EVENT_BUFFER);
      for(int k = 0; k < events_to_check; k++)
      {
         int idx = (m_sweep_write_idx - 1 - k + LIQ_SWEEP_EVENT_BUFFER)
                   % LIQ_SWEEP_EVENT_BUFFER;
         SweepEventRecord ev = m_sweep_buffer[idx];
         int bars_ago = m_current_m15_bar_idx - ev.swept_bar_idx;
         if(bars_ago < 0) continue;  // safety
         if(bars_ago > LIQ_SWEEP_RELEVANCE_BARS) continue;

         r.sweep_detected     = true;
         r.sweep_direction    = ev.reversal_direction;
         r.sweep_strength     = ev.strength;
         r.sweep_candles_ago  = bars_ago;
         r.swept_pool_type    = ev.pool_type;
         r.swept_pool_price   = ev.pool_price;
         break;   // newest match wins
      }

      // Environment score (0-1) — combines proximity and sweep freshness
      // Phase 4 may or may not use this. It's an observation summary.
      double score = 1.0;
      if(r.pool_detected)
      {
         // Being close to strong pools reduces "clean environment" score
         double lvl_quality = (nearest_idx >= 0)
                              ? ComputePoolQuality(m_pools[nearest_idx]) : 0.0;
         double prox_penalty = (1.0 - (nearest_dist / LIQ_POOL_PROXIMITY_PIPS)) * lvl_quality;
         score -= (0.5 * prox_penalty);
      }
      if(r.sweep_detected)
      {
         // Fresh sweep events reduce the "clean" score — the environment
         // has known active liquidity activity. Phase 4 interprets sign.
         score -= (0.3 * r.sweep_strength);
      }
      r.score = MathMax(0.0, MathMin(1.0, score));

      // State classification
      if(!m_structure_provided && !m_volatility_provided && m_pool_count == 0)
      {
         r.state          = LIQ_UNKNOWN;
         r.is_valid       = true;
         r.invalid_reason = "no_inputs_yet";
      }
      else if(r.sweep_detected)
      {
         r.state = LIQ_POST_SWEEP;
      }
      else if(!r.pool_detected)
      {
         r.state = LIQ_CLEAN;
      }
      else if(r.score >= 0.75)
      {
         r.state = LIQ_NEUTRAL;
      }
      else if(r.score >= 0.55)
      {
         r.state = LIQ_UNFAVORABLE;
      }
      else if(r.score >= 0.30)
      {
         r.state = LIQ_UNFAVORABLE;
      }
      else
      {
         r.state = LIQ_DANGEROUS;
      }

      r.is_valid = true;
      m_cached = r;
      m_cache_valid = true;
      RecordSuccess(r.score);
   }

public:
   //===================================================================
   // CONSTRUCTOR
   //===================================================================
   CLiquidityEngine() :
      m_pool_count(0),
      m_sweep_write_idx(0),
      m_sweep_count(0),
      m_last_processed_m15_bar(0),
      m_current_m15_bar_idx(0),
      m_last_asian_computed(0),
      m_asian_high(0.0),
      m_asian_low(0.0),
      m_asian_valid(false),
      m_structure_provided(false),
      m_volatility_provided(false),
      m_cache_valid(false),
      m_pools_added_total(0),
      m_pools_decayed_total(0),
      m_sweeps_confirmed_total(0),
      m_sweeps_broken_total(0)
   {
      ZeroMemory(m_pools);
      ZeroMemory(m_sweep_buffer);
      ZeroMemory(m_last_day_processed);
      ZeroMemory(m_last_structure);
      ZeroMemory(m_last_volatility);

      m_meta.id          = ENG_LIQUIDITY;
      m_meta.name        = "LIQUIDITY";
      m_meta.description = "Liquidity pool detection and sweep event tracking";
      m_meta.enabled     = true;
      m_meta.initialized = false;
      m_meta.available   = false;

      ZeroMemory(m_cached);
      m_cached.state    = LIQ_UNKNOWN;
      m_cached.is_valid = false;
   }

   //===================================================================
   // DEPENDENCY INJECTION
   //===================================================================
   void SetStructureResult(const StructureResult &sr)
   {
      m_last_structure     = sr;
      m_structure_provided = true;
   }
   void SetVolatilityResult(const VolatilityResult &vr)
   {
      m_last_volatility     = vr;
      m_volatility_provided = true;
   }

   //===================================================================
   // INIT
   //===================================================================
   virtual bool Init(string symbol, double pip_size) override
   {
      m_symbol   = symbol;
      m_pip_size = pip_size;
      if(pip_size <= 0)
      {
         Logger.Fatal("LIQUIDITY", "Init: pip_size <= 0");
         return false;
      }
      Logger.Info("LIQUIDITY",
         StringFormat("Initializing. symbol=%s pip=%.5f pool_max=%d",
                       symbol, pip_size, LIQ_ACTIVE_POOLS_MAX));

      // First-run cadence detection
      TimeToStruct(TimeCurrent(), m_last_day_processed);
      m_last_asian_computed = 0;   // Force initial Asian scan

      m_meta.initialized = true;
      m_initialized      = true;
      m_meta.available   = true;   // Empty but operational

      // First-tick detection (delayed to Evaluate — needs price context)

      Logger.Info("LIQUIDITY",
         StringFormat("Init complete. tiers: T1_window=%d T2_window=%d T3_window=%d",
                       LIQ_SWEEP_WINDOW_TIER1, LIQ_SWEEP_WINDOW_TIER2,
                       LIQ_SWEEP_WINDOW_TIER3));
      return true;
   }

   //===================================================================
   // EVALUATE — called by coordinator on M15 bar close
   //===================================================================
   virtual bool Evaluate(const IntelligenceContext &ctx) override
   {
      if(!m_initialized) return false;

      double current_price = ctx.mid_price;
      if(current_price <= 0) current_price = ctx.bid;
      if(current_price <= 0)
      {
         m_cached.invalid_reason = "no_price";
         RecordError("no_price");
         return false;
      }

      // Cadence: PDH/PDL daily
      if(IsNewCalendarDay(ctx.server_time) || m_current_m15_bar_idx == 0)
      {
         DetectPDH_PDL();
         TimeToStruct(ctx.server_time, m_last_day_processed);
      }

      // Cadence: Asian session (after 06:00, at most once per 12h)
      if(ShouldRecomputeAsian(ctx.server_time))
      {
         DetectAsianHighLow();
         m_last_asian_computed = ctx.server_time;
      }

      // If no new M15 bar and cache valid: return cached
      if(!ctx.new_m15_bar && m_cache_valid)
      {
         return m_cached.is_valid;
      }

      // M15 bar close processing
      m_current_m15_bar_idx++;

      // Fetch last two M15 closes + last M15 high/low
      double closes[], highs[], lows[];
      ArrayResize(closes, 3); ArrayResize(highs, 2); ArrayResize(lows, 2);
      ArraySetAsSeries(closes, true);
      ArraySetAsSeries(highs,  true);
      ArraySetAsSeries(lows,   true);

      int cc = CopyClose(m_symbol, PERIOD_M15, 1, 3, closes);
      int ch = CopyHigh(m_symbol,  PERIOD_M15, 1, 2, highs);
      int cl = CopyLow(m_symbol,   PERIOD_M15, 1, 2, lows);

      if(cc < 2 || ch < 1 || cl < 1)
      {
         Logger.Debug("LIQUIDITY",
            StringFormat("M15 data partial: closes=%d highs=%d lows=%d", cc, ch, cl));
         // Still build result with existing pools
         BuildResult(current_price);
         return m_cached.is_valid;
      }

      double last_close = closes[0];
      double prev_close = (cc >= 2) ? closes[1] : 0.0;
      double last_h = highs[0];
      double last_l = lows[0];

      // Layer 1: pool detection (per M15 close)
      DetectEqualHighsLows();      // From injected StructureResult
      UpdateRoundNumbers(current_price);
      UpdateTouchCounts(last_h, last_l);

      // Pool decay (Equal H/L only, per spec)
      if(prev_close > 0)
         DecayPools(last_close, prev_close);

      // Layer 2: sweep state machine
      AdvanceSweepStates(last_h, last_l, last_close, m_current_m15_bar_idx);

      // Build result
      BuildResult(current_price);

      m_last_processed_m15_bar = iTime(m_symbol, PERIOD_M15, 1);

      return m_cached.is_valid;
   }

   //===================================================================
   // GET CACHED (O(1) const-ref)
   //===================================================================
   LiquidityResult GetCached() const { return m_cached; }

   //===================================================================
   // RESET
   //===================================================================
   virtual void Reset() override
   {
      ZeroMemory(m_pools);
      ZeroMemory(m_sweep_buffer);
      m_pool_count               = 0;
      m_sweep_write_idx          = 0;
      m_sweep_count              = 0;
      m_last_processed_m15_bar   = 0;
      m_current_m15_bar_idx      = 0;
      m_last_asian_computed      = 0;
      m_asian_high               = 0.0;
      m_asian_low                = 0.0;
      m_asian_valid              = false;
      m_structure_provided       = false;
      m_volatility_provided      = false;
      m_cache_valid              = false;
      ZeroMemory(m_last_day_processed);
      ZeroMemory(m_last_structure);
      ZeroMemory(m_last_volatility);
      ZeroMemory(m_cached);
      m_cached.state    = LIQ_UNKNOWN;
      m_cached.is_valid = false;
      m_initialized     = false;
      m_meta.available  = false;
      Logger.Info("LIQUIDITY", "Engine reset");
   }

   //===================================================================
   // SHUTDOWN
   //===================================================================
   virtual void Shutdown() override
   {
      Logger.Info("LIQUIDITY",
         StringFormat("Shutdown. pools_added=%d decayed=%d sweeps_conf=%d broken=%d",
                       m_pools_added_total, m_pools_decayed_total,
                       m_sweeps_confirmed_total, m_sweeps_broken_total));
      IIntelligenceEngine::Shutdown();
   }

   //--- Convenience accessors
   int  GetPoolCount()          const { return m_pool_count; }
   bool HasFreshSweep()         const { return m_cached.sweep_detected; }
   double GetEnvironmentScore() const { return m_cached.score; }
};

//--- Global singleton
CLiquidityEngine LiquidityEngine;

#endif // CLIQUIDITYENGINE_MQH

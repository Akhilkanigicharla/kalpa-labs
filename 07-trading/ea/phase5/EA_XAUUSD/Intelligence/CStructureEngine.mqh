
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Structure Engine                        |
//| File: Intelligence/CStructureEngine.mqh                           |
//| Purpose: Identify and track confirmed swing highs/lows across     |
//|           H4, H1, and M15 timeframes. Detect HH/HL, LH/LL        |
//|           patterns. Produce structural clarity and confidence.    |
//| Phase: 3 — Step 2                                                 |
//|                                                                    |
//| GUARD SLOT: N/A (Intelligence Layer — no guard authority)         |
//| ENGINE ID:  ENG_STRUCTURE                                         |
//|                                                                    |
//| DEPENDENCY:                                                        |
//|   Reads:  Raw OHLC via MT5 CopyHigh/CopyLow                      |
//|   Reads:  Defines.mqh constants (SWING_MIN_PIPS_*, etc.)          |
//|   Reads:  IntelligenceTypes.mqh (StructureResult, StructureSnapshot)|
//|   Reads:  IIntelligenceEngine.mqh (base class)                    |
//|   NO other intelligence engines — StructureEngine is independent. |
//|                                                                    |
//| OUTPUT:    StructureResult (cached, returned every tick)          |
//|                                                                    |
//| CRITICAL DESIGN RULES:                                            |
//|   1. Swings confirmed by 2-bar right-side rule ONLY               |
//|   2. Minimum swing size filter per timeframe (prevents noise)     |
//|   3. Circular buffer pattern — no runtime ArrayResize             |
//|   4. NO indicator handles — reads raw OHLC directly               |
//|   5. Separate per-timeframe state — independent failure modes     |
//|   6. Unavailability reduces confidence, NEVER hard-invalidates    |
//|      downstream engines (per architecture revision)               |
//+------------------------------------------------------------------+
#ifndef CSTRUCTUREENGINE_MQH
#define CSTRUCTUREENGINE_MQH

#include "IIntelligenceEngine.mqh"

//===================================================================
// CONSTANTS — StructureEngine specific
//===================================================================
#define STRUCT_PENDING_MAX      5    // Max pending (unconfirmed) swings tracked
#define STRUCT_CLARITY_WINDOW   3    // Swing pairs checked for clarity score
#define STRUCT_MIN_LOOKBACK_H4  10   // Min H4 bars before any output
#define STRUCT_MIN_LOOKBACK_H1  20   // Min H1 bars before any output
#define STRUCT_MIN_LOOKBACK_M15 20   // Min M15 bars before any output
#define STRUCT_STALE_H4_SEC     18000  // > 5 H4 bars without update = stale
#define STRUCT_STALE_H1_SEC      7200  // > 2 H1 bars
#define STRUCT_STALE_M15_SEC     2700  // > 3 M15 bars

//===================================================================
// INTERNAL: Per-Timeframe Engine State
//
// PSEUDO-CODE:
//   Each timeframe is processed independently by a TimeframeState.
//   This means H1 processing can fail (e.g. bad data) without
//   affecting H4 or M15 processing.
//
//   Circular buffer for confirmed swings:
//     Array of fixed size SWING_ARRAY_MAX (50).
//     write_high_idx / write_low_idx track the NEXT write position.
//     Read the most recent confirmed swing: array[(write_idx - 1 + MAX) % MAX]
//     The "count" tracks how many valid entries exist (capped at MAX).
//
//   Pending swing mechanism:
//     A "pending swing" is a local high/low that has 1-bar right-side
//     confirmation but has NOT yet satisfied the 2-bar requirement.
//     Pending swings are promoted to confirmed after the 2nd right-side bar.
//     Pending swings are invalidated if a higher high / lower low occurs
//     on the right side before confirmation completes.
//
//   Price buffer:
//     Last SWING_LOOKBACK bars of High/Low prices stored locally.
//     Refreshed on each bar close of this timeframe.
//     CopyHigh / CopyLow called once per bar close.
//     NOT called per tick (would be expensive).
//===================================================================
struct TimeframeState
{
   ENUM_TIMEFRAMES   tf;
   double            min_swing_pips;     // Minimum valid swing size

   // Price buffer (filled via CopyHigh/CopyLow on bar close)
   // PRICE_BUFFER_MAX = 100 — covers H1 and M15 lookbacks (both 100 bars)
   double            highs[PRICE_BUFFER_MAX];
   double            lows[PRICE_BUFFER_MAX];
   int               bar_count;           // Valid bars in buffer

   // Confirmed swing circular buffers
   SwingPoint        conf_highs[SWING_ARRAY_MAX];
   SwingPoint        conf_lows[SWING_ARRAY_MAX];
   int               write_high_idx;     // Next write position (circular)
   int               write_low_idx;
   int               high_count;         // Valid confirmed highs (max SWING_ARRAY_MAX)
   int               low_count;

   // Pending swings awaiting 2nd right-side bar
   SwingPoint        pend_highs[STRUCT_PENDING_MAX];
   SwingPoint        pend_lows[STRUCT_PENDING_MAX];
   int               pend_high_count;
   int               pend_low_count;

   // Bar boundary tracking
   datetime          last_bar_time;      // Time of last processed bar
   int               bars_processed;     // Total bars processed since init

   // Derived state (computed after swing update)
   STRUCTURE_STATE   state;
   bool              hh_hl;
   bool              lh_ll;
   double            clarity;

   // Availability
   bool              initialized;
   bool              has_min_history;    // Enough bars for meaningful output
   string            last_error;
};

//===================================================================
// MAIN CLASS: CStructureEngine
//===================================================================
class CStructureEngine : public IIntelligenceEngine
{
private:
   //--- Per-timeframe state (H4, H1, M15)
   TimeframeState    m_h4;
   TimeframeState    m_h1;
   TimeframeState    m_m15;

   //--- Last computed result (returned every tick via GetCached())
   StructureResult   m_cached;
   bool              m_cache_valid;

   //===================================================================
   // UTILITY: Get most recently written confirmed swing (index relative)
   //   offset=0 → most recent, offset=1 → second most recent, etc.
   //   Returns false if fewer than (offset+1) confirmed swings exist.
   //===================================================================
   bool GetConfirmedHigh(const TimeframeState &tfs,
                          int offset, SwingPoint &out) const
   {
      if(tfs.high_count <= offset) return false;
      int idx = (tfs.write_high_idx - 1 - offset + SWING_ARRAY_MAX) % SWING_ARRAY_MAX;
      out = tfs.conf_highs[idx];
      return (out.price > 0 && out.confirmed);
   }

   bool GetConfirmedLow(const TimeframeState &tfs,
                         int offset, SwingPoint &out) const
   {
      if(tfs.low_count <= offset) return false;
      int idx = (tfs.write_low_idx - 1 - offset + SWING_ARRAY_MAX) % SWING_ARRAY_MAX;
      out = tfs.conf_lows[idx];
      return (out.price > 0 && out.confirmed);
   }

   //===================================================================
   // UTILITY: Write a new confirmed swing into circular buffer
   //===================================================================
   void WriteConfirmedHigh(TimeframeState &tfs, const SwingPoint &sp)
   {
      tfs.conf_highs[tfs.write_high_idx] = sp;
      tfs.write_high_idx = (tfs.write_high_idx + 1) % SWING_ARRAY_MAX;
      tfs.high_count     = MathMin(tfs.high_count + 1, SWING_ARRAY_MAX);
   }

   void WriteConfirmedLow(TimeframeState &tfs, const SwingPoint &sp)
   {
      tfs.conf_lows[tfs.write_low_idx] = sp;
      tfs.write_low_idx = (tfs.write_low_idx + 1) % SWING_ARRAY_MAX;
      tfs.low_count     = MathMin(tfs.low_count + 1, SWING_ARRAY_MAX);
   }

   //===================================================================
   // UTILITY: Convert price history into price buffer for a timeframe
   //
   // PSEUDO-CODE:
   //   CopyHigh(symbol, tf, 0, lookback, highs_array)
   //   Returns number of bars copied. Index 0 = most recent closed bar.
   //   Note: bar 0 in MT5 CopyHigh is the CURRENT (incomplete) bar.
   //   We start analysis from bar 1 (most recent CLOSED bar).
   //
   //   The buffer is stored in tfs.highs[]/tfs.lows[] with:
   //   tfs.highs[0] = most recent closed bar's high (= MT5 bar index 1)
   //   tfs.highs[1] = second most recent closed bar (= MT5 bar index 2)
   //   ...
   //   This "flip" vs MT5 indexing is handled once here.
   //   All downstream swing detection uses our 0=most-recent convention.
   //===================================================================
   bool RefreshPriceBuffer(TimeframeState &tfs, int lookback)
   {
      // PSEUDO-CODE:
      //   CopyHigh returns bars in MT5 order (0=current incomplete).
      //   We want bars 1..lookback (all completed bars).
      //   Shift = 1 skips the current incomplete bar.

      double temp_highs[];
      double temp_lows[];
      ArraySetAsSeries(temp_highs, true);
      ArraySetAsSeries(temp_lows,  true);

      int copied = CopyHigh(m_symbol, tfs.tf, 1, lookback, temp_highs);
      if(copied <= 0)
      {
         tfs.last_error = StringFormat("CopyHigh failed: tf=%s copied=%d",
                                        EnumToString(tfs.tf), copied);
         return false;
      }

      int copied_l = CopyLow(m_symbol, tfs.tf, 1, lookback, temp_lows);
      if(copied_l <= 0)
      {
         tfs.last_error = StringFormat("CopyLow failed: tf=%s copied=%d",
                                        EnumToString(tfs.tf), copied_l);
         return false;
      }

      int n = MathMin(copied, copied_l);
      n = MathMin(n, PRICE_BUFFER_MAX);  // Safety cap at array size

      for(int i = 0; i < n; i++)
      {
         tfs.highs[i] = temp_highs[i];
         tfs.lows[i]  = temp_lows[i];
      }
      tfs.bar_count = n;
      return true;
   }

   //===================================================================
   // CORE: Swing Detection Algorithm
   //
   // PSEUDO-CODE — Full algorithm for swing HIGH detection:
   //
   //   For bar index i (0 = most recent closed bar):
   //     A swing HIGH at bar[i] requires:
   //       LEFT SIDE:  highs[i] > highs[i+1]  (higher than previous bar)
   //                   highs[i] > highs[i+2]  (higher than 2 bars before)
   //                   This establishes the candidate.
   //       RIGHT SIDE: highs[i-1] < highs[i]  (bar AFTER has lower high)
   //                   highs[i-2] < highs[i]  (2 bars after also lower)
   //                   This is the 2-bar CONFIRMATION rule.
   //
   //   In our 0=most-recent buffer:
   //     bar[i] is at index i
   //     "bar before" (older) is at index i+1
   //     "bar after"  (newer) is at index i-1
   //
   //   So for bar at index [i]:
   //     Left side (already happened):  highs[i] > highs[i+1] && highs[i] > highs[i+2]
   //     Right side (recent bars):      highs[i-1] < highs[i] && highs[i-2] < highs[i]
   //                                    BUT: i-1 and i-2 must be >= 0
   //
   //   MINIMUM SIZE FILTER:
   //     The swing must be at least min_swing_pips from the last confirmed low.
   //     If no confirmed lows exist: size filter uses distance to nearest low
   //     in the price buffer within 10 bars.
   //
   //   PENDING SWING LOGIC (incremental — avoids re-scanning from scratch):
   //     On each new bar close, only bar[2] can newly become confirmed:
   //       - Bars 0 and 1 cannot yet be confirmed (need 2 right-side bars).
   //       - Bar[2] has bars[0] and [1] as its right-side.
   //       - If bar[2] was already a LEFT-SIDE candidate (pending),
   //         check if bars[1] and [0] confirm it.
   //
   //   INCREMENTAL VS FULL SCAN:
   //     Full scan: iterate ALL bars in buffer (called at Init/Reset).
   //     Incremental: only check bar[2] on each new bar (called per bar close).
   //     Incremental is O(1). Full scan is O(n).
   //     We use incremental in normal operation. Full scan only at startup.
   //===================================================================

   //--- Full scan: detect ALL swings in the current price buffer
   //    Called ONCE at init and after Reset().
   void FullScanSwings(TimeframeState &tfs)
   {
      // PSEUDO-CODE:
      //   Scan from oldest to newest (i = bar_count-3 down to i=2)
      //   For each bar: check left + right side conditions.
      //   Must check size against nearest opposite swing.
      //   Promote qualifying swings to confirmed array in chronological order.
      //   This means iterating from HIGH index (oldest) to LOW (newest).
      //
      //   We iterate in reverse order (oldest first) so that confirmed swings
      //   are written to the circular buffer chronologically.

      int n = tfs.bar_count;
      if(n < (SWING_CONFIRM_BARS * 2 + 1)) return;

      // We need i-2 and i+2 to exist: valid range is [2, n-3]
      // In our 0=newest buffer: index 2 = third most recent bar
      //   Its right-side bars are index 1 and 0 (newer).
      //   Its left-side bars are index 3 and 4 (older).
      //   So for index i, right side = i-1, i-2 and left side = i+1, i+2.
      //   Valid range: i >= 2 (right side exists) AND i <= n-3 (left side exists).

      // Process from oldest to newest so circular buffer fills chronologically
      for(int i = n - 3; i >= 2; i--)
      {
         double h = tfs.highs[i];
         double l = tfs.lows[i];

         // --- Swing HIGH candidate ---
         // Left side: bar[i] is highest of [i-2..i+2] (2 bars each side)
         bool left_high  = (h > tfs.highs[i+1] && h > tfs.highs[i+2]);
         bool right_high = (h > tfs.highs[i-1] && h > tfs.highs[i-2]);

         if(left_high && right_high)
         {
            // Size filter: distance from nearest prior confirmed low
            double size_pips = GetSwingSize(tfs, i, true);
            if(size_pips >= tfs.min_swing_pips)
            {
               SwingPoint sp;
               sp.price     = h;
               sp.time      = GetBarTime(tfs.tf, i);
               sp.is_high   = true;
               sp.confirmed = true;
               sp.timeframe = tfs.tf;
               // Avoid duplicating a swing already in buffer
               if(!IsDuplicateHigh(tfs, sp.price, sp.time))
                  WriteConfirmedHigh(tfs, sp);
            }
         }

         // --- Swing LOW candidate ---
         bool left_low  = (l < tfs.lows[i+1] && l < tfs.lows[i+2]);
         bool right_low = (l < tfs.lows[i-1] && l < tfs.lows[i-2]);

         if(left_low && right_low)
         {
            double size_pips = GetSwingSize(tfs, i, false);
            if(size_pips >= tfs.min_swing_pips)
            {
               SwingPoint sp;
               sp.price     = l;
               sp.time      = GetBarTime(tfs.tf, i);
               sp.is_high   = false;
               sp.confirmed = true;
               sp.timeframe = tfs.tf;
               if(!IsDuplicateLow(tfs, sp.price, sp.time))
                  WriteConfirmedLow(tfs, sp);
            }
         }
      }
   }

   //--- Incremental scan: only check if bar[2] is now confirmable
   //    Called on each new bar close (O(1) amortized).
   void IncrementalScanSwings(TimeframeState &tfs)
   {
      // PSEUDO-CODE:
      //   After a new bar close, the price buffer has been refreshed.
      //   Bar at index 2 now has:
      //     Right-side bars: index 1 (1 bar after) and index 0 (2 bars after).
      //     Left-side bars:  index 3 and index 4 (already existed).
      //   This is the ONLY bar that has just become confirmable.
      //   Check it and promote to confirmed if qualifies.

      if(tfs.bar_count < 5) return; // Need at least 5 bars

      int i = 2;
      double h = tfs.highs[i];
      double l = tfs.lows[i];

      // --- Check swing HIGH at bar[2] ---
      bool left_high  = (h > tfs.highs[i+1] && h > tfs.highs[i+2]);
      bool right_high = (h > tfs.highs[i-1] && h > tfs.highs[i-2]);

      if(left_high && right_high)
      {
         double size_pips = GetSwingSize(tfs, i, true);
         if(size_pips >= tfs.min_swing_pips)
         {
            SwingPoint sp;
            sp.price     = h;
            sp.time      = GetBarTime(tfs.tf, i);
            sp.is_high   = true;
            sp.confirmed = true;
            sp.timeframe = tfs.tf;
            if(!IsDuplicateHigh(tfs, sp.price, sp.time))
            {
               WriteConfirmedHigh(tfs, sp);
               Logger.Debug("STRUCTURE",
                  StringFormat("New swing HIGH confirmed: tf=%s price=%.5f pips=%.1f",
                               EnumToString(tfs.tf), sp.price, size_pips));
            }
         }
      }

      // --- Check swing LOW at bar[2] ---
      bool left_low  = (l < tfs.lows[i+1] && l < tfs.lows[i+2]);
      bool right_low = (l < tfs.lows[i-1] && l < tfs.lows[i-2]);

      if(left_low && right_low)
      {
         double size_pips = GetSwingSize(tfs, i, false);
         if(size_pips >= tfs.min_swing_pips)
         {
            SwingPoint sp;
            sp.price     = l;
            sp.time      = GetBarTime(tfs.tf, i);
            sp.is_high   = false;
            sp.confirmed = true;
            sp.timeframe = tfs.tf;
            if(!IsDuplicateLow(tfs, sp.price, sp.time))
            {
               WriteConfirmedLow(tfs, sp);
               Logger.Debug("STRUCTURE",
                  StringFormat("New swing LOW confirmed: tf=%s price=%.5f pips=%.1f",
                               EnumToString(tfs.tf), sp.price, size_pips));
            }
         }
      }
   }

   //===================================================================
   // UTILITY: Swing size calculation
   //
   // PSEUDO-CODE:
   //   For a swing HIGH at bar index i:
   //     Size = distance from high[i] to nearest confirmed LOW before it.
   //     "Before" = confirmed low with time PRIOR to bar[i]'s time.
   //     If no confirmed low exists: use lowest low in the 10 bars around it.
   //
   //   For a swing LOW at bar index i:
   //     Size = distance from low[i] to nearest confirmed HIGH before it.
   //===================================================================
   double GetSwingSize(const TimeframeState &tfs, int bar_idx, bool is_high) const
   {
      if(bar_idx < 0 || bar_idx >= tfs.bar_count) return 0.0;

      double bar_price = is_high ? tfs.highs[bar_idx] : tfs.lows[bar_idx];
      double opposite  = 0.0;

      if(is_high)
      {
         // Look for nearest confirmed low prior to this bar
         SwingPoint sp;
         for(int k = 0; k < tfs.low_count && k < 5; k++)
         {
            if(GetConfirmedLow(tfs, k, sp) && sp.price > 0)
            {
               opposite = sp.price;
               break;
            }
         }
         // Fallback: lowest low in ±10 bars
         if(opposite <= 0)
         {
            opposite = tfs.lows[bar_idx];
            int scan_end = MathMin(bar_idx + 10, tfs.bar_count - 1);
            for(int k = bar_idx - 2; k <= scan_end; k++)
               if(k >= 0 && tfs.lows[k] < opposite)
                  opposite = tfs.lows[k];
         }
         return PriceToPips(bar_price - opposite);
      }
      else
      {
         SwingPoint sp;
         for(int k = 0; k < tfs.high_count && k < 5; k++)
         {
            if(GetConfirmedHigh(tfs, k, sp) && sp.price > 0)
            {
               opposite = sp.price;
               break;
            }
         }
         if(opposite <= 0)
         {
            opposite = tfs.highs[bar_idx];
            int scan_end = MathMin(bar_idx + 10, tfs.bar_count - 1);
            for(int k = bar_idx - 2; k <= scan_end; k++)
               if(k >= 0 && tfs.highs[k] > opposite)
                  opposite = tfs.highs[k];
         }
         return PriceToPips(opposite - bar_price);
      }
   }

   //===================================================================
   // UTILITY: Bar time lookup
   // Gets the server timestamp of bar at index i on a timeframe.
   // index 0 = most recent CLOSED bar (we store as our index 0).
   // MT5 iTime(sym, tf, 1) = most recent closed bar.
   // So our buffer[i] = MT5 bar index (i+1).
   //===================================================================
   datetime GetBarTime(ENUM_TIMEFRAMES tf, int our_idx) const
   {
      return iTime(m_symbol, tf, our_idx + 1);
   }

   //===================================================================
   // UTILITY: Duplicate detection
   // Prevents the same swing being confirmed twice (e.g. during full scan
   // followed by incremental, or if CopyHigh returns overlapping data).
   // A swing is a duplicate if price AND time match an existing entry.
   //===================================================================
   bool IsDuplicateHigh(const TimeframeState &tfs,
                         double price, datetime t) const
   {
      for(int i = 0; i < tfs.high_count && i < 10; i++)
      {
         SwingPoint sp;
         if(!GetConfirmedHigh(tfs, i, sp)) continue;
         // Same bar time = definitely same swing
         if(sp.time == t) return true;
         // Very close price + close time = likely same swing
         if(MathAbs(sp.price - price) < PipsToPrice(2.0) &&
            MathAbs((double)(sp.time - t)) < 3600)
            return true;
      }
      return false;
   }

   bool IsDuplicateLow(const TimeframeState &tfs,
                        double price, datetime t) const
   {
      for(int i = 0; i < tfs.low_count && i < 10; i++)
      {
         SwingPoint sp;
         if(!GetConfirmedLow(tfs, i, sp)) continue;
         if(sp.time == t) return true;
         if(MathAbs(sp.price - price) < PipsToPrice(2.0) &&
            MathAbs((double)(sp.time - t)) < 3600)
            return true;
      }
      return false;
   }

   //===================================================================
   // PATTERN RECOGNITION: HH/HL and LH/LL
   //
   // PSEUDO-CODE:
   //   HH+HL (higher highs AND higher lows) = bullish structure:
   //     most_recent_high > second_most_recent_high   (HH)
   //     most_recent_low  > second_most_recent_low    (HL)
   //     Both must be true. One alone is insufficient.
   //
   //   LH+LL (lower highs AND lower lows) = bearish structure:
   //     most_recent_high < second_most_recent_high   (LH)
   //     most_recent_low  < second_most_recent_low    (LL)
   //
   //   MIXED: one up, one down = no directional conviction.
   //
   //   EDGE CASE — interleaved timing:
   //     We look at the most recent confirmed HIGH and LOW independently.
   //     Their timestamps may not be perfectly alternating.
   //     We only use the price comparison — not timing order.
   //     Timing-based alternation would be too strict for Gold's
   //     complex candle-by-candle structure.
   //===================================================================
   void DetectPatterns(TimeframeState &tfs)
   {
      tfs.hh_hl = false;
      tfs.lh_ll = false;

      SwingPoint h0, h1, l0, l1;
      bool has_h0 = GetConfirmedHigh(tfs, 0, h0);
      bool has_h1 = GetConfirmedHigh(tfs, 1, h1);
      bool has_l0 = GetConfirmedLow(tfs,  0, l0);
      bool has_l1 = GetConfirmedLow(tfs,  1, l1);

      if(!has_h0 || !has_h1 || !has_l0 || !has_l1) return;

      bool hh = (h0.price > h1.price);   // Higher high
      bool hl = (l0.price > l1.price);   // Higher low
      bool lh = (h0.price < h1.price);   // Lower high
      bool ll = (l0.price < l1.price);   // Lower low

      tfs.hh_hl = (hh && hl);
      tfs.lh_ll = (lh && ll);
   }

   //===================================================================
   // CLARITY SCORING: How clean is the structure?
   //
   // PSEUDO-CODE:
   //   Examine last STRUCT_CLARITY_WINDOW (3) swing pairs.
   //   For each pair (consecutive highs and lows):
   //     Bullish context: +1 if HH and HL, 0 otherwise
   //     Bearish context: +1 if LH and LL, 0 otherwise
   //     Mixed: 0 for all
   //   clarity = conforming_pairs / STRUCT_CLARITY_WINDOW
   //
   //   Special case: only 1 pair available → clarity = 0.5 (partial)
   //   No pairs available → clarity = 0.0
   //===================================================================
   double ComputeClarity(const TimeframeState &tfs) const
   {
      int pairs_available  = MathMin(tfs.high_count, tfs.low_count) - 1;
      if(pairs_available <= 0) return 0.0;
      if(pairs_available == 1) return 0.5;

      int window    = MathMin(STRUCT_CLARITY_WINDOW, pairs_available);
      int conforming = 0;

      // First determine expected direction from most recent pattern
      bool expecting_bull = tfs.hh_hl;
      bool expecting_bear = tfs.lh_ll;
      if(!expecting_bull && !expecting_bear) return 0.0; // Mixed — no clarity

      for(int w = 0; w < window; w++)
      {
         SwingPoint h_new, h_old, l_new, l_old;
         if(!GetConfirmedHigh(tfs, w,   h_new)) break;
         if(!GetConfirmedHigh(tfs, w+1, h_old)) break;
         if(!GetConfirmedLow(tfs,  w,   l_new)) break;
         if(!GetConfirmedLow(tfs,  w+1, l_old)) break;

         bool pair_bull = (h_new.price > h_old.price && l_new.price > l_old.price);
         bool pair_bear = (h_new.price < h_old.price && l_new.price < l_old.price);

         if(expecting_bull && pair_bull) conforming++;
         if(expecting_bear && pair_bear) conforming++;
      }

      return (double)conforming / (double)window;
   }

   //===================================================================
   // CLASSIFY: Convert internal state to STRUCTURE_STATE enum
   //===================================================================
   STRUCTURE_STATE ClassifyState(const TimeframeState &tfs) const
   {
      if(!tfs.has_min_history || tfs.high_count < 1 || tfs.low_count < 1)
         return STRUCT_UNKNOWN;

      // Need at least 2 confirmed swings of each type for pattern
      if(tfs.high_count < SWING_MIN_CONFIRMED || tfs.low_count < SWING_MIN_CONFIRMED)
      {
         // REVISION: single confirmed swing is insufficient to determine direction.
         // A HH requires TWO confirmed highs (current > previous).
         // A HL requires TWO confirmed lows.
         // With only one swing of either type, no pattern can be established.
         // Return STRUCT_UNKNOWN — caller uses low confidence (0.0 from ComputeClarity).
         return STRUCT_UNKNOWN;
      }

      if(tfs.hh_hl && !tfs.lh_ll)
      {
         return (tfs.clarity >= 0.67) ? STRUCT_CLEAR_BULL : STRUCT_WEAK_BULL;
      }
      if(tfs.lh_ll && !tfs.hh_hl)
      {
         return (tfs.clarity >= 0.67) ? STRUCT_CLEAR_BEAR : STRUCT_WEAK_BEAR;
      }

      return STRUCT_MIXED; // Both patterns present = conflicted
   }

   //===================================================================
   // BUILD: Populate StructureSnapshot from TimeframeState
   //===================================================================
   void BuildSnapshot(const TimeframeState &tfs, StructureSnapshot &snap) const
   {
      snap.timeframe       = tfs.tf;
      snap.high_count      = tfs.high_count;
      snap.low_count       = tfs.low_count;
      snap.state           = ClassifyState(tfs);
      snap.hh_hl           = tfs.hh_hl;
      snap.lh_ll           = tfs.lh_ll;
      snap.structure_clarity = tfs.clarity;
      snap.last_updated    = tfs.last_bar_time;

      // Copy confirmed swing arrays (full copy — fixed size, fast)
      for(int i = 0; i < SWING_ARRAY_MAX; i++)
      {
         snap.confirmed_highs[i] = tfs.conf_highs[i];
         snap.confirmed_lows[i]  = tfs.conf_lows[i];
      }

      // Populate convenience last/prev fields
      SwingPoint h0, h1, l0, l1;
      snap.last_high  = GetConfirmedHigh(tfs, 0, h0) ? h0.price : 0.0;
      snap.prev_high  = GetConfirmedHigh(tfs, 1, h1) ? h1.price : 0.0;
      snap.last_low   = GetConfirmedLow(tfs,  0, l0) ? l0.price : 0.0;
      snap.prev_low   = GetConfirmedLow(tfs,  1, l1) ? l1.price : 0.0;

      // Pending swing status
      snap.has_pending_high = false;
      snap.has_pending_low  = false;
   }

   //===================================================================
   // BUILD: Populate StructureResult from all three snapshots
   //===================================================================
   void BuildResult()
   {
      m_cached.evaluated_at = TimeCurrent();

      // Build each timeframe snapshot
      BuildSnapshot(m_h4,  m_cached.h4);
      BuildSnapshot(m_h1,  m_cached.h1);
      BuildSnapshot(m_m15, m_cached.m15);

      // Availability
      m_cached.h4_available  = m_h4.initialized  && m_h4.has_min_history;
      m_cached.h1_available  = m_h1.initialized  && m_h1.has_min_history;
      m_cached.m15_available = m_m15.initialized && m_m15.has_min_history;
      m_cached.any_available = (m_cached.h4_available ||
                                 m_cached.h1_available ||
                                 m_cached.m15_available);

      // Cross-timeframe agreement
      TRADE_DIR d_h4  = SnapDirection(m_cached.h4);
      TRADE_DIR d_h1  = SnapDirection(m_cached.h1);
      TRADE_DIR d_m15 = SnapDirection(m_cached.m15);

      m_cached.h4_h1_agree  = (m_cached.h4_available && m_cached.h1_available &&
                                d_h4 != DIR_NONE && d_h4 == d_h1);
      m_cached.h1_m15_agree = (m_cached.h1_available && m_cached.m15_available &&
                                d_h1 != DIR_NONE && d_h1 == d_m15);
      m_cached.all_agree    = (m_cached.h4_h1_agree && m_cached.h1_m15_agree &&
                                d_h4 != DIR_NONE);

      // Consensus direction: use H1 as arbiter when H4 and H1 agree
      // (M15 disagreement reduces confidence but doesn't override H4/H1)
      if(m_cached.all_agree)
         m_cached.consensus_direction = d_h4;
      else if(m_cached.h4_h1_agree)
         m_cached.consensus_direction = d_h4;  // H4+H1 agree = use their direction
      else
         m_cached.consensus_direction = DIR_NONE;

      // Validity and confidence
      m_cached.is_valid = m_cached.any_available;
      if(!m_cached.is_valid)
         m_cached.invalid_reason = "no_timeframe_available";

      // Overall confidence
      double conf = ComputeOverallConfidence();
      RecordSuccess(conf);

      m_cache_valid = true;
   }

   //--- Get directional implication of a snapshot
   TRADE_DIR SnapDirection(const StructureSnapshot &snap) const
   {
      if(snap.hh_hl && !snap.lh_ll) return DIR_LONG;
      if(snap.lh_ll && !snap.hh_hl) return DIR_SHORT;
      return DIR_NONE;
   }

   //===================================================================
   // CONFIDENCE SCORING
   //
   // PSEUDO-CODE:
   //   Weighted average of available timeframe clarity scores.
   //   H4 carries most weight (macro structure = most reliable).
   //   H1 is the primary direction filter.
   //   M15 is entry-level (least reliable for overall confidence).
   //
   //   If a timeframe is unavailable: skip it (not penalized by zero).
   //   Rationale from architecture revision: unavailable = reduced
   //   confidence, not hard invalidation.
   //
   //   Weights when all three available: H4=0.40, H1=0.40, M15=0.20
   //   When H4 unavailable: H1=0.60, M15=0.40
   //   When H1 unavailable: H4=0.60, M15=0.40
   //   When M15 unavailable: H4=0.50, H1=0.50
   //===================================================================
   double ComputeOverallConfidence() const
   {
      bool h4_ok  = m_cached.h4_available;
      bool h1_ok  = m_cached.h1_available;
      bool m15_ok = m_cached.m15_available;

      if(!h4_ok && !h1_ok && !m15_ok) return 0.0;

      double h4_clarity  = h4_ok  ? m_h4.clarity  : 0.0;
      double h1_clarity  = h1_ok  ? m_h1.clarity  : 0.0;
      double m15_clarity = m15_ok ? m_m15.clarity : 0.0;

      double w_h4 = 0.0, w_h1 = 0.0, w_m15 = 0.0;

      if(h4_ok && h1_ok && m15_ok) { w_h4=0.40; w_h1=0.40; w_m15=0.20; }
      else if(h4_ok && h1_ok)      { w_h4=0.50; w_h1=0.50; }
      else if(h4_ok && m15_ok)     { w_h4=0.60; w_m15=0.40; }
      else if(h1_ok && m15_ok)     { w_h1=0.60; w_m15=0.40; }
      else if(h4_ok)               { w_h4=1.00; }
      else if(h1_ok)               { w_h1=1.00; }
      else                          { w_m15=1.00; }

      double base_conf = (h4_clarity * w_h4) + (h1_clarity * w_h1) + (m15_clarity * w_m15);

      // Agreement bonus: all three agree = +0.10 to confidence
      // H4+H1 agree only = +0.05
      double agreement_bonus = 0.0;
      if(m_cached.all_agree)   agreement_bonus = 0.10;
      else if(m_cached.h4_h1_agree) agreement_bonus = 0.05;

      return MathMin(1.0, base_conf + agreement_bonus);
   }

   //===================================================================
   // INITIALIZE a single TimeframeState
   //===================================================================
   bool InitTimeframe(TimeframeState &tfs, ENUM_TIMEFRAMES tf,
                       double min_swing_pips, int lookback)
   {
      ZeroMemory(tfs);
      tfs.tf             = tf;
      tfs.min_swing_pips = min_swing_pips;
      tfs.write_high_idx = 0;
      tfs.write_low_idx  = 0;
      tfs.high_count     = 0;
      tfs.low_count      = 0;
      tfs.pend_high_count = 0;
      tfs.pend_low_count  = 0;
      tfs.bars_processed  = 0;
      tfs.state           = STRUCT_UNKNOWN;
      tfs.hh_hl           = false;
      tfs.lh_ll           = false;
      tfs.clarity         = 0.0;
      tfs.initialized     = false;
      tfs.has_min_history = false;

      // Load initial price buffer
      if(!RefreshPriceBuffer(tfs, lookback))
      {
         Logger.Warn("STRUCTURE",
            StringFormat("Init: RefreshPriceBuffer failed for tf=%s",
                          EnumToString(tf)));
         return false;
      }

      // Min history check
      int min_bars = (tf == PERIOD_H4) ? STRUCT_MIN_LOOKBACK_H4 :
                     (tf == PERIOD_H1) ? STRUCT_MIN_LOOKBACK_H1 :
                                          STRUCT_MIN_LOOKBACK_M15;
      tfs.has_min_history = (tfs.bar_count >= min_bars);

      if(tfs.has_min_history)
      {
         // Full scan to populate swing arrays from history
         FullScanSwings(tfs);
         DetectPatterns(tfs);
         tfs.clarity = ComputeClarity(tfs);
         tfs.state   = ClassifyState(tfs);
      }

      // Record most recent bar time
      tfs.last_bar_time = GetBarTime(tf, 0);
      tfs.initialized   = true;

      Logger.Info("STRUCTURE",
         StringFormat("tf=%s bars=%d highs=%d lows=%d state=%s clarity=%.2f",
                       EnumToString(tf), tfs.bar_count,
                       tfs.high_count, tfs.low_count,
                       EnumToString(tfs.state), tfs.clarity));
      return true;
   }

   //===================================================================
   // UPDATE a single timeframe on bar close
   //===================================================================
   void UpdateTimeframe(TimeframeState &tfs, int lookback)
   {
      // PSEUDO-CODE:
      //   1. Refresh price buffer (CopyHigh/CopyLow — one call pair).
      //   2. Run incremental swing detection (check bar[2] only).
      //   3. Recompute patterns and clarity.
      //   4. Update last_bar_time.

      if(!tfs.initialized) return;

      if(!RefreshPriceBuffer(tfs, lookback))
      {
         Logger.Error("STRUCTURE",
            StringFormat("UpdateTimeframe: buffer refresh failed tf=%s",
                          EnumToString(tfs.tf)));
         tfs.last_error = "price_buffer_refresh_failed";
         return;
      }

      tfs.has_min_history = (tfs.bar_count >= STRUCT_MIN_LOOKBACK_M15);

      IncrementalScanSwings(tfs);
      DetectPatterns(tfs);
      tfs.clarity         = ComputeClarity(tfs);
      tfs.state           = ClassifyState(tfs);
      tfs.last_bar_time   = GetBarTime(tfs.tf, 0);
      tfs.bars_processed++;
   }

public:
   //===================================================================
   // CONSTRUCTOR
   //===================================================================
   CStructureEngine() : m_cache_valid(false)
   {
      m_meta.id          = ENG_STRUCTURE;
      m_meta.name        = "STRUCTURE";
      m_meta.description = "Swing structure detection H4/H1/M15";
      m_meta.enabled     = true;
      m_meta.initialized = false;
      m_meta.available   = false;

      ZeroMemory(m_cached);
      m_cached.is_valid = false;
      m_cached.consensus_direction = DIR_NONE;
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
         Logger.Fatal("STRUCTURE", "Init: pip_size <= 0 — cannot calculate swing sizes");
         return false;
      }

      Logger.Info("STRUCTURE",
         StringFormat("Initializing. symbol=%s pip_size=%.5f", symbol, pip_size));

      // Initialize each timeframe independently
      // Failure of one timeframe is non-fatal — engine degrades gracefully
      bool h4_ok  = InitTimeframe(m_h4,  PERIOD_H4,
                                   SWING_MIN_PIPS_H4,  SWING_LOOKBACK_H4);
      bool h1_ok  = InitTimeframe(m_h1,  PERIOD_H1,
                                   SWING_MIN_PIPS_H1,  SWING_LOOKBACK_H1);
      bool m15_ok = InitTimeframe(m_m15, PERIOD_M15,
                                   SWING_MIN_PIPS_M15, SWING_LOOKBACK_M15);

      if(!h4_ok)  Logger.Warn("STRUCTURE", "H4 timeframe init failed — degraded");
      if(!h1_ok)  Logger.Warn("STRUCTURE", "H1 timeframe init failed — degraded");
      if(!m15_ok) Logger.Warn("STRUCTURE", "M15 timeframe init failed — degraded");

      // At least one timeframe must be operational
      if(!h4_ok && !h1_ok && !m15_ok)
      {
         Logger.Error("STRUCTURE", "All timeframes failed — engine unavailable");
         m_initialized = false;
         return false;
      }

      // Build initial cached result
      BuildResult();

      m_meta.initialized = true;
      m_initialized      = true;

      Logger.Info("STRUCTURE",
         StringFormat("Init complete. h4=%d h1=%d m15=%d confidence=%.2f",
                       (int)h4_ok, (int)h1_ok, (int)m15_ok,
                       GetConfidence()));
      return true;
   }

   //===================================================================
   // EVALUATE — called by coordinator on bar close
   //
   // PSEUDO-CODE:
   //   Coordinator passes context with new_h4_bar / new_h1_bar /
   //   new_m15_bar flags set based on iTime() comparison.
   //   Only the affected timeframe(s) are updated.
   //   After any update, rebuild the full result.
   //   Return true if any timeframe produced valid output.
   //===================================================================
   virtual bool Evaluate(const IntelligenceContext &ctx) override
   {
      if(!m_initialized) return false;

      bool any_updated = false;

      if(ctx.new_h4_bar)
      {
         UpdateTimeframe(m_h4, SWING_LOOKBACK_H4);
         any_updated = true;
      }
      if(ctx.new_h1_bar)
      {
         UpdateTimeframe(m_h1, SWING_LOOKBACK_H1);
         any_updated = true;
      }
      if(ctx.new_m15_bar)
      {
         UpdateTimeframe(m_m15, SWING_LOOKBACK_M15);
         any_updated = true;
      }

      if(any_updated)
         BuildResult();

      return m_cached.is_valid;
   }

   //===================================================================
   // GET CACHED RESULT (O(1) — called every tick)
   //===================================================================
   StructureResult GetCached() const { return m_cached; }

   //===================================================================
   // RESET — clear all swing history (for testing/restart edge cases)
   //===================================================================
   virtual void Reset() override
   {
      ZeroMemory(m_h4);
      ZeroMemory(m_h1);
      ZeroMemory(m_m15);
      ZeroMemory(m_cached);
      m_cache_valid = false;
      m_initialized = false;
      m_meta.available = false;
      Logger.Info("STRUCTURE", "Engine reset");
   }

   //===================================================================
   // SHUTDOWN — StructureEngine uses no indicator handles (raw CopyHigh)
   // so no IndicatorRelease() needed. Just clean state.
   //===================================================================
   virtual void Shutdown() override
   {
      Logger.Info("STRUCTURE",
         StringFormat("Shutdown. total_evals=%d errors=%d",
                       m_meta.eval_count, m_meta.error_count));
      m_initialized      = false;
      m_meta.initialized = false;
      m_meta.available   = false;
   }

   //--- Convenience accessors for other engines (passed as pointers in Phase 3)
   double GetH4Clarity()  const { return m_h4.clarity; }
   double GetH1Clarity()  const { return m_h1.clarity; }
   double GetM15Clarity() const { return m_m15.clarity; }

   STRUCTURE_STATE GetH4State()  const { return m_h4.state; }
   STRUCTURE_STATE GetH1State()  const { return m_h1.state; }
   STRUCTURE_STATE GetM15State() const { return m_m15.state; }

   bool GetH4Available()  const { return m_h4.initialized  && m_h4.has_min_history; }
   bool GetH1Available()  const { return m_h1.initialized  && m_h1.has_min_history; }
   bool GetM15Available() const { return m_m15.initialized && m_m15.has_min_history; }

   //--- H1 swing levels (used by TrendEngine in later steps)
   double GetH1LastHigh() const
   {
      SwingPoint sp;
      return GetConfirmedHigh(m_h1, 0, sp) ? sp.price : 0.0;
   }
   double GetH1LastLow() const
   {
      SwingPoint sp;
      return GetConfirmedLow(m_h1, 0, sp) ? sp.price : 0.0;
   }
   double GetH1PrevHigh() const
   {
      SwingPoint sp;
      return GetConfirmedHigh(m_h1, 1, sp) ? sp.price : 0.0;
   }
   double GetH1PrevLow() const
   {
      SwingPoint sp;
      return GetConfirmedLow(m_h1, 1, sp) ? sp.price : 0.0;
   }

   //--- H4 swing levels (used by RegimeEngine)
   double GetH4LastHigh() const
   {
      SwingPoint sp;
      return GetConfirmedHigh(m_h4, 0, sp) ? sp.price : 0.0;
   }
   double GetH4LastLow() const
   {
      SwingPoint sp;
      return GetConfirmedLow(m_h4, 0, sp) ? sp.price : 0.0;
   }
};

//--- Global singleton
CStructureEngine StructureEngine;

#endif // CSTRUCTUREENGINE_MQH

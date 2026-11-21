# Phase 2.5 — Guard Layer Hardening Report
## XAUUSD Institutional EA — Complete Audit Findings
### Audits: Compile · Init · State Machine · Persistence · Guard Interaction · Recovery · Performance · Prop-Firm

---

## SECTION A — CRITICAL ISSUES
*Will cause runtime crash, infinite loop, or silent wrong behavior. Must fix before any live testing.*

---

### CRITICAL-1: Infinite Recursion in SaveState() — CCircuitBreaker and CCooldownManager

**Severity:** CRITICAL — Runtime stack overflow, EA crash
**Files:** `Guards/CNewsGuard.mqh` (line 652), `Guards/CCooldownManager.mqh` (line 287)

**Root Cause:**
Both `CCircuitBreaker` and `CCooldownManager` contain a private method `void SaveState()`
and then attempt to implement the base class virtual override with:
```
virtual void SaveState() override { SaveState(); }
```
In MQL5, there is no C++-style scope resolution (`ClassName::Method()`).
When `virtual SaveState()` calls `SaveState()`, it resolves to itself — the virtual method —
not the private implementation. This is an **infinite recursive call** that will immediately
overflow the call stack and crash the EA the first time any guard state is saved.

**Fix:**
Rename the private implementation methods to avoid the naming collision:

In `CCircuitBreaker` (CNewsGuard.mqh line ~455):
```mql5
// BEFORE
void SaveState() { int h = FileOpen(CB_FILE, ...); ... }
virtual void SaveState() override { SaveState(); }  // INFINITE LOOP

// AFTER
void WriteCBStateToDisk() { int h = FileOpen(CB_FILE, ...); ... }
virtual void SaveState() override { WriteCBStateToDisk(); }
virtual void Shutdown()  override { WriteCBStateToDisk(); m_initialized = false; }
```

In `CCooldownManager` (CCooldownManager.mqh line ~78):
```mql5
// BEFORE
void SaveState() { int h = FileOpen(COOLDOWN_FILE, ...); ... }
virtual void SaveState() override { SaveState(); }  // INFINITE LOOP

// AFTER
void WriteCooldownStateToDisk() { int h = FileOpen(COOLDOWN_FILE, ...); ... }
virtual void SaveState() override { WriteCooldownStateToDisk(); }
virtual void Shutdown()  override { WriteCooldownStateToDisk(); m_initialized = false; }
```

**Also fix all internal calls** to the renamed methods:
- All `SaveState()` calls inside `CCircuitBreaker::Trigger()`, `Evaluate()` → `WriteCBStateToDisk()`
- All `SaveState()` calls inside `CCooldownManager::OnTradeClosed()`, `OnNewsCleared()`, `Evaluate()` → `WriteCooldownStateToDisk()`

---

### CRITICAL-2: STATE_PROFIT_TARGET Is a Dead-End State — Never Reached

**Severity:** CRITICAL — Challenge completion never correctly detected
**Files:** `Guards/CPropFirmGuard.mqh`, `Guards/CGuardCoordinator.mqh`, `EA_XAUUSD.mq5`

**Root Cause:**
`CPropFirmGuard.Evaluate()` returns `GUARD_SUSPEND` with `SUSPEND_PROFIT_TARGET`
when balance >= target. The coordinator receives this and calls `HandleSuspend()`,
which transitions to `STATE_SUSPENDED` with reason `SUSPEND_PROFIT_TARGET`.

`STATE_PROFIT_TARGET` (defined in `EA_STATE` enum and handled in the `OnTick()` switch)
is **never entered**. The EA ends up in `STATE_SUSPENDED` instead, which still calls
`OnState_Suspended()` every tick. `CheckResume()` for `SUSPEND_PROFIT_TARGET` returns
false forever — so the EA is permanently suspended but NOT in the dedicated terminal state.

The practical consequence: no clean distinction between "suspension due to limit" vs
"challenge completed." Alerts may still fire but the state machine is semantically wrong.

**Fix:**
In `CGuardCoordinator::HandleSuspend()`, detect `SUSPEND_PROFIT_TARGET` specifically
and route to `STATE_PROFIT_TARGET` instead of `STATE_SUSPENDED`:

```mql5
void HandleSuspend(const GuardEvalResult &result)
{
   // Special case: profit target is a terminal state, not a suspension
   if(result.suspend_reason == SUSPEND_PROFIT_TARGET)
   {
      if(result.close_required)
         CloseOpenPositionSafely("profit_target_close");
      Logger.Info("GUARD_COORD", "PROFIT TARGET REACHED — transitioning to terminal state");
      Alert(EA_NAME, ": CHALLENGE TARGET REACHED — EA suspending permanently.");
      StateManager.Transition(STATE_PROFIT_TARGET, "profit_target_guard");
      return;
   }
   // ... rest of existing HandleSuspend logic
}
```

Also ensure `STATE_PROFIT_TARGET` is reachable from `STATE_SUSPENDED` in `CStateManager`
(currently only reachable from `GUARD_CHECK`, `SEEK_ENTRY`, `MANAGE_TRADE`):
```mql5
case STATE_SUSPENDED:
   return (to == STATE_GUARD_CHECK  ||
           to == STATE_FATAL_ERROR  ||
           to == STATE_PROFIT_TARGET);  // ADD THIS
```

---

### CRITICAL-3: GuardCoordinator.Init() Called Before Guards Are Registered

**Severity:** CRITICAL — Init validity check always fails; "critical guards not registered" warning fires on every startup
**File:** `EA_XAUUSD.mq5` (lines 207–217)

**Root Cause:**
```mql5
if(!GuardCoordinator.Init()) { /* degraded OK during build */ }  // line 207
GuardCoordinator.RegisterGuard(&GuardSysHealth, 1);              // line 208
// ... rest of registrations
```
`Init()` checks whether slots 1 and 2 are registered and logs an error if not —
but registration happens *after* `Init()`. The suppressed `/* degraded OK during build */`
comment masks this real initialization error. In production this means every startup logs
false "critical guard not registered" errors.

**Fix:**
Swap the order: register all guards first, then call `Init()`:
```mql5
// Register all guards FIRST
GuardCoordinator.RegisterGuard(&GuardSysHealth,   1);
GuardCoordinator.RegisterGuard(&GuardPropFirm,    2);
// ... all 10 registrations
GuardCoordinator.RegisterGuard(&GuardCooldown,    10);

// THEN initialize (now can validate all slots)
if(!GuardCoordinator.Init())
{
   Logger.Fatal("INIT", "GuardCoordinator init failed");
   return INIT_FAILED;
}
```

---

## SECTION B — HIGH PRIORITY ISSUES
*Will cause incorrect behavior under specific conditions. Fix before live deployment.*

---

### HIGH-1: CDailyDrawdownGuard Uses StateManager Without Including CStateManager.mqh

**Severity:** HIGH — Compilation failure (hidden dependency on include order)
**File:** `Guards/CDailyDrawdownGuard.mqh` (line 156)

**Root Cause:**
`CheckResume()` calls `StateManager.GetSuspendReason()` but `CDailyDrawdownGuard.mqh`
does not include `CStateManager.mqh`. It compiles only because the main EA file includes
`CStateManager.mqh` first, making the global `StateManager` singleton visible.
If include order changes or the guard is tested in isolation, this fails.

**Fix:**
Add the explicit include to `CDailyDrawdownGuard.mqh`:
```mql5
#include "../Core/CStateManager.mqh"
```

---

### HIGH-2: Global MathSrand() Corruption — CSessionGuard and CCooldownManager

**Severity:** HIGH — Random number sequences corrupted across modules; Phase 5 ExecutionRandomization will be broken
**Files:** `Guards/CSessionGuard.mqh` (line 40), `Guards/CCooldownManager.mqh` (line 56)

**Root Cause:**
MQL5's `MathSrand()` sets a **global** random seed shared across the entire EA process.
Both `CSessionGuard::ComputeSoftBoundaries()` and `CCooldownManager::ComputeJitteredCooldown()`
call `MathSrand()` with their own seeds before calling `MathRand()`. This is safe only when
each module seeds immediately before consuming. However:

1. When Phase 5 `ExecutionRandomizationLayer` also uses `MathSrand()`/`MathRand()`,
   any interleaving (e.g. timer callback between guard evaluation and entry execution)
   can corrupt the sequence another module expects.
2. `ComputeSoftBoundaries()` is called from within `Evaluate()` on day rollover —
   mid-evaluation-chain seeding affects any subsequent `MathRand()` call in the same tick.

**Fix:**
Replace `MathSrand`/`MathRand` with a **local deterministic hash function** that takes
a seed and returns a value without touching global state:

```mql5
// Add to Include/Defines.mqh or a new Include/MathUtils.mqh
int DeterministicRand(int seed, int range_min, int range_max)
{
   // Simple integer hash (no global state)
   int h = seed;
   h ^= h << 13;
   h ^= h >> 17;
   h ^= h << 5;
   h = MathAbs(h);
   int range = range_max - range_min + 1;
   return range_min + (h % range);
}
```

Replace all `MathSrand(seed); MathRand() % N` patterns with `DeterministicRand(seed, min, max)`.

---

### HIGH-3: CEquityGuard Tier Thresholds Wrong if Init() Skipped

**Severity:** HIGH — Wrong thresholds if Evaluate() somehow called before Init()
**File:** `Guards/CEquityGuard.mqh` (lines 59–61)

**Root Cause:**
Constructor hardcodes `tier1=9500, tier2=9300, tier3=9200` — values that assume
`Config.EquityFloor = $9,100`. If `EquityFloor` is set to a different value
(e.g. on a $50K scaled account), and `Init()` is not called (or fails silently),
thresholds will be wrong. MQL5 does not enforce calling `Init()` before `Evaluate()`.

**Fix:**
Set constructor defaults to 0 (invalid sentinel), and add an initialization check in `Evaluate()`:
```mql5
// Constructor
m_tier1_threshold(0.0),
m_tier2_threshold(0.0),
m_tier3_threshold(0.0),

// Evaluate() — first line
if(m_tier3_threshold <= 0)
{
   Logger.Fatal("EQUITY", "Evaluate() called before Init() — thresholds invalid");
   return GuardFatal(...);
}
```

---

### HIGH-4: SpreadGuard File Written as FILE_CSV, Read as FILE_TXT

**Severity:** HIGH — Potential data corruption on certain MQL5 builds/platforms
**File:** `Guards/CSpreadGuard.mqh` (lines 155–156, 194–195)

**Root Cause:**
`SaveCalibration()` opens with `FILE_WRITE|FILE_CSV|FILE_ANSI` but writes raw strings
via `FileWriteString()`. `LoadCalibration()` opens with `FILE_READ|FILE_TXT|FILE_ANSI`.
While `FileWriteString()` behavior is nominally unaffected by `FILE_CSV` flag, this is
an undocumented implementation detail. The MQL5 specification does not guarantee that
`FILE_CSV` mode with `FileWriteString()` produces the same byte output as `FILE_TXT` mode.
This is a latent risk — works now but may break across MT5 builds.

**Fix:**
Use consistent `FILE_TXT` mode for both write and read:
```mql5
int h = FileOpen(SPREAD_CALIB_FILE,
                 FILE_WRITE|FILE_TXT|FILE_ANSI, '\n');
```

---

### HIGH-5: CNewsGuard and CCircuitBreaker Defined in the Same File

**Severity:** HIGH — Architecture violation; misleading naming causes maintainability and dependency confusion
**File:** `Guards/CNewsGuard.mqh`

**Root Cause:**
`CCircuitBreaker` is defined inside `CNewsGuard.mqh` under the `#ifndef CNEWSGUARD_MQH` guard.
Any file that includes `CNewsGuard.mqh` also silently includes `CCircuitBreaker`.
Conversely, there is no way to include `CCircuitBreaker` without `CNewsGuard`.
This violates the one-class-per-file architectural rule stated in Phase 2 design.

**Fix:**
Split into two files:
- `Guards/CNewsGuard.mqh` — contains only `CNewsGuard`
- `Guards/CCircuitBreaker.mqh` — contains only `CCircuitBreaker`

`CCircuitBreaker.mqh` includes `CSpreadGuard.mqh` directly (it already uses it).
Update `EA_XAUUSD.mq5` includes:
```mql5
#include "Guards/CNewsGuard.mqh"
#include "Guards/CCircuitBreaker.mqh"
```

---

## SECTION C — MEDIUM PRIORITY ISSUES
*Correct behavior under normal conditions but fragile under edge cases.*

---

### MEDIUM-1: const_cast in SpreadGuard Public Interface

**Severity:** MEDIUM — Architecturally unsafe; indicates design flaw
**File:** `Guards/CSpreadGuard.mqh` (lines 428, 438)

**Root Cause:**
`GetSessionAvgSpread()` and `GetSessionAvgATR()` are declared `const` but call
`GetSessionHour()` which is non-const. The `const_cast<CSpreadGuard*>(this)->` workaround
compiles but is semantically incorrect — it allows a `const` method to call a method
that could modify state. If `GetSessionHour()` is ever extended to cache a result,
this breaks const correctness silently.

**Fix:**
Extract `GetSessionHour()` into a free function or make it fully const by computing
inline without modifying member state:

```mql5
// Replace GetSessionHour() member method with inline const helper:
void GetSessionHourConst(const GuardContext &ctx,
                          int &sess_idx, int &hour) const
{
   int gmt_min = ctx.gmt_hour * 60 + ctx.gmt_minute;
   SESSION_STATE sess;
   // ... same logic as GetSessionHour but pure computation, no state change
   sess_idx = (int)sess;
   hour     = ctx.gmt_hour;
}
```

---

### MEDIUM-2: CSpreadGuard ArrayInitialize for m_min_spread Uses Wrong Default

**Severity:** MEDIUM — Calibration p95 calculation wrong on first sample if min_spread=999
**File:** `Guards/CSpreadGuard.mqh` (constructor, line with `ArrayInitialize(m_min_spread, 999)`)

**Root Cause:**
`m_min_spread` is initialized to 999 (pips) as a sentinel value. When the first real
sample arrives and `sample_count=1`, `ComputeP95()` returns `MathMin(p95, m_max_spread)`.
But `m_min_spread[s][hr] = 999` is compared against real values in no place.
The actual issue is that `MathMin(spread, m_min_spread[s][hr])` correctly updates to the
real spread — so after 1 sample, `m_min_spread` = that sample's spread. Harmless.

**However**: if `sample_count` is checked before using p95 (it is — `ComputeP95` returns
`m_max_spread` if `n < 2`), and `m_max_spread` starts at 0 — then with 1 sample:
`m_max_spread = that_spread`, `m_min_spread = that_spread`. Return value = that_spread.
This is correct and acceptable.

**Fix:** Document the sentinel value explicitly:
```mql5
ArrayInitialize(m_min_spread, 999.0); // 999 = "no sample yet" sentinel — overwritten on first sample
```

---

### MEDIUM-3: PropFirmGuard Lock File Check After Manual Reset Could Restore Lock

**Severity:** MEDIUM — Logic sequencing issue in Init()
**File:** `Guards/CPropFirmGuard.mqh` (Init(), lines ~141–155)

**Root Cause:**
```mql5
if(Config.ManualReset)
{
   ClearLockFile();        // Deletes lock file
   m_lock_engaged = false;
}
if(ReadLockFile())         // File just deleted — returns false. Safe.
{
   m_lock_engaged = true;  // This line cannot execute if ManualReset was true
}
```
The sequence is actually correct — `ClearLockFile()` deletes the file, then
`ReadLockFile()` finds no file and returns false. `m_lock_engaged` stays false.

**But**: what if `ClearLockFile()` fails (file locked by another process)?
`m_lock_engaged = false` is set regardless — and then `ReadLockFile()` finds
the file still present and sets `m_lock_engaged = true`, overriding the intent.

**Fix:** Add return-value check on `ClearLockFile()`:
```mql5
if(Config.ManualReset)
{
   bool cleared = ClearLockFile(); // Return bool: FileDelete() result
   if(!cleared)
   {
      Logger.Critical("PROPFIRM",
         "ManualReset requested but lock file could not be deleted — lock maintained");
      m_lock_engaged = true; // Stay locked — safer than false positive
   }
   else
   {
      m_lock_engaged = false;
   }
}
```

---

### MEDIUM-4: Spread Calibration ArrayResize in ReadKVFile Is O(n²)

**Severity:** MEDIUM — Performance on startup with large calibration file
**File:** `Core/CPersistence.mqh` (ReadKVFile, lines 87–88)

**Root Cause:**
`ArrayResize(keys, count + 1)` inside a loop causes one reallocation per key-value pair.
For the spread calibration file which can contain `6 × 24 = 144` non-zero cells × 9 fields
= potentially ~1,296 array resizes on startup.

**Fix:**
Pre-allocate to a reasonable maximum before the loop:
```mql5
int ReadKVFile(string filename, string &keys[], string &vals[])
{
   ArrayResize(keys, 0);
   ArrayResize(vals, 0);
   if(!FileIsExist(filename)) return 0;
   // ...
   // Pre-allocate to expected maximum
   ArrayResize(keys, 1500);
   ArrayResize(vals, 1500);
   int count = 0;
   // ... loop fills keys[count], vals[count], count++
   // After loop:
   ArrayResize(keys, count);
   ArrayResize(vals, count);
   return count;
}
```

---

### MEDIUM-5: CSystemHealthCheck Test-File Write Runs Every 30 Seconds

**Severity:** MEDIUM — Unnecessary I/O on VPS; creates + deletes file 2,880 times per day
**File:** `Guards/CSystemHealthCheck.mqh` (HEALTH_FULL_CACHE_SEC = 30)

**Root Cause:**
`CheckPersistence()` creates `EA_XAUUSD_healthcheck.tmp`, writes "ok\n", and deletes it.
This runs every `HEALTH_FULL_CACHE_SEC` (30 seconds). Over a 24-hour period this is
2,880 file create/delete operations — relevant on a VPS with I/O-throttled storage.

**Fix:**
Cache the persistence check result for 5 minutes after a successful write:
```mql5
#define HEALTH_PERSIST_CACHE_SEC  300   // Re-check every 5 minutes

datetime m_last_persist_check;
HEALTH_CHECK_STATUS m_cached_persist_status;

HEALTH_CHECK_STATUS CheckPersistence()
{
   if(m_cached_persist_status == HEALTH_OK &&
      (TimeCurrent() - m_last_persist_check) < HEALTH_PERSIST_CACHE_SEC)
      return HEALTH_OK;
   // ... actual check
   m_last_persist_check = TimeCurrent();
   m_cached_persist_status = result;
   return result;
}
```

---

## SECTION D — LOW PRIORITY ISSUES
*Minor architecture, documentation, or cosmetic issues. Can defer.*

---

### LOW-1: CSessionGuard.mqh Contains Two Classes (CRolloverGuard)

**Severity:** LOW — Same architecture violation as HIGH-5 but lower risk since both classes are simple
**File:** `Guards/CSessionGuard.mqh`
**Fix:** Split into `CSessionGuard.mqh` and `CRolloverGuard.mqh` when refactoring.

---

### LOW-2: SpreadGuard FILE_CSV vs FILE_TXT Mode Inconsistency (Documentation)

**Severity:** LOW — Works correctly in practice but confusing to readers
**File:** `Guards/CSpreadGuard.mqh` (SaveCalibration)
**Fix:** Change `FILE_CSV` to `FILE_TXT` in `SaveCalibration()` as noted in HIGH-4.
This is already captured there — noting here as a documentation concern.

---

### LOW-3: CEquityGuard Header Comment Has Incorrect Tier Dollar Values

**Severity:** LOW — Documentation error only
**File:** `Guards/CEquityGuard.mqh` (file header comment)
**Root Cause:** Header says "Tier2 ($9,300)" but computed value is floor+$400=$9,500.
**Fix:** Correct the header to show formula rather than hardcoded values:
```
// Tier 1: floor + $700 (warning)
// Tier 2: floor + $400 (50% sizing)
// Tier 3: floor + $200 (close + suspend)
```

---

### LOW-4: Heartbeat File Never Closed Between Writes

**Severity:** LOW — File handle leak potential on rapid timer fires
**File:** `Core/CPersistence.mqh` (WriteHeartbeat)
**Root Cause:** Opens handle, writes, closes — all in one call. Correct.
Actually this is fine — audited as no issue. No action needed.

---

### LOW-5: CNewsGuard m_spread_guard NULL Check Duplicated

**Severity:** LOW — Minor code duplication; not a bug
**File:** `Guards/CNewsGuard.mqh`
**Fix:** Extract null-checked access pattern into a private helper in Phase 3 refactor.

---

## SECTION E — MUST FIX BEFORE PHASE 3

These issues will cause **compilation failure, runtime crash, or silent wrong behavior**
if Phase 3 code is added without fixing them first:

| # | Issue | File | Why Blocking |
|---|-------|------|-------------|
| CRITICAL-1 | `SaveState()` infinite recursion | CNewsGuard.mqh, CCooldownManager.mqh | EA crashes on first guard state save (happens at startup on reconnect) |
| CRITICAL-2 | `STATE_PROFIT_TARGET` unreachable | CGuardCoordinator.mqh, EA_XAUUSD.mq5 | Challenge completion never correctly signaled; wrong terminal state |
| CRITICAL-3 | Init() before RegisterGuard() | EA_XAUUSD.mq5 | False startup errors; Init validity check always fails |
| HIGH-1 | Missing `#include CStateManager` | CDailyDrawdownGuard.mqh | Compilation fails if include order changes; Phase 3 adds more files |
| HIGH-2 | Global MathSrand corruption | CSessionGuard.mqh, CCooldownManager.mqh | Phase 5 ExecutionRandomization will have broken sequences |
| HIGH-3 | Zero default tier thresholds | CEquityGuard.mqh | Wrong protection on scaled accounts ($50K/$100K) |
| HIGH-4 | FILE_CSV write / FILE_TXT read | CSpreadGuard.mqh | Latent risk: fix before relying on calibration data |
| HIGH-5 | Two classes in one file | CNewsGuard.mqh | Phase 3 will add more includes; confusing coupling must be resolved |

---

## SECTION F — CAN DEFER UNTIL LATER

These issues are real but do not block Phase 3 development:

| # | Issue | Safe Deferral Reason |
|---|-------|---------------------|
| MEDIUM-1 | const_cast in SpreadGuard | Works correctly; Phase 5 integration can clean up |
| MEDIUM-2 | m_min_spread sentinel value | Functionally harmless; document clearly |
| MEDIUM-3 | PropFirmGuard ClearLockFile return | Edge case (locked file); add in Phase 7 hardening |
| MEDIUM-4 | ReadKVFile O(n²) resize | Only runs at startup; not in hot path |
| MEDIUM-5 | Persistence test write every 30s | Reduce cache interval in Phase 7 |
| LOW-1 | CSessionGuard dual class | Refactor in cleanup pass before live trading |
| LOW-3 | EquityGuard header comment | Documentation only |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Critical | 3 |
| High | 5 |
| Medium | 5 |
| Low | 3 |
| **Total Issues** | **16** |
| Must fix before Phase 3 | **8** |
| Safe to defer | 8 |

---

## Confirmed Correct — No Action Required

The following items were audited and found to be correctly implemented:

- **Throttle first-tick behavior**: `m_eval_count=0` on first tick correctly bypasses throttle cache
- **Fast equity check placement**: Runs before throttle, before context population — correct
- **PropFirmGuard lock after ManualReset**: File deletion → ReadLockFile returns false — safe sequence (with caveat in MEDIUM-3)
- **VPS disconnect behavior**: Open positions protected by server-side SL/TP; no forced close during disconnect — correct by design
- **MathSrand determinism per day**: Same seed from date → same soft boundary values across same-day restarts — correct
- **Guard broker action isolation**: No individual guard calls `OrderSend()` or `PositionClose()` — all broker actions go through coordinator
- **SUSPEND_REASON enum completeness**: All values used in guard files are defined in `Defines.mqh`
- **Spread calibration corruption safety**: Partial file write detected by `n < 10` pair check — fails safely
- **Position file corruption safety**: Validated by ticket=0 / entry<=0 / sl<=0 check — fails safely
- **SpreadGuard pointer injection timing**: `SetSpreadGuard()` called before `GuardNews.Init()` — correct order
- **Emergency close with no position**: `CloseOpenPositionSafely()` returns `true` if no position found — no false error
- **OnTimer spread sampling**: Stale price during disconnect rejected by range check (spread <= 0 || > 200)
- **Night rollover midnight crossing**: `IsInRolloverWindow()` correctly handles window spanning midnight
- **PropFirmGuard one-sided exposure**: Monitoring-only approach is correct per The5%ers rules

---
*Phase 2.5 Hardening Report — Complete*
*8 issues must be resolved before Phase 3 begins*

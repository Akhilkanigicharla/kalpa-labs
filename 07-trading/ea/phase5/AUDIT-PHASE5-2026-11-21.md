# Audit · EA_XAUUSD Phase 5 bundle + ICT_RR_HYBRID_5ERS · 21 Nov 2026

Uploads: `EA_XAUUSD_Phase5.zip` (36 files, 16,690 lines incl. 2 docs), `ICT_RR_HYBRID_5ERS.mq5` (407 lines), and
`XAUUSD_EA_Architecture.md` (same Phase 1 doc as before). Copied verbatim to `07-trading/ea/phase5/`.
**Not compiled:** no MetaEditor here. Line numbers are file lines.

## 1. Coverage (honest ledger)

| Group | Files | Status |
|---|---|---|
| Main | EA_XAUUSD.mq5 (667) | Read in full |
| Execution | CPositionSizer (136), CTradeCalculator (190), CEntryEngine (286) | Read in full |
| Core | CConfig (322), PriceUtils (155) | Read in full |
| Guards (10) | identical to the files audited this morning (GuardTypes differs only by a final newline) | Read in full → `../mql5/AUDIT-2026-11-21.md` |
| Targeted | CVolatilityEngine 180–258, CTradeScorer gates (87–300), CDailyStats API, CStateManager transitions, CSessionGuard time source, Defines constants | Read where they decide trading |
| **Not yet line-audited** | IntelligenceCoordinator, Liquidity, Structure, Regime, RegimePersistence, Trend, IntelligenceTypes, IIntelligenceEngine (≈6,000 lines), CLogger, CPersistence, CTimerSystem, rest of Defines, CSessionGuard body | Pending. The P0 below stops every trade before these matter, so they come after the unit fix |

## 2. The headline: as shipped, this EA can never open a trade (P0, fail-closed)

1. `PriceUtils.Init` sets **1 pip = 1 point** (PriceUtils 57). On a 2-digit XAUUSD that is **$0.01**; on a 3-digit
   broker, $0.001.
2. Every threshold was written as if 1 pip were about $1: SL 30–80 pips (Config 58–59), spread cap 25 (53),
   pullback 25 (77), news-spike ATR 40 (Defines 385), swing sizes 150/60/25 (Defines 434–436), CB velocity 40 (90).
3. Gold's M15 ATR is about $5–10 = **500–1,000 "pips"**, so `ClassifyState` always returns at least `VOL_SPIKE`
   (CVolatilityEngine 205–206), and the scorer rejects `VOL_SPIKE` (CTradeScorer 96). → `decision.valid` is never true.
4. If the spike gate were bypassed: SL = ATR×1.5 ≈ 1,100 "pips", clamped to 80 = **$0.80**
   (CVolatilityEngine 247–254), inside normal spread and noise. Lot = $75 / (80 × $1) = 0.94 → capped at 0.10
   → real risk **$8 (0.08 %)**, not 0.75 %. The spread cap of 25 pips = $0.25 blocks much of the day.

**Fix (one place):** define `pip_size` as a price distance chosen on purpose (e.g. $0.10 or $1.00 for gold) in
`PriceUtils.Init`, derive `pip_value = tick_value × pip_size / tick_size`, and re-state every pip constant in that
unit. Or better, express stops, spread and pullback in ATR multiples. The design's numbers fit pip = $1 best.

## 3. Findings register (new in this bundle)

| ID | Sev | File:lines | Problem | Impact | Fix | Test |
|---|---|---|---|---|---|---|
| P0-1 | P0 | PriceUtils 57; Config 53–90; Defines 358–454; CVolatilityEngine 205; CTradeScorer 96 | Pip = $0.01 vs thresholds sized for ~$1 | No trade ever; if forced, $0.80 stops and 0.08 % risk | Single pip definition + ATR-based limits | Unit test: ATR $7 → state NORMAL, SL in $ range |
| P0-2 | P0 | EA 494–517 | `OnState_ManageTrade` is a stub: no TP1 partial, breakeven, trail, and **no guard evaluation while a trade is open** (GuardCoordinator runs only in GUARD_CHECK, 381–397) | Equity floor, Tier-3 close and the prop lock don't run during a trade; only the server SL protects | Call `GuardCoordinator.Evaluate()` (fast equity + floor) every tick in MANAGE_TRADE and SUSPENDED | Open trade, equity → floor → close within 1 tick |
| P0-3 | P0 | CDailyStats 139, 152; EA 555–574 | `OnTradeOpen` / `OnTradeClose` have **no callers**; `OnTradeTransaction` only logs | Daily loss limit ($300), max 3 trades/day, losing-streak pause, cooldown and profitable-day count never trigger | In `OnTradeTransaction`, on DEAL_ADD for our magic: ENTRY_IN → `OnTradeOpen`; ENTRY_OUT → `OnTradeClose(profit+commission+swap)` + `GuardCooldown.OnTradeClosed` + `GuardPropFirm.RecordTradeDirection` | Simulate 3 closed losses → DailyDD suspends |
| P1-1 | P1 | EA 532–541 | `OnTimer` passes `atr_m5 = 0` | Spread-guard ATR store empty → News ATR trigger dead; volatility baseline falls back to 15 | Pass VolatilityEngine's M5 ATR | After 2 timer fires, `GetLastATR() > 0` |
| P1-2 | P1 | EA 519–527 | In SUSPENDED only `CheckResume()` runs | Confirms guard audit H3: CB/news suspensions never clear; C1: no equity check while suspended | as P0-2 | — |
| P1-3 | P1 | CEntryEngine 185–221 | Retries re-send without re-checking for a position; a timeout that actually filled → duplicate | Second position (bulk-trading rule) | Call `HasOpenPosition()` before each retry; treat 10012/10013 timeouts as "check first" | Mock timeout + filled → no second send |
| P1-4 | P1 | CEntryEngine 112; Coordinator 354/451 | Deviation = SlippageMax×10 points, but pip = point here | 10× looser slippage than intended (100 points) | `SetDeviationInPoints(SlippageMax * pip_size/point)` | Deviation equals 10 pips in points |
| P1-5 | P1 | CSessionGuard 38; Config 42 | Sessions use `TimeGMT()`; in the Strategy Tester `TimeGMT()` equals server time, so London/NY windows shift by the broker offset in backtests | Backtests test the wrong hours | In the tester, derive GMT from `TimeCurrent() - GmtOffset*3600` | Tester run at 10:00 server (GMT+3) → session = 07:00 GMT |
| P1-6 | P1 | Config 36 | Profit target 11,000 (+10 %) | The5%ers High Stakes step 1 is 8 % (10,800); the EA keeps trading past a pass | Set per step (10,800 / 10,500) | — |
| P2-1 | P2 | Config 82–85 | `EnableJitter`, `JitterMin/MaxSec` declared, never used | Dead settings ("execution randomisation") | Remove; The5%ers allows EAs, no need to disguise | — |
| P2-2 | P2 | PriceUtils 141 | `ClampLot` forces at least 0.01 lot even when risk sizing says less | Risk above target on tiny accounts or wide stops | Refuse instead of rounding up | raw 0.004 → refuse |
| P2-3 | P2 | Config 208–226 | Many inputs unvalidated (ProfitTarget vs balance, session hours, CB multipliers, TradeScoreMin, PullbackMaxPips, RealRRMin, RegimeMinScore) | Silent bad config | Validate all | — |
| P2-4 | P2 | Config 315 | `PipsToPoints` returns pips unchanged ("placeholder") | Wrong if ever used | Delete or implement | — |
| Info | — | EA 279–287 | Orphaned-position recovery not implemented (Phase 7) | Restart with an open trade: detected, not managed | — | — |

Guard-layer findings (C1–C3, H1–H9, M1–M9) from this morning still apply unchanged.

## 4. ICT_RR_HYBRID_5ERS.mq5 (407 lines, read in full)

A different, simpler EA (swing/fib + EMA trend + 20-bar breakout), with a The5%ers risk envelope.

| Sev | Lines | Finding |
|---|---|---|
| P0 | 201–211, 303 | Floor and daily-loss checks only **block new entries** on a new bar; nothing closes an open position at the floor or at the daily breaker, and `tradingHalted` is never set true. A position can run through The5%ers' 5 % daily or 10 % max loss on its own SL only |
| P1 | 13, 172–178, 258–262 | No magic number set (`CTrade` default 0); `HasOpenPosition` and the trailing stop act on **any** position on the symbol, including manual or other EAs' trades |
| P1 | 350–386 | SL/TP and lot are computed from the previous bar's **close**, but the order fills at the current ask/bid, so the real risk and RR differ from the plan; `trade.Buy()==true` isn't checked against `ResultRetcode` |
| P1 | 396–406 | Losing-streak logic counts every deal on the account (all symbols, entry deals with 0 profit) and ignores commission/swap |
| P1 | 213–214 | `maxSpreadPoints = 60` is $0.60 on 2-digit gold but $0.06 on 3-digit (blocks everything) |
| P2 | 233–247 | News filter ±2 min only; the calendar isn't available in the Strategy Tester (returns "clear") |
| P2 | 155–156 | `isPH/isPL` compare only older bars (no right-side confirmation): not look-ahead, but not a confirmed swing either |
| Evidence | 5 | "Live May 13 → Jun 2: +$468, 45 % WR, PF 1.67": about 3 weeks, tens of trades, no confidence interval. Not proof of an edge |

## 5. Verdict

- **EA_XAUUSD Phase 5:** *Prototype quality.* Safe only because it can't trade (P0-1). Fixing units alone would make
  it trade **without** daily limits (P0-3), without guards during a trade (P0-2), and without trade management.
  Fix order: P0-1 → P0-3 → P0-2 → guard C2/H3 → demo.
- **ICT_RR_HYBRID_5ERS:** *Development quality.* Trades, but its prop-firm envelope doesn't close positions at the
  limits (P0) and it isn't isolated by magic number.
- **Edge:** THE EXISTING INFORMATION IS INSUFFICIENT TO ESTABLISH A STATISTICALLY VALIDATED TRADING EDGE (for both).

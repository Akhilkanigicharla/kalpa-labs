# EA_XAUUSD independent debug pass (b): 26 Nov 2026

Scope: `07-trading/ea/phase5/EA_XAUUSD/` with preset `presets/E8_Pro_10K_challenge.set` (E8 Pro $10K, live, Wine VPS).
Method: desk check only. There is no MetaEditor here. I followed the include order in EA_XAUUSD.mq5, ran a script that checks each `Object.Method(` call against its class, and checked every `input` name, the preset keys and enum values, and the API signatures. Then I read the live paths: entries, sizing, the daily stop, the profit cap, the floor, news, the Friday cut, restarts and close loops.

## Pass 1: compile

- **Include order:** every global object or variable is declared before it is used. `FloorNow` is in Core/CDailyStats and is used in Guards and Execution. The guard singletons are declared in the .mq5 before `CMixEngine` is included. `NewsDerisk`, `NewsBlackout` and the `KALPA_US_EVENTS_UTC` list are in CMSNREngine, before the scorer and the mix engine. `g_last_trade_r` is in CPositionSizer.
- **Input names:** all unique. All 15 preset keys exist. `inp_Program=8` = `PROGRAM_CLASSIC` and `inp_Stage=1` = `STAGE_STEP1`.
- **Preset values pass Config.Init:** daily stop = min(1.5, 2.5 - 1) = 1.5%. Auto floor = $9,300, above the firm line of $9,200. Target $10,850 is within [10K, 30K].
- **No C++-only syntax:** no `auto`, lambdas, `std::`, `nullptr` or templates.
- **API signatures checked:** `CalendarValueHistory`, `CalendarEventById`, `OrderCalcMargin`, `HistorySelect`/`HistorySelectByPosition`/`HistoryDeal*`, CTrade (`PositionClose`, `PositionClosePartial`, `SetTypeFillingBySymbol`, `SetExpertMagicNumber`, `ResultRetcode` returning uint printed with `%u`), and `%I64u`/`%I64d`/`%lld`/`%llu` on ulong/long.
- **Brace, parenthesis and bracket balance:** OK in every .mq5/.mqh, after stripping comments, strings and `D'..'` literals.

## Pass 2: live logic findings

| Sev | File:line | Problem | Fix | Applied |
|---|---|---|---|---|
| HIGH | EA_XAUUSD.mq5:157; Guards/CSystemHealthCheck.mqh:164 | When the terminal starts before it logs in (for example after a VPS reboot), `ACCOUNT_MARGIN_MODE` reads 0, which is NETTING. OnInit then returns INIT_FAILED, and SysHealth latches a permanent FATAL. Either way the EA unloads and does not come back until someone attaches it again. | Treat NETTING as fatal only when `ACCOUNT_LOGIN > 0`. | Yes |
| HIGH (decision) | Guards/CEquityGuard.mqh:79-81, 186 | Tier 3 = floor + $200 = **$9,500**. At a 5% drawdown it closes everything and suspends until equity > $9,500. With no positions left, equity cannot get back above that line, so the EA stops for good. This sits well inside E8's 8% line. Tier 2 sizing (50%) is never applied, because `GetSizeMultiplier()` has no caller. | Product choice: keep it as a hard 5% stop, or tie the tiers to the firm line, or let it resume at the next server day. | No |
| MEDIUM (behaviour) | Guards/CDailyDrawdownGuard + EA_XAUUSD.mq5:414-418 | The main strategy's 3-trades/day cap and its 3-loss pause SUSPEND the state machine. While suspended, the mix only cancels pendings and opens nothing. So A347 (mix not capped) holds only partly. The 15-min cooldown is a BLOCK, so it does not stop the mix. | Product choice, as in the earlier review. | No |
| MEDIUM | Intelligence/CMSNREngine.mqh:371, 439 | The backup schedule computed `datetime - datetime` inside one cast. If MQL5 treats that result as unsigned, the "after the event" half of the blackout window is lost. | Cast each value to `long` before subtracting. | Yes |
| MEDIUM | Guards/CSystemHealthCheck.mqh:38 | The price sanity cap was $5,000. Gold was about $3.5K-4K this month (local GC=F data $3,509 on 20 Nov; fxnx 12 Nov $3,951). A rally above $5K would BLOCK main entries, and after any disconnect the EA would never resume. | Raise the cap to 10000. | Yes |
| MEDIUM | Include/PriceUtils.mqh:73 | Tick value or size can read 0 right after a reboot. PriceUtils then fails, OnInit returns INIT_FAILED and the EA unloads for good. | Wait up to 10 × 500 ms before failing. | Yes |
| LOW | EA_XAUUSD.mq5:665 | After a restart between the TP1 half-close and the breakeven move, the main trade would half-close a second time. | If the position already has an OUT deal in its history, mark the partial as done. | Yes |
| LOW | Guards/CGuardCoordinator.mqh:379 | When the market is closed, the failed emergency close repeats every 5 s and pops an Alert each time. | Show the Alert at most every 10 min. | Yes |
| LOW | Intelligence/CMSNREngine.mqh:460 | A failed news-derisk close was retried on every tick and every second. | Retry every 10 s. | Yes |
| LOW | Intelligence/CMSNREngine.mqh:430-432 | Derisk inputs are not range-checked. They cannot be checked in Config.Init, because they are declared later in the include order. | Left as is. | No |
| INFO | Preset | Main risk is $10K × 0.30% × 0.5 = $15. A 0.01 lot at a 30-80 pip stop risks $30-80, more than 1.5× $15, so the main strategy will mostly skip (by design). At $4K gold, the weekend gap budget (1.5%) and the news jump budget (2%) allow about 0.01 lot net to be held. | n/a | n/a |

**Checked and OK:**
- Every order has a stop loss: the main entry rejects SL ≤ 0, and the mix uses zone or EMA stops.
- Lot sizing: tick value / tick size (100 oz), floored to the lot step, minimum lot only if its risk is ≤ 1.5× target, 0.10 hard caps, and a margin floor of notional / 15.
- Daily stop: 1.5% below max(balance, equity) at server midnight, checked every tick and every second. It is latched, saved, and cleared at the next server day.
- Profit cap: measured from the day's start balance, so it cannot fire at the rollover itself.
- Floor: $9,300. `FloorNow` is off in the challenge preset (`inp_FloorAfterPayoutPct` = 0).
- News: entry blackout ±120 min (main strategy via the scorer, mix via `GateOk`). Derisk runs from 120 min before an event, using GMT for the backup list and server time for the MT5 calendar.
- Friday cut: runs at most every 10 s with a bounded loop.
- Close loops: all bounded and throttled.
- DryRun=false: both the main strategy and the mix reach `CTrade` Buy/Sell/BuyLimit/SellLimit.

## Pass 3

I re-read every edit. The static locals are inside functions or class methods. `fail_t` is in scope in the loop. The history scan re-selects the position afterwards. No test strings changed.

**Results after the fixes:** `pytest -q tests` = **283 passed**. Brace/paren/bracket balance = OK. Nothing committed.

## Still needs a real MetaEditor compile

- `CEntryEngine` calls `HasOpenPosition()`, which is defined at the end of the .mq5. MQL5 normally resolves calls to global functions defined later in the file, but only the compiler can confirm it.
- `StateManager.GetStateAge() % 600` uses a datetime with modulo.
- Constructor init lists are not in member order (warnings only).
- The dates of the 2026-27 CPI/NFP/FOMC events were not re-verified in this pass.

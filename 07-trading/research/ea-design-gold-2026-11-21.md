# A315 · Akhil's "XAUUSD Institutional EA" design (The5%ers High Stakes), backtested (21 Nov 2026)

Source: Akhil's upload (sections 1–9; the text stops inside section 9). Code `research/ea_design_gold.py`,
tests `tests/test_ea_design_gold.py`, numbers `reports/ea-design-gold*.json`.

## Fact checks on the design
- **Daily loss:** the doc says The5%ers High Stakes has no daily drawdown limit. Wrong: High Stakes terminates at
  **5% daily loss**. The doc's own 3% daily stop keeps it safe anyway.
- **Target:** step 1 is 8% (some sources say 10%), step 2 is 5%; max loss 10%. EAs are allowed (no HFT, arbitrage or tick scalping).
- **India:** The5%ers is not named on the RBI Alert List seen 21 Nov, but RBI says the list isn't exhaustive, and
  MetaTrader 4/5 themselves are on it. Legal grey area: get a CA's view before paying.
- **5-minute history:** only 60 days are free here; a longer download was blocked, so the M15/M5 test is short.

## Results
| Version | Period | Trades | Result |
|---|---|---|---|
| As written (H4 → H1 → M15 → M5) | 60 days | 1 | +1.6R (one win; no evidence) |
| As written, setup on H1 | 2 years | 0 | never trades |
| All $ numbers turned into ATR multiples (fixed in advance) | 60 days / 2 years | 1 / 0 | still almost never trades |

Why: 6 filters must all agree. H4 regime is "on" only 26% of the time, and with the H1 trend, the session,
the rejection candle and the "$30 room" rule, 1,700 London/NY 15-minute bars shrink to 1 trade.

## Which filters cost the trades (2 years, setup on H1, ATR-scaled; explains the design, not a pick)
| Removed | Trades/month | Avg R | Earlier / later half | Profit on $10K | Worst drop | The5%ers fail |
|---|---|---|---|---|---|---|
| room rule | 0.3 | +0.62 | +1.41 / +0.31 (7 trades) | +$330 | 0.8% | 0% |
| rejection + room | 1.0 | +0.20 | +0.37 / +0.09 | +$440 | 2.3% | 0% |
| + H1 agreement | 3.1 | +0.09 | +0.04 / +0.14 | +$595 | 6.0% | 0% |
| + pullback rule | 4.1 | +0.08 | +0.02 / +0.14 | +$690 | 6.7% | 0% (33% reach 8%) |

Reading: the design's risk side works (0.75% risk, 3% daily stop, never broke The5%ers' 5% daily or 10% max
loss in any start). The entry side is too strict to trade, and when loosened it earns about +0.1R a trade,
around $300 a year on $10K: an 8% target takes ~2.5 years at that pace.

## A316 · 3 trades per opportunity (Akhil: "every time… take three trades with stop loss… forward test it")
Same 118 signals (loose version above, 2 years H1). Risk 0.75% split into 3 × 0.25%; one stop for all three;
targets 1R, 2R, 3R; after target 1 the stop moves to breakeven + $0.20, after target 2 to the 1R level.

| Exits | Win % | Avg R | Profit on $10K | Worst drop | Green months | Reach The5%ers 8% | Fail |
|---|---|---|---|---|---|---|---|
| Doc's exits (50% at 1.5R, trail, 2.5R) | 46% | +0.08R | +$690 | 6.7% | 17/29 | 33% | 0% |
| **3 trades, 1R/2R/3R** | **52%** | +0.05R | **+$377** | 7.3% | 18/29 | 19% | 0% |
Of the 3-trade signals: 53% hit no target, 25% one, 14% two, 9% all three.
The 3-trade version wins more often but makes less, because the breakeven stop cuts trades 2 and 3 short.
Forward test: `paper/ea-ladder/state.json`, every weekday from 21 Nov 2026 (no orders sent).

## A317 · Phase 3 "Market Intelligence Layer" gate, measured (2 years of hourly gold)
Code `research/phase3_gate.py`, tests `tests/test_phase3_gate.py`, numbers `reports/phase3-gate-*.json`.

| Gate step (London/NY hours, cumulative) | Open alone | Still open after this step |
|---|---|---|
| Regime confirmed, not ranging (with persistence) | 34% | 34% |
| H1 trend = regime direction | 10% | 10% |
| Volatility not too quiet / news spike | 60% | 8.1% |
| Liquidity score ≥ 0.50 | 16% | 3.4% |
| H4 and H1 structure agree | 17% | **2.2% (104 hours in 2 years)** |

- **Round-number rule:** "within 25 pips of a $50 level" is always true when 1 pip = $1 (the reading the
  doc's ATR numbers need), so every entry loses 0.25 liquidity points. The pip size has to be defined once.
- **On the 118 A315 signals:** the gate keeps 12 (+0.47R avg, +5.7R ≈ +$430 on $10K) and drops 106 (+0.04R).
  The direction is encouraging, but 12 trades in 2.4 years is too few to prove anything, and it is 0.4 trades a month.
- **Phase 2.5 hardening report:** it reviews MQL5 files (`Guards/*.mqh`, `EA_XAUUSD.mq5`) that are not in the
  repo or the uploads, so the 8 must-fix items can't be applied or checked here.
- Execution "randomisation" / "human-like" timing: The5%ers allows EAs, so disguising a bot isn't needed,
  and doing it to hide automation could break a firm's terms. Left out.

## Full Phase 1 document (re-uploaded complete, 858 lines) — 3 problems in its pseudo-code
The re-upload adds sections 9–11 (trade management, pseudo-code, risk review). The other 6 uploads are exact
copies of the Phase 3 design and Phase 2.5 report (same file hashes). Still no `.mq5` / `.mqh` code.

1. **Lot size is 10–100× too small (line 738).** `pip_value = TICK_VALUE × (10 / TICK_SIZE)`. On a typical
   XAUUSD contract (100 oz, tick 0.01, tick value $1) that gives $1,000 a pip per lot. True value: $100 a pip
   if 1 pip = $1, or $10 if 1 pip = $0.10. So $75 risk / (30 × 1,000) = 0.0025 lot, which rounds to 0.00 and is
   clamped up to 0.01 lot. Real risk is then $30 (pip = $1) or $3 (pip = $0.10), never the intended 0.75%.
   Fix: `pip_value = TICK_VALUE × (pip_size / TICK_SIZE)` with `pip_size` defined once.
2. **Wide stops are tightened instead of skipped (lines 729 vs 661).** `CalculateSLDistance` clamps the stop to
   80, so the later `sl_pips > 80` check can never fire. Section 4A says such trades must be skipped; the code
   would take them with a stop that is too tight. Fix: return the unclamped value and skip above 80.
3. **"Pass probability 55–70%" (line 837)** is an estimate with no test behind it. Our 2-year test: as written,
   0 trades; loosened, 33% of starts reach 8% and the median takes well over a year.
Also still open: "no daily DD" (High Stakes has 5%), target $1,000 = 10% vs step-1 8%, and the undefined pip size.

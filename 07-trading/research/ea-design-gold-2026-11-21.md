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

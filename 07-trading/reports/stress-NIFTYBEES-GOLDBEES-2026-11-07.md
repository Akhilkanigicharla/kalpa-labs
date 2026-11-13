# Stress test: NIFTYBEES ⇄ GOLDBEES regime rotation (07 Nov 2026)

Paper only. Not advice. Data: Yahoo Finance daily bars via yfinance (NIFTYBEES.NS, GOLDBEES.NS), 01 Feb 2010 to 06 Nov 2026, 4135 common trading days. Indian delivery costs (STT, stamp, exchange, GST, DP) on every switch.

## Funnel (train period)
- Variants tried: **20** → enough trades: **20** → profitable after costs: **20** → Sharpe > 0.5: **20**
- Train ends 23 Oct 2024; hold-out starts 24 Oct 2024 (looked at once).

## Best variant
- trend=250,vol_cap=0.2: train Sharpe 0.85, train return +388%, hold-out return -4% (buy-and-hold NIFTYBEES: +4%).
- Better than **80%** of random switching with the same number of trades.
- Survivors still profitable in the hold-out: **15 of 20**.
- PBO (chance the best in-sample pick is overfit): **0.88**; Deflated Sharpe of best: **0.90**.

## Data checks
- Repaired: NIFTYBEES: removed 19 Dec 2019 (wrong-scale block, close 13.02)
- Repaired: NIFTYBEES: removed 20 Dec 2019 (wrong-scale block, close 13.03)
- Repaired: GOLDBEES: removed 19 Dec 2019 (wrong-scale block, close 0.34)
- Repaired: GOLDBEES: removed 20 Dec 2019 (wrong-scale block, close 0.34)
- Clean: no gaps, no impossible prices, no one-day jumps above 25%.

## Verdict
**FAIL**: lost money in the hold-out; not better than 95% of random; PBO 0.5 or more (likely overfit); Deflated Sharpe not above 0.95. Not traded, not even on paper.

## Verdict rule
Moves to paper trading only if: Sharpe > 0.5 in train, profitable in the hold-out, better than 95% of random, PBO < 0.5 and DSR > 0.95. Real money needs 90 days of paper results and Akhil's decision.

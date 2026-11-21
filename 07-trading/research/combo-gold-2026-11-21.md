# A310 · MSNR + Fair Value Gap + Order Block on gold: a combined strategy (21 Nov 2026)

Akhil: "Msnr 1hr and 4hr fix also try adding fair value gap and order block and other things and take best trades
from other and form a new strategy and test it". Code `research/combo_gold.py`, tests `tests/test_combo_gold.py`,
numbers `reports/combo-gold-*.json`.

## Method (fixed before running)
- 8 setups: MSNR fresh level (key level 2 and 5), QM, equal-low sweep, rejection; SMC fair value gap, order block, Fibonacci.
- Each alone and every pair "A confirmed by B" (B formed in the last 12 1h / 6 4h bars, within 0.5 ATR), buy and sell,
  1h and 4h, 9 EMA on/off, storyline on/off: **1,024 versions**. Double costs throughout.
- Picked the 5 best on the **earlier data only** (Jul 2024 → Aug 2025: ≥ 30 trades, ≥ +0.10R, beats random p < 0.05).
  12 qualified. The new strategy takes a trade whenever any of the 5 fires.
- Then tested once on the **later data** (Sep 2025 → Nov 2026) that the selection never saw.

## Picks
| Setup | Earlier data | Later data | Random entries, later |
|---|---|---|---|
| 1h sell, Fibonacci + 9 EMA | 92 trades, +0.11R | 122, −0.00R | −0.24R |
| 1h sell, Fibonacci confirmed by FVG + 9 EMA | 58, +0.22R | 96, −0.17R | −0.17R |
| 1h buy, QM confirmed by order block | 53, +0.40R | 49, +0.07R | −0.08R |
| (same, 9 EMA on: identical trades) | | | |
| 4h buy, MSNR fresh level (5) confirmed by rejection + 9 EMA | 92, +0.37R | 98, +0.01R | −0.01R |

## The new strategy
| | Trades | Win % | Avg R | Total | ₹ at ₹100 a trade | Worst drop |
|---|---|---|---|---|---|---|
| Earlier data (where it was picked) | 237 | 48% | +0.28R | +65R | +₹6,510 | −10R |
| **Later data (the real test)** | **269** | 40% | **+0.01R** | **+3.6R** | **+₹364** | **−22R (−₹2,230)** |
Random entries on the later data: −0.08R a trade. Chance the new strategy is no better than random: 13%.

## Reading
The combination looked strong where it was chosen and fell to break-even on new data: the classic sign of
picking past winners. It loses less than random trades, but not reliably (13%), and the worst drop is 6× the profit.
Fair value gaps alone lost the most (−0.51R earlier); order blocks and Fibonacci helped only as confirmations.
Not added to paper trading as its own strategy; the A308/A309 paper runs continue.

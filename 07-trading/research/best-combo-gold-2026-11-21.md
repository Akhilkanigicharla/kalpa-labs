# A323 · "Best" gold mix: every strategy so far, 1h/2h/4h, 2 years (21 Nov 2026)

Code: `research/best_combo_gold.py`. Results: `reports/best-combo-gold-2026-11-21.json`. Every trade: `reports/best-combo-gold-trades-2026-11-21.csv`.

The rule for joining the mix was fixed before any result was seen: in the earlier part (Jul 2024 – Aug 2025), a strategy needs at least 15 trades and an average of +0.05R or better. 13 of 27 candidates joined:
- EA+MSNR 1h
- MSNR fresh_v long 1h / 2h / 4h and fresh_v short 2h / 4h
- MSNR QM long 1h / 2h / 4h and QM short 1h / 4h
- EMA9 2h and EMA9 4h

| 2 years, $10K, 0.5% risk a trade | Value |
|---|---|
| Trades | 4,745 (≈166 a month) |
| Wins / losses / breakeven | 1,966 / 2,748 / 31 (41% win) |
| Avg R | +0.164 (later part: +0.143) |
| Profit | +$38,810, no compounding |
| Worst drop | 11.1% |
| Worst day | −$525 |
| Profit months | 26 of 29 |
| Double costs ($0.80 a trade) | +0.138R, +$32,772 |
| Random entries, same exits | +0.065R (p < 0.05, 20 seeds) |
| The5%ers step 1 | 0.5% risk: 85% pass / 14% fail · 0.35%: 97% / 2% · **0.25%: 98% / 1%, +$19,405, worst drop 6.5%** |

**Limits**
- Random entries also make +0.065R. Part of the profit comes from the exits in a market that has trended up, not from skill. The excess over random is about +0.10R a trade.
- The MSNR setups assume a limit order fills the moment price touches the level. Real fills will be worse.
- 1h, 2h and 4h often take the same move, and up to 11 trades can be open at once.
- The weakest members are EMA9 4h (+0.007 vs random +0.017) and MSNR QM long 2h (+0.066 vs random +0.074). They are candidates to drop after paper trading.
- Paper first. Nothing here trades real money.

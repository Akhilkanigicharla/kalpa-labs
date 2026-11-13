# Can ₹5,000 make ₹200 a day after charges? (13 Nov 2026)

Akhil asked for a bot that makes at least ₹200/day net from ₹5,000. Script: `aggressive_5k_test.py`.
Raw output: `aggressive_5k_results.csv`, `aggressive_5k_per_stock.csv`.

## Rules checked first (two sources each)
- Equity intraday (MIS) leverage is capped at 5x (20% margin): Zerodha support, Sharekhan bulletin May 2026.
  So ₹5,000 controls at most ₹25,000. ₹200/day = 0.8% net on ₹25,000 every day.
- No leverage on options; buyers pay the full premium (Zerodha support; SEBI rules from Feb 2025).
- Nifty lot = 65 since Jan 2026 (NSE circular; Fyers, 5paisa, Sahi). ₹5,000 buys a premium of at most ~₹76.
- Option selling (straddles etc.) needs lakhs of margin, so it is not possible with ₹5,000.

## Results (last ~60 trading days, all charges, 5-min bars)
| Test | Avg ₹/day | Days ≥ ₹200 | Worst day | Result |
|---|---|---|---|---|
| ORB r=1, 5x, 51 stocks avg | −39 | 0% | −131 | loses |
| ORB r=2, 5x | −32 | 1.7% | −132 | loses |
| VWAP trend (2 settings), 5x | −37 to −42 | 0% | −78 | loses |
| RSI reversal (2 settings), 5x | −54 to −57 | 0% | −185 | loses |
| Stocks-in-play top pick, 5x | −18 | 7.5% | −114 | loses |
| Nifty option buying, ₹5,000 (modelled) | −235 | 30% | −2,504 | **account wiped out** |

- 13 of 306 stock+strategy combos made money: about what luck alone gives.
- Picking the 10 best combos on the first 30 days and trading them the next 30 days: −₹12.6/day.
- Only ADANIPORTS ORB (r=2) held up in both halves: about +₹56/day in the second half. One survivor out of 306 is
  likely luck; it is watched on paper only (task A168), not traded.
- Option buying hits ₹200+ on 30% of days, but the losing days are bigger, and it went below zero.
  This is the same pattern SEBI found: most F&O traders lose money (91% in FY25, 87.7% in FY26).

## Verdict
No tested route reaches ₹200/day from ₹5,000. The aggressive routes lose money faster than Track A.
Option premiums in test C are Black-Scholes estimates using India VIX (no free intraday option data), so C is approximate.

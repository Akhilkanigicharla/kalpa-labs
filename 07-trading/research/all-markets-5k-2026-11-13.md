# All markets, all strategies, any leverage: can ₹5,000 average ₹200/day? (13 Nov 2026)

Script: `all_markets_5k_test.py`. Results: `all_markets_5k_results.csv`.
Follows `aggressive-5k-2026-11-13.md` (Indian intraday stocks and options: all lost).

## Access rules (checked in 2+ sources)
- Crypto futures: legal on FIU-registered Indian exchanges (Delta Exchange India, CoinDCX, CoinSwitch). Up to 100x
  leverage. Fees about 0.05% taker + 18% GST on the full position value. Spot crypto: 30% tax, 1% TDS, and losses
  cannot be set off. Crypto F&O tax treatment is disputed (30% vs slab rate).
- Offshore leveraged forex/CFD apps: not allowed under FEMA; the RBI Alert List names about 95 platforms.
  Only INR pairs on recognised Indian exchanges are legal. EUR/USD below is for information only.
- Gold: MCX futures. Nifty: NSE futures (a lot needs far more than ₹5,000 margin; included anyway).

## Method
- 13 strategies × settings (21 in total): EMA trend, Donchian breakout, RSI reversal, Bollinger fade, momentum,
  buy-and-hold. Long and short. Hourly bars.
- The best one per market is chosen on year 1 only, then traded on year 2 untouched (no hindsight).
- Leverage 1x–100x is applied on year 2 with costs × leverage.
- 2,000 bootstrapped one-year paths per leverage level.

## Best case per market (highest odds of averaging ₹200/day over a year)
| Market | Strategy picked on year 1 | Leverage | Actual avg ₹/day (year 2) | Odds of ₹200/day | Odds of wipe-out |
|---|---|---|---|---|---|
| Nasdaq-100 | buy & hold | 10x | +2.7 | 13% | 0% at 10x, 62% at 20x |
| Nifty | 6-hour momentum | 20x | −8.5 | 3% | 95% at 50x |
| Gold | buy & hold | 10x | −11.2 | 2.5% | 85% at 20x |
| BTC | buy & hold | 5x | −13.5 | 0.2% | 63% at 10x, 100% at 20x |
| ETH | buy & hold | 3x | −13.0 | 0.1% | 86% at 10x |
| SOL | Donchian 20 | any | ≤ −8.4 | 0% | 100% at 20x |
| USD/INR | Bollinger 3 | any | ≤ −0.5 | 0% | — |
| EUR/USD (not legal) | buy & hold | any | ≤ −0.4 | ~0% | 86% at 100x |

The best actual result of any market at any leverage: +₹11.4/day (Nasdaq-100, 5x).
Wipe-out counts only equity reaching exactly 0; exchanges liquidate earlier, so real odds are worse.

## Verdict
No market, strategy or leverage level gives ₹200/day from ₹5,000 with reasonable odds. Raising leverage
raises the odds of a lucky year only slightly (best: 13%, and only on a market that is hard for a ₹5,000 Indian
account to reach with leverage). It raises the odds of losing everything much faster.

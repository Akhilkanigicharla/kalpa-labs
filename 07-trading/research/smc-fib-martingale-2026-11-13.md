# Order blocks, fair value gaps, Fibonacci, martingale: tested on Indian stocks (13 Nov 2026)

Akhil: "use all the papers... martingale... orderblock and fair value gap and fibonacci... news, sentiment, volume... test it".

## What the research says (checked today)
- FVG: TradingView placebo study, 14 measurements over 3 asset classes, 3 timeframes, 2 periods: no advantage over size-matched random zones.
- Order blocks: TradingView placebo study, 31 runs: no reliable difference vs placebo levels.
- Fibonacci: forexop, G10 FX 1-minute 2003-2016: explained by chance. Gurrib et al. 2022 (Financial Innovation): Fibonacci beat buy-and-hold for US energy stocks 2017-2020 (one positive academic study).
- Martingale: Taranto & Khan 2020 (IMFI 17(3)): can outperform short term but "will almost surely ruin an investment account in the long term".

## Our test (src/smc.py; scripts research/smc_placebo_test.py, research/fvg_momentum_check.py)
51 NSE large caps + Nifty, daily 2012-2026, long only (no overnight shorts in cash), limit entry at the zone, stop under the zone, 2R target,
20-day time exit, 0.25% round-trip cost, stop counted first. Every real zone vs 3 random same-size zones (placebo).

| Pattern | Trades | Win | Avg per trade after costs | Placebo avg | Real minus placebo (95% range) |
|---|---|---|---|---|---|
| Fair value gap | 11,645 | 32.5% | +0.113% | −0.142% | **+0.256% (+0.198 .. +0.313)** |
| Order block | 2,090 | 38.3% | +0.071% | +0.047% | +0.024% (−0.168 .. +0.214): no edge |
| Fibonacci 50-61.8% | 5,176 | 36.8% | +0.160% | +0.064% | +0.094% (−0.039 .. +0.227): not proven |

FVG extra checks: beats momentum-matched no-gap twins by +0.215% (+0.142 .. +0.279); positive in 2012-18 (+0.100%) and 2019-26 (+0.124%).
But: average hold 3.3 days, +0.034% per day in a trade vs +0.065%/day for simply holding the average stock (17.8%/yr). Real
information, too small to beat holding; 66% of trades hit the stop.

## Martingale (double after each loss) on the 11,645 real FVG trades, in real time order
- Start 10% (up to 80%): account −99.9%. Fixed size at the same 40% average exposure: grew. Start 5%: same story.
- 1,000 crash-preserving reshuffles (blocks of 100 trades): martingale beat same-exposure fixed sizing in 0%.
- Why: single trades of −13% to −15% (gaps through stops). At an 80% doubled position each costs 10-12% of the account.
- **Decision: martingale is never used in Kalpa bots.** (An earlier shuffle test of only 2,000 trades made it look good: shuffling hides real losing streaks.)

## News, sentiment, pre-market volume
Already built and tested: opening-volume "stocks in play" (−3.7% after costs, 60 sessions); World Check of global markets, yields, rupee,
oil, India VIX, Fed/RBI events (tested as trading rules, none improved returns); newspaper intraday tips in India earn no significant returns
(Kolte et al. 2024). No free archive of past Indian news exists for a fair news-trading test, so news stays an alert.

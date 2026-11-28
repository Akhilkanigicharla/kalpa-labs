# A307: hourly gold strategies vs prop rules (2026-11-28)

**Weak evidence.** About 2 years of hourly data (Yahoo keeps no more), one market, two rule sets fixed before testing. Paper research only, no tips. Rules and method: `research/hourly_gold_prop.py` docstring.

Data: 13762 hourly bars, 2024-07-08 to 2026-11-27 (GC=F x USD/INR, INR per gram).

## The edge itself (per trade, in R = multiples of the risk)

| Book | Trades | Win rate | Avg R | Total R | Profit factor |
|---|---|---|---|---|---|
| breakout | 488 | 0.484 | -0.009 | -4.3 | 0.97 |
| breakout|random | 355.7 | 0.454 | -0.051 | -18.215 | - |
| pullback | 503 | 0.439 | 0.001 | 0.7 | 1.0 |
| pullback|random | 393.75 | 0.403 | -0.088 | -34.775 | - |

Random rows are the average of 20 seeds (same trade count, stop size, target and exit time; random day, hour and side).

## Prop challenge (a fresh attempt every 5th trading day)

| Firm | Book | Risk | Pass | Fail | Unfinished | Median days to pass | Random pass | Random fail |
|---|---|---|---|---|---|---|---|---|
| Hindustan 1-Step | breakout | 0.5% | 0% | 9% | 91% | - | 0% | 24% |
| Hindustan 1-Step | breakout | 1.0% | 0% | 46% | 54% | - | 5% | 63% |
| Greenwick 2-Step | breakout | 0.5% | 0% | 1% | 99% | - | 0% | 22% |
| Greenwick 2-Step | breakout | 1.0% | 0% | 46% | 54% | - | 2% | 56% |
| Hindustan 1-Step | pullback | 0.5% | 19% | 29% | 53% | 218.0 | 1% | 56% |
| Hindustan 1-Step | pullback | 1.0% | 24% | 61% | 14% | 78.0 | 9% | 77% |
| Greenwick 2-Step | pullback | 0.5% | 10% | 29% | 61% | 305.5 | 0% | 41% |
| Greenwick 2-Step | pullback | 1.0% | 21% | 47% | 32% | 111.0 | 10% | 73% |

## Verdict

- **breakout**: no edge (avg -0.009 R a trade, profit factor 0.97 after costs). Beating the random row only shows the rules lose less than coin flips; a prop pass here would be luck, so it is not kept.
- **pullback**: no edge (avg 0.001 R a trade, profit factor 1.0 after costs). Beating the random row only shows the rules lose less than coin flips; a prop pass here would be luck, so it is not kept.

## How to read it

- Random books hold fewer trades than the real ones because overlapping random trades are dropped (one position at a time).
- A book only beats luck if its pass rate is clearly above the random row at the same risk AND its average R is above 0.
- 'Unfinished' = the 2-year window ended before a pass or fail; late starts have little time, so pass rates are a floor.
- Costs ignore the MCX import-duty premium and overnight funding (every day ends flat). Bots are banned at Hindustan and need written approval at Greenwick (A305), so any use is signals only.
- Two years of one instrument cannot prove an edge. Treat a good result as a reason for a longer paper run, not for money.

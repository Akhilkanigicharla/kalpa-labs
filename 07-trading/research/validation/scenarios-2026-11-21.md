# EA mix scenarios A–I (21 Nov 2026)

Research only. Not investment advice, and none of these numbers is a promise.
- Script: `research/validation/ea_mix_scenarios.py`. Results: `reports/ea-mix-scenarios-2026-11-21.json`.
- Engine: `research/ea_mix_backtest.portfolio()` with the new options. Its defaults still reproduce the A329 engine trade for trade ($13,239.59 at 0.25%).
- Data: GC=F hourly from 1 Jul 2024 to 20 Nov 2026. Sizing is fixed at $10K with no compounding.

## Assumptions
- **Time:** data timestamps are UTC and are treated as server time.
  - The day boundary is the UTC date.
  - The Friday cut runs at the first bar close at or after 22:00 on Friday. If the data has no bar that late, it runs at the last Friday bar close. GC=F's last Friday bar closes at 21:00 or 22:00 UTC.
  - On a real GMT+2/+3 server, 22:00 is about 1–2 h before the market closes.
- **Equity:** marked at every 1h bar close. Research trades only carry R, so the entry price is the 1h open at `t_in`. Open R is side × (close − entry) / stop distance, clipped to [min(−1, r), max(2, r)]. Intrabar dips are not seen.
- **Rails (B onwards and A2):** min stop $1.50, lot cap 0.10, day stop at 4% of max(balance, equity) at day start (closes all positions, no new trades that day), equity floor $9,100 (closes all, stops for good).
- **Weights:** KEEP 1.0, HALF 0.5, CUT 0, as in `WEIGHTS_2026_11_21`. The EA's own risk equals the mix risk × its weight. The EA stays outside the 2% mix open-risk cap but counts toward max positions.
- **The5%ers simulation:** a new attempt starts every Monday that has at least 90 days of data after it (111 attempts).
  - A pass is judged on closed balance and needs 3 profitable days of at least $50.
  - A breach is equity at or below 95% of the day-start reference, or at or below $9,000.
  - A floor halt counts as a fail.
  - Once funded, 80% of profit above $10K is paid out every 14 days.
  - The "within N days" pass rates only count attempts with at least N days of data.

## Scenarios
- **A:** current setup: 13 strategies, 0.25% risk, 2% cap, old closed-loss day stop.
- **A2:** A plus the rails.
- **B:** weights at 0.25%.
- **C:** weights at 0.40%.
- **D:** C plus max 3 positions and no opposite positions.
- **E:** D plus the Friday cut to 1.25%.
- **F:** E plus $0.30/oz per side extra cost.
- **G, H, I:** added after D lost profit and showed a bigger drawdown than C.
  - G = C plus the Friday cut.
  - H = G plus $0.30.
  - I = B plus the Friday cut plus $0.30.

| Scen | Trades | W/L | Win% | Avg R | Net $ | Worst day $ | Max DD $ (% of 10K) | Lowest eq (vs $9K) | Step 1 pass % (30/60/90/180d) | Funded % | Failed % | Avg payout/attempt $ | Months to 1st payout |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 3,731 | 1521/2188 | 40.8 | 0.156 | 13,240 | -295 | 1,100 (11.0%) | 9,798 (+798) | 18.9/55.9/73.9/80.6 | 97.3 | 48.6 | 3,071 | 3.1 |
| A2 | 3,731 | 1521/2188 | 40.8 | 0.156 | 13,233 | -295 | 1,100 (11.0%) | 9,798 (+798) | 18.9/55.9/73.9/80.6 | 93.7 | 70.3 | 2,862 | 3.1 |
| B | 2,035 | 873/1160 | 42.9 | 0.248 | 10,696 | -118 | 495 (4.95%) | 9,865 (+865) | 1.8/39.6/72.1/86.7 | 98.2 | 0.0 | 3,071 | 4.3 |
| C | 2,450 | 1057/1383 | 43.1 | 0.262 | 20,904 | -205 | 546 (5.46%) | 9,770 (+770) | 36.0/85.6/98.2/100 | 100 | 0.0 | 7,503 | 2.5 |
| D | 1,603 | 716/882 | 44.7 | 0.304 | 16,058 | -229 | 721 (7.21%) | 9,771 (+771) | 22.5/66.7/88.3/100 | 100 | 0.0 | 5,672 | 3.0 |
| E | 1,603 | 716/882 | 44.7 | 0.305 | 16,098 | -229 | 721 (7.21%) | 9,771 (+771) | 22.5/66.7/88.3/100 | 100 | 0.0 | 5,703 | 3.0 |
| F | 1,599 | 713/882 | 44.6 | 0.257 | 13,517 | -234 | 781 (7.81%) | 9,721 (+721) | 18.0/61.3/80.2/100 | 100 | 0.0 | 4,869 | 3.5 |
| G | 2,450 | 1055/1385 | 43.1 | 0.262 | 20,862 | -205 | 546 (5.46%) | 9,770 (+770) | 36.0/83.8/98.2/100 | 100 | 0.0 | 7,526 | 2.5 |
| H | 2,445 | 1050/1386 | 42.9 | 0.212 | 16,860 | -210 | 568 (5.68%) | 9,671 (+671) | 22.5/63.1/92.8/100 | 100 | 0.0 | 6,242 | 3.1 |
| I | 2,034 | 871/1160 | 42.8 | 0.196 | 8,446 | -121 | 518 (5.18%) | 9,803 (+803) | 0.0/26.1/52.3/82.7 | 98.2 | 0.0 | 2,383 | 5.6 |

Most of A's 48.6% failures are "funded, then breached" during the Feb–May 2026 drawdown. With the floor (A2), the same accounts are halted at −9% instead.

## Monte Carlo
Setup: 5,000 paths, 252 trading days, day-block bootstrap with a mean block of 5. P(−10%) is measured over a full year and does not stop at a pass.

| Scen | P(−10%) | P(floor −9%) | P(day ≤ −5%) | P(Step 1 in 1y) | Median trading days to +10% | 50% edge haircut: P(−10%) / P(floor) / P(pass 1y) / median days |
|---|---|---|---|---|---|---|
| A | 1.98% | 3.08% | 0 | 97.7% | 46 | – |
| B | 0.00% | 0.00% | 0 | 99.9% | 65 | – |
| C | 0.10% | 0.14% | 0 | 99.9% | 33 | – |
| E | 0.46% | 0.88% | 0 | 99.5% | 41 | – |
| F | 1.20% | 1.90% | 0 | 98.6% | 47 | 12.0% / 14.9% / 85% / 67 |
| G | 0.10% | 0.14% | 0 | 99.9% | 33 | – |
| H | 0.30% | 0.58% | 0 | 99.7% | 39 | 6.5% / 9.0% / 92% / 62 |
| I | 0.02% | 0.04% | 0 | 99.1% | 80 | 1.7% / 2.5% / 79% / 121 |

The 50% haircut stands for the out-of-sample decay (about 45%) plus the placebo share found in the validation report.

## Crash stress
The worst day in the data is **30 Jan 2026**: −7.3% close to close, with a low 9.2% under the previous close. The data has only 16 bars that day.
- **E and F made 0 trades that day and lost $0.** The day before, E lost $51.
- Why: the minimum-lot rule skipped every signal. When ATR is that high, even 0.01 lot risks more than 1.5× the target.
- The next worst days, 5 Feb 2026 and 21 Oct 2025, cost E $0 and −$77 (F −$79).
- **Hypothetical worst case:** E's largest open book was 0.22 lots, with $143 of risk to the stops. If a 9.5% gap jumped every stop, that book would lose about **$5,800**, which breaches the account.
- **Weekend exposure:** the largest book E held over a weekend was 0.17 lots, about $4,500 at a 9.5% gap. G's largest was 0.16 lots (about $3,900).
- The Friday cut limits risk to the stops, not lots, so it cannot protect against a gap. The worst real weekend result was −$113 (E) and −$146 (G).

## Recommendation
**Default: G.** That is the weights, 0.40% risk, 2% cap, the rails and the Friday cut, with **no** max-3-positions rule and **no** no-opposite rule.
- **Against E/F, G has lower breach risk and more profit:**
  - Historical drawdown: 5.5% vs 7.2%.
  - MC P(−10%) with costs: 0.3% vs 1.2%.
  - With a 50% haircut: 6.5% vs 12%.
- **The position cap and the no-opposite rule hurt.** They removed about 850 good trades and still raised the drawdown. This matches section 7 of the validation report.
- **If Akhil wants breach risk under 2% even at half the edge, use I (0.25%).** The cost is a slower pass: about 52% within 90 days and 79% within a year, against 93% and 92% for G.
- **Not modelled:** spread spikes, swaps, intrabar equity dips and broker XAUUSD vs GC=F differences. Paper-trade on demo before trusting any of this.

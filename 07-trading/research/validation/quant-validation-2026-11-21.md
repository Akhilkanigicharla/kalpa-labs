# Gold mix: quant validation (21 Nov 2026)

This is research only. It is not investment advice and it guarantees nothing.
Input: `reports/ea-mix-backtest-trades-cap2-2026-11-21.csv`, with 3,731 trades from 2 Jul 2024 to 20 Nov 2026. The data is GC=F hourly futures from yfinance, in UTC. The backtest already charges $0.40/oz per round trip.
Scripts are in `research/validation/`:
- `gen_candidates.py` writes all 27 candidate strategies to `candidates_r.csv`.
- `quant_validate.py` covers sections 1–8 and writes `results.json`.
- `risk_grid.py` runs the real portfolio engine at different risk and cap settings, plus a limit-fill test, and writes `risk_grid.json`.
- `haircut_mc.py` writes `haircut_mc.json`.

Every rule below was declared in the script docstrings before the scripts were run. The mix was originally selected on data before 2025-09-01 ("SEL"), so everything after SEL is out-of-sample (OOS) for the selection.

## 1. Stats (0.25% risk, $10K fixed)

| Strategy | n | win% | avg R | PF | Sharpe | t(R) | P&L $ | DSR (N=50) |
|---|---|---|---|---|---|---|---|---|
| MSNR fresh_v long 1h | 879 | 40.3 | 0.173 | 1.33 | 2.33 | 3.45 | 4,069 | 0.36 |
| MSNR fresh_v long 2h | 420 | 44.3 | 0.304 | 1.45 | 2.22 | 4.16 | 2,606 | 0.29 |
| MSNR fresh_v short 2h | 403 | 44.7 | 0.301 | 1.57 | 2.47 | 4.05 | 2,948 | 0.45 |
| MSNR fresh_v long 4h | 140 | 47.1 | 0.390 | 1.72 | 1.76 | 3.09 | 1,260 | 0.09 |
| MSNR qm long 4h | 21 | 71.4 | 0.815 | 4.61 | 1.52 | 3.05 | 473 | 0.01 |
| MSNR qm long 1h | 177 | 44.6 | 0.159 | 1.35 | 1.04 | 1.59 | 722 | 0.01 |
| MSNR qm short 1h | 177 | 39.5 | 0.078 | 1.20 | 0.64 | 0.83 | 390 | 0.00 |
| EA+MSNR 1h (EA rules) | 68 | 51.5 | 0.176 | 1.24 | 0.50 | 1.21 | 197 | 0.00 |
| MSNR fresh_v short 4h | 126 | 36.5 | 0.067 | 1.14 | 0.41 | 0.52 | 248 | 0.00 |
| EMA9 2h | 794 | 36.5 | 0.030 | 1.03 | 0.26 | 0.58 | 377 | 0.00 |
| MSNR qm short 4h | 17 | 41.2 | 0.104 | 1.37 | 0.34 | 0.37 | 59 | 0.00 |
| EMA9 4h | 448 | 38.2 | −0.004 | 1.00 | −0.03 | −0.06 | −27 | 0.00 |
| MSNR qm long 2h | 61 | 36.1 | −0.017 | 0.89 | −0.23 | −0.11 | −81 | 0.00 |
| **Portfolio** | 3,731 | 40.8 | 0.149 | 1.27 | 3.06 | 6.38 | 13,240 | 0.82 |

Portfolio risk numbers:
- The longest losing streak was 17 trades.
- The worst day was −$203 (−2.0%) and the worst week was −$342.
- **Max drawdown is understated.** The 4.9% figure is measured against grown equity. Measured in dollars against the $10K start, which is how the prop firm counts it, the peak-to-trough drawdown is **10.5%**.

## 2. Walk-forward

The calendar halves split on 2025-09-10, almost the same date as SEL.

- **Portfolio:**
  - First half +$9,053 at avg R 0.186. Second half +$4,186 at avg R 0.101.
  - After SEL: avg R 0.108, t = 3.09.
  - 9 of 10 quarters were positive.
  - The edge fell by about 45% out-of-sample.
- **Positive in both halves:** fresh_v long 1h, fresh_v long 2h, fresh_v short 2h, qm long 4h and EA+MSNR. fresh_v long 4h was +1,146 then +114, so it is fading.
- **Positive in only one half:** EMA9 2h (+777 / −400), EMA9 4h (+166 / −193), fresh_v short 4h (+258 / −10), qm short 4h (+107 / −49) and qm long 1h (+548 / +174, t = 0.5 after SEL). qm short 1h went the other way: +59 then +331.
- **Negative in both halves:** qm long 2h.

## 3. Overfitting

**Deflated Sharpe Ratio (DSR)** for the portfolio. The variance of Sharpe across trials was taken from the 27 candidates: 1.12 annualised.

| Trials (N) | DSR |
|---|---|
| 13 | 0.98 |
| 27 | 0.92 |
| 50 | 0.82 |
| 100 | 0.66 |

- **After SEL only, at N=50: DSR = 0.48.** The out-of-sample Sharpe of 2.5 sits at the expected maximum from luck alone (2.54).
- Only fresh_v long 1h, fresh_v long 2h and fresh_v short 2h have DSR above 0.25.

**Probability of Backtest Overfitting (PBO), CSCV method** with 16 blocks and 12,870 splits:

| Trial set | PBO | Sharpe of in-sample best: IS → OOS |
|---|---|---|
| 27 candidates | 0.005 | 3.3 → 2.25 |
| 13 mix strategies | 0.06 | 2.85 → 1.78 |

PBO is low, but the OOS Sharpe decays by about 35%.

**Placebo check.** This uses the repo's own result in `best-combo-gold-2026-11-21.json`.
- When the mix's entries are replaced by random levels, it still earns **+0.065 R** a trade, against 0.149 R for the real mix.
- About half of the backtested R is structural: limit-at-level entries, 2R exits and a +50% gold drift (GC=F went from 2334 to 3515).
- That structural part is not proven signal.
- This fits the earlier 25-year daily result, where MSNR showed no edge over random.

**Limit-fill realism.** I required price to trade through the level instead of only touching it. My copy of the simulator reproduces the original exactly at a $0 requirement.

| Fill requires | MSNR avg R | Change |
|---|---|---|
| Touch only | 0.219 | — |
| Trade through by $0.30 | 0.204 | −7% |
| Trade through by $1.00 | 0.178 | −19% |

## 4. Monte Carlo

Setup: 10,000 paths, a stationary block bootstrap of daily P&L (mean block 5 days), 1-year horizon.

Rules used: The5%ers High Stakes. I checked them on the5ers.com/high-stakes today and confirmed them with a second source:
- Step 1 target +10%, Step 2 target +5%.
- 5% daily loss limit and 10% max loss.
- At least 3 profitable days.
- No time limit.
- Trading in the 2 minutes either side of high-impact news is not allowed.

Current mix at 0.25% risk:
- Max drawdown: median 5.4%, 95th percentile 9.7%, 99th percentile 12.4%.
- Chance of a −5% day: 0.
- Chance of hitting −10% total: 0.9%.
- Step 1 pass: 51% within 60 days, 73% within 90 days, 96% within 180 days.
- Step 2 pass: 80% within 60 days, 91% within 90 days.

Using only the post-SEL days, Step 1 pass is 33% / 55% / 87% at 60 / 90 / 180 days.

**Scaling risk linearly is wrong.** At 0.75% risk the naive scaling gives a 96% chance of a −5% day, but the real engine's 2% open-risk cap stops that from happening. So I re-ran the real portfolio engine at each setting (`risk_grid.json`). All figures below include +$0.30/oz extra cost.

| Setup | Sharpe | Max DD vs start | Worst day | Step 1 pass (90d / 1y) | Fail (1y) |
|---|---|---|---|---|---|
| Current 13, 0.25%, cap 2% | 2.06 | 12.2% | −2.2% | 56% / 94% | 4% |
| Current 13, 0.50%, cap 2% | 2.72 | 15.0% | −3.9% | 84% / 90% | 10% |
| Current 13, 0.50%, cap 3% | 2.56 | 25.2% | −4.6% | 83% / 85% | 15% |
| Cut to 8, 0.25%, cap 2% | 3.33 | 7.2% | −1.7% | 59% / 99.9% | 0% |
| **Cut to 8, 0.40%, cap 2%** | 3.24 | 6.3% | −2.8% | 85% / 99% | 0.8% |
| Cut to 8, 0.50%, cap 2% | 3.65 | 8.3% | −3.4% | 93% / 99% | 1% |

**Edge haircut** (`haircut_mc.json`). This takes the cut 8-strategy mix at 0.40% risk with +$0.30 cost, and lowers avg R by 50% to match the out-of-sample decay plus the placebo share:
- Step 1 pass: 58% within 90 days, 82% within 180 days.
- Chance of failing within 1 year: 9%.
- At a 75% haircut: 41% pass within 90 days and 24% fail within 1 year.
- If the true edge is only the placebo level, the expected result is about zero.

## 5. Cost stress (extra $/oz per side, on top of the $0.40 round trip already charged)

| Extra cost | Portfolio P&L | Sharpe | Max DD |
|---|---|---|---|
| +0.00 | $13,240 | 3.06 | 4.9% |
| +0.10 | $11,766 | 2.73 | 5.4% |
| +0.30 | $8,818 | 2.06 | 7.4% |
| +0.50 | $5,870 | 1.38 | 10.4% |

- **Fail on costs:** EMA9 2h (+377 → −733 at +$0.30), EMA9 4h, qm long 2h, and EA+MSNR at +$0.50.
- **Survive +$0.50:** every fresh_v strategy, qm long 1h, qm long 4h and qm short 1h (barely, +$54).
- Average cost at +$0.30 is $1.19 a trade, or 0.053 R.

## 6. News and spikes

There are 75 CPI, NFP and FOMC events in the window.
- **No mix trades open within 2 hours of an event**, because the A325 blackout already blocks them.
- **The blackout is justified.** Across all 27 candidates without a filter, entries within 2 hours average **−0.104 R (n=292)** against +0.113 R otherwise (p = 0.008). Keep the blackout.
- Mix trades already open when an event lands average +0.44 R (n=160) against +0.14 R for the rest. This is a small sample and probably reflects long exposure during the bull run. Don't build on it.

**Spike-capture rules (declared in advance, with $0.30/oz per side cost):**
- **Rule A, news-bar breakout (n=66):** avg R −0.08, t = −0.63. First half −0.10, second half −0.06. **No edge.**
- **Rule B, ATR-expansion momentum (n=628):** avg R −0.14, t = −2.6. First half −0.25, second half +0.01. Without costs it is −0.08. **No edge; it mean-reverts if anything.**

Do not add spike-chasing.

## 7. Risk changes (fit on year 1 before 2025-07-01, test on everything after)

| Rule | Test Sharpe | Max DD | Return / DD |
|---|---|---|---|
| Baseline | 2.84 | 6.9% | 9.8 |
| (a) Drop strategies with negative year-1 P&L (EA+MSNR, EMA9 4h, qm long 2h) | 3.20 | 5.1% | 12.7 |
| (b) Inverse-volatility weights | 2.83 | 4.8% | 8.3 |
| **(e) (a) + (b)** | **3.35** | 5.2% | **13.3** |
| (c) Volatility targeting | 2.28 | 12.8% | 5.3 (worse) |
| (d) Max 2 same-side positions | 2.21 | 6.9% | 5.1 (worse) |
| (d) Max 1 same-side position | 1.35 | 7.7% | 1.9 (worse) |

- Average daily correlation between strategies is 0.05.
- The highest pairs are within families: fresh_v short 2h with short 4h at 0.54, and fresh_v long 1h, 2h and 4h with each other at 0.45–0.51.
- Concurrency caps remove good trades, so the 2% open-risk cap is already enough.

## 8. Verdict

- **Keep:** fresh_v long 1h, fresh_v long 2h and fresh_v short 2h. They are positive in both halves, survive +$0.50 costs and are the only ones with DSR above 0.25.
- **Keep at half weight:** fresh_v long 4h (fading), qm long 1h (t = 0.5 out-of-sample), qm long 4h (only 21 trades), qm short 1h (cost-fragile) and EA+MSNR (68 trades, failed the year-1 rule).
- **Cut:** EMA9 2h, EMA9 4h, qm long 2h, fresh_v short 4h and qm short 4h. They are negative out-of-sample or after costs, with DSR of about 0. The year-1 version of this rule improved test Sharpe from 2.84 to 3.2–3.35.

**Parameter changes:**
- Set the MIX list to the 8 strategies above.
- Raise `inp_MixRiskPct` from 0.25 to **0.40**.
- Keep `inp_MixMaxOpenRiskPct` at **2%**. A 3% cap doubles drawdown for the current mix.
- Set the EA's own risk to 0.40%, not 0.75%.
- Keep the 2-hour news blackout and the 4% daily stop.
- Don't add volatility targeting or concurrency caps.
- Optional: weight by inverse volatility from trailing data.

**Realistic expectations** for the cut 8 strategies at 0.40% risk, after +$0.30 cost and a 25–75% edge haircut:
- **About +1.5% to +4.4% a month** ($150–440 on $10K). The backtest says +5.8%, which is the optimistic case.
- Step 1 pass within 90 days: **about 40–75%**. Within 180 days: **about 60–95%**.
- Failure within 1 year: **about 3–25%**.
- If the edge is only placebo-level, expect about breakeven and an eventual fail.

**Caveats:**
- GC=F is a futures contract, not broker XAUUSD spot. Futures data has roll gaps.
- Swaps, spread spikes and intraday equity drawdown (the daily loss limit is judged on equity) are not modelled.
- The 2-minute news rule is not modelled.
- There are only 2.4 years of data, mostly in a strong gold bull market.
- The cuts in section 8 were chosen after seeing post-SEL data. Only the year-1 rule (a) is clean.
- Before trusting any of these numbers, paper-trade on the broker's MT5 demo for at least 2 months and compare live avg R with the out-of-sample 0.10 R.

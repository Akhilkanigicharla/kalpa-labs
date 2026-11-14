# A282: Alpha Brain on live data, day by day (14 Nov 2026)

Akhil: "Results look ok to me, do more testing with live data and give me results day wise."
Script `research/a282_alpha_brain_live.py`. Prices re-downloaded fresh to the latest NSE close (Fri 13 Nov 2026).
Files: `a282_daily_2026.csv` (every trading day), `a282_monthly_2026.csv`, `a282_picks_2026.csv`,
`a282_rolling_starts.csv`, `a282_rolling_summary.csv`. Trial T0033.

## 1. ₹10,000 from 1 Jan 2026 to 13 Nov 2026 (214 trading days, all unseen by the 2026 model)
| Line | ₹10,000 became | Return | Worst fall | Green days | Avg day | Best day | Worst day | Trades |
|---|---|---|---|---|---|---|---|---|
| **Alpha Brain, top 5 monthly** | **₹10,073** | **+0.7%** | −12.9% | 50% | +₹0.3 | +₹313 | −₹317 | 81 |
| Alpha Brain + Nifty 200-day filter | ₹9,932 | −0.7% | −4.0% | 88%* | −₹0.3 | +₹235 | −₹317 | 16 |
| Current bot (Nifty trend + gold)** | ₹9,584 | −4.2% | −15.7% | 51% | −₹1.9 | +₹483 | −₹688 | 13 |
| Buy and hold Nifty | ₹9,679 | −3.2% | −14.7% | 52% | −₹1.5 | +₹337 | −₹241 | 1 |

\* The filter sat in cash (liquid-fund rate) from March, so most "green" days are ₹1 of interest.
\** Monthly approximation of the bot in the A273 engine, not the live paper ledger.

**By month (%):**
| Month | Brain | Brain + filter | Current bot | Nifty |
|---|---|---|---|---|
| Jan | −0.8 | −0.8 | +6.6 | −3.8 |
| Feb | −1.8 | −1.8 | −0.7 | −0.5 |
| Mar | −9.3 | −0.8 | −3.6 | −11.0 |
| Apr | +3.4 | +0.4 | +1.0 | +7.2 |
| May | −1.5 | +0.3 | +2.3 | −1.5 |
| Jun | +2.1 | +0.4 | −4.7 | +1.5 |
| Jul | +5.1 | +0.4 | +1.2 | +2.0 |
| Aug | +0.2 | +0.4 | +3.9 | −0.9 |
| Sep | −0.5 | +0.4 | −5.3 | −5.8 |
| Oct | −3.4 | +0.4 | −3.2 | +1.7 |
| Nov (to 13th) | +8.4 | +0.2 | −1.0 | +9.5 |

**Last 10 trading days (₹ value / change that day):**
| Date | Brain | Day | Bot | Day | Nifty | Day |
|---|---|---|---|---|---|---|
| 30 Oct | 9,289 | −11 | 9,677 | −44 | 8,843 | +34 |
| 2 Nov | 9,466 | +177 | 9,569 | −108 | 8,942 | +99 |
| 3 Nov | 9,584 | +118 | 9,577 | +8 | 9,081 | +139 |
| 4 Nov | 9,787 | +203 | 9,734 | +157 | 9,170 | +89 |
| 5 Nov | 10,100 | +313 | 9,807 | +73 | 9,386 | +216 |
| 6 Nov | 10,132 | +32 | 9,727 | −80 | 9,547 | +161 |
| 9 Nov | 10,095 | −37 | 9,755 | +28 | 9,573 | +26 |
| 11 Nov | 10,102 | +7 | 9,691 | −64 | 9,623 | +50 |
| 12 Nov | 10,238 | +136 | 9,583 | −108 | 9,679 | +56 |
| 13 Nov | 10,073 | −165 | 9,584 | +1 | 9,679 | 0 |

Monthly picks the brain made in 2026 are in `a282_picks_2026.csv` (e.g. 30 Oct: BAJAJFINSV, GOLDBEES, HINDALCO,
INDUSINDBK, SHRIRAMFIN).

## 2. Every possible start month since Jan 2019
| Hold | Line | Starts | Median | Worst | Best | Lost money | Beat the bot |
|---|---|---|---|---|---|---|---|
| 3 months | Brain | 92 | +3.0% | −25.2% | +39.5% | 29% of starts | 51% |
| 3 months | Brain + filter | 92 | +1.3% | −12.7% | +23.7% | 29% | 46% |
| 3 months | Current bot | 92 | +2.9% | −6.0% | +11.7% | 22% | – |
| 3 months | Nifty | 92 | +3.7% | −31.2% | +27.9% | 34% | 52% |
| 12 months | Brain | 83 | +11.6% | −17.3% | +88.3% | 33% | 45% |
| 12 months | Brain + filter | 83 | +6.6% | −13.6% | +49.8% | 27% | 33% |
| 12 months | **Current bot** | 83 | **+15.8%** | **−1.9%** | +37.3% | **4%** | – |
| 12 months | Nifty | 83 | +9.4% | −27.0% | +82.7% | 21% | 48% |

## Verdict
- In 2026 so far the brain is **ahead**: +0.7% while the bot is −4.2% and Nifty −3.2%. It won by picking banks and
  finance stocks into the November rally.
- Over every 12-month window since 2019, the **current bot is steadier**: it lost money in 4% of start dates against
  33% for the brain, with a higher typical year (+15.8% vs +11.6%). The brain has the bigger best case (+88%).
- So: the brain is a higher-risk, higher-swing option; the current bot stays the ₹10,000 plan. The brain keeps paper
  trading monthly (`paper/alpha-brain/`) and this file is re-run each month with fresh data.

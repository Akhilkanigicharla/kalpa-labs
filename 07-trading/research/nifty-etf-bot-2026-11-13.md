# Track A: Nifty ETF trend bot, real-data results (13 Nov 2026)

Akhil, 13 Nov 2026 19:10 IST: "trading track nifty etf bot" → **Track A picked.**

## Data and method
- Nifty 50 index (^NSEI), Yahoo Finance via yfinance, 2 Jan 2008 – 12 Nov 2026 (4,627 days). Used for the SIGNAL because
  NIFTYBEES' Yahoo history has an unadjusted 2019 split. Orders fill at the NIFTYBEES price.
- ^NSEI is a price index: it leaves out dividends (roughly 1–1.5%/yr, not re-checked today). Holding the real ETF gets them,
  so "just holding" is a little better than shown, and the bot (in the market 67% of the time) gets less of that.
- Gate: rolling walk-forward (3 years to pick settings, the next 1 year traded), Indian delivery costs, PSR, PBO, DSR,
  stress test at 2× costs + a one-day delay. Every run logged in `research/trials.csv` (T0001–T0014) so the deflated Sharpe
  counts all tries. Gate thresholds are still pending Akhil's approval.
- **New: idle cash earns interest.** A real bot parks out-of-market money in a liquid ETF. LIQUIDBEES returned 4.69%/yr
  since 2003 after its 0.69% fee (anandrathi.com scheme page, as on 1 Jun 2025; 1Y 4.92%, 5Y 3.99%). Cheaper copies: Mirae
  0.15%, Kotak 0.19% expense ratio (groww.in). The lab used 0% before, which was unfair to every timing strategy.

## Gate results (out-of-sample Feb 2011 – Jul 2026)
| Strategy | Cash 0% | Cash 4.7% | Fails at 4.7% |
|---|---|---|---|
| tsmom (12-month-style trend, lookback 63–252 days) | rejected | **5 of 6 pass** (Sharpe 0.86 vs hold 0.68, PBO 0.11, DSR 0.997) | stress: 0.62 vs hold ~0.68 |
| ma_filter_vt | rejected | 5 of 6 (Sharpe 0.78, worst fall −12.8%) | stress |
| sma_cross / ema_cross | rejected | 4 of 6 | overfit (PBO 0.73), stress |
| ma_filter, tsmom_vt, markov_regime | rejected | rejected | several |

Nothing passes all 6. We do NOT loosen the gate to get a pass.

## What the money would have done (tsmom, settings picked by the walk-forward, cash 4.7%)
| | ₹1 became | Per year | Worst fall |
|---|---|---|---|
| A. Bot, up to 100% NIFTYBEES | ₹3.83 | 9.4% | −15.7% |
| B. Bot under draft risk rules (max 20% in one position) | ₹2.28 | 5.7% | −2.6% |
| Hold Nifty always | ₹4.39 | 10.4% | −38.4% |
| Liquid ETF only | ₹1.99 | 4.7% | 0% |

- Before tax. The bot sells more often: short-term gains taxed at 20% (+cess) each time, holding defers tax. After tax the
  gap to "hold" is wider than shown.
- The draft rule "stop at a 10% fall from peak" would have fired in June 2011 and switched A off for good. 8 of 186 months
  lost ≥ 4% (the draft monthly cap).

**Plain answer:** on Nifty, a trend bot is a *smoother ride*, not *more money*. It roughly halves the worst crash
(−16% vs −38%) and gives up about 1 point a year. The draft risk rules, written for several swing trades at once, turn it
into a liquid fund. Akhil chooses the rules (CEO queue C66).

## Built today
- `src/backtest.py` + `src/gate.py`: `cash_rate` (default 0, old numbers unchanged; track A uses 0.047).
- `src/live/runner.py`: `tsmom` in the runner; `--signal-symbol ^NSEI` (signal from the index, fill at the ETF price, refuses
  if the two dates are > 4 days apart); settings picked each day by the same rule as the gate; idle-cash interest in paper mode.
- `src/data.py` bug fix: with no start date Yahoo returned only the last month (a cached file held 21 bars). Now from 2008.
- Tests: lab 98 green.
- First real paper decision (13 Nov 2026 close): target 100% NIFTYBEES (lookback 63), but the draft rules allowed 1 unit
  (₹287, 5.7% of ₹5,000). This is exactly the rule conflict above.

## Akhil's decision and what runs now (13 Nov 2026)
- Akhil chose **"Up to 100%"** (C66). `src/risk.py` `TRACK_A_LIMITS`: 100% max position, 20% protective stop, new buys pause
  at a 20% fall from peak (alert line in the summary), day/week/month caps off. Track B keeps the draft limits.
  In the 15-year test the worst fall was −15.7%, so neither the stop nor the pause would have fired.
- `.github/workflows/paper-trade.yml`: weekdays 16:15 IST, paper only, commits `07-trading/paper/track-A/`.
- Paper day 1 = 13 Nov 2026 close: BUY 17 NIFTYBEES at the next open (simulated), lookback 63 picked by the gate rule.

## World-check overlays and multi-asset test (13 Nov 2026, 19:30 IST)
Akhil asked for a strategy that also weighs pre-market, world news, the Fed, interest rates and elections. Five overlays, fixed before testing, gated as T0015–T0019 (cash 4.7%): none improved tsmom (₹3.47–3.74 vs ₹3.83; no smaller worst fall). Event study: election result days +17.7/+1.1/−0.7/−5.9%. Built `src/worldcheck.py` (alerts only) + `research/events.json` (two sources per date) and added it to the daily workflow. Multi-asset quick test (fixed 12-month rule, not yet gated, hindsight caveat): Nifty+gold+Nasdaq-100 in INR, Sharpe 1.16 vs 0.45 for Nifty only with the same fixed rule; held up in both halves. Full strategy: `07-trading/STRATEGY.md`.

## 5-minute intraday (13 Nov 2026, 19:34 IST request)
`src/intraday.py` + `paper/intraday/` + paper-trade.yml step. 6 configs on 60 sessions of NIFTYBEES 5-min: all lose after costs (best ORB 2×: +₹118 gross, ₹478 costs). Yahoo 5-min depth is 60 days (1-min: 8 days, 1-hour: back to Nov 2023), so our own 5-min history is stored daily. SEBI intraday study (PR 13/2024, 24 Jul 2024): 71% of individual intraday traders lost money in FY23; 80% for >500 trades/yr; loss-makers paid 57% of losses again as costs.

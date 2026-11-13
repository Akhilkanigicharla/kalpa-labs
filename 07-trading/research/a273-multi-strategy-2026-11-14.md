# A273: more trades, more companies, more timeframes, fear / inflation / rupee filters (14 Nov 2026)

Akhil: "push more for more profit, take more trades, multiple companies and time frames, consider news, sentiment,
inflation, GDP, currency, politics, fear and greed." Script `a273_multi_strategy.py`; results `a273_results.csv`,
`a273_train_all.csv`, `a273_filters_train.csv`.

## Method (no hindsight)
- ₹10,000 account simulated share by share: whole shares, every NSE delivery charge, ₹15.34 DP charge per stock sold,
  0.1% slippage each side, idle cash 4.7%/yr. Signal at close, trade next day's close.
- 78 settings tried, **chosen on 2011–2018 only**, then run untouched on **2019–2026**.
- Universe: today's 47 Nifty 50 stocks found on Yahoo (survivorship bias: this *flatters* the stock results),
  5 ETFs (NIFTYBEES, BANKBEES, JUNIORBEES, GOLDBEES, MON100). Monthly and weekly timeframes.
- Fear & greed: no free history for India, so India VIX (the market's fear gauge) is used: "fear_out" = cash when VIX
  is in its top 20% of the year; "fear_in" = buy extreme fear. Inflation: India CPI (FRED, lagged 2 months) above 6% →
  30% to gold. Rupee: USD/INR up >3% in 3 months → 30% to MON100.
- Not testable honestly: historical news sentiment (GDELT unreachable from our cloud; no free Indian archive), politics,
  GDP surprises (quarterly, revised). These stay as alerts in `src/worldcheck.py`, not trade rules.

## Result, 2019–2026 (never seen when choosing)
| Strategy | Return/yr | Worst fall | Worst year | Trades/yr | ₹10,000 became |
|---|---|---|---|---|---|
| **Current bot: Nifty trend + gold held** | **13.1%** | **−15.4%** | **−2.5%** | 18 | **₹26,332** |
| Top 5 Nifty 50 stocks by 12-month momentum (best of 32 stock settings) | 13.1% | −35.5% | −10.4% | 51 | ₹26,266 |
| Best ETF rotation (best of 24 ETF settings) | 6.9% | −39.7% | −20.5% | 10 | ₹16,861 |

- **Filters:** on the training years, every fear / inflation / rupee filter *lowered* returns. "fear_out" cut the stock
  strategy's worst fall from −24% to −20% but cut return from 25.8% to 22.0%; CPI and rupee tilts cost 1–5 points a year.
  None was picked, so none is in the test above.
- **More trades:** weekly instead of monthly tripled the trades (and charges) and lowered returns in every family.

## Verdict
The current bot keeps the job: same return as the best stock strategy with less than half the worst fall, and far
fewer charges. More trades, more companies and more filters did not add profit on data the choice never saw.
Kept for later: stock momentum as a *second* paper track if Akhil wants more trades for learning (A274).
Research only, own money only, not advice.

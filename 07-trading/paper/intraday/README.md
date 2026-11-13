# 5-minute intraday paper bot · PAPER ONLY

Akhil, 13 Nov 2026: "take trades on 5 mins time frame ... take profit and close".
Every weekday at 16:15 IST the bot replays that day's 5-minute NIFTYBEES bars one by one (no peeking ahead) for 3
strategies, ₹5,000 each: opening-range breakout, VWAP trend, RSI bounce. Each trade has a take-profit, a stop, and a forced
close at 15:15. Costs: brokerage, STT, exchange, SEBI, stamp, GST + slippage.

- `summary.txt`: today's trades + running totals. `trades.csv`: every trade.
- **Status: all 3 REJECTED** on Aug–Nov 2026 data (they lose after costs). Running on paper only, to build our own
  5-minute history and a real track record.
- Real-money intraday needs: a strategy that passes (≥30 trades, profit after costs, t-stat ≥ 2, profit in both halves of
  the data), then 90 paper days, an always-on server with a static IP and a broker live-data feed (GitHub Actions cannot
  trade in real time), and Akhil's "go". Not investment advice.

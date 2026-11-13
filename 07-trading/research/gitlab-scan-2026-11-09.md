# GitLab scan for trading repos (9 Nov 2026, Akhil gave GitLab access)

Searched the public GitLab API (projects sorted by stars) for: algorithmic trading, trading bot, backtest, kiteconnect, freqtrade, quant trading.

| Repo | Stars | Licence | Use for us |
|---|---|---|---|
| open-source-keir/financial-modelling/trading/barter-rs | 54 | MIT | Design reference only: event-driven engine where live and backtest share one code path, the same idea as our Live Guard. Rust, last updated 2022, so we don't run it. |
| algo2t/kiteext | 9 | check before use | Zerodha Kite helper. Small and last updated 2023. Prefer the official `kiteconnect` (MIT) from GitHub. |
| AndreyPopov/spot-trading-bot | 5 | check before use | Binance DCA bot. Binance is not FIU-registered for us, so crypto goes through an Indian FIU-registered exchange instead. |

Verdict: GitLab has no trading project stronger than our GitHub picks (vectorbt, backtesting.py, freqtrade, Kite/Upstox/Dhan official SDKs, TradingAgents). Every other hit has under 10 stars, is a fork, or hasn't been updated in years. Re-scan when Akhil names a specific GitLab repo.

# Deep scan v2: the best open-source trading code and research, tested for b7

Deep-Scan Agent 1 of 8, 2026-10-13. Follows `a8-trading.md` (read that first). This is engineering research only. It is not investment advice and does not recommend buying or selling any security. b7 trades on paper only.

**Status: complete (Steps 1–3), 13 Oct 2026.** Headline: three engines agree to within 0.005%, the gate wrongly passes only 1.3% of random walks, and on real Nifty 50 data 2007–2026 **no strategy beat simply holding the index after Indian costs**.

## How this list was made

- Star counts are read from GitHub topic pages sorted by stars (`/topics/quantitative-finance`, `/topics/backtesting`, `/topics/quant`, `/topics/stock-market`, `/topics/zerodha`, `/topics/nse`, `/topics/finrl`) and from repo pages on 2026-10-13. The GitHub search API and `curl` on topic pages were blocked (403), so these were read through a page fetcher. Treat them as ±5%.
- Licence and last-commit date come from our own blobless `git clone --depth 1` of each repo (the `LICENSE` file at HEAD and `git log -1`), not from the GitHub sidebar.
- "Fit for Indian legal venues" means: can it help with b7's year-1 scope, which is **NSE/BSE cash delivery and ETFs, daily or weekly bars, paper only** (see `PLAN.md` §2a)? Crypto-only and HFT/market-making tools score low because those venues are out of scope, not because the code is bad.

## Top repos by stars (trading-relevant only)

Verdicts: **ADOPT** = we may depend on it or copy from it (permissive licence, fits scope). **LEARN** = read it, run it privately, do not ship its code. **AVOID** = do not use.

| # | Repo | Stars | Last commit | Licence | What it is | Fit for Indian legal venues | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | 98.0k | 2026-10-03 | Apache-2.0 | Multi-agent LLM "trading firm" (analyst, researcher, trader, risk roles debate a decision) | Low. Single-ticker LLM opinions, no costs, no walk-forward. LLM backtests carry look-ahead bias because the model has seen the "future" in training. | LEARN (agent design only) |
| 2 | [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | 72.7k | 2026-10-12 | Apache-2.0 (LICENSE at HEAD) | Open data platform and SDK for analysts and AI agents | Medium. Good data plumbing, but Indian data comes via yfinance anyway. Heavy install. | LEARN |
| 3 | [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) | 64.7k | 2026-10-11 | MIT | LLM daily stock report bot (A-share/HK/US) on Actions cron | Low. Produces "analysis" text; publishing it would be advice. Its Actions-cron pattern is useful. | LEARN (cron pattern) |
| 4 | [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | 63.3k | 2026-10-02 | MIT | LLM agents styled as famous investors; README says educational, no live trades | Low. US data APIs, no cost model, no OOS test. | LEARN |
| 5 | [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | 55.0k | 2026-10-12 | **GPL-3.0** | The most-used crypto bot: backtest, hyperopt, dry-run, FreqAI | Low (crypto is out of scope). Its dry-run discipline and "lookahead-analysis" / "recursive-analysis" commands are the best bias checks in open source. | LEARN (ideas only, GPL) |
| 6 | [microsoft/qlib](https://github.com/microsoft/qlib) | 48.3k | 2026-10-08 | MIT | AI quant research platform: data layer, Alpha158 factors, model zoo, portfolio backtest | Medium. Permissive and rigorous, but built around China/US datasets and a custom binary data format; heavy for 1 h/day. | LEARN (factor ideas, MIT) |
| 7 | [ccxt/ccxt](https://github.com/ccxt/ccxt) | 43.9k | 2026-10-12 | MIT | Unified API for 100+ crypto exchanges | None (crypto out of scope; Indian crypto tax is 30% + 1% TDS). | AVOID for b7 |
| 8 | [vnpy/vnpy](https://github.com/vnpy/vnpy) | 43.1k | 2026-10-06 | MIT | Full Chinese quant platform (CTA engine, GUI, gateways) | Low. China futures gateways; docs in Chinese; heavy. | LEARN |
| 9 | [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | 35.0k | 2026-10-12 | MIT | Natural-language "personal trading agent" | Low. Same LLM caveats as #1. | LEARN |
| 10 | [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | 29.1k | 2026-10-13 | LGPL-3.0 | Rust core, Python API, same code for backtest and live | Low now. No Indian broker adapter; built for intraday. Usable unmodified as a library under LGPL. | LEARN |
| 11 | [mementum/backtrader](https://github.com/mementum/backtrader) | 22.6k | 2023-04-19 | **GPL-3.0** | Classic event-driven Python backtester | Low. Unmaintained 3.5 years, GPL. | AVOID |
| 12 | [QuantConnect/Lean](https://github.com/QuantConnect/Lean) | 21.2k | 2026-10-06 | Apache-2.0 | C# engine behind QuantConnect, Python strategies | Low. .NET/Docker, no Indian data or broker. | LEARN |
| 13 | [stefan-jansen/machine-learning-for-trading](https://github.com/stefan-jansen/machine-learning-for-trading) | 20.8k | 2026-10-13 | MIT | Book code (3rd ed.): data, alpha factors, ML, backtests | Medium as a textbook. | LEARN |
| 14 | [quantopian/zipline](https://github.com/quantopian/zipline) → [zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded) | 20k → 1.9k | 2020 → 2025-11-13 | Apache-2.0 | Event-driven engine with Pipeline API | Low-medium. Needs an XNSE calendar and custom bundles. | LEARN |
| 15 | [hummingbot/hummingbot](https://github.com/hummingbot/hummingbot) | 19.5k | 2026-09-22 | Apache-2.0 | Crypto market-making / HFT bots | None (crypto, HFT). | AVOID for b7 |
| 16 | [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | 16.6k | 2026-10-09 | MIT | Deep reinforcement learning for trading (PPO/A2C/SAC on stock envs) | Low. Published DRL results rarely survive costs and OOS; heavy GPU-ish stack. | LEARN |
| 17 | [TA-Lib/ta-lib-python](https://github.com/TA-Lib/ta-lib-python) | 12.2k | 2026-10-12 | BSD-2 | Wrapper for the TA-Lib C indicator library | Medium. Needs the C library; we only need 3–4 indicators, written in pandas. | LEARN |
| 18 | [OpenByteInc/QuantDinger](https://github.com/OpenByteInc/QuantDinger) | 11.4k | 2026-10-07 | Apache-2.0 | AI quant platform (backtest + live, SaaS features) | Low. Crypto/forex/US focus. | LEARN |
| 19 | [je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading) | 10.7k | 2024-04-14 | Apache-2.0 | Notebook collection: pairs, RSI, MACD, Bollinger, Dual Thrust, London breakout | Medium as examples; no costs, in-sample only. | LEARN |
| 20 | [huseinzol05/Stock-Prediction-Models](https://github.com/huseinzol05/Stock-Prediction-Models) | 9.5k | 2021-01-05 | Apache-2.0 | 30+ deep-learning price-prediction notebooks and "agents" | Low. Abandoned 2021, in-sample price forecasting, no costs. | AVOID |
| 21 | [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | 9.0k | 2026-10-09 | Apache-2.0 **+ Commons Clause** | Numba-vectorised backtests and huge parameter sweeps | High for private research. Cannot be in anything sold. | LEARN (internal only) |
| 22 | [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | 8.7k | 2026-08-05 | **AGPL-3.0** | Simple single-asset backtester with HTML plots | High for private research. | LEARN (internal only) |
| 23 | [jesse-ai/jesse](https://github.com/jesse-ai/jesse) | 8.4k | 2026-10-12 | MIT | Crypto bot framework | None (crypto). | AVOID for b7 |
| 24 | [ranaroussi/quantstats](https://github.com/ranaroussi/quantstats) | 7.5k | 2026-09-27 | Apache-2.0 | Tear-sheets and 50+ risk metrics | High. | **ADOPT** (tear-sheets) |
| 25 | [robertmartin8/PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt) | 6.1k | 2026-07-07 | MIT | Mean-variance, Black-Litterman, HRP | Medium (later, for ETF baskets). | LEARN → ADOPT later |
| 26 | [Superalgos/Superalgos](https://github.com/Superalgos/Superalgos) | 5.6k | 2026-05-07 | Apache-2.0 | Visual crypto bot designer | None. | AVOID for b7 |
| 27 | [dcajasn/Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | 4.4k | 2026-10-04 | BSD-3 | Portfolio optimisation with 20+ risk measures | Medium (later). | LEARN → ADOPT later |
| 28 | [nkaz001/hftbacktest](https://github.com/nkaz001/hftbacktest) | 4.3k | 2025-12-23 | MIT | Tick/queue-position HFT backtester (Rust) | None (HFT not allowed or affordable for retail under 2026 algo rules). | AVOID for b7 |
| 29 | [AI4Finance-Foundation/FinRL-Trading](https://github.com/AI4Finance-Foundation/FinRL-Trading) | 3.7k | 2026-09-18 | Apache-2.0 | Modular infra around FinRL | Low. | LEARN |
| 30 | [edtechre/pybroker](https://github.com/edtechre/pybroker) | 3.5k | 2026-08-27 | Apache-2.0 **+ Commons Clause** | ML-friendly backtester with built-in walk-forward and bootstrap metrics | High for private research; Commons Clause blocks selling. | LEARN (internal only) |
| 31 | [pmorissette/bt](https://github.com/pmorissette/bt) | 3.0k | 2026-10-10 | MIT | Composable portfolio "algo stack" backtester | High (daily/weekly allocation). | **ADOPT** |
| 32 | [marketcalls/openalgo](https://github.com/marketcalls/openalgo) | ~2.7k | 2026-10-12 | **AGPL-3.0** (server) | Self-hosted Indian multi-broker bridge with sandbox "Analyzer" mode | High at go-live, as a separate unmodified service. | LEARN (separate service) |
| 33 | [barter-rs/barter-rs](https://github.com/barter-rs/barter-rs) | 2.2k | 2026-08-20 | MIT | Rust event-driven live/backtest framework | Low. | LEARN |
| 34 | [Lumiwealth/lumibot](https://github.com/Lumiwealth/lumibot) | 1.9k | 2026-10-10 | **GPL-3.0** | Backtest + live trading "agents" (US brokers) | Low. | AVOID copying |
| 35 | [zerodha/pykiteconnect](https://github.com/zerodha/pykiteconnect) | 1.3k | 2026-09-15 | MIT | Official Zerodha Kite Connect SDK | High at go-live only. | ADOPT (later) |

Also checked: [freqtrade/freqtrade-strategies](https://github.com/freqtrade/freqtrade-strategies) (GPL-3.0, 2026-09-08: crypto strategy zoo, most are in-sample curve fits; do not copy), [hudson-and-thames/mlfinlab](https://github.com/hudson-and-thames/mlfinlab) (public repo frozen 2021-12-01, now a **proprietary licence**: do not use), [bukosabino/ta](https://github.com/bukosabino/ta) (MIT, pure pandas indicators), [AI4Finance FinRL-Trading]. Curated lists used for discovery: [wilsonfreitas/awesome-quant](https://github.com/wilsonfreitas/awesome-quant) (29.4k), [paperswithbacktest/awesome-systematic-trading](https://github.com/paperswithbacktest/awesome-systematic-trading) (14.1k, formerly wangzhe3224's list), [firmai/financial-machine-learning](https://github.com/firmai/financial-machine-learning) (8.8k), [georgezouq/awesome-ai-in-finance](https://github.com/georgezouq/awesome-ai-in-finance) (6.7k).

Indian-specific repos (from `/topics/zerodha` and `/topics/nse`) are all small (under 1k stars): [pranjal-joshi/Screeni-py](https://github.com/pranjal-joshi/Screeni-py) (697), [pkjmesra/PKScreener](https://github.com/pkjmesra/PKScreener) (377), [deshwalmahesh/NSE-Stock-Scanner](https://github.com/deshwalmahesh/NSE-Stock-Scanner) (337), [BennyThadikaran/eod2](https://github.com/BennyThadikaran/eod2) (165, NSE EOD bhavcopy downloader), [NayakwadiS/mftool](https://github.com/NayakwadiS/mftool) (248, AMFI mutual fund NAVs). None changes the a8 recommendation. **eod2** is worth a look as a bhavcopy-based data source; **mftool** gives free AMFI NAVs, which are public data and a clean benchmark for "beat the index fund".

### What the star ranking says

1. **The 2025–26 star leaders are LLM agent projects** (TradingAgents 98k, daily_stock_analysis 65k, ai-hedge-fund 63k, Vibe-Trading 35k). None of them reports a walk-forward, cost-aware result. LLM backtests over past dates are contaminated: the model has read news from after those dates (Lopez-Lira, Tang & Zhu 2025, "The Memorization Problem: Can We Trust LLMs' Economic Forecasts?", [arXiv:2504.14765](https://arxiv.org/abs/2504.14765)). They are also close to "advice" products, which b7 cannot sell. Verdict: interesting agent design, no evidence of edge.
2. **The best engineering is in crypto tools** (freqtrade, hummingbot, ccxt, jesse), which are out of b7's legal scope.
3. **The permissive, maintained, daily-bar stack is small**: bt (MIT), quantstats (Apache-2.0), PyPortfolioOpt (MIT), Riskfolio-Lib (BSD-3), qlib (MIT, heavy). a8's ADOPT list still holds.

## Strategy families with the strongest published evidence

Ranked by strength of out-of-sample, multi-market, multi-decade evidence, then by fit for daily delivery trading in India after costs. Delivery STT is 0.1% on **each** side, so anything with high turnover is ruled out before it starts.

| Rank | Family | Key evidence | India evidence | Turnover / cost fit | Repos that implement it |
|---|---|---|---|---|---|
| 1 | **Time-series momentum / trend following** (hold when the asset's own 12-month return or a long moving-average filter is positive, else cash) | Moskowitz, Ooi & Pedersen 2012, "Time Series Momentum", *JFE* 104(2) ([doi](https://doi.org/10.1016/j.jfineco.2011.11.003)); Hurst, Ooi & Pedersen 2017, "A Century of Evidence on Trend-Following Investing" ([AQR](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing)); Faber 2007, "A Quantitative Approach to Tactical Asset Allocation" ([SSRN 962461](https://ssrn.com/abstract=962461)) | Indian index futures and equity indices included in several cross-country TSMOM studies; effect strongest at index/ETF level | Low (a few switches a year) | bt, vectorbt, backtesting.py, Lean, je-suis-tm; trivial in pandas |
| 2 | **Volatility targeting / volatility-managed exposure** (scale position by target vol ÷ recent realised vol) | Moreira & Muir 2017, "Volatility-Managed Portfolios", *JF* 72(4) ([doi](https://doi.org/10.1111/jofi.12513)); Harvey et al. 2018, "The Impact of Volatility Targeting", *JPM* ([SSRN 3175538](https://ssrn.com/abstract=3175538)): it reliably **cuts drawdowns and tail risk**, Sharpe gains are smaller and mixed (Cederburg et al. 2020, *JFE*, find OOS gains often vanish) | Same mechanism; no India-specific contrary evidence found | Low-medium if rebalanced weekly with a no-trade band | bt (`WeighTarget`), Riskfolio, PyPortfolioOpt; trivial in pandas |
| 3 | **Cross-sectional momentum** (rank stocks by 12-1 month return, hold the top slice, rebalance monthly) | Jegadeesh & Titman 1993, *JF* 48(1) ([doi](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x)); Asness, Moskowitz & Pedersen 2013, "Value and Momentum Everywhere", *JF* 68(3) ([doi](https://doi.org/10.1111/jofi.12021)) | Agarwalla, Jacob & Varma 2014, IIM-A four-factor data library for India finds a positive momentum (WML) premium ([IIMA WP 2013-12-08](https://faculty.iima.ac.in/~iffm/Indian-Fama-French-Factor/)); NSE runs a rules-based Nifty200 Momentum 30 index | Medium (monthly rebalance; ~100–200% turnover a year). Needs a survivorship-free universe, which free data does not give. | qlib (Alpha158), bt, ML4T book |
| 4 | Low-volatility / betting-against-beta | Frazzini & Pedersen 2014, "Betting Against Beta", *JFE* 111(1) ([doi](https://doi.org/10.1016/j.jfineco.2013.10.005)); Blitz & van Vliet 2007 | NSE Nifty Low Volatility 50 index exists; IIM-A data shows the anomaly | Low-medium | PyPortfolioOpt, Riskfolio |
| 5 | Pairs trading / mean reversion | Gatev, Goetzmann & Rouwenhorst 2006, *RFS* 19(3) ([doi](https://doi.org/10.1093/rfs/hhj020)); Do & Faff 2010, *FAJ*: **profits decayed sharply after 2000** | Needs shorting, which retail delivery cannot do overnight | High turnover, needs a short leg: **not feasible** in year 1 | je-suis-tm, Stock-Prediction-Models |
| 6 | Short-term reversal, RSI/Bollinger "oscillator" rules, candlestick patterns | Weak and cost-sensitive; most "indicator" rules fail after data-snooping corrections (Sullivan, Timmermann & White 1999, *JF* 54(5)) | — | High turnover, killed by 0.2% round-trip STT | freqtrade-strategies, je-suis-tm |
| 7 | Deep RL / deep-learning price prediction / LLM agents | Few results survive realistic costs and true OOS; LLM look-ahead bias (arXiv:2504.14765) | — | Usually high turnover | FinRL, Stock-Prediction-Models, TradingAgents, ai-hedge-fund |

**Overfitting research that the gate is built on** (more important than any strategy):

- Bailey & López de Prado 2012, "The Sharpe Ratio Efficient Frontier", *J. of Risk* 15(2) ([SSRN 1821643](https://ssrn.com/abstract=1821643)): Probabilistic Sharpe Ratio (PSR).
- Bailey & López de Prado 2014, "The Deflated Sharpe Ratio", *JPM* 40(5) ([SSRN 2460551](https://ssrn.com/abstract=2460551)): corrects PSR for the number of trials, non-normal returns and short samples. **This is why the trials registry matters: the more configurations you try, the higher the bar.**
- Bailey, Borwein, López de Prado & Zhu 2017, "The Probability of Backtest Overfitting", *J. Computational Finance* ([SSRN 2326253](https://ssrn.com/abstract=2326253)): PBO via CSCV.
- Harvey, Liu & Zhu 2016, "…and the Cross-Section of Expected Returns", *RFS* 29(1): a new factor needs t > 3.0, not 2.0.

**Choice for `src/strategies/`:** (1) time-series momentum / long-MA trend filter, (2) volatility targeting as an overlay, (3) the a8 SMA crossover kept as the **negative control** the gate must reject. Cross-sectional momentum is left for later because free NSE data has survivorship bias (delisted stocks missing), which inflates momentum results.

## Licence warnings

| Licence | Repos | Rule for Kalpa Labs |
|---|---|---|
| **AGPL-3.0** | backtesting.py, OpenAlgo server, esvhd/pypbo | Never copy code. Private research only. OpenAlgo only as a separate, unmodified service. |
| **GPL-3.0** | freqtrade, freqtrade-strategies, backtrader, lumibot, nsepython | Never copy into anything sold or distributed. Ideas only. |
| **Apache-2.0 + Commons Clause** (source-available, not open source) | vectorbt, pybroker | May not "sell" anything whose value comes substantially from them. Private research only. |
| **LGPL-3.0** | nautilus_trader | Use unmodified as a library only. |
| **Proprietary** | mlfinlab (post-2021) | Do not use. |
| Changed licence | OpenBB: LICENSE at HEAD (2026-10-12) now says Apache-2.0 for all files | Re-check before any reuse; earlier versions were AGPL. |
| Permissive (OK to copy with attribution in `07-trading/NOTICE`) | bt, ccxt, qlib, FinRL, TradingAgents, ai-hedge-fund, quantstats, PyPortfolioOpt, Riskfolio-Lib (BSD-3), TA-Lib wrapper (BSD-2), zipline-reloaded, Lean, ta, pykiteconnect | Keep the copyright line and licence text in NOTICE. |

## Step 2: engine bake-off (real runs, 13 Oct 2026)

Method: published packages installed from PyPI into a throwaway venv (`bt 1.4.1`, `quantstats 0.0.86`, `backtesting 0.6.6`, `pandas 3.0.6`, `numpy 2.5.4`; a second venv with `pandas 2.3.3`). No cloned repo code was executed. Our own small scripts compared the engines on the **same synthetic series** (10 years, seed 7) and the same a8 SMA 10/50 crossover, costs off for the comparison.

| Engine | Licence | Final equity (gross) | Gap vs ours | Time | Verdict |
|---|---|---|---|---|---|
| **Our `src/backtest.py`** (pandas, vectorised) | ours (MIT-able) | 0.708258 | — | **2–3 ms** | ADOPT (core) |
| bt 1.4.1 | MIT | 0.708266 | 1.2e-5 (whole-share rounding) | 350–435 ms | ADOPT (cross-check, portfolios later) |
| backtesting.py 0.6.6 | **AGPL-3.0** | 0.708288 | 4.2e-5 | 27–30 ms | private cross-check only, never imported in `src/` |

| Metric | Ours (`src/metrics.py`, from the papers) | quantstats 0.0.86 |
|---|---|---|
| Sharpe (252) | -0.279929 | -0.279929 |
| PSR | 0.188215 | 0.188215 |
| Max drawdown | -36.4456% | -36.4456% |
| Inverse-normal (our `_phi_inv` vs scipy) | max error 9.3e-15 | — |

Findings from the runs:
1. **Three independent engines agree to within 0.005%**, so our 60-line engine is trustworthy and 150× faster than bt, which matters for walk-forward × grid × stress runs on free CI minutes.
2. **bt 1.4.1 bug found:** with `initial_capital=1e9` and `integer_positions=False` it crashes ("Potentially infinite loop detected") on both pandas 2 and 3; the default capital works. Use bt with default settings only.
3. **Costs are the story:** the same SMA rule went from 0.708 gross to **0.655 net** over 10 years: 33 round trips × ~0.22% (0.1% STT each side + stamp + exchange + DP) ate 7.5% of capital.
4. **Data validator caught two real problems in free Yahoo data:** NIFTYBEES has an **unadjusted 1:10 split on 19 Dec 2019** even with `auto_adjust=True` (two >40% "jumps"), and `^NSEI` has a 6-day hole (1 → 7 Oct 2014), which turned out to be real holidays, so the gap limit was set to 7 days. Without validation the split alone would fake a 90% crash.
5. **PBO bias found in our own first draft:** with 3 configs, the median out-of-sample rank gives logit 0, so pure noise scores PBO ≈ 0.67 instead of 0.5. Every grid now has an even number (≥ 4) of configs, and a test enforces it.

### Gate calibration (300 synthetic runs)

30 random seeds × 5 strategies × 2 worlds, 20 years of daily bars each:

| World | What it is | Passed the gate | Meaning |
|---|---|---|---|
| Random walk (8% drift, 18% vol, no edge) | Any pass is a false positive | **2 / 150 (1.3%)** | The gate almost never blesses luck |
| Planted trend (regimes of ~1 year, ±35% drift) | A real edge exists | 62 / 150 (41%) | Strict: it misses many real edges, by design |

Which criteria stopped the random walks (out of 150): beat buy-and-hold 144, survive 2× costs + 1-bar delay 145, DSR 134, PSR 113, PBO 72, ≥ 30 trades 0. The cost/delay stress and the buy-and-hold comparison do most of the work; PSR alone would have let 37 lucky series through.

### Real data dry run: Nifty 50 index, 17 Sep 2007 – 31 Aug 2026 (yfinance, 4,650 bars)

Scratch registry (not logged in `trials.csv`, because Q7.7 hypotheses are the CEO's call). Lab result, not advice; the index is not a recommendation.

| Strategy | OOS Sharpe | Buy-and-hold Sharpe | PSR | DSR | PBO | Round trips | Stress Sharpe | Verdict |
|---|---|---|---|---|---|---|---|---|
| tsmom (12-month momentum) | 0.62 | 0.62 | 0.99 | 0.98 | 0.10 | 57 | 0.27 | rejected (ties B&H; dies under stress) |
| ma_filter | 0.40 | 0.62 | 0.94 | 0.86 | 0.87 | 92 | 0.19 | rejected |
| tsmom_vt | 0.39 | 0.62 | 0.93 | 0.91 | 0.97 | 118 | 0.22 | rejected |
| ma_filter_vt | 0.49 | 0.62 | 0.97 | 0.92 | 0.18 | 113 | 0.28 | rejected |
| sma_cross (a8 control) | 0.66 | 0.62 | 0.99 | 0.96 | 0.86 | 44 | 0.39 | rejected (PBO 0.86 = lucky pick) |

**Verdict: on 19 years of the Nifty 50, nothing beat holding the index after Indian delivery costs.** Time-series momentum came closest (lower drawdown, same Sharpe) but collapsed at 2× costs plus one day of delay. This matches PLAN.md's honest benchmark: the index fund is the bar, and it is hard to beat. b7 keeps its value as a lab and content source ("why our backtest lied"), not as a money machine.

## Step 3: what was built

| Item | Files | Check | Result |
|---|---|---|---|
| A23 (Q7.1) | `.gitignore` (`07-trading/data/`, `reports/`), `requirements.txt` (pinned to the versions above), `NOTICE`, README licence note | `git check-ignore 07-trading/data/x.parquet` | passes |
| A23 (Q7.2) | `src/data.py`: yfinance `.NS`, optional fallback, Parquet cache, validator (NaN, dupes, ≤ 0, high<low, gaps > 7 days, > 40% jumps), synthetic generator | tests on synthetic data only | pass |
| A23 (Q7.3) | `src/costs.py`: delivery, intraday, futures, options; every rate has source URL + check date; stale after 90 days | contract-note example ₹1L buy + ₹1L sell = **₹237.82** (STT 200, NSE 6.14, SEBI 0.20, stamp 15, GST 1.14, DP 15.34) | within ₹1 |
| A24 (Q7.4) | `src/strategies.py`, `src/backtest.py`, `src/metrics.py` (PSR, DSR, PBO-CSCV from the papers), `src/gate.py` (6 criteria, thresholds "pending CEO approval") | a8 SMA rejected on 3 random walks; planted trend passes | pass |
| A24 (Q7.5) | `src/trials.py` + `research/trials.csv`: gate refuses unlogged or mismatched trials, verdicts can't be overwritten, DSR counts every config ever logged per hypothesis | "running without a log entry fails" | pass |

`cd 07-trading && python -m pytest -q` → **24 passed** (4.4 s).

**Proposed for the CEO (thresholds pending approval):** add criterion 6, Deflated Sharpe ≥ 0.95 using all configs ever tried for a hypothesis. It stopped 134/150 random walks and is the direct defence against "try 50 things, publish the best".

# A8: Open-source tools for a legal Indian backtesting and paper-trading lab

Research agent 8 of 8, 2026-10-13. Scope (world b7 Trading): backtesting engines, Indian market data, broker SDKs, OpenAlgo, paper-trading and forward-test harnesses, risk metrics, and walk-forward or overfitting checks. All of it has to fit the 90-days-of-paper-trading-first rule and run free in GitHub Actions or Colab. This is an engineering evaluation only. Nothing here is investment advice or a recommendation to buy or sell anything.

## Summary

Most of the popular engines are **not** permissively licensed, and `07-trading/README.md` currently names two of them:

- **backtesting.py is AGPL-3.0.**
- **vectorbt is Apache-2.0 + Commons Clause.** You may not "Sell" a product or service whose value comes substantially from vectorbt.
- **backtrader is GPL-3.0** and its last commit was in April 2023.
- **nsepython is GPL-3.0.**

All four are fine for **internal** research, where nothing is distributed or sold. None of their code can go into anything Kalpa Labs sells, such as a signals product or a "strategy kit" in b3.

The permissive core that works is:

- **bt** (MIT) or plain pandas/numpy for the backtests we keep.
- **quantstats** (Apache-2.0) for tear-sheets.
- **yfinance** (Apache-2.0) for free NSE daily bars (`.NS`). It is unofficial Yahoo data and fine for research only.
- **pykiteconnect, dhanhq, upstox and fyers SDKs** (all MIT) when a broker is eventually connected.

**OpenAlgo** has the most complete self-hosted multi-broker bridge, with a ₹1 crore "Analyzer"/sandbox paper mode. Its server is AGPL-3.0 and its Python client is MIT, so run it as a separate service only.

There are three hard regulatory facts:

- **SEBI's retail algo framework has been live since 1 April 2026.** Every API order needs a registered app or API key mapped to a whitelisted **static IP**, it carries an **Algo ID**, a 2FA login is needed every trading day, and orders are capped at **≤10 orders per second** before an algo has to be registered. As a result, **GitHub Actions runners (dynamic, shared, often non-Indian IPs) can never place live orders.** Actions is fine for backtests and simulated paper trading only.
- **NSE data is NSE's property.** Republishing or redistributing it (for example as a CSV in a public repo, on a website, or in a paid kit) needs an NSE Data & Analytics licence. Keep raw data out of git, cache it as Actions artifacts or in Colab, and publish derived metrics only.
- **Zerodha's free "Personal" API has no historical data.** Kite Connect costs ₹500/month and Dhan's Data API costs ₹499/month, so the zero-budget phase relies on yfinance and jugaad-data.

The "Tried it" section has the main finding. Optimising the same SMA crossover in-sample gave Sharpe **1.21**. Walk-forward out-of-sample gave **0.15**, against **0.59** for buy-and-hold over the same period. The lab's first deliverable should therefore be the walk-forward and overfitting gate, not a strategy.

## Shortlist

Stars are approximate because the GitHub API is blocked. Last commit and licence come from a shallow `git clone` (LICENSE file plus HEAD) and from PyPI metadata where a repo has no LICENSE file.

| Repo | What | Stars ~ | Last commit | Licence | Fit 1–5 | Verdict | Why |
|---|---|---|---|---|---|---|---|
| [ranaroussi/quantstats](https://github.com/ranaroussi/quantstats) | Tear-sheets and 50+ risk metrics (Sharpe, PSR, Sortino, drawdowns) from a returns series | 6k | 2026-09-27 | Apache-2.0 | 5 | **ADOPT** | Engine-agnostic, so every engine reports through the same metric definitions. Built a 1.3 MB HTML tear-sheet in 3.1 s. Includes Probabilistic Sharpe. Pass `periods_per_year=252`. |
| [pmorissette/bt](https://github.com/pmorissette/bt) | Composable "algo stack" portfolio backtester (rebalancing, weighting) | 2.5k | 2026-10-10 | MIT | 4 | **ADOPT** | The only actively maintained engine with a permissive licence that installs as a light pip package (installed cleanly with pandas 3). Suits daily/weekly allocation strategies, which are the realistic kind for a 1-hour/day operator. Does not suit intraday tick simulation. |
| [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | Yahoo Finance downloader (`RELIANCE.NS`, `^NSEI`) | 20k | 2026-09-30 | Apache-2.0 (code) | 4 | **ADOPT (research only)** | Fetched 2,901 adjusted daily bars (2015 to 2026-09) in 2.0 s from this sandbox. The code is Apache, but the **data falls under Yahoo's terms (personal use)**. It is unofficial and can break, so never redistribute it and cross-check it against bhavcopy. |
| [zerodha/pykiteconnect](https://github.com/zerodha/pykiteconnect) | Official Zerodha Kite Connect SDK | 1.2k | 2026-09-15 | MIT | 4 | **ADOPT (at go-live)** | Clean MIT SDK. Personal API is free (orders only). Historical and live data need Connect at ₹500/month. Orders must come from the registered static IP. |
| [dhan-oss/DhanHQ-py](https://github.com/dhan-oss/DhanHQ-py) | Official Dhan SDK (orders, historical, websocket) | 0.2k | 2026-10-08 | MIT | 4 | **ADOPT (alt broker)** | Trading API is free. Data API is ₹499/month since the free-with-trades promo ended. Dhan also has a broker-side sandbox for safe order-path tests. |
| [marketcalls/openalgo](https://github.com/marketcalls/openalgo) | Self-hosted multi-broker bridge (36 broker plugins), Analyzer/sandbox paper mode, TradingView/Amibroker webhooks, MCP | 2k? | 2026-10-12 | **AGPL-3.0** server; `openalgo` PyPI client MIT | 4 | **LEARN / separate service** | The best ready-made paper-then-live path. Its Analyzer mode gives ₹1 Cr sandbox capital with the same API as live, and the project tracks the SEBI rules (static IP, Algo ID, 10 OPS). It needs a broker login plus a host with a static Indian IP (home PC or an Indian VPS, not Actions). Run it unmodified as a service and talk to it through the MIT client. Never copy server code. |
| [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | Numba-vectorised backtesting and huge parameter sweeps | 6.5k | 2026-10-09 | Apache-2.0 **+ Commons Clause** | 4 | **LEARN (internal only)** | Ran 4,465 SMA combos in 23.7 s (after a 16 s Numba JIT warm-up) and reproduced backtesting.py's result exactly. Very good for internal research sweeps. The Commons Clause bars selling anything whose value comes from it, so keep it out of b3 kits and any paid product. |
| [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | Simple event-style single-asset backtester with HTML plots | 7.5k | 2026-08-05 | **AGPL-3.0** | 3 | **LEARN (internal only)** | Easiest API, 48 ms per run. AGPL is acceptable for private Colab research but not for anything distributed or served to customers. The README's current mention is fine only on those terms. |
| [jugaad-py/jugaad-data](https://github.com/jugaad-py/jugaad-data) | NSE bhavcopy, stock, index and derivatives history from NSE's own site | 0.5k | 2026-10-06 | "YOLO licence" (unusual, permissive-sounding) | 3 | **LEARN (flag licence + data terms)** | Fetched 44 RELIANCE EQ rows (Jan–Feb 2024) from this sandbox, even though `curl nseindia.com` returned 403. Free and official-source data, but it is scraping NSE's site, and both the YOLO licence and NSE's data policy make it **personal research only**. Nothing that uses it should be redistributed. |
| [stefan-jansen/empyrical-reloaded](https://github.com/stefan-jansen/empyrical-reloaded) | Pure risk-metric functions (Sharpe, Sortino, alpha/beta, tail ratio) | 0.1k | 2025-07-29 | Apache-2.0 | 3 | LEARN | Small and dependency-light. Useful for unit-testing our own metric code. quantstats already covers it. |
| [stefan-jansen/zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded) | Quantopian-style event engine with pipeline and calendars | 1.5k | 2025-11-13 | Apache-2.0 | 2 | LEARN | Permissive and rigorous, but needs custom data "bundles" and an XNSE calendar. Too heavy for 1 hour a day, and commits slowed in 2025. |
| [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | Rust/Python production-grade event-driven engine, same code for backtest and live | 15k+ | 2026-10-12 | LGPL-3.0 | 2 | LEARN | Best-in-class backtest/live parity and fine as a library under LGPL, but it has no Indian broker adapters and a steep learning curve. Overkill now, and worth revisiting only for intraday F&O. |
| [QuantConnect/Lean](https://github.com/QuantConnect/Lean) | C# engine (Python strategies) behind QuantConnect | 16k | 2026-10-06 | Apache-2.0 | 2 | LEARN | Permissive and complete, but needs .NET/Docker and has no Indian broker or data. Its walk-forward and "insight" design is worth reading. |
| [mementum/backtrader](https://github.com/mementum/backtrader) | Classic event-driven engine | 20k | 2023-04-19 | **GPL-3.0** | 1 | **AVOID** | Unmaintained for 3.5 years, GPL-3, and has known pandas-2/3 friction. Old Indian blog tutorials use it, but they shouldn't be followed. |
| [aeron7/nsepython](https://github.com/aeron7/nsepython) | NSE website and API wrappers (option chain, bhavcopy, FII/DII) | 0.3k | 2026-10-08 | **GPL-3.0** | 2 | AVOID copying | Handy in Colab for ad-hoc lookups, but GPL code plus NSE-site scraping means it must never be bundled into anything sold. |
| Angel One [smartapi-python](https://github.com/angel-one/smartapi-python), [upstox/upstox-python](https://github.com/upstox/upstox-python), Fyers [fyers-apiv3](https://pypi.org/project/fyers-apiv3/) | Broker SDKs | 0.1–0.3k | 2025-05 / 2026-09 / PyPI 3.1.19 | **None in repo** / MIT / MIT (PyPI) | 3 | LEARN | Equivalent alternatives to Kite and Dhan. Angel's SDK ships with **no licence file and an empty PyPI licence field**, so treat it as unclear and call it through OpenAlgo instead. Fyers already enforces the new rules (MPP market orders, daily 2FA, 10 OPS, static IP). |

Other candidates screened:

- **[esvhd/pypbo](https://github.com/esvhd/pypbo)**: Probability of Backtest Overfitting/CSCV. AGPL-3.0, so learn from the paper (Bailey et al.) and write about 40 lines ourselves.
- **[microsoft/qlib](https://github.com/microsoft/qlib)**: MIT, ML research platform. Too heavy.
- **[jesse-ai/jesse](https://github.com/jesse-ai/jesse)**: MIT, crypto only, which is outside our legal venue scope.
- **[kieran-mackle/AutoTrader](https://github.com/kieran-mackle/AutoTrader)**: GPL-3, quiet.
- **[dcajasn/Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib)**: BSD-3, portfolio optimisation, a later need.
- **quantopian/pyfolio**: dead since 2020. pyfolio-reloaded (Apache-2.0) is quantstats-like.
- **TA-Lib/ta-lib-python** (BSD-2, needs the C library) and **bukosabino/ta** (MIT, pure pandas) for indicators.
- **twopirllc/pandas-ta**: the clone failed because the repo was moved or made private in 2025, so skip it.

## Tried it

All runs used one fresh venv in scratch (Python 3.13, `pip install backtesting vectorbt quantstats yfinance jugaad-data bt`). The install took **2 min** and the venv is **938 MB**, mostly numba, llvmlite, scipy, plotly and matplotlib, so this belongs in Colab or Actions, not on the low-spec PC. The data was **real**: RELIANCE.NS daily, 2015-01-01 to 2026-09-30, 2,901 adjusted bars from yfinance. No credentials or broker accounts were used.

1. **Same strategy, two engines**
   - Setup: a long-only SMA 10/30 crossover. Signal on the close, fill at the **next open**. Fee 0.12% per side as a rough proxy for STT, stamp duty and exchange charges on delivery.
   - **backtesting.py 0.6.6:** +236.7%, 53 trades, max drawdown −31.9%, Sharpe 0.53, **48 ms**. A 38-combo `optimize()` grid took **2.0 s**.
   - **vectorbt 1.1.2:** **identical** results (+236.7%, 53 trades, max drawdown −31.9%), but it reported Sharpe **0.79**. The difference comes from metric definitions: vectorbt with `freq="1D"` annualises on 365 days, while backtesting.py uses geometric returns. The first call took **16.3 s** because of the Numba JIT. After that, a **4,465-combo** sweep (all fast/slow pairs from 5 to 99) took **23.7 s**.
   - Lesson: the engines agree on trades, but a Sharpe number means nothing unless one library computes it with one annualisation (252). Use quantstats for that.
2. **Walk-forward check (vectorbt plus our own loop, 49.6 s)**
   - Setup: rolling 3-year in-sample optimisation over 190 SMA pairs, then a 1-year out-of-sample test, for every year from 2018 to 2026, with indicator warm-up handled correctly.
   - The chosen parameters jumped around: (50,140), (25,60), (5,40), (15,40) and others.
   - **Mean in-sample Sharpe was 1.21 and stitched out-of-sample Sharpe was 0.15**, against **0.59** for buy-and-hold over the same 2018–2026 window.
   - Out-of-sample Sharpe for individual years ranged from −2.33 to +2.15.
   - A rerun with a coarser 16-pair grid gave in-sample 0.86 and out-of-sample 0.04.
   - This is the overfitting signature the lab must catch before any paper trading starts.
3. **quantstats 0.0.86 tear-sheet**
   - `qs.reports.html(oos, benchmark=buy_and_hold, periods_per_year=252)` wrote a 1.27 MB self-contained HTML file in **3.1 s**. It logs harmless "Arial not found" warnings on Linux.
   - Out-of-sample strategy: cumulative return −10% against +193% for the benchmark, CAGR −1%, time in market 64%, max drawdown −46% (2020), **Probabilistic Sharpe Ratio 0.55** (the benchmark's was 0.96).
4. **Data access**
   - yfinance `.NS` worked.
   - **jugaad-data** `stock_df("RELIANCE", 2024-01-01..2024-03-01, "EQ")` returned 44 rows, even though a plain `curl https://www.nseindia.com` returned **403**.
   - The NSE-direct path is therefore fragile, so build in retries and a yfinance fallback.

The clones, venv, data and tear-sheet were all deleted afterwards.

## Concrete changes for Kalpa Labs

- **`07-trading/README.md`**:
  - Add a licence note: *"backtesting.py (AGPL-3) and vectorbt (Commons Clause) are used for internal research only; nothing built on them is sold or distributed."*
  - Name **bt (MIT) + quantstats (Apache-2.0)** as the default stack for any code that might later ship.
- **New `07-trading/src/data.py`**:
  - `get_daily(symbol)` tries yfinance `.NS` first and falls back to jugaad-data `stock_df`.
  - Cache Parquet under `07-trading/data/`, and add `07-trading/data/` to `.gitignore`. **Never commit NSE or Yahoo price data**, because of NSE's data policy and Yahoo's terms.
  - Validate the data: no gaps on NSE trading days, no non-positive prices, and splits adjusted.
- **New `07-trading/src/costs.py`**: one function with Indian cost assumptions (STT, exchange transaction charge, SEBI fee, stamp duty, GST on brokerage, DP charge), kept separate for delivery, intraday and F&O. Every engine run imports it, so no backtest runs at zero cost.
- **New `07-trading/src/gate.py`**: the go/no-go gate for any strategy. A strategy only enters paper trading if it passes:
  - an anchored or rolling **walk-forward** test with out-of-sample Sharpe above 0.5 and above buy-and-hold over the same window;
  - quantstats **Probabilistic Sharpe** of at least 0.95;
  - an out-of-sample trade count of at least 30;
  - a **CSCV/PBO** score below 0.5. Write this ourselves (about 40 lines, from Bailey et al.) rather than copying AGPL pypbo.
- **New `07-trading/src/paper.py` plus `.github/workflows/paper-trade.yml`** (next to the existing `.github/workflows/leadfinder.yml`):
  - A cron job on weekdays at about 16:15 IST (`45 10 * * 1-5` UTC) pulls the end-of-day bars, computes signals, and records **simulated** next-open fills.
  - It appends them to `07-trading/paper/ledger.csv`. That file holds our own hypothetical trades and P&L only, never raw price data.
  - It renders a quantstats HTML file as a workflow artifact.
  - The 90-day clock starts on the first ledger row.
  - The job makes **no broker calls**, so the static-IP rule doesn't apply.
- **New `.github/workflows/backtest.yml`**: on push to `07-trading/src/**`, run the gate on a fixed symbol list and upload the tear-sheets. Data comes from the Actions cache, never from git.
- **Go-live step (after 90 days, not before)**:
  - Run OpenAlgo unmodified (AGPL, separate service) on a host with a **static Indian IP**, in Analyzer mode first.
  - Strategy code talks to it through the MIT `openalgo` client, or calls `kiteconnect`/`dhanhq` directly.
  - Keep orders far below 10 orders per second, re-login with 2FA every day, and use limit or MPP orders.
  - Budget item: Kite Connect at ₹500/month or the Dhan Data API at ₹499/month, if real-time data is needed.

## Risks

- **Regulatory:**
  - The SEBI and NSE retail algo rules (static IP, Algo ID, daily 2FA, the 10 OPS registration threshold, and empanelment for third-party platforms) are still being clarified broker by broker.
  - Running live orders from GitHub Actions, Colab, or any shared or dynamic IP is non-compliant.
  - Selling signals or strategy advice to others needs SEBI RA/IA registration. Keep b7 strictly proprietary and paper-first.
- **Data licensing:**
  - NSE owns its market data, and redistribution or derived index/instrument creation needs an NSE Data licence.
  - jugaad-data and nsepython scrape nseindia.com, whose terms restrict automated access.
  - Yahoo data is for personal use only.
  - Treat all three as private research inputs.
- **Licences:** backtesting.py and OpenAlgo server (AGPL), backtrader and nsepython (GPL-3), vectorbt (Commons Clause), Angel SmartAPI (no licence file) and jugaad-data (YOLO, non-standard). None of them may be copied into b3 kits or any paid product.
- **Overfitting:** the trial showed in-sample Sharpe 1.21 falling to 0.15 out-of-sample. Without the gate, a "backtested bot" will look good and lose money. Survivorship bias also matters: yfinance only has currently listed symbols, so delisted stocks are missing.
- **Fragility:** NSE endpoints block plain HTTP clients (curl got 403) and change without notice, and yfinance is unofficial. Pin versions (vectorbt 1.1.2, quantstats 0.0.86, bt 1.4.1, backtesting 0.6.6) because pandas 3 is fresh.
- **Cost creep:** historical and real-time broker data are paid (₹499–500/month), which is within the ₹0–5,000 budget only once paper results justify it.

Sources: [Fyers: SEBI retail algo rules from 1 Apr 2026](https://support.fyers.in/portal/en/kb/articles/what-are-the-new-sebi-rules-for-retail-algo-trading-from-april-01-2026), [Marketcalls: new NSE rules for retail algo trading](https://www.marketcalls.in/market-regulations/new-nse-rules-for-retail-algo-trading-what-retail-traders-algo-platforms-and-brokers-must-now-do.html), [NSE data policy](https://www.nseindia.com/static/market-data/nse-data-policy), [NSE Data Sharing & Usage Policy (PDF)](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/NSE_Data_Sharing%26Usage_Policy.pdf), [Zerodha: Kite API charges](https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/what-are-the-charges-for-kite-apis), [Dhan: Data API pricing](https://dhan.co/support/platforms/dhanhq-api/is-the-dhanhq-data-api-subscription-free-if-i-execute-a-minimum-number-of-trades-every-month/).

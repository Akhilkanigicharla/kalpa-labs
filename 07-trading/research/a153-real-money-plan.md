# A153 · b7 Real-money algo trading for Akhil: legal facts, setup, build plan

Research by Claude, 6 Nov 2026 (evening IST). Two sources per legal fact. This is engineering and process, not investment advice; no strategy can promise profit. Akhil trades his own money only; nobody else gets tips or signals (SEBI).

## 1. The answer in 5 lines
1. **Legal path:** your own Python bot can trade Indian stocks/ETFs through a SEBI broker's API, as long as it stays under 10 orders a second, sends orders from a **whitelisted static IP**, and you log in with 2FA every trading day (rules in force since 1 Apr 2026).
2. **Crypto is legal** on an FIU-registered Indian exchange with an API (e.g. Delta Exchange India, CoinDCX), but every profit is taxed 30%, 1% TDS is cut on each sale, and losses cannot be set off. Only slow strategies survive that.
3. **Forex:** only 7 pairs, only as exchange futures/options on NSE/BSE through a SEBI broker. MetaTrader/offshore forex apps (OctaFX etc.) are illegal for Indians. Not a good first step.
4. **Free static IP:** Oracle Cloud Always Free gives a small server with a public IP (official docs) and 1 reserved (fixed) IP (secondary sources). Signup asks for a card for identity, so it is Akhil's call (rule 1).
5. **Order:** backtest → 90-day paper → small live (an amount you can fully lose) with stop-loss, 1% daily loss cap and kill switch → grow only on proof. The lab code for steps 1–2 already exists (51 tests green today).

## 2. Legal facts (checked twice today)
| Fact | Status | Sources |
|---|---|---|
| SEBI retail algo framework mandatory for all brokers from 1 Apr 2026 (SEBI circular Feb 2025); each algo order carries an exchange Algo ID | VERIFIED | aliceblueonline.com; dev.to (reyazk08); liquide blog |
| Below 10 orders/second per exchange: "regular API user", no separate strategy registration | VERIFIED | Tradejini; FYERS support; QuantInsti; sahi.com |
| API orders only from a whitelisted static IP (primary + optional backup; change at most once a week) | VERIFIED | FYERS support; Angel One SmartAPI notice; Dhan (madefortrade); Zerodha via onetradejournal; NSE standards via finseclaw |
| Daily 2FA login; no overnight sessions | VERIFIED | FYERS support; aliceblueonline.com |
| Zerodha Kite Connect: Personal API free (orders only, no data); Connect ₹500/month with live + historical data | VERIFIED | support.zerodha.com (2 pages); onetradejournal (checked 14 Oct 2026) |
| FYERS, Dhan, Angel One SmartAPI APIs free (brokerage still applies) | VERIFIED | stratzy.in; algotest.in; investorgain (FYERS) |
| Crypto: 30% tax on gains + 1% TDS, no loss set-off; Budget 2026 kept it; new reporting penalties from 1 Apr 2026; sections renumbered in Income-tax Act 2025 | VERIFIED | tokentax.co; coingape (1 Feb 2026); koinx; whale-alert (CoinDesk) |
| Delta Exchange India (FIU-registered, INR crypto futures/options) has REST + WebSocket API; CoinDCX FIU-registered with API | VERIFIED | OpenAlgo docs; latestly; koinly; outlookbusiness |
| Forex for residents: only exchange-traded currency derivatives, 4 INR pairs + EUR/USD, GBP/USD, USD/JPY; LRS money cannot fund offshore margin trading; RBI Alert List ~95 names | VERIFIED | RBI press release; Mint (pressreader); righttoinformation.wiki; gulfnews; outlookmoney |
| Oracle Always Free: public IP per free VM (official); 1 reserved public IP free | Official page + 2 secondary (reserved IP: confirm when creating) | docs.oracle.com; devfoliox; orendra |
| SEBI FY25 study: over 91% of individual F&O traders lost money | From 07-trading/PLAN.md (checked 13 Oct) | PLAN.md §1 |

## 3. Three tracks for Akhil to pick
| Track | What the bot does | Why | Watch-outs |
|---|---|---|---|
| **A. Indian ETF trend bot (recommended first)** | Holds a Nifty ETF (e.g. NIFTYBEES) when its long trend is up, cash when down; position sized by volatility; a few trades a year | Strongest published evidence (time-series momentum, volatility targeting: 07-trading/research/deep-scan-v2.md); low costs; already built in the lab (`src/strategies.py`, `gate.py`, `paper.py`) | Needs static IP + free broker API; slow: may earn less than just holding the index |
| **B. Crypto trend bot (your first ask)** | Same slow trend rule on BTC/ETH spot on an FIU-registered exchange, 24×7 | Runs from any cloud (no SEBI static-IP rule); exchange APIs are free | 30% tax + 1% TDS on every sale and no loss set-off: fast trading loses; exchange risk |
| **C. A + B together** | Two small bots, separate loss caps | Spreads risk across markets | Twice the setup; Akhil checks 2 dashboards |

**Forex** stays as a later research item: legal only as NSE currency futures, which are leveraged F&O.

## 4. Build plan (after Akhil picks)
1. **Broker adapter** (paper first): one small interface `place / cancel / positions` with a FakeBroker for tests, then the real one (FYERS or Dhan free API for A; Delta/CoinDCX API for B). MIT SDKs only; OpenAlgo (AGPL) only as a separate unmodified service, never copied.
2. **Live guard** on top of the existing Risk Warden (`src/risk.py`, daily 1% / weekly 2% / monthly 4% loss caps): order-rate limiter well under 10/second, max position size, a kill-switch file, stop-loss on every position, alerts to Akhil's private Telegram (CEO chat only).
3. **Paper run 90 days** with real prices; weekly tear-sheet in the daily brief.
4. **Go-live gate:** the strategy passes `gate.py` + 90 days paper + Akhil types "go" for live money and sets the broker keys himself as secrets (Claude never sees keys or places trades by hand).
5. **Server:** Oracle free VM with reserved IP (or a paid VPS ~₹400–800/month, jayadevrana.com, UNVERIFIED price) whitelisted at the broker; GitHub Actions only for research and paper.

## 5. For Akhil to decide (CEO queue C64)
1. Pick a track: **A**, **B** or **C**.
2. Live money size you can fully lose (your number; suggestion: start with ₹5,000 or less).
3. OK the Oracle free server (card needed for identity) or a paid VPS later.

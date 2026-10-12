# P7: b7 Trading. The Market Maze plan

Planning agent P7, 2026-10-13. Inputs: `00-hq/research/BRIEF.md`, `07-trading/README.md`, `00-hq/research/github/a8-trading.md`. This document describes engineering and process only. It does not recommend buying or selling any security, and it is not investment or tax advice. Check tax points with a CA.

---

## 1. Verdict

b7 is not a business. It is the CEO's own capital research lab, and of the 8 worlds it is the **least likely to make money and the most likely to lose it**. SEBI's own FY25 study found that **over 91% of individual F&O traders lost money**, with net losses of ₹1.06 lakh crore. Our research run showed the same trap at small scale: an SMA strategy had an in-sample Sharpe of 1.21, but walk-forward gave **0.15**, against 0.59 for simply holding the stock.

The lab can only make money by finding a rule that survives a strict gate, then 90 days of paper trading, then small live capital. Even then, profit on ₹25,000 is pocket change next to a CA fee.

Realistic ₹ result, net of costs (trading P&L on capital Akhil chooses to risk, plus any b3/b5 spin-off sales):

| | Low | Likely | High |
|---|---|---|---|
| Month 1 | ₹0 | ₹0 | ₹0 |
| Month 3 | ₹0 (paper only) | ₹0 | ₹0 |
| Month 6 | −₹1,500 | ₹0 (still paper, or nothing passed) | +₹800 |
| Month 12 | −₹4,000 | −₹500 | +₹3,000 |

**The biggest risk** is that a good-looking backtest leads to real money going into an overfit rule, and that money then grows after losses. The second risk is regulatory: live API orders from GitHub Actions or Colab are non-compliant under the SEBI retail-algo rules in force since 1 Apr 2026 (static IP, Algo ID, daily 2FA). The lab's real product is **the gate that says "no"**, and its likeliest useful output is honest education content and calculators sold through b3 and b5, not trading profit.

---

## 2. Customer & offer

**Who pays:** Akhil, with his own capital. There are no clients. Selling signals, tips or strategies to anyone needs SEBI registration (see §2c), so b7 has no external customer.

**The offer to the CEO:** a lab that turns trading ideas into one of three verdicts: *rejected*, *paper*, or *live-micro*. Every verdict comes with a tear-sheet and a cost-and-tax estimate. Akhil's time is capped at about 5 minutes a day (b7's 8% share).

**The honest alternatives** (what the same ₹ could do instead):

| Alternative | Price | What it means for b7 |
|---|---|---|
| Nifty 50 index fund, direct plan (for example Navi) | ~0.10% a year expense ratio | **This is the benchmark.** If the lab can't beat it after costs and tax over 12 months, the capital goes here. |
| AlgoTest | from ₹499/month | Paid no-code backtest, paper and deploy. |
| Tradetron | about ₹1,000–4,000/month | Paid strategy marketplace and deploy. |
| Streak (Zerodha) | about ₹500–1,500/month | Paid no-code scanner and backtest. |

The lab costs ₹0 a month. Our edge over these platforms is not alpha. It is that our gate is stricter than theirs, because walk-forward testing, the Probability of Backtest Overfitting (PBO) and cost stress are built in.

### 2a. Venues allowed in year 1, and why the "crypto and forex bot" idea is parked

| Venue | Year-1 status | Reason |
|---|---|---|
| NSE/BSE cash segment, delivery (stocks, ETFs) | **Allowed** (paper, then micro-live) | Lowest costs, capital-gains tax treatment, no leverage. |
| Intraday equity | Not allowed | Taxed as speculative income, and losses only offset speculative profits (4-year carry-forward). Costs are high relative to the edge. |
| F&O | Not allowed | 91% of individuals lose money. Index contracts have a minimum size of about ₹15 lakh. STT rose on 1 Apr 2026 (futures 0.02%→0.05%, options 0.1%→0.15%). |
| Currency derivatives | Exchange-listed INR pairs only (USD/EUR/GBP/JPY-INR, plus the listed crosses), and not in year 1 | Offshore "forex" apps are a FEMA violation, with penalties up to 3× the amount involved, and RBI keeps an alert list of unauthorised platforms. |
| Crypto | Not allowed | Gains taxed at a flat 30% plus 1% TDS, losses can't be set off, and the legal status is unsettled. |

### 2b. Taxes on trading income (India; Akhil as an individual or proprietor)

Kalpa Labs is a Udyam-registered proprietorship, so trading P&L is filed under **Akhil's PAN**, on the same return as Kalpa Labs' business income. The **Income-tax Act 2025 has applied since 1 Apr 2026**. Classifications are unchanged but section numbers moved (the speculative definition is now s.66(31)/(33)). The old numbers below are given for reference.

| Activity | Tax head | Rate | Losses |
|---|---|---|---|
| Delivery equity, held < 12 months | STCG | 20% | Set off against capital gains, carry forward 8 years |
| Delivery equity, held > 12 months | LTCG | 12.5% above ₹1.25 lakh a year | Same |
| Frequent delivery trading | Can be treated as business income | Slab rate | Ask the CA which treatment to take, then stay consistent |
| Intraday equity | **Speculative business income** | Slab rate | Only against speculative income, 4 years |
| F&O, exchange currency derivatives | **Non-speculative business income** | Slab rate | Against other business income (not salary), 8 years |
| Crypto | VDA | 30% flat + 1% TDS | No set-off |

Points that bite:

- **ITR-3** is required once there is any business or trading income. ITR-1, -2 or -4 will be rejected as defective. The return must be filed **on time**, or the right to carry losses forward is lost.
- **Tax audit (old s.44AB):**
  - Audit is needed above ₹1 crore of turnover, or ₹10 crore if cash is no more than 5% of transactions. Trading is all digital, so ₹10 crore is the relevant limit.
  - Audit is also needed if Akhil opts out of presumptive tax and declares profit below 6% of turnover while total income is above the exemption limit.
  - F&O turnover counts the *absolute* profit and loss of each trade (ICAI method), not the contract value.
  - Presumptive taxation (s.44AD) at 6% has a 5-year lock-in, and losses can't be carried forward under it.
- **Advance tax** applies if the year's liability exceeds ₹10,000. Otherwise interest under s.234B/C is charged.
- **CA fee for ITR-3:** expect about ₹2,000–5,000 a year. On ₹25k capital, that fee alone needs an 8–20% return just to break even.

### 2c. What b7 could ever sell legally

| Idea | Legal? | Where it goes |
|---|---|---|
| **Education content** ("why my backtest lied", walk-forward explained, cost and tax maths) | Yes, within limits. Under SEBI's 8 May 2026 circular, in force from **1 Jul 2026**, educators may only use price data **at least 30 days old**, and may not name securities (or use code names) in a way that suggests future moves or recommendations. No return claims, and no paid tie-ups that make us a finfluencer for a SEBI-regulated entity. | b5 blog and newsletter, YouTube |
| **Charges and tax calculator** (brokerage, STT, ICAI turnover, audit-flag check) | Yes. It is a tool, not advice. | b5 finance-calculator site |
| **Trading-journal and tax-turnover Google Sheet** (₹199–299) | Yes, as long as it contains no NSE or Yahoo data and no signals | b3 Kits |
| **Open-source `gate.py` and `costs.py`** (MIT) | Yes, with no data and no strategies included. Only bt and quantstats code may be used, never backtesting.py or vectorbt code. | GitHub, credibility for b6 |
| Signals, tips, model portfolios, paid Telegram groups | **No**, unless registered as a SEBI Research Analyst: graduate, NISM Series XV certificate, about ₹5,000 in SEBI fees plus GST, a ₹1 lakh deposit for up to 150 clients, ongoing compliance. Part-time providers also have to register. | Not planned |
| Selling or renting an algo to retail users | **No.** The provider must be empanelled with the exchange and each algo needs its own Algo ID. Black-box algos also need RA registration and a research report per algo. | Not planned |
| Managing other people's money or copy-trading | **No.** That needs PMS/IA-level registration. | Never |

---

## 3. Unit economics (cost of the lab per month)

| Phase | What runs | ₹/month | Limit |
|---|---|---|---|
| R: research | Colab plus Actions `backtest.yml` | ₹0 | Actions minutes are free on a public repo, 2,000/month on a private one. A gate run takes about 3–5 min, so ~400 runs a month on a private repo. |
| P: paper (90 days) | Actions cron `paper-trade.yml`, about 2 min each weekday | ₹0 | About 45 min/month |
| L1: live-micro, manual | The paper job produces a "signal card". Akhil places any order himself in the broker app. | ₹0 extra (delivery brokerage is ₹0–20 per order at most discount brokers) | Manual orders aren't algo orders, so there is no static IP or Algo ID. |
| L2: live API (not planned within 12 months) | OpenAlgo on a static Indian IP, plus Kite Connect or Dhan data | About ₹500 for data + ₹300–800 for a static IP or Indian VPS = **about ₹1,000+** | Not affordable at small capital |

**Break-even:**

- L1 needs only profit greater than the yearly CA fee (about ₹3,000) to beat zero.
- L2 costs about ₹12,000 a year plus the CA fee, about **₹15,000/year**. A realistic edge of 5% a year over the index would need **about ₹3 lakh or more of capital** just to pay for the setup.
- The rule that follows: **no paid data or VPS until live-micro has run for 12 months with net after-tax returns above the index fund, on capital of at least ₹3 lakh.** This plan does not expect to reach that point.

---

## 4. Go-to-market (adapted: the path from idea to capital)

The plan has no customers, so the "first 10 customers" become **the first 10 hypotheses through the gate**, then the paper ledger.

1. **Hypothesis card (Akhil, 5 min).** One line: the idea, the universe (liquid ETFs and large caps only), the holding period (daily or weekly), and why it might work. Agents never invent a hypothesis to "find something".
2. **Pre-registration (agent).** The parameter grid is fixed *before* the run, and every configuration tried is logged to `07-trading/research/trials.csv`. The trial count feeds the PBO and the Probabilistic Sharpe Ratio (PSR).
3. **Gate run (`backtest.yml`).** Output is a tear-sheet plus a pass or fail on each criterion (§5, Q7.4).
4. **Weekly verdict (Akhil, 10 min on Sunday).** Choose rejected, re-think (only once per hypothesis) or paper.
5. **Quota:** at most 2 hypotheses a week. At most 50 logged trials in total before 31 Dec 2026 (see kill criteria).

**10 → 100:** b7 doesn't scale with customers. The scaling path is the **spin-offs in §2c**. Each passed or failed experiment becomes one educational post (using data at least 30 days old). The cost and tax calculator feeds b5 traffic, and the journal sheet becomes a b3 product. Their GTM belongs to the b3 and b5 plans.

---

## 5. Build plan (quests ≤ 60 min of CEO time)

All code goes under `07-trading/`. **Stack:** bt (MIT) and quantstats (Apache-2.0) for anything that might ship. backtesting.py (AGPL) and vectorbt (Commons Clause) are **internal Colab research only**. yfinance is the primary data source with jugaad-data as fallback, and both are research-only inputs.

### Week 1

| id | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| Q7.1 | Licence and data hygiene | Read the README diff (2 min) | Add the a8 licence note to `07-trading/README.md`. Add `07-trading/data/` to `.gitignore`. Pin versions in `07-trading/requirements.txt` (bt 1.4.1, quantstats 0.0.86, yfinance, pandas). | `git check-ignore 07-trading/data/x.parquet` passes |
| Q7.2 | `07-trading/src/data.py` | none | `get_daily(symbol)`: yfinance `.NS`, falling back to jugaad-data, with Parquet cache. Validation checks for NSE-calendar gaps, prices ≤ 0 and split jumps. Unit tests use synthetic data only. | Tests pass in Actions, and no price file appears in git |
| Q7.3 | `07-trading/src/costs.py` | none | Separate cost functions for delivery, intraday and F&O covering STT (2026 rates), exchange charge, SEBI fee, stamp duty, GST on brokerage and charges, and DP charge. Every rate carries a source URL and the date it was checked. | A test reproduces one broker contract-note example to within ₹1 |

### Weeks 2–4

| id | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| Q7.4 | `07-trading/src/gate.py` | Approve the thresholds (10 min) | Pass requires **all** of the following: (1) rolling walk-forward OOS Sharpe ≥ 0.5 **and** above buy-and-hold on the same window, (2) quantstats PSR ≥ 0.95, (3) at least 30 OOS trades, (4) PBO by CSCV < 0.5, written by us from Bailey et al. and not copied from AGPL pypbo, (5) still passes at **2× costs plus a one-bar fill delay**. Sharpe is always annualised at 252. | The a8 SMA example is **rejected** by the gate, as a regression test |
| Q7.5 | Trials registry | none | `research/trials.csv` (hypothesis id, params, date, IS/OOS metrics). The gate refuses any run that isn't logged. | Running without a log entry fails |
| Q7.6 | `.github/workflows/backtest.yml` | Approve the workflow (5 min) | Runs on push to `07-trading/src/**`. Data comes from the Actions cache, never git. Tear-sheets are uploaded as artifacts. | A green run with an HTML artifact |
| Q7.7 | First 3 hypothesis cards | Write 3 one-liners (15 min) | Run them through the gate and write a one-page verdict for each | 3 verdicts in `07-trading/docs/verdicts/` |
| Q7.8 | Capital-rules sign-off | Read §5a and decide the capital amount, including ₹0 (15 min) | Draft `07-trading/docs/capital-rules.md` from §5a | File signed off with a date |

### Month 2 (only if at least one strategy passes the gate; otherwise keep cycling Q7.7 until the K1 date)

| id | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| Q7.9 | `07-trading/src/paper.py` | none | Reads the end-of-day bars after close, computes signals, records **simulated next-open fills** including costs, applies the §5a risk rules, and makes no broker calls | Dry run over 20 past days matches the backtest's trades exactly |
| Q7.10 | `.github/workflows/paper-trade.yml` | Enable the workflow (5 min) | Cron `45 10 * * 1-5` UTC (16:15 IST), with an NSE holiday skip. Appends to `07-trading/paper/ledger.csv` (date, id, side, qty, simulated return %, costs, P&L %, with no raw OHLC). Uploads a quantstats artifact. | First ledger row exists, and **the 90-day clock starts at this date** |
| Q7.11 | Risk-rule checker | none | `src/risk.py` blocks paper "orders" that break per-trade, daily or position limits and logs each breach | A test with a forced breach is blocked |

### Month 3

| id | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| Q7.12 | Weekly paper review | 10 min each Sunday | Writes the paper vs backtest comparison: slippage, hit rate, drawdown, missed runs | 4 weekly notes |
| Q7.13 | Tax pack v1 | Shortlist one CA (20 min) | `docs/tax-notes.md`: how ITR-3 applies, the ICAI turnover method, the audit flag, advance-tax dates, the new-Act section map | Note reviewed by the CA or marked "to check" |
| Q7.14 | Spin-off 1 | Approve the post (10 min) | "Why our backtest lied" post for b5, using data at least 30 days old, naming no security as an opportunity, with a disclaimer. Plus a charges calculator spec handed to b5. | The content validator (§6) passes |

### Day 90 and after: the paper gate (about Feb–Mar 2027)

Go to **L1 live-micro** only if every one of these holds:

- at least 60 trading days of ledger and at least 20 trades (if there are fewer trades, *extend* the paper period; don't shortcut it);
- paper drawdown no more than 1.5× the backtest OOS drawdown;
- net-of-cost paper return above the 5th percentile of the backtest's OOS 90-day windows;
- at least 95% of scheduled runs completed;
- zero risk-rule overrides.

L1 starts with ₹10,000, orders placed by Akhil by hand, for 3 months. After that it can go up to the signed cap.

### 5a. Capital rules (proposed; Akhil signs in Q7.8)

1. **Keep company and trading money separate.** The Kalpa Labs ₹0–5,000 budget and its business bank account **never** fund trading, and trading losses are never covered by Kalpa revenue. Trading uses a separate personal bank account and demat. (Legally it is the same PAN, but separate accounts keep operating cash and books clean.)
2. **Size of the trading pot:** the smaller of **₹25,000** and **5% of liquid savings**, and only money Akhil could lose entirely without changing his life. No loans, credit cards, margin (MTF) or pledging.
3. **Per trade:** at most **0.5% of the pot at risk** (₹125 on ₹25k), measured from entry to stop. At most 20% of the pot in any one position, and at most 5 open positions.
4. **Per day:** loss of **1% or more** means no new orders that day. **Per week:** 2%. **Per month:** loss of 4% or more means pause for the rest of the month and review.
5. **Drawdown of 10% from the pot's peak:** live trading stops and the strategy goes back to paper (kill criterion K3).
6. **No top-ups after a loss.** The pot can only grow from realised profit or from a written, dated decision made when the pot is at its peak. Profit above the cap is withdrawn every quarter.
7. **No discretionary overrides.** A trade the signal didn't produce counts as a rule breach.

---

## 6. Agent swarm (registry style)

```js
// world b7: Trading lab; tokens are tiny because most of it is code
A({ id:"b7.data",  name:"Market Data Keeper", unit:"b7", team:"lab", mission:"Fetch and validate NSE daily bars into the cache (yfinance → jugaad fallback).", trigger:{event:"gate or paper run"}, runs_as:"code", code:"07-trading/src/data.py", tokens:0, kpi:"0 bad bars reach the gate", validator:{checks:["no prices in git","no gaps on NSE trading days","no price ≤ 0","split jumps adjusted"]} }),
A({ id:"b7.costs", name:"Cost Modeller", unit:"b7", team:"lab", mission:"Apply Indian charges (STT, exchange, SEBI, stamp, GST, DP) to every simulated fill.", trigger:{event:"every run"}, runs_as:"code", code:"07-trading/src/costs.py", tokens:0, kpi:"Matches a real contract note within ₹1", validator:{checks:["every rate has source + check date ≤ 90 days old","no run at zero cost"]} }),
A({ id:"b7.gate",  name:"Overfit Gatekeeper", unit:"b7", team:"lab", mission:"Walk-forward, PSR, PBO/CSCV, 2× cost stress; verdict rejected/paper.", trigger:{event:"push to 07-trading/src"}, runs_as:"code", code:"07-trading/src/gate.py", tokens:0, kpi:"a8 SMA example always rejected", validator:{checks:["trial logged before run","Sharpe annualised at 252","OOS trades ≥ 30"]} }),
A({ id:"b7.paper", name:"Paper Trader", unit:"b7", team:"lab", mission:"Weekday 16:15 IST simulated next-open fills to paper/ledger.csv.", trigger:{cron:"weekdays:16:15"}, runs_as:"code", code:"07-trading/src/paper.py", tokens:0, kpi:"≥95% scheduled runs", validator:{checks:["no broker calls","no raw OHLC in ledger","holiday skip"]} }),
A({ id:"b7.risk",  name:"Risk Warden", unit:"b7", team:"lab", mission:"Enforce capital rules on paper and live-micro signal cards.", trigger:{event:"every signal"}, runs_as:"code", code:"07-trading/src/risk.py", tokens:0, kpi:"0 unblocked breaches", validator:{checks:["0.5%/trade","1% day","10% DD stop"]} }),
A({ id:"b7.review",name:"Weekly Lab Reviewer", unit:"b7", team:"lab", mission:"Paper-vs-backtest note and verdict prep for Sunday.", trigger:{cron:"weekly:sun"}, tokens:3000, kpi:"note ready by 9 AM Sunday", validator:{checks:["numbers match ledger","no buy/sell language"]} }),
A({ id:"b7.tax",   name:"Trading Tax Clerk", unit:"b7", team:"finance", mission:"ICAI turnover, audit flag, advance-tax reminders, ITR-3 pack for the CA.", trigger:{cron:"monthly"}, tokens:2000, kpi:"ITR-3 filed on time", validator:{checks:["CA reviews before filing","new-Act section numbers checked"]} }),
A({ id:"b7.reg",   name:"SEBI/NSE Rule Watcher", unit:"b7", team:"compliance", mission:"Read new SEBI/NSE/broker circulars on retail algo, education, F&O; flag impact.", trigger:{cron:"monthly"}, tokens:2000, kpi:"no rule missed > 30 days", validator:{checks:["source is sebi.gov.in / nseindia.com / broker"]} }),
A({ id:"b7.edu",   name:"Education Writer", unit:"b7", team:"content", mission:"Turn verdicts into b5 posts and calculator specs.", trigger:{event:"verdict"}, tokens:4000, kpi:"1 post per 2 verdicts", validator:{checks:["price data ≥ 30 days old","no security named as an opportunity","no return claims","disclaimer present"]} }),
A({ id:"b7.exec",  name:"Live-Micro Executor", unit:"b7", team:"lab", mission:"Akhil places L1 orders by hand from the signal card.", trigger:{event:"signal card"}, runs_as:"human", human_needed:true, tokens:0, kpi:"fills logged same day", validator:{checks:["order matches card","no override"]} }),
```

---

## 7. Metrics and kill criteria

**Weekly numbers:** hypotheses tested, trials logged, gate pass rate (expect about 0–10%), paper runs completed %, paper P&L % against the backtest band, drawdown, rule breaches (target 0), and CEO minutes spent on b7 (target ≤ 35 a week).

| # | Condition | Action |
|---|---|---|
| K1 | **31 Dec 2026:** nothing has passed the gate within 50 logged trials | **Pause b7.** Freeze the code. Only the monthly Rule Watcher and spin-off content keep running. The time moves to the b1/b2 plans. |
| K2 | **Day 90 of paper:** the paper gate fails | Back to research once. A second failure pauses b7 until at least Q3 2027. |
| K3 | **Live:** 10% drawdown from peak, or any manual override | Stop live immediately and go back to paper. |
| K4 | **12 months live:** net after-tax return is below the Nifty index fund over the same period | Stop live trading for good and move the pot to the index fund. |
| K5 | b7 takes more than 60 CEO minutes a week for 3 weeks in a row | Pause b7 for one month. |
| K6 | A rule change, such as a broker requiring a static IP even for retail app orders, makes L1 impossible | Stay on paper or close b7. Never work around a rule. |

---

## 8. What I need from Akhil

- [ ] Agree that **₹0 of the Kalpa Labs budget** goes to trading, and that b7's realistic 12-month outcome is about ₹0.
- [ ] Decide the trading pot (₹0 is a valid answer), up to the smaller of ₹25,000 and 5% of liquid savings. Sign `capital-rules.md` (Q7.8).
- [ ] Confirm a separate personal bank account and demat for trading, at a broker of your choice. Don't share any login, password, OTP or API key in chat, ever.
- [ ] Confirm the year-1 venue list: delivery equity and ETFs only, with no F&O, intraday, crypto or offshore forex.
- [ ] Say whether the repo is public or private. That decides the Actions minutes and what the ledger may contain.
- [ ] Shortlist a CA for ITR-3 before the first live trade.
- [ ] Write 2 hypothesis one-liners a week. No hypothesis means no run.

---

## 9. Sources

- Research: `00-hq/research/github/a8-trading.md` (licences, walk-forward result, SEBI algo rules, NSE data policy, Kite and Dhan pricing)
- [Business Standard: SEBI FY25 F&O study, more than 91% of individuals lost money](https://www.business-standard.com/amp/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html)
- [5paisa: STT hike on F&O effective 1 Apr 2026](https://www.5paisa.com/news/stt-hike-on-fo-to-take-effect-from-april-1-amid-rising-options-activity)
- [Upstox: F&O under the Income-tax Act 2025 (sections, turnover, losses)](https://upstox.com/news/personal-finance/tax/income-tax-act-2025-f-and-o-taxation-turnover-calculation-loss-set-off-and-carry-forward-explained/article-200609/)
- [Groww: how traders are taxed, AY 2026-27 (intraday, audit, 44AD)](https://groww.in/blog/how-traders-are-taxed-in-india)
- [Outlook Money: SEBI 30-day price-data rule for education, from 1 Jul 2026](https://www.outlookmoney.com/amp/story/invest/sebi-revises-norms-for-sharing-and-usage-of-price-data-for-educational-purposes)
- [Business Standard: SEBI finfluencer circular (Jan 2025)](https://www.business-standard.com/markets/news/sebi-finfluencer-circular-live-stock-data-market-education-rules-125013000571_1.html)
- [Moneylife: SEBI RA/IA reforms, Dec 2024](https://www.moneylife.in/article/sebi-introduces-major-reforms-for-investment-advisers-and-research-analysts/75888.html)
- [Taxation Consultancy: SEBI RA registration requirements 2026](https://taxationconsultancy.in/?p=393)
- [KS&K: SEBI retail algo framework (white or black box, empanelment, RA for black box)](https://ksandk.com/corporate/sebis-new-regulatory-framework-for-retail-algorithmic-trading/)
- [Marketcalls: NSE retail algo rules (10 OPS, static IP, Algo ID)](https://www.marketcalls.in/market-regulations/new-nse-rules-for-retail-algo-trading-what-retail-traders-algo-platforms-and-brokers-must-now-do.html)
- [Fyers: SEBI retail algo rules from 1 Apr 2026](https://support.fyers.in/portal/en/kb/articles/what-are-the-new-sebi-rules-for-retail-algo-trading-from-april-01-2026)
- [Moneylife: SEBI F&O measures (minimum contract size)](https://www.moneylife.in/article/sebi-tightens-regulations-on-equity-derivatives-trading/75288.html)
- [Jainam: forex legality in India (permitted pairs, FEMA penalties)](https://www.jainam.in/blog/is-forex-trading-legal-in-india/)
- [Outlook Business: RBI alert list of unauthorised forex platforms](https://www.outlookbusiness.com/news/rbi-issues-alert-list-on-entities-not-authorised-to-deal-in-forex-trading-news-221754)
- [KoinX: crypto tax in India 2026](https://www.koinx.com/in/crypto-tax-guide)
- [AlgoTest: algo platform pricing (AlgoTest, Tradetron, Streak)](https://algotest.in/blog/algo-trading-software-price-in-india.md). This is a competitor-published page, so verify the prices.
- [INDmoney: Nifty 50 index fund expense ratios](https://www.indmoney.com/mutual-funds/equity/nifty-50-index-funds)
- [NSE data policy](https://www.nseindia.com/static/market-data/nse-data-policy)

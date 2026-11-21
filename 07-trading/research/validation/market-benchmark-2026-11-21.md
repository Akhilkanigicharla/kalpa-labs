# Market benchmark for the XAUUSD MSNR+EMA9 EA (2026-11-21)

Research only. No sign-ups, no logins. Web content treated as data. Quotes are under 15 words with their URL.
Tags: **VERIFIED** = primary source fetched today, or 2+ independent sources. **UNVERIFIED** = one source only, or a vendor/affiliate source.
Our claim under test: +66% over 2 years on $10K, 4.9% max DD, ~5 trades/day, 0.25% risk per trade, H1–H4, for The5%ers High Stakes $10K.

---

## 0. Headline findings (read this first)

1. **The5%ers rules block selling this EA to customers for use there.** Their Terms (last updated 28 Oct 2026) say any automated software needs **prior written approval**, and "the Company prohibits use of any Automated Trading Software owned or developed by any third party other than the User" ([the5ers.com/terms-and-conditions](https://the5ers.com/terms-and-conditions/)). The FAQ also bans "EA from a third party, where other traders have the same trades open" ([the5ers.com/faqs/prohibited-trading-practices](https://the5ers.com/faqs/prohibited-trading-practices/)). VERIFIED (primary, plus [jptradingcapital](https://www.jptradingcapital.com/blog/en/the5ers-ea-rules) and [tesseratrades](https://www.tesseratrades.com/learn/the5ers-ea-rules)). Akhil running **his own** EA is possible only after The5%ers approves it in writing.
2. **Our backtest is far above every professional benchmark.** +66%/2 yrs is about **28.8% a year** (1.66^0.5). Return-to-drawdown is about **5.9 a year** (28.8 / 4.9). A century of trend following gave **7.3% a year net of fees, 9.7% vol, Sharpe 0.76** ([Hurst, Ooi, Pedersen, AQR](https://fairmodel.econ.yale.edu/ec439/hurst.pdf)). That gap means the backtest is most likely optimistic (costs, fills, curve-fit, or gold's 2024–2026 bull run). Treat it as a hypothesis until forward-tested.
3. **Most funded prop traders are never paid.** FPFX Tech data on 300,000+ accounts: 14% passed, about 7% of all traders got a payout, average payout about 4% of account size ([Finance Magnates, 18 Sep 2024](https://www.financemagnates.com/forex/exclusive-only-7-of-300000-prop-trading-accounts-achieved-payouts/); repeated by [CoinGape, Jul 2026](https://coingape.com/blog/93-of-funded-prop-traders-never-see-a-payout-a-new-report-explains-why/)). The5%ers has **never published** payout figures ([Finance Magnates, 2025 payouts](https://www.financemagnates.com/forex/prop-firm-match-tracked-about-325-million-in-payouts-to-traders-in-2025/amp)).
4. **India: The5%ers is not on the RBI Alert List; FTMO is.** RBI list "Updated as on November 19, 2025", 95 entities, includes FTMO (#13), FundedNext (#83) and Smart Prop Trader (#82); no "5ers" entry ([rbi.org.in Id=4235](https://rbi.org.in/scripts/Bs_viewcontent.aspx?Id=4235), fetched today; count matches [Gulf News](https://gulfnews.com/business/banking/etoro-forexcom-among-95-unauthorised-forex-platforms-in-india-flagged-by-rbi-1.500352489)). RBI says absence "should not be assumed to be authorised". Legality of paying an offshore forex/CFD prop firm is a grey area with no RBI ruling (UNVERIFIED single source, see §5).
5. **Grid/martingale gold EAs fail; a few stop-loss gold EAs survive at ~2%/month.** One real Dark Gold account is at −97% (Myfxbook). The 8-year Waka Waka grid record was reportedly wiped out in Oct 2026 (non-gold). The best independent real gold record found: Golden Pickaxe, +56% over ~2 yrs, 12% DD (§1).

---

## 1. Real verified results of public gold EAs

Survivorship warning: three of the MQL5 gold signals surfaced by search this week now return "signal not found" (deleted): [2380246](https://www.mql5.com/en/signals/2380246) (QuantumQueenX; the search snippet showed growth −99.83%, UNVERIFIED because the page is gone), [2391110](https://www.mql5.com/en/signals/2391110), [2376246](https://www.mql5.com/en/signals/2376246), [2380262](https://www.mql5.com/en/signals/2380262). Losing accounts disappear, so public lists look better than reality.

| # | EA / account | Type | Real/demo | Result (as fetched 20–21 Nov 2026) | Age | Alive? | Link |
|---|---|---|---|---|---|---|---|
| 1 | Dark Gold XAUUSD (DarkEAs) | Gold EA | Real | Gain **−97.34%**, DD **99.96%**, balance $21 from a $16.9K high | n/a | Blown | [myfxbook 11572408](https://www.myfxbook.com/members/DarkEAs/dark-gold-xauusd-mt4-411580/11572408) |
| 2 | Golden Pickaxe (independent user Deltatash) | Gold, AI/trend, SL | Real | **+56.41%**, ~**2.02%/month**, DD **12.0%**, 427 trades | joined Jan 2023; last update Apr 2025 | Stopped updating | [myfxbook 10049533](https://www.myfxbook.com/members/Deltatash/golden-pickaxe/10049533); same figures on [Stanchion Systems](https://stanchionsystems.com/ea-vendor-results/golden-pickaxe/) |
| 3 | Golden Pickaxe "Risky Set" (vendor account) | Gold | Real | **+221.45%**, 2.70%/month, DD **50.62%**, 3,026 trades | custom start Apr 2023 | Live | [myfxbook 10254914](https://www.myfxbook.com/members/MischenkoValeria/golden-pickaxe-risky-set/10254914) |
| 4 | Quantum OmniGold (MQL5, $999/month copy fee) | Gold | Real (ICMarketsSC) | **+35.91%**, DD **32.1%** by balance; "80% of growth achieved within 5 days" | 23 weeks | Live | [mql5 2379249](https://www.mql5.com/en/signals/2379249) |
| 5 | Quantum AI – Low Drawdown | Gold, averaging, no fixed SL | Likely real (BlackBull) | **−21%**, DD **30.7%**, PF 0.37 vs marketed PF 6.99 | 2 weeks | — | [mql5 2380210](https://www.mql5.com/en/signals/2380210) |
| 6 | Gold Detector 2026 EA | Gold M5 scalper | Not stated | **−20%**, DD 20.6% | 1 week | — | [mql5 2387828](https://www.mql5.com/en/signals/2387828) |
| 7 | Gold Martingale Pro | Gold grid-martingale | Not stated (IC Markets Raw) | **−12%**, DD **34%** | 1 week | — | [mql5 2377929](https://www.mql5.com/en/signals/2377929) |
| 8 | Gold Hunter V8 | Gold scalper | **Demo** | +346%, DD 0.43%, 12,982 trades | — | — | [myfxbook 11981314](https://www.myfxbook.com/members/ForexEALab/gold-hunter-v8-ea-mt5/11981314). Demo plus a near-zero DD on 13K trades fits HFT/latency effects. Ignore it. |
| 9 | The Gold Reaper v2.3 (third-party copy) | Gold H1 breakout | **Demo** | +47.85%, DD 4.40%, 42 trades | joined Jun 2025 | Last update Apr 2026 | [myfxbook 11684274](https://www.myfxbook.com/members/Forex_EAs/gold-reaper-v23/11684274). Vendor claims "+340.0%", "16.8%" max DD ([forexeasolutions.com](https://www.forexeasolutions.com/)), UNVERIFIED (vendor). |
| 10 | Waka Waka original (non-gold grid, context) | AUD-cross grid | Real | Reported **96.91% loss in Oct 2026**, max DD **99.61%** after 8 years | since Jun 2018 | Wiped (reported) | [bestforexeas review](https://www.bestforexeas.com/waka-waka-ea-review/), [myfxbots](https://www.myfxbots.com/blog/forex-robots/waka-waka/waka-waka-loses-main-track-record.html). The Myfxbook page #11662830 now shows "Private System Page" (403) today, which is consistent with the reports. Two secondary sources agree; primary not readable. |

**Blow-up rate evidence**
- A vendor blog ran backtests on 43 paid MQL5 gold EAs (2015–Jul 2026, M15, default inputs). About **19%** of the measurable ones blew the account (equity DD 60–102%), and the $1,999 EA had **PF 0.23 / 99% DD** ([mql5 blog 773167](https://www.mql5.com/en/blogs/post/773167)). UNVERIFIED: the author sells gold EAs and names none of the 43.
- **30 Jan 2026 gold crash:** spot gold fell about 9.5–9.8% from a ~$5,595 record, the steepest one-day drop since 1983 ([mql5 blog 778166](https://www.mql5.com/en/blogs/post/778166); confirmed by [Morningstar](https://www.morningstar.com/markets/why-are-gold-silver-plunging) and [GV Wire/Reuters](https://gvwire.com/2026/01/30/gold-set-for-steepest-daily-drop-since-1983-silver-eyes-worst-day-ever/)). By that blog's arithmetic, a flat $10 grid on $10K is wiped at about an 8% move, and any lot multiplier is wiped after a 2–6% move. VERIFIED for the price move; the grid maths is illustrative.

**What this means for us:** the realistic ceiling for honest, surviving, stop-loss gold EAs is about **1–3%/month with 10–30% drawdown**. Our backtest's ~2.1%/month is in that range, but a 4.9% DD is much lower than any real account found.

---

## 2. Prop-firm reality

### 2a. Pass and payout rates
| Metric | Figure | Source | Status |
|---|---|---|---|
| Pass rate (got funded) | **14%** of traders | FPFX Tech, 300K+ accounts, 100K traders, 10 firms ([Finance Magnates, 2024](https://www.financemagnates.com/forex/exclusive-only-7-of-300000-prop-trading-accounts-achieved-payouts/)) | VERIFIED (2 outlets) |
| Funded traders who got any payout | ~**45%** of funded = ~**7%** of all | same | VERIFIED |
| Average payout | ~**4%** of account size | same | VERIFIED |
| Funded lifespan | ~22 days (FPFX CEO) | [CoinGape, Jul 2026](https://coingape.com/blog/93-of-funded-prop-traders-never-see-a-payout-a-new-report-explains-why/) | UNVERIFIED |
| Industry payouts tracked 2025 | **$324,963,316**; FundedNext ~$107.8M, FundingPips ~$97.1M | Prop Firm Match via [Finance Magnates](https://www.financemagnates.com/forex/prop-firm-match-tracked-about-325-million-in-payouts-to-traders-in-2025/amp) | VERIFIED (FM + [TradingView mirror](https://www.tradingview.com/news/financemagnates:dbcee565f094b:0-prop-firm-match-tracked-about-325-million-in-payouts-to-traders-in-2025/)) |
| FTMO lifetime payouts | ">$450 million" (CEO claim, Sep 2025) | same article | UNVERIFIED (company claim) |
| The5%ers payouts | "never publicly shared" | same article | VERIFIED as absence |

On a $10K account, a 4% average payout is about $400 gross, or about $320 at an 80% split.

### 2b. The5%ers High Stakes $10K, as read on 21 Nov 2026
- Price: **$69** for $10K ([comparefuturesprop](https://comparefuturesprop.com/articles/the5ers-new-high-stakes-10k-account-guide), [pipster](https://www.pipster.io/research/firms/the5ers), [proea](https://proea.app/en/blog/the5ers-hyper-growth-rules)). VERIFIED (3 sources). At about ₹88/$ (rate not checked today), $69 is roughly ₹6,100, inside the ₹10,000 budget.
- Rules (primary page [the5ers.com/high-stakes](https://the5ers.com/high-stakes/)): Step 1 **10%**, Step 2 **5%**, max daily loss **5%**, max loss **10%**, **3** profitable days (each ≥0.5%), 1:100, split 80–100%, no time limit, but 30 days of inactivity expires the account. **No trades 2 minutes before or after high-impact news.**
- Payouts moved from monthly to **bi-weekly**, first one 14 days after funding ([propfirmmap, Apr 2026](https://propfirmmap.com/blog/prop-firm-news-april-16-22-2026-the5ers-topstep-thinkcapital)). UNVERIFIED (affiliate site).
- At the backtest pace of ~2.1%/month, Step 1 (10%) takes about 4–5 months and Step 2 (5%) about 2–3 more. That is arithmetic from our own claim, not a forecast.

### 2c. The5%ers EA rules (critical)
- Terms §Automated Trading Software: user-owned software needs **written notice and prior written approval**; The5%ers "may require advance testing"; third-party software is prohibited ([T&C, updated 28 Oct 2026](https://the5ers.com/terms-and-conditions/)). VERIFIED (primary).
- Prohibited practices: third-party EA where others hold the same trades; EA where "the trader does not own the source code"; rollover scalping; excessive server requests; HFT; tick scalping; news bracketing; copy trading; account management "Pass your Challenge" services ([FAQ](https://the5ers.com/faqs/prohibited-trading-practices/)). VERIFIED (primary).
- **Consequence:** selling this EA (or "pass-your-challenge" setups) to customers for The5%ers is banned. If Akhil uses it himself, he needs written approval first, and the EA must not trade within ±2 minutes of high-impact news.

---

## 3. Hedge-fund / CTA benchmarks

| Benchmark | Return | Risk | Source | Status |
|---|---|---|---|---|
| Trend following, 1880–2016 | **7.3%/yr excess, net of 2/20** (11.0% gross of fee) | vol 9.7%, **Sharpe 0.76** | [Hurst/Ooi/Pedersen (AQR)](https://fairmodel.econ.yale.edu/ec439/hurst.pdf) | VERIFIED (also [jkgcapital copy](https://jkgcapital.com/wp-content/uploads/2017/02/AQR-A-Century-of-Trend-Following-Investing.pdf), 1880–2013 version: 11.2% net, Sharpe 0.77) |
| Same, 2010–2016 | 3.3%/yr net | Sharpe 0.41 | same | VERIFIED |
| SG Trend Index 2025 | **+2.4%** | — | [Top Traders Unplugged](https://www.toptradersunplugged.com/trend-following-performance-report-december-2025/), [Aussie Turtles](https://www.aussieturtles.com/battle-of-the-trend-following-indexes-december-2025/) | VERIFIED |
| Barclay CTA Index 2025 | **+3.16%** (provisional) | −0.39% in 2023 | [TheFullFX](https://thefullfx.com/ctas-end-2025-on-a-positive-note/) | UNVERIFIED (one source; BarclayHedge site redirects) |
| SG CTA / SG Trend 2026 YTD | **+11.15% / +11.12%** (to 18 Nov 2026) | Nov MTD −2.38% / −2.87% | [SG Prime Services](https://wholesale.banking.societegenerale.com/en/prime-services-indices/) | VERIFIED (primary, live fetch) |
| CTA dispersion | best vs worst manager gap "typically around 10 percentage points" per year | — | [AIMA/Man](https://www.aima.org/article/a-trend-following-deep-dive-the-dynamics-of-dispersion.html) | single source |
| Renaissance Medallion 1988–2018 | **~66% gross, ~39% net** per year | net std dev ~20% (UNVERIFIED Medium calc) | [InvestmentNews](https://www.investmentnews.com/guides/what-the-man-who-solved-the-market-teaches-about-quantitative-investing/265700), [Institutional Investor](https://www.institutionalinvestor.com/article/2bswymr8cih3jeaslxc00/portfolio/famed-medallion-fund-stretches-explanation-to-the-limit-professor-claims) | VERIFIED. Employee-only, capacity-capped; not a realistic target. |
| Gold buy-and-hold 2025 | **+65%** (best year since 1979) | then −9.5% in one day on 30 Jan 2026 | [BullionVault](https://www.bullionvault.com/gold-news/gold-price-news/gold-silver-2025-record-price-123120251), [Yahoo/Carson](https://finance.yahoo.com/news/gold-is-up-more-than-40-in-2025-on-pace-for-its-best-year-since-1979-145005086.html) | VERIFIED |
| arXiv gold trend-momentum paper | Sharpe **2.88**, max DD 0.52% OOS 2015–2025 | — | [arXiv 2511.08571](https://arxiv.org/abs/2511.08571) | UNVERIFIED: not peer-reviewed, and the figures are extreme |

**Calibration of our claim**
- 28.8%/yr with 4.9% DD means return/maxDD ≈ 5.9. AQR trend following had about 7% a year with drawdowns in the tens of percent; [Hurst et al.](https://fairmodel.econ.yale.edu/ec439/hurst.pdf) show a 60/40 max DD of −62%.
- The 2-year window overlaps gold's +65% year. A long-biased S/R + EMA9 system would look good in that window. **Required check:** split results by long/short and by regime (2022 falling gold, 2023 range, 2025 trend, Jan 2026 crash).
- Thin-edge arithmetic (our own numbers): ~5 trades/day × ~500 trading days ≈ 2,500 trades. +66% over 2,500 trades at 0.25% risk works out to roughly **+0.1R per trade** on average (simple-sum approximation). If a stop is about $8 and the spread about $0.30, cost is about 0.04R per trade, which is **a third or more of the edge**. A news spread of $2–4 would wipe out the edge on that trade. So costs and slippage decide whether this EA makes money. Re-run the backtest with **real-tick data, variable spread, and +$0.30–0.50 slippage**.

---

## 4. What works on gold intraday (evidence)

**Peer-reviewed**
1. **Cai, Cheung & Wong (2001), J. Futures Markets**, COMEX gold intraday: "intraday patterns exert a profound impact" on volatility. Of 23 US releases, **employment reports, GDP, CPI, personal income** matter most ([CityU](https://scholars.cityu.edu.hk/en/publications/what-moves-the-gold-market(cb5f241d-cbf1-43c5-819a-a12813db32c4).html), [RePEc](https://ideas.repec.org/a/wly/jfutmk/v21y2001i3p257-278.html)).
2. **Elder, Miao & Ramchander (2012), J. Banking & Finance**, 2002–2008 intraday: the reaction is "both swift and significant". 8:30 ET releases (NFP, durable goods) matter most, and better-than-expected US data pushes gold **down**. Volatility and volume rise, with asymmetric effects ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378426611001968), [working paper](https://mountainscholar.org/bitstreams/21623442-a01d-45a6-879d-d645e781e52a/download)).
3. **Batten & Lucey (2007/2010)**, gold futures 10-min data: a **U-shaped** intraday volatility curve, a spike at the GLOBEX open, and price dependence limited to about 20 minutes, i.e. efficient at 20+ minutes ([SSRN 1008722 via ResearchGate](https://www.researchgate.net/publication/46527871_Volatility_in_the_gold_futures_market)).
4. **Batten, Lucey, McGroarty, Peat, Urquhart (2017)**, 5-min precious metals 2000–2015: significant intraday periodicity in returns, volatility, volume and spreads. Spreads have narrowed over time ([PMC5407636](https://pmc.ncbi.nlm.nih.gov/articles/PMC5407636/)).
5. **Xu, Bouri, Saeed, Wen (2020)**, commodity ETFs including gold: **intraday momentum** (early-session return predicts last-period return) exists ([PMC7480318](https://pmc.ncbi.nlm.nih.gov/articles/PMC7480318/)).

**Practitioner / broker (UNVERIFIED, marketing sources)**
- XAUUSD spread is about $0.15–0.20 normally and can blow out to "$1.50–$4.00+ per ounce" on CPI/NFP. They suggest a 60–120 s no-trade window, then trading the post-release pullback ([FXNX](https://fxnx.com/en/blog/why-gold-spreads-widen-during-news-how-trade)).
- Typical slippage: $0–0.30 in calm markets, $2+ on news spikes ([VT Markets](https://www.vtmarkets.com/en-mena/discover/gold-trading-slippage-explained-xau-usd-price-moves/)). Highest volume and tightest spreads in the London–NY overlap, 13:00–17:00 GMT ([Afterprime](https://afterprime.com/metals/xauusd)).
- About 45% of GC regular sessions are trend days; the London AM fix window is a range-bound "dead zone" ([Market Stalkers](https://marketstalkers.co.uk/blog/posts/market-profile-on-gold-futures-gc), own research).

**Evidence-based spike capture?** No peer-reviewed source found for a profitable retail "spike capture" (straddle) method after costs. The papers show the reaction is fast, which favours colocated HFT. The5%ers also bans news bracketing and trades within ±2 minutes of high-impact news. **Practical design implication:** add a news filter (flat or no new entries from −5 to +5 minutes around NFP/CPI/FOMC/GDP), prefer London–NY overlap entries, and test a "post-release pullback after spread normalises" module as a separate, separately-validated idea.

---

## 5. India legal reality (facts, not advice)

| Point | Fact | Source | Status |
|---|---|---|---|
| RBI Alert List date | "Updated as on November 19, 2025"; page fetched 21 Nov 2026; 95 entries | [rbi.org.in Id=4235](https://rbi.org.in/scripts/Bs_viewcontent.aspx?Id=4235); [PR 2025-26/1530](https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=61646) | VERIFIED |
| The5%ers on list? | **No** match for "5ers"/"5%ers" | same (text search) | VERIFIED |
| FTMO on list? | **Yes** (#13, ftmo.com/en) | same | VERIFIED |
| Other prop firms on list | FundedNext (#83), Smart Prop Trader (#82) | same | VERIFIED |
| Not listed ≠ authorised | List "is not exhaustive"; absence "should not be assumed" to mean authorised | same | VERIFIED |
| FEMA on ETPs | "resident persons are not permitted to undertake forex transactions on unauthorised ETPs"; liable to "penal action under FEMA" | [RBI FAQ, updated 28 Aug 2024](https://www.rbi.org.in/CommonPerson/English/scripts/FAQs.aspx?Id=3347) | VERIFIED (primary) |
| LRS | Only for permissible current/capital account transactions; **not** for "margins or margin calls to overseas exchanges"; limit USD 250,000/FY | RBI FAQ; [completetradersedge](https://completetradersedge.com/prop-firm-payouts-india-lrs-fema/) | VERIFIED |
| Is a prop **fee** permissible? | "Genuinely grey"; "no settled RBI ruling" for offshore retail prop firms; forex/CFD challenges "bump directly against the forex restrictions" | [completetradersedge](https://completetradersedge.com/prop-firm-payouts-india-lrs-fema/) (affiliate site) | **UNVERIFIED** (single source) |
| TCS on LRS | Threshold raised to **₹10 lakh/FY** (Budget 2025); above that, 20% for general purposes, creditable against tax | [Business Standard](https://www.business-standard.com/amp/budget/news/tcs-on-foreign-remittances-up-to-rs-10-lakh-none-on-foreign-education-loan-125020100857_1.html), [BusinessToday](https://www.businesstoday.in/personal-finance/tax/story/budget-2025-tcs-threshold-for-foreign-remittances-hiked-to-rs10-lakh-what-it-means-for-you-462983-2025-02-01) | VERIFIED. Budget 2026 changes not checked. |
| Tax head | Payouts "best classified as business income" → ITR-3; foreign income in Schedule FSI, wallet balances in Schedule FA; bring funds home within ~30–60 days | CA Niyati Shah in [BusinessToday, Aug 2025](https://www.businesstoday.in/personal-finance/tax/story/as-indian-trader-earning-from-prop-firms-abroad-how-do-i-stay-tax-compliant-avoid-red-flags-487537-2025-08-02) | UNVERIFIED (one expert opinion) |

Internal note: CLAUDE.md rule 4 says b7 trades Akhil's own money "through a registered broker's API". A foreign CFD prop-firm account is a different route. That is Akhil's decision, ideally after a CA/FEMA consultation.

---

## 6. Best free AI models (Nov 2026), verified on provider pages today

**Provider limits verified**
- **OpenRouter `:free`**: 20 req/min; **50/day** if under 10 credits ever bought, 1,000/day at 10+ (a one-time purchase, i.e. trial-credit-like) ([docs](https://openrouter.ai/docs/api-reference/limits)). The live API lists **14 free models** today, including `nvidia/nemotron-3-ultra-550b-a55b:free`, `google/gemma-4-31b-it:free` and `openrouter/free` ([api/v1/models](https://openrouter.ai/api/v1/models), queried directly). No Qwen/DeepSeek coder `:free` today.
- **Groq**: `openai/gpt-oss-120b`, `gpt-oss-20b`, `qwen/qwen3.8-27b` at 30 RPM, 1K RPD, 8K TPM, 200K TPD ([rate-limits](https://console.groq.com/docs/rate-limits); the page calls these base plan limits). Groq's training-data policy was not checked: UNVERIFIED.
- **Gemini API free tier**: "Free of charge" for Gemini 3.8 Flash, 3.6 Flash, 3.5/3.1 Flash-Lite, **2.5 Pro**, 2.5 Flash and Gemma 4. 3.1 Pro Preview is not free. Free-tier data **is used to improve products**; paid-tier data is not ([pricing](https://ai.google.dev/gemini-api/docs/pricing)). The RPM/RPD page is blocked to fetchers, so per-model limits are UNVERIFIED.
- **Hugging Face licences** (hub metadata): Kronos-small **MIT**, 24.7M params ([hf](https://hf.co/NeoQuasar/Kronos-small)); TimesFM 2.5 **Apache-2.0**, 231M ([hf](https://hf.co/google/timesfm-2.5-200m-pytorch)); Chronos-2 **Apache-2.0**, 119.5M ([hf](https://hf.co/amazon/chronos-2)); Chronos-Bolt-small Apache-2.0 ([hf](https://hf.co/amazon/chronos-bolt-small)); Moirai-2.0 **CC-BY-NC-4.0** ([hf](https://hf.co/Salesforce/moirai-2.0-R-small)); **FinBERT is CC-BY-NC-SA-4.0** ([hf](https://hf.co/ProsusAI/finbert)), non-commercial.

**Recommendations (one per task)**
| Task | Pick | Why | Fallback |
|---|---|---|---|
| (a) Headline/news sentiment for gold | **Groq `openai/gpt-oss-120b`** | Free, 1K req/day is enough for a headline feed, open weights, fast. Prompt for a "USD-real-yield direction → gold" label. FinBERT is non-commercial and Moirai too, so both are out for a product. | Gemini 3.8 Flash free tier (only for public headlines, since free-tier data is used for training) |
| (b) MQL5 code review | **Groq `openai/gpt-oss-120b`** for proprietary EA code | Keeps code off Gemini's free tier, which trains on inputs. **Limit:** 8K TPM means reviewing about one file chunk per minute. | Gemini 2.5 Pro free tier for non-secret files (large context); OpenRouter `nemotron-3-ultra-550b:free` (50/day) |
| (c) Time-series forecasting | **amazon/chronos-2** (Apache-2.0) | Permissive licence for a sold product, small enough for CPU in GitHub Actions, most downloaded TS model on the Hub. Use it as a volatility/regime **feature**, not a direction signal. | Kronos-small (MIT, finance K-line specific; its paper [arXiv 2508.02739](https://arxiv.org/abs/2508.02739) is the authors' own claim). Exclude Moirai (NC). TimesFM 2.5 is also fine (Apache-2.0). |

Caveat: no source found shows these foundation models add trading edge on H1 gold after costs. Backtest any such feature out-of-sample before use.

---

## 7. Suggested next validation steps (from the data above)
1. Ask The5%ers support in writing whether the EA is approvable (needs Akhil, his account).
2. Re-run the backtest on real ticks with variable spread, +$0.30–0.50 slippage and a ±5 min news blackout. Report long and short results separately, by year 2022–2026, including 30 Jan 2026.
3. Forward-test on a demo for at least 3 months and compare against the backtest's +0.1R/trade.
4. Get a CA/FEMA view on paying an offshore CFD prop firm before spending the ₹10,000.

*Compiled 2026-11-21 by research subagent. Not committed.*

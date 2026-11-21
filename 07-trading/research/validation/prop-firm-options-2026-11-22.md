# Prop-firm options for an own MT5 gold EA (India, budget about ₹10,000)

Checked: 22 Nov 2026. Analyst run, research only. Nothing was bought, signed up for or logged into.
Rate used: ₹92.97 per US$ (RBI/FBIL reference rate, 20 Nov 2026, rbi.org.in home page). Budget ₹10,000 ≈ US$107.

**Method.** Each key fact comes from the firm's own page fetched today plus one other source (a second page, a review site or Trustpilot). A fact with only one source is marked **UNVERIFIED**. Rows also marked "(agent)" were gathered by a Firecrawl research agent from the firm's own pages today. I spot-checked them but did not re-read every one; treat them as one source. This is not legal or tax advice. It only states facts.

**Client EA profile.** XAUUSD, H1–H4 limit orders, 3–5 trades/day, a stop loss on every trade, max 3 open positions, 0.25–0.40% risk per trade (worst case about 1.2% open risk), sometimes holds over weekends, avoids news ±2 h.

---

## Step 1: RBI Alert List (exclusion screen)

- Source: https://rbi.org.in/scripts/Bs_viewcontent.aspx?Id=4235, fetched today. Heading: "Alert List (Updated as on November 19, 2025)". The page footer reads "Website last updated date: Nov 21, 2026", so there has been no newer list. **95 entities.**
- Second source: completetradersedge.com/rbi-alert-list ("Entities listed 95", page checked 18 Aug 2026). FXNX also cites 95 as of Nov 2025.
- RBI says the list "contains names of entities which are neither authorised to deal in forex under ... FEMA" nor to run a forex trading platform. RBI also says the list is not exhaustive (calcguru.in summary). Not being on it does not mean a firm is authorised.

**Prop firms and related brands on the list (verbatim rows):**

| # | Entity | Effect |
|---|---|---|
| 13 | FTMO, https://ftmo.com/en | **Excluded** |
| 82 | Smart Prop Trader | **Excluded** |
| 83 | FundedNext, https://fundednext.com | **Excluded** |
| 81 | Think Markets | Parent of ThinkCapital, so **excluded** |
| 46 / 47 | **MetaTrader 4 / MetaTrader 5** (metatrader4.com / metatrader5.com) | ⚠️ The MT5 platform brand itself is on the list. See Risks. |

FundingPips, The5ers, E8, FXIFY, Audacity, Alpha Capital, Blue Guardian, Maven, Goat Funded Trader, Funded Trading Plus, Instant Funding, Hola Prime, Lark, Fintokei and FundingTraders are **not** on the list (checked against the full 95-row text).

---

## Step 2: Firm-by-firm screen

Hard filters for this client: (a) not on the RBI list, (b) India accepted, (c) MT5, (d) a fully automated **own** EA is allowed, (e) plan ≤ about $107.

### Passed all filters

#### E8 Markets (E8 Pro 1-Step)
- **EA:** "you can use any EA (Expert Advisor) as long as we don't see multiple users executing the same trades/strategy." (help.e8markets.com/en/articles/6929927). The E8 Pro page says "Expert Advisors and trade copiers allowed" (e8markets.com/e8-pro). Second source: propvator.com/blog/e8-markets-expert-advisors. No approval needed. One strategy per user. Bans: hedging across accounts, team/signal trading. VPS: "Not stated" (e8 policy page + massivegrid.com, 22 Oct 2026) → **ask support in writing**.
- **India:** accepted. India appears only under "Allocation limits: E8 One only up to $200,000", and those countries "can purchase only E8 Pro (all sizes)..." (help.e8markets.com/en/articles/5514278, updated 1 Oct 2026). Confirmed by the agent's reading of the same page.
- **MT5:** listed (help.e8markets.com/en/articles/9799834). "US clients can utilize only TradeLocker and MatchTrader." Second source: propfirmmatch.
- **Cheapest:** $5K, 1 step, **$28 sale / $32 list (≈ ₹2,603 / ₹2,975)** (e8markets.com/e8-pro). Second source: propfirmmatch lists the "E8 Pro - 1-Step 5K" at $23.80 with its own coupon.
- **Rules:** 8% target. Only 2% of the initial balance per day counts toward the target, so the target takes at least 4 days (agent). **2.5% daily** drawdown. **8% static** max ("never trails"). No minimum days, no time limit; one closed trade every 60 days. News "unrestricted"; weekend holding "Allowed". Metals leverage 1:15 (agent, UNVERIFIED second source).
- **Payout:** daily requests, 1% minimum profit. 80% split, or 100% with a paid add-on. Only 50% of profits can be requested; the rest is a buffer (agent + rizetrade.com). Methods: Rise (cash or crypto) and WorkMarket. Aeropay is US-only. Rise availability in India: **UNVERIFIED**.
- **Trust:** Trustpilot shows **"This company's rating is unavailable due to a breach of our guidelines"**, 3,308 reviews, profile merged (trustpilot.com/review/e8markets.com, today). Years operating and published payout totals: UNVERIFIED.

#### The5ers (High Stakes, 2-step)
- **EA:** FAQ: "You can use any EA you have... the trader must own the source code of the EA." Banned: copying others' signals, tick scalping, latency/reverse/hedge arbitrage, HFT, emulators (the5ers.com/faqs/can-i-use-an-ea...). **Terms (last update 28 Oct 2026): "User shall notify the Company in writing and obtain written approval from the Company prior to using any Automated Trading Software"**. The Company "may require advance testing". Third-party software is prohibited (the5ers.com/terms-and-conditions). Second sources: massivegrid.com and copygram.app say the same. VPS: not stated.
- **India:** not in the Terms' "Forbidden Territory" list (same page). Second source: propfirmmatch's India list. This is a "not listed" result, not an explicit yes.
- **MT5:** "Platform: Mt5 Hedge" (the5ers.com/high-stakes).
- **Cheapest:** **$2.5K for $19 (≈ ₹1,766)** (the5ers.com/high-stakes). Second sources: propfirmbridge.com ("High Stakes New $2,500 account is $19") and an Instagram post from 30 Sep 2026 ("$5K account: $35"). The $5K price is therefore second-source only (≈ ₹3,254).
- **Rules:** Step 1 target 10%, Step 2 5%. **5% daily**, **10% max**; the Terms mention a midnight balance/equity basis, and static vs trailing is not stated on the page (UNVERIFIED). Minimum 3 profitable days per step (each ≥0.5%). No time limit. Leverage 1:100; gold-specific leverage UNVERIFIED. No trades 2 minutes before or after high-impact news, which the EA's ±2 h filter already covers. "Overnight and weekend actions are allowed."
- **Payout:** split 80–100% as the account scales. First payout timing and payout methods: **UNVERIFIED** (not on the pages fetched).
- **Trust:** Trustpilot **4.7 / 43,739 reviews** (today). Operating since 2016 (tradernotion.com; the firm's own date is UNVERIFIED).

#### FXIFY (Two Phase Classic)
- **EA:** "allowed ... upon review by our support team and **pre-approval**... use of an EA without pre-approval may... lead to account suspension" (fxify.com/faqs/.../can-i-use-an-expert-advisor..., modified 18 Jun 2026). Banned: HFT, reverse/group hedging, latency and statistical arbitrage, "using the same EA from the same company" (herd trading), high-leverage news trading (agent). Second source: thepropfirmguide.com.
- **India:** accepted; not on the "countries not accepted" list (agent, fxify.com/faqs/all-faqs/what-countries-are-accepted). Second source: UNVERIFIED.
- **MT5:** yes (MT5, DXTrade, TradingView) (agent).
- **Cheapest:** $5K, 2 steps, **$59 list (≈ ₹5,485)**; a sale price of $38.35 was shown today (agent). Second source for $59: myfxbook.com/prop-firms ("starting at $59 for a $5,000 account").
- **Rules:** 5% + 5% targets. **4% daily** from the previous day's closing balance, breached on equity. **10% static** max. Minimum 4 days, no time limit. News allowed on this plan; weekend holding allowed. Gold leverage: not stated (agent says "up to 30:1" general, commodities 2:1 on the rules page; conflicting, UNVERIFIED).
- **Payout:** up to 100% split, every 14 or 30 days, each payout reviewed. Methods: bank wire, crypto, Rise. 2.5% fee (minimum $25 for Rise/wire, $5 for crypto) (agent).
- **Trust:** Trustpilot **4.3 / 6,711** (today).

### Passed, but with a serious catch
- **FundingPips.** Own EA: "Full automation is permitted on your own EA, provided you can supply proof of ownership" (source code, version history, or a live call). A compiled file alone is not proof. **But:** "Connecting to a VPN or VPS while accessing your trading account is not permitted." The EA would have to run on a home PC 24/5. The firm also watches the "region of your IP address". Weekend holding on Master accounts needs the Swing add-on (agent). India accepted: only Iran, Vietnam and UAE are restricted. The $5K price is not on the firm's page; lunefi.com says $29 (UNVERIFIED). Trustpilot **4.5 / 76,012**. Source: help.fundingpips.com articles 34505029138449 and 44390730743825; second source massivegrid.com (VPS) and propvator (EA).
- **Audacity Capital (Ability, 2-step).** $5K for **$25 promo / $49 list (≈ ₹2,324 / ₹4,556)**. Second sources: propfirmmatch ($49) and thetrustedprop ("Allowed only if you personally own/developed the EA"). Targets 10% and 5%. Daily 7.5%/5% and max 15%/10%, static on initial balance. Minimum 4 days each phase. MT5. Founded 2012 (own page). India not restricted (agent). Weekend holding allowed; no trading ±3 min around high-impact news. EA: "EAs are allowed if they follow our prohibited-strategy rules". **Catch:** the same page bans "Automated Multi-Trade Activity ... without the trader actively overseeing or managing each one". A fully hands-off EA could be read as a breach, so get written OK first. Trustpilot: **rating unavailable (guideline breach), 304 reviews.**
- **Goat Funded Trader.** Own EA only, and proof can be requested. **VPN/VPS prohibited while trading.** India not restricted (agent). Trustpilot rating **unavailable (guideline breach)**, 4,373 reviews, profile shown as "Wishes Tower".
- **Funded Trading Plus.** Own EA allowed. MT5. India not on the prohibited list. Gold 1:20. Weekend OK. The cheapest entry is $4 up front + **$179 activation on pass ($183 total, over budget)** (agent). Payout only via crypto/Rise. Trustpilot rating **unavailable (guideline breach)**, 2,674 reviews.
- **Instant Funding.** "First-party EAs you build yourself are allowed". MT5. **India status not stated** on its page (agent), so UNVERIFIED. The visible price was $459, over budget.

### Excluded
| Firm | Reason (own page, fetched today) | Second source |
|---|---|---|
| FTMO, FundedNext | On RBI Alert List (#13, #83) | completetradersedge (95-row list) |
| ThinkCapital | Parent Think Markets on the RBI list (#81). No MT5; "the ThinkMarkets app does not support automated trading" (agent) | — |
| Alpha Capital Group | EA only "for risk management and trade assistance", MT5 only (alphacapitalgroup.uk blog) | massivegrid.com |
| Maven Trading | "EAs and automated trading are prohibited" (agent, maventrading.com/faqs). Trustpilot rating unavailable (breach) | — |
| Blue Guardian | "Fully automated systems, AI and bots are not allowed" (agent). Trustpilot rating unavailable (breach) | — |
| FundingTraders | EAs only "focused on risk management" (agent) | — |
| Hola Prime | **India restricted** (agent: India "among currently restricted countries") | holaprimemarkets.com FAQ: "does not provide services to ... India". Trustpilot 4.6 / 4,392 |
| Fintokei | **India restricted** ("India" in "Who can join" list) | fintokei.com home page + propvator |
| Lark Funding | **No MT5** (DXTrade, cTrader, Match-Trader) (agent) | — |
| Topstep / Apex | Futures firms, no MT5. Apex bans fully automated systems on funded accounts (massivegrid.com) | — |
| India-focused firms | None verified today. Atmos Funded advertises UPI for India (atmosfunded.com, own blog only) → **UNVERIFIED, not assessed** | — |

---

## Comparison (passed firms)

| Firm | RBI list | EA rule | Cheapest plan | Daily / max loss | Payout | Trustpilot |
|---|---|---|---|---|---|---|
| The5ers | No | Own EA, **prior written approval** | $2.5K, $19 (₹1.8k) | 5% / 10% | 80–100%; timing and methods UNVERIFIED | 4.7 (43.7k) |
| E8 Markets | No | Any EA, no approval, one strategy per user | $5K, $28–32 (₹2.6–3.0k) | 2.5% / 8% static | Daily, 80% (100% add-on), 50% buffer | Rating hidden (breach) |
| FXIFY | No | EA **pre-approval** | $5K, $59 ($38 sale) (₹3.6–5.5k) | 4% / 10% static | 14 or 30 days, up to 100%, 2.5% fee | 4.3 (6.7k) |
| Audacity | No | Own EA; bans unattended multi-trade | $5K, $25–49 (₹2.3–4.6k) | 7.5%→5% / 15%→10% static | Bi-weekly, first at 14 days, 75–90% | Rating hidden (breach) |
| FundingPips | No | Own EA with proof; **VPS banned** | $5K, ~$29 (UNVERIFIED) | 5% (3% option) / 10% | Weekly, bi-weekly or on demand, 60–100% | 4.5 (76k) |

## Step 3: Top 3 for this client

1. **The5ers High Stakes $2.5K ($19).** It has the strongest verified trust signal (4.7 from 43.7k reviews). Your own EA is allowed once you get written approval. Weekend holds are allowed, and the 2-minute news rule sits inside the EA's own ±2 h filter. The cheapest entry leaves room for 4–5 attempts within ₹10,000. Get approval **before** buying.
2. **E8 Markets E8 Pro $5K ($28–32).** It has the most permissive EA rule (no approval), a static 8% max loss, and no news or weekend limits. India is explicitly listed for E8 Pro. The 2.5% daily limit is fine for about 1.2% worst-case open risk. Against it: the Trustpilot rating is hidden for a guideline breach, only 50% of profit can be requested, and the VPS policy is unstated.
3. **FXIFY $5K ($59, $38 on sale).** EA allowed after pre-approval. Rules are static (4% daily, 10% max). Weekend and news are allowed. Trustpilot is 4.3 from 6.7k reviews with no warning. It costs more per attempt, and the gold leverage figures conflict.

Alternatives: Audacity is cheap and static, but its ban on unattended automation and its hidden Trustpilot rating count against it. FundingPips is fine only if the EA can run on a home PC (no VPS).

## Risks, stated plainly
1. **FEMA/RBI.** RBI's FAQ says a resident cannot remit margin under LRS for online forex trading: "All other transactions which are otherwise not permissible under FEMA and those in the nature of remittance for margins or margin calls to overseas exchanges / overseas counterparty are not allowed under the Scheme" (rbi.org.in/commonman FAQ Id=3347). RBI's LRS FAQ also lists "Remittance for trading in foreign exchange abroad" as not allowed (FAQ Id=1834). theindustryspread.com says a simulated account bought for an evaluation fee "is not obviously a margin remittance". That is a grey area, not a clearance. Payouts would arrive as foreign remittances, and their tax treatment is UNVERIFIED.
2. **MT5 itself is on the RBI Alert List** (#47, metatrader5.com). Every option here runs on MT5.
3. **Firms can deny payouts.** All of them reserve discretion (prohibited-strategy reviews, IP checks, proof-of-EA calls). FundingPips: violations "may be terminated immediately without prior notice". The5ers: approval is "at the Company's sole discretion". Shut-downs in 2026: FundingTicks (Jan 2026) and MyFundedFX/SeacrestFunded (6 Feb 2026) (tradernotion.com, single source, UNVERIFIED). None of the firms above appeared in that list.
4. **Trustpilot guideline-breach banners** today on E8, Maven, Blue Guardian, Goat, Funded Trading Plus and Audacity. The banner means the rating is hidden. It does not by itself prove misconduct.
5. **Prices and rules change often.** Several prices above are promotions shown today. Re-check on the day of purchase.
6. **Card or forex charges** on a $19–59 payment from an Indian card: UNVERIFIED.

# P5 · b5 Deals ("Bazaar Bay"): plan

Planning agent P5 · 2026-10-13 · Sources: research `00-hq/research/github/a5-kits-deals.md` and live web checks (listed at the end). Rupee figures marked *est.* are my own estimates, not quotes.

## 1. Verdict

b5 earns money in three ways. **(a) Commission:** affiliate links on a Telugu deals Telegram channel and a weekly newsletter, starting with EarnKaro (₹10 minimum withdrawal) and adding Amazon Associates later. **(b) Kit sales:** a free calculator site that sends visitors to b3's ₹199–499 tax and SIP kits. These kits are our own product, with about 95% margin, and are the best rupees in this world. **(c) Ads:** AdSense, but only once we own a domain and have traffic.

The plan in one line: build the tools in English and Telugu, grow the audience on Telegram, and earn mostly from Kits.

We do not compete head-on for "SIP calculator", because Groww, ClearTax, ET Money and the banks already hold page one. We go after the Telugu and long-tail searches they ignore.

| ₹ per month (cash received) | Low | Likely | High |
|---|---|---|---|
| Month 1 (Nov 2026) | 0 | 0 | 300 |
| Month 3 (Jan 2027, tax season starts) | 0 | 800 | 3,000 |
| Month 6 (Apr 2027, new FY and ITR season) | 500 | 3,500 | 12,000 |
| Month 12 (Oct 2027) | 2,000 | 10,000 | 35,000 |

**Biggest risk:** Google treats finance as "Your Money or Your Life", so a new site may get almost no search traffic for 4–6 months. Telegram therefore has to carry the early months. A second risk is regulatory drift: one "best fund to buy" post or a guaranteed-returns line would put us on the wrong side of SEBI or ASCI. Section 3b sets the guardrails.

## 2. Customer & offer

Readers pay nothing. The money comes from merchants (as commission), from Google (as ads), and from Kit buyers.

| Rung | What the reader gets | Price | Who pays us |
|---|---|---|---|
| 0 | 10 calculators in English and Telugu: no login, works offline, shareable result link | Free | — |
| 1 | Telegram channel: 3–5 checked deals a day with Telugu copy, plus 1 money tip a week | Free | Merchant commission (EarnKaro, Cuelinks, later Amazon) |
| 2 | Weekly newsletter: tax deadline reminders, the best deals of the week, one explainer | Free | Kit sales and Cuelinks/EarnKaro links (no Amazon links in email; see 3b) |
| 3 | b3 Kit: "New-regime vs old-regime tax planner FY 2026-27" Sheet | ₹199 | The reader |
| 4 | b3 Kit bundle: tax planner, SIP/goal planner and loan prepayment planner | ₹499 (launch price ₹399) | The reader |
| 5 | Credit-card offers (through EarnKaro) on the calculator pages, with fees shown | Free | Issuer's commission, paid via EarnKaro |

**Why buy now:** the tax calendar sets the timing. Proof submissions for salary TDS fall in Jan–Feb, the new FY and regime choice come in April, and ITR filing runs Jun–Jul. The calculator shows the number; the Kit gives a year-long plan built on it.

**Competitors (all free to readers):**

| Alternative | Price to reader | How they earn | Our gap |
|---|---|---|---|
| Groww calculators (groww.in/calculators) | ₹0 | MF and broking | No Telugu; they push their own funds |
| ClearTax income-tax calculator | ₹0 | ITR filing plans | No Telugu; they upsell filing |
| BankBazaar / Paisabazaar calculators | ₹0 | Card and loan referrals | No Telugu; heavy lead capture |
| DesiDime / "loot deals" Telegram channels | ₹0 | Affiliate | English or Hindi, noisy; no Telugu-first channel found |

## 3. Unit economics

The "customer" here is an audience unit. Hosting stays at ₹0 until a domain is bought.

| Engine | Assumption (*est.*) | ₹ per month |
|---|---|---|
| Telegram, per 1,000 members | ~40 clicks/day, so 1,200/mo; 3% buy; AOV ₹1,000; ~4% commission | ≈ ₹1,400 |
| Calculator site, per 10,000 visits: Kits | 0.2% buy a ₹299 average kit (20 orders); minus Razorpay ~2% and GST if registered | ≈ ₹5,800 |
| Calculator site, per 10,000 visits: cards | 0.3% apply, 30% approved, so 9 cards at ~₹350–750 each | ≈ ₹4,500 |
| Calculator site, per 10,000 visits: AdSense | RPM unknown for a new Indian finance site; assume ₹50–150 per 1,000 views | ≈ ₹500–1,500 (only after domain and approval) |

**Cost to serve:** ₹0. The site is static and sends every calculation to the browser. The bot runs on a GitHub Actions cron or a Cloudflare Worker. The newsletter is on a free tier. Gross margin is about 100% on affiliate income and about 95% on Kits.

**Break-even:** there are no running costs to recover. The first spend is a **.in domain**, at whatever price the registrar shows that day. It is needed because AdSense and a proper Search Console domain property want a site we own, not a `pages.dev` or `netlify.app` subdomain. **Buy it when the site reaches 1,000 visits a month or makes its first Kit sale, whichever comes first.** The second spend is beehiiv or Kit paid, and only above about 2,500 or 10,000 subscribers.

**Where the free tiers run out:**

| Service | Free limit (checked Oct 2026) | When we hit it |
|---|---|---|
| **Cloudflare Pages** (recommended for this site) | 500 builds/mo, unlimited static bandwidth, Functions on the Workers 100k requests/day | Effectively never at our scale |
| Netlify (new accounts since 4 Sep 2025) | 300 credits/mo (about 15 GB, or ~20 production deploys); **site pauses** when used up | A traffic spike could take the site offline, so keep Netlify for BotBhai only |
| GitHub Actions (public repo) | Free minutes | Bot cron every 30 minutes is fine |
| Newsletter: Kit free / beehiiv Launch | 10,000 / 2,500 subscribers (beehiiv free has no ad network) | Start on **Kit free** for headroom |
| EarnKaro | ₹10 minimum withdrawal, NEFT in 6–10 days | Never a limit |
| Amazon Associates IN | ₹2,500 payout threshold; **3 qualifying sales in the first 180 days or the account closes**; Creators API needs **10 sales in the last 30 days** | This is why Amazon waits (see 4) |
| AdSense | Pays in USD: $10 triggers PIN verification by post, $100 triggers payment | Month 6 or later |

### 3b. Compliance guardrails (rules every agent follows)

| Area | Rule as it stands now | What we do |
|---|---|---|
| **SEBI finfluencer rules** (2024–25) | SEBI-regulated entities cannot associate (money, referrals, tech) with unregistered persons who give securities advice or make return or performance claims. Educators must not use market price data from the last 3 months. | No stock or fund tips, no named-fund returns, no "best SIP to buy". Calculators use a user-entered rate labelled "assumed, not guaranteed". No broker or demat referral links until a CA or lawyer confirms. |
| **Mutual fund distribution** | Earning MF commission needs NISM Series V-A plus an **AMFI ARN**, and distributors must disclose commissions. | **FLAG: we have no ARN, so no MF affiliate or commission links of any kind.** If Akhil wants this later, it is a separate decision: NISM exam, then ARN, then KYD. |
| **RBI credit cards** | The issuer is responsible for its agents' conduct. No unsolicited cards. Interest-bearing EMI cannot be called "no-cost". | Card offers only through EarnKaro/BankKaro (the issuer's channel). Show annual fee, joining fee and eligibility, link to the issuer's terms, and never write "free" unless it is lifetime-free. |
| **RBI Digital Lending Directions 2025** | Multi-lender LSPs (from 1 Nov 2025) must show all matching offers without bias, with APR. | **No personal-loan or BNPL affiliate links.** The EMI calculator stays neutral, with no "apply for a loan" button. |
| **IRDAI** | Selling insurance needs a registered intermediary. | No insurance affiliate links. |
| **ASCI influencer guidelines** | Label every paid or affiliate post with #ad, #collab, #sponsored, #promo or #partnership, in the first two lines and in the post's language. A bio disclaimer is not enough. Since Addendum 2 (Apr 2025), finance influencers who give advice must show SEBI registration and qualifications; unregistered creators may only post generic, non-technical content. | Every Telegram and newsletter deal line starts with **"#ad · affiliate link / అనుబంధ లింక్"**. Our money content stays generic education. |
| **Amazon Associates** | Price shown must be current; links not allowed in email (verify against the IN Operating Agreement at sign-up). | Prices carry "₹X as of 13 Oct, 6 pm; may change". Amazon links on Telegram and the site only, never in the newsletter. |
| **DPDP Act and Rules 2025** (notified 14 Nov 2025; most duties from ~May 2027) | Plain-language notice, consent, easy withdrawal, breach reporting. | Collect email only, via double opt-in. Privacy notice in English and Telugu. One-click unsubscribe. No member data from Telegram. |
| **Tax and GST** | Affiliate and AdSense income is business income. GST registration above ₹20L turnover. AdSense counts as an export of services. Indian affiliates deduct TDS on commission. | Track everything in a b6 or FinOps sheet. Not a concern until revenue is meaningful; confirm with a CA. |
| Data sources | Do not scrape Amazon, Flipkart or price trackers (Discount-Bandit and PriceBuddy are AVOID). | Deals come from human curation plus EarnKaro's Magic Tool, then the Creators API once eligible. |

**Flipkart:** public sign-ups to Flipkart's own affiliate programme are reported as discontinued. Use **Cuelinks** (Flipkart CPS up to ~7%, **30-minute cookie**, 60-day validation, social allowed organically, no FB ads) or **EarnKaro**. Ask Cuelinks to confirm Telegram is allowed before relying on it.

## 4. Go-to-market

**Sequencing matters:**
1. Start with **EarnKaro**, which has no qualifying-sales clock.
2. Sign up for Cuelinks in week 2.
3. Apply to **Amazon Associates only once the channel has about 300 members**, so the 3-sales-in-180-days clock does not run out on an empty channel.
4. Apply for the Creators API after reaching 10 sales in 30 days.

**First 10 "customers"** (10 tracked affiliate purchases, or 1 Kit sale). Daily quota: 20 minutes.

| Step | Channel | Action | Daily minutes |
|---|---|---|---|
| 1 | Personal network | Share the channel link once in 3–5 Telugu WhatsApp groups Akhil already belongs to (family, college, colleagues), with a personal note rather than spam. | 5 (week 1 only) |
| 2 | Telegram | Akhil picks 3 deals (from Amazon/Flipkart deal pages in his own browser) and pastes the links into a sheet. The agent converts them through EarnKaro, writes Telugu copy with the #ad line and price timestamp, and schedules the posts. | 10 |
| 3 | Calculator site | Every result has "Share on WhatsApp" with a prefilled Telugu message and a site link (no tracking pixels). | 0 (built in) |
| 4 | Reddit (r/telugu, r/hyderabad, r/IndiaTax) and Quora (Telugu) | Answer genuine tax or EMI questions with the calculator link where it truly helps, disclose that it is our site, follow each sub's rules. | 5 |
| 5 | Newsletter | Footer of every channel post and calculator: "Weekly tax reminders, 1 email". | 0 |

**Group script (Telugu):** "Free Telugu tax/EMI calculator, no login; daily checked deals on Telegram, marked #ad. Join if useful: [link]."

**10 → 100:** swap shout-outs with 2–3 small Telugu channels in other niches (jobs, exam prep), post a weekly "tax in 60 seconds" Telugu image, publish 2 long-tail pages a week ("₹40L home loan EMI", "₹15L salary tax in Telugu"), and run seasonal pushes in Jan (proof submission), Apr (regime choice) and Jul (ITR deadline).

### The first 10 calculators

No paid keyword tool is affordable, so the ranking below is an *estimate* from SERP crowding and competitor coverage. Quest W2-3 checks it with free Google Trends and Keyword Planner ranges, then with Search Console.

| # | Calculator | Why it is in the top 10 | Kit cross-sell |
|---|---|---|---|
| 1 | **Income tax: new vs old regime, FY 2026-27** | Highest intent. Slabs unchanged by Finance Bill 2026. 87A to ₹12L with marginal relief; engine is india-tax-guru (MIT). | Tax planner ₹199 |
| 2 | **EMI** (home, car, personal; same engine, 3 pages) | The largest evergreen query family. | Loan prepayment planner |
| 3 | **SIP** (plus step-up) | Huge volume. Show "assumed rate, not guaranteed". | SIP/goal planner |
| 4 | **Salary in-hand (CTC to take-home)** | Strong Hyderabad IT audience; feeds the tax page. | Tax planner |
| 5 | **FD** (bank and senior citizen) | Large, older Telugu audience. | — |
| 6 | **PPF** | Tax-saving season. | Tax planner |
| 7 | **HRA exemption** | Old-regime proof season (Jan–Feb). | Tax planner |
| 8 | **GST** (add/remove GST) | Huge volume from small traders; easy page. | — |
| 9 | **Gratuity** | Job switchers; Payment of Gratuity formula. | — |
| 10 | **RD** (or Sukanya Samriddhi if Trends ranks it higher) | Small savers. | SIP/goal planner |

Every page has: an English path at `/x` and a Telugu path at `/te/x` with hreflang; FAQ schema; a "formula and source" box citing incometaxindia.gov.in and the Income-tax Act 2025 section alongside the old 1961 number; a "last verified" date; no ads above the result.

## 5. Build plan

Repo: `05-deals/src/site` (Astro, Cloudflare Pages), `05-deals/src/bot` (deal poster), `05-deals/src/content` (posts and newsletter drafts), `05-deals/docs`. The tax engine is shared with b3 at `05-deals/src/site/src/lib/tax/` with the MIT attribution kept. **ADOPT** picks from a5: Astro, india-tax-guru, grammY/aiogram (or plain Bot API calls), python-amazon-paapi (later), Kit free (in place of listmonk for now).

**Week 1 (by 20 Oct)**

| id | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| b5.W1.1 | Site skeleton | Approve the name and Telugu brand line (5 min) | Astro project in Codespaces; `fin.ts` with SIP/EMI/tax from a5; vitest fixtures for ₹12.75L, ₹13L and ₹25L | `npm test` green in Actions; ₹13L gives ₹26,000 |
| b5.W1.2 | Deploy | Connect GitHub to Cloudflare Pages, free (15 min) | Build config, `_headers`, privacy page (English and Telugu) | Live at `*.pages.dev`, Lighthouse ≥ 90 on mobile |
| b5.W1.3 | Telegram channel | Create a public channel and a BotFather bot; store the token as a GitHub secret yourself (15 min) | `src/bot/post.py`: reads `queue.csv`, posts at set times, refuses any post without "#ad" | Test post with disclosure appears |
| b5.W1.4 | EarnKaro | Sign up, add bank details yourself (15 min) | Write the daily "paste 3 links" sheet template and Telugu copy rules | First converted link posted |

**Weeks 2–4 (by 10 Nov)**

| id | Quest | CEO | Agent | Done-check |
|---|---|---|---|---|
| b5.W2.1 | Calculators 4–7 (salary, FD, PPF, HRA) in English and Telugu | Read 2 Telugu pages for naturalness (20 min) | Pages, FAQ schema, fixtures against bank and IT-dept examples | Fixtures pass; Telugu reviewed |
| b5.W2.2 | Search Console | Verify the site in Search Console (10 min) | Sitemap, hreflang | Sitemap "Success" |
| b5.W2.3 | Keyword check | Open Google Trends and compare the 10 names; screenshot (15 min) | Re-rank the list and record it in `05-deals/docs/keywords.md` | List frozen |
| b5.W3.1 | Newsletter | Kit free signup (15 min) | Double opt-in form on the site, DPDP notice, first 3 issues drafted | First issue sent to ≥ 20 people |
| b5.W3.2 | Cuelinks | Apply, and ask support about Telegram (15 min) | Add Flipkart deals to the queue | Approved |
| b5.W4.1 | Calculators 8–10 plus the Kits CTA | Approve the Kit CTA copy (10 min) | GST, gratuity and RD pages; CTA linking to b3's Razorpay page | 10 calculators live |

**Month 2 (Nov 10 – Dec 10)**: 2 long-tail pages a week; a card-offers box on salary and tax pages (EarnKaro, fees shown) after Akhil approves; channel cross-promos; **Amazon Associates sign-up once the channel has ≥ 300 members** (CEO, 30 min; add the channel URL and site as properties).

**Month 3 (Dec 10 – Jan 10)**: domain purchase if the gate is met, moving the site to it with 301s; AdSense application (CEO, 20 min); a January "proof submission" campaign (HRA, 80C, Telugu explainers); Creators API wrapper (`python-amazon-paapi`, IN) wired in once at 10 sales/30 days, so the bot fetches live prices and the timestamp rule is met automatically.

## 6. Agent swarm

These replace the generic `b5.*` lean team in `00-hq/agents/registry.js` when b5 goes live. Proposed specs only; the registry is not edited here.

```js
A({ id: "b5.calc", name: "Calculator Builder", unit: "b5", team: "tech", mission: "Build/maintain the 10 calculators (EN+TE) on one Astro template.", trigger: { event: "quest" }, runs_as: "claude", tokens: 12000, kpi: "10 pages live by 10 Nov", validator: { name: "Calculator Tester", checks: ["vitest fixtures 12.75L/13L/25L pass", "matches official formula", "no result above-the-fold ad"] } }),
A({ id: "b5.taxrules", name: "Tax Rules Watcher", unit: "b5", team: "research", mission: "Check slabs, 87A, std deduction, cess vs incometaxindia.gov.in; update fixtures on Budget day (1 Feb).", trigger: { cron: "monthly:1" }, runs_as: "claude", tokens: 3000, kpi: "No stale rule >7 days", validator: { checks: ["every rule cites a gov source", "IT Act 2025 section noted"] } }),
A({ id: "b5.seo", name: "Telugu SEO Writer", unit: "b5", team: "marketing", mission: "2 long-tail pages/week, EN+TE, education only.", trigger: { cron: "weekly:wed" }, tokens: 8000, kpi: "Impressions up week on week", validator: { name: "Finance Content Reviewer", checks: ["no fund/stock recommendation", "no return promise", "rate labelled assumed", "sources cited"] } }),
A({ id: "b5.curator", name: "Deal Curator", unit: "b5", team: "sales", mission: "Turn Akhil's 3 pasted links into Telugu posts via EarnKaro/Cuelinks.", trigger: { cron: "daily:08:30" }, runs_as: "human", tokens: 2000, kpi: "3 posts/day", validator: { checks: ["no scraping", "price + timestamp + 'may change'"] } }),
A({ id: "b5.poster", name: "Deal Poster Bot", unit: "b5", team: "delivery", mission: "Post queue.csv to the channel on schedule.", trigger: { cron: "every 30 min" }, runs_as: "code", code: "05-deals/src/bot/post.py", tokens: 0, kpi: "0 missed slots", validator: { name: "Disclosure Gate", checks: ["'#ad' in first 2 lines", "no Amazon link in email", "no loan/insurance/MF/broker links"] } }),
A({ id: "b5.news", name: "Newsletter Editor", unit: "b5", team: "marketing", mission: "Weekly issue: deadline, 1 explainer, top deals (non-Amazon), 1 Kit CTA.", trigger: { cron: "weekly:fri" }, tokens: 5000, kpi: "Open rate ≥ 40%", validator: { checks: ["unsubscribe link", "DPDP notice link", "#ad labels"] } }),
A({ id: "b5.compliance", name: "SEBI/ASCI/RBI Checker", unit: "b5", team: "validation", mission: "Monthly audit of 20 random posts/pages against §3b.", trigger: { cron: "monthly:15" }, tokens: 4000, kpi: "0 violations", validator: { checks: ["sample random", "findings fixed within 7 days"] } }),
A({ id: "b5.metrics", name: "Deals Metrics", unit: "b5", team: "pm", mission: "Weekly: visits, members, clicks, ₹ earned/received, Kit sales from b5.", trigger: { cron: "weekly:sun" }, tokens: 1500, kpi: "Report every Sunday", validator: { checks: ["numbers match dashboards"] } }),
```

Existing `b5.pm` and `b5.research` stay as they are. Total is about 35k tokens a week, which fits b5's 8% share.

## 7. Metrics & kill criteria

**Weekly numbers:** channel members and views per post; deal clicks (EarnKaro dashboard); ₹ earned vs ₹ received; site visits and Search Console impressions; newsletter subscribers and open rate; Kit sales attributed to b5 (UTM `?src=b5`); compliance violations (target 0).

| By date | Target to keep going |
|---|---|
| 30 Nov 2026 | 10 calculators live; channel ≥ 150 members; first EarnKaro sale |
| 31 Jan 2027 | Channel ≥ 400; site ≥ 1,500 visits/mo or ≥ 5,000 impressions/wk; ≥ ₹1,000 earned; ≥ 1 Kit sale via b5 |
| 30 Apr 2027 | ≥ ₹3,000/mo received (any mix) |

**Pause rule:** if the **31 Jan 2027** targets are mostly missed (3 of 4), stop the Telegram and newsletter work and move the 20 minutes a day to b1 or b3. The static calculator site stays up, since it costs ₹0, and keeps feeding Kits. If Amazon is joined, put the channel decision on the calendar before the 180-day clock ends.

## 8. What I need from Akhil

- [ ] Approve: site and channel name plus the Telugu brand line (numerology check is yours).
- [ ] Create: a Cloudflare account and connect the GitHub repo (free).
- [ ] Create: a Telegram channel and bot. Paste the bot token **into GitHub Secrets yourself, never in chat**.
- [ ] Sign up: EarnKaro now, Cuelinks in week 2, Amazon Associates IN only at ≥ 300 members, Kit (newsletter) free.
- [ ] Daily 10 minutes: paste 3 deal links into the queue sheet.
- [ ] Decide: no MF, broker, loan or insurance links (needs ARN, RBI LSP or IRDAI status). Confirm you agree.
- [ ] Later: approve the domain spend when the gate is met. Ask a CA about TDS and GST once income passes ~₹10k/month.

## 9. Sources

- Research: `00-hq/research/github/a5-kits-deals.md` (india-tax-guru checked against slabs, Astro build, Creators API).
- Amazon Creators API eligibility: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction
- Amazon India commission rates, 3 sales in 180 days, ₹2,500 payout: https://www.wscubetech.com/blog/affiliate-marketing-amazon/
- Flipkart public sign-ups discontinued: https://www.haulpack.com/blog/how-to-start-flipkart-affiliate-marketing/
- Cuelinks Flipkart terms: https://www.cuelinks.com/campaigns/flipkart-affiliate-program
- EarnKaro ₹10 minimum: https://gauravtiwari.org/best-money-earning-apps-in-india/ · EarnKaro card payouts (2024 data, re-check): https://earnkaro.com/blog/idfc-bank-affiliate-program/
- SEBI finfluencer restrictions and 3-month price rule: https://www.medianama.com/2025/02/223-sebi-regulated-entities-restriction-finfluencers/ · https://www.business-standard.com/markets/news/sebi-finfluencer-circular-live-stock-data-market-education-rules-125013000571_1.html
- ASCI finance influencer addendum (Apr 2025): https://conventuslaw.com/report/india-asci-updates-influencer-guidelines-for-health-and-finance-sectors-strikes-balance-between-expertise-and-expression/ · ASCI labels: https://legal500.com/developments/?p=28469 · https://www.ascionline.in/social/wp-content/uploads/2024/03/ASCIs-Guide-For-Influencers-1.pdf
- AMFI ARN / NISM V-A: https://rupeezy.in/blog/regulatory-compliance-mutual-fund-distributors · https://amfiindia.com/Themes/Theme1/downloads/home/ReadyReckonerforMFDs.pdf
- RBI credit card directions: https://m2pfintech.com/blog/rbis-new-directives-for-credit-debit-card-issuance/ · https://rbi.org.in/scriptS/BS_ViewMasDirections.aspx?id=13155
- RBI Digital Lending Directions 2025: https://vinodkothari.com/2025/05/digital-lending-directions-largely-a-consolidation-new-rules-on-multi-lender-platforms-and-lending-apps/
- AdSense India thresholds and tax: https://www.xflowpay.com/blog/get-paid-from-adsense-in-india
- DPDP Rules 2025 phasing: https://www.storyboard18.com/digital/breaking-govt-notifies-final-dpdp-rules-sets-staggered-rollout-with-key-obligations-for-data-fiduciaries-84201.htm
- Netlify free credits: https://netli.fyi/blog/netlify-free-plan-limits-2026 · Cloudflare Pages limits: https://temps.sh/blog/cloudflare-pages-free-tier-limits-2026
- beehiiv and Kit free tiers: https://www.sendx.io/blog/beehiiv-pricing-plans-costs-alternatives-for-newsletter-publishers-2026
- Telegram channel ad revenue share (50%, ≥ 1,000 subs, TON): https://telegram.org/blog/monetization-for-channels
- Competitor calculators: https://groww.in/calculators · sipcalculator.in traffic: https://cw.semrush.com/website/sipcalculator.in/overview
- Tax slabs FY 2026-27: https://www.indiabudget.gov.in/doc/memo.pdf · https://www.incometaxindia.gov.in/w/tax-rates-and-computation

# P0 · HQ: Kalpa Labs as one money machine

*Planning agent P0 (HQ / portfolio) · 2026-10-13 · Inputs: research BRIEF, the 7 world READMEs, research reports a1–a8, `00-hq/agents/registry.js` (215 agents) and `state.json` (active: salon, 0 clients). The world plans P1–P7 hold the detail for each world. This file decides **order, money and rhythm**.*

---

## 1. Verdict

Kalpa Labs makes money by **selling one high-ticket service first and running the cheap products in the background**. BotBhai Salon (₹9,999 setup + ₹2,999/month) is already built and needs only selling, so it gets most of the CEO's hour from tomorrow. Agents build the Kits (₹199–499) and the calculator/deals site alongside it, at almost no CEO cost. FinOps (₹1,999–7,999/month) starts as a paid audit in month 2. JobCard is timed to launch for the March 2027 AC season. The Extension waits for a free slot. Trading stays on paper and adds ₹0 revenue in year 1.

**Company revenue, all worlds combined (₹, gross receipts):**

| | Month 1 (Nov 26) | Month 3 (Jan 27) | Month 6 (Apr 27) | Month 12 (Oct 27) | 12-month total |
|---|---|---|---|---|---|
| Low | 0 | 3,950 | 9,653 | 27,440 | 1.58 L |
| **Likely** | **0** | **18,097** | **41,548** | **86,374** | **5.11 L** |
| High | 4,100 | 40,994 | 99,072 | 2,15,507 | 13.2 L |

**Single biggest risk:** the CEO's hour gets spread across 7 worlds and no world gets enough selling time to land its first 3 customers. The plan prevents this with a hard cap: **at most 3 worlds get CEO time in any week**, and a world that misses its dated gate (section 7) gives its day back.

---

## 2. Customers and flagship offers (company level)

| World | Who pays | Flagship offer and price ladder | Why they buy now | Competitor alternatives (price) |
|---|---|---|---|---|
| **b1 BotBhai** | Salon owners in Hyderabad, then gyms (Jan) and coaching institutes | Founding 3 clients: ₹4,999 setup + ₹1,999/month. Standard Salon: ₹9,999 + ₹2,999. Gym: ₹9,999 + ₹3,499. Coaching: ₹14,999 + ₹4,999. Ads add-on: ₹2,000/month | Wedding season (Nov–Feb) means bridal enquiries go unanswered. The README's worked example shows about ₹14k/month of no-shows recovered | WATI Growth ₹2,499/mo, Interakt Starter ₹999/mo, AiSensy Basic ₹1,500/mo. All are DIY software with Meta fees plus markup, and none is set up for the owner |
| **b3 Kits** | Telugu-state exam aspirants; salaried people doing tax/SIP | One kit ₹199–299, bundle ₹499 (Sheet + per-buyer stamped PDF) | Exam notification dates and tax season (Jan–Mar declarations) | Testbook/Adda247 passes (sold at deep festive discounts; P3 to verify current prices), free YouTube PDFs |
| **b5 Deals & Tools** | Advertisers and affiliate programmes (not the reader) | Free calculators plus a Telugu deals channel; income from Amazon/affiliate commissions, later newsletter sponsorships | Traffic compounds, so the earliest start wins | Groww/ClearTax calculators (free); existing Telugu deal channels |
| **b6 FinOps** | Indian AI startups and SaaS teams spending ₹50k+/month on LLM APIs | Entry: one-off "AI cost + DPDP readiness audit" at ₹4,999. Then ₹1,999 / ₹3,999 / ₹7,999 per month | DPDP core duties apply from **12 May 2027**; LLM bills are rising | Langfuse Core $29/mo, Helicone Pro $79/mo (cost only, no INR or DPDP pack); compliance consultants |
| **b2 JobCard** | AC/appliance technicians | Free tier, then ₹149/month, ₹299/month Pro | Summer peak (Mar–Jun): most jobs and most lost invoices | Vyapar (free Android tier, desktop from about ₹3,399/yr); paper bill books |
| **b4 Extension** | Global Chrome users of one niche (picked from review mining) | Free 5 uses/day, Pro $3–5/month via Dodo Payments | A fix for a pain they already complain about | The incumbent extension in that niche |
| **b7 Trading** | Nobody; this is proprietary research | Paper ledger only | Not applicable | Not applicable |

**The company-level offer rule:** each world sells **one** flagship until it has 10 paying customers. No second offer before that.

---

## 3. Unit economics (company level)

**Fixed cost today: ₹0.** Every tool is on a free tier. Variable cost per customer per month:

| World | Cost to serve on free tiers | After free limits | Gross margin | Break-even |
|---|---|---|---|---|
| b1 | ≈ ₹0. The client pays Meta message fees and ad spend on their own account | Supabase Pro $25/mo shared across all clients (≈ ₹450/client at 5 clients) | ≈ 85–95% | 1 client covers every company cost through month 6 |
| b3 | Razorpay 0% on the first ₹5 L GMV or 90 days (activation offer), then 2% + GST | ≈ ₹7 per ₹299 sale | ≈ 97% | 1 sale covers the ₹199 KYC fee |
| b5 | ₹0 (Netlify free) | Netlify Personal $9/mo only if traffic exceeds 300 credits | ≈ 100% | n/a |
| b6 | ≈ ₹0 (Workers + Supabase free); Presidio batch on Actions | Supabase Pro once client data exceeds 500 MB | ≈ 90% | 1 audit pays for a trademark |
| b2 | Sarvam STT ₹0.50/min ≈ ₹50/user; Play fee 15% | Same | ≈ 55–60% of ₹149 | 18 users cover Play fee + Sarvam + a share of Supabase |
| b4 | ₹0; Dodo ≈ 4% + $0.40 per sale | Same | ≈ 80% | $5 CWS fee = 2 sales |

**Where the free tiers run out first (company-wide watch list):**

| Free tier | Limit | Who hits it first | Trigger to pay |
|---|---|---|---|
| Supabase Free | **2 active projects**, 500 MB DB, 5 GB egress, **pauses after 1 week idle** | BotBhai + JobCard + FinOps all want a project. A third project is impossible | At the 5th BotBhai client, or when a third world needs its own DB: Pro $25/mo. Until then, separate worlds by schema inside one project |
| Netlify Free | 300 credits/month (a deploy costs 15, 1 GB costs 20); **all sites pause** when credits run out | Many client sites + calculator site on one team | Put the b5 site on Cloudflare Pages (free) so one world cannot pause another |
| GitHub Actions | Free minutes on private repos | Lead finder, paper trading, Lighthouse, Presidio jobs | Keep heavy jobs on public test repos or Colab |
| Razorpay offer | 0% fees for ₹5 L GMV or 90 days from activation | Kits + BotBhai collections | **Activate only when Kit #1 is ready** to use all 90 days |

**Company break-even:** at likely numbers, revenue exceeds all running costs from **month 2** (₹5,400 in vs ≈ ₹1,435 out).

---

## 4. Go-to-market: the company's first 10 customers

Customers 1–10 come in this order: **3 salons → 5 kit buyers → 1 FinOps audit → 1 gym.** The daily sales quota takes 20 of the 60 minutes and changes by day (section 5).

1. **Salons 1–3 (weeks 1–6).** The BotBhai lead finder (OSM Overpass, legal) lists salons within 3 km of home. On Mon/Thu, walk in to 2 salons between 11:00 and 13:00, the quietest time. Show the live demo bot on your phone (Demo Builder clones the salon config with their name). Offer the founding price with a 14-day money-back pilot. Follow up on day 2, 5 and 10 using the Follow-up Nudger's ready messages. Funnel target: 30 visits → 10 demos → 3 pilots.
2. **Kit buyers 1–5 (weeks 3–8).** The agent builds Kit #1. The CEO posts it in the Kalpa Telugu Telegram channel (b5) and in 3 exam groups he already belongs to (no spam, one post). Coaching institutes visited for BotBhai Exam Kits get a 30% reseller code.
3. **FinOps audit 1 (weeks 5–10).** Every Friday, send 5 personal LinkedIn messages to Hyderabad/Bengaluru AI founders: "free 20-minute AI-cost teardown, paid audit ₹4,999 if useful."
4. **Gym 1 (December).** Pitch in December for the January resolution rush.

**10 → 100:** referrals (one free month for every client who refers a paying client), commission-only referral partners (₹2,000 per closed BotBhai setup; no salary, no upfront cost), case-study posts from client dashboards (with written consent), the calculator site's SEO traffic feeding kits, and JobCard's built-in "Made with JobCard" invoice footer.

**Channel rules (all worlds):** no scraping of Google Maps, Justdial or Instagram. No unsolicited WhatsApp blasts, and BotBhai templates go only to opted-in contacts. No cold robocalls (TRAI). An affiliate disclosure on every deal post. No return promises anywhere.

---

## 5. Build plan: sequencing, the CEO's hour, and HQ quests

### 5a. Which world gets the hour on which day

| Phase | Dates | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|---|---|
| **A · Ignite** | 14 Oct – 15 Nov | b1 sell | b1 sell/deliver | b3+b5 | b1 sell | b1 deliver | HQ money + review | off (5-min scorecard) |
| **B · First rupees** | 16 Nov – 15 Dec | b1 sell | b1 deliver | b3+b5 | b1 sell | **b6 discovery** | HQ | off |
| **C · Second engine** | 16 Dec – 15 Feb | b1 sell (salon + gym) | **b2 build** | b3+b5 | b1 sell | b6 build/sell | HQ | off |
| **D · Season** | 16 Feb – 31 May | b1 | b2 launch | b3+b5 | b1 or b2 (whichever earns more per hour) | b6 | HQ | off |
| **E · Rebalance** | Jun onward | Set by the 1 June portfolio review: winners get days, losers go agent-only. **b4 gets a CEO day only when another world is paused** | | | | | | |

**Start now (agent-only, 0 CEO minutes):** the b5 calculator site (SEO compounds, so the earliest start wins), b3 Kit #1 production, and the b7 walk-forward gate plus paper ledger (the 90-day clock is the bottleneck, so start it now). **Start later:** b6 on 16 Nov, b2 discovery in December and build in Dec–Feb, b4 review mining in January (agent-only) and a build only when a slot frees up.

**Token budget follows the CEO's hour.** Change `WORLD_SHARE` in `registry.js` from `{hq:10,b1:22,b2:20,b3:12,b4:10,b5:8,b6:10,b7:8}` to **`{hq:10,b1:35,b2:8,b3:15,b4:4,b5:10,b6:12,b7:6}`** for phases A–B, then revisit on 15 Dec. (This is a proposed edit for the HQ agent; P0 does not edit it.)

### 5b. Daily 60-minute template

| Minute | Block | What happens |
|---|---|---|
| 0–5 | **Brief** | Read the 07:47 brief. Tap approve or deny on up to 3 decisions. |
| 5–25 | **Revenue** | Today's sales quota: walk-ins, follow-ups, a post, or LinkedIn messages. The scripts are already drafted. |
| 25–50 | **Quest** | One quest of 25 minutes or less from today's world, prepared by agents. |
| 50–60 | **Close** | Log numbers (leads, demos, ₹ in), mark the quest done, and note one blocker for the agents. |

**Saturday (HQ day) instead:** 15 min ledger and invoices, 15 min collections, 20 min weekly scorecard and kill/scale check, 10 min choosing next week's quests.

### 5c. HQ quests (each 60 CEO minutes or less)

**Week 1 (14–20 Oct)**

| ID | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| Q-HQ-01 | Approve this plan | Read §1, §5a and §7 (15 min); reply "approved" or note changes | Updates `state.json` launch order and WORLD_SHARE (proposal above) | `run.js today` shows the b1-heavy split |
| Q-HQ-02 | Kalpa Ledger sheet | Create an empty Google Sheet in your Drive and share it with the agents' account (10 min) | Adds tabs: Receipts, Expenses, Invoices, Reserve, Scorecard | First row: ₹0 opening balance |
| Q-HQ-03 | Udyam update | Add NIC activities on udyamregistration.gov.in: software/IT consultancy, online sale of digital products, data processing (20 min, free) | Lists exact NIC codes with descriptions | Updated certificate PDF saved |
| Q-HQ-04 | Free business UPI QR | Open a free business UPI QR (PhonePe/Paytm/GPay for Business) on the spare Kalpa bank account (20 min) | Drafts the payment-instructions message for clients | ₹1 test payment received |
| Q-HQ-05 | Invoice template | Check one sample invoice (10 min) | `hq.invoice` builds a Sheet→PDF invoice: "Invoice" (not "Tax Invoice"), no GST, Udyam no. UDYAM-TS-02-0382711, series `KL/26-27/001` | Sample PDF approved |

**Weeks 2–4 (21 Oct – 10 Nov)**

| ID | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| Q-HQ-06 | **Go-public decision** | Decide "BotBhai goes public on <date>" (memory rule: no paid sign-ups until then). Target: the day a salon agrees to a pilot | `hq.legal` drafts the client agreement (with a DPDP processor clause), privacy notice and terms | Decision logged; drafts ready for review |
| Q-HQ-07 | Legal pages live | Read the drafts (25 min) | Publishes the pages on Netlify/Cloudflare Pages | Public URLs work on a phone |
| Q-HQ-08 | Trademark pre-check | Run a free IP India public search for "BotBhai" and "Kalpa Labs" in classes 9/35/42 using the agent's search list (25 min) | Prepares variants and phonetic spellings, then summarises conflicts | Conflict table in `00-hq/docs/` |
| Q-HQ-09 | Razorpay activation | **Only when Kit #1 is ready.** KYC as Registered (Udyam + one more document) or Unregistered (PAN), then pay the ₹199 KYC fee (45 min) | Pre-fills answers and builds the Payment Page for Kit #1 | Live ₹1 test, then refund |
| Q-HQ-10 | Tax reserve pot | Create a separate savings "pot" or sweep FD in the Kalpa account (15 min) | `hq.taxreserve` computes 30% of each receipt | First transfer done |

**Month 2 (11 Nov – 10 Dec):** Q-HQ-11 domain + Cloudflare DNS + free Email Routing (after the first ₹5k). Q-HQ-12 first real invoice issued and collected. Q-HQ-13 portfolio review #1 on **15 Dec** (30 min). Q-HQ-14 switch b6 on in `state.json`.
**Month 3 (11 Dec – 10 Jan):** Q-HQ-15 book a 1-hour CA consult (after ₹25k), covering presumptive scheme, advance tax, and GST treatment of Play/Dodo/Razorpay receipts. Q-HQ-16 file the BotBhai trademark, TM-A class 42, ₹4,500 e-filing with the Udyam concession. Q-HQ-17 Play Console $25 the week JobCard needs closed testing (12 testers × 14 days before production for new personal accounts). Q-HQ-18 portfolio review #2 on **15 Jan**.

### 5d. Reinvestment rules

**Every rupee in is split three ways:** 30% to the tax reserve, 10% to a buffer (until it holds 3 months of running costs), 60% to the reinvest pot. Spend from the pot only in ladder order, and only on an item that **unlocks revenue or removes a free-tier limit that is already at 80% or more**.

| Cumulative revenue | Spend on (in order) | What it unlocks |
|---|---|---|
| **First ₹5,000** | Razorpay KYC ₹199 + GST (only at kit launch); domain (about ₹500–1,000/yr, compare registrars); Cloudflare Email Routing (free) for hello@; QR standee and 100 visiting cards for salon walk-ins (≈ ₹500) | Automated kit checkout; a trustworthy brand address; better walk-in conversion |
| **₹25,000** | Trademark "BotBhai", class 42 (₹4,500); 1-hour CA consult (≈ ₹1,500–3,000); Play Console $25 (when JobCard is ready); Chrome Web Store $5 (when b4 is ready); ₹1,000 Sarvam credits | Brand protection before scaling; correct tax filing; the 2nd and 3rd product launches |
| **₹1,00,000** | Supabase Pro $25/mo (no pausing, backups) once BotBhai has 5 or more live clients; current account (Udyam + Telangana Shops & Establishments or GST as the 2nd proof); BotBhai's own Meta lead-ad test, capped at ₹5,000 and judged on cost per demo; second trademark class; Kite Connect ₹500/mo **only if** the b7 gate passes | Production reliability for paying clients; clean books; a paid acquisition channel tested on data |
| **Never from company money** | Trading capital, paid courses, paid "lead lists", any tool a free tier still covers | Not applicable |

**Cash flow, likely case, net of spends (₹):**

| | M1 Nov | M2 Dec | M3 Jan | M4 Feb | M5 Mar | M6 Apr | M7 May | M8 Jun | M9 Jul | M10 Aug | M11 Sep | M12 Oct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue | 0 | 5,400 | 18,097 | 23,745 | 30,629 | 41,548 | 43,704 | 57,322 | 59,872 | 71,705 | 72,991 | 86,374 |
| Spends | 0 | 1,435 | 200 | 8,700 | 1,100 | 3,150 | 8,500 | 4,000 | 4,000 | 4,500 | 4,500 | 5,000 |
| Net | 0 | 3,965 | 17,897 | 15,045 | 29,529 | 38,398 | 35,204 | 53,322 | 55,872 | 67,205 | 68,491 | 81,374 |

### 5e. Twelve-month revenue by world (₹)

**Assumptions.** b1 setup fees are paid 50% at signing and 50% at go-live, the first 3 clients are on founding prices, and churn is 2 (likely). b3 nets ≈ ₹290 per sale. b2 nets ₹127 per ₹149 user after Play's 15%. b6 combines ₹4,999 audits with monthly plans. b7 is paper only.

**Likely**

| World | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 | M11 | M12 | Year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| b1 BotBhai | 0 | 2,500 | 6,998 | 8,997 | 13,496 | 18,996 | 19,997 | 22,997 | 25,997 | 28,997 | 29,998 | 32,998 | 2,11,971 |
| b3 Kits | 0 | 2,900 | 5,800 | 7,250 | 8,700 | 10,150 | 11,600 | 13,050 | 14,500 | 14,500 | 15,950 | 17,400 | 1,21,800 |
| b5 Deals | 0 | 0 | 300 | 500 | 800 | 1,000 | 1,500 | 2,000 | 2,500 | 3,000 | 3,500 | 4,000 | 19,100 |
| b6 FinOps | 0 | 0 | 4,999 | 6,998 | 6,998 | 8,997 | 5,997 | 12,995 | 9,995 | 16,993 | 13,993 | 20,991 | 1,08,956 |
| b2 JobCard | 0 | 0 | 0 | 0 | 635 | 1,905 | 3,810 | 5,080 | 5,080 | 5,715 | 6,350 | 6,985 | 35,560 |
| b4 Extension | 0 | 0 | 0 | 0 | 0 | 500 | 800 | 1,200 | 1,800 | 2,500 | 3,200 | 4,000 | 14,000 |
| b7 Trading | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **0** | **5,400** | **18,097** | **23,745** | **30,629** | **41,548** | **43,704** | **57,322** | **59,872** | **71,705** | **72,991** | **86,374** | **5,11,387** |

**Low and high totals per month**

| | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 | M11 | M12 | Year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Low | 0 | 870 | 3,950 | 6,338 | 12,221 | 9,653 | 12,917 | 15,800 | 22,081 | 22,662 | 23,696 | 27,440 | 1,57,628 |
| High | 4,100 | 22,097 | 40,994 | 59,893 | 87,496 | 99,072 | 1,19,851 | 1,40,360 | 1,61,329 | 1,74,299 | 1,93,403 | 2,15,507 | 13,18,401 |

What the scenarios assume. **Low:** 5 BotBhai clients in the year and FinOps starting late. **Likely:** 11 BotBhai clients signed (9 active), about 60 kits a month by M12, 7 FinOps subscribers. **High:** 22 BotBhai clients and 12 FinOps subscribers. Even the high case stays **under the ₹20 L GST threshold** for services in year 1.

### 5f. Company legal and financial setup

| Item | Status / action | When |
|---|---|---|
| **Business form** | Sole proprietorship under Akhil's PAN. Udyam is done (UDYAM-TS-02-0382711). No company or LLP until profit or investors justify one | Now |
| **Udyam** | Add NIC codes for every world (Q-HQ-03). Free | Week 1 |
| **GST** | Not needed below **₹20 L** aggregate turnover for services. Registration becomes compulsory regardless of turnover only for things we avoid: inter-state sale of **goods**, or selling goods through marketplaces that collect TCS. Kits stay digital and sell from our own page. The CA confirms Play/Dodo treatment. Register voluntarily only if a B2B FinOps client insists on input credit | Watch monthly (`hq.compliance`) |
| **Bank** | The spare Kalpa savings account holds everything now. Open a current account at ₹1 L cumulative or when Razorpay asks for a business-name account. Banks want 2 entity proofs: Udyam + one more | ₹1 L |
| **Invoicing** | Sheet→PDF via `hq.invoice`. Use "Invoice" until GST registration, never "Tax Invoice". One FY series `KL/26-27/NNN`. Udyam number on every invoice. Chase on days 3 and 7 | First client |
| **Collections** | BotBhai: business UPI QR, free (setup fee and monthly). Kits: Razorpay Payment Page, with Cashfree as the backup (1.95%, zero setup fee). FinOps: UPI or Razorpay link. JobCard: Play Billing. Extension: Dodo Payments (merchant of record, so we receive a foreign payout) | Staged as above |
| **Income tax** | Proprietorship profit goes on Akhil's personal return. The CA picks between presumptive 44ADA (50% deemed profit, receipts up to ₹50–75 L) and 44AD (6% of digital receipts), as renumbered under the Income-tax Act 2025. Advance tax applies if liability exceeds ₹10,000 | CA consult (₹25k) |
| **Trademark** | Use ™ now. File BotBhai class 42 at ₹4,500 (individual/MSME e-filing). Never use ® until registered | ₹25k |
| **DPDP** | BotBhai acts as a data processor for salons: processor clause in the client agreement, a privacy notice on every site, no sale of data. Core duties apply from **12 May 2027**, so every world must be compliant by April 2027 | Agreement before the first client |
| **Policies** | Meta WhatsApp Business policy (opt-in, templates), TRAI (no unsolicited calls or SMS), ASCI affiliate disclosure, Chrome Web Store single purpose, Play payments policy, SEBI (no tips or signals from b7) | Validators check every deliverable |

---

## 6. Agent swarm (HQ additions, registry.js style)

The existing HQ agents (`hq.chief`, `hq.evening`, `hq.finance`, `hq.invoice`, `hq.compliance`, `hq.legal`, `hq.brand`, `hq.research`, `game.herald`) stay. Changes and additions:

```js
A({ id: "hq.chief", mission: "07:47 IST money-first brief (spec in §6b of p0 plan)", runs_as: "code", tokens: 30000,
    validator: { checks: ["≤ 60 CEO minutes", "max 3 approvals", "only free actions until the go-public date", "₹ figures match the Ledger"] } }),
A({ id: "hq.cashflow", name: "Cash-flow Forecaster", mission: "Weekly: actual ₹ in vs the low/likely/high tables; re-forecast 12 months.", trigger: { cron: "weekly:sat" },
    runs_as: "code", code: "00-hq/src/cashflow.js (reads Ledger sheet export)", tokens: 0, kpi: "Forecast error < 25% by M3",
    validator: { checks: ["totals equal the sum of worlds", "receipts reconcile with the bank statement"] } }),
A({ id: "hq.reinvest", name: "Reinvestment Gatekeeper", mission: "Approve or deny each spend against the §5d ladder and 30/10/60 split.", trigger: { event: "spend request" },
    runs_as: "claude", tokens: 2000, human_needed: true, kpi: "Zero off-ladder spends",
    validator: { checks: ["cumulative revenue threshold met", "unlocks revenue or a free tier is ≥ 80% used"] } }),
A({ id: "hq.taxreserve", name: "Tax Reserve Keeper", mission: "30% of every receipt to the reserve pot; advance-tax dates.", trigger: { event: "receipt" },
    runs_as: "code", code: "00-hq/src/reserve.js", tokens: 0, kpi: "Reserve ≥ 30% of profit", validator: { checks: ["matches Ledger"] } }),
A({ id: "hq.freetier", name: "Free-tier Watchman", mission: "Daily usage of Supabase, Netlify, Actions, Groq, Sarvam; alert at 80%.", trigger: { cron: "daily:07:30" },
    runs_as: "planned", tokens: 0, kpi: "No surprise pause", validator: { checks: ["limits re-checked monthly against pricing pages"] } }),
A({ id: "hq.portfolio", name: "Portfolio Judge", mission: "Monthly on the 15th: ₹ per CEO-hour per world, gate checks, kill/scale verdicts, new day allocation.",
    trigger: { cron: "monthly:15" }, runs_as: "claude", tokens: 15000, human_needed: true, kpi: "Every world judged on its dated gate",
    validator: { checks: ["uses Ledger + scorecard only", "max 3 worlds with CEO time"] } }),
A({ id: "hq.quota", name: "Sales Quota Planner", mission: "Each morning: today's 20-minute sales list for the day's world, with ready scripts.",
    trigger: { cron: "daily:07:40" }, runs_as: "claude", tokens: 4000, kpi: "Quota done ≥ 5 days/week",
    validator: { checks: ["no scraped contacts", "opt-in only for WhatsApp", "no TRAI-violating calls"] } }),
```

### 6b. Morning brief and notification spec

**Push (one a day, 07:47 IST, at most 120 characters):**
`Day 23 · ₹4,999 this month (goal ₹10k) · Today: 2 salon walk-ins + Q-B1-07 (20m)`
A second push is allowed only for a red incident: a client bot is down or a payment failed.

**The brief, in this order (phone screen, 30 seconds to read):**
1. **Money line:** ₹ in yesterday, month to date against the likely target, cash in the account, tax reserve, overdue invoices (name + days late).
2. **Today's 3 things:** the sales quota, the quest, and approvals (at most 3, one tap each).
3. **Copy-ready scripts:** pitch or follow-up messages in English and Telugu.
4. **Pipeline:** leads → demos → pilots → paying, for each active world.
5. **Red alerts only:** a free tier at 80% or more, a policy change (Meta, TRAI, DPDP, Play), a client issue.
6. **Streak and XP:** one line.

---

## 7. Metrics and portfolio kill/scale rules

**The weekly scorecard (Saturday):** ₹ collected; MRR; new paying customers; demos given; sales quota days completed (of 6); CEO minutes per world; **₹ per CEO-hour per world** (revenue in the last 30 days ÷ CEO hours spent); overdue ₹; free-tier usage %; streak.

**World gates (miss the date and the world loses its CEO day; agents keep it on maintenance):**

| World | Gate date | Must have by then | If missed |
|---|---|---|---|
| b1 Salon | 15 Dec 2026 | 15 demos and 1 paying pilot | Switch the pitch to gyms (January rush) with the same days |
| b1 overall | 31 Jan 2027 | 3 paying clients | Pause new sales and serve existing clients only; move days to b6/b2 |
| b3 Kits | 31 Dec 2026 | 10 sales | Stop new kits; keep the existing kit for sale |
| b5 Deals | 31 Mar 2027 | 500 channel members or ₹500/month | Full autopilot, 0 CEO minutes |
| b6 FinOps | 28 Feb 2027 | 10 discovery calls and 1 paid audit | Pause; publish the research as content |
| b2 JobCard | 31 May 2027 (end of AC peak) | 20 paying technicians | Pause and revisit before the 2028 season |
| b4 Extension | 90 days after publishing | 500 installs or ₹1,000/month | Maintenance only |
| b7 Trading | Every strategy | Passes `gate.py` (OOS Sharpe > 0.5 and above buy-and-hold, PSR ≥ 0.95, ≥ 30 trades, PBO < 0.5), then 90 days of paper | Strategy deleted; lab continues at no CEO cost |

**Scale rules:**
- A world that brings in 40% or more of the month's revenue **and** grew month on month twice in a row gets one more CEO day, taken from the lowest ₹/CEO-hour world.
- At most 3 worlds hold CEO days at any time.
- **Company-level gate:** if cumulative revenue is below ₹10,000 on 31 Jan 2027 (below the low case), all CEO time goes to b1 alone until the first ₹10k month.

---

## 8. What I need from Akhil

- [ ] Approve the sequencing (§5a) and the WORLD_SHARE change (§5b note).
- [ ] Set a **go-public date** for BotBhai. It unlocks the client agreement, Razorpay and the domain.
- [ ] Create the Kalpa Ledger Google Sheet and share it with the agents.
- [ ] Add NIC codes on the Udyam portal, and open a free business UPI QR on the spare Kalpa account.
- [ ] Confirm whether you have salary income (it changes the tax reserve %). Tell me in words only, never documents.
- [ ] Choose a walk-in radius and the hours you can visit salons on Mon/Thu.
- [ ] Later: run the IP India search and pick a CA for the 1-hour consult.
- Never paste passwords, OTPs, API keys, PAN or Aadhaar numbers in chat. KYC steps happen on the provider's own site.

---

## 9. Sources

- Razorpay pricing (2% standard, no setup or AMC, ₹199 KYC fee, 0% offer up to ₹5 L or 90 days): [razorpay.com/blog/razorpay-payment-gateway-pricing-explained](https://razorpay.com/blog/razorpay-payment-gateway-pricing-explained/)
- Razorpay account types and KYC (Registered/Unregistered; Udyam accepted): [razorpay.com/docs/payments/create-account](https://razorpay.com/docs/payments/create-account/)
- Cashfree charges (1.95%, zero setup, new-merchant offer): [cashfree.com/payment-gateway-charges](https://www.cashfree.com/payment-gateway-charges)
- GST thresholds and compulsory registration: [calcguru.in GST threshold](https://calcguru.in/?p=3364), [kanakkupillai: services threshold](https://www.kanakkupillai.com/learn/new-gst-registration-threshold-limit-for-services/)
- Trademark fees (₹4,500 individual/MSME): [setindiabiz](https://www.setindiabiz.com/blog/trademark-registration-fee-concession-msme-startup), [ssrana](https://ssrana.in/ufaqs/trademark-filing-cost-inr-4500-india/)
- Presumptive taxation 44AD/44ADA: [calcguru.in presumptive](https://calcguru.in/?p=8194), [cleartax 44ADA](https://cleartax.in/s/section-44ada)
- Proprietorship current account documents: [mymoneyway.in](https://www.mymoneyway.in/2026/08/current-account-opening-documents-proprietorship-firm.html)
- DPDP Rules phased dates (13 Nov 2025 / 12 Nov 2026 / 12 May 2027): [AZB & Partners](https://www.azbpartners.com/bank/indias-digital-personal-data-protection-act-phased-rollout-and-key-compliance-milestones/)
- Supabase free plan limits: [supabase.com/pricing](https://supabase.com/pricing.md)
- Netlify free plan credits: [netli.fyi](https://netli.fyi/blog/netlify-free-plan-limits-2026)
- WATI, Interakt and AiSensy prices: [codingclave WATI pricing 2026](https://codingclave.com/blog/wati-pricing-india-2026)
- Vyapar pricing: [itforsme.in](https://www.itforsme.in/pricing/vyapar-india)
- Langfuse and Helicone pricing: [costbench](https://costbench.com/compare/helicone-vs-langfuse/)
- Testbook price (user report, outdated; P3 to verify): [techjockey](https://www.techjockey.com/reviews/testbook)
- Play Console fee and testing rule: [afkarsoftware](https://afkarsoftware.com/en/blog-detail/google-play-console-account-2026-one-time-25-fee/)
- Internal: `00-hq/research/github/a1–a8`, `01-studio/botbhai/setups/*/README.md` (prices, Meta message fees), `00-hq/agents/registry.js`, `state.json`.

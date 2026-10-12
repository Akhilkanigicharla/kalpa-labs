# P3 · World b3 Kits ("Library of Ranks") — plan

Planning agent P3 · 2026-10-13 · Inputs: `00-hq/research/BRIEF.md`, `03-kits/README.md`, `00-hq/research/github/a5-kits-deals.md`, `01-studio/botbhai/setups/examkits/`, `00-hq/agents/registry.js`. Facts about prices, fees, dates and rules were checked with web search on 2026-10-13 (sources at the end). Not legal or tax advice; confirm GST points with a CA before turnover nears ₹10 lakh.

## 1. Verdict

b3 earns money by selling copy-to-your-Drive Google Sheets kits for ₹199–499 through a Razorpay Payment Page. Delivery is automatic through a `/copy` link, and fulfilment costs almost nothing. The first three kits follow exam and tax deadlines: **GATE 2027 Final-120-Days Tracker** (exam 6–21 Feb 2027), **UPSC CSE 2027 Prelims Tracker** (prelims 23 May 2027) and **Salary Tax-Regime + SIP Goal Planner FY 2026-27** (Jan–Mar investment-proof season, then ITR in July). A Telugu TGPSC/APPSC Group kit launches within 7 days of an official notification. Margin is about 97%, and break-even is one sale. This world can produce the **first rupee in under a week**. Revenue will be small and seasonal, so treat it as cash flow and a lead magnet for BotBhai examkits, not a salary.

| ₹ per month | Month 1 (Nov '26) | Month 3 (Jan '27) | Month 6 (Apr '27) | Month 12 (Oct '27) |
|---|---|---|---|---|
| Low | 0 | 1,000 | 3,000 | 2,000 |
| Likely | 1,000 | 6,000 | 15,000 | 12,000 |
| High | 4,000 | 20,000 | 50,000 | 60,000 |

**Biggest risk:** getting seen, not building. Free sheets and ₹49 launch-priced sellers already exist, and 20 minutes a day of organic posting may not cut through. A smaller risk is piracy, because a `/copy` link is easy to forward.

## 2. Customer & offer

**Who pays:**
- Aspirants aged 20–30 who already live in Google Sheets on their phones: engineering grads for GATE, graduates for UPSC.
- Salaried 25–40-year-olds choosing between the old and new tax regimes and setting SIP goals.
- Later, coaching institutes that buy kits in bulk (through the BotBhai bundle).

**Why now:** each kit is tied to a dated deadline.
- GATE is about 4 months away; registration has already closed.
- UPSC prelims are about 7 months away.
- Employers ask for tax-saving proofs in Jan–Mar.

**Demand evidence:** keyword volumes need a Google Ads account, which we don't have, so the evidence below is proxies.

| Kit | Evidence | Paid competitors proving people pay |
|---|---|---|
| GATE 2027 Final-120-Days Tracker | Exam 6, 7, 13, 14, 20, 21 Feb 2027 (IIT Madras). Registration closed in Sep/Oct 2026, so the buyer pool is fixed and committed. | "GATE 2027 Tracker" Notion template at 299 on Carrd + Cashfree; GateOS at ₹99/month or ₹999/year |
| UPSC CSE 2027 Prelims Tracker | 8,19,732 applied for CSE 2026; prelims 2027 on 23 May 2027 | Topmate "UPSC Syllabus Tracker" at ₹49 (struck through from ₹299) |
| Salary Tax-Regime + SIP Goal Planner | 10.02 crore contributing SIP accounts and 66.4 lakh new SIP registrations in Aug 2026. Most free sheets miss 87A marginal relief; taxcalcindia is off by ₹40,300 at ₹13L gross. | freefincal tools (free); many Gumroad budget sheets (free–₹500) |
| (Kit 4, on trigger) TGPSC/APPSC Group, in Telugu | TGPSC has about 15 more notifications planned for about 3,800 posts, but the groups aren't confirmed. SSC CGL 2026 drew 28 lakh+ applications. | Coaching material only; almost no Telugu Sheets trackers found |

**Exact offer:** each kit is one Google Sheet that the buyer copies to their own Drive. It works on a phone and needs no add-ons. It also comes with a 6-page PDF guide stamped with the buyer's name, and free updates until the exam or until 31 Jul 2027 (tax).
- **Exam kits** include:
  - an official-syllabus checklist with topics weighted by how often they appeared in previous papers (we count this from public papers; this is our own analysis);
  - a daily log with a streak counter;
  - a spaced-revision scheduler (1/3/7/21 days);
  - a mock-test analyser that separates careless from concept errors;
  - a countdown and a weekly plan.
- **Tax kit** includes:
  - old vs new regime with 87A marginal relief and cess, checked against india-tax-guru fixtures;
  - HRA, 80C and 80D inputs;
  - a SIP goal planner (step-up, inflation), a loan prepay-vs-invest sheet and an EMI table;
  - "assumed return" fields only. It names no funds and makes no return promises (SEBI).

**Price ladder:**

| Tier | ₹ | What's in it |
|---|---|---|
| Lite (free) | 0 | Countdown + bare syllabus checklist, view-only. The ask is to join Telegram. |
| Kit | 199 (early-bird ₹99 for the first 30 buyers) | Full kit + PDF guide + updates |
| Kit Pro | 299 | Kit + previous-paper topic weights + mock analyser + Telugu/Hindi instructions tab |
| Bundle | 499 | Both exam kits for one exam season, or Tax + SIP + Loan. Adds a daily Telegram question channel (BotBhai examkits content). |
| Institute licence (B2B) | ₹2,999 for 50 students, or free with a BotBhai examkits setup | White-label copy with the institute's name |

**Alternatives a buyer compares us to:** the ₹49–299 Topmate UPSC tracker, the GATE Notion tracker at 299, and GateOS (₹999/year). Our edge is that the kit is a phone-first Google Sheet with no account to create, weighted by previous papers, includes a mock analyser, and has Telugu instructions.

## 3. Unit economics

| Item (per ₹199 sale) | ₹ |
|---|---|
| Razorpay platform fee 2% + 18% GST on the fee | 4.70 (₹0 for the first 90 days / ₹5L GMV under the new-merchant offer) |
| Email delivery (Apps Script MailApp, consumer quota 100 recipients/day) | 0 |
| Copy delivery (`/copy` link; buyer's own Drive storage) | 0 |
| Order log (Supabase free tier, shared ops project) | 0 |
| PDF stamping (pdf-lib in Edge Function or pypdf in Actions) | 0 |
| **Net per sale** | **≈ ₹194 (97.6%)** |

- **One-off costs:** a ₹199 + tax Razorpay KYC fee (new-merchant terms, July 2026 onward). This is worth paying because it unlocks UPI and cards with no setup fee.
- **Break-even:** 1 sale.
- **Where free tiers run out:**
  - MailApp sends 100 emails a day. Above about 80 orders a day, move to a transactional email free tier or Razorpay's receipt alone.
  - Apps Script allows 250 new documents a day, which only matters if we make per-buyer copies.
  - Supabase free tier pauses projects after inactivity. The webhook traffic and a weekly cron keep it awake.
- **First spend worth making:** a ₹700–900/year domain, after 25 sales. It adds trust on the payment page and enables a proper email sender. Spend nothing else until ₹10,000 cumulative.

**Storefront comparison (₹199 sale, $1 ≈ ₹88 assumed):**

| Option | Fee | ≈ you keep | UPI | Verdict |
|---|---|---|---|---|
| **Razorpay Payment Pages** | 2% + GST on fee; 0% for first 90 days / ₹5L for new merchants (₹199 KYC). Custom success message or redirect; webhook. | ₹194 | Yes | **PICK** |
| Cashfree Payment Forms | 1.95% + tax; forms free; festive offer waives fee on first ₹20L for eligible new merchants | ₹195 | Yes | Backup if Razorpay KYC stalls |
| Instamojo | 2% + ₹3 standard; digital-product store 5% + ₹3 (figures from a 2019-era article, so re-check) | ₹186 | Yes | Skip |
| Topmate | 10% via your own profile link, 20% via its marketplace (+ gateway, unclear); ECO TDS 0.1% u/s 194-O | ₹175 / ₹155 | Yes | **Second listing for discovery only** |
| Gumroad | 10% + $0.50 direct (30% via Discover) + card processing; Merchant of Record (MoR); no fee refunds | ≈ ₹100 | Not listed | No; the fixed fee kills ₹199 pricing |
| Lemon Squeezy | 5% + $0.50; MoR; in "help users migrate to Stripe Managed Payments" mode since Jan 2026; India payouts uncertain | ≈ ₹140 | Not listed | No |

## 4. Go-to-market

**First 10 customers (about 20 min/day; agents draft everything and Akhil posts or records):**
1. **Day 1–3:** publish the free Lite GATE sheet and the ₹99 early-bird page. Create a Telegram channel, "Library of Ranks", with a daily previous-paper question and a countdown.
2. **Day 3–7:** post one **value post** each in r/GATE and in the GATE/UPSC Telegram groups whose admins agree. The post shows "how I'd plan the last 120 days" with a screenshot and the free Lite link, discloses "I made this", and puts the paid link only in the Lite sheet's "Upgrade" tab. Read each community's self-promotion rules first, and skip any group that bans it.
3. **Day 5–14:** record 3 faceless **YouTube Shorts / Instagram Reels** a week, batched in one 45-minute session. Each is a 25-second screen recording, for example "the sheet that tells you which GATE topic to revise today". Agent-written scripts use the same video on both platforms, and every caption carries the Lite link.
4. **Day 7–14:** write 2 **Quora** answers a week to "how to plan last 4 months GATE / how to track UPSC syllabus" questions, with the free Lite link.
5. **Day 7–21:** give the full kit free to **5 Telegram channel admins / YouTube teachers** in return for honest feedback. Offer **30% commission** through a "referred by" field on the Payment Page, which Razorpay supports as a custom input.
6. **Day 10:** email every Lite user who consented: "Early-bird ₹99 ends at 30 buyers."

**Daily quota (20 min):**
- 5 min: approve today's Telegram post (written by the agent).
- 10 min: post or answer in 1 community.
- 5 min: reply to buyer and support messages.
- Once a week: a 45-minute Shorts batch, which replaces that day's quota.

**10 → 100:**
- Launch the UPSC kit on 15 Nov and the Tax kit on 1 Dec, so each audience gets the other's cross-sell.
- Pay a 30% affiliate share to 10 small creators.
- Move a Topmate listing to the marketplace for passive discovery.
- Ship the Telugu Group kit when a TGPSC/APPSC Group notification lands; that is our least-contested niche.
- Run the institute bundle through BotBhai examkits pitches (see the bundle section below).
- Post a "results" thread with consent-only testimonials. Never claim ranks or "AIR 1".

**Bundle with BotBhai examkits:**
- The examkits config (`01-studio/botbhai/setups/examkits/bot.config.json`) already lists "kit alone ₹199" in its catalog. Point those entries at the real Payment Page links.
- Every institute that buys the ₹14,999 setup gets a **white-labelled kit for its students free** (sweetener). Institutes without BotBhai can buy the ₹2,999 / 50-student licence.
- Reuse the examkits daily-question content (`bb_exam_daily_q`) as the Bundle tier's **Telegram** channel. Use Telegram, not WhatsApp, for B2C: a WhatsApp marketing message costs about ₹0.86 each, which ₹199 can't carry.
- An institute is also a channel: it can resell kits at ₹199 for 30%.

**Refunds:** publish the policy on the Payment Page and in the PDF:
- "Works-or-refund within 7 days": if the copy fails or a formula is wrong, we fix it within 48 h or refund in full.
- No refund for change of mind after copying (the product is delivered instantly).
- Expect to absorb the gateway fee on refunds. Target refunds below 3%.

**Piracy:** accept some leakage, and make the **update stream** the paid value.
- Each kit's About tab and PDF carry "Licensed to {name} · order {id}" (pypdf/pdf-lib, ADOPT).
- Updates (previous-paper weights after each exam, new tax rules) go only to verified buyer emails.
- Rotate the master template ID each season so old leaked `/copy` links die (buyers keep their copies).
- Report pirated uploads through each platform's copyright form. Don't use DRM add-ons.

**GST and income tax:**
- Digital kits are a supply of services, taxed at 18% once registered. Kalpa Labs' **aggregate all-India turnover across all worlds** (including BotBhai setup fees) is below ₹20L (Telangana is a normal-category state). That means:
  - Selling directly through Razorpay (a payment aggregator, not an e-commerce operator) needs no GST registration.
  - Selling through Indian e-commerce operators (Topmate, Instamojo store) is also exempt from compulsory registration under Notification 65/2017-CT, up to ₹20L.
- Topmate deducts 0.1% TDS (194-O; renumbered under the Income-tax Act 2025). That TDS is nil if gross sales stay ≤ ₹5L and PAN is given.
- Price GST-inclusive from day one. That way, if registration comes later (BotBhai growth may trigger it first), ₹199 still works (₹30.36 of it would be GST).
- Book kit income as business income of the proprietorship.

## 5. Build plan (quests ≤ 60 min CEO time each)

Code lives in `03-kits/src/` (new):
- `sheets/<kit>/`: Apps Script and formula docs via clasp (Apache-2.0, ADOPT).
- `qbank/`: CSV MCQ schema modelled on text2qti/GIFT.
- `guides/`: PDF and `stamp.py` (pypdf BSD-3, ADOPT).
- `delivery/supabase/functions/kit-order/`: Razorpay webhook. Learn the flow from Open Payment Host (AGPL) but don't copy its code.
- `tests/tax_fixtures.json`: india-tax-guru (MIT) numbers.

**Week 1 (first rupee)**

| ID | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| K-01 | Razorpay live | Sign up with PAN, Udyam and bank; pay the ₹199 KYC; add terms, privacy and refund text (agent drafts) | Draft policies, Payment Page copy and success message | Test ₹1 payment captured, then refunded |
| K-02 | GATE kit v1 | Review on phone, 20 min | Build the Sheet: syllabus × 30 papers, topic weights, revision scheduler, mock analyser, Lite version | 25-item QA checklist passes on Android Sheets |
| K-03 | v0 delivery | Paste the `/copy` link into "Show custom message" | Write the success message and receipt note | Test buyer receives a working copy in under 1 minute |
| K-04 | Telegram + Lite launch | Create the channel and post the first 3 posts | Write 14 days of daily-question posts | Channel live; Lite link opens view-only |
| K-05 | First community posts | Post 2 value posts | Draft posts per group rules | Posts live; no rule strikes |

**Weeks 2–4**

| ID | Quest | CEO | Agent | Done-check |
|---|---|---|---|---|
| K-06 | Webhook delivery v1 | Add Razorpay webhook secret and Supabase keys as secrets (never in chat) | Edge Function verifies `X-Razorpay-Signature`, logs the order, stamps the PDF (pdf-lib), triggers the Apps Script mailer with a shared secret | 3 test orders: email with `/copy` + stamped PDF; replayed webhook does not double-send |
| K-07 | UPSC kit v1 | 20-min phone review | Prelims GS + CSAT checklist, 10-year topic weights, current-affairs log | QA checklist; launch 15 Nov |
| K-08 | Tax + SIP kit v1 | Review the numbers | Port the slab logic; fixtures ₹12.75L / ₹13L / ₹25L must show 0 / 26,000 / 3,19,800 (new regime) and 1,40,400 / 1,48,200 / 5,22,600 (old); SEBI-safe disclaimers | In-sheet test tab all PASS; launch 1 Dec |
| K-09 | Shorts batch #1 | Record 3 screen videos (45 min) | Scripts, captions, thumbnails text | 3 posted on YT + IG |
| K-10 | Affiliate kit | DM 5 admins/creators (texts drafted) | "Referred by" field, payout sheet | ≥2 partners agree |

**Month 2**
- K-11: Topmate listing. CEO creates the profile; agent writes the listing. Done when it is live.
- K-12: Kit Pro and Bundle pages (₹299 / ₹499). Done when the upsell appears in delivery emails.
- K-13: Wire examkits catalog links and the institute licence one-pager into `b1.examkits.pitch`. Done when the BotBhai demo shows real kit links.
- K-14: Weekly numbers sheet. Done when the Reporter fills it automatically.

**Month 3**
- K-15: Telugu Group kit, built only if a TGPSC/APPSC Group notification is out. Done when it ships within 7 days of the notification.
- K-16: Season rotation playbook (template ID rotation and update emails).
- K-17: Post-GATE review (exam 6–21 Feb). Decide whether to go to GATE 2028 early-bird or retire the kit.

## 6. Agent swarm (registry style, unit `b3`)

```js
A({ id: "b3.calendar", name: "Exam & Tax Calendar Watcher", unit: "b3", team: "research", mission: "Watch UPSC/SSC/GATE/TGPSC/APPSC/CBDT official sites; trigger kit launches and updates.", trigger: { cron: "weekly:mon" }, tokens: 3000, kpi: "Kit 4 ships ≤7 days after notification", validator: { checks: ["official source link for every date"] } }),
A({ id: "b3.kitsmith", name: "Kit Builder", unit: "b3", team: "tech", mission: "Build and update Sheets with clasp; previous-paper topic weights from public papers.", trigger: { event: "quest" }, tokens: 15000, kpi: "Kit v1 ≤ 5 days", validator: { name: "Kit QA Tester", checks: ["25-item phone checklist", "no #REF!/#N/A", "works after /copy"] } }),
A({ id: "b3.taxcheck", name: "Tax Rule Checker", unit: "b3", team: "validation", mission: "Recompute fixtures with india-tax-guru; fail if the sheet differs.", trigger: { event: "tax kit change" }, runs_as: "code", code: "03-kits/src/tests/tax_fixtures.json", tokens: 0, kpi: "0 wrong rupees", validator: { checks: ["87A marginal relief case", "slab source cited"] } }),
A({ id: "b3.fulfil", name: "Order Fulfiller", unit: "b3", team: "delivery", mission: "Razorpay webhook → verify → log → stamped PDF + /copy email.", trigger: { event: "payment.captured" }, runs_as: "planned", code: "03-kits/src/delivery/supabase/functions/kit-order", tokens: 0, kpi: "100% delivered < 2 min", validator: { checks: ["signature verified", "idempotent on replays", "only email+name stored (DPDP notice)"] } }),
A({ id: "b3.shorts", name: "Shorts Script Writer", unit: "b3", team: "marketing", mission: "3 scripts/week for YT Shorts + IG Reels from kit screens.", trigger: { cron: "weekly:sat" }, tokens: 4000, kpi: "≥1 Lite signup per 500 views", validator: { checks: ["no rank/selection guarantees", "no return promises", "maker disclosed"] } }),
A({ id: "b3.telegram", name: "Telegram Poster", unit: "b3", team: "marketing", mission: "Daily previous-paper question + countdown in the channel (grammY, MIT).", trigger: { cron: "daily:07:00" }, runs_as: "planned", tokens: 500, kpi: "+300 subscribers/month", validator: { checks: ["answer key correct", "one promo per 5 posts max"] } }),
A({ id: "b3.answers", name: "Community Answer Drafter", unit: "b3", team: "marketing", mission: "Draft Quora/Reddit/Telegram value posts per community rules; Akhil posts.", trigger: { cron: "daily" }, runs_as: "human", human_needed: true, tokens: 2000, kpi: "2 posts/week, 0 removals", validator: { checks: ["subreddit rules read", "affiliation disclosed", "no spam"] } }),
A({ id: "b3.support", name: "Support & Refund Desk", unit: "b3", team: "success", mission: "Draft replies; fix-or-refund within 48 h.", trigger: { event: "buyer message" }, tokens: 1000, kpi: "Refunds < 3%", validator: { checks: ["policy followed", "no personal data in chat logs"] } }),
A({ id: "b3.piracy", name: "Piracy Watch", unit: "b3", team: "success", mission: "Monthly search for leaked copies; prepare copyright reports; rotate templates each season.", trigger: { cron: "monthly" }, tokens: 1500, kpi: "Leaks reported within 7 days", validator: { checks: ["report only our own work"] } }),
A({ id: "b3.bundle", name: "Institute Bundle Seller", unit: "b3", team: "sales", mission: "Feed kit licence offer into b1.examkits pitches and proposals.", trigger: { event: "b1.examkits visit planned" }, tokens: 1500, kpi: "1 institute licence per month from M3", validator: { checks: ["price floor ₹2,999/50", "no rank claims"] } }),
A({ id: "b3.reporter", name: "Kits Reporter", unit: "b3", team: "pm", mission: "Monday: visits, sales, ₹, refunds, subscribers, CEO minutes vs kill criteria.", trigger: { cron: "weekly:mon" }, runs_as: "planned", tokens: 1000, kpi: "Report every Monday", validator: { checks: ["numbers match Razorpay export"] } }),
```

These sit alongside the existing `b3.pm`, `b3.research`, `b3.builder`, `b3.marketer` and `b3.validator` entries.

## 7. Metrics & kill criteria

**Weekly numbers:**
- Payment-page visits, then conversion (target ≥ 3%)
- Paid sales and ₹
- Lite sign-ups and Telegram subscribers
- Shorts views
- Refund %
- Affiliate sales
- CEO minutes (cap 140/week)

**Kill criteria:**
- **By 31 Dec 2026, fewer than 10 paid sales:** stop new kit building. Leave the pages live on autopilot and move the 20 minutes to b5/b1.
- **By 28 Feb 2027, under ₹5,000 cumulative:** pause b3 except the institute licence inside BotBhai.
- **Refunds above 10% in any month:** freeze sales until the kit is fixed.
- **Any platform strike for spam:** stop posting in that channel.

## 8. What I need from Akhil

- [ ] Approve the brand "Library of Ranks", the prices (₹99 early-bird, then ₹199 / 299 / 499) and the refund policy.
- [ ] Open the Razorpay account yourself (PAN, Udyam, bank) and pay the ₹199 KYC. Cashfree is the fallback.
- [ ] Create the Telegram channel and YouTube/Instagram handles (or reuse Kalpa Labs ones), and decide between faceless and voice.
- [ ] Add the webhook secret and Supabase/Google keys only as repository/Supabase secrets, never in chat.
- [ ] Spend 10 min on Google Trends + YouTube search suggestions for "GATE tracker", "UPSC tracker" and "tax regime calculator excel", and screenshot them for the Researcher.
- [ ] Decide whether institutes get the kit free with BotBhai or for ₹2,999.
- [ ] Book a CA check once Kalpa Labs' total turnover passes ₹10L.

## 9. Sources

- Razorpay pricing: [razorpay.com/pricing](https://razorpay.com/pricing/), [pricing explained (new-merchant 0% offer, ₹199 KYC)](https://razorpay.com/blog/razorpay-payment-gateway-pricing-explained/), [UPI MDR vs platform fee](https://razorpay.com/blog/upi-charges-explained-mdr-vs-platform-fees/), [Payment Pages create (success message/redirect, fields, webhooks)](https://razorpay.com/docs/payments/payment-pages/create)
- Cashfree: [payment gateway charges](https://www.cashfree.com/payment-gateway-charges)
- Instamojo: [Wise article on Instamojo charges](https://wise.com/in/blog/instamojo-payment-gateway-pricing-charges-features)
- Topmate: [topmate.io/pricing](https://topmate.io/pricing)
- Gumroad: [Checkout Page fee breakdown (competitor source)](https://checkoutpage.com/blog/gumroad-fees), [Gumroad getting paid](https://gumroad.com/help/article/13-getting-paid)
- Lemon Squeezy: [Dodo Payments review (competitor source)](https://dodopayments.com/blogs/lemonsqueezy-review)
- GST and TDS: [Notification 65/2017-CT summary](https://www.gstzen.in/a/central-tax-notification-652017-seeks-to-exempt-suppliers-of-services-through-an-e-commerce-platform-from-obtaining-compulsory-registration.html), [GST Council registration flyer](https://www.gstcouncil.gov.in/sites/default/files/e-version-gst-flyers/Registration_under_GST_Law_new.pdf), [ClearTax 194-O](https://cleartax.in/s/section-194o)
- Apps Script quotas: [developers.google.com](https://developers.google.com/apps-script/guides/services/quotas)
- Exam calendars and demand:
  - GATE: [GATE 2027 dates (PW)](https://www.pw.live/gate/exams/gate-2027-exam-date-out), [GATE 2027 registration (Deccan Herald)](https://deccanherald.com/education/gate-2027-registration-begins-august-14-digilocker-mandatory-for-indian-candidates-4108240)
  - UPSC: [UPSC 2027 calendar (Deccan Herald)](https://deccanherald.com/education/upsc-cse-prelims-2027-on-may-23-mains-begins-aug-20-check-full-calendar-4015277), [UPSC CSE 2026 applicants](https://www.manoramayearbook.in/current-affairs/india/2026/05/25/over-5-lakh-candidates-appear-in-upsc-cse-2026.html)
  - SSC: [SSC CGL 2026 28 lakh applications](https://www.deccanherald.com/education/ssc-cgl-2026-application-window-extended-till-june-25-28-lakh-applications-so-far-4050397)
  - TGPSC: [TGPSC 15 notifications / 3,800 posts (Adda247)](https://www.adda247.com/exams/telangana/tgpsc-to-announce-15-new-recruitment-notifications-in-september-2026-for-3800-vacancies/)
  - SIP: [AMFI Aug 2026 SIP data (Onmanorama)](https://www.onmanorama.com/news/business/2026/10/07/contributing-sip-accounts-cross-10-cr-in-aug-2026-sip-assets-reach-21-4-of-industry-aum.html)
- Competitors: [Topmate UPSC Syllabus Tracker](https://topmate.io/cashflowie/2324163), [GATE 2027 Notion tracker](https://gatetracker.carrd.co/), [GateOS](https://similarlabs.com/fr/p/gateos-ai-preparation-tracker), [freefincal tools](https://freefincal.com/retirement-calculator-freefincal-robo-advisor/)
- Repo research: `00-hq/research/github/a5-kits-deals.md` (india-tax-guru MIT, pypdf BSD-3, pdf-lib MIT, clasp Apache-2.0, grammY MIT, Open Payment Host AGPL, learn only)

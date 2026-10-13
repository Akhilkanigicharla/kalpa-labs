# P6 — b6 AI FinOps & Governance ("Ledger Peaks"), the flagship plan

*Planning agent P6, 2026-10-13. Inputs: `00-hq/research/BRIEF.md`, `06-finops/README.md`, `06-finops/research/a7-finops.md`, `00-hq/agents/registry.js`. Prices and dates below were checked on the web today. Sources are listed at the end. USD is converted at about ₹96/$ (12 Oct 2026 rate).*

## 1. Verdict

Ledger Peaks makes money by telling an Indian SaaS or AI startup **what each of its customers and features costs in LLM spend, in rupees, and whether that customer is profitable**. Every month it also hands them a **DPDP + ISO 42001 + EU AI Act Art. 50 evidence pack** built from the same logs. The way in is a free "LLM Bill X-ray": they upload a usage export, and we send back a 2-page report within 48 hours. Two things drive the paid upgrade: savings found in that X-ray, and enterprise security questionnaires that now ask about AI. We never receive prompts, only metadata. That keeps us safe, cheap to run, and easy to trust.

Realistic revenue, because B2B sales cycles are long and the CEO has 20 minutes a day:

| | Month 1 (Nov 2026) | Month 3 (Jan 2027) | Month 6 (Apr 2027) | Month 12 (Oct 2027) |
|---|---|---|---|---|
| Low | ₹0 | ₹0 | ₹6,000 | ₹20,000 MRR |
| Likely | ₹0 (3 free X-rays done) | ₹5,000 (1 paid audit or pilot) | ₹25,000 MRR | ₹75,000 MRR |
| High | ₹5,000 (1 paid audit) | ₹20,000 | ₹60,000 MRR | ₹2,00,000 MRR |

**Biggest risk: trust.** A one-person company with no logo wall is asking startups for their usage data. The plan answers this with a metadata-only design, open-source code they can read, a public sample pack, and 3 named design partners before we charge anyone.

The **deadline tailwind** is real. DPDP's full duties (notice, consent, security safeguards, breach notification) start in **May 2027**. EU AI Act Art. 50 transparency has applied since **2 Aug 2026**.

## 2. Customer & offer

**Who pays (ICP).** The buyer is an Indian B2B SaaS or AI-app startup, seed to Series B, with 5–150 people, that:
- spends **₹50,000–₹10 lakh a month (~$500–$10k) on LLM APIs** such as OpenAI, Anthropic, Gemini, Sarvam or Groq. Below ₹50k a month our fee is more than 5% of their bill, so they won't care.
- sells AI features to many customers (B2B seats, per-conversation pricing or bundled AI) and doesn't know per-customer AI margin;
- sells to enterprises, BFSI, health, or EU/US buyers who send security questionnaires.

The buyer is the CTO or founder. The founder or finance lead signs off.

Signals to look for: a changelog announcing AI features, job posts for "AI/LLM engineer", a "Powered by GPT/Claude" mention, a trust page, or sales to Europe. Lists are covered in §4.

**Why they buy now.**
1. **The money problem.** AI is a COGS line that grows with usage. One heavy customer can wipe out the margin on their plan. LLM providers bill in USD, and USD/INR moved from about ₹88 to about ₹96 this year.
2. **GST leakage.** Foreign API bills paid without a GSTIN lose 18% that can't be claimed back. With a GSTIN, they owe reverse-charge tax that is easy to miss. We flag both.
3. **The deadline.** DPDP's substantive duties start in **May 2027**, with penalties up to ₹250 crore for weak security safeguards and ₹200 crore for breach-notification failures. Art. 50 is enforceable now for anyone with EU users.

**The offer and price ladder.** All prices exclude GST. Kalpa Labs is below the ₹20 lakh registration threshold.

| Tier | Price | What they get |
|---|---|---|
| **X-ray (free)** | ₹0, one-off | Upload an OpenAI/Anthropic usage export, LiteLLM spend log, Langfuse export or CSV. Within 48 h they get a 2-page PDF: INR cost by feature and model (by customer if tagged), "unpriced" models, top 3 savings ideas (caching, a smaller model, batch), a GST reverse-charge note, and a DPDP readiness score out of 20. |
| **Audit + Starter Pack** | ₹4,999 one-off | The X-ray plus a 45-min call, model-routing recommendations, a DPDP/Art. 50 gap list, and a filled AI section for their security questionnaire. **This is the fastest first rupee.** |
| **Starter** | ₹1,999/mo | Hosted dashboard for 1 product and up to 500k events a month. INR cost per feature and customer, a monthly cost report, and a DPDP checklist. |
| **Growth** | ₹4,999/mo | Up to 3M events a month. Per-customer gross margin (they upload revenue per customer), budget alerts by email or Slack, and the **monthly evidence pack** (DPDP duty map, ISO 42001 control IDs, Art. 50 checklist, model and region inventory, PII-exposure counts). |
| **Scale** | ₹7,999/mo | Multiple products, the PII-scan GitHub Action, questionnaire answers kept up to date, OSCAL JSON export (v1), and a quarterly review call. |
| **Founding pilot** | 3 design partners free for 60 days, then ₹999/mo locked for 12 months | In exchange for a named case study, a logo, and 2 feedback calls. Offered to the first 3 only. |

**Competitor alternatives** (prices checked today):

| Alternative | Price | What they lack for our ICP |
|---|---|---|
| **Langfuse** Cloud | Core $29/mo (~₹2,800), Pro $199/mo (~₹19,100), Enterprise $2,499/mo, $8 per 100k extra units | Engineer tracing in USD. No INR, GST, per-customer margin or DPDP evidence. We **ingest** it instead of fighting it. |
| **Helicone** | Pro $79/mo (~₹7,600), Team $799/mo | Proxy observability in USD. Same gaps. |
| **Portkey** (Bengaluru) | Production $49/mo (~₹4,700) for 100k logs, then $9 per 100k | A gateway, not a FinOps or compliance view. Its open-source gateway has had no commits on main since May 2026. |
| **Sprinto / Vanta** (compliance) | Sprinto ~$6k–30k/yr (₹5.8–29 L); Vanta Core ~$10k–15k/yr (₹9.6–14 L) | Generic SOC2/ISO tooling. Not wired to LLM logs, and too expensive for seed-stage teams. |
| **CloudZero / OpenMeter** | CloudZero is quote-only, median ~$42,850/yr; OpenMeter is now Kong "Konnect Metering & Billing" (contact sales) | Built for cloud cost or usage billing at enterprise prices. |

**Our position:** "Keep your tracer. We turn its logs into rupees, margins and a DPDP evidence pack, for less than the cost of one Langfuse Pro seat."

## 3. Unit economics

The design choice that keeps costs near zero: **metadata only** (tokens, model, provider, feature tag, hashed customer id, region). We batch ingestion, so one HTTP request carries up to 1,000 events. Raw events are kept for 30 days, then rolled up daily per (customer, feature, model).

| Item | Free tier | Our use per customer per month |
|---|---|---|
| Cloudflare Workers | 100,000 requests/day, 10 ms CPU each | ~3,000 batched requests at 3M events, so about 30 Growth customers fit easily |
| Supabase | 500 MB database, 2 projects, pauses after 7 days idle | ~15–30 MB with 30-day raw data plus rollups, so about **15–25 customers** fit |
| GitHub Actions | Free minutes. Public repos unlimited | Weekly price-map refresh, monthly pack build. The PII scan runs in the **customer's** Actions. |
| Claude (report narrative) | Within the company token budget | ~20k tokens per customer per month |
| Akhil's time | — | ~20 min per customer per month to review the pack before it goes out |

- **Cost to serve on free tiers:** about ₹0 in cash plus 20 minutes of review. Razorpay takes about 2% + GST per payment (≈₹100 on ₹4,999).
- **After the limits:** Supabase Pro $25 (₹2,400) + Workers Paid $5 (₹480) + a domain (~₹900/yr) ≈ **₹3,000 a month fixed**.
- **Gross margin:** about 98% on free tiers and about 85–90% after the upgrade at 10 customers.
- **Break-even after the upgrade:** 2 Starter customers or 1 Growth customer.
- **Where the free tiers run out:** Supabase storage at about 15–25 customers (upgrade then, unlocking daily backups and no pause), Workers CPU if we price inside the Worker for very large batches (move bulk pricing to an Action), and Presidio's 400 MB model, which never runs in our infrastructure.
- **Spends worth making, and what each unlocks:**
  - **₹900 domain** at the first paid customer (a trust signal for B2B email).
  - **₹3–5k one-time lawyer review** of the DPA and terms before the first paid invoice.
  - **Supabase Pro** at customer #10 or the first backup requirement.

## 4. Go-to-market

### First 10 customers (20 min a day)

**Assets ready before any outreach (Week 1–2):**
- the public sample X-ray and evidence pack on synthetic data;
- an open-source repo;
- an "LLM prices in ₹ this week" page;
- a one-page trust note ("we never see prompts; data stays in Supabase's Mumbai region; delete anytime").

**Lists (manual research only, no scraping):**
1. **Inc42's GenAI startup tracker** (175 startups, updated June 2026). Use only the application-layer companies.
2. **The YC company directory** filtered to India, and recent Indian launches on Product Hunt.
3. **LinkedIn**, searched by hand for "CTO" + "GenAI/LLM" in Bengaluru, Hyderabad and Pune. Look at the profile and the company changelog. Never export or scrape.
4. **Communities:** SaaSBoomi, Hasgeek (The Fifth Elephant), Hyderabad and Bengaluru GenAI meetups, r/developersIndia, and the LiteLLM and Langfuse community channels. In those channels we answer questions; we don't pitch.

**Daily quota (20 min):** 5 personal LinkedIn connection notes or work emails, written with a draft from the Pitch agent. Plus 1 helpful comment or post. Plus follow-ups due today, up to 3 per prospect, stopping on "no".

**Script outline (≤80 words):**
> "Saw you shipped [AI feature]. Quick question: do you know which of your customers cost more in GPT/Claude than they pay you? I'm building an open-source INR cost meter for Indian AI teams. Send me last month's usage export (metadata only, no prompts) and I'll send back a free 2-page X-ray: cost per feature, 3 savings ideas, and your DPDP-May-2027 readiness score. Sample here: [link]. Not for you? Just say so and I won't follow up."

Business-contact data is still personal data. Keep only name, role, work email and company. Delete it on request. Add an opt-out line to every email.

**Funnel target:** 150 contacts → 15 X-rays (10%) → 3 design partners plus 2 paid audits → 2–3 paying subscribers by the end of month 3. From month 4, design partners convert at ₹999 and new customers at list price.

**The X-ray call (15 min):** walk through the report, show the cost of one heavy customer, and offer either the ₹4,999 audit or the founding pilot.

### 10 → 100

- **Content flywheel.** A weekly "₹ per 1M tokens" table, a monthly "DPDP for AI teams" post counting down to May 2027, and anonymised X-ray findings ("the median startup we audited could cut 23% with caching"). Use real numbers only once we have them.
- **Integrations as distribution.** A LiteLLM callback, a Langfuse importer and an OpenLLMetry exporter recipe, each listed in its project's docs or examples where they accept community entries.
- **Partners.** Indian CA firms and virtual-CFO firms that serve startups (the GST angle). Also ISO 42001 consultants and auditors, who need the evidence. Offer partners 20% recurring.
- **Upsell path.** Starter → Growth when the customer gets its first enterprise questionnaire. Growth → Scale when they add a second product.

## 5. Build plan (quests, each ≤60 min of CEO time)

Code lives in `06-finops/src/`. The ADOPT picks from a7 are `@pydantic/genai-prices` (MIT), LiteLLM's price JSON as a cross-check, Presidio (MIT), OTel `gen_ai.*` conventions (Apache-2.0), and Probo's ISO 42001 control-ID JSON (MIT, with attribution).

**Never touch:** LiteLLM `enterprise/`, Langfuse `ee/`, any part of Comp AI (AGPL), or the ISO standard text (copyrighted). We publish control IDs and our own wording only.

### Week 1

| id | Quest | Agent action | CEO action | Done-check |
|---|---|---|---|---|
| F-01 | Price engine | Worker `06-finops/src/price/` uses `@pydantic/genai-prices`, takes the cached FBIL USD/INR rate, returns paise. Tests use a7's 4 fixtures. (a7 Q-B6-01) | Read the README (5 min) | `npm test` green, and INR matches USD × rate |
| F-02 | Unknown-model guard | Shows "unpriced spend" for retired models instead of ₹0 (Q-B6-06) | — | Test with `claude-3-5-haiku-20241022` |
| F-03 | Usage schema | Supabase `usage_event` + `usage_daily` tables mirroring the OTel `gen_ai.*` fields + `customer_id_hash`, `feature`. RLS on. Migration in `06-finops/src/db/` (Q-B6-02) | Create a free Supabase project in the Mumbai region (10 min) | RLS test: tenant A can't read B |
| F-04 | Positioning | Landing page copy + trust note + public sample X-ray PDF from synthetic data | Approve the name "Ledger Peaks" and the copy (15 min) | Page passes the 390 px phone check |

### Weeks 2–4

| id | Quest | Agent action | CEO action | Done-check |
|---|---|---|---|---|
| F-05 | Importers | OpenAI usage/costs CSV, Anthropic console CSV, LiteLLM spend-log CSV, Langfuse export, generic CSV/JSONL | — | 5 fixture files import with no rows lost |
| F-06 | X-ray generator | One command makes the 2-page HTML/PDF: INR by feature/model/customer, savings rules (cache hit rate, model downgrade, batch), GST RCM note, 20-question DPDP score | Review 1 sample (20 min) | Synthetic X-ray reads well on a phone |
| F-07 | Open-source release | Public repo `Akhilkanigicharla/ledger-peaks-meter` (MIT): price engine, INR rates, importers, `dpdp-2023.json` | Approve going public (10 min) | LICENSE, NOTICE (Probo/genai-prices attribution), no secrets |
| F-08 | ₹ price page | GitHub Action refreshes prices weekly and publishes "LLM prices in ₹" on the Netlify free subdomain | — | Page updates on schedule |
| F-09 | First outreach | The 50-prospect list, built by hand from Inc42/YC, with drafts | Send 5 a day (20 min/day) | 50 sent by day 28, logged |
| F-10 | Legal pack | Draft DPA, terms, privacy notice, and a "not legal advice / not certification" disclaimer | Read and approve (30 min) | Lawyer review flagged before first invoice |

### Month 2

| id | Quest | Agent action | CEO action | Done-check |
|---|---|---|---|---|
| F-11 | Ingest API | Worker `POST /v1/events` (batched, per-tenant key), LiteLLM callback, OpenLLMetry exporter recipe | — | 1M synthetic events in under 10 min, within free CPU |
| F-12 | Dashboard | Netlify static dashboard over Supabase: cost by customer/feature, margin with an uploaded revenue CSV | Click through (15 min) | Numbers equal SQL totals |
| F-13 | Framework catalogue | `dpdp-2023.json` (Act + Rules duties, dated), ISO 42001 IDs from Probo, our own Art. 50 checklist (Q-B6-04) | — | Every DPDP item cites a section or rule |
| F-14 | Evidence pack v0 | Monthly HTML/PDF: cost table, model and region inventory, PII-exposure counts, control map (Q-B6-05) | Review the first real one (30 min) | Validator checklist passes |
| F-15 | PII scan Action | Presidio with an allow-list + Indian mobile/UPI/IFSC recognizers, run in the **customer's** repo, outputs counts and hashes only (Q-B6-03) | — | Synthetic fixtures only. Raw values never leave |
| F-16 | First payments | Razorpay payment links for the audit and the pilot | Complete Razorpay KYC with Udyam (45 min, once) | ₹1 test link works |

### Month 3

| id | Quest | Agent action | CEO action | Done-check |
|---|---|---|---|---|
| F-17 | Alerts | Daily budget and anomaly alerts by email (free tier) or Slack webhook | — | Alert fires on a synthetic spike |
| F-18 | Case study #1 | A one-page before/after in INR with the partner's approval | Get written approval (15 min) | Partner signs off on the text |
| F-19 | Questionnaire kit | Standard AI-section answers generated from the pack | — | Covers 30 common AI questions |
| F-20 | Pricing live | The three tiers on the site, invoice template with the Udyam number | Decide pilot conversions (15 min) | 2 invoices sent |

## 6. Agent swarm (for `00-hq/agents/registry.js`)

These replace the generic b6 lean team when the world goes live. Same `A({...})` shape.

```js
A({ id:"b6.price", name:"INR Price Engine", unit:"b6", team:"tech", mission:"Price every usage row in paise from genai-prices × FBIL rate; weekly map refresh, LiteLLM cross-check.", trigger:{cron:"weekly:mon"}, runs_as:"code", code:"06-finops/src/price/", tokens:0, kpi:"0 rows priced ₹0 silently", validator:{checks:["4 a7 fixtures match","diff vs LiteLLM ≤0.5%","unpriced rows flagged"]} }),
A({ id:"b6.ingest", name:"Usage Ingestor", unit:"b6", team:"tech", mission:"Import CSV/JSONL/LiteLLM/Langfuse/OTLP into usage_event; roll up daily; purge raw at 30 days.", trigger:{event:"upload / POST"}, runs_as:"code", code:"06-finops/src/ingest/", tokens:0, kpi:"No rows lost", validator:{checks:["row counts in = out","no prompt/completion text stored","RLS per tenant"]} }),
A({ id:"b6.xray", name:"X-ray Writer", unit:"b6", team:"sales", mission:"Turn a prospect's export into the 2-page X-ray with 3 savings ideas in ₹.", trigger:{event:"export received"}, runs_as:"claude", tokens:15000, human_needed:true, kpi:"Sent within 48 h", validator:{checks:["every ₹ figure traces to a SQL query","savings stated as estimates with assumptions","export deleted after 14 days unless they sign up"]} }),
A({ id:"b6.prospect", name:"Prospect Researcher", unit:"b6", team:"sales", mission:"Weekly 25 ICP startups from Inc42/YC/Product Hunt by hand; note AI-feature evidence.", trigger:{cron:"weekly:mon"}, tokens:8000, kpi:"25 qualified a week", validator:{checks:["no scraping or bulk export","work contact only","ICP signal cited"]} }),
A({ id:"b6.pitch", name:"Pitch Writer", unit:"b6", team:"sales", mission:"≤80-word personal notes + day 3/7/14 follow-ups.", trigger:{cron:"daily"}, tokens:3000, kpi:"≥10% reply rate", validator:{checks:["no guarantees","opt-out line","stops on no"]} }),
A({ id:"b6.pack", name:"Evidence Pack Builder", unit:"b6", team:"delivery", mission:"Monthly DPDP + ISO 42001 + Art. 50 pack per customer from their logs.", trigger:{cron:"monthly"}, runs_as:"code", code:"06-finops/src/pack/", tokens:20000, human_needed:true, kpi:"Delivered by the 5th", validator:{name:"Compliance Reviewer", checks:["no ISO text copied","each DPDP item cites section/rule","'not legal advice, not certification' footer","Akhil approved"]} }),
A({ id:"b6.regwatch", name:"Regulation Watcher", unit:"b6", team:"research", mission:"Track DPDP Rules/Board notices, MeitY AI guidelines, EU AI Act guidance; update dpdp-2023.json dates.", trigger:{cron:"monthly"}, tokens:10000, kpi:"No stale date in packs", validator:{checks:["official or law-firm source per change"]} }),
A({ id:"b6.content", name:"₹ Price & DPDP Content", unit:"b6", team:"marketing", mission:"Weekly ₹ price table post + monthly DPDP-for-AI explainer.", trigger:{cron:"weekly:thu"}, tokens:5000, kpi:"1 inbound X-ray request/week by month 4", validator:{checks:["numbers from price engine","no fear-mongering, penalties quoted exactly"]} }),
A({ id:"b6.success", name:"Customer Success", unit:"b6", team:"success", mission:"Monthly: savings realised, alert noise, churn risk, upsell readiness.", trigger:{cron:"monthly"}, tokens:4000, kpi:"Net revenue retention ≥100%", validator:{checks:["metrics from database only"]} }),
```

## 7. Metrics & kill criteria

**Weekly numbers:** contacts sent (target 25), replies, X-rays requested and delivered (and hours to deliver), design partners, paid audits, MRR, ₹ of savings identified for customers (our proof number), and Supabase MB used.

**Kill criteria:**
- **Pause on 15 Jan 2027** if, after at least 150 targeted contacts, we have fewer than **5 X-rays delivered and 0 design partners sharing real data**. Time then moves to the best-performing world. The open-source repo stays up.
- **Second gate on 30 Apr 2027:** if MRR is below ₹10,000 with at least 3 customers' worth of effort spent, drop to the open-source repo plus the content page only, and revisit after the May 2027 DPDP deadline.

## 8. What I need from Akhil

- [ ] Approve the name "Ledger Peaks", the positioning line, and the price ladder, including the 3-slot founding pilot.
- [ ] Approve a **metadata-only** rule: we never accept prompts or completions, and PII scans run in the customer's repo.
- [ ] Create a free Supabase project (Mumbai region) for b6 yourself. Keys go into env settings, never into chat.
- [ ] Approve making `ledger-peaks-meter` public under MIT on Akhilkanigicharla.
- [ ] Update your LinkedIn headline ("Building an open-source ₹ cost meter + DPDP evidence for Indian AI teams"), then send 5 notes a day from Week 3.
- [ ] Complete Razorpay KYC with the Udyam number when the first prospect says yes.
- [ ] Decide on two spends when triggered: ₹3–5k for a lawyer to review the DPA and terms before the first invoice, and ~₹900 for a domain at the first paid customer.
- [ ] Never call the pack "certification" or "legal advice". This needs your sign-off on the disclaimer.

## 9. Sources

- DPDP Rules phased commencement (13 Nov 2025; 12 months for consent managers; 18 months, May 2027, for the substantive duties): [AZB & Partners](https://www.azbpartners.com/bank/indias-digital-personal-data-protection-act-phased-rollout-and-key-compliance-milestones/), [Hogan Lovells](https://ca.hoganlovells.com/en/publications/indias-digital-personal-data-protection-act-2023-brought-into-force-), [Outlook Money](https://www.outlookmoney.com/news/govt-notifies-dpdp-rules-implementation-planned-in-phases-spread-over-12-18-months)
- DPDP penalties schedule: [AMLEGALS](https://amlegals.com/penalties-under-the-digital-personal-data-protection-act2023/)
- EU AI Act Art. 50 in force 2 Aug 2026, Omnibus 2026/1744 changes: [Goodwin](https://www.goodwinlaw.com/en/insights/publications/2026/08/alerts-technology-dpc-eu-ai-act-transparency-obligations-now-in-force)
- Langfuse pricing: [langfuse.com/pricing](https://langfuse.com/pricing)
- Helicone pricing: [helicone.ai/pricing](https://www.helicone.ai/pricing)
- Portkey pricing: [portkey.ai/pricing](https://portkey.ai/pricing)
- OpenMeter / Kong: [openmeter.io/pricing](https://openmeter.io/pricing), [SiliconANGLE](https://siliconangle.com/2025/09/03/kong-acquires-openmeter-power-api-ai-monetization/)
- CloudZero pricing estimate: [CostBench](https://costbench.com/software/cloud-cost-management/cloudzero/)
- Sprinto pricing estimate: [UnderDefense](https://underdefense.com/blog/sprinto-pricing)
- Vanta pricing estimate: [Knowlee](https://www.knowlee.ai/blog/tools/vanta-pricing-2026)
- ISO 42001 cost: [Sprinto hub](https://sprinto.com/hub/iso-42001-cost/)
- GST on foreign AI tools (OIDAR, RCM 18%): [StartupTalky](https://startuptalky.com/getting-wrong-gst-chatgpt-claude-foreign-ai-tools/)
- Inc42 GenAI tracker (175 startups): [Inc42](https://inc42.com/startups/indian-genai-startup-tracker/amp/)
- Cloudflare Workers / Supabase free limits: [eastondev (Jul 2026 figures)](https://eastondev.com/blog/en/posts/dev/20261009-solo-founder-backend-stack-cloudflare-workers-supabase-node/), [Cloudflare limits](https://developers.cloudflare.com/workers/about/limits)
- Razorpay fee (~2% + GST, verify on the official page): [Dodo Payments review](https://dodopayments.com/blogs/razorpay-review)
- USD/INR ~₹95.8 (12 Oct 2026): [dollarrupee.in](https://dollarrupee.in/)
- Open-source picks, licences and test runs: `06-finops/research/a7-finops.md`

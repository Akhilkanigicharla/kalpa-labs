# Revenue engine: one sales team per business, one HQ view

Built 24 Oct 2026 at Akhil's request: "every business gets a full workforce for the 24 money jobs, and HQ gathers it all". It runs on **n8n with free models**, so it costs ₹0 and almost no Claude tokens.

## The 24 jobs (same list for every business)

| Pod | Jobs (item no.) | Agent |
|---|---|---|
| Strategy | 2 niche, 3 competitors, 4 ideal customer, 7 offer, 8 pricing | Echo, Kavi, Quant |
| Pipeline | 5 where to find customers, 6 lead plan, 9 cold emails, 10 personalised outreach, 17 follow-ups | Scout, Kavi, Chitti |
| Sales | 11 proposal, 18 call script, 19 objections, 20 case studies (template only until real pilots) | Doc, Vani |
| Marketing | 1 website, 12 landing page, 13 content plan, 14 ad creatives, 15 funnel | Forge, Kavi, Adi |
| Success | 21 onboarding system | Chitti |
| RevOps | 16 CRM automation, 22 automate repetitive tasks, 23 KPIs, 24 conversion tests | Plug, Dash, Probe |

Every draft is checked by **Guard** (rules + locked company facts) before it is saved. b7 Trading Lab only does items 2, 3, 22 and 23: SEBI, it never sells.

## Where things live (n8n Cloud, project rGMOjAIMJ48jQbPi)

| Thing | ID | What |
|---|---|---|
| Data table **KL GTM Kit** | SCUeS3YQfXS1yxhf | 168 jobs (7 × 24). `status`: todo → draft (Guard-reviewed) → approved by Akhil; `skip-sebi` for b7 |
| Data table **KL Pipeline** | Pqxl3ZzCkC69XT8w | Deals per business: stage (new, contacted, demo, proposal, won, lost), value, consent, next step |
| Data table **KL Leads** | pdD6nm9KtK73bDHw | Existing leads table, new `stream` column (b1…b7) |
| Data table **KL Knowledge** | iOJMuvV1AOu8ywr6 | Two `rules` rows every agent reads: GTM rules (verified 24 Oct) and locked company facts |
| Workflow **Kalpa Revenue Workforce** | ACjGCagrhbvnlAyV | Every 10 min: next todo job → reads that world's `PLAN.md` from GitHub + rules + the team's earlier drafts → owner agent writes → Guard lists issues (checks rules, facts and the plan) → writer fixes them → saved with a "Guard check" note. NVIDIA Nemotron free, Groq fallback. One job ≈ 7 min, so all 148 jobs take about a day |
| Workflow **Kalpa HQ Revenue Rollup** | 4jivwOaUOH8QtROZ | Daily 8:30 PM IST: consolidates all businesses (kit progress, CEO checks, leads, pipeline, won ₹) → Telegram to Akhil → full report to `00-hq/revenue/daily/<date>.md` |

Both workflows are **off** until Akhil switches them on (n8n → workflow → Active). Nothing in them sends email, WhatsApp, posts or ads: they only write drafts and reports.

## Rules the agents follow (sources in `00-hq/audit/facts.md`)
Email: real sender + address, one-click unsubscribe within 48 h, SPF/DKIM/DMARC, spam under 0.1%, small hand-picked lists. DPDP: public business contacts only, log the source, opt-out; core duties from 13 May 2027. TRAI: no unsolicited promotional calls/SMS from personal mobiles. WhatsApp: opt-in first. LinkedIn: manual only. No scraping Google Maps, Justdial, Instagram. ASCI `#ad`. SEBI: b7 never sells. No invented facts; unverified = `[TO VERIFY]`, Akhil-only = `[CEO]`.

## Akhil's part
1. Switch on both workflows: open each link in n8n and press **Publish** (2 min). Claude was not allowed to switch on scheduled runs itself.
2. Read each evening's Telegram report; open the GitHub report for any business and mark good items approved (or reply with changes).

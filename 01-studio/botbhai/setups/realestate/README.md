# BotBhai Real Estate setup

One complete automation system sold to one real estate business at a time. It runs on the shared BotBhai engine (`../../core`), but each client gets its own WhatsApp number, its own config, its own dashboard link and (optionally) its own Netlify site built with `SETUP=realestate`.

## What the client gets
1. **WhatsApp chatbot** — menu, current projects, FAQs, site visit booking in under a minute, human hand-off. Flow fields: purpose, bhk, budget, area, date, slot, name.
2. **Lead generation bot** — Meta ads (Instant lead forms (higher intent questions: budget, BHK, timeline) + Click-to-WhatsApp for retargeting) feed straight into the chatbot; lead-form leads get a WhatsApp reply within 60 seconds (`core/functions/metaleads.js`).
3. **Meta ads bot** — every morning it checks each ad's cost per lead against a ₹450 target, pauses losers (with permission) and WhatsApps the owner a report (`core/functions/adsbot.js`).
4. **Voice agent** — answers phone calls in Telugu, Hindi or English, books the same fields, sends a WhatsApp confirmation (`voice/agent.py`). Free on the website; phone numbers cost per minute.
5. **Follow-up agent** — reminders 24 h and 2 h before, after-visit message (`core/functions/reminders.js`).
6. **Owner dashboard + Excel** — live leads with hot/warm/cold scores, conversations, one-tap Excel/CSV export.

## Price (suggested launch pricing)
- Setup: **₹24,999** one-time (50% advance)
- Monthly: **₹7,999**
- Ads management: ₹5,000/month or 10% of ad spend, whichever is higher
- Voice calls: Telephony pass-through at cost + ₹2/min
- WhatsApp message fees are paid by the client directly to Meta on their own account (India, from 1 Oct 2026: marketing ≈ ₹0.86, utility ≈ ₹0.115 per message + GST; replies inside the 24-hour window are free up to 1,000 a month; chats started from Click-to-WhatsApp ads are free for 72 hours).

## Why it pays for the client
At ₹450 per Meta lead and 300 leads/month (₹1.35 lakh spend), moving site visits from 3% to 7% means 12 extra visits. At 1 booking per 5 visits, that's 2–3 extra bookings a month; one booking's brokerage or margin pays for a year of BotBhai. *(Worked example with stated assumptions; replace with the client's real numbers in the proposal.)*

## Targets we promise to track
- First response < 60 seconds for 100% of leads
- Lead → site visit 6–9% (from 2–4%)
- Site visit show-up ≥ 45%
- Cost per site visit tracked weekly

## Meta ads playbook
- Objective: Instant lead forms (higher intent questions: budget, BHK, timeline) + Click-to-WhatsApp for retargeting
- Budget: ₹1500–₹5000 per day (client's money), 20 km radius
- Audience: Age 28–55, 15–25 km of the project, IT corridors (Gachibowli, HITEC City, Financial District), interests: real estate, home loans, NRI (separate campaign)
- Ad angles: Ready-to-move 2/3 BHK with price from ₹X; Free site visit with pick-up; EMI starting ₹X/month; RERA-approved, possession date
- Lead form questions: Budget; BHK; When do you plan to buy? (0–3 months / 3–6 / 6+); Preferred area
- Guard rules: judge after ₹1500 spend; pause above 1.6× target cost per lead; suggest +20% budget below 0.7× target.

## WhatsApp templates (submit with `node tools/create-templates.js realestate <WABA_ID>`)
| Key | Template | Category | Text |
|---|---|---|---|
| lead_welcome | `bb_re_welcome` | MARKETING | Hi {{1}}, thanks for enquiring with {{2}} 🏡. I'm the assistant — tap *Book site visit* and I'll shortlist homes for your budget, or *Call me* for an advisor. |
| day_before | `bb_re_reminder_day` | UTILITY | Hi {{1}}, your site visit with {{2}} is tomorrow ({{3}}) at {{4}} in {{5}}. Reply *1* to confirm or *2* to reschedule. Free pick-up available. |
| two_hours | `bb_re_reminder_2h` | UTILITY | Hi {{1}}, your {{2}} site visit is at {{3}} today. Our advisor will call you 30 minutes before. 📍 {{4}} |
| after_visit | `bb_re_followup` | UTILITY | Hi {{1}}, thanks for visiting with {{2}}. Shall we share the price sheet, floor plans and home-loan estimate for {{3}}? Reply *Yes* and we'll send them. |
| winback | `bb_re_winback` | MARKETING | Hi {{1}}, new launch prices are out at {{2}}. Reply *Details* for the latest {{3}} options in your budget. |
| owner_report | `bb_owner_report` | UTILITY | Daily update from BotBhai: {{1}}. Reply to this message to see the full report. |

## Agent swarm for this setup
| Agent | Side | What it does | Its validator checks |
|---|---|---|---|
| Prospector | BotBhai sales | Runs the lead finder for this industry in a city, scores businesses | Every row has a phone or address; no duplicates; DND/"do not contact" respected |
| Pitch Writer | BotBhai sales | Writes a personal WhatsApp/email intro + demo link per prospect | No false claims; mentions the prospect by name; under 80 words |
| Demo Builder | BotBhai sales | Copies this setup's config with the prospect's name, prices and address | Demo answers 10 test questions correctly |
| Onboarding Ops | Delivery | Runs the client checklist (Meta business, WhatsApp number, templates, Page, ad account) | All checklist items ticked; test message received |
| Concierge | Delivery | WhatsApp + website chatbot (bookings, prices, FAQs, hand-off) | Weekly review of "unanswered" questions; no medical/legal/financial advice |
| Speed-to-Lead | Delivery | Meta lead form → WhatsApp welcome in under 60 seconds, owner alert | 100% of leads messaged; failures retried and reported |
| Voice Receptionist | Delivery | Answers calls, books, requests call-backs; calls consented leads (if enabled) | Calls only 9 AM–9 PM; recordings disclosed; stop requests honoured |
| Ad Strategist | Delivery | Writes ad copy and creative briefs from this setup's angles; picks audiences | Meta ad policy check; no before/after body claims (gym); RERA facts only (real estate) |
| Ad Guardian | Delivery | Daily: judges each ad by cost per lead, pauses losers (if allowed), reports | Never pauses more than half the ads in one day without owner OK |
| Follow-up Agent | Delivery | Reminders 24 h and 2 h before, after-visit message, renewals, win-backs | One message per window; opted-out contacts never messaged |
| Reporter | Delivery | Owner dashboard, Excel export, Monday WhatsApp summary | Numbers match the database; client sees only their own data |

## Voice agent rules
- Role: Pre-sales executive of a real estate firm
- Goals: Call every new lead within 2 minutes (consented Meta form leads only); Qualify: buy/rent, BHK, budget, area, timeline; Book a site visit and confirm on WhatsApp
- Never: Make claims beyond the RERA-registered project details; Promise loan approval or returns; Call before 9 AM or after 9 PM, or anyone who said stop
- Opening line: "Hello, this is the Skyline Homes assistant calling about the enquiry you just made on Facebook. Is this a good time for two minutes?"

## Client onboarding checklist (about 2–5 days, mostly Meta approvals)
1. Client creates or shares a Meta Business portfolio and a Facebook Page (free).
2. New phone number (SIM not used on the WhatsApp app) added in WhatsApp Manager; display name approved.
3. Client adds a payment method in WhatsApp Manager (they pay Meta directly).
4. We add the client row in Supabase, submit templates, connect the Page's lead forms to our webhook.
5. Fill config: business name, address, hours, prices, slots, review link, owner WhatsApp.
6. Run 10 test conversations; owner approves; go live; send the dashboard link.
7. Week 1 ads: 2–3 creatives per angle, ₹1500/day; Ad Guardian starts judging after day 3.

## Evidence we found (read with care: most are vendor case studies)
- [Speed to lead: contacting within a minute vs later, and Indian site-visit benchmarks (Sell.Do; several figures unsourced)](https://www.sell.do/blog/speed-to-lead-real-estate-2026)
- [AI calling agents in Indian real estate: time-to-first-dial 45 min–8 h → 30–90 s; site visits per 100 leads 2–4 → 5–9 (vendor estimates)](https://caller.digital/blog/ai-calling-agent-real-estate-india-2026)
- [WhatsApp lead capture for Indian developers (Hyperleap)](https://hyperleap.ai/blog/whatsapp-real-estate-developers-india-lead-capture)

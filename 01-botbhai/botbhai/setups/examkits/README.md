# BotBhai Exam Kits (coaching institutes) setup

One complete automation system sold to one exam kits (coaching institutes) business at a time. It runs on the shared BotBhai engine (`../../core`), but each client gets its own WhatsApp number, its own config, its own dashboard link and (optionally) its own Netlify site built with `SETUP=examkits`.

## What the client gets
1. **WhatsApp chatbot** — menu, courses, kits & fees, FAQs, quiz booking in under a minute, human hand-off. Flow fields: service, name.
2. **Lead generation bot** — Meta ads (Click-to-WhatsApp: free quiz / demo class (72-hour free messaging window)) feed straight into the chatbot; lead-form leads get a WhatsApp reply within 60 seconds (`core/functions/metaleads.js`).
3. **Meta ads bot** — every morning it checks each ad's cost per lead against a ₹100 target, pauses losers (with permission) and WhatsApps the owner a report (`core/functions/adsbot.js`).
4. **Voice agent** — answers phone calls in Telugu, Hindi or English, books the same fields, sends a WhatsApp confirmation (`voice/agent.py`). Free on the website; phone numbers cost per minute.
5. **Follow-up agent** — reminders 24 h and 2 h before, after-visit message, renewals 7/3/1 days before expiry and win-backs (`core/functions/reminders.js`).
6. **Owner dashboard + Excel** — live leads with hot/warm/cold scores, conversations, one-tap Excel/CSV export.

## Price (suggested launch pricing)
- Setup: **₹14,999** one-time (50% advance)
- Monthly: **₹4,999**
- Ads management: ₹3,000/month (ad spend paid by the institute)
- WhatsApp message fees are paid by the client directly to Meta on their own account (India, from 1 Oct 2026: marketing ≈ ₹0.86, utility ≈ ₹0.115 per message + GST; replies inside the 24-hour window are free up to 1,000 a month; chats started from Click-to-WhatsApp ads are free for 72 hours).

## Why it pays for the client
A ₹12,000 batch needs 1 extra admission a quarter to cover BotBhai. Quiz → demo → admission funnels typically run 20% → 25%: 500 quiz takers → 100 demos → 25 admissions. *(Worked example with stated assumptions; replace with the client's real numbers in the proposal.)*

## Targets we promise to track
- Quiz takers → demo bookings ≥ 20%
- Demo → admission ≥ 25%
- Fee collected on time ≥ 90%
- Daily-question list growth +200/month

## Meta ads playbook
- Objective: Click-to-WhatsApp: free quiz / demo class (72-hour free messaging window)
- Budget: ₹500–₹1500 per day (client's money), 15 km radius
- Audience: 18–30, Telangana/AP, interests: TSPSC, SSC, banking exams, government jobs; Telugu + English creatives
- Ad angles: Free mock quiz: check your rank in 2 minutes; Free demo class with topper faculty; Previous-year selections (real, with consent); Fee instalments available
- Guard rules: judge after ₹500 spend; pause above 1.6× target cost per lead; suggest +20% budget below 0.7× target.

## WhatsApp templates (submit with `node tools/create-templates.js examkits <WABA_ID>`)
| Key | Template | Category | Text |
|---|---|---|---|
| lead_welcome | `bb_exam_welcome` | MARKETING | Hi {{1}} 📚 Thanks for your interest in {{2}}. Tap *Free quiz* to check your level in 2 minutes, or *Demo class* to book a free class. |
| day_before | `bb_exam_demo_day` | UTILITY | Hi {{1}}, your free demo class at {{2}} is tomorrow ({{3}}) at {{4}}. Reply *1* to confirm. |
| two_hours | `bb_exam_demo_2h` | UTILITY | Hi {{1}}, your demo class at {{2}} starts at {{3}} today. 📍 {{4}} |
| after_visit | `bb_exam_after_demo` | MARKETING | Hi {{1}}, hope you enjoyed the demo at {{2}}! The {{3}} batch has limited seats. Reply *Join* for fee details and instalment options. |
| renew_7 | `bb_exam_fee_7` | UTILITY | Hi {{1}}, your next {{2}} fee instalment at {{3}} is due on {{4}}. Reply *Pay* for the link. |
| renew_1 | `bb_exam_fee_1` | UTILITY | Hi {{1}}, reminder: your {{2}} instalment at {{3}} is due tomorrow ({{4}}). Reply *Pay* for the link. |
| daily_question | `bb_exam_daily_q` | MARKETING | Good morning {{1}} ☀️ Today's {{2}} question: {{3}} Reply A, B, C or D. |
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
- Role: Admissions counsellor at a coaching institute
- Goals: Book free demo classes; Explain batches, timings and fees from config; Send the brochure on WhatsApp
- Never: Guarantee selection or ranks; Quote fees not in config; Pressure students or parents
- Opening line: "Namaskaram, Vidya Competitive Academy. Which exam are you preparing for?"

## Client onboarding checklist (about 2–5 days, mostly Meta approvals)
1. Client creates or shares a Meta Business portfolio and a Facebook Page (free).
2. New phone number (SIM not used on the WhatsApp app) added in WhatsApp Manager; display name approved.
3. Client adds a payment method in WhatsApp Manager (they pay Meta directly).
4. We add the client row in Supabase, submit templates, connect the Page's lead forms to our webhook.
5. Fill config: business name, address, hours, prices, slots, review link, owner WhatsApp.
6. Run 10 test conversations; owner approves; go live; send the dashboard link.
7. Week 1 ads: 2–3 creatives per angle, ₹500/day; Ad Guardian starts judging after day 3.

## Evidence we found (read with care: most are vendor case studies)
- [WhatsApp for coaching institutes: admissions, demo classes, fee reminders 7/3/1 days (AiSensy; vendor claims)](https://m.aisensy.com/blog/whatsapp-for-coaching-institute-or-tuition-center/)
- [Competitive-exam student inquiry agent (Tars)](https://hellotars.com/ai-agents/competitive-exam-prep-student-inquiry-agent)
- [Social media case study for a medical coaching institute (Dinero Tech Labs)](https://www.dinerotechlabs.com/case-study/smm-case-study-leading-medical-coaching-institute/)

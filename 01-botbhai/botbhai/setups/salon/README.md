# BotBhai Salon setup

One complete automation system sold to one salon business at a time. It runs on the shared BotBhai engine (`../../core`), but each client gets its own WhatsApp number, its own config, its own dashboard link and (optionally) its own Netlify site built with `SETUP=salon`.

## What the client gets
1. **WhatsApp chatbot** — menu, price list, FAQs, booking booking in under a minute, human hand-off. Flow fields: service, date, slot, name.
2. **Lead generation bot** — Meta ads (Click-to-WhatsApp (messages) — every chat is free to reply to for 72 hours) feed straight into the chatbot; lead-form leads get a WhatsApp reply within 60 seconds (`core/functions/metaleads.js`).
3. **Meta ads bot** — every morning it checks each ad's cost per lead against a ₹120 target, pauses losers (with permission) and WhatsApps the owner a report (`core/functions/adsbot.js`).
4. **Voice agent** — answers phone calls in Telugu, Hindi or English, books the same fields, sends a WhatsApp confirmation (`voice/agent.py`). Free on the website; phone numbers cost per minute.
5. **Follow-up agent** — reminders 24 h and 2 h before, after-visit message (`core/functions/reminders.js`).
6. **Owner dashboard + Excel** — live leads with hot/warm/cold scores, conversations, one-tap Excel/CSV export.

## Price (suggested launch pricing)
- Setup: **₹9,999** one-time (50% advance)
- Monthly: **₹2,999**
- Ads management: ₹2,000/month (ad spend paid by the salon to Meta)
- WhatsApp message fees are paid by the client directly to Meta on their own account (India, from 1 Oct 2026: marketing ≈ ₹0.86, utility ≈ ₹0.115 per message + GST; replies inside the 24-hour window are free up to 1,000 a month; chats started from Click-to-WhatsApp ads are free for 72 hours).

## Why it pays for the client
A salon doing 300 bookings/month at ₹600 average with 12% no-shows loses ₹21,600/month. Cutting no-shows to 4% recovers about ₹14,400/month, and 15 extra bookings from 24×7 replies add ₹9,000. Against ₹2,999/month, the salon is about 7× ahead. *(Worked example with stated assumptions; replace with the client's real numbers in the proposal.)*

## Targets we promise to track
- Chats → bookings ≥ 25%
- No-show rate ≤ 5% (from 10–15%)
- Google reviews +20/month
- Repeat visit within 45 days ≥ 40%

## Meta ads playbook
- Objective: Click-to-WhatsApp (messages) — every chat is free to reply to for 72 hours
- Budget: ₹300–₹700 per day (client's money), 5 km radius
- Audience: Women 20–45 (and men 18–40 for grooming), 3–5 km radius, interests: beauty salon, bridal makeup, hair care
- Ad angles: Combo offer: hair spa + haircut; Bridal / party makeup trial booking; Weekday afternoon discount to fill empty chairs; Before/after hair colour reels (client's real photos, with consent)
- Guard rules: judge after ₹300 spend; pause above 1.6× target cost per lead; suggest +20% budget below 0.7× target.

## WhatsApp templates (submit with `node tools/create-templates.js salon <WABA_ID>`)
| Key | Template | Category | Text |
|---|---|---|---|
| lead_welcome | `bb_salon_welcome` | MARKETING | Hi {{1}}, thanks for your interest in {{2}}! 💇 Tap *Book now* to pick a slot, or *Price list* to see services. This week: hair spa + haircut combo at a special price. |
| day_before | `bb_salon_reminder_day` | UTILITY | Hi {{1}}, reminder: your {{2}} at {{3}} is tomorrow ({{4}}) at {{5}}. Reply *1* to confirm or *2* to reschedule. |
| two_hours | `bb_salon_reminder_2h` | UTILITY | Hi {{1}}, see you at {{2}} today at {{3}}. 📍 {{4}} |
| after_visit | `bb_salon_review` | MARKETING | Hi {{1}}, thank you for visiting {{2}}! 💖 If you loved your {{3}}, a quick Google review helps us a lot: {{4}} |
| winback | `bb_salon_winback` | MARKETING | Hi {{1}}, we miss you at {{2}}! Your next visit gets 15% off any service this month. Reply *Book* to pick a slot. |
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
- Role: Front desk of a salon
- Goals: Book or reschedule a slot; Share prices from the price list only; Take bridal enquiries and hand to the owner
- Never: Promise a stylist by name unless the config lists them; Quote prices not in the price list; Give skin or medical advice
- Opening line: "Namaste, Glow Studio salon, how can I help you today?"

## Client onboarding checklist (about 2–5 days, mostly Meta approvals)
1. Client creates or shares a Meta Business portfolio and a Facebook Page (free).
2. New phone number (SIM not used on the WhatsApp app) added in WhatsApp Manager; display name approved.
3. Client adds a payment method in WhatsApp Manager (they pay Meta directly).
4. We add the client row in Supabase, submit templates, connect the Page's lead forms to our webhook.
5. Fill config: business name, address, hours, prices, slots, review link, owner WhatsApp.
6. Run 10 test conversations; owner approves; go live; send the dashboard link.
7. Week 1 ads: 2–3 creatives per angle, ₹300/day; Ad Guardian starts judging after day 3.

## Evidence we found (read with care: most are vendor case studies)
- [A beauty salon using an AI WhatsApp admin reports no-shows falling from 15% to 3% and bookings up 40% (vendor case study, not independently verified)](https://www.aiinsider.it.com/en/cases/beauty-salon-ai-admin)
- [Aimy: salon bookings up 30% with WhatsApp automation (Bird case study)](https://www.casestudies.com/company/bird/case-study/aimy-boosts-salon-bookings-30-with-bird)
- [Zapis.kz: salon booking via WhatsApp automation (Infobip customer story)](https://www.infobip.com/customer/zapis-kz)
- [Indian salons using WhatsApp marketing (MioSalon blog)](https://blog.miosalon.com/?p=35058)

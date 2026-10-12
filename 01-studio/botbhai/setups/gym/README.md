# BotBhai Gym setup

One complete automation system sold to one gym business at a time. It runs on the shared BotBhai engine (`../../core`), but each client gets its own WhatsApp number, its own config, its own dashboard link and (optionally) its own Netlify site built with `SETUP=gym`.

## What the client gets
1. **WhatsApp chatbot** — menu, membership plans, FAQs, free trial booking in under a minute, human hand-off. Flow fields: goal, date, slot, name.
2. **Lead generation bot** — Meta ads (Click-to-WhatsApp: free trial offer) feed straight into the chatbot; lead-form leads get a WhatsApp reply within 60 seconds (`core/functions/metaleads.js`).
3. **Meta ads bot** — every morning it checks each ad's cost per lead against a ₹150 target, pauses losers (with permission) and WhatsApps the owner a report (`core/functions/adsbot.js`).
4. **Voice agent** — answers phone calls in Telugu, Hindi or English, books the same fields, sends a WhatsApp confirmation (`voice/agent.py`). Free on the website; phone numbers cost per minute.
5. **Follow-up agent** — reminders 24 h and 2 h before, after-visit message, renewals 7/3/1 days before expiry and win-backs (`core/functions/reminders.js`).
6. **Owner dashboard + Excel** — live leads with hot/warm/cold scores, conversations, one-tap Excel/CSV export.

## Price (suggested launch pricing)
- Setup: **₹9,999** one-time (50% advance)
- Monthly: **₹3,499**
- Ads management: ₹2,000/month (ad spend paid by the gym)
- WhatsApp message fees are paid by the client directly to Meta on their own account (India, from 1 Oct 2026: marketing ≈ ₹0.86, utility ≈ ₹0.115 per message + GST; replies inside the 24-hour window are free up to 1,000 a month; chats started from Click-to-WhatsApp ads are free for 72 hours).

## Why it pays for the client
A 400-member gym renewing at 60% loses 160 members a year. Lifting renewals 10 points keeps 40 more members ≈ ₹1.6 lakh for every renewal on a ₹3,999 quarterly plan (≈ ₹6.4 lakh a year if they keep renewing), plus win-backs. Cost: ₹42,000/year. *(Worked example with stated assumptions; replace with the client's real numbers in the proposal.)*

## Targets we promise to track
- Trial → member ≥ 30%
- Renewal rate +15–20 points
- Win-back 10–20% of lapsed members
- Trial show-up ≥ 60%

## Meta ads playbook
- Objective: Click-to-WhatsApp: free trial offer
- Budget: ₹400–₹1000 per day (client's money), 4 km radius
- Audience: 18–45 within 3–5 km, interests: fitness, weight loss, yoga; separate women-only batch ad
- Ad angles: Free trial + body-composition check; Women-only batch with female trainers; New-year / summer transformation challenge; Member transformation stories (with consent)
- Guard rules: judge after ₹400 spend; pause above 1.6× target cost per lead; suggest +20% budget below 0.7× target.

## WhatsApp templates (submit with `node tools/create-templates.js gym <WABA_ID>`)
| Key | Template | Category | Text |
|---|---|---|---|
| lead_welcome | `bb_gym_welcome` | MARKETING | Hey {{1}} 💪 Your free trial at {{2}} is ready to book. Tap *Book trial* to pick a time, or *Plans* to see memberships. |
| day_before | `bb_gym_reminder_day` | UTILITY | Hi {{1}}, your free trial at {{2}} is tomorrow ({{3}}) at {{4}}. Bring sports shoes and water. Reply *1* to confirm. |
| two_hours | `bb_gym_reminder_2h` | UTILITY | Hi {{1}}, see you at {{2}} at {{3}} today! 📍 {{4}} |
| after_visit | `bb_gym_trial_followup` | MARKETING | Hi {{1}}, great work at your trial at {{2}}! Join this week and get the annual plan at the trial-day price. Reply *Join* and we'll send the payment link. |
| renew_7 | `bb_gym_renew_7` | UTILITY | Hi {{1}}, your {{2}} at {{3}} ends on {{4}}. Renew this week to keep your streak going — reply *Renew* for the payment link. |
| renew_3 | `bb_gym_renew_3` | UTILITY | Hi {{1}}, 3 days left on your {{2}} at {{3}} (ends {{4}}). Reply *Renew* to continue without a break. |
| renew_1 | `bb_gym_renew_1` | UTILITY | Hi {{1}}, your {{2}} at {{3}} ends tomorrow ({{4}}). Reply *Renew* and we'll keep your slot. |
| winback | `bb_gym_winback` | MARKETING | Hi {{1}}, we miss you at {{2}}! Come back this month and get 2 weeks free on any plan. Reply *Back* to restart. |
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
- Role: Front desk of a gym
- Goals: Book free trials; Explain plans from the price list; Handle renewals and freezes, hand payment to the desk
- Never: Give medical or diet prescriptions; Promise weight-loss results; Offer discounts not in config
- Opening line: "Hi, IronPulse Fitness, how can I help you?"

## Client onboarding checklist (about 2–5 days, mostly Meta approvals)
1. Client creates or shares a Meta Business portfolio and a Facebook Page (free).
2. New phone number (SIM not used on the WhatsApp app) added in WhatsApp Manager; display name approved.
3. Client adds a payment method in WhatsApp Manager (they pay Meta directly).
4. We add the client row in Supabase, submit templates, connect the Page's lead forms to our webhook.
5. Fill config: business name, address, hours, prices, slots, review link, owner WhatsApp.
6. Run 10 test conversations; owner approves; go live; send the dashboard link.
7. Week 1 ads: 2–3 creatives per angle, ₹400/day; Ad Guardian starts judging after day 3.

## Evidence we found (read with care: most are vendor case studies)
- [WhatsApp CRM for gyms: renewal, win-back and churn ranges (ChatDaddy; author's estimates, no sources)](https://chatdaddy.tech/blog/whatsapp-crm-gym)
- [WhatsApp marketing strategies for gyms (AiSensy)](https://m.aisensy.com/blog/whatsapp-marketing-for-gyms-and-fitness-centers/)
- [Gym customer-service automation case study (Builts)](https://builts.ai/blog/gym-fitness-studio-customer-service-automation-case-study/)

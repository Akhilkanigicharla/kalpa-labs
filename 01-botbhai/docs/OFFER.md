# BotBhai offer, v0 (30 Oct 2026)

Built from the first 12 of 24 agent research jobs (KL Tasks, Vigil PASS). Figures marked UNVERIFIED need a second source before they go in front of a customer (CLAUDE.md rule 8). v1 lands when the rest of the swarm finishes.

## 1. What a salon gets (only built features)
- **Customers chat** on the salon's WhatsApp, the website chat or Telegram, in Telugu, Hindi or English. They book service → day → time → name in under a minute; a taken slot gets the nearest free times.
- **Reminders** 24 h and 2 h before; after-visit message.
- **Owner tools (web login, phone-friendly):** dashboard (today's bookings, 30-day report, Excel export), shared inbox (take over any chat, hand back), billing page, GST receipt for each paid booking.
- **Owner alerts** for complaints, hand-overs and new bookings; a person takes over angry chats.
- **Not included yet:** payments inside chat, Google reviews, Instagram posts (Social Team add-on is planned, not sold).

## 2. What it costs us per salon (UNVERIFIED where marked)
- Fixed: ₹0 on free tiers (Netlify, Supabase, n8n, free LLMs + our router) up to the first upgrade (Supabase Pro ≈ US$25/month, shared by all salons).
- WhatsApp (Meta, per delivered message, India): utility ≈ ₹0.115, marketing ≈ ₹0.86, + 18% GST; replies inside the 24-hour customer window are free.
- Example: 40 bookings × 4 utility messages + 10 promos ≈ ₹32/month per salon incl. GST.
- **Gross margin at ₹1,499/month ≈ 97% before Akhil's time.** The real cost is setup and support hours (to be measured in the pilot).

## 3. Price (draft, to test in pilots)
- Free 14-day pilot, then ₹2,999 setup + ₹1,499/month (months 1–3), ₹1,999 after.
- Market today (agent research, re-check before quoting): DINGG ₹999–2,499; MioSalon ₹999–2,500; Cleomitra from ₹499; AiSensy ₹1,500 + per message; Interakt ₹2,799; WATI ₹4,999; Salonist from US$59. BotBhai sits in the middle and is the only one built for Telugu chat booking.
- Open: whether the setup fee scares small salons (price-ladder job still running).

## 4. Why a salon pays
- No-shows: 10–30% without reminders; automated reminders cut them by about a quarter (studies, UNVERIFIED primary check). For a small salon that is several lost appointments a week.
- Missed WhatsApp messages at night and during busy hours become bookings.
- Owner's top fear: "the bot mangles bookings and message costs spiral" → answered by the calendar lock, human takeover and a fixed monthly price.

## 5. How we find salons (no contacts needed, no scraping)
1. **Walk-in visits** near home with the printed card (`docs/sales/card-a5.pdf`) and a 2-minute demo on the phone (DINGG sells demo-first).
2. **Beauty product distributors and beauty academies:** they visit or train many salons; offer them a referral fee.
3. **Salon associations** (e.g. HBF India) and local beauty events.
4. **Referral:** one free month for every salon that brings another.
5. Our own posts (A129 marketing department), only after Akhil approves.

## 6. Pilot (from 16 Nov)
- Prove in 14 days: ≥5 real bookings by the bot, reminders sent for every booking, owner stops answering booking calls.
- Measured from the dashboard; day-14 talk shows the numbers, then asks yes/no. No invoice before a yes.

## 7. Legal (must be done before the first pilot)
- DPDP: salon = data fiduciary, Kalpa = processor; agreement clause + customer privacy notice (`docs/sales/agreement.pdf`, `privacy-notice.pdf`, C23 lawyer/CA read).
- WhatsApp: opt-in, approved utility templates (booking confirmation, reminder), no unsolicited marketing.

## 8. Blockers, honestly
- **WhatsApp is what salon customers use.** Meta's "coexistence" lets a salon keep its WhatsApp Business app and connect the same number to BotBhai (app must be opened every 13 days, per Meta docs, agent-sourced). That needs our Meta app working (C02 parked). Telegram + website chat can run a pilot but are weaker.
- No reference customer yet; first pilot is the proof.

# BotBhai Salon — Requirements Pack (v1, 12 Oct 2026)

Audience: developer building the salon pilot, QA agent automating tests, Kalpa Labs owner pricing the deal.
Product: BotBhai Salon setup — ₹9,999 setup + ₹2,999/month (+ ₹2,000/month optional ads management), sold to salons in Hyderabad.
Sources read: `README.md`, `setups/salon/README.md`, `setups/salon/bot.config.js`, `setups/salon/templates.json`, `setups/salon/setup.meta.json`, `core/engine.js`, `core/humanize.js`, `core/automations.js`, `core/functions/{whatsapp,reminders,leads,chat,metaleads,adsbot,_lib,_fake}.js`, `voice/agent.py`, `supabase/schema.sql`, `web/index.src.html`.
Behaviour claims marked "(verified)" were checked by running `core/engine.js` with `TZ=UTC` (Netlify runs in UTC) on 12 Oct 2026.

Status legend used in section 3:
- **EXISTS** — works today; file/function cited.
- **PARTIAL** — some of it exists; the missing part is named.
- **GAP** — nothing in code yet.

---

## 0. Code facts the rest of this document depends on

| # | Fact | Where |
|---|---|---|
| F1 | The engine is rule-based. Booking flow = 4 fixed steps: service → date → slot → name. | `engine.js` `createBot`, `handleStep`; `bot.config.js` `steps` |
| F2 | Slots are one fixed list for every day (`11:00 AM, 1:00 PM, 4:00 PM, 7:00 PM`). There are no service durations, no stylists, no opening-day rules. | `bot.config.js` `steps[2].choices` |
| F3 | Capacity is one number per slot for the whole salon (`config.capacity`, default unlimited). | `engine.js` `freeSlots` |
| F4 | One session and one lead row per WhatsApp number. Booking data lives in `state.data`, so a second booking from the same phone overwrites the first in the session and in `leads.details`. The `bookings` table keeps both rows. | `engine.js` `startFlow` (resets `state.data`); `schema.sql` `leads unique(client_id, contact)` |
| F5 | Reminders read `leads.details` (not `bookings`) and record sent flags in `leads.details.reminders`. | `automations.js` `dueReminders`; `functions/reminders.js` |
| F6 | **Bug:** the webhook upserts `leads.details` from the engine snapshot on every inbound message. The snapshot has no `reminders` key, and PostgREST `merge-duplicates` replaces the whole jsonb column. Any customer message after a reminder therefore wipes the sent flags, and the next hourly run sends the same reminder again. The test fake (`_fake.js`) deep-merges rows, so tests don't catch this. | `functions/whatsapp.js` (leads upsert); `_fake.js` |
| F7 | **Bug:** the "day before" template says "Reply *1* to confirm or *2* to reschedule" and has buttons Confirm/Reschedule. Engine behaviour (verified): "Confirm" → "Sorry, I didn't quite get that" + menu; "1" → starts a **new booking**; "2" → price list. Only "Reschedule" works. | `templates.json` `day_before`; `engine.js` `handle` |
| F8 | **Bug:** time-of-day checks use server-local time. On Netlify (UTC) at 6:00 PM IST, today's 1:00 PM and 4:00 PM slots are still offered (verified). The webhook does not pass `meta.now`, so between 00:00 and 05:30 IST, "today" means yesterday's date. | `engine.js` `freeSlots`, `parseDate`; `whatsapp.js` (`bot.handle` call) |
| F9 | **Bug:** a bare number in the slot step is read as an option index. "4" means option 4 (7:00 PM), not 4 PM (verified). "7pm" and "evening" are rejected. | `engine.js` `pickChoice` |
| F10 | Voice bookings write only `leads`, never `bookings`, and skip the capacity check, so voice and WhatsApp can double-book a chair. | `voice/agent.py` `book()` |
| F11 | Owner alerts use a free-form text message. Meta only delivers free-form text inside the 24-hour customer-service window, so alerts fail silently (logged only) once the owner hasn't messaged the number for 24 h. | `whatsapp.js` (`notify_owner`/`handoff` loop) |
| F12 | After a handoff, the bot keeps auto-replying. There is no "human is handling this" pause and no inbox where staff can reply from the BotBhai number. | `engine.js` `key === "human"` |
| F13 | Nothing sets `bookings.status` to `completed` or `no_show`. Because of that, `after_visit` (the review ask) and `refer` also go to customers who never came. | `schema.sql` `bookings.status`; `automations.js` `dueReminders` |
| F14 | Bridal makeup is in the catalog, so it can be booked like a 1-hour haircut (verified: "Bridal makeup, Thu 19 Nov 11:00 AM" got confirmed). | `bot.config.js` `catalog` |
| F15 | The language layer detects Telugu/Hindi script plus romanized Tenglish/Hinglish and translates replies with Groq. A validator rejects any translation that changes a number, ₹ amount, time or URL. **But** intent matching is English-only. Verified: "repu haircut kavali", "kitna hai facial", "kal facial karna hai", "mee salon ekkada undi" and "హాయ్" (Telugu "hi") all get "didn't get that". | `humanize.js` `detectLanguage`, `mirrorLanguage`; `engine.js` `GREET` (`\b` doesn't work after Telugu script) |
| F16 | "hair cut" (two words) is read as **Hair spa**. "haircut" and "ladies haircut" are read as **Haircut (men)** (verified). | `engine.js` `pickChoice` word scoring |
| F17 | "home visit" triggers the booking flow, not the home-service FAQ, because `visit` is a booking keyword checked before the FAQs (verified). | `engine.js` intent regex order |
| F18 | Dashboard: `leads.js` returns leads and the last 500 messages for a secret token. The web page exports leads to Excel/CSV (SheetJS). There is no calendar or bookings view. | `functions/leads.js`; `web/index.src.html` `#x-xlsx` |
| F19 | Referral code (`REF-XXXX`) is generated and detected, and the referrer is notified. Rewards are not tracked. | `automations.js` `referralCode`; `engine.js` `handle` (REF match) |
| F20 | Win-back exists only for the `members` table (gym/coaching expiry). The salon `winback` template is never sent. | `automations.js` `dueRenewals`; `reminders.js` |
| F21 | There is no broadcast/campaign sender and no marketing opt-in flag. `STOP` opts a contact out in the session only (`state.optedOut`, `leads.status = opted_out`). | `engine.js` |
| F22 | There is no billing of salons (BotBhai → salon) anywhere. | — |

---

## 1. Personas

### Salon side
**Sunitha Reddy — Owner, 38, unisex salon, 4 chairs, Kukatpally/Jubilee Hills**
- Goals: full chairs Mon–Thu afternoons; bridal bookings in Nov–Feb muhurtham season; 4.5★+ on Google; a clear daily number for her UPI + cash collections.
- Frustrations: staff don't answer WhatsApp after 9 PM; no-shows on Saturday evening slots she turned others away for; a stylist leaving takes clients with them; she pays ₹2,000+ a month to "digital marketing" people with no proof.
- Language: Telugu at home, English/Tenglish with customers ("Madam, slot full undi, repu 4 ki rāndi"). Reads WhatsApp, not dashboards. Wants a one-line WhatsApp summary.

**Farhana — Receptionist, 24, also does threading**
- Goals: fewer calls while she's with a client; a single list of today's appointments; not getting blamed for double bookings.
- Frustrations: 3 phones (salon mobile, her own, landline); customers asking "price entha?" 40 times a day; walk-ins arguing with booked customers.
- Language: Hindi/Urdu-Hinglish with Old City and Tolichowki customers, Telugu with locals, basic English. Types fast, with typos and voice notes.

**Raju — Senior stylist, 31, men's and women's cuts**
- Goals: knows his day in advance; regulars ask for him by name; gets a fair share of high-ticket (colour, keratin) work.
- Frustrations: back-to-back bookings with no lunch break; a 2-hour keratin booked in a 1-hour slot; customers who arrive 40 minutes late.
- Language: Telugu/Hindi. Uses WhatsApp voice notes. Will never open a dashboard. Needs his day's list as a WhatsApp message at 9:30 AM.

### Customer side
**Keerthana — College student, 20, CBIT/Osmania, Gachibowli PG**
- Goals: haircut + eyebrows under ₹500; student offers; quick booking from Instagram ads late at night.
- Frustrations: hidden prices ("call for price"); being upsold a hair spa; salons not replying to DMs.
- Language: Tenglish with English letters ("bro slot unda repu evening ki?", "entha haircut ki"). Heavy abbreviations (tmrw, pls, eve), emojis, sends at 11:30 PM.

**Aisha — Working woman, 29, IT at HITEC City, lives in Kondapur**
- Goals: weekend facial/hair spa without waiting; reminders, because she forgets; UPI payment; sometimes books for her mother.
- Frustrations: waiting 30 minutes despite a booking; inconsistent prices; calls during office hours.
- Language: Hinglish/English ("Can I get a slot Sat 11ish? kitna lagega for facial + threading"). Books for others ("for my mom").

**Sravani — Bride-to-be, 26, wedding in Jan (muhurtham season), family in Vijayawada + Hyderabad**
- Goals: trial before booking; package for haldi, mehendi, wedding and reception; a price that fits a ₹40k–₹1L budget; artist availability on the muhurtham date.
- Frustrations: vague "starting from ₹15,000" quotes; artists double-booked on peak muhurtham dates; no portfolio.
- Language: English + Telugu, very detailed questions, often with mother/sister in the conversation; haggles ("last price entha?"). High-value lead (₹15k–₹80k): must reach a human fast.

**Ramesh — Regular men's haircut customer, 42, businessman, Ameerpet**
- Goals: same barber, same cut, every 3–4 weeks; Sunday morning; in and out in 30 minutes.
- Frustrations: Sunday morning queue; menus with 6 options when he just wants "usual"; discovering on Tuesday that the salon is closed (many traditional Hyderabad barber shops close on Tuesdays).
- Language: Telugu-first, short Tenglish/Hinglish ("cutting ki vastha sunday 10ki", "bhai Sunday subah"). Types "cutting" and "shave", not "Haircut (men)". Likely to call rather than chat.

---

## 2. The salon owner's real day — where money leaks

| Time (IST) | What happens | Money leak (worked example: 4 chairs, avg ticket ₹600) | BotBhai feature that plugs it | Status |
|---|---|---|---|---|
| 9:30 AM | Owner opens; doesn't know today's bookings; stylists ask "how many today?" | Unplanned staff (a stylist on leave on a busy day) means walk-aways | Daily 9:30 AM "today's list" on WhatsApp to owner + each stylist | GAP (only the Monday weekly summary exists, `adsbot.js` `weeklySummary`) |
| 10 AM–1 PM | Phone rings while the receptionist is threading; 30–40% of calls missed | ~3 missed bookings/day × ₹600 ≈ ₹54,000/month | Voice agent answers in Telugu/Hindi/English and books | PARTIAL (`voice/agent.py`; doesn't write `bookings`, F10) |
| 1–5 PM Mon–Thu | Empty chairs (weekday afternoon dip) | 4 chairs × 3 empty hours × 20 weekdays at ~₹400/hr ≈ ₹96,000/month of idle capacity | Opt-in "weekday afternoon offer" broadcast to lapsed/regular clients; Click-to-WhatsApp ad angle; offer FAQ | PARTIAL (offer FAQ and ad angle exist; broadcast is a GAP, F21) |
| Saturday 6–8 PM | Prime slots booked, 10–15% don't show | 300 bookings × 12% × ₹600 = ₹21,600/month | 24 h + 2 h reminders, one-tap confirm, auto-release of unconfirmed slots to a waitlist | PARTIAL (reminders exist; confirm reply broken F7; duplicate reminders F6; no waitlist) |
| 9 PM–midnight | 20–40% of WhatsApp enquiries arrive after closing (students, IT staff); nobody replies until noon, and they book elsewhere | 15 lost bookings × ₹600 ≈ ₹9,000/month | 24×7 bot booking + price list + offers | EXISTS (`engine.js`; WhatsApp webhook) — but late-evening "today" bugs (F8) |
| After a visit | Happy customers leave without a review; Google rating stuck at 4.1 with 60 reviews | Lower Maps ranking; fewer new walk-ins | After-visit review ask with Google link, sent only to **completed** visits | PARTIAL (`after_visit` template; goes to no-shows too, F13) |
| Week 6–10 after a visit | Customer quietly moves to a cheaper salon | Losing 30% of 400 active clients a year ≈ 120 × ₹600 × 6 visits ≈ ₹4.3 lakh/year | Lapsed-client win-back at 45/60 days, per-service rebook cadence (men's cut 4 wks, colour 6 wks, facial 4 wks) | GAP for salon (F20) |
| Festivals (Bathukamma/Dasara Oct, Karwa Chauth, Diwali, Sankranti Jan, Ugadi, Ramzan/Eid) | Demand spikes; phone jammed; walk-ins turned away; no pre-booking | Lost peak-day revenue; no deposit means peak-day no-shows | Festival template (opt-in), festival-specific slots and capacity, advance booking | PARTIAL (`salon-festival.png` card exists; no festival template in `templates.json`, no broadcast) |
| Nov–Feb wedding season | Bridal enquiries in DMs; artist double-booked; quotes lost in chats | One lost bride ≈ ₹25,000–₹80,000 | Bridal enquiry flow → hot lead → owner callback within 15 min; date hold | PARTIAL (FAQ + handoff exist; bridal can be booked as a 1-hour slot, F14) |
| Month end | Owner doesn't know CAC, repeat rate or no-show rate | Spends on ads blind | Dashboard + Excel + weekly WhatsApp summary + ads guard | PARTIAL (leads dashboard; no bookings or visit metrics) |

---

## 3. User stories with acceptance criteria

The Given/When/Then lines are testable. "Bot" means the WhatsApp engine and webhook unless marked Voice.

### Epic A — Booking & calendar

**A1. Book a service in under a minute** — **EXISTS** (`engine.js` `startFlow`/`handleStep`/`nextOrFinish`; `whatsapp.js` writes `bookings`)
- Given a new customer on WhatsApp, when they send "hi" → "1" → "4" → "tomorrow" → "3" → "Ravi Kumar", then the bot confirms "Hair spa, <tomorrow> at 4:00 PM" with the salon address, a `bookings` row is inserted with status `confirmed`, the lead becomes `hot`/`booked`, and the owner gets "🔔 New booking".
- Given the flow is mid-way, when the customer types "cancel", then the flow stops and the menu is shown.

**A2. Free-text service matching that understands how Hyderabad customers talk** — **PARTIAL** (`pickChoice` does fuzzy matching; fails cases F16 and Tenglish words)
- Given the service step, when the customer types "hair cut", "cutting", "baal katna", "gents cut" or "boys haircut", then "Haircut (men)" is selected for a male context or the bot asks "Men's or women's haircut?". It must never select Hair spa.
- Given "ladies cut" or "haircut for girl", then "Haircut & styling (women)" is selected.
- Given "shave", "gaddam" or "beard", then "Beard trim" is selected.
- Given an ambiguous "haircut", then the bot asks a 2-button question (Men ₹250 / Women ₹600) instead of guessing.

**A3. Intent + entities in one message** — **GAP**
- Given "hi i want haircut tomorrow 5pm" (or "repu evening facial kavali"), when received, then the bot pre-fills service, date and time window and asks only for what is missing. Today the greeting regex wins and the intent is dropped (verified).

**A4. Natural time input** — **GAP** (F9)
- Given the slot step, when the customer types "4", "4pm", "4 baje", "sayantram 4" or "evening", then the bot maps it to the 4:00 PM slot (or offers the evening slots). An option number is only used when the customer replies with a list/button id or a number ≤ the option count **and** that number doesn't match a slot hour.
- Given "7pm" and 7:00 PM is free, then 7:00 PM is booked.

**A5. Opening hours, weekly off and holidays** — **GAP**
- Given `config.weekly_off = ["tuesday"]`, when a customer picks "Tuesday" or a date that falls on a Tuesday, then the bot replies "We're closed on Tuesdays 🙏 Wednesday 11 AM is free — shall I book it?" and does not create a booking.
- Given `config.holidays = ["2026-11-08"]` (Diwali) with label, when that date is chosen, then the bot names the holiday and offers the nearest open day.
- Given `config.special_hours = {"2026-10-19": "08:00-22:00"}` (Saddula Bathukamma/Dasara rush), then that day's slots are generated from those hours.
- Given the hours string changes in config, then the "Timings" reply and slot generation stay consistent (one source of truth: structured hours, not a free-text string).

**A6. Service durations and slot generation** — **GAP** (F2)
- Given each catalog item has `duration_min` (men's cut 30, women's cut 45, hair spa 60, facial 60, keratin 150, bridal trial 120), when the customer picks a date, then slots are generated every 30 minutes within opening hours, and only start times where the full duration fits before closing and fits free chair-time are offered.
- Given a 150-minute keratin, when 4:00 PM is chosen, then the 4:00–6:30 PM chair time is blocked for that chair.
- Given more than 10 free slots, then the bot shows morning/afternoon/evening first (WhatsApp list max 10 rows), then specific times.

**A7. Multiple stylists / chairs** — **PARTIAL** (single salon-wide `capacity`, F3)
- Given `config.staff = [{name:"Raju", services:[...], days_off:["wednesday"]}, ...]`, when a customer books, then a booking is assigned to a free qualified stylist, and capacity = number of qualified stylists free for the full duration.
- Given a regular asks "Raju unnara Sunday?", when Raju is free, then the bot offers Raju's free slots. If he's off, it says so and offers another stylist. The voice rule "never promise a stylist by name unless config lists them" still applies.
- Given "any stylist", then the least-loaded stylist is assigned.

**A8. Staff breaks and leave** — **GAP**
- Given `staff[i].breaks = ["14:00-14:45"]` or a leave day entered by the owner ("Raju leave 20/10" sent from the owner's number), then those times are not offered for that stylist, and existing bookings on that day are listed to the owner for reassignment.

**A9. Walk-ins block chairs** — **GAP**
- Given the owner or receptionist sends "walkin facial 4pm" (or taps "Add walk-in" on the dashboard), then a `bookings` row with `source='walkin'` blocks that chair-time, and bot customers no longer see it.

**A10. Same-day late-evening booking** — **PARTIAL** (past-slot filter exists but is wrong in UTC, F8; message misleading)
- Given it is 8:45 PM IST and closing is 9:00 PM, when a customer asks for "today", then the bot says "We're closing for today 🌙 Tomorrow's first slot is 10:00 AM — book it?", **not** "fully booked".
- Given it is 6:00 PM IST on a UTC server, when "today" is chosen, then 1:00 PM and 4:00 PM are **not** offered.
- Given it is 00:30 IST, when "today" is chosen, then the date is the current IST date.

**A11. Booking for someone else / multiple bookings per phone** — **GAP** (F4)
- Given a customer says "for my friend Priya" (or "for my mom"), when asked for the name, then the name is stored as "Priya" (prefix stripped), `booked_by` stores the customer's contact, and reminders go to the customer's number with Priya's name.
- Given a contact already has an upcoming booking and books another, then both bookings exist, both get reminders, and "cancel"/"reschedule" asks "Which booking? 1) Hair spa Sat 4 PM (you) 2) Facial Sat 4 PM (Priya)".
- Given 2 people book together (mother + daughter), then 2 chairs at the same time are allocated, or the bot says only 1 is free.

**A12. Bridal and high-value services go to enquiry, not instant booking** — **PARTIAL** (FAQ + handoff exist; F14)
- Given a catalog item has `enquiry_only: true` (bridal, engagement, pre-bridal packages > ₹10,000), when it is chosen, then the bot collects event date, event type (haldi/mehendi/wedding/reception), number of people, location (salon/venue) and budget band, creates a `hot` lead with intent `bridal`, alerts the owner with a template message within 1 minute, and offers a trial slot instead of a wedding-day slot.
- Given the wedding date already has `config.bridal_capacity` brides held, then the bot says the artist is fully committed that day and offers the owner callback.

**A13. Price-safe answers** — **EXISTS** (`catalogReply`; `humanize.js` `translationIsSafe`)
- Given any language, when prices are shown, then every ₹ amount matches `config.catalog` exactly; if a translation changes a number, the English text is sent.

### Epic B — Reschedule / cancel

**B1. Reschedule an existing booking** — **EXISTS** (`engine.js` reschedule branch; `whatsapp.js` marks the old `bookings` row `rescheduled`)
- Given a booked customer, when they send "reschedule" / "change time" / "postpone", then the bot shows the current booking, asks only date and time, frees the old slot, and confirms with "🔁 Done, I've moved it". The owner gets "🔁 Rescheduled: … old → new".

**B2. Reschedule in Tenglish/Hinglish** — **GAP**
- Given "time marchandi", "vere roju ki marchali", "date change karna hai" or "kal ki jagah parso", then the reschedule flow starts.

**B3. Cancel with confirmation** — **EXISTS** (`state.pending = "cancel"`; yes/avunu/haan accepted; `bookings` row → `cancelled`)
- Given a booked customer, when they send "cancel", then the bot asks YES/keep. "avunu" or "haan" cancels and notifies the owner; anything else keeps the booking.

**B4. Late-cancel policy** — **GAP**
- Given `config.cancel_cutoff_hours = 2`, when a customer cancels less than 2 h before, then the bot still cancels, tags the booking `late_cancel`, and (if `config.deposit_required`) explains the deposit rule. It never charges automatically.

**B5. Reschedule/cancel works after a voice booking** — **GAP** (F10)
- Given a customer booked by phone, when they reply "reschedule" on WhatsApp, then the bot finds the voice booking.

### Epic C — Reminders & no-show

**C1. 24 h and 2 h reminders** — **EXISTS** (`automations.js` `dueReminders`; `reminders.js` hourly; templates `day_before`, `two_hours`)
- Given a booking tomorrow at 4 PM, when the hourly job runs between 20 h and 28 h before, then exactly one `bb_salon_reminder_day` is sent; between 1 h and 3 h before, exactly one `bb_salon_reminder_2h`.

**C2. Reminders are never duplicated** — **GAP / bug** (F6)
- Given a reminder was sent and the customer then replies anything, when the next hourly job runs, then no reminder is resent. Fix: keep reminder flags on the `bookings` row (new `reminders jsonb` column), or exclude `reminders` from the webhook's details upsert.

**C3. One-tap confirm / reschedule from the reminder** — **GAP / bug** (F7)
- Given the day-before reminder, when the customer taps "Confirm" or replies "1", "ok", "yes", "sare", "haan" or "confirmed", then the bot replies "Thanks Ravi! See you tomorrow at 4:00 PM 😊", sets `bookings.confirmed_at`, and does **not** start a new booking.
- When they tap "Reschedule" or reply "2", then the reschedule flow starts.

**C4. Unconfirmed booking handling** — **GAP**
- Given `config.release_unconfirmed = true` and no confirmation 3 h before the slot, then the owner gets "⚠️ Ravi hasn't confirmed 4 PM". The slot is never auto-cancelled without owner approval in the pilot.

**C5. Mark visit outcome (completed / no-show)** — **GAP** (F13)
- Given today's bookings, when the owner/receptionist replies to the 9 PM "close the day" WhatsApp list with "all done except 3" (or taps on the dashboard), then those bookings are set `completed` and number 3 is set `no_show`.
- Given no input by 11 PM, then bookings stay `confirmed` and **no** review ask goes out for that day (safe default).

**C6. No-show follow-up** — **GAP**
- Given a booking marked `no_show`, then 2 h later the customer gets a friendly "We missed you today 🙂 Want to rebook?" (utility/service message inside 24 h if they messaged, else template). After 2 no-shows, the contact is flagged and the owner can require a UPI deposit for future bookings.

**C7. Reminders respect opt-out and quiet hours** — **PARTIAL** (`leads.status = opted_out` excludes from reminder query since it is no longer `booked`)
- Given a contact who sent STOP, then no reminder, review or referral message is sent.
- Given any marketing message, then it is sent only between 9 AM and 9 PM IST. Utility reminders may go any time within their window.

### Epic D — Reviews & referrals

**D1. Review ask after a completed visit** — **PARTIAL** (`after_visit` template with `review_link`; sent 20–30 h after slot regardless of outcome, F13)
- Given a booking marked `completed`, when it is 2–4 h after the visit ends (same day, still fresh), then `bb_salon_review` is sent with the Google review link `config.review_link`.
- Given a booking that is `no_show`, `cancelled` or `rescheduled`, then no review ask is sent.
- The ask goes to **every** completed customer. No review gating: don't send only happy customers to Google; it breaks Google's review policy.

**D2. Private feedback captured too** — **GAP**
- Given the customer replies to the review message with a complaint ("colour patchy ga vachindi"), then the frustration handoff fires (`humanize.js` FRUSTRATION, extended with Telugu/Hindi words), the owner gets the full text, and the lead is tagged `complaint`.

**D3. Referral code** — **PARTIAL** (`referralCode`, REF detection, `refer` template 3 days later; F19)
- Given customer A received code REF-7KQ2, when friend B messages "Hi REF-7KQ2", then B's lead stores `referred_by = REF-7KQ2` and the owner is notified (EXISTS).
- Given B's first booking is marked `completed`, then A's ₹100 credit is recorded (new `referrals` table) and shown to the receptionist when A next books (GAP).
- `refer` is a MARKETING template: send only to contacts with marketing opt-in (GAP, see E1).

### Epic E — Offers / broadcasts (opt-in only)

**E1. Capture marketing opt-in** — **GAP** (F21)
- Given a booking confirmation, then the bot asks once: "Want birthday + festival offers on WhatsApp? (max 2/month) Yes / No". The answer is stored as `leads.marketing_opt_in` (bool) with `opt_in_at` and `opt_in_source`.
- Meta lead-form leads keep `consent: meta_lead_form` (EXISTS in `metaleads.js`) but are still asked explicitly before the first broadcast.

**E2. Owner-triggered broadcast** — **GAP**
- Given the owner sends "offer: Diwali glow facial ₹799 till 8 Nov" from their number (or uses the dashboard), when they confirm the preview and the count ("Send to 214 opted-in clients? ~₹184 Meta fees"), then the approved marketing template is sent only to `marketing_opt_in = true` and not-opted-out contacts, between 10 AM and 8 PM IST, throttled, with a STOP footer.
- Given a contact got a marketing message in the last 7 days, then they are skipped (frequency cap ≤ 2/month by default).

**E3. Festival calendar presets** — **GAP**
- Given the setup ships with a Telangana festival calendar (Bathukamma/Dasara, Karwa Chauth, Diwali, Christmas/New Year party season, Sankranti, Valentine's Day, Ugadi, Ramzan/Eid, Teej/Varalakshmi Vratham, plus wedding season Nov–Feb), then 10 days before each one the owner gets a suggestion: "Diwali in 10 days. Send 'Diwali glow' offer to 214 clients? Reply YES". Nothing is sent without that reply. Exact dates must be checked against the Telangana government holiday list each year.

**E4. Weekday-afternoon filler** — **GAP**
- Given tomorrow's 1–5 PM utilisation < 40% at 6 PM today, then the owner is asked whether to send the "weekday afternoon 20% off" offer to opted-in clients who are due for a visit.

**E5. Lapsed-client win-back** — **GAP for salon** (F20)
- Given a completed visit more than `config.winback_days` ago (default 45; per-service cadence when set) and no upcoming booking, then one `bb_salon_winback` (15% off) is sent if opted in, never more than once per 90 days.

**E6. Birthday offer** — **GAP** (Could)
- Given a stored birthday (asked optionally after the 2nd visit), then an opt-in birthday offer goes out 3 days before.

### Epic F — Voice calls

**F1. Answer inbound calls in Telugu/Hindi/English and book** — **PARTIAL** (`voice/agent.py` `run_call`, Sarvam codemix STT, `book()` tool; F10)
- Given a caller says "repu sayantram 5 ki haircut kavali", then the agent books the same fields, sends a WhatsApp confirmation, and alerts the owner (EXISTS).
- It must check and write the same `bookings` calendar (capacity, closed days, durations) as WhatsApp, and refuse full slots (GAP).

**F2. Callback request and bridal hand-off** — **EXISTS** (`request_callback` tool) / PARTIAL for bridal
- Given a caller asks for bridal or something the agent cannot answer, then `request_callback` stores the reason and the owner gets a WhatsApp alert.

**F3. Disclosure and recording consent** — **PARTIAL** (validator rule documented in README; implementation in `voice/prompt.py` not verified here)
- Given any call, then the opening states that it is the salon's AI assistant and that the call may be recorded. If the caller asks for a person, the agent transfers to `config.phone` or takes a callback.

**F4. Outbound calls only to consented leads, 9 AM–9 PM** — **EXISTS** (`outbound_worker` hour check; `metaleads.js` queues only when `voice_followup`)

**F5. Missed-call → WhatsApp** — **GAP** (Should)
- Given a call that drops or isn't answered (outside hours or line busy), then within 1 minute the caller gets the `lead_welcome` template with Book now.

### Epic G — Owner dashboard & Excel

**G1. Leads list with score and status, Excel/CSV export** — **EXISTS** (`functions/leads.js`; `web/index.src.html` `#x-xlsx`, `#x-csv`)

**G2. Bookings calendar view (today / week, by stylist)** — **GAP**
- Given the dashboard token, then the owner sees today's bookings grouped by stylist and time, with status chips (confirmed / reminder confirmed / completed / no-show / cancelled), and can mark outcomes and add walk-ins.

**G3. Bookings Excel export** — **GAP**
- Given a date range, then Excel export contains date, time, customer, phone (masked except last 4 unless owner), service, price, stylist, source (whatsapp/voice/web/walkin), status, and referral code.

**G4. Daily WhatsApp digest** — **GAP** (weekly exists: `adsbot.js` `weeklySummary`, Mondays)
- Given 9:30 AM IST, then the owner and each stylist get today's list. At 9 PM the owner gets "Today: 23 booked, 19 done, 2 no-show, 2 cancelled, 4 new reviews requested, est. revenue ₹13,800". Sent through the `owner_report` UTILITY template when outside the 24 h window.

**G5. Owner alerts always delivered** — **GAP / bug** (F11)
- Given the owner hasn't messaged the business number in 24 h, when a new booking, handoff or complaint happens, then the alert goes through an approved utility template (e.g. `bb_owner_alert` with one text parameter), not free-form text.

**G6. Staff inbox / human takeover** — **GAP** (F12)
- Given a customer asked for a human or was flagged as frustrated, then the bot pauses auto-replies for that contact for `config.handoff_minutes` (default 120) or until staff press "Resume bot". Staff can reply from the dashboard inbox (or the WhatsApp Business app, if the number is onboarded with Cloud API coexistence), and those replies are logged in `messages`.

**G7. Data isolation** — **EXISTS** (`leads.js` token → single client; RLS on all tables)

### Epic H — Onboarding

**H1. Client row + config** — **PARTIAL** (`schema.sql` example insert; manual SQL)
- Given a signed salon, then Onboarding Ops fills a form/CSV (business, address, structured hours, weekly off, holidays, catalog with prices + durations, staff, capacity, review link, owner WhatsApp) and a script validates it: every price has ₹, every duration is a multiple of 15, the review link starts `https://g.page/` or `https://search.google.com/local/writereview`, and the owner number is in `91XXXXXXXXXX` format.

**H2. Templates submitted and approved** — **EXISTS** (`tools/create-templates.js salon <WABA_ID>`) / PARTIAL: add `bb_owner_alert`, festival/offer, no-show and opt-in-friendly variants, and Telugu/Hindi template languages (`te`, `hi`).

**H3. Import existing client list** — **GAP**
- Given the salon's Excel/contact export (name, phone, last visit, last service), then contacts are imported as leads with `marketing_opt_in = false`, and they are used only for win-back after the salon confirms it has their consent.

**H4. Go-live test** — **PARTIAL** (README step 6: "Run 10 test conversations")
- Given the 25 conversations in section 5, then all Must ones pass on the client's config before go-live.

**H5. Staff training (15 min)** — **GAP** (doc)
- A one-page Telugu/English card for the receptionist: how to mark done/no-show, add a walk-in, take over a chat, and resume the bot.

### Epic I — Billing (BotBhai → salon)

**I1. Setup fee invoice** — **GAP**
- Given a signed salon, then a GST-compliant invoice for ₹9,999 (50% advance, 50% on go-live) with a UPI QR / payment link is generated, and payment status is stored (new `subscriptions`/`invoices` tables).

**I2. Monthly subscription** — **GAP**
- Given go-live date D, then ₹2,999 (+ ₹2,000 if ads management) is billed monthly via a Razorpay/Cashfree subscription with UPI AutoPay mandate, or a manual UPI link for the pilot. The reminder goes to the owner 3 days before the due date.

**I3. Dunning and suspension** — **GAP**
- Given an invoice unpaid 7 days after due date, then the owner gets 2 reminders. After 15 days the client is set `active = false` only after Kalpa Labs approves. Customers then get a polite "please call the salon" reply, never silence.

**I4. Meta costs stay on the salon's account** — **EXISTS** (by design: README; client adds their own payment method in WhatsApp Manager). The monthly report shows estimated template spend (marketing ≈ ₹0.86, utility ≈ ₹0.115 + GST per message as listed in the salon README) so there are no surprises.

---

## 4. Prioritised GAP list (MoSCoW) — what must exist before the first paid salon goes live

Effort: **S** ≤ 1 dev-day, **M** 2–4 days, **L** 5+ days.

### MUST (blockers for a paid pilot; ~12–16 dev-days total)
| # | Gap | Why it blocks | Effort | Touches |
|---|---|---|---|---|
| M1 | Reminder reply handling: "Confirm"/"1"/"yes"/"sare"/"haan" confirm; "Reschedule"/"2" reschedule (F7, C3) | Today a customer confirming from the reminder starts a **new booking** or sees the price list. Core no-show feature looks broken. | S | `engine.js` (state `awaiting_confirm` set by reminders), `reminders.js` |
| M2 | Reminder flags are wiped, so reminders are resent (F6, C2) | Duplicate reminders cost money and annoy customers. | S | `whatsapp.js` upsert (preserve `reminders`) or move flags to `bookings` |
| M3 | IST timezone: pass `meta.now`, compute date and slot cut-offs in IST (F8, A10) | Past slots bookable after 5:30 PM IST; wrong "today" after midnight. | S | `engine.js` `freeSlots`/`parseDate`, `whatsapp.js` |
| M4 | Weekly off, holidays, special hours; "closing for today" message (A5, A10) | Bookings on closed Tuesdays or Diwali mean angry customers at a locked shutter. | M | config schema + `engine.js` |
| M5 | Time input: "4"/"4pm"/"evening"/"sayantram" (F9, A4) | "4" books 7 PM today, so customers arrive at the wrong time. | S | `engine.js` `pickChoice` for slot step |
| M6 | Service matching: "hair cut", "cutting", "ladies cut", ask men/women when ambiguous (F16, A2) | Wrong service → wrong chair-time and price shown. | S | `engine.js` + catalog `aliases` |
| M7 | Owner alerts via utility template outside 24 h (F11, G5) | Owner silently stops getting booking/complaint alerts after day 1. | S | `whatsapp.js`, new template `bb_owner_alert` |
| M8 | Bridal = enquiry flow, not a 1-hour slot (F14, A12) | Highest-value lead mishandled; artist double-booked on muhurtham dates. | S | catalog `enquiry_only`, `engine.js` |
| M9 | Human takeover pause + a way for staff to reply (F12, G6) | Bot talking over the receptionist with a bride or angry customer. | M | session `paused_until`; dashboard inbox or Cloud API coexistence |
| M10 | Mark visit outcome (done/no-show) via owner WhatsApp list + dashboard; review ask only for completed visits (F13, C5, D1) | Review ask to no-shows is embarrassing; no-show KPI cannot be measured without it. | M | `bookings.status`, `reminders.js`, owner command parser |
| M11 | Voice bookings write `bookings` with capacity check (F10, F1) | Phone and WhatsApp double-book the same chair. | M | `voice/agent.py` `book()` + availability tool |
| M12 | Tenglish/Hinglish intent keywords + Telugu-script greeting (F15) | The pitch is "speaks your customers' language", but "repu haircut kavali" fails today. | S | `engine.js` intent regexes, `GREET` without `\b` for non-Latin |
| M13 | Marketing opt-in flag; gate `refer`, `winback` and any offer on it (E1) | WhatsApp Business Policy + DPDP Act 2023; risk of number quality drop/ban. | S | `leads.marketing_opt_in`, `reminders.js` |
| M14 | "home visit" → home-service FAQ, not booking (F17) | Small but visible wrong answer in demos. | S | `engine.js` intent order |

### SHOULD (within the first 30 days of the pilot)
| # | Gap | Effort |
|---|---|---|
| S1 | Service durations + 30-min slot generation within hours (A6) | M |
| S2 | Multiple bookings per phone; "for my friend/mom" name handling (A11, F4) | M |
| S3 | Bookings calendar view + bookings Excel export (G2, G3) | M |
| S4 | Daily 9:30 AM list + 9 PM day-close digest on WhatsApp (G4) | S |
| S5 | Walk-in entry by owner WhatsApp command / dashboard (A9) | S |
| S6 | Salon win-back from last completed visit (E5) | S |
| S7 | Owner-approved broadcast to opted-in contacts with cost preview + frequency cap (E2) | M |
| S8 | Manual billing: invoice PDF + UPI link + paid flag (I1, I2 manual) | S |
| S9 | Intent + entities in the first message (A3) | M |
| S10 | Missed-call → WhatsApp (F5) | S |
| S11 | No-show follow-up + repeat no-show flag (C6) | S |
| S12 | Telugu (`te`) and Hindi (`hi`) versions of the reminder templates | S |

### COULD
| # | Gap | Effort |
|---|---|---|
| C1 | Multiple stylists with skills/days off/breaks; "Raju unnara?" (A7, A8) | L |
| C2 | Festival calendar suggestions (E3) and weekday-afternoon filler (E4) | M |
| C3 | Referral reward ledger (D3) | S |
| C4 | Razorpay/Cashfree UPI AutoPay subscriptions + dunning (I2, I3) | M |
| C5 | Deposit for bridal / repeat no-shows via UPI payment link | M |
| C6 | Birthday offers (E6) | S |
| C7 | Client list import with consent tagging (H3) | S |

### WON'T (this pilot)
- Inventory/product retail tracking, staff payroll/commission, POS billing for the salon's own customers, multi-branch chains, loyalty points wallet, an Instagram DM bot.

---

## 5. Test conversations for QA automation (25)

**Harness.** Engine-level tests use the `talk()` pattern in `core/engine.test.js` (`B.createBot("salon", overrides)`, `bot.handle(state, text, { now, contact, profileName, busy, known })`). **Run every suite with `TZ=UTC`** to match Netlify. Webhook-level tests (reminders, owner alerts, bookings rows, handoff pause) use `core/functions/_fake.js`. Fix `_fake.js` so an upsert **replaces** jsonb columns the way PostgREST does, otherwise T07 can't fail.

Default fixture: config = `bot.config.js` plus `{ weekly_off:["tuesday"], holidays:[{date:"2026-11-08",label:"Diwali"}], capacity:2, review_link:"https://g.page/r/test" }`. `now` = Mon 12 Oct 2026 11:00 IST unless stated. Contact `919876543210`.
"Today" column: result of running the current code (✗ = fails today, ✓ = passes, ~ = partly).

| ID | Scenario | Customer messages (in order) | Expected bot behaviour | Today |
|---|---|---|---|---|
| T01 | Happy path, numbers only | `hi` → `1` → `4` → `tomorrow` → `3` → `ravi kumar` | Confirms "Hair spa · Tue, 13 Oct at 4:00 PM" + address; 1 `bookings` row confirmed; owner alert; lead hot/booked. **With weekly_off=tuesday: says closed Tuesday, offers Wed** | ~ (books Tuesday) |
| T02 | Tenglish full booking | `hi` → `repu evening haircut kavali` → `ravi` | Pre-fills date=tomorrow, service=men's haircut (or asks men/women), offers only 4 PM/7 PM; reply translated to Tenglish with ₹ and times unchanged | ✗ (unanswered) |
| T03 | Hinglish price question | `bhai facial kitna hai?` | Shows facial price ₹999 (or full list) in Hinglish; no "didn't get that" | ✗ |
| T04 | Typo-heavy | `hii` → `boook` → `hair cut` → `tmrw` → `4pm` → `Keerthana` | "boook" → booking flow; "hair cut" → asks Men/Women (never Hair spa); "4pm" → 4:00 PM | ✗ ("boook" unanswered, "hair cut" → Hair spa, "4pm" rejected) |
| T05 | Bare number as a time | `book` → `facial` → `saturday` → `4` | Books **4:00 PM** (or asks "4 PM?"), not 7:00 PM | ✗ (books 7 PM) |
| T06 | Reminder confirm button | Booking exists for tomorrow 4 PM; day-before reminder sent; customer taps `Confirm` (then separately `1`, `sare`) | "Thanks! See you tomorrow at 4:00 PM"; `confirmed_at` set; no new booking flow, no menu | ✗ ("Confirm" → menu; "1" → new booking) |
| T07 | No duplicate reminder | Day-before reminder sent at 14:00 IST; customer replies `ok thanks` at 14:10; reminders job runs at 15:00 | No second day-before reminder | ✗ (real PostgREST wipes the flag) |
| T08 | Reschedule from reminder | Reminder sent; customer taps `Reschedule` → `friday` → `1:00 PM` | Old slot → `rescheduled`, new slot booked, owner "🔁 Rescheduled" | ✓ |
| T09 | Reschedule in Telugu-English | Booked; `time marchali, ellundi ki` | Starts reschedule, takes date = day after tomorrow, asks time | ✗ |
| T10 | Cancel with Telugu yes | Booked; `cancel` → `avunu` | Cancelled; owner "❌ Cancelled"; bookings row cancelled | ✓ |
| T11 | Late-evening same day | now = 20:45 IST; `book` → `1` → `today` | "We're closing soon for today 🌙 Tomorrow 10/11 AM?"; never "fully booked"; no past slots | ✗ ("fully booked" message) |
| T12 | Evening UTC past-slot | now = 18:00 IST, TZ=UTC; `book` → `facial` → `today` | Offers only 7:00 PM | ✗ (offers 1 PM, 4 PM) |
| T13 | Closed-day request | `book` → `1` → `tuesday` | "We're closed on Tuesdays"; offers Wednesday slots; no booking on Tuesday | ✗ |
| T14 | Holiday (Diwali) | `book` → `5` → `8/11` | "Closed for Diwali 🪔"; offers 7 or 9 Nov | ✗ |
| T15 | Bridal enquiry | `Hi, bridal makeup for wedding on 22 Jan, haldi on 20th also. Price?` → `around 50k budget` → `Sravani` | Bridal package info "from ₹15,000"; collects event dates, event types and budget; does **not** confirm a 1-hour slot; owner gets a hot-lead template alert within 1 min; offers a trial slot | ~ (FAQ answers; but `book`→`6` books a 1-hour slot) |
| T16 | Price haggling | `facial 999 too much, 600 ki chestara?` → `last price entha` | Polite: prices are fixed; mentions the current offer (20% off facials Mon–Thu → ₹799) from config only; never invents a discount; offers booking | ✗ ("didn't get that") |
| T17 | Angry customer | `worst service, waiting since 30 min, no one picking phone` | Apology first ("I'm really sorry…"); owner alert with the text; lead tagged complaint; bot **pauses** for this contact; no "didn't get that" menu appended | ~ (apology + handoff, but menu appended, no pause) |
| T18 | Angry in Telugu/Hindi | `chala chetha service, refund kavali` / `bakwas service yaar` | Same as T17 | ~ (only "chetha"/"bakwas"/"refund" words trigger) |
| T19 | Booking for a friend | `book` → `2` → `saturday` → `11:00 AM` → `for my friend Priya` | Name stored as "Priya"; `booked_by` = sender; confirmation says Priya | ✗ (name "For My Friend Priya") |
| T20 | Two bookings, one phone | T19 done, then `book` → `5` → `saturday` → `11:00 AM` → `Aisha`; then `cancel` | Two bookings exist; cancel asks "Which booking?" | ✗ (second overwrites session; cancel hits the latest only) |
| T21 | Capacity full | capacity 2; two confirmed bookings Sat 11 AM; `book` → `1` → `saturday` | 11:00 AM not offered; if the whole day is full, asks another day | ✓ |
| T22 | Home service | `home visit possible?` | Home service FAQ (within 5 km, bookings above ₹1,500) | ✗ (starts booking) |
| T23 | Telugu script greeting | `హాయ్` then `నమస్కారం` | Greeting + menu, replies in Telugu script | ✗ (unanswered) |
| T24 | Opt-out and back | `STOP` → `hi` → `START` | Unsubscribed message; silence to "hi"; welcome back on START; no reminders/offers while opted out | ✓ (engine); check reminders skip |
| T25 | Referral + human hand-off | `Hi REF-7KQ2 my friend said you are good` → `talk to owner` | Lead `referred_by=REF-7KQ2`; owner "🤝 Referral"; hand-off message with hours and phone; bot paused for this contact | ~ (no pause) |

Extra assertions for every test:
- Every reply ≤ 1,024 characters when sent with buttons/lists, and ≤ 10 list options.
- No ₹ amount appears that is not in `config.catalog` or `config.faqs`.
- Translated replies keep every number, time and URL identical to the English source (`translationIsSafe`).
- `messages` gets 1 `in` row + N `out` rows per turn (webhook tests).
- No marketing template goes to a contact with `marketing_opt_in != true` or status `opted_out`.

---

## 6. Pilot success metrics and how to measure them

Pilot = 1–3 salons, 60 days, baseline from the owner's register/notebook for the 4 weeks before go-live.
Several metrics need small schema additions (marked ★). Add them before go-live, or the metric can't be computed.

Schema additions needed:
- ★ `bookings`: `source text` (whatsapp/voice/web/walkin), `price numeric`, `stylist text`, `confirmed_at timestamptz`, `reminders jsonb`, `booked_by text`, `updated_at timestamptz`.
- ★ `leads`: `marketing_opt_in boolean`, `opt_in_at timestamptz`.
- ★ `messages`: an index already exists on `(client_id, contact, created_at)`; reuse it.
- ★ `bookings.status` must actually be set to `completed`/`no_show` (M10).

| # | Metric | Target (from README) | SQL sketch (Supabase, `:cid` = client id) |
|---|---|---|---|
| 1 | Chat → booking conversion | ≥ 25% | `select count(*) filter (where status in ('booked','cancelled') or details ? 'date_iso')::float / count(*) from leads where client_id=:cid and source in ('whatsapp','meta_ads','web') and created_at >= :start;` Better (★): distinct contacts with a `bookings` row ÷ distinct contacts with an inbound `messages` row in the period. |
| 2 | No-show rate | ≤ 5% (baseline 10–15%) | `select count(*) filter (where status='no_show')::float / nullif(count(*) filter (where status in ('completed','no_show')),0) from bookings where client_id=:cid and date_iso between :start and :end;` |
| 3 | Reminder confirmation rate ★ | ≥ 70% | `select count(confirmed_at)::float / count(*) from bookings where client_id=:cid and reminders ? 'day_before';` |
| 4 | After-hours capture | report | `select count(*) from bookings b where client_id=:cid and (extract(hour from b.created_at at time zone 'Asia/Kolkata') >= 21 or extract(hour from b.created_at at time zone 'Asia/Kolkata') < 10);` → × avg ticket = "₹ booked while you were closed" (headline number for the owner) |
| 5 | Bot response time | p95 < 10 s | Pair each `messages` `in` row with the next `out` row for the same contact: `select percentile_cont(0.95) within group (order by extract(epoch from o.created_at - i.created_at)) from messages i join lateral (select created_at from messages o where o.client_id=i.client_id and o.contact=i.contact and o.direction='out' and o.created_at>=i.created_at order by created_at limit 1) o on true where i.client_id=:cid and i.direction='in';` |
| 6 | Unanswered rate (bot fallback) | < 10% of inbound | Count `out` messages starting with the fallback variants ("Sorry, I didn't quite get that", "Hmm, I didn't catch", "Oops, that one", "Sorry, I'm still learning") ÷ `in` messages. Better: persist the engine's `unanswered` events into `jobs` or a new `events` table. |
| 7 | Google reviews added | +20/month | Not in the DB; record the review count weekly from Google Business Profile (manual or GBP API) into `clients.config.review_counts`. Proxy: `count(*) from leads where details->'reminders' ? 'after_visit'` = asks sent. |
| 8 | Repeat visit within 45 days | ≥ 40% | `with v as (select contact, date_iso from bookings where client_id=:cid and status='completed') select count(distinct a.contact)::float / (select count(distinct contact) from v where date_iso <= current_date - 45) from v a join v b on a.contact=b.contact and b.date_iso > a.date_iso and b.date_iso <= a.date_iso + 45 where a.date_iso <= current_date - 45;` |
| 9 | Weekday-afternoon utilisation ★ | +15 pts vs baseline | Bookings with `extract(dow from date_iso) between 1 and 4` and slot between 1–5 PM, ÷ (chairs × slots available). Needs `capacity` and the generated-slot count per day. |
| 10 | Voice share and voice booking success | report | `select source, count(*) from leads where client_id=:cid group by source;` and `count(*) filter (where status='booked')` among `source='voice'`. |
| 11 | Handoff volume and owner response ★ | handoffs answered < 15 min in hours | `leads.status='callback'` count; response time = first staff `out` message after the handoff (needs staff replies logged in `messages` with `author='staff'`). |
| 12 | Opt-out rate | < 2% of messaged contacts/month | `select count(*) filter (where status='opted_out')::float / count(*) from leads where client_id=:cid;` |
| 13 | Revenue recovered (ROI for renewal pitch) | ≥ 5× the ₹2,999 fee | (Bot/voice bookings `completed` × `price` ★) + (baseline no-show rate − current) × bookings × avg ticket. Reported monthly on WhatsApp and in Excel. |
| 14 | Ads cost per lead | ≤ ₹120 | `select sum(spend)/nullif(sum(leads),0) from ad_stats where client_id=:cid and day >= :start;` (EXISTS: `ad_stats` from `adsbot.js`) |
| 15 | Message cost to salon | report | Count template sends by category (needs a `template` field in `messages` ★) × Meta rates in the salon README. |

**Pilot exit criteria (go/no-go to sell salon #2–#10):** M1–M14 shipped; T01–T25 at least 22 passing; 60-day no-show ≤ 7% (stretch 5%); conversion ≥ 25%; owner says they would pay ₹2,999 again (ask on day 45); zero WhatsApp quality-rating drops.

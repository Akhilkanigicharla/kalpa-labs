# Kalpa Labs soft launch · Sunday 13 December 2026

Decided by Akhil on 18 Oct 2026 (C13). Goal: **real customers, real rupees, real feedback**, with every live thing production-grade. Building is no longer the goal by itself.

## The two dates

| Date | What happens | Why this date |
|---|---|---|
| **Mon 16 Nov 2026 · Pilot Day** (29 days away) | First real salon on BotBhai (free pilot); Telugu deals channel posting daily; UPI payments switched on | Sravana nakshatra all day IST (Akhil's janma nakshatra). Checked on drikpanchang.com and prokerala.com: 15 Nov 23:28 → 17 Nov 02:16 IST |
| **Sun 13 Dec 2026 · Soft launch** (56 days away) | Public: BotBhai salon plans + Social Team add-on, Kits + Claude Skill pack, deals channel, workshop sign-ups | Sravana nakshatra from 06:12 IST (13 Dec 06:12 → 14 Dec 09:12, same two sources). 8 weeks fits Akhil's 1 hour a day for the CEO steps below |

Numerology, for the record: 13-12-2026 adds up to 8 and 16-11-2026 to 1; the 6-days near them (6 Dec, 15 Nov) miss Sravana. Readiness and Sravana won the tie. Astrology is Akhil's choice of timing, not a business forecast.

## What "launched" means (all five must be true on 13 Dec)

| # | Offer | Live means | Money | Owner |
|---|---|---|---|---|
| 1 | **BotBhai for salons** (b1) | WhatsApp number live, 1–3 salons using it, dashboard + inbox working, privacy notice + agreement signed | Founding plan per `01-botbhai/PLAN.md` §2 (₹2,999 setup, ₹1,499/month for months 1–3); first salons free for 14 days | Chitti, Scout, Vani + build sprint |
| 2 | **Social Team add-on** (b1, C18 approved) | Month plan + posts approved by the salon on WhatsApp, published through the official API | ₹999–1,499/month as suggested; launch offer ₹999 for founding salons | Adi, Lens, Reel, Kavi |
| 3 | **Telugu deals channel** (b5, C32: build this first, no swap) | 3–5 checked deals a day, Telugu copy, ASCI `#ad`, link tracking, weekly money tip | EarnKaro/Cuelinks commission first; Amazon Associates only at ~300 members (PLAN §4 rule) | Deal, Kavi + poster bot |
| 4 | **Kits + Claude Skill pack** (b3, C30/A54) | GATE kit, Tax+SIP planner, GATE Study Coach skill pack on a sales page | ₹199–499 via business UPI QR, manual delivery until Razorpay | Kavi, Echo |
| 5 | **Telugu "Claude Code with me" workshop** (C31 yes) | Sign-up page + outline; one live session on Google Meet; recording sold after | Price: Akhil picks (C38) | Kavi, Adi |

Plus, for all five: **feedback in, fixes out** (below), uptime checks, and a clean audit.

## Production-grade bar (checked by the Fact-check desk before 13 Dec)

1. `Kalpa quality` CI green on main, and every launch world's tests green.
2. Deployed URLs pass a scheduled smoke test (page loads, chat answers, booking saves, payment page shows the right UPI ID).
3. No unverified claim on any public page (audit desk: price, law, "free", income).
4. Privacy notice names every processor (Groq, NVIDIA, TypeSafe, Meta, Supabase, Netlify); WhatsApp opt-in templates approved; ASCI `#ad` on every affiliate post.
5. Money is reconciled weekly in the Kalpa Ledger sheet (C06).
6. A rollback path for each deploy (Netlify previous deploy, git revert).

## Feedback loop (real people, ground truth)

- **In:** WhatsApp replies from pilot salons, a Telegram poll + comments on the deals channel, a 3-question Google Form linked from every product page, YouTube comments through the official API on our own videos.
- **Not allowed:** scraping Instagram, Google Maps, Justdial or anyone's personal numbers (CLAUDE.md rule 4). Instagram insights only from our own account.
- **Process:** n8n "Feedback desk" puts every item in one data table; Echo (free open model) groups it weekly; the build sprint turns the top 3 into roadmap fixes; Akhil sees them in the CEO Room.

## Weekly plan (agents build, Akhil does ≤ 1 hour a day)

| Week (Mon) | Akhil (CEO quests) | Agents (build sprint + n8n) |
|---|---|---|
| 19 Oct | C01 approve plan · C08 business UPI QR · C09 Telegram channel · C38 workshop price | A55 green CI · A58 deals channel production · A54 skill pack |
| 26 Oct | C27 deals bot token · EarnKaro sign-up (C39) · C06 Kalpa Ledger | A60 feedback desk · A61 smoke tests · A62 workshop page |
| 2 Nov | C02 Meta app + WhatsApp test number · C03 deploy BotBhai · C14 prepaid SIM (≈₹250, now unlocked) | A59 salon pilot kit · A57 launch readiness board |
| 9 Nov | C04 demo to a salon owner · C05 pick 15 salons · C28 Turnstile | A63 launch countdown + quests · A64 launch content calendar |
| **16 Nov · Pilot Day** | First salon starts free pilot; deals channel live; UPI on | Daily feedback triage; fix within 24 h |
| 23 Nov – 6 Dec | 2 salon visits a week · workshop sign-ups · Telugu reader (C17) | Fixes from feedback; audit of every public claim; payment reconciliation |
| **13 Dec · Soft launch** | Announce on channel + WhatsApp status; open sign-ups | On-call: smoke tests every 5 h with the build sprint |

## Game layer (until real money arrives)

The Kingdom keeps running: every launch step is a quest, Pilot Day is the **Boss of the Silver Gate**, 13 Dec is the **Launch Boss**. The CEO Room shows the countdown. The game ends when the first ₹ lands; after that the scoreboard is revenue.

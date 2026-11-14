# BotBhai depth map (A87), 14 Nov 2026

Every feature promised in `01-botbhai/PLAN.md` (price ladder, P1 quests) and `botbhai/README.md`, with evidence.
A87 is ticked only when every row below is **built**. Each partial / missing row has its own roadmap item.
Test suite: `bash 01-botbhai/botbhai/tools/test-all.sh` (all green on 14 Nov 2026, incl. the Postgres schema test).

## Conversation (all tiers)
| Feature | Status | Evidence |
|---|---|---|
| WhatsApp bot: prices, FAQ, booking, reschedule, cancel | built | `core/engine.js`, `core/functions/whatsapp.js`; `core/engine.test.js`, `core/regression.test.js` |
| 4 setups: salon, gym, real estate, coaching (exam kits) | built | `setups/*/bot.config.js`; every setup in `qa/depth.test.js` (8 multi-turn bookings) |
| 5 languages: English, Telugu, Hindi, Tenglish, Hinglish | built | `core/lang.test.js`, `core/functions/chat-lang.test.js`, 224-message corpus `qa/depth.cases.txt` |
| AI fallback for messages the rules don't understand, in WhatsApp **and** web chat | built (A87) | `core/aiask.js` wired in `whatsapp.js` + `chat.js`; `core/functions/aifallback.test.js` |
| AI off switch: whole platform (`BOTBHAI_AI_FALLBACK=off`) and per client (`config.ai_fallback=false`) | built (A87) | `core/aiask.js`; checked on all 224 messages and through both handlers |
| AI can never invent a price, phone number or time | built | `core/fallback.js` guard; `qa/depth.test.js` runs 5 broken/attacked model answers per message |
| Owner sees every AI answer in the inbox (marked "AI (check)") | built (A87) | `messages.author = 'ai'` (`supabase/schema.sql`, `supabase/test.sql`), `web/inbox.js` |
| Website chats logged for the owner's inbox | built (A87) | `core/functions/chat.js`; `aifallback.test.js` |
| 200+ real-style test messages incl. Telugu/Hindi script + multi-turn | built (A87) | 224 messages, 5,078 checks; report `botbhai/qa/depth-report.md` |
| AI accuracy measured with the **real** free model on the 224 messages | missing | A283 (needs a Groq key as a GitHub secret, or n8n back) |
| Rules answer the right thing (5 of 154 rules answers still off-topic) | partial | listed in `qa/depth-report.md`; A284 |
| Bridal enquiry flow (salon) | built | `core/bridal.test.js` |
| Human hand-off on complaints, owner alert | built | `core/humanize.js` FRUSTRATION (widened in A87), `webhook.test.js` |
| WhatsApp Flows booking form (P1-M2-01) | missing | no `core/functions/flow.js`; A285 |

## Operations
| Feature | Status | Evidence |
|---|---|---|
| 24 h + 2 h reminders, after-visit, renewals, win-backs, review asks | built | `core/functions/reminders.js`, `core/automations.test.js`, `core/nudges.test.js` |
| Owner alerts, 9:30 AM daily list, close-the-day (P1-M2-04) | built | `core/functions/dayclose.js`, `agents.test.js` |
| Slot engine phase 1 + 2 (hours, holidays, durations, stylist capacity) | built | `core/slots.js`, `slots.test.js`, `slots.fuzz.test.js` |
| Shared inbox phase 1 + assignment and notes | built | `web/inbox.html`, `core/functions/inbox.js` |
| Inbox phase 2 rest: phone PWA install, unread badge (P1-M2-05) | missing | no manifest / unread count; A286 |
| Owner dashboard + Excel/CSV export | built | `web/dashboard.html`, `web/dashboard.js` |
| Manual billing: invoice + UPI QR + paid flag | built | `core/billing.js`, `billing.test.js`, Postgres invoice test |
| Message cost meter in the owner report (P1-M2-03) | missing | no per-template cost tracking; A287 |
| Monthly ROI report (Standard tier) | missing | only mentioned on the landing page; A287 |
| Nightly encrypted Supabase backup + restore drill (P1-M2-07) | missing | no workflow in `.github/workflows`; A288 |

## Growth add-ons
| Feature | Status | Evidence |
|---|---|---|
| Meta lead forms → WhatsApp in < 60 s | built | `core/functions/metaleads.js`, `hardening.test.js` |
| Comment-to-DM (dry run by default) | built | `core/comments.js`, `comments.test.js` |
| Meta ads bot (Pro) | built | `core/functions/adsbot.js`, `agents.test.js` |
| SEO mini-site per client | built | `seo/seo_bot.py`, 20 SEO checks per setup in `test-all.sh` |
| Voice: web (Standard), phone receptionist (Pro) | built in code, phone unproven | `voice/agent.py`, `voice/test_turns.py`; phone needs a client-paid number (P1-M3-07) |
| Starter tier: chat link + QR poster + quick replies | partial | QR in `core/billing.js`, counter poster not built; A286 |
| BotBhai's own lead finder | built | `leadfinder/`, `leadfinder.yml` |

**Status: 5 rows missing, 2 partial → A87 stays `[~]` until A283–A288 are done.**

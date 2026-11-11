# BotBhai industry maps (salon · gym · real estate)

Idea from a reel Akhil shared on 11 Nov 2026 (Instagram @skilltreeos, "The Clinic Map": 7 departments, 58 agents, one map a clinic owner understands at a glance; their numbers are marked "illustrative"). Same idea for BotBhai: show the owner every department of their business and which BotBhai agent runs it. Status is checked against the code in `01-botbhai/botbhai` on 11 Nov 2026: **Built** = code + tests exist; **Partial** = some parts built; **Planned** = not built yet. Never show a Planned box to a customer as working (18 Oct rule: the site must not claim more than is built).

## Shared departments (all three industries)

| Department | What the agent does | BotBhai piece | Status |
|---|---|---|---|
| Front desk | Answers WhatsApp/web chat 24×7 in English, Telugu, Hindi, Tenglish, Hinglish; books slots | `core/engine.js`, `core/slots.js`, `web/widget.js` | Built |
| No-shows | Reminder the day before and 2 hours before; follow-up after a missed visit | `core/automations.js` `dueReminders`, templates `day_before`, `two_hours` | Built |
| Win-back | Messages customers who have not come back | template `winback` | Built |
| Reviews + referrals | Asks happy customers for a Google review; gives a referral code | templates `after_visit`, `refer`, `referralCode()` | Built |
| New leads | Takes Meta ad leads in, welcomes them in seconds | `parseMetaLead`, template `lead_welcome` | Built |
| Ads | Checks Meta ads daily, pauses losers (capped), weekly ads report | `judgeAds`, `capPauses`, `adsReport` | Built |
| Owner desk | Day-close list, nudges, weekly summary on WhatsApp | `dayCloseList`, `ownerNudges`, `weeklySummary`, template `owner_report` | Built |
| Social media | Month of posts: plan → copy → compliance → design → owner OK → publish | `social/` | Partial (owner OK and publishing need the client's Meta access) |
| Phone line | Voice receptionist for calls | `voice/agent.py` (Sarvam, paid per minute) | Partial (Pro plan only) |
| Voice notes | Telugu/English/Hindi voice notes and reel voice-overs | `voice/recorded_tts.py` (Indic Parler-TTS, free on CPU) | Built (needs `HF_TOKEN`) |
| Billing | Invoices and receipts | `core/billing.js`, `core/receipt.js`, `web/billing.html` | Built |
| Contracts | Client signs the BotBhai agreement online | Documenso free hosted plan (5 documents a month, checked 11 Nov 2026) | Planned |

## Industry-only departments

| Industry | Department | What the agent does | Status |
|---|---|---|---|
| Salon | Bridal desk | Takes bridal enquiries and hands them to the owner | Built (`core/bridal.test.js`) |
| Gym | Renewals | Reminds members before their plan ends | Built (`dueRenewals`) |
| Real estate | Site visits | Books site visits, sends location and reminders | Built (slots + reminders) |
| Real estate | Lead finder | Finds new property-buyer leads from allowed sources | Built (`leadfinder/`, no Google Maps/Justdial scraping) |

## Next step
- Agents (Pixel + Forge) can turn this into a one-page visual map per industry, like the reel, using the Kalpa design system and only the Built/Partial boxes. Show Akhil first before any customer sees it.

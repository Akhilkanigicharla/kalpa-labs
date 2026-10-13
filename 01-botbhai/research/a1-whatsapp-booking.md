# a1: WhatsApp bots, booking engines and shared inboxes for BotBhai (b1)

Research agent 1 of 8. Date: 2026-10-13. Last-commit dates and licences were read from shallow clones (`git log -1`, LICENSE file). Star counts were read from GitHub pages where marked; "~" means an estimate from memory, because the page fetch hit a limit.

## Summary
BotBhai's core (its own engine, an atomic `book_slot` in Supabase, and HMAC-checked webhooks) is already sound, so no framework should replace it. The biggest gaps are a real **shared inbox with human takeover** (today the bot just pauses and tells the owner to "reply from the WhatsApp Business app") and a **booking engine** that handles staff, service durations and holidays (today slots are fixed strings plus a capacity count). The best fits are **ArnasDon/wacrm** (MIT, Next.js + Supabase + official Cloud API, so the same stack: learn from it or fork its inbox), **cal.diy**, now at `calcom/cal.com` and fully MIT (copy its slot and date-range algorithms, but don't run the app), and **whatsapp-api-js** (MIT, no dependencies, 157 tests pass: use it for typed message builders and as a check on our webhook code). Avoid unofficial WhatsApp Web libraries (Baileys, whatsapp-web.js, OpenWA, Evolution in Baileys mode), because of the ban risk and Meta's terms.

## Shortlist

| Repo | What it is | Stars | Last commit | Licence | Fit 1–5 | Verdict | Why |
|---|---|---|---|---|---|---|---|
| [ArnasDon/wacrm](https://github.com/ArnasDon/wacrm) | Self-hostable WhatsApp CRM: shared inbox, assignment, notes, roles, broadcasts, AI auto-reply with human handoff | 1.9k (page) | 2026-10-07 | MIT | 5 | ADOPT (fork the inbox) / LEARN | Same stack as ours (Next.js 16, Supabase with RLS, official Meta Cloud API). Its 1,142 tests pass. Its migrations (assignment, member presence, AI-reply caps) map straight onto our `sessions`/`messages` tables. |
| [calcom/cal.com → cal.diy](https://github.com/calcom/cal.com) | Cal.com community fork with all enterprise code removed | 49.0k (page) | 2026-09-20 | **MIT** (relicensed; was AGPL) | 4 | LEARN / copy algorithms | `packages/features/schedules/lib/slots.ts`, `date-ranges.ts` and `availability/lib/getAggregatedAvailability` (with date overrides, holidays, merging overlapping ranges) are MIT and tested. The full app is too heavy for us: the README says to set a 16 GB Node heap. |
| [Secreto31126/whatsapp-api-js](https://github.com/Secreto31126/whatsapp-api-js) | Dependency-free TypeScript Cloud API client with webhook verification and middleware for Netlify, Vercel, Cloudflare and others | 354 (page); 28.8k npm downloads/month | 2026-09-26 | MIT | 4 | ADOPT (selectively) | Typed builders for lists, buttons, templates and Flows. It verifies signatures and rejects bad ones. Requires Node ≥22.13 (fine on Netlify). |
| [david-lev/pywa](https://github.com/david-lev/pywa) | Python WhatsApp framework: Flows, templates, async, FastAPI/Flask | 591 (page); v4.5.0 | 2026-09-30 | MIT | 4 | ADOPT for `voice/` and Python agents | Its 556 tests pass. The best way to build WhatsApp Flows (form-style booking screens) in code. Fits `voice/agent.py`. |
| [WhatsApp/WhatsApp-Flows-Tools](https://github.com/WhatsApp/WhatsApp-Flows-Tools) | Meta's official Flows endpoint examples, including `examples/endpoint/nodejs/book-appointment` | 156 (page) | 2026-05-14 | MIT | 4 | LEARN / copy the example | An official appointment-booking Flow endpoint. Replaces typing back and forth for date/slot/name with one native form. |
| [chatwoot/chatwoot](https://github.com/chatwoot/chatwoot) | Omnichannel support desk with a WhatsApp Cloud channel, agents, bots and handoff | 37.3k (page) | 2026-10-12 | MIT outside `enterprise/` | 3 | LEARN (or run as a separate service later) | The best open-source inbox, but it is a 300 MB Rails app needing Redis, Sidekiq and Postgres. It won't fit free tiers or 1 hour a day. Its Agent Bot API is the pattern for bot→human handoff. |
| [schedule-x/schedule-x](https://github.com/schedule-x/schedule-x) | Modern JS event calendar (alternative to FullCalendar) | 2.6k (page) | 2026-10-06 | MIT | 3 | ADOPT for the dashboard | Day/week calendar view of `bookings` in the owner dashboard. |
| [codigoencasa/builderbot](https://github.com/codigoencasa/builderbot) | Node chatbot flow framework that works with any provider (including `@builderbot/provider-meta`) | 3.0k (page); 10k npm downloads/month | 2026-10-08 | MIT | 2 | LEARN | Popular in India and Latin America, but our engine is already more advanced. Switching would be a rewrite with no gain. |
| [alextselegidis/easyappointments](https://github.com/alextselegidis/easyappointments) | Self-hosted PHP appointment scheduler with Google Calendar sync | 4.3k (page) | 2026-10-06 | GPL-3.0 | 2 | LEARN only | A good data model for providers, services, working plans and breaks. GPL, and PHP/MySQL, so don't copy the code. |
| [EvolutionAPI/evolution-api](https://github.com/EvolutionAPI/evolution-api) | WhatsApp REST gateway (Baileys + Cloud API) with Chatwoot and Typebot bridges | 9.8k (page) | 2026-05-06 | Apache-2.0 **plus extra conditions** (logo and "usage notification") | 1 | AVOID | Licence conditions are unclear for resale. Its main mode is unofficial Baileys. |

Other candidates checked and not shortlisted (27 checked in total): n8n (Sustainable Use License, which bars resale: AVOID copying, though templates are fine to learn from), Typebot (FSL, not OSI-approved: AVOID), Hexabot (FCL-1.0 fair-core: AVOID), Botpress (MIT, now cloud-first: LEARN), Flowise (Apache-2.0, last commit 2026-08), Rasa (Apache-2.0, last commit 2025-12, heavy), Rocket.Chat (MIT, heavy), activepieces (MIT core), receevi (Supabase WhatsApp inbox, but **SSPL** and stale since 2025-01: AVOID), LibreBooking (GPL-3; versions before 7.0 have a critical admin-takeover bug), rallly (AGPL), rrule.js (BSD, stale since 2023), heyoo (MIT, stale since 2025-01), tawn33y/whatsapp-cloud-api (GPL-3, stale), WhatsApp-Nodejs-SDK (Meta, archived 2023), papercups (archived 2022), and Baileys, whatsapp-web.js and OpenWA (unofficial WhatsApp Web: AVOID).

## Tried it

All runs were offline, from inside each clone's own folder, with no real tokens. Node v22.22.0, Python 3.13.

**1. whatsapp-api-js (passed)**
```
npx -y pnpm@10 install --frozen-lockfile --ignore-scripts   # 9.2 s
npx pnpm@10 run build                                        # esbuild + tsc OK
node --test --test-reporter=spec                             # tests 157, pass 157, fail 0 (1.4 s)
```
Quickstart: a script in a separate folder loaded the built `lib/` with a dummy token and app secret.
- The GET verify returned the challenge (`42`).
- An HMAC-signed fake text message ("book haircut tomorrow 5pm" from "Ravi") reached `on.message` and returned 200.
- A bad signature threw `WhatsAppAPIFailedToVerifyError: Signature doesn't match`.
- The `Interactive(ActionList(...))` builder produced valid list JSON for a slot picker.

**2. pywa (passed after adding a missing dev dependency)**
```
python3 -m venv venv && ./venv/bin/pip install -e "./repo[fastapi,flask,cryptography]" pytest pytest-asyncio pytest-cov   # ~10 s
python -m pytest -q        # first run: 5 passed, 1 error: fixture 'mocker' not found (pytest-mock is in the uv dev group only)
pip install pytest-mock && python -m pytest -q   # 556 passed in 16.3 s
```

**3. wacrm (passed)**
```
npm ci --ignore-scripts --no-audit --no-fund   # 703 packages, 34 s
npx vitest run                                  # Test Files 96 passed, Tests 1142 passed (27 s)
```
I did not boot the Next.js app, because it needs a Supabase project and Meta keys.

**Not run:** cal.diy (only the scheduling folders were sparse-cloned and read; a full install is multi-GB) and Chatwoot (only cloned and inspected: 303 MB Rails app).

All clones were deleted afterwards.

## Concrete changes for Kalpa Labs

1. **Human takeover inbox.** In `core/engine.js`, `handoff()` currently pauses the bot and says "reply from the WhatsApp Business app". That breaks on Cloud-API numbers unless coexistence is set up. Add `web/inbox.html` plus `core/functions/inbox.js` (list conversations, send a reply through the Graph API, "resume bot" button). Model them on wacrm's inbox: add `assigned_to`, `status`, `human_until` and `notes` to `sessions` in `supabase/schema.sql`, taken from wacrm's migrations (MIT, keep the notice). Alternative: fork wacrm as the BotBhai owner app.
2. **Booking engine upgrade.** Replace `freeSlots()`/`slotMinutes()` in `core/engine.js`, which use fixed slot strings and a capacity count. Instead, port cal.diy's `schedules/lib/slots.ts` + `date-ranges.ts` logic (MIT) into a new `core/slots.js`. Drive it with per-setup working hours, breaks, holiday overrides, service duration and per-staff capacity in `setups/*/bot.config.json`. Keep `book_slot` in SQL as the final lock.
3. **WhatsApp Flows booking form.** Add `core/functions/flow.js` based on Meta's `WhatsApp-Flows-Tools/examples/endpoint/nodejs/book-appointment` (MIT), with templates under `setups/salon/`. This gives a single native form for service, date, slot and name, and the old chat steps stay as a fallback.
4. **Message builders and webhook check.** In `core/functions/_lib.js` and `whatsapp.js`, either use `whatsapp-api-js` (MIT, no dependencies) for list, button and template payloads, or at least add its webhook mock payloads (`test/webhooks.mocks.js`) to `core/functions/webhook.test.js` for new message types: `bsuid`/username contacts and v26 status payloads.
5. **Python side.** In `voice/agent.py`, send the WhatsApp confirmation with `pywa` (MIT) instead of hand-written Graph calls, and pin `pywa>=4.5` in `voice/requirements.txt`.
6. **Owner dashboard calendar.** Add a day/week booking calendar to the owner dashboard (`web/`) using `schedule-x` (MIT), reading the `bookings` table. Never adopt Baileys, Evolution, n8n, Typebot or Hexabot code in what we sell, for the licence and Meta-terms reasons above.

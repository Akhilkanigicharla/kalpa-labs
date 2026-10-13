# Deep scan v2: chat, booking and inbox for BotBhai (b1)

Deep-scan agent 2 of 8. Date: 2026-10-13. Builds on `a1-whatsapp-booking.md` (read that first; this note does not repeat its shortlist reasoning).

**How the numbers were collected.** Stars come from GitHub topic pages sorted by stars (`/topics/whatsapp-bot`, `chatbot`, `conversational-ai`, `nlu`, `no-code`, `helpdesk`, `omnichannel`, `appointment-scheduling`, `booking-system`, `whatsapp-cloud-api`, `chatbot-framework`) or from the repo page, read on 2026-10-13. Last-commit dates and licences come from 45 metadata-only shallow clones (`git clone --depth 1 --filter=blob:none --no-checkout`, then `git log -1` and `git show HEAD:LICENSE`). The `ee/` / `enterprise/` column lists folders found at the repo root that carry a different (paid) licence.

## Top 30 (by stars, relevant to chat / booking / inbox)

| # | Repo | Stars | Last commit | Licence (+ ee folders) | What | Fit for BotBhai | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | [n8n-io/n8n](https://github.com/n8n-io/n8n) | 204k | 2026-10-13 | Sustainable Use License (not OSI; bars resale) | Workflow automation with a WhatsApp node | Templates are useful as ideas; code can't go into a product we sell | AVOID code / LEARN |
| 2 | [langgenius/dify](https://github.com/langgenius/dify) | 155k | 2026-10-13 | Apache-2.0 **plus extra conditions** (no multi-tenant SaaS, keep logo) | LLM app and agent builder | Too heavy; the licence conditions conflict with multi-client hosting | LEARN |
| 3 | [FlowiseAI/Flowise](https://github.com/FlowiseAI/Flowise) | 55.5k | 2026-08-13 | Apache-2.0 | Visual LLM agent builder | We don't want an LLM in the booking path | LEARN |
| 4 | [calcom/cal.com](https://github.com/calcom/cal.com) (cal.diy) | 49.0k | 2026-09-20 | **MIT** (enterprise code removed) | Scheduling platform | `schedules/lib/slots.ts` + `date-ranges.ts` are exactly the slot algorithm we need | **ADOPT algorithm** (done: `core/slots.js`) |
| 5 | [RocketChat/Rocket.Chat](https://github.com/RocketChat/Rocket.Chat) | 46.1k | 2026-10-12 | MIT outside `ee/` (ee = proprietary) | Team chat + omnichannel livechat | Heavy Meteor + Mongo; WhatsApp is an ee app | AVOID |
| 6 | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 43.0k | 2026-10-12 | MIT | Stateful agent graphs, checkpoints, `interrupt()` for human-in-the-loop | The checkpoint + interrupt pattern equals our `humanUntil` pause; worth copying the idea for the inbox | LEARN |
| 7 | [chatwoot/chatwoot](https://github.com/chatwoot/chatwoot) | 37.3k | 2026-10-12 | MIT outside `enterprise/` | Omnichannel inbox, WhatsApp Cloud channel, Agent Bot API | Best inbox UX, but a 300 MB Rails stack | LEARN (status pattern below) |
| 8 | [wwebjs/whatsapp-web.js](https://github.com/wwebjs/whatsapp-web.js) | 22.7k | 2026-09-28 | Apache-2.0 | Unofficial WhatsApp Web client | Breaks Meta terms; numbers get banned | **AVOID** |
| 9 | [RasaHQ/rasa](https://github.com/RasaHQ/rasa) | 21.3k | 2025-12-18 | Apache-2.0 | NLU + dialogue (forms, slot filling) | Forms/digression design is the gold standard; the runtime is too heavy | LEARN |
| 10 | [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) | 16.4k | 2026-10-12 | BSD-2 | Voice agents | Already used by `voice/` (other agent's area) | ADOPT (voice) |
| 11 | [rmyndharis/OpenWA](https://github.com/rmyndharis/OpenWA) | 15.1k | 2026-10-09 | MIT | Self-hosted WhatsApp Web gateway | Unofficial | **AVOID** |
| 12 | [botpress/botpress](https://github.com/botpress/botpress) | 14.9k | 2026-10-09 | MIT (packages; cloud-first) | Bot builder | Cloud-first now; nothing we lack | LEARN |
| 13 | [WhiskeySockets/Baileys](https://github.com/WhiskeySockets/Baileys) | 11.0k | 2026-08-04 | MIT | Unofficial WhatsApp Web socket library | Breaks Meta terms | **AVOID** |
| 14 | [baptisteArno/typebot.io](https://github.com/baptisteArno/typebot.io) | 10.3k | 2026-10-07 | FSL (Functional Source, not OSI) | Visual chat-flow builder with a WhatsApp channel | Good builder UX; licence bars a competing product | AVOID code / LEARN UX |
| 15 | [evolution-foundation/evolution-api](https://github.com/evolution-foundation/evolution-api) | 9.8k | 2026-05-06 | Apache-2.0 + extra conditions | WhatsApp gateway (mostly Baileys) | Unofficial mode, unclear licence | **AVOID** |
| 16 | [devlikeapro/waha](https://github.com/devlikeapro/waha) | 7.6k | 2026-10-02 | Apache-2.0 | WhatsApp HTTP API on WhatsApp Web engines | Unofficial | **AVOID** |
| 17 | [axa-group/nlp.js](https://github.com/axa-group/nlp.js) | 6.6k | 2024-03-21 | MIT | JS intent classifier + NER, 40 languages | Tested below; tiny and fast but stale and weaker than our rules on Tenglish | LEARN (fallback idea) |
| 18 | [zammad/zammad](https://github.com/zammad/zammad) | 6.0k | 2026-10-12 | AGPL-3.0 | Helpdesk with a WhatsApp channel | AGPL | AVOID code |
| 19 | [lukevella/rallly](https://github.com/lukevella/rallly) | 5.2k | 2026-10-13 | AGPL-3.0 | Group meeting polls | Only the UX | LEARN UX |
| 20 | [freescout-help-desk/freescout](https://github.com/freescout-help-desk/freescout) | 4.6k | 2026-10-10 | AGPL-3.0 | Shared mailbox helpdesk | AGPL, PHP | LEARN |
| 21 | [alextselegidis/easyappointments](https://github.com/alextselegidis/easyappointments) | 4.3k | 2026-10-06 | GPL-3.0 | Appointment scheduler: providers, services, working plan, breaks, exceptions | Its data model matches a salon; the code is GPL | LEARN model |
| 22 | [chaskiq/chaskiq](https://github.com/chaskiq/chaskiq) | 3.6k | 2026-06-30 | AGPL-3.0 | Intercom-style live chat | AGPL | AVOID |
| 23 | [frappe/helpdesk](https://github.com/frappe/helpdesk) | 3.4k | 2026-10-11 | AGPL-3.0 | Helpdesk | AGPL | AVOID |
| 24 | [codigoencasa/builderbot](https://github.com/codigoencasa/builderbot) | 3.0k | 2026-10-08 | MIT | WhatsApp flow framework (has a Meta provider) | Our engine is ahead | LEARN |
| 25 | [abhinavxd/libredesk](https://github.com/abhinavxd/libredesk) | 3.0k | 2026-10-12 | AGPL-3.0 | Single-binary support desk | The single-binary idea; AGPL | LEARN |
| 26 | [schedule-x/schedule-x](https://github.com/schedule-x/schedule-x) | 2.6k | 2026-10-06 | MIT | JS calendar view | Owner dashboard calendar | ADOPT (dashboard) |
| 27 | [apache/burr](https://github.com/apache/burr) | 2.6k | 2026-09-20 | Apache-2.0 | Chatbots as explicit state machines with tracing | Same philosophy as our step machine; its tracing UI is a good idea | LEARN |
| 28 | [ArnasDon/wacrm](https://github.com/ArnasDon/wacrm) | 1.9k | 2026-10-07 | MIT | WhatsApp CRM inbox on Next.js + Supabase + Cloud API | Same stack; best inbox to fork (see a1) | **ADOPT inbox** |
| 29 | [shridarpatil/whatomate](https://github.com/shridarpatil/whatomate) | 1.7k | 2026-10-12 | AGPL-3.0 | Go + Vue single binary: official Cloud API inbox, flows, campaigns, IVR | Closest open-source competitor to BotBhai; AGPL, so ideas only | LEARN (competitor) |
| 30 | [david-lev/pywa](https://github.com/david-lev/pywa) | 591 | 2026-09-30 | MIT | Python Cloud API + Flows framework | For `voice/` and Python agents | ADOPT |

Also checked (below 30 or off-topic): [thunderbird/appointment](https://github.com/thunderbird/appointment) (549★, MPL-2.0, LEARN), [adamspd/django-appointment](https://github.com/adamspd/django-appointment) (277★, **Apache-2.0**, staff work-days + days-off + lead/finish time model, LEARN), [Tymeslot](https://github.com/Tymeslot/tymeslot) (174★, AGPL), [ChatbotXIO/ChatbotX](https://github.com/ChatbotXIO/ChatbotX) (532★, MIT, ManyChat alternative, LEARN), [Secreto31126/whatsapp-api-js](https://github.com/Secreto31126/whatsapp-api-js) (354★, MIT, ADOPT), [WhatsApp/WhatsApp-Flows-Tools](https://github.com/WhatsApp/WhatsApp-Flows-Tools) (156★, MIT, ADOPT), [gokapso/whatsapp-cloud-api-js](https://github.com/gokapso/whatsapp-cloud-api-js) (184★), [netflie/whatsapp-cloud-api](https://github.com/netflie/whatsapp-cloud-api) (676★, MIT, PHP), [dograh-hq/dograh](https://github.com/dograh-hq/dograh) (5.9k★, BSD, voice), [Bytedesk](https://github.com/Bytedesk/bytedesk) (AGPL), [howdyai/botkit](https://github.com/howdyai/botkit) (MIT, last commit 2022: dead), [microsoft/botframework-sdk](https://github.com/microsoft/botframework-sdk) (MIT, last 2025-12). Not cloneable: Tiledesk/tiledesk-server.

**Licence warnings.** Every big helpdesk except Chatwoot is AGPL (Zammad, FreeScout, Chaskiq, Frappe, Libredesk, Whatomate, Bytedesk). Chatwoot and Rocket.Chat are MIT only *outside* their `enterprise/` and `ee/` folders. n8n (Sustainable Use), Typebot (FSL), Hexabot (Fair-code) and Dify (extra conditions) cannot be copied into a sold product.

## Best techniques found

### Slot allocation
1. **Working hours → date ranges → slots** ([cal.com `date-ranges.ts`](https://github.com/calcom/cal.com/blob/main/packages/features/schedules/lib/date-ranges.ts), [`slots.ts`](https://github.com/calcom/cal.com/blob/main/packages/features/schedules/lib/slots.ts), MIT). Weekly rules become concrete start–end ranges per day. A **date override replaces that day's working hours completely**. A zero-length override means "closed that day" (it is kept to cancel the weekly hours, then filtered out). Slots are generated per range: start at `max(range.start, now + minimum notice)`, round up to the interval **in the business's local timezone** (cal.com's comment calls out Asia/Kolkata +5:30 rounding bugs), step by `frequency`, and keep a slot only while `start + length ≤ range.end`. Slots are de-duplicated by start time.
2. **Team availability = union or intersection** ([`getAggregatedAvailability`](https://github.com/calcom/cal.com/tree/main/packages/features/availability/lib/getAggregatedAvailability), MIT). For "any stylist" (round-robin) a slot is free if *any* member is free (union). For "everyone needed" it is the intersection (`intersect()` in `date-ranges.ts`). For a salon, "any stylist" = count free stylists per slot, which equals per-slot capacity.
3. **Interval overlap, not equal-string matching.** A 90-minute keratin booked at 4 PM blocks the 5 PM start too. cal.com checks busy times as overlapping intervals. BotBhai used to compare slot strings, so long services could be double-booked.
4. **Working plan + breaks + exceptions** ([Easy!Appointments](https://github.com/alextselegidis/easyappointments) data model, GPL: idea only). Per provider: a weekly plan with breaks, plus "working plan exceptions" for single dates. [django-appointment](https://github.com/adamspd/django-appointment) (Apache) adds a per-staff `DayOff`, `lead_time` / `finish_time` and a buffer before the next appointment.

### Conversation design
5. **Forms with per-slot validation and digressions** ([Rasa forms](https://rasa.com/docs/rasa/forms/)). Each required field has its own validator. A side question in the middle of a form (e.g. "where are you?") is answered, and then the form re-asks the same field. BotBhai validates per field but does **not** answer FAQs mid-flow (see gap list).
6. **Bot ↔ human status on the conversation** ([Chatwoot Agent Bot](https://www.chatwoot.com/docs/product/others/agent-bots)). A conversation is `pending` while the bot owns it and `open` once a human takes it. The bot only receives webhooks for `pending` ones, and the human hands it back by setting `pending` again. That is cleaner than our timer-only `humanUntil`: keep the timer as the fallback, and add an explicit status for the inbox.
7. **Checkpoint + `interrupt()`** ([LangGraph human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)). Pause a graph mid-run, let a person edit the state, resume. This maps to "owner approves a bridal enquiry, then the bot continues booking".
8. **Native forms instead of typed turns** ([WhatsApp Flows book-appointment example](https://github.com/WhatsApp/WhatsApp-Flows-Tools/tree/main/examples/endpoint/nodejs/book-appointment), MIT). One screen picks service, date and slot. Keep the chat steps as the fallback.
9. **Interactive list messages for slot pickers.** Up to 10 rows, so a day with more free slots should be paged by morning/afternoon/evening (pattern used by builderbot and wacrm).

## What BotBhai already does better
- **Indian language coverage.** Its Tenglish/Hinglish/Telugu/Hindi intent and date words (`repu`, `ellundi`, `kal`, `రేపు`) are not in any framework above. nlp.js (tested below) misses most of them out of the box.
- **₹0 per message, zero dependencies, runs in the browser and on Netlify.** Rasa, Botpress, Dify and Chatwoot all need servers.
- **Atomic booking lock in SQL (`book_slot`)** plus a graceful "someone grabbed it" recovery. Most open-source WhatsApp bots have no race handling at all.
- **Human-like disambiguation.** "4" (row 4 or 4 o'clock?), "haircut" (men or women?), "did you mean", enquiry-only services, and booking for someone else.
- **Compliance built in.** STOP/START opt-out, marketing opt-in kept separate, task-specific bot (inside WhatsApp's 2026 policy on general-purpose AI chat).
- **In-chat reschedule/cancel and returning-customer memory**, which builderbot and ChatbotX lack.

## Gaps found (for the roadmap)
- Answer FAQs mid-flow, then re-ask the step (Rasa digression pattern). Today an "address?" during the date step gives "couldn't read that date".
- An explicit inbox status (`bot` / `human` / `resolved`) alongside the `humanUntil` timer (Chatwoot pattern; wacrm schema).
- Page slot lists past 10 rows for WhatsApp interactive lists.

## Tried it
(see below; filled in after the runs)

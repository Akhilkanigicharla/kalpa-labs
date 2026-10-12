# BotBhai — automation setups for local businesses (by Kalpa Labs)

BotBhai sells **four separate setups**, each a complete system for one industry:

| Setup | For | Folder |
|---|---|---|
| Salon | salons, parlours, spas | `setups/salon` |
| Real Estate | builders, brokers, channel partners | `setups/realestate` |
| Gym | gyms, yoga and fitness studios | `setups/gym` |
| Exam Kits | coaching institutes for TSPSC, SSC, RRB, banking | `setups/examkits` |

Every setup contains: WhatsApp chatbot · lead-generation bot (Meta lead forms + Click-to-WhatsApp) · Meta ads bot · voice agent · follow-up/reminder agent · owner dashboard with Excel export · its own agent swarm with validators. Read the setup's README for price, flows, templates, ads playbook and onboarding checklist.

## How it fits together
```
Meta ad ──► lead form ──► metaleads.js ──► WhatsApp welcome (<60 s) ─┐
Meta ad ──► Click-to-WhatsApp ─────────────────────────────────────┤
Customer texts / website widget / voice note ─► whatsapp.js / chat.js ─► engine + setup config ─► replies, booking
Phone call ─► Plivo/Exotel ─► voice/agent.py (Sarvam + Groq) ─► same booking fields ─► WhatsApp confirmation
                                   all of it ─► Supabase (leads, sessions, messages) ─► owner dashboard + Excel
Hourly  reminders.js ─► 24 h / 2 h reminders, after-visit, renewals, win-backs
Daily   adsbot.js    ─► cost per lead per ad ─► pause / scale ─► owner report on WhatsApp
On demand  GitHub Action "BotBhai lead finder" ─► Excel of prospects for BotBhai's own sales
```

## Free tools used
WhatsApp Cloud API (Meta) · Netlify Functions (free tier) · Supabase Postgres (free tier) · Groq (free LLM + Whisper) · Sarvam AI (free starting credits; Indian-language speech) · Pipecat (open-source voice pipeline) · OpenStreetMap Overpass (free lead data, ODbL) · GitHub Actions · SheetJS (Excel export).

Costs that are never free and are paid by the client on their own accounts: Meta ad spend, WhatsApp template messages, phone-call minutes.

## Run all tests (no keys needed)
```
tools/test-all.sh
```

## Deploy one industry site
Netlify site → base `01-studio/botbhai`, env `SETUP=salon` (or realestate / gym / examkits), plus the env vars listed in `core/functions/whatsapp.js`. Database: run `supabase/schema.sql` once.

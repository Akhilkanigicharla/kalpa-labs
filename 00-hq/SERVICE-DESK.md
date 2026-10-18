# Service Desk: what we sell, who delivers it, and whether we may charge yet

Rule (Akhil, 18 Oct 2026): **no money is taken for anything until its delivery team and setup are proven live.** The website shows only what this page says is true. Any claim not in the "Proven" column is labelled *planned* or removed.

Checked 18 Oct 2026 23:40 IST against the repo, ROADMAP ticks and live n8n tests.

| Offer | Price on site | Proven today (evidence) | Missing before we charge | Delivery team (n8n agents) | Charge now? |
|---|---|---|---|---|---|
| **Website AI chat (Kalpa Bhai)** | free | Live on the site; Groq free models; Telugu/Hindi/English; guarded lead saving (n8n gKZZrZwdHFGxO6ys, 0L8c66aom2JiP86b; 6 live tests 18 Oct) | Telegram alert token (CEO) | Kalpa Bhai (workflow), World Keeper (3JWUJd7dccmZVbWw) | n/a (free) |
| **BotBhai salon pilot** | free 14 days, then ₹2,999 + ₹1,499/mo | Code built and tested: booking engine, 24 h/2 h reminders, shared inbox, owner dashboard, billing (ROADMAP A04–A06, `bash 01-botbhai/botbhai/tools/test-all.sh`) | WhatsApp test number (C02), demo SIM + Meta number (C14), one real salon run end to end, reminder templates approved by Meta | Chitti (customer chat), Vani (voice), Guard (risk), Dash (owner report), Forge (fixes), Kalpa (escalation) | **No.** Free pilot only. First invoice only after a salon finishes a pilot and says yes |
| **Social Team add-on** | ₹999/mo | Agents exist (Kavi, Adi, Lens, Pixel, Reel) | A finished sample month of posts for a salon, approval flow, posting tool | Kavi (captions), Adi (ads copy), Lens + Pixel (images), Reel (short video scripts), Guard (ASCI check) | **No** |
| **Workshop "Claude Code with me"** | ₹299 | Date and price decided (C31, C38) | Agenda, 3 tested mini-projects, prompt sheet, recording setup, payment page, refund flow; value review (swarm report missing 18 Oct) | Echo (research), Kavi (material), Forge (test the 3 projects), Vigil (fact-check), Doc (prompt sheet) | **No.** Free waitlist only until the agenda and materials are published |
| **Exam & Money Kits** | ₹199–499 | GATE 2027 kit v1 and Tax + SIP kit v1 built with in-sheet tests; delivery function tested with fake payments (A19–A21) | Razorpay KYC + payment pages (C24), policy pages reviewed | Doc (kit upkeep), Probe (formula tests), Vigil (tax-rule check each Budget) | **No.** Opens when C24 is done |
| **Telugu Deals channel** | free (affiliate #ad) | 10 calculators built (A15–A17); poster bot in dry-run (A18) | Telegram channel (C09), bot token secret (C27), affiliate terms checked (C39) | Deal (finds deals), Guard (ASCI #ad), Plug (posting) | n/a (free) |
| **JobCard** | free while testing | Voice-to-job-card function, Expo app scaffold (offline voice, outbox, invoice share), reminders + "my customers" PWA, schema with RLS; tests green (A34–A37) | Supabase project switches (C33), WhatsApp template (C34), 3 real technicians testing for 2 weeks | Forge (build), Probe (tests), Chitti (WhatsApp side), Vani (Telugu voice) | **No.** Free beta with technicians first (AC season Mar 2027) |
| **Tab Lifeboat** (Chrome extension) | free core, Pro later | Save/restore with Chromium e2e test, OneTab/Session Buddy importers, 1,000-tab fixture, privacy/terms pages, store images (A38–A40) | CI red on the site job (A55), policies approved (C35, partly), Chrome Web Store developer account (one-time fee, amount to verify before CEO decides), payment provider for Pro (C16) and licence check (A53) | Forge (fixes), Probe (e2e), Pixel (store images), Kavi (store text), Guard (policy check) | **No.** Free version first; Pro only after A53 + C16 |
| **Ledger Peaks** (FinOps) | early access; planned ₹4,999 audit | Price engine in ₹, 5 importers, X-ray report, DPDP catalogue, PII scan (A27–A32) | Ingest API + dashboard + alerts (A33), Supabase project (C11), one real company's usage data run end to end, sample X-ray reviewed | Ledger (costs), Quant (numbers), Vigil (DPDP facts), Doc (report), Scout (finds teams, no scraping) | **No.** Free X-ray for 2 design partners first |
| **Trading Lab** (b7) | never sold | Data + Indian costs + gate + trials registry, paper fills, risk rules, tear-sheet Action (A23–A26); gate thresholds approved (C12) | 90 days of paper trading that passes the gate; capital rules signed. SEBI: no tips, no signals sold, paper only | Quant (backtests), Guard (risk), Vigil (cost/rule facts), Probe (tests) | **Never** (research only, ₹0 by design) |

## How the teams run (free tools only)
- Every team works through **KL Tasks** in n8n (owner_agent = the agent). Kalpa reads it in the 8:45 IST brief.
- **World Keeper** (8:20 IST daily, no AI tokens) checks CI for every world, site uptime and new leads.
- Customer-facing answers come only from facts in the Kalpa Bhai prompt; anything else goes to Akhil.
- Models: Groq free (gpt-oss-20b/120b, qwen3.8-27b), NVIDIA nemotron nano, OpenRouter free as backup. No paid plans.

## Review
Re-check this table every Sunday and before changing any price or claim on the website.

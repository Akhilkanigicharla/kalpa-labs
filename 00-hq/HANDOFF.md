# START HERE: state on 6 Nov 2026 (evening IST), written for a fresh session

**Read in this order:** `CLAUDE.md` (rules; rule 0 = Akhil's ideas first, find the way) → `00-hq/VISION.md` (Akhil's 7 streams, the source of truth) → this file → `00-hq/ROADMAP.md` (top blocks) → `00-hq/log/2026-11-06.md`.

## Akhil's direction (6 Nov, in his words, firm)
- "These are my ideas, don't change them for your convenience." "Never say no to me; think every possible way; use the best AI models, Hugging Face, OpenRouter and the best GitHub repos." Do not send him lists of limits; build safety and law into the work quietly.
- 7 streams (details in VISION.md): b1 BotBhai = AI agents for **salons, gyms and real estate agents** (bookings, new customers, social media); b2 = a **worldwide paid mobile app** Claude finds, builds, deploys, promotes (JobCard PARKED, never his idea); b3 = **Exam Kits** for all govt/bank/private exams (tracker, reminders, progress, exam alerts, best material + YouTube videos; India first, then world; workshop dropped); b4 = Tab Lifeboat browser extension; b5 = Telugu Deals (affiliate yes, calculators to rework); b6 = **AI FinOps + AI Guardrails consulting** (Akhil as consultant, AIGP / ISO 42001; old "Ledger Peaks" is one small tool); b7 = **real-money algo trading for Akhil** (research → backtest → paper → small live with stop-loss + daily loss cap; Akhil sets broker keys).
- Soft launch Sun 13 Dec 2026. BotBhai pilot from Mon 16 Nov (first 3 businesses: gym, salon or real estate).

## Next job (agent queue top block "Akhil's 7 streams, restated")
A150 consulting plan · A151 exam kits research · A152 mobile app ideas (3 for Akhil to pick) · A153 trading research + build · A154 deals calculators · A155 BotBhai growth + social agents. Then A87 BotBhai depth. Research with live sources, two per fact; bring Akhil clear choices; he picks.

## What runs now (all free)
- **Agents:** GitHub Actions `agents.yml`, hourly, 8 worlds in parallel, queues `00-hq/tasks/<world>.json`, runner `00-hq/agents/runner.py` (Groq, OpenRouter, **Google Gemini 3.5 Flash / Flash-Lite**: 50-50 split, Vigil cross-checks with another provider, humanizer rules). Drafts land in `00-hq/knowledge/K*.md` (20 in review, 3 todo). Agents have NO web search: they must mark unknown facts UNVERIFIED.
- **Self-hosted n8n:** https://kalpa-n8n.onrender.com (Render free + Supabase Postgres, image n8nio/n8n:2.46.4). `n8n-sync.yml` pushes workflows from `00-hq/n8n-selfhost/workflows/` and makes credentials from GitHub secrets (Groq, OpenRouter, Telegram, Gemini). Workflow "Kalpa Morning Councils (all worlds)" 07:30 IST → Telegram, on Gemini. Keep-awake `n8n-keepalive.yml`. Render firewall blocks the word "prompts" in node names. Old n8n Cloud trial ENDED 31 Oct (locked; its MCP connector 404s).
- **Daily brief:** `daily-brief.yml` 9 PM IST to Akhil's private Telegram (CEO_CHAT_ID 1905524851; NEVER TELEGRAM_CHAT_ID = public deals channel), alerts first.
- **Website:** kalpalabs.dpdns.org (Netlify site kalpa-labs, id 187b4397-f16b-4642-ab64-87d15bd43b47). Akhil deploys by zip drag-drop (Claude's prod deploy is blocked). Chat = Netlify function `00-hq/site/netlify/functions/chat.mjs` at /api/chat (Groq → OpenRouter, 5 languages with per-turn Tenglish/Hinglish hint, callbacks → Netlify Forms "contact"). Latest built zip: v8 (gyms/salons/real estate; JobCard branch → "Mobile App, idea stage"); Akhil uploaded v6 at least: check the live deploy before assuming v7/v8 are live. Website text for Kits, Consulting, Trading must be rewritten after A150–A153.
- **CEO Room** dashboard https://claude.ai/artifact/CKKijmDLbL6hAkn5BFibpC: data files rebuilt by `00-hq/tools/ceo_room_data.py` (old n8n live sources dead). **Kingdom** https://claude.ai/artifact/MdD3R2kEYP4qHDXXvbsJF1 is private again; builds + launch/readiness synced 3 Nov.

## Akhil's open tasks (CEO queue)
Upload website v8 zip; review drafts K009/K010 (Tab Lifeboat), K006/K007 (Deals), K023 (where to find first customers), K032/K033 when done (gym + real estate pitches); C43 Reddit post; C23 lawyer/CA for BotBhai papers; C22/C24/C54 payments later. K001-v2 salon pitch approved, HOLD until A87.

## Things learned the hard way
- Ask before choosing any product for Akhil (JobCard mistake). Never shrink his idea (Ledger Peaks mistake).
- Google retired gemini-2.5-flash for new users; run `gemini-models.yml` to see working names.
- Free Render n8n has 512 MB: NODE_OPTIONS 280 MB, runners 96 MB, concurrency 1.
- Don't write chained `sleep` loops in this environment; use until-loops or background runs.

---

# Handoff · state of Kalpa Labs (updated 16 Oct 2026)

## Latest (13–16 Oct 2026): start here in a new chat
- **Built since the last update:** BotBhai Social Team (A45, `01-botbhai/botbhai/social/`), marketing team for every world in Kalpa colours (A47, `00-hq/marketing/`; b7 switched off for SEBI), Superpowers skills vendored + roadmap task engine `node 00-hq/agents/tasks.js next|validate` + short-answers skill (A46), REA outsider audit fixed (A48, `00-hq/research/rea-audit-2026-10-16.md`).
- **Akhil's PC:** has Node.js 24 + REA (`rea-agents@6.4.0`) in Claude desktop config and Claude Code (`claude mcp add rea`). REA works only in sessions running on his PC, not cloud chats. Superpowers plugin is on his account.
- **Built 16 Oct (afternoon):** A04 shared inbox (`01-botbhai/botbhai/web/inbox.html` + `core/functions/inbox.js`, commit 08b6409).
- **Built 16 Oct (late, 3):** A11 kit landing + policy pages on the calculator site (`05-deals/site`: `/kits/`, `/legal/`).
- **Built 16 Oct (late, 2):** A10 owner dashboard `01-botbhai/botbhai/web/dashboard.html` (+ brief `01-botbhai/design/BRIEF.md`).
- **Built 16 Oct (late):** A08 Cluster 1 visit sheet (`01-botbhai/docs/sales/visit-cluster1.pdf`); lead finder runs on Actions again (private 7-day artifact, `near`/`radius` inputs).
- **Built 16 Oct (night):** A07 sales kit (`01-botbhai/docs/sales/`: card, proposal, agreement, privacy notice, objections; prices.json = PLAN §2).
- **Built 16 Oct (evening):** A05 billing (`01-botbhai/botbhai/web/billing.html`, `core/functions/billing.js`, sample PDF in `01-botbhai/docs/billing/`); CI now runs BotBhai's browser + SQL checks.
- **Next agent work:** run `node 00-hq/agents/tasks.js next`. Open audit follow-ups: A49 (SEO pages), A50 (Turnstile), A51 (Vault), A52 (self-host fonts); A53 blocked on payment account (C16).
- **Next CEO work:** C01 (approve PLAN.md), C04/C05 (salon demo + list), C06, C11, C18 (Social Team price), C19 (real links), C21 (try the inbox demo), C22 (switch on billing), C23 (legal + Telugu read of the sales kit), C24 (kit policy pages + Razorpay links), C25 (Netlify visitor access at go-live), C20 (only if repo goes public).
- **Standing preferences:** research GitHub/papers/web before building; short action-first replies (`.claude/skills/short-answers/`); keep chats short, save progress to the repo.

---
# Earlier handoff (13 Oct 2026, 10:00 IST)

Read this first in any new Claude session, then `CLAUDE.md`, `README.md` and `00-hq/ROADMAP.md`.

## Who and what
- Akhil Kanigicharla, Hyderabad (IST), CEO of **Kalpa Labs** (sole proprietorship, Udyam UDYAM-TS-02-0382711). He has 1 hour a day, ₹0 budget in build mode, and a low-RAM Windows PC (nothing heavy installed locally). GitHub: Akhilkanigicharla. Business Gmail: aakhiil51458@gmail.com.
- HQ + 7 worlds: b1 BotBhai (WhatsApp + voice automation for salons first, then gyms, coaching, real estate) · b2 JobCard (voice job cards for AC technicians) · b3 Kits (exam + tax Sheets kits) · b4 Tab Lifeboat (Chrome extension) · b5 Deals & Tools (Telugu + English calculators, deals channel) · b6 Ledger Peaks (AI FinOps + DPDP evidence, flagship) · b7 Trading Lab (paper only).
- He wants depth: "world-class", "use full potential", agent swarms with validators. He doesn't want long single chats that burn his daily limit, so work in fresh sessions and save progress to the repo often.

## Done so far
- **BotBhai v3** built: `01-botbhai/botbhai/` (engine, WhatsApp/chat/reminders/ads/leads functions, Supabase schema, 4 setups, voice agent on Pipecat + Sarvam, SEO bot, lead finder (672 Hyderabad businesses), smile cards). `bash 01-botbhai/botbhai/tools/test-all.sh` is green (623/623 QA checks).
- **228-agent registry** + orchestrator: `00-hq/agents/`.
- **Research v1:** 8 GitHub reports (a1–a8), now in each world's `research/` folder.
- **Plans:** `00-hq/PLAN.md` (company) + each world's `PLAN.md`.
- **Reorganised** the repo by world, with labelled READMEs, `CLAUDE.md`, `00-hq/ROADMAP.md` (agent + CEO queues), `00-hq/LINKS.md` and `00-hq/log/`. A copy sits in the user's PC at Documents\Kalpa Labs (refresh it only on request).
- **Design system "Kalamkari"**: `00-hq/design/` (tokens, rules, free UI toolkit with verified licences). The Kingdom control room is redesigned and republished (https://claude.ai/artifact/MdD3R2kEYP4qHDXXvbsJF1, v12).
- **Scheduled tasks:** Kalpa Labs · Morning CEO brief (07:47), Evening check-in (20:44), **Build sprint** (11:07 and 23:07 IST; works through the ROADMAP Agent queue). IDs in `00-hq/LINKS.md`.

## Interrupted work: Deep Scan v2 (the user asked for it; resume it)

**Progress (13 Oct 2026, evening IST): Deep Scan v2 is COMPLETE, all 8 areas.** Reports with real runs are in every world's `research/deep-scan-v2*.md`, and the built items are ticked in ROADMAP.md (A23, A24, A27, A29, A32, A02, A06, A44, A15, A16, A34, A34b, A38, A39, A43). New follow-ups: A02b (BotBhai NLU gaps), C17 (Telugu read-through). The `Kalpa quality` workflow now runs every world's tests on each push to main; if it goes red, fixing it is the next job. Otherwise the Build sprint simply continues down the Agent queue (next unticked: A01).
The user asked: scan GitHub again, in depth, for every world. Rank the most-starred and best projects (e.g. for trading, the top algorithms and frameworks by stars), prove them, and build the best into the project. "Impress me; not a basic search."

How to do it **within limits** (the last attempts died at the usage limit, and running cloned repo code was blocked by the safety classifier):
- Do **one area per step, sequentially**, using at most 2 subagents at a time. **Save each report to the repo and commit/push before starting the next area.**
- Discovery that works here: WebFetch GitHub's star-ranked topic pages (`https://github.com/topics/<topic>?o=desc&s=stars`, plus `&page=2`), awesome lists, and the npm/PyPI JSON APIs for versions, licences and downloads. The GitHub search API is blocked. `git clone --depth 1` works, but **read** clones; don't execute their scripts. To prove a tool, install the published package from npm/PyPI into a fresh venv or node project and run our own small test against it.
- Report file per area: `<world>/research/deep-scan-v2*.md` with the top 30 repos (stars, last commit, licence incl. weights/ee caveats, ADOPT/LEARN/AVOID), what we tried with real results, and concrete changes.
- Then build the matching roadmap item(s) with tests, tick them in ROADMAP.md, and log them in `00-hq/log/`.

Order and scope (each line = one step):
1. **b7 trading:** topics algorithmic-trading, trading-bot, backtesting, quantitative-finance; awesome-quant; qlib, FinRL, freqtrade, NautilusTrader, Lean, vectorbt, backtrader, OpenAlgo, TradingAgents… Build A23 + A24 (data, Indian costs with sources, 2–3 best-evidenced strategies, gate, trials registry; synthetic data; paper only; no advice).
2. **b6 FinOps:** llmops, llm-observability, ai-gateway, pii-detection, ai-governance; LiteLLM, Langfuse, Helicone, OpenLIT, Phoenix, Opik, genai-prices, tokencost, Presidio. Competitor map. Build A27 + A29 + A32.
3. **b1 chat + booking:** whatsapp-bot, chatbot, booking-system, appointment-scheduling, customer-support; Chatwoot, Typebot, Dify, cal.diy, Easy!Appointments (unofficial WhatsApp Web libs = AVOID). Build A02 slot engine.
4. **b1 voice:** voice-agent, text-to-speech, speech-recognition, vad; Hugging Face Telugu TTS/STT (check weight licences). Build A06.
5. **Growth (all worlds):** web-scraping, seo, marketing-automation, crm, newsletter, social-media-scheduler. Build: enrich.py with extruct, SEO-bot contrast + favicon, Lighthouse CI.
6. **b3 + b5:** calculator, income-tax, astro, telegram-bot, google-apps-script, spaced-repetition (FSRS). Verify FY 2026-27 slabs. Build A15 + A16 (Astro site on Kalamkari tokens).
7. **b2 JobCard:** expo, react-native-template, invoice, offline-first. Build A34 + invoice PDF generator + transcript→job-card parser.
8. **b4 + dev tooling:** chrome-extension, tab-manager, github-actions. Build A38 + A39 + a quality workflow.

## Rules that always apply
See `CLAUDE.md`: free tiers only; never handle passwords, OTPs, tokens or bank numbers; licence rule; legal rules (Meta WhatsApp policy, TRAI, DPDP, ASCI, SEBI); tests before ticks; every UI uses `00-hq/design/`. Commit as `Akhilkanigicharla <84580207+Akhilkanigicharla@users.noreply.github.com>`, then fetch + rebase + push to `main` (the Build sprint also pushes, so rebase often).

## State on 30 Oct 2026, 14:30 IST (for a fresh session)
- **Money sprint** (top of ROADMAP agent queue): 1 Telugu Deals (A89, EarnKaro already earned ₹260), 2 Tab Lifeboat on Chrome with Pro (A90, A111, C54, A53), 3 BotBhai first salon pilot on website chat + Telegram (A87, A130 done). Other worlds paused.
- **n8n:** Task Runner t8XJCgW8Gdi2rmBX every 30 min (~70 KL Tasks queued 30 Oct; put back to `15 */3 * * *` when empty); daily councils at 06:00 IST for HQ, b5, b4, b1; CEO daily Telegram update JPcvGGcm2hq9VcQr at 9 PM IST to Akhil (chat 1905524851, @Kalplabsbot).
- **Due 31 Oct 10:00 IST:** reminder trig_011knfv7h7XE1QGnAe6fPopx → read swarm results (output_summary only) → write `01-botbhai/docs/OFFER.md`, rebuild `00-hq/leads/seeds/` from research, send Akhil the council verdicts.
- **Rules added 30 Oct:** standing go after a Depth item passes (CLAUDE.md rule 9); WhatsApp parked (C02), Telegram only.
- **Akhil's open asks:** one salon owner name for the 16 Nov pilot; C54 payment provider sign-up after research.

## 🚨 3 Nov 2026: n8n Cloud trial ENDED (31 Oct 21:45 IST)
Every n8n workflow stopped: Task Runner, councils, CEO 9 PM update, World Keeper, **website chat (Kalpa Bhai)**. Test run error: "Your trial has ended". Akhil chose BOTH GitHub Actions (primary) and self-hosted n8n (fallback), and wants alerts like this in the daily brief. Next session: A143 → A145 → A144 → A146 (ROADMAP top block). Claude weekly limit was nearly used on 3 Nov.

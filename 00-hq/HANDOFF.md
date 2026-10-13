# Handoff · state of Kalpa Labs at 13 Oct 2026, 10:00 IST

Read this first in any new Claude session, then `CLAUDE.md`, `README.md` and `00-hq/ROADMAP.md`.

## Who and what
- Akhil Kanigicharla, Hyderabad (IST), CEO of **Kalpa Labs** (sole proprietorship, Udyam UDYAM-TS-02-0382711). He has 1 hour a day, ₹0 budget in build mode, and a low-RAM Windows PC (nothing heavy installed locally). GitHub: Akhilkanigicharla. Business Gmail: aakhiil51458@gmail.com.
- HQ + 7 worlds: b1 BotBhai (WhatsApp + voice automation for salons first, then gyms, coaching, real estate) · b2 JobCard (voice job cards for AC technicians) · b3 Kits (exam + tax Sheets kits) · b4 Tab Lifeboat (Chrome extension) · b5 Deals & Tools (Telugu + English calculators, deals channel) · b6 Ledger Peaks (AI FinOps + DPDP evidence, flagship) · b7 Trading Lab (paper only).
- He wants depth: "world-class", "use full potential", agent swarms with validators. He doesn't want long single chats that burn his daily limit, so work in fresh sessions and save progress to the repo often.

## Done so far
- **BotBhai v3** built: `01-botbhai/botbhai/` (engine, WhatsApp/chat/reminders/ads/leads functions, Supabase schema, 4 setups, voice agent on Pipecat + Sarvam, SEO bot, lead finder (672 Hyderabad businesses), smile cards). `bash 01-botbhai/botbhai/tools/test-all.sh` is green (623/623 QA checks).
- **215-agent registry** + orchestrator: `00-hq/agents/`.
- **Research v1:** 8 GitHub reports (a1–a8), now in each world's `research/` folder.
- **Plans:** `00-hq/PLAN.md` (company) + each world's `PLAN.md`.
- **Reorganised** the repo by world, with labelled READMEs, `CLAUDE.md`, `00-hq/ROADMAP.md` (agent + CEO queues), `00-hq/LINKS.md` and `00-hq/log/`. A copy sits in the user's PC at Documents\Kalpa Labs (refresh it only on request).
- **Design system "Kalamkari"**: `00-hq/design/` (tokens, rules, free UI toolkit with verified licences). The Kingdom control room is redesigned and republished (https://claude.ai/artifact/MdD3R2kEYP4qHDXXvbsJF1, v12).
- **Scheduled tasks:** Kalpa Labs · Morning CEO brief (07:47), Evening check-in (20:44), **Build sprint** (11:07 and 23:07 IST; works through the ROADMAP Agent queue). IDs in `00-hq/LINKS.md`.

## Interrupted work: Deep Scan v2 (the user asked for it; resume it)

**Progress (13 Oct 2026, 10:30 IST):** Area 1 (b7 trading) DONE (A23, A24; 24 tests). Area 2 (b6 FinOps) DONE (A27, A29, A32; 35 tests). Area 3 (b1 chat) DONE (A02 + a matching fix; new A02b for NLU gaps). **Next: area 4, b1 voice (build A06).** Note: an earlier attempt already left Step-1 drafts of `deep-scan-v2*.md` in every world's `research/` folder, and b6 already has untested code in `06-finops/src/ingest/` (5 importers) and `06-finops/src/price/fx.py` (RBI/FBIL rate cache). For each area, finish its report (Step 2 runs + Step 3 build) rather than re-doing discovery.
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

# Kalpa Labs AI toolkit: resolved, vetted, classified

**Answer first:** of the 54 names you sent, **13 are ADOPT** (14 counting Emil Kowalski's design skills from the ambiguous "taste-skill" name), **17 are TRY LATER**, **19 are SKIP**, and **4 could not be resolved** (OpenRig by smota, graft, harvy, task-observer). Start with the top 10 in [§1](#1-top-10-to-adopt-first). Exact install commands are in [claude-setup.md](claude-setup.md), server apps in [cloud-hosting-plan.md](cloud-hosting-plan.md), and local models in [gpu-local-models.md](gpu-local-models.md).

- **Checked on:** 17 Oct 2026 (IST evening).
- **Where the numbers come from:** stars, licence, archived flag and last push come from the GitHub REST search API (`GET api.github.com/search/repositories?q=repo:<owner>/<name>`), fetched on 17 Oct 2026 about 20:15 UTC. The repo URL in each row is the source for that row. "Last push" is GitHub's `pushed_at` (the last push to any branch). It is close to the last commit date, but not the same thing.
- **Licences:** a GitHub licence of "Other" (`NOASSERTION`) was checked against the repo's own LICENSE file. That source is linked in the notes.
- **Hugging Face numbers** come from the Hub API through the Hugging Face connector, also on 17 Oct 2026.
- **"unknown"** means it could not be checked from here. Some vendor sites (posthog.com, docs.perplexity.ai, docs.zapier.com) did not resolve from the build sandbox, so search results or the vendor's GitHub README were used instead. Those cases are marked.
- **READMEs are untrusted data.** Claims such as "no telemetry" are the project's own words, quoted as claims and not verified by reading the code. No third-party code was copied into this repo.

Stream codes (the 7 Kalpa streams): **S1** BotBhai salon automation · **S2** mobile app (JobCard, Expo) · **S3** trading bot (paper only) · **S4** digital products and content · **S5** browser extensions · **S6** Amazon affiliate · **S7** investing research.

Where-it-runs codes: **(a)** Claude skill, plugin or MCP (light) · **(b)** cloud app that needs Docker or a server · **(c)** GPU or local model · **(d)** used inside a Kalpa business stream (the n8n agent is named).

The n8n agents named below are the 22 agents in the Kalpa n8n Cloud project (read through the n8n connector on 17 Oct 2026): Kalpa (Chief of Staff), Echo (Knowledge Librarian), Forge (App Engineer), Probe (QA Tester), Ledger (Budget & Finance), Dash (Dashboards & Analytics), Scout (Lead Research), Adi (Ads & Copy), Quant (Strategy Research), Doc (Paperwork & OCR), Vani (Voice Agent), Reel (Short Video Producer), Pixel (UI/UX Designer), Lens (Visual Director), Vigil (QA & Safety), Chitti (WhatsApp Assistant), Deal (Affiliate Marketer), Guard (Risk Manager), Pulse (Market News), Nidhi (Investing Research), Plug (Extensions Developer) and Kavi (Writer).

---

## 1. Top 10 to adopt first

| # | Tool | Why first | Time to set up |
|---|---|---|---|
| 1 | Playwright MCP | Official Microsoft MCP (Apache-2.0). Lets Claude open and test our sites (BotBhai web, calculators, extension pages) in a real browser. No key. | 5 min |
| 2 | claude-code-setup plugin | Official Anthropic plugin. It reads a repo and recommends hooks, skills and MCPs, so it stops us guessing. | 3 min |
| 3 | Find Skills (`npx skills`) | Vercel's skill installer and search. It is the install path for #4 and #5. Turn telemetry off. | 3 min |
| 4 | Grill Me (mattpocock/skills) | Forces a plan to be questioned before building. That fits a 1-hour-a-day CEO. | 3 min |
| 5 | Cloudflare security-audit skill | Official Cloudflare, MIT. Six-phase security audit of our own code before BotBhai goes live. | 3 min |
| 6 | PostHog Cloud + PostHog MCP | Product analytics for the BotBhai web pages, calculator site and extension. The hosted MCP uses OAuth, so no key is stored. | 15 min |
| 7 | HyperFrames | HeyGen's Apache-2.0 "HTML to video" renderer with a Claude plugin. Reel can make shorts from Kalamkari-styled HTML and render them in GitHub Actions. | 10 min |
| 8 | Scrapling | BSD-3 Python scraper, run in GitHub Actions. Only for allowed public pages (price pages, our own sites), never Maps, Justdial or Instagram. | 20 min |
| 9 | Presenton | Apache-2.0 deck generator (Docker) that works with OpenRouter or Ollama. Makes kit and digital-product decks. Turn anonymous tracking off. | 30 min |
| 10 | Expo | MIT mobile framework that JobCard already plans to use (month 3, per `02-jobcard/PLAN.md`). Runs in Codespaces and on EAS, nothing on the PC. | when JobCard starts |

The other ADOPT items (public-apis, emilkowalski/skills, PostHog MCP once PostHog is live, and Rea, which is already installed) are low-effort and can follow.

---

## 2. Master table

| # | Name (as given) | Resolved to (full URL) | Stars | Licence | Last push | Category | Verdict | Where it runs | Cost | Kalpa use (stream · n8n agent) | Install |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Scrapling (D4Vinci) | https://github.com/D4Vinci/Scrapling | 88,279 | BSD-3-Clause | 2026-10-17 | Web scraping library + MCP | **ADOPT** | (b) GitHub Actions / Codespaces (Python), (d) | ₹0 | S6 price checks, S1 lead enrichment from **allowed** sources · Scout, Deal | `pip install scrapling` in an Actions job (see cloud plan) |
| 2 | Dify | https://github.com/langgenius/dify | 158,723 | Apache-2.0 + extra conditions ([LICENSE](https://github.com/langgenius/dify/blob/main/LICENSE)) | 2026-10-17 | LLM app/agent builder | **SKIP** | (b) Docker, heavy | ₹0 self-host | Duplicates n8n; licence bars multi-tenant hosting · none | — |
| 3 | OpenSEO (every-app/open-seo) | https://github.com/every-app/open-seo | 23,912 | MIT | 2026-10-14 | SEO suite (Semrush alternative) | **TRY LATER** | (b) Cloudflare free plan or Docker | Needs paid DataForSEO key; hosted plan $10/mo ([README](https://github.com/every-app/open-seo)) | S4/S6 keyword research · Kavi, Deal | Decide on DataForSEO spend first |
| 4 | openshorts (mutonby) | https://github.com/mutonby/openshorts (search index did not return it; the page exists: 6.7k stars, MIT core + commercial `cloud/` dir, per the [repo page](https://github.com/mutonby/openshorts)). Plugin: https://github.com/mutonby/openshorts-plugin | ~6.7k (page) | MIT core; `cloud/` = OpenShorts Commercial License | unknown | Long video → shorts | **TRY LATER** | (b) Docker Compose, 8 GB+ RAM recommended | Gemini key (free tier) + fal.ai / ElevenLabs / Upload-Post for some features | S4 content shorts · Reel | Docker in Codespaces only |
| 5 | Presenton | https://github.com/presenton/presenton | 11,175 | Apache-2.0 | 2026-10-16 | AI presentation generator + MCP | **ADOPT** | (b) Docker (Codespaces or HF Space) | ₹0 with OpenRouter free / Ollama | S4 kit decks, S1 sales decks · Kavi, Pixel | `docker run … ghcr.io/presenton/presenton` with `DISABLE_ANONYMOUS_TRACKING=true` |
| 6 | ds4 (antirez) | https://github.com/antirez/ds4 | 23,903 | MIT | 2026-10-08 | DeepSeek V4 local inference engine | **SKIP** | (c) Mac ≥ 96 GB or DGX Spark / Ada-class GPUs | Hardware only | None on current PC | See gpu-local-models.md |
| 7 | Ollama | https://github.com/ollama/ollama | 183,619 | MIT | 2026-10-17 | Local model runner | **TRY LATER** | (c) local, after `nvidia-smi` check | ₹0 | Offline drafts if the PC can run a 1–4B model · Kavi, Echo | gpu-local-models.md |
| 8 | Text-to-CAD (earthtojake) | https://github.com/earthtojake/text-to-cad | 21,232 | MIT | 2026-10-17 | Agent CAD skill | **SKIP** | (a) | ₹0 | No stream needs CAD | — |
| 9 | ponytail (DietrichGebert) | https://github.com/DietrichGebert/ponytail | 166,092 | MIT | 2026-10-16 | Claude plugin: "write less code" | **TRY LATER** | (a) plugin | ₹0 | Forge, Plug coding sessions | Review `hooks/` + `scripts/` first |
| 10 | God's Eye View | https://github.com/bilawalsidhu/gods-eye-view | 57,588 | MIT (code only; some data CC BY-NC / ODbL, per [LICENSE](https://github.com/bilawalsidhu/gods-eye-view/blob/main/LICENSE)) | 2026-10-17 | 3D OSINT globe | **SKIP** | (b) Node/Docker | Metered Google/OpenAI keys for some features | No stream fit | — |
| 11 | HyperFrames (heygen-com) | https://github.com/heygen-com/hyperframes | 65,887 | Apache-2.0 | 2026-10-17 | HTML → MP4 video, agent skills | **ADOPT** | (a) plugin + (b) render in GitHub Actions (Node 22 + FFmpeg) | ₹0 | S4 shorts, S1 salon promo reels, S6 deal reels · Reel, Lens | `claude plugin install hyperframes@hyperframes` |
| 12 | OpenMontage | https://github.com/calesthio/OpenMontage | 69,131 | **AGPL-3.0** | 2026-10-16 | Agentic video production | **TRY LATER** | (b) Python + FFmpeg; many paid model APIs | API costs | Reel (tool use only; never ship its code) | — |
| 13 | multica | https://github.com/multica-ai/multica | 53,065 | Multica License (Apache-2.0 + conditions; "source-available") | 2026-10-16 | Human + agent task board | **SKIP** | (b) Docker + Postgres 17 | ₹0 self-host | Duplicates n8n agents + ROADMAP; daily telemetry by default | — |
| 14 | Talorys (rociiu) | https://github.com/rociiu/talorys | 1,296 | MIT | 2026-10-17 | Personal AI agent on Cloudflare | **TRY LATER** | (b) Cloudflare Workers free plan | ₹0 (daily AI quota) | CEO personal reminders/notes | `npx create-talorys@latest` (repo is 1 week old) |
| 15 | OpenRig (smota) | **Not found under smota.** Closest: https://github.com/mvschwarz/openrig | 7,671 (mvschwarz) | Apache-2.0 | 2026-10-17 | Multi-agent rig for Claude Code/Codex (tmux) | **SKIP (unresolved)** | (a)/(b) needs tmux | — | Ambiguous; please send the full link | — |
| 16 | PostHog | https://github.com/PostHog/posthog | 40,325 | MIT Expat outside `ee/` ([LICENSE](https://github.com/PostHog/posthog/blob/master/LICENSE)) | 2026-10-17 | Product analytics, flags, replay | **ADOPT (cloud)** | (b) use PostHog Cloud free plan, not self-host | Free plan; exact limits unknown (posthog.com unreachable from sandbox) | S1, S4, S5, S6 sites · Dash | Sign-up by Akhil; snippet in sites |
| 17 | Invoice Ninja | https://github.com/invoiceninja/invoiceninja | 10,290 | **Elastic License 2.0** ([LICENSE](https://github.com/invoiceninja/invoiceninja/blob/v5-stable/LICENSE)) | 2026-10-16 | Invoicing | **SKIP** | (b) PHP/Laravel | — | BotBhai billing already built (A05); ELv2 bars hosting for clients | — |
| 18 | Cal.diy (calcom) | https://github.com/calcom/cal.diy | 49,113 | MIT | 2026-09-26 | Scheduling platform | **TRY LATER** | (b) Next.js + Postgres | ₹0 self-host | S1: slot algorithm already learned (A02) · Chitti | — |
| 19 | Autumn (useautumn) | https://github.com/useautumn/autumn | 2,823 | Apache-2.0 | 2026-10-17 | Pricing/billing layer | **SKIP** | (b) | — | Built around Stripe; India billing is Razorpay/UPI (Razorpay support: unknown) | — |
| 20 | Typebot | https://github.com/baptisteArno/typebot.io | 10,554 | **FSL-1.1-Apache-2.0** ([LICENSE](https://github.com/baptisteArno/typebot.io/blob/main/LICENSE)) | 2026-10-15 | Chatbot builder | **SKIP** | (b) | — | FSL bars a competing commercial product, which BotBhai is (same finding as `01-botbhai/research/deep-scan-v2-chat.md`) | — |
| 21 | Frappe CRM | https://github.com/frappe/crm | 3,804 | **AGPL-3.0** | 2026-10-17 | CRM | **TRY LATER** | (b) Frappe bench, heavy | ₹0 self-host | S1 salon pipeline · Scout (internal tool only, never in sold code) | — |
| 22 | Mautic | https://github.com/mautic/mautic | 10,787 | GPL-3.0 ([LICENSE](https://github.com/mautic/mautic/blob/7.x/LICENSE.txt)) | 2026-10-16 | Email marketing automation | **SKIP** | (b) PHP + MySQL | ₹0 self-host | Heavy for us; TRAI/consent rules limit outreach anyway | — |
| 23 | Chatwoot | https://github.com/chatwoot/chatwoot | 37,895 | MIT Expat outside `enterprise/` ([LICENSE](https://github.com/chatwoot/chatwoot/blob/develop/LICENSE)) | 2026-10-17 | Omnichannel inbox | **TRY LATER** | (b) min 4 GB RAM ([docs](https://developers.chatwoot.com/self-hosted/deployment/requirements)) | No free host fits except Oracle Always Free | S1 shared inbox (A04 already built in-house) · Chitti | — |
| 24 | PhotoCraft (storytold) | https://github.com/storytold/photocraft | 66,210 | Apache-2.0 | 2026-10-17 | Rust photo editor (desktop) | **SKIP** | Desktop app | — | Repo created 30 Sep 2026 with 2,733 open issues; too new to trust | — |
| 25 | Compositor (robbietilton) | https://github.com/robbietilton/Compositor | 17,298 | MIT | 2026-10-15 | Photoshop alternative | **SKIP** | macOS only (Swift) | — | CEO is on Windows | — |
| 26 | Rea (morluto/rea) | https://github.com/morluto/rea | 305,698 | MIT | 2026-10-17 | Reverse-engineering agent tools (MCP) | **ADOPT (already installed)** | (a) MCP on Akhil's PC | ₹0 | Outsider audits (A48 done) · Vigil, Probe | Already in Claude Code (`claude mcp add rea`) |
| 27 | Find Skills (vercel-labs/skills) | https://github.com/vercel-labs/skills | 35,356 | MIT | 2026-10-09 | Skill installer + search (`npx skills`) | **ADOPT** | (a) | ₹0 | Install/search skills for all agents | `npx skills find <word>`; set `DISABLE_TELEMETRY=1` |
| 28 | Orca (stablyai) | https://github.com/stablyai/orca | 95,246 | MIT | 2026-10-17 | Desktop agent IDE | **SKIP** | Desktop app | ₹0 | Heavy for a low-RAM PC; 8,544 open issues | — |
| 29 | Arena skill (Jakeschincariol) | https://github.com/Jakeschincariol/arena-skill | 712 | MIT | 2026-09-27 | 100-agent "tournament" skill | **TRY LATER** | (a) | Burns a lot of usage (100 sub-agents per run, per repo description) | Hard prompts only · Kavi, Adi | — |
| 30 | Universal Modder (rehan-remade) | https://github.com/rehan-remade/universal-modder | 8,212 | MIT | 2026-10-17 | Game-modding plugin | **SKIP** | (a) + fal API | fal credits | No stream fit | — |
| 31 | Cloudflare security audit skill | https://github.com/cloudflare/security-audit-skill | 30,625 | MIT | 2026-09-14 | Security audit skill | **ADOPT** | (a) | ₹0 | Every world before go-live · Vigil, Probe | `npx skills add … --skill security-audit -g` |
| 32 | SlopMonster (ItsssssJack) | https://github.com/ItsssssJack/SlopMonster | 1,106 | MIT | 2026-09-26 | Lint AI-sounding copy | **TRY LATER** | (a)/(b) Python, uses a "rival model" | API key of a second model | S4/S6 copy · Kavi, Adi | — |
| 33 | taste-skill (Emil Kowalski design) | **Ambiguous.** `taste-skill` is https://github.com/Leonxlnx/taste-skill. Emil Kowalski's own repo is https://github.com/emilkowalski/skills | 98,405 / 46,992 | MIT / MIT | 2026-10-14 / 2026-10-11 | Design skills | Leonxlnx: **TRY LATER**; emilkowalski: **ADOPT** | (a) | ₹0 | Pixel, Lens, but must obey the Kalamkari design system (rule 6) | See claude-setup.md |
| 34 | Impeccable skill | https://github.com/pbakaus/impeccable | 82,325 | Apache-2.0 | 2026-10-17 | Design skill + detector | **TRY LATER** | (a) | ₹0 | Pixel. Telemetry on by default, downloads a binary, and hooks run outside tool approval (README) | Only with `IMPECCABLE_NO_TELEMETRY=1` after review |
| 35 | Grill Me skill | https://github.com/mattpocock/skills (path `skills/productivity/grill-me/SKILL.md`) | 294,973 | MIT | 2026-10-13 | Planning-interview skill | **ADOPT** | (a) | ₹0 | Kalpa (Chief of Staff) planning | `npx skills add mattpocock/skills -g` (pick grill-me) |
| 36 | graft | **Ambiguous / not resolved.** Top "graft" repo is https://github.com/orbitinghail/graft (storage engine), not an AI tool | 1,566 | Apache-2.0 | 2026-10-13 | — | **SKIP (unresolved)** | — | — | Please send the full link | — |
| 37 | agency-agents | https://github.com/msitarzewski/agency-agents | 160,844 | MIT | 2026-10-15 | 100+ agent persona files | **TRY LATER** | (a) markdown agents | ₹0 | Prompt ideas for n8n agents · Kalpa | Read-only reference; don't bulk-install |
| 38 | codebase-memory MCP | https://github.com/DeusData/codebase-memory-mcp | 46,766 | MIT | 2026-10-17 | Code knowledge-graph MCP | **TRY LATER** | (a) single binary | ₹0 | Forge on big repos. Unsigned Windows binary (Defender false-positive noted in its README) | — |
| 39 | ECC | https://github.com/affaan-m/ECC | 282,320 | MIT | 2026-10-15 | Mega harness: 311 skills, 71 agents, hooks | **SKIP** | (a) | ₹0 | Overlaps Superpowers; large context load; open Windows defects (README) | — |
| 40 | Playwright MCP | https://github.com/microsoft/playwright-mcp | 38,284 | Apache-2.0 | 2026-10-16 | Browser automation MCP | **ADOPT** | (a) `npx` (Node 18+) | ₹0 | Test S1/S4/S5/S6 sites · Probe, Vigil | `claude mcp add -s user playwright -- npx @playwright/mcp@latest` |
| 41 | Perplexity MCP | https://github.com/perplexityai/modelcontextprotocol (official) | 2,577 | MIT | 2026-10-17 | Web-search MCP | **TRY LATER** | (a) | **Paid API**, no standing free tier per [search summary](https://costbench.com/software/ai-search-apis/perplexity-sonar-api/) (unverified on Perplexity's own page) | Pulse, Nidhi research | In `.mcp.json` with a placeholder; enable only if Akhil pays |
| 42 | PostHog MCP | Hosted `https://mcp.posthog.com/mcp`; code moved to https://github.com/PostHog/posthog/tree/master/services/mcp (old repo https://github.com/PostHog/mcp is **archived**) | 151 (old repo) | MIT | 2026-01-19 (old repo) | Analytics MCP | **ADOPT** | (a) remote HTTP + OAuth | ₹0 on free plan | Dash | `claude mcp add --transport http posthog https://mcp.posthog.com/mcp -s user` ([PostHog docs](https://posthog.com/docs/model-context-protocol/claude-code)) |
| 43 | Zapier MCP | https://github.com/zapier/zapier-mcp (plugin distribution of the hosted server) | 441 | MIT | 2026-07-29 | Hosted app-connector MCP | **SKIP** | (a) hosted | Free plan is tiny; sources disagree (≈50 calls or 300/month) ([Zapier usage doc](https://docs.zapier.com/mcp/usage), [Latenode](https://latenode.com/blog/zapier-mcp-pricing)) | n8n already does this | — |
| 44 | public-apis | https://github.com/public-apis/public-apis | 489,727 | MIT | 2026-10-17 | List of free APIs | **ADOPT** | Reference only | ₹0 | Finding free data APIs · Scout, Pulse, Quant | Bookmark |
| 45 | freellm | **Ambiguous.** Most-starred: https://github.com/tashfeenahmed/freellmapi. Exact name: https://github.com/Devansh-365/freellm | 36,569 / 64 | MIT / MIT | 2026-10-17 / 2026-05-29 | Free-tier LLM router | **SKIP** | (b) Node | ₹0 | README says "personal experimentation only"; stacking free tiers is fragile. n8n already uses OpenRouter free | — |
| 46 | harvy | **Not found** (GitHub search for "harvy" returned only unrelated personal repos) | — | — | — | — | **SKIP (unresolved)** | — | — | Please send the full link | — |
| 47 | MiroFish | https://github.com/666ghj/MiroFish | 79,922 | **AGPL-3.0** | 2026-10-16 | Swarm "predict anything" engine | **SKIP** | (b) heavy | LLM costs | Risky for S3/S7 (SEBI: no tips); AGPL | — |
| 48 | omniroute | https://github.com/diegosouzapw/OmniRoute | 77,670 | MIT | 2026-10-17 | AI gateway, 359 providers | **SKIP** | (b) | ₹0 | README lists 13 providers as terms-risk "avoid" and mentions "TLS stealth"; it holds all keys | — |
| 49 | graphify | https://github.com/Graphify-Labs/graphify | 127,703 | Apache-2.0 | 2026-10-16 | Codebase → knowledge-graph skill | **TRY LATER** | (a) needs Python/uv; run in cloud sessions, not on the PC | ₹0 | Echo (repo knowledge) | `uv tool install graphifyy` then `graphify install` (cloud only) |
| 50 | headroom | https://github.com/headroomlabs-ai/headroom | 75,581 | Apache-2.0 | 2026-10-17 | Token-compression proxy/MCP | **TRY LATER** | (a)/(b) proxy | ₹0 | Could cut usage. Telemetry beacon on by default; proxy sits in front of all model traffic | Only with `HEADROOM_TELEMETRY=off` |
| 51 | claude-code-setup | Official plugin in https://github.com/anthropics/claude-plugins-official | 41,571 | Apache-2.0 | 2026-10-17 | "Automation recommender" plugin | **ADOPT** | (a) | ₹0 | Every repo setup · Forge | `/plugin install claude-code-setup@claude-plugins-official` |
| 52 | task-observer | **Not resolved.** Only https://github.com/vedhanth1304/task-observer (1 star, no description) matched | 1 | none stated | 2026-08-30 (updated) | unknown | **SKIP (unresolved)** | — | — | Please send the full link | — |
| 53 | OpenJev (HF GGUF, llama.cpp) | https://huggingface.co/ggml-org/OpenJev-GGUF (quantised from https://huggingface.co/openjev/openjev) | 20 likes / 11.3k downloads (HF) | **CC BY-NC 4.0 (non-commercial)** | 2026-10-11 (HF "updated") | 27B "decision" model, `/v1/systemone` API | **SKIP** | (c) Q4_K_M file is 19.4 GB, so it needs ≈24 GB RAM/VRAM (estimate) | ₹0 | Non-commercial licence bars business use | gpu-local-models.md (for reference) |
| 54 | Expo | https://github.com/expo/expo | 52,793 | MIT | 2026-10-17 | React Native framework | **ADOPT** | (b) Codespaces + EAS cloud builds | ₹0 to start (EAS free-plan limits: unknown) | S2 JobCard app (month 3) · Forge | `npx create-expo-app` in Codespaces |
| 55 | llama.cpp (related to OpenJev) | https://github.com/ggml-org/llama.cpp | 131,513 | MIT | 2026-10-17 | Local GGUF inference | **TRY LATER** | (c) CPU or GPU | ₹0 | Needed only for GGUF models | gpu-local-models.md |
| 56 | emilkowalski/skills | see #33 | 46,992 | MIT | 2026-10-11 | Design/animation skills (Markdown) | **ADOPT** | (a) | ₹0 | Pixel, Plug | `npx skills add emilkowalski/skills -g` |
| 57 | Leonxlnx/taste-skill | see #33 | 98,405 | MIT | 2026-10-14 | Art-direction skill (runs Node + Chrome, fetches images) | **TRY LATER** | (a) | ₹0 | Lens. May fight Kalamkari rules | — |
| 58 | openshorts-plugin | https://github.com/mutonby/openshorts-plugin | 0 | MIT | 2026-10-17 | Claude plugin for hosted OpenShorts MCP | **SKIP (for now)** | (a) hosted | Hosted service pricing unknown | Created today; wait | — |

Rows 1–54 are the names you sent. Rows 55–58 are related entries found while resolving them. Playwright is also used in CI through `@playwright/test`, which is the same project as #40.

Count over rows 1–54: ADOPT 13 (Scrapling, Presenton, HyperFrames, PostHog, Rea, Find Skills, Cloudflare audit, Grill Me, Playwright MCP, PostHog MCP, public-apis, claude-code-setup, Expo), plus the split #33 (emilkowalski/skills ADOPT); TRY LATER 17; SKIP 19; unresolved 4.

---

## 3. Vetting notes and red flags (per tool)

These are the findings behind each verdict. Each claim is the project's own README unless said otherwise.

**Light Claude-side tools (a)**
- **Playwright MCP.** It is official Microsoft and needs Node 18+ ([README](https://github.com/microsoft/playwright-mcp)). It asks for no credentials. The README doesn't mention telemetry (unknown). Its browser can log in to sites, so never let it type passwords. Akhil types those himself.
- **PostHog MCP.** The hosted server is at `mcp.posthog.com/mcp` and logs in by browser OAuth on first use. PostHog's docs advise reviewing each tool call because of prompt-injection risk ([PostHog Claude Code docs](https://posthog.com/docs/model-context-protocol/claude-code), seen via search). The old GitHub repo is archived and its code now lives in the monorepo ([archived README](https://github.com/PostHog/mcp)).
- **Perplexity MCP.** This is the official server (`@perplexity-ai/mcp-server`, env var `PERPLEXITY_API_KEY`) ([README](https://github.com/perplexityai/modelcontextprotocol)). The API is pay-as-you-go: base Sonar was reported at $1 per 1M input and output tokens, plus a per-search fee ([CostBench](https://costbench.com/software/ai-search-apis/perplexity-sonar-api/), not verified on Perplexity's site). That cost makes it a CEO decision.
- **Find Skills / `npx skills`.** It sends anonymous usage telemetry by default. Set `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` to stop it ([README](https://github.com/vercel-labs/skills)).
- **Cloudflare security-audit skill.** It ships two zero-dependency Node validators. The README asks that target code be built and tested in a sandbox with networking off ([README](https://github.com/cloudflare/security-audit-skill)). We run it in cloud sessions or Codespaces, not on the PC.
- **Grill Me.** This is one SKILL.md in Matt Pocock's skills repo. The Claude plugin route installs the whole set. `npx skills` lets you pick just grill-me ([README](https://github.com/mattpocock/skills)).
- **claude-code-setup.** This is Anthropic's own plugin (official marketplace). It is already active in Kalpa's cloud sessions (the `claude-code-setup:claude-automation-recommender` skill), so this is low risk.
- **ponytail.** It is one SKILL.md plus a status band. The plugin also has `hooks/` and `scripts/` folders that the README doesn't explain. `/ponytail band import` reads past Claude Code sessions, locally per the README ([README](https://github.com/DietrichGebert/ponytail)). It reached 166k stars in 4 months. Review the hooks before installing.
- **Impeccable.** Telemetry is **on by default**: it calls impeccable.style and records design choices. It downloads an engine binary to `~/.impeccable/bin/`, and its hooks "run independently of model-tool approval" ([README](https://github.com/pbakaus/impeccable)). Hence TRY LATER.
- **taste-skill (Leonxlnx).** It runs scripts on Node 22+ with a local Chrome, and fetches pictures from Wikimedia, Openverse and the Met ([README](https://github.com/Leonxlnx/taste-skill)). The repo also promotes a sponsor's API key, which is optional.
- **codebase-memory MCP.** No telemetry and no network calls, per the README. It ships a prebuilt, **unsigned** Windows binary that Defender may flag, with SHA-256 checksums published ([README](https://github.com/DeusData/codebase-memory-mcp)).
- **ECC.** It installs 71 agents, 311 skills, hooks and rules. The guided installer edits `~/.claude/settings.json`, and native Windows has open defects ([README](https://github.com/affaan-m/ECC)). It is too invasive next to Superpowers.
- **graphify.** No telemetry, per the README, but it logs queries to `~/.cache/graphify-queries.log`. It needs Python (uv/pipx) ([README](https://github.com/Graphify-Labs/graphify)). That breaks the "nothing installed on the PC" rule, so run it in cloud sessions only.
- **headroom.** An anonymous telemetry beacon is on by default, and the proxy checks PyPI daily. Windows wheel support is described inconsistently ([README](https://github.com/headroomlabs-ai/headroom)).
- **Rea.** Already installed and audited (A48, `00-hq/research/rea-audit-2026-10-16.md`). It has 305k stars in 6 months, which is unusual growth, so keep it scoped to audits.
- **agency-agents.** These are plain Markdown personas. The installer is a bash script, `scripts/install.sh` ([README](https://github.com/msitarzewski/agency-agents)), with no Windows CLI steps. Use it as reading material for n8n agent prompts.
- **Arena skill.** It runs up to 100 strategies as sub-agents per task (repo description), which would eat Akhil's daily limit.

**Server apps (b)**
- **Presenton.** Anonymous tracking is on unless `DISABLE_ANONYMOUS_TRACKING=true`. It has an MCP endpoint at `/mcp` with 90-day API keys. It supports OpenRouter and Ollama ([README](https://github.com/presenton/presenton)).
- **HyperFrames.** Needs Node 22+ and FFmpeg. Cloud render is a HeyGen-hosted option, and whether it needs an account is unknown, so we render locally in Actions ([README](https://github.com/heygen-com/hyperframes)).
- **Scrapling.** BSD-3 with an MCP server. It has "stealth" features. Kalpa rule 4 bans scraping Google Maps, Justdial, Instagram and consumers' numbers, so respect robots.txt and site terms.
- **openshorts.** The core is MIT, and `cloud/` is source-available only. It needs a Gemini key (or a local LLM) plus fal.ai, ElevenLabs and Upload-Post for some features, and recommends 8 GB+ RAM ([repo page](https://github.com/mutonby/openshorts)). Upload-Post auto-publishing would need care with platform rules.
- **OpenSEO.** Needs your own **paid DataForSEO** key. The hosted plan adds a 28% markup and costs $10/month. It can run on the Cloudflare free plan ([README](https://github.com/every-app/open-seo)).
- **Talorys.** Single-user, on Cloudflare free (Workers AI daily quota). No telemetry, per the README. You log in to Cloudflare with Wrangler OAuth ([README](https://github.com/rociiu/talorys)). Akhil does that login himself. The repo is 1 week old.
- **Chatwoot.** Official minimum is 2 CPU, 4 GB RAM and 20 GB SSD, plus Postgres and Redis ([Chatwoot docs](https://developers.chatwoot.com/self-hosted/deployment/requirements)).
- **Dify.** Apache-2.0 plus: no multi-tenant service without permission, and keep the logo ([LICENSE](https://github.com/langgenius/dify/blob/main/LICENSE)).
- **multica.** Sends a daily anonymous snapshot (opt out with `DO_NOT_TRACK=1`). The licence is Apache-2.0 plus conditions ([README](https://github.com/multica-ai/multica)).
- **Typebot.** FSL-1.1: "Competing Use" (a commercial product with the same functionality) is not allowed until 2 years after each release ([LICENSE](https://github.com/baptisteArno/typebot.io/blob/main/LICENSE)).
- **Invoice Ninja.** ELv2: "You may not provide the software to third parties as a hosted or managed service" ([LICENSE](https://github.com/invoiceninja/invoiceninja/blob/v5-stable/LICENSE)).
- **OmniRoute.** README: 13 providers are tagged terms-risk "avoid". It mentions "TLS stealth" and OAuth to consumer coding plans ([README](https://github.com/diegosouzapw/OmniRoute)). That is a ToS and account-ban risk.
- **freellmapi.** Keys are AES-256-GCM encrypted in SQLite. It fetches a model catalog from freellmapi.co twice a day. "Personal experimentation only" ([README](https://github.com/tashfeenahmed/freellmapi)).

**GPU and local models (c):** see [gpu-local-models.md](gpu-local-models.md). ds4 targets Macs with 96 GB+ or a DGX Spark ([README](https://github.com/antirez/ds4)). OpenJev's Q4 file alone is 19.4 GB and its licence is non-commercial ([HF repo](https://huggingface.co/ggml-org/OpenJev-GGUF)).

---

## 4. Which n8n agent uses what

| n8n agent | Stream | Tools from this list |
|---|---|---|
| Probe (QA Tester), Vigil (QA & Safety) | all | Playwright MCP, Cloudflare security audit, Rea |
| Dash (Dashboards & Analytics) | S1, S4, S5, S6 | PostHog + PostHog MCP |
| Reel (Short Video Producer), Lens (Visual Director) | S1, S4, S6 | HyperFrames (now), openshorts / OpenMontage (later) |
| Kavi (Writer), Pixel (UI/UX Designer) | S4 | Presenton, emilkowalski/skills, SlopMonster (later) |
| Scout (Lead Research), Deal (Affiliate Marketer) | S1, S6 | Scrapling (allowed sources only), public-apis, OpenSEO (later) |
| Forge (App Engineer), Plug (Extensions Developer) | S2, S5 | Expo, Playwright, claude-code-setup, codebase-memory MCP (later) |
| Pulse (Market News), Nidhi (Investing Research), Quant (Strategy Research), Guard (Risk Manager) | S3, S7 | public-apis; Perplexity MCP only if paid. **No** MiroFish (SEBI: no tips, paper only) |
| Kalpa (Chief of Staff) | HQ | Grill Me, Find Skills |
| Echo (Knowledge Librarian) | HQ | graphify (cloud, later) |
| Chitti (WhatsApp Assistant), Vani (Voice Agent), Doc (Paperwork & OCR), Ledger (Budget & Finance), Adi (Ads & Copy) | S1, HQ | Nothing new needed now. BotBhai inbox, billing and slots are already built in-house |

## 5. What the CEO must decide or pay for

1. **Sign-ups (Akhil only, free):** PostHog Cloud account; later Cloudflare (Talorys/OpenSEO) and Expo/EAS. Claude never creates accounts.
2. **Paid, optional:** Perplexity API (pay-as-you-go), DataForSEO (OpenSEO), fal.ai / ElevenLabs / Upload-Post (openshorts). Each one is a yes/no. Budget fits inside ₹5,000 only if usage is capped.
3. **GPU check:** run `nvidia-smi` in PowerShell and paste the result, before any local-model plan (see gpu-local-models.md).
4. **Oracle Always Free:** the only free host big enough for Chatwoot or Frappe CRM. It needs a Visa/Mastercard credit card (RuPay and prepaid cards are reported to be declined) ([dev.to report](https://dev.to/ashish-codejourney/getting-a-free-oracle-cloud-vps-from-india-the-full-guide-and-the-rupay-wall-nobody-warns-you-4p5o)). That is a CEO decision. Not needed now.
5. **Unresolved names:** please send full links for **OpenRig (smota)**, **graft**, **harvy** and **task-observer**, and say which "taste-skill" you meant.

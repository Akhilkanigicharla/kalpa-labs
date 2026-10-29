# Reels Akhil sent, 25 Oct 2026: 13 screenshots, 12 projects

**How each was checked (25 Oct):**
- LICENSE file and last commit from a shallow clone of each repo.
- The README read for what the project needs: GPU, paid APIs, a server, or account risk.
- A web search where the repo name wasn't shown in the screenshot.
- Star and like counts come from the screenshots and are unverified.

Deeper write-ups were delegated to the n8n agents: KL Tasks rows "Reel 25 Oct …".

| # | Project (as seen) | Repo | Licence | Last commit | What it really needs | Verdict → world |
|---|---|---|---|---|---|---|
| 1 | HeyGem (AI avatar video) | suifeng9203/HeyGem.ai (fork of duixcom/Duix-Avatar) | **Custom "community" licence**: extra commercial terms once the product passes a monthly-active-user threshold | fork 2025-04-27; upstream 2026-04-21 | GPU, Windows/Docker | **Skip for sold products** (not open source; usage cap). Social Team keeps faceless video (A96 walkthrough, A114) |
| 2 | freehire (IT jobs from company career pages) | strelov1/freehire | MIT | 2026-10-25 | Go + Postgres server; crawls company ATS pages | **Idea → b4 scorecard (A106):** "job hunter" extension for Indian IT job seekers on Workday/Greenhouse/Lever pages they already visit (no crawling by us). Learn from its ATS parsers (MIT) |
| 3 | HyperFrames (HTML → MP4, agent skills) | heygen-com/hyperframes | Apache-2.0 | 2026-10-25 | Node + headless Chrome + ffmpeg; renders locally, free | **Adopt → b1 Social Team (A118):** deterministic explainer and listing videos rendered in GitHub Actions; the skills are already installed in this workspace |
| 4 | Awesome Systematic Trading | wangzhe3224/awesome-systematic-trading | MIT (list) | 2026-10-18 | Reading list | **Adopt as reading → b7 (A119):** pick the backtesting libraries and strategies that fit paper trading; SEBI rule: no tips, paper only |
| 5 | FreeLLMAPI (one API over 34 free LLM tiers) | tashfeenahmed/freellmapi | MIT | 2026-10-24 | Self-hosted router; README says "personal experimentation and learning, not production"; per-provider terms vary | **Learn only → HQ (A120):** add more free providers to our own model fallback list, each with its terms checked. Never for customer bots; no pooled or rotated accounts |
| 6 | Captain JSON (JSON toolkit extension) | Chrome Web Store item, not a repo | — | — | — | **b4 data point:** the dev-tools JSON niche is crowded with free tools → low payment willingness; scored in A106 |
| 7 | Stickman Video Director (faceless YouTube) | kaomei/stickman-video-director | MIT | 2026-10-24 | Free skill, but its image, voice and video steps use paid services (its FAQ says long videos cost money per run) | **Take the style and storyboard ideas, not the paid pipeline → A118:** draw stickman scenes as SVG/HTML in HyperFrames + free TTS (A98) |
| 8 | Coolify ("your own Vercel") | coollabsio/coolify | Apache-2.0 | 2026-10-25 | A server you rent (VPS) | **Skip for now:** Netlify, GitHub Pages and Supabase free tiers cover us; revisit when a paid VPS is justified |
| 9 | Invoice Builder (offline invoicing) | piratuks/invoice-builder | MIT | 2026-10-21 | Electron desktop app (not installed on Akhil's PC, rule 2) | **Learn → b1 (A121):** GST-ready receipts for BotBhai owners after a booking; reuse its tax/discount logic ideas (MIT, credited) |
| 10 | FreeDomain (free .dpdns.org / .us.kg / .qzz.io) | DigitalPlatDev/FreeDomain | AGPL-3.0 (info repo; the service is free) | 2026-08-12 | An account on their dashboard | **Skip for the brand:** free shared-suffix domains look less trustworthy to buyers and some get blocklisted (unverified). Keep kalpa-labs.netlify.app; a real .in domain stays C16 |
| 11 | OpenWA (free WhatsApp API gateway) | rmyndharis/OpenWA | MIT | 2026-10-25 | Its own README: "unofficial… reverse-engineered clients… non-zero risk of account restriction or ban" | **Never (rule 4):** BotBhai uses only the official WhatsApp Cloud API; an unofficial gateway risks the customer's number |
| 12 | Awesome LLM Apps (100+ agent apps) | Shubhamsaboo/awesome-llm-apps | Apache-2.0 | 2026-10-21 | Reference code | **Learn → every world:** the n8n agents read it for patterns (A120 note); nothing copied without a licence check |

**New roadmap items:** A118 (HyperFrames videos), A119 (b7 reading list), A120 (free-model fallback list), A121 (GST receipts). Two ideas were added to A106: the job hunter and the JSON niche data point.

## Added 26 Oct (5 screenshots; HeyGem, freehire and HyperFrames already covered above)
| # | Project | Repo | Licence | Last commit | What it really needs | Verdict → world |
|---|---|---|---|---|---|---|
| 13 | MoneyPrinterTurbo (topic → finished short video) | harry0703/MoneyPrinterTurbo | MIT | 2026-10-25 | Python + ffmpeg; an LLM (our A120 router works, since it accepts OpenAI-compatible endpoints), free Pexels/Pixabay stock-footage API keys, a TTS voice. Its README lists many paid sponsors; we use only the free path | **Adopt → A123:** Kalpa Shorts maker for b1 Social Team, b5 Telugu Deals and the Kalpa YouTube channel. Free path only: our router for the script, Pexels/Pixabay keys (licence to be checked live), Kokoro (Apache-2.0) / Indic Parler-TTS (A98) voice. Not Edge TTS (unofficial Microsoft endpoint) |
| 14 | AI Engineering Hub (75+ AI app tutorials) | patchy631/ai-engineering-hub | MIT | 2026-10-12 | Reference code | **Learn → every world:** added to the n8n pattern task with Awesome LLM Apps (#12); nothing copied without a licence check |

## Added 29 Oct (5 screenshots)
Checked 29 Oct: licence and last commit from a shallow clone; README read for what each needs. Star counts in the reels are unverified.

| # | Project | Repo | Licence | Last commit | What it really needs | Verdict → world |
|---|---|---|---|---|---|---|
| 15 | Postiz (schedule posts to 20+ networks, n8n node, public API) | gitroomhq/postiz-app | **AGPL-3.0** | 2026-10-28 | Self-host: Docker + Postgres + Redis + storage on a VPS (no free host that stays up); Postiz Cloud is paid | **Option for b1 Social Team / Kalpa channels, unmodified only:** if a free always-on host appears, run it as a separate service and post through its n8n node. Never copy its code into a sold product (rule 3). Until then our n8n posting flows stay |
| 16 | Orca (run Codex / Claude Code / OpenCode side by side in worktrees) | stablyai/orca | MIT | 2026-10-29 | Desktop app on a PC | **Skip:** rule 2, nothing installed on Akhil's PC; our sessions already run in the cloud with worktrees |
| 17 | httpSMS (Android phone as an SMS gateway) | NdoleStudio/httpsms | **AGPL-3.0** | 2026-10-28 | An Android phone + their server | **Never for customers (rule 4):** business SMS in India must go through TRAI DLT registration; sending from a personal SIM breaks it and risks the number. Owner alerts stay on WhatsApp/Telegram |
| 18 | Comp AI CRM ("agentic-first": the agent is the product, the CRM is where it keeps notes) | trycompai/crm | MIT | 2026-10-22 | Bun + NestJS + Postgres + an LLM | **Learn → HQ (A125):** copy the pattern, not the stack: the agent *leases* a queue row, spends a fixed research budget, writes findings back, stops when the budget is spent. Apply to the n8n Task Runner + KL Tasks (credit MIT). Later the b1 sales pipeline can use it |
| 19 | News-trading cheat sheet (FOMC / CPI / NFP → rates → currency) | reel infographic, no repo | — | — | — | **Reading → b7 (A119):** add an "event day" filter to paper backtests using India's own calendar (RBI policy, CPI India, US Fed days). SEBI: paper only, no tips |

## Added 30 Oct (6 screenshots; Comp AI CRM and Postiz already above)
| # | Project | Repo | Licence | Last commit | What it really needs | Verdict → world |
|---|---|---|---|---|---|---|
| 20 | gstack (Claude Code as a team: /office-hours, /review, /qa, security, release) | garrytan/gstack | MIT | 2026-10-29 | Claude Code slash commands (Markdown); runs on Claude tokens | **Learn → HQ (A127):** trial only `/office-hours` (product pushback before a build) and `/review` on one A-item; keep only what beats Superpowers. Vendor unmodified with credit, like `00-hq/vendor/superpowers` |
| 21 | Claude SEO (technical SEO, Core Web Vitals, schema, local SEO, AI-search citations) | AgriciDaniel/claude-seo | MIT | 2026-10-22 | Claude Code plugin | **Adopt → HQ + b1 (A126):** audit kalpalabs.dpdns.org once; turn its local-SEO checklist into a "Google profile + reviews" add-on for salons, run by n8n agents (the swarm prices it) |
| 22 | 10 content tools list (OpenCreator, Social Media Research Skills, Local Deep Research, FLUX.2, Kokoro, ACE-Step 1.5, Short Video Factory, AI YouTube Shorts Generator, Podcastfy, Social Media Agent) | various | to check | — | — | **Delegated:** KL Tasks "REEL TOOLS part 1/2" find each repo, licence and a free way to run it; Kokoro (Apache-2.0) is already our TTS pick in A98/A123 |
| 23 | Kids canvas pouches ad (a friend's WhatsApp status) | — | — | — | — | **b1 idea:** home-based WhatsApp/Instagram sellers as a second BotBhai buyer type (order bot + Social Team). KL Tasks row queued. The seller's phone number is not stored |
| 24 | Roast Room (7 AI advisors debate a business decision in Claude Code) | nateherkai/roast-room | MIT | 2026-10-21 | Claude Code skills; we run it on n8n free models instead | **Adopted → every world:** daily council of 7 framework lenses + a chair per world (64 agents in the registry, team `council`), protocol `00-hq/agents/council/ROAST-ROOM.md`, queued 06:00 IST by the Task Runner. Lenses, not impersonations: no real names in anything published |
| 25 | "Claude superpowers for marketing" (brainstorm → plan → researcher/writer/editor/publisher subagents → rubric review → ship; skill files brand-voice, copywriting, seo-audit, social-post, cold-email) | built on obra/superpowers (MIT, already vendored in `00-hq/vendor/superpowers`) | MIT (superpowers) | — | Claude Code skills; we run the word steps on n8n free models | **Adopt the pipeline → HQ marketing (A129):** n8n agents draft the 5 skill files (KL Tasks, 30 Oct); "cold email" becomes a consent-only outreach file (TRAI, WhatsApp opt-in) |
| 26 | free-for-dev (1,300+ services with free tiers for developers) | ripienaar/free-for-dev | no licence file (read and link only, never copy its text) | 2026-10-29 | A list | **Use as the first place to look → every world:** before picking any hosting, email, SMS, monitoring or database service, agents check this list, then verify the provider's own page today (rule 8). KL Tasks row queued to map our needs to the best free options |

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
| 3 | HyperFrames (HTML → MP4, agent skills) | heygen-com/hyperframes | Apache-2.0 | 2026-10-25 | Node + headless Chrome + ffmpeg; renders locally, free | **Adopt → b1 Social Team (A114):** deterministic explainer and listing videos rendered in GitHub Actions; the skills are already installed in this workspace |
| 4 | Awesome Systematic Trading | wangzhe3224/awesome-systematic-trading | MIT (list) | 2026-10-18 | Reading list | **Adopt as reading → b7 (A115):** pick the backtesting libraries and strategies that fit paper trading; SEBI rule: no tips, paper only |
| 5 | FreeLLMAPI (one API over 34 free LLM tiers) | tashfeenahmed/freellmapi | MIT | 2026-10-24 | Self-hosted router; README says "personal experimentation and learning, not production"; per-provider terms vary | **Learn only → HQ (A116):** add more free providers to our own model fallback list, each with its terms checked. Never for customer bots; no pooled or rotated accounts |
| 6 | Captain JSON (JSON toolkit extension) | Chrome Web Store item, not a repo | — | — | — | **b4 data point:** the dev-tools JSON niche is crowded with free tools → low payment willingness; scored in A106 |
| 7 | Stickman Video Director (faceless YouTube) | kaomei/stickman-video-director | MIT | 2026-10-24 | Free skill, but its image, voice and video steps use paid services (its FAQ says long videos cost money per run) | **Take the style and storyboard ideas, not the paid pipeline → A114:** draw stickman scenes as SVG/HTML in HyperFrames + free TTS (A98) |
| 8 | Coolify ("your own Vercel") | coollabsio/coolify | Apache-2.0 | 2026-10-25 | A server you rent (VPS) | **Skip for now:** Netlify, GitHub Pages and Supabase free tiers cover us; revisit when a paid VPS is justified |
| 9 | Invoice Builder (offline invoicing) | piratuks/invoice-builder | MIT | 2026-10-21 | Electron desktop app (not installed on Akhil's PC, rule 2) | **Learn → b1 (A117):** GST-ready receipts for BotBhai owners after a booking; reuse its tax/discount logic ideas (MIT, credited) |
| 10 | FreeDomain (free .dpdns.org / .us.kg / .qzz.io) | DigitalPlatDev/FreeDomain | AGPL-3.0 (info repo; the service is free) | 2026-08-12 | An account on their dashboard | **Skip for the brand:** free shared-suffix domains look less trustworthy to buyers and some get blocklisted (unverified). Keep kalpa-labs.netlify.app; a real .in domain stays C16 |
| 11 | OpenWA (free WhatsApp API gateway) | rmyndharis/OpenWA | MIT | 2026-10-25 | Its own README: "unofficial… reverse-engineered clients… non-zero risk of account restriction or ban" | **Never (rule 4):** BotBhai uses only the official WhatsApp Cloud API; an unofficial gateway risks the customer's number |
| 12 | Awesome LLM Apps (100+ agent apps) | Shubhamsaboo/awesome-llm-apps | Apache-2.0 | 2026-10-21 | Reference code | **Learn → every world:** the n8n agents read it for patterns (A116 note); nothing copied without a licence check |

**New roadmap items:** A114 (HyperFrames videos), A115 (b7 reading list), A116 (free-model fallback list), A117 (GST receipts). Two ideas were added to A106: the job hunter and the JSON niche data point.

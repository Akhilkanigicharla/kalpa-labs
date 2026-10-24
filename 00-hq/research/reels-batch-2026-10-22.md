# Reels and posts Akhil sent, 22 Oct 2026: what we take

Checked 22 Oct 2026: each repo's LICENSE file and last commit from a shallow clone of the repo itself, plus a web search per project. The Instagram and Facebook links could not be opened from this cloud session (the sites refuse automated reading here), so only the screenshots were used. Next time: the built-in browser when the chat is linked to Akhil's PC, or a screen recording through `00-hq/tools/reel/`. Star counts are from the screenshots, unverified.

| Seen in | Project | Licence (checked) | Last commit | Verdict for Kalpa |
|---|---|---|---|---|
| Vishnu.ai reel | cloudflare security-audit skill | MIT | | **Already in** `.claude/skills/security-audit` |
| Sanskar Prajapati reel | wheresryan22/anatomy (isometric SVG illustrations skill) | MIT | 2026-10-18 | **Taken**: vendored to `00-hq/vendor/anatomy` (MIT, 1.6 MB without examples); first use = A81 BotBhai "how a booking works" figure |
| Nivedan Rathi reel | Panniantong/Agent-Reach | MIT | 2026-10-08 | **Skip**: reads X, Reddit, Xiaohongshu etc. through logged-in cookies; breaks rule 4 and AGENT-TOOLS.md |
| Skool post | Cal.com | MIT (now) | 2026-10-19 | **Skip**: BotBhai already books slots with a lock; self-hosting needs a paid server |
| Skool post | Chatwoot | MIT outside `enterprise/` | 2026-10-22 | **Learn, don't run**: BotBhai has its own shared inbox; Chatwoot needs Rails + Postgres + Redis hosting |
| Skool post | Tencent/WeKnora (RAG) | MIT + third-party parts | 2026-10-22 | **Skip**: too heavy for a salon FAQ |
| Skool post | every-app/open-seo | MIT | 2026-10-19 | **Check later for b5 Deals**: unverified whether it needs a paid data API |
| Skool post | OpenWhispr (dictation) | MIT | 2026-10-22 | **CEO option C45**: free offline voice typing for Akhil's PC (his choice; Claude installs nothing). Uses whisper.cpp / Parakeet locally; cloud and sign-in parts not needed |
| Skool post | CapSoftware/Cap | AGPL-3.0 (most) | 2026-10-22 | **Never copy** (rule 3) |
| Skool post | opf/openproject | GPL-3.0 | 2026-10-22 | **Never copy**; we use ROADMAP.md + tasks.js |
| lobehub.com | lobehub/lobehub | LobeHub Community License (Apache-2.0 + a commercial licence for derivative works) | 2026-10-22 | **Skip**: we run agents on n8n; can't build a sold product on it without their licence |
| Taskmaster reel | eyaltoledano/claude-task-master | MIT + Commons Clause (not open source) | 2026-04-23 | **Skip**: our `tasks.js` does this |
| Dr. cintas reel | GLM-5.3 Flash EXL3 (DGX Spark) | AGPL-3.0 (screenshot) | | **Skip**: needs DGX hardware; AGPL |
| Grok "business analyst" reel | idea, not code | | | **Taken**: A80 owner nudges in BotBhai's 9 PM message (rules, no AI, no cost) |
| Earlier reels | Superpowers, I-have-ADHD, ECC, launch-your-agent, Ponytail, Pipecat, 20 vibecoded tells | | | **Already in** (see 00-hq/vendor, CLAUDE.md, vibecheck) |
| LinkedIn post | DevOps interview questions | | | Not for Kalpa now |
| GitHub Projects reel (24 Oct) | makecindy/cindy ("Cindy" desktop AI agent) | Apache-2.0 | 2026-10-24 | **Skip**: a desktop app installed on your PC (rule 2) that drives your logged-in browser, computer and phone (rule 12); it runs Claude Code / Codex with your own keys or plans, or local models that need a strong PC. We already get the same in the cloud: Claude sessions for code + n8n free models for words, with nothing on your PC |
| restructureai reel (24 Oct) | "41-agent AI social media team for real estate" (Claude + ElevenLabs + Higgsfield + Slack + Twilio, closed product) | n/a | | **Ideas taken, tools not**: those tools are paid. We already have the Social Team (plan → copy → design → approve → publish). New: A96 listing photos → walkthrough Reel (free, ffmpeg) and A97 best posting time per channel learned from real views |
| buildwithai.club reel (24 Oct) | Jakeschincariol/youtube-agent-skill (11 Claude skills: plan, script, shorts, SEO, chapters, retention…) | MIT | 2026-09-16 | **Taken as reading material**: vendored to `00-hq/vendor/youtube-agent` (no API key, does not publish). For our own YouTube/workshop content (A62, A64) |

## Security note
One screenshot (github.com/settings/security) shows **two-factor authentication not enabled** on Akhil's GitHub account. If it is older than the "2FA done" message of 20 Oct, ignore it; otherwise enable it (CEO queue).

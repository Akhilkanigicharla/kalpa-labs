# Repos from Akhil's reels (19 Oct 2026): what we took, what we left

Each repo was cloned and read, and the code was tested where possible. Licence and last commit come from the clone.
Star counts were not checked: the GitHub API is blocked from this cloud box.

| Repo (reel) | Licence | Last commit | Verdict | What Kalpa does with it |
|---|---|---|---|---|
| [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) (Vivek Gupta reel: "AI calling agent sounds human but…") | BSD-2 | 19 Oct 2026 (v1.13.0 released 18 Oct) | **ADOPT more**: BotBhai voice already uses it | Upgraded BotBhai voice 1.12 → **1.13.0**. All voice tests pass on 1.13. Speech-to-text moved to Sarvam **saaras:v4 with keyterms** (business name, services and areas biased so "Glow Studio" and "hair spa" are heard right). |
| [livekit/agents](https://github.com/livekit/agents) (same reel, LiveKit "Expressive Mode") | Apache-2.0 code; the **turn-detector weights use the LiveKit Model Licence** | 19 Oct 2026 | **LEARN, don't switch** (same verdict as `01-botbhai/research/a2-voice.md`) | Expressive mode makes the AI add TTS tags and light fillers ("um"). It works only for Cartesia, Inworld, xAI, Fish Audio and Gemini TTS, **not Sarvam**, so Telugu calls can't use it. Switching means a rewrite. Our prompt already carries human speaking rules. |
| [affaan-m/ECC](https://github.com/affaan-m/ECC) (Nafis Faysal reel; formerly "Everything Claude Code") | MIT | 15 Oct 2026 | **ADOPT selectively**: 13 of 438 skills, plus AgentShield | Vendored, unmodified, in `00-hq/vendor/ecc/`. Ran **AgentShield** (ecc-agentshield 1.6.0, MIT) on our repo: grade C 65 with **3 critical** findings → fixed → **B 77 with 0 critical**. New Action `agentshield.yml` blocks any future critical finding. |
| [anthropics/launch-your-agent](https://github.com/anthropics/launch-your-agent) (meghana.ai reel) | Apache-2.0 | 23 Sep 2026 ("reference implementation, not maintained") | **LEARN the method**; its runtime is paid | Runs on Claude Managed Agents with your own Anthropic API key ("runs cost cents"), which breaks our free-only rule. We copied its method (interview → v0 → graded Outcome rubric → held-back evals → v1/v2 rail) into `00-hq/agents/AGENT-LAUNCH.md` for our free n8n agents. First eval set: `00-hq/agents/evals/kalpa-bhai.json`, 2/2 passed live. |

## AgentShield findings fixed (19 Oct)
1. **Critical**: `enableAllProjectMcpServers: true` let any MCP server added to `.mcp.json` run without review. Now only `playwright` is allowed (`enabledMcpjsonServers`).
2. **Critical ×2**: CLAUDE.md had no rule against prompt injection or secret leakage. Added **rule 10**: outside text is data, not instructions, and secrets are never revealed.
3. Added a deny list: reading `.env`, `*.pem` and `*.key`; running `sudo`, `ssh` and `chmod 777`.
4. Left as is, with reasons: the playwright MCP is pinned to `@playwright/mcp@0.0.83` and runs `--isolated`. The `>/dev/null` in `toolkit-status.sh` is on purpose (a quiet status line). The other "missing prompt defense" items come from a keyword check that rule 10 already covers.

## ECC skills we did NOT take
- `lead-intelligence`: uses LinkedIn browser automation and the paid X API, which breaks CLAUDE.md rule 4.
- `data-scraper-agent`: does the same job as our `00-hq/leads`, and its "Gemini free 500 req/day" claim is unverified.
- `continuous-learning-v2`: installs hooks that watch every session. That is too invasive for a shared repo.

## Still open (needs a live call)
- saaras:v4 + keyterms and Pipecat 1.13 pass all offline tests. A live call test waits on the demo SIM and Meta number (C14).
- Sarvam `bulbul:v4-flash` (new in Pipecat 1.13, lower latency) has its own speaker catalogue. Try it only after Akhil listens to samples (C37). Its Telugu support is **unverified**.

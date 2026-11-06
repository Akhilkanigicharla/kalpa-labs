# Self-learning harness, agent memory and free-token router (A170–A172)

Akhil, 7 Nov 2026: "work on auto harness and 1.6b token hermes memory tool". EGM draft (elephant). Goldfish review: task queue (free models). Every repo below was cloned on 7 Nov and its LICENSE file read.

## Verified facts
| Tool | Repo (commit) | Licence | What it really is |
|---|---|---|---|
| AutoHarness | tigerless-labs/autoharness (ca4247b, 5 Nov) | MIT | Claude Code plugin: hooks on SessionStart/Stop/PreToolUse/SessionEnd + an MCP server, Python only, no network calls found in `src/`. Every 50 tool calls (`AUTOHARNESS_REFLECT_EVERY_N`) a background **Haiku** session reflects and writes "self-authored" skills into `.claude/skills/`; it never edits hand-written skills; unused skills are pruned. The "42% → 78% CORE-Bench" headline is from the HAL paper about harnesses in general, **not** a measurement of AutoHarness (README + towardsai review). |
| OmniRoute | diegosouzapw/OmniRoute (120403bb, 6 Nov) | MIT | OpenAI-compatible gateway, 380 providers, token compression (RTK + Caveman). Its own README says **~1.62B free tokens per month**, not per day as the video said. npm package is ~915 MB unpacked, Node ≥22. Part of that budget comes from routes that reuse IDE subscriptions (Kiro, Antigravity, Qoder) and "TLS stealth"; those likely break the providers' terms. |
| Mnemosyne | mnemosyne-oss/mnemosyne (ead261c, 6 Nov) | MIT | Agent memory in one SQLite file, Python ≥3.10, MCP or SDK (`remember`/`recall`), local-first. |
| Hindsight | vectorize-io/hindsight | MIT | Memory server (Docker/pip) with local embeddings; needs a running server and a 64K-context model. |
| Hermes Agent | NousResearch/hermes-agent | MIT | Agent framework; memory is pluggable (Mnemosyne, Hindsight). |

## Design (smallest complete version)
**A170 AutoHarness for Kalpa Claude sessions.**
1. CI first: a GitHub Action runs AutoHarness's own test suite at the pinned commit (external code is never run inside Claude's session container).
2. If green, enable it for this repo only via `.claude/settings.json` (`extraKnownMarketplaces` + `enabledPlugins`), with `AUTOHARNESS_REFLECT_EVERY_N=150` to keep the extra Haiku cost low.
3. Learned skills land in `.claude/skills/` and are committed, so every session (and lane) shares them. A weekly goldfish review reads new self-authored skills; any skill that conflicts with CLAUDE.md rules is deleted.
4. Off switch: remove the two settings lines.

**A171 Memory for the free-model agents (Mnemosyne).** The GitHub agents runner (`00-hq/agents/runner.py`) gets a memory: before a task it recalls up to 5 lessons for that world (past Vigil fixes, Akhil decisions); after Vigil it stores the lesson. One SQLite file per world in `00-hq/agents/memory/`, committed. No customer personal data ever goes in (same rule as the prompts). Claude's own memory is unchanged. Hindsight and the full Hermes Agent are not needed: they add a server and a 64K model for no gain at our size.

**A172 OmniRoute as the free-token router.** Run it inside the GitHub Actions agent job (cached install), pointed at **official free tiers only** (Groq, OpenRouter `:free`, Gemini, plus any new ones that pass the audit: provider page + second source, recurring, no card). Kiro/Antigravity/Qoder/stealth routes stay off. Use its compression to stretch the free quota. Measure real tokens per day for a week before claiming any number. Replaces FreeLLMAPI only if it beats it on that measure.

## Akhil-only steps
None for A170/A171. A172 may need new free API keys that Akhil creates himself (each one audited first).

## Open questions for goldfish
- Does a self-learning skill layer risk overriding hard rules? (Mitigation: self-authored only, CLAUDE.md wins, weekly review.)
- Is committing SQLite memory files to git safe and small enough?

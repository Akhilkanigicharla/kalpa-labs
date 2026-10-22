# Agent tooling verdicts (A77, lane E, 22 Oct 2026)

Akhil's 7 add-on questions, checked today. Each repo fact comes from two sources: the GitHub page fetched today (Firecrawl, live) and a shallow `git clone` read today (LICENSE file + last commit). Star counts are GitHub's rounded figures on 22 Oct 2026. Policy that follows from this: `00-hq/AGENT-TOOLS.md`.

## Repos checked

| Repo | What it is | Stars | Licence | Last commit | Anthropic-authored? |
|---|---|---|---|---|---|
| [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) | Curated reading list: context, tools, permissions, memory, evals | 4.9k | CC0-1.0 | 2026-10-22 (`dfc24cd`) | No |
| [walkinglabs/awesome-harness-engineering](https://github.com/walkinglabs/awesome-harness-engineering) | Second list with the same name: guides, benchmarks, runtimes | 4.5k | CC0-1.0 | 2026-08-19 (`cff9b00`) | No |
| [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills) | 818 security skills incl. offensive red-team ones | 34.8k | Apache-2.0 | 2026-08-31 (`54a7988`) | **No.** Its README says "Community Project ... Not affiliated with Anthropic PBC"; owner is a personal account |
| [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) `plugins/claude-security` | Anthropic's in-session vulnerability scan + patch plugin, v0.12.0 | (marketplace repo) | **Proprietary**: "Copyright (c) 2026 Anthropic, PBC. All rights reserved", no redistribution | 2026-10-21 (`af59ee3`) | Yes (plugin.json author "Anthropic") |
| same repo, `plugins/security-guidance` | Hooks: regex warnings on edits + LLM diff review on every Stop and commit, v2.0.16 | (marketplace repo) | Apache-2.0 | 2026-10-21 (`af59ee3`) | Yes (author dworken@anthropic.com) |
| [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review) | GitHub Action for PR security review | 6.5k | MIT (c) 2025 Anthropic | 2026-02-11 (`0c6a49f`) | Yes, but needs a paid `claude-api-key` secret |
| [volcengine/OpenViking](https://github.com/volcengine/OpenViking) | Context database for agents, `viking://` filesystem, L0/L1/L2 summaries | 40.6k | **AGPL-3.0** | 2026-10-22 (`824e9c7`) | No (ByteDance/Volcengine) |
| [anthropics/skills](https://github.com/anthropics/skills) | Anthropic's public skills | - | per skill | 2026-10-09 (`dbd4588`) | Yes; **no security skill** in its 19 skills |

Also confirmed today on Anthropic's own docs (`code.claude.com/docs/en/commands.md`): Claude Code ships a built-in `/security-review` command that reviews the branch diff. Second source: the claude-code-security-review README section "Claude Code Integration: /security-review Command".

## Verdict table

| # | Add-on | Verdict | Reason | Token cost | Risk |
|---|---|---|---|---|---|
| 1 | Browser use (Playwright MCP, Claude in Chrome) | **Limited**: own UI (localhost, previews, private URLs) and docs only; scripts over snapshots | Needed to check our own screens; nothing else justifies it | High: page snapshots are large (Akhil's estimate "thousands of tokens each"; not measured here) | High: page text is the main prompt-injection path; a logged-in browser exposes accounts. Playwright runs `--headless --isolated`; Claude in Chrome denied |
| 2 | Third-party agent memory (mem0, Zep, Letta, etc.) | **Skip** | Repeats CLAUDE.md + auto-memory + git log | Per-turn tax: recalled memories are added to every turn | Persistence vector: a poisoned entry keeps steering later sessions |
| 3 | Scientific agent skills | **Skip** | No world needs them | Skill descriptions load every session | Low, but pure clutter |
| 4 | Diagram skill (text to Mermaid/SVG) | **Keep**: our own `.claude/skills/diagrams/` | Clear architecture docs for Akhil | Low: a short skill, text output | Low: no network, no install |
| 5 | Security skills | **Adopt defensively, no new vendoring** | Existing `security-audit` (Cloudflare, MIT, vendored 18 Oct) + built-in `/security-review` cover diff review and threat models | Medium: only when run | Low if aimed at our own code. "Anthropic-Cybersecurity-Skills" is not by Anthropic and ships offensive skills: skip. `claude-security` is by Anthropic but proprietary: may be installed from the official marketplace for internal use, never copied into the repo. `security-guidance` is Apache-2.0 but is a hooks plugin that runs an LLM review on every Stop (constant token cost), so not enabled |
| 6 | Awesome harness engineering | **Read, don't install** | CC0 reading list; ideas below | None (read once) | None |
| 7 | OpenViking | **Skip** | Needs its own server, an embedding model and a VLM provider; AGPL-3.0 (rule 3 blocks copying into products); its L0/L1/L2 "summary before source" idea we already have as README label cards, PLAN.md and ROADMAP | High to run (embeddings + VLM per resource) | Medium: another stateful store that agents trust |

## Vendored or skipped
- **Vendored: nothing.** The only Anthropic-authored security *skill* (`claude-security`) is proprietary, so it can't be copied here. The Apache-2.0 Anthropic plugin (`security-guidance`) is hooks + Python, not a skill, and would add a per-turn LLM review. The Apache-2.0 "Anthropic-Cybersecurity-Skills" is not Anthropic's.

## 10 harness-engineering ideas we apply

From the ai-boost list (read today). Claims about outside papers are as the list summarises them; we did not re-check each paper (unverified).

1. **Every agent mistake becomes a harness fix**, not a longer prompt (Hashimoto, the essay the list credits with the term). For us: a roadmap check or a test, like `tooling.test.mjs`.
2. **Prose rules are not controls.** Anthropic's memory docs say CLAUDE.md is "context, not enforced configuration". A paper in the list found only about 4% of security rules in 481 public CLAUDE.md files had a matching built-in control (unverified). So our risky rules get a deny rule or a test.
3. **Keep CLAUDE.md short.** Anthropic's docs: under 200 lines, "longer files consume more context and reduce adherence". We cap at 60 lines and link out.
4. **Summary before source** (progressive disclosure: OpenViking's L0/L1/L2, Trellis). Our version: world `README.md` label card, then `PLAN.md`, then code.
5. **Tool output is the biggest token sink.** Tools in the list (context-mode, headroom) exist only to shrink snapshots and logs. For us: Playwright scripts that print pass/fail, `curl …/page.md` for docs.
6. **Stable prefix, cheaper turns.** Prompt caching rewards a CLAUDE.md that rarely changes; add rules rarely and keep them one line.
7. **Least privilege beats approval prompts.** OWASP LLM06 "excessive agency"; Anthropic's auto-mode post says people approve almost every prompt, so prompts stop protecting. For us: deny lists, isolated browser, "go" only for named things.
8. **Compaction can drop rules** (the list's "governance decay" paper, unverified). Hard rules live in files that are re-read and in tests, never only in chat.
9. **Verification inside the loop, not after.** Evals and CI gates per change (Anthropic "Demystifying evals"). Ours: each roadmap item names its check; `quality.yml` runs on every push.
10. **Memory needs evidence.** Memory systems in the list that work keep each fact tied to versioned evidence. Ours: the daily log + commit hash per tick; auto-memory is data, never orders.

## Not verified
- Exact token size of a Playwright MCP snapshot (Akhil's figure; not measured in this session).
- Paper figures quoted via the reading list (ideas 2 and 8).
- Mermaid render of `00-hq/design/architecture.md` was checked by eye only (no Mermaid CLI run); GitHub renders it on view.

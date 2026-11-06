# Elephant-Goldfish Model (EGM), vendored unmodified

- Source: https://github.com/google/elephant-goldfish-model at commit 6a8001e (5 Nov 2026), Apache-2.0 (see LICENSE). Copied: skills, agents, resources, adapters, plugin manifests. Left out: site, docs, tests.
- Shared by Akhil, 7 Nov 2026 (Julian Goldie video "Google's FREE Elephant Goldfish AI Agents").
- What it does: the "elephant" (the session with full context) drafts a spec; "goldfish" reviewers (fresh sub-agents with no chat history) review only the written draft, which exposes hidden assumptions.
- Kalpa use: for any roadmap item that needs design decisions before code (new product, payments, bots), run `egm-draft` → `egm-review` before `writing-plans`. Small fixes skip it.
- If the plugin isn't loaded, read `00-hq/vendor/egm/skills/<name>/SKILL.md` directly.

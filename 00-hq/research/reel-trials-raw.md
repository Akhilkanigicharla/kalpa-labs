# Reel trials (raw) · 2026-11-13T12:45:53Z · commit 2d2e4fc

Tokens ≈ characters ÷ 4. Times are wall-clock seconds on one GitHub runner.
## 1. claude-mem 0c488b5 / npm 15.18.3 vs Graft 0.10.1
- licence:  Apache License Version 2.0, January 2004 http://www.apache.; src files reading a model key: 25
- claude-mem@15.18.3 install exit 0, 22.10 s, node_modules 83 MB, ~45 packages
- @nanonets/graft@0.10.1 install exit 0, 3.78 s, node_modules 156 MB, ~40 packages
- claude-mem --help exit 0:  claude-mem v15.18.3 — your coding agent remembers between sessions  Install Commands (no Bun required):   npx claude-mem                     Interactive install   npx claude-mem install              Interactive install (also puts the claude-mem hook launcher on PATH)   Installing for a user who i
- what a session reads today as memory: HANDOFF.md 3658 tokens, newest log 3833 tokens
## 2. ECC d2ef268 vs Superpowers (vendored)
- licence: MIT License Copyright (c) 2026 Affaan Mustafa Permission is ; full ECC: 1068 skills, all SKILL.md 2475086 tokens, description lines 67146 tokens; agents 71, commands 98, hooks files 9
- our vendored ECC subset: 13 skills, all SKILL.md 23521 tokens, description lines 1053 tokens
- Superpowers (in use): 15 skills, all SKILL.md 42531 tokens, description lines 849 tokens
## 3. Worktrunk v0.81.0 vs plain git worktree (TEAM.md lanes use separate cloud sessions)
- binary: /tmp/wtbin/worktrunk-x86_64-unknown-linux-musl/wt, wt v0.81.0
- git worktree add x3: 0.71 s, 4 worktrees
- wt switch --create x3: 3/3 ok, 0.99 s; wt list lines 8; first output: ✓ Created branch w1 from main and worktree @ /tmp/repo.w1 ↳ To customize worktree locations, run wt config create 
## 4. Agent Reach c70ae6d (public no-login channels) vs plain fetch
- licence: MIT License Copyright (c) 2025 Agent Eyes Permission is here; channel files 16, of which need a login/session 11
- pip install exit 0, 6.47 s, venv 66 MB
- doctor exit 0, 1 lines
- read https://example.com: agent-reach exit 0, 0.50 s, 125 tokens (goes via r.jina.ai) · curl+strip 0.05 s, 84 tokens
- read https://www.rfc-editor.org/rfc/rfc2606.html: agent-reach exit 0, 1.90 s, 2449 tokens (goes via r.jina.ai) · curl+strip 0.10 s, 1786 tokens

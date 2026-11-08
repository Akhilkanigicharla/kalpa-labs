# Token-saver trial (raw) · 2026-11-08T19:58:12Z · commit 9ad1e00

Tokens ≈ characters ÷ 4 of what an agent would read. Lower is better.

## Baseline: grep -rn (what a session does today)
| Question | grep tokens |
|---|---|
| inbox reply send | 14646 |
| billing void invoice | 11781 |
| agents runner free model call | 86789 |
| tap sweep 44 px | 39736 |
| seo check canonical | 50200 |
## codebase-memory-mcp latest (MIT): 0.12.1
- index exit 0, 4.713145673 s; output: warning: passing raw JSON to 'cli index_repository' is deprecated and will be removed in a future release; use flags (run 'cli index_repository --help'), --args-file <path>, or piped stdin. {"project":"tmp-repo","excluded":{"dirs":[".claude","07-trading/reports","00-hq/vendor","00-hq/site/.netlify",
| Question | tokens |
|---|---|
| inbox reply send | 94 |
| billing void invoice | 94 |
| agents runner free model call | 94 |
| tap sweep 44 px | 94 |
| seo check canonical | 94 |
- get_architecture: 96 tokens
## Graft @nanonets/graft 0.10.1 (MIT)
- build exit 0, 6.599118917 s, map folder 12696 KB; output: 381 file, 219 method, 77 class, 60 type, 23 interface), 5133 edges, 381 cards [javascript, python, tsx, typescript]   parsed: 381 of 381 files (0 replayed from cache)   → /tmp/repo/graft   graft/ is git-ignored (added automatically) — a local cache; teammates run `graft build` to get their own. 
| Question | tokens |
|---|---|
| inbox reply send | 2398 |
| billing void invoice | 1296 |
| agents runner free model call | 3019 |
| tap sweep 44 px | 2115 |
| seo check canonical | 649 |

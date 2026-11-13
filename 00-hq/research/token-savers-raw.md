# Token-saver trial (raw) · 2026-11-09T00:46:21Z · commit 91040da

Tokens ≈ characters ÷ 4 of what an agent would read. Lower is better.

## Baseline: grep -rn (what a session does today)
| Question | grep tokens |
|---|---|
| inbox reply send | 14685 |
| billing void invoice | 11822 |
| agents runner free model call | 87892 |
| tap sweep 44 px | 40996 |
| seo check canonical | 50485 |
## codebase-memory-mcp latest (MIT): 0.12.1
- index exit 0, 3.817182354 s; output: warning: passing raw JSON to 'cli index_repository' is deprecated and will be removed in a future release; use flags (run 'cli index_repository --help'), --args-file <path>, or piped stdin. {"project":"tmp-repo","excluded":{"dirs":[".claude","07-trading/reports","00-hq/vendor","00-hq/site/.netlify",
| Question | tokens |
|---|---|
| inbox reply send | 94 |
| billing void invoice | 94 |
| agents runner free model call | 94 |
| tap sweep 44 px | 94 |
| seo check canonical | 94 |
- get_architecture: 96 tokens
## Graft @nanonets/graft 0.10.1 (MIT)
- build exit 0, 4.865759631 s, map folder 12932 KB; output: 386 file, 238 method, 82 class, 60 type, 23 interface), 5270 edges, 386 cards [javascript, python, tsx, typescript]   parsed: 386 of 386 files (0 replayed from cache)   → /tmp/repo/graft   graft/ is git-ignored (added automatically) — a local cache; teammates run `graft build` to get their own. 
| Question | tokens |
|---|---|
| inbox reply send | 2398 |
| billing void invoice | 1296 |
| agents runner free model call | 3501 |
| tap sweep 44 px | 2286 |
| seo check canonical | 649 |

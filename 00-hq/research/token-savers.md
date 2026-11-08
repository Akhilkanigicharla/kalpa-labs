# Token savers: result (A200, 9 Nov 2026)

Trial: `.github/workflows/token-savers.yml` on a copy of the repo in GitHub Actions (Akhil said yes, 9 Nov). Raw numbers: `token-savers-raw.md`.

| Question (what a sprint looks up) | plain `grep -rn` | Graft 0.10.1 `graft grep` |
|---|---|---|
| inbox reply send | ~14,600 | ~2,400 |
| billing void invoice | ~11,700 | ~1,300 |
| agents runner free model call | ~86,700 | ~3,000 |
| tap sweep 44 px | ~39,700 | ~2,100 |
| seo check canonical | ~50,200 | ~650 |

Tokens ≈ characters ÷ 4. Graft built the map of 381 files in 3.6 s with no API key; its `graft/` folder is git-ignored.

**Honest limits:** the grep column is a blunt full search; a careful session greps narrower, so the real saving per sprint is smaller than these 80–98% figures. codebase-memory-mcp 0.12.1 indexed in 4.7 s, but our query calls returned only a ~94-token reply (wrong call format), so it is **not measured yet**; pinned 0.10.7 had a missing release file.

**Decision (Akhil said "yes CLAUDE graft", 9 Nov 01:33):** adopted: make Graft the first code lookup in build sprints, fail-soft, by adding one line to CLAUDE.md step 2. Changing the instructions every session follows needs Akhil's explicit yes (the safety check stopped Claude from editing CLAUDE.md on its own). Keep it only if the next 7 days of `00-hq/log/tokens.csv` show build sprints using at least 30% fewer tokens than the 7 days before.

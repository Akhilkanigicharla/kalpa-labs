# A300 · Karpathy coding rules vs CLAUDE.md + Ponytail (27 Nov 2026)

Source: github.com/forrestchang/andrej-karpathy-skills, commit `2c60614` (20 Apr 2026), cloned 27 Nov 2026.
Licence: MIT, as stated in `README.md` ("## License / MIT"), `.claude-plugin/plugin.json` and the skill's frontmatter. **There is no LICENSE file** (so no copyright line to carry). We copy no text: the two added lines in CLAUDE.md are our own words, with attribution.

| Their rule | Already in our rules | Gap | Action |
|---|---|---|---|
| 1 Think before coding: state assumptions, name other readings, push back, stop when unclear | Rule 0 (never pick or narrow a product without Akhil's yes); Ponytail "Before you write" (read the task, list scope); Ponytail ultra (push back) | Scheduled runs are unattended, so "ask" becomes: write assumptions and the other readings down instead of picking silently | **Added** a line to CLAUDE.md build procedure: write assumptions + other readings in the log (and the CEO queue if it changes the product) |
| 2 Simplicity first: no extra features, no single-use abstractions, no config nobody asked for | Ponytail "The smallest complete change" (all of it, stricter) | none | none |
| 3 Surgical changes: don't tidy nearby code or formatting, match house style, mention unrelated dead code instead of deleting it, remove only orphans your change made | Ponytail "keep the structure the codebase already has"; TEAM.md rule 3 (small line edits in shared files) | Not tidying nearby code/formatting, mentioning (not deleting) old dead code, cleaning your own orphans | **Added** to CLAUDE.md build procedure |
| 4 Goal-driven: turn the task into a check, loop until it passes, short plan with a check per step | Rule 5 (tests before ticks), TDD + `writing-plans` + `verification-before-completion`, ROADMAP "Check:" per item | none | none |

Result: 2 of 4 rules had gaps; both added to CLAUDE.md ("Karpathy rules" line). Nothing vendored.

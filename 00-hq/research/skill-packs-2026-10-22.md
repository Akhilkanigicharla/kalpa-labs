# The 10 "AI skills" Akhil sent, 22 Oct 2026: what they really are and what we take

The text Akhil pasted describes these as abstract abilities. They are actually **GitHub skill packs** for coding agents (folders with a SKILL.md). Two descriptions in that text are wrong: "Ponytail" is the opposite of a perfectionist (it makes the agent write the *least* code), and "Graphifi" is Graphify, a code map tool, not GraphRAG in general. Each repo below was shallow-cloned today to read its LICENSE and last commit.

| Name in the list | Real repo | Licence (checked) | Last commit | Verdict |
|---|---|---|---|---|
| Agent Skills | agentskills/agentskills (the SKILL.md standard) | Apache-2.0 | 2026-08-09 | **Already used**: our skills follow this format |
| Anthropic Skills | anthropics/skills | Per skill: frontend-design, skill-creator Apache-2.0; docx/pdf/pptx/xlsx "All rights reserved" | 2026-10-09 | **Already available** in our sessions; never copy the proprietary ones |
| Karpathy Skills | forrestchang/andrej-karpathy-skills (one CLAUDE.md) | **No licence file** (cannot copy) | 2026-04-20 | **Ideas only**, already covered: ask when unsure (CLAUDE.md rule 8, grilling), smallest change (Ponytail), don't touch unrelated code |
| Matt Pocock Skills | mattpocock/skills | MIT | 2026-10-19 | **Already in** (`grill-me`, `grilling`) |
| Taste Skill | Leonxlnx/taste-skill | MIT | 2026-10-20 | **Skip**: brings its own fonts and looks; our rule 6 says Kalpavruksha only. `emil-design-eng` + vibecheck already cover taste |
| UI UX Pro Max | nextlevelbuilder/ui-ux-pro-max-skill | MIT | 2026-10-22 | **Skip**: a big database of palettes and fonts (rule 6); 696 files |
| Graphifi | safishamsi/graphify (`graphifyy` on PyPI) | Apache-2.0 | 2026-10-21 | **Taken (A82)**: local code map, tried on our repo (489 files, 14 s); answers "who calls X" in ~1 KB. Code-only, no hooks, no cloud |
| Caveman | JuliusBrussee/caveman | Apache-2.0 | 2026-10-17 | **Trial first (A83)**: claims 33% fewer input tokens (its own benchmark, unverified). Installs hooks and a terse voice; replies to Akhil must stay plain English |
| Ponytail | DietrichGebert/ponytail | MIT | | **Already in** (CLAUDE.md build sprint) |
| Superpowers | obra/superpowers | MIT | | **Already in** (00-hq/vendor/superpowers) |

Note: "prefilling Claude's responses" in the pasted text is an API technique that newer Claude models do not all support; we don't rely on it.

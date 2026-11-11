# Third-party skills in .claude/skills

Copied unmodified on 18 Oct 2026 with `npx skills add … --copy` (telemetry off), reviewed before commit: no network code, no hooks, no hidden instructions. Exact versions are pinned by hash in `/skills-lock.json`; restore with `npx skills experimental_install`. CEO approval: "approveskills", 18 Oct 2026 02:35 IST.

| Skill folder | Source | Licence |
|---|---|---|
| grill-me, grilling | https://github.com/mattpocock/skills | MIT, (c) 2026 Matt Pocock |
| security-audit | https://github.com/cloudflare/security-audit-skill | MIT, (c) 2025-2026 Cloudflare, Inc. |
| hallmark | https://github.com/Nutlope/hallmark (commit `4f6a46c`, copied 31 Oct 2026; theme pictures `*.jpg` and `photos.json` left out for size) | MIT, (c) 2026 Hallmark contributors |
| humanizer | https://github.com/blader/humanizer (commit `0ef9fe5`, SKILL.md + LICENSE copied unmodified 4 Nov 2026) | MIT, (c) 2025 Siqi Chen |
| first-customer-finder | https://github.com/Kappaemme-git/codex-first-customer-finder-skill (commit `d3f6964`, folder copied unmodified 6 Nov 2026) | MIT, (c) 2026 Francesco Mistero |
| line-art-animation | https://github.com/JDhruv14/line-art-animation (commit `c43d698`, 10 Nov 2026; copied unmodified 11 Nov 2026 without `media/` demo files, 7 MB) | MIT, (c) 2026 JDhruv14 |
| video-watch (skill name `watch`) | https://github.com/bradautomates/claude-video (commit `03ceb42`, skills/watch copied 6 Nov 2026; one Kalpa section added to SKILL.md on 11 Nov 2026, "Agent-Reach first", rest unmodified) | MIT, (c) 2026 Bradley Bonanno |
| Agent-Reach CLI (not copied; used by `00-hq/agents/reach.py` and video-watch) | https://github.com/Panniantong/Agent-Reach release `v1.6.1`, `agent-reach.zip` sha256 `51443d733bcb26064262442083a8f8abf6ba5e3e7df54beebafe98c88be04a60`; repo main last commit 2026-11-08 (reviewed 11 Nov 2026). Installed only in CI, in its own venv with `--no-deps` + pinned requests/loguru/PyYAML/yt-dlp (Unlicense)/yt-dlp-ejs, so yt-dlp's GPL extra `mutagen` is never installed. The PyPI package named `agent-reach` is a different project: never install it by name. | MIT, (c) 2025 Agent Eyes |
| animate, animate-expo, break-ui, emil-design-eng, mobile-native, pick-ui-library, prototype, review-animations | https://github.com/emilkowalski/skills | MIT, (c) 2026 Emil Kowalski |

Plugin (not copied, loaded by Claude Code): HyperFrames `hyperframes@hyperframes`, https://github.com/heygen-com/hyperframes, Apache-2.0, pinned to tag `v0.8.169` in `.claude/settings.json`. Skills only, no hooks or MCP servers. When a skill says `npx hyperframes@latest`, use `npx hyperframes@0.8.169` instead.

Our own skills (not third-party): `short-answers` (adapted, see its header) and `diagrams` (A77, written 22 Oct 2026). No Anthropic security skill was vendored on 22 Oct 2026: the only one, `claude-security`, is proprietary; see `00-hq/research/agent-tooling-2026-10-22.md`.

Kalpa rules still win: line-art-animation must use Kalpavruksha paper/ink colours from `00-hq/design/tokens.css` instead of its own palette, and its `references/matching.md` X-video download tip is not used (no scraping). Design skills must use the Kalpavruksha system in `00-hq/design/` (CLAUDE.md rule 6); security-audit runs only on our own code.

---

## LICENSE: mattpocock/skills

```
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## LICENSE: cloudflare/security-audit-skill

```
MIT License

Copyright (c) 2025-2026 Cloudflare, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## LICENSE: emilkowalski/skills

```
MIT License

Copyright (c) 2026 Emil Kowalski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Hallmark (31 Oct 2026): our design system is locked, so Hallmark must treat `00-hq/design/DESIGN-SYSTEM.md` + `tokens.css` as the locked `DESIGN.md` and never pick one of its own themes or palettes. Do not run `install-hook.mjs` and do not set `TOGETHER_API_KEY` (paid image API). Its `sloplint.mjs` runs only after Akhil approves running it (external code), in Actions or a Codespace.

first-customer-finder (6 Nov 2026): public demand signals only; no private groups, data brokers or scraped contact lists (its own rule, same as our rule 4). It never sends outreach; Akhil sends every message himself.
video-watch (6 Nov 2026): use it only on video FILES Akhil attaches (screen recordings, his own clips). Do not download from Instagram (rule 4) or YouTube (YouTube's terms forbid downloading). Transcription uses our free Groq key; never set a paid OpenAI or Gemini key for it.

---

## LICENSE: JDhruv14/line-art-animation

```
MIT License

Copyright (c) 2026 JDhruv14

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
Agent-Reach (11 Nov 2026): **no-login channels only.** Allow-list in `00-hq/agents/reach.py`: YouTube captions (`yt-dlp`), GitHub public API (`github-api`, no token), Reddit and web pages/RSS through Jina Reader (`public-web`, `jina`). Every call names its backend so Agent-Reach never falls back to its browser tools. Never enable Twitter/X, XiaoHongShu, LinkedIn, Instagram, Facebook, Bilibili, Boss or Xueqiu, never run `agent-reach login`, and never let it copy Chrome cookies. Its CLI gets no secrets (minimal environment). YouTube: captions only, never the video file.

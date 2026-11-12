# unslop audit: Tab Lifeboat popup + options page · 12 Nov 2026 (A198 part 4)

Skill: `.claude/skills/unslop` (heydamir/unslop, CC BY 4.0, credit Damir Sokolovsky). Signs from `references/signs.md`, Kalpa rules from its `KALPA.md`.
Pages: `04-extensions/src/entrypoints/popup/` and `options/` (`index.html`, `main.ts`, `style.css`, `options.css`).
Verdict: **light slop → polish mode**: tokens (plum `--l4`), bundled fonts and the temple strip already follow `00-hq/design/tokens.css`; fix only the signs found.
K074 (free-model copy pass) was checked: the agent said the files did not exist (they do), so this audit comes from a code scan + screenshots.

## Signs found and what happened

| Sign | Found (code scan + 390 px shots) | 12 Nov |
|---|---|---|
| Uppercase tracked labels | popup status ("LAST SNAPSHOT JUST NOW"), options eyebrow ("TAB LIFEBOAT", "PRO · OPENS SOON"), plan pill ("FREE"): mono 10–11 px, `uppercase`, `.1em` tracking | **fixed** → sentence case, body font 12 px, no tracking |
| Noise in list meta | every session said "· 0 groups"; popup also said "· auto" under "Auto snapshot…" | **fixed** → groups shown only when > 0; popup drops the repeated "auto" (options keeps the kind tag) |
| Broken row at 390 px | options session rows: Delete fell onto its own line, wider than the other buttons | **fixed** → Restore / Rename / Delete in one right-aligned row under the name (and one line with the name on wide screens) |
| Spacing off the 4 px scale | 6 px and 10 px gaps/paddings/margins (12 values) | **snapped** to 8/12 px |
| Purple gradients, glows, glass, emoji, gradient text | none (plum is the world colour `--l4`; Pro card is a flat tint) | — |
| Inline styles, off-token colours or fonts | none | — |
| Tap target under 44 px | none (all buttons and the file picker are 44 px) | — |

## Direction (5 lines, from the existing brand)
- **Product:** Tab Lifeboat quietly saves every window, tab and tab group so a crash or update never loses them.
- **Character:** a calm lifeboat locker: plain words, numbers you can trust, nothing shouting.
- **World:** Kalpavruksha tokens with world colour plum `--l4`.
- **Moment:** after a crash, open the popup, see "3 tabs", tap Restore.
- **Signature:** the gold-dot temple strip on deep green at the top, kept.

## Proof
Before/after at 390 px, light + dark: `unslop/tablifeboat/<popup|options>-before-<scheme>.jpg` and `-after-<scheme>.jpg` (from the real built extension, `tests/e2e/screens.e2e.mjs`).
Checks after the pass (12 Nov, local build): `npm run build` OK, `tsc --noEmit` OK, `vitest` 34/34, `screens.e2e.mjs` SCREENS PASSED (popup + options, light + dark, backup file round trip, import message, Restore). Lint: 6 older notes, none on changed lines.
Not live: store upload waits for Akhil's "go" (rule 9).

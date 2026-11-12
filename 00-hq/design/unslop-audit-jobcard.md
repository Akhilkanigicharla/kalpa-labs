# unslop audit: JobCard "my customers" PWA · 12 Nov 2026 (A198 part 3)

Skill: `.claude/skills/unslop` (heydamir/unslop, CC BY 4.0, credit Damir Sokolovsky). Signs from `references/signs.md`, Kalpa rules from its `KALPA.md`.
Pages: `02-jobcard/web/` (`index.html`, `app.mjs`, `app.css`, `i18n.mjs`): Due, Customers, Bills, Record tabs + sign-in.
Verdict: **light slop → polish mode**: tokens, fonts and the 4 line-icon tabs already follow `00-hq/design/tokens.css`; fix only the signs found.
K073 (free-model copy pass) was checked against the code: it returned 5 placeholder rows ("UNVERIFIED"), no real strings, so this audit comes from a code scan + screenshots.

## Signs found and what happened

| Sign | Found (code scan) | 12 Nov |
|---|---|---|
| Purple gradients, gradient text, glows, glass | none (only gradient is the skeleton shimmer, a loading pattern) | — |
| Text glyph as icon | Record button showed "●" / "■" while its tab used a mic line icon | **fixed** → same mic line icon (48 px, `currentColor`), filled square for stop |
| Hard-coded English in a 3-language UI | "Total" on the voice job card showed in English for Telugu/Hindi users | **fixed** → uses the existing `spent` key (మొత్తం / कुल / Total) |
| Clumsy copy | "1 due customers haven't agreed…" (plural bug) | **fixed** → "Not agreed to WhatsApp reminders yet: 1. Tick them in Customers." (te/hi already correct) |
| Spacing off the 4 px scale | 12 values (10 px, 6 px gaps/paddings, tab bar 6 px) | **snapped** to 8/12 px; 2 px hairlines on tags and tab labels kept |
| Inline styles | 13 `style=""` in `app.mjs` | **moved** to 5 small classes (`gap-top`, `gap-top-s`, `wide`, `end`, `strong`) + `.card>h2:first-child` |
| Off-token radius | logo `10px` | **fixed** → `var(--r-m)` |
| Uppercase tracked labels, emoji, italic, 800/900 weights | none | — |
| Tap target under 44 px | none (check.py) | — |

## Direction (5 lines, from the existing brand)
- **Product:** JobCard keeps an AC/appliance technician's customers, due services and bills, filled by voice.
- **Character:** a reliable notebook in the van: plain, quick, Telugu first.
- **World:** Kalpavruksha tokens with world colour `--l2`.
- **Moment:** tap the gold mic, speak the job, see the bill lines appear.
- **Signature:** the big gold mic button (madder ring while recording), kept.

## Proof
Before/after full pages at 390 px, light + dark: `unslop/jobcard/<tab>-before-<scheme>.jpg` and `<tab>-after-<scheme>.jpg` (due, customers, bills, record).
Checks after the pass (12 Nov, local build): `web/check.py` PASS (manifest, offline, 390 px light + dark, 16 px inputs, 44 px targets, no outside requests), `web/ux.py` PASS (tap sweep of UX patterns), `npm test` 36/36, vibecheck JobCard 20/20 clean.
Not live: JobCard is not deployed until Akhil's "go" (rule 9).

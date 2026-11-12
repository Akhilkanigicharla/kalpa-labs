# unslop audit: Ledger Peaks landing, dashboard + X-ray · 12 Nov 2026 (A198 part 5)

Skill: `.claude/skills/unslop` (heydamir/unslop, CC BY 4.0, credit Damir Sokolovsky). Signs from `references/signs.md`, Kalpa rules from its `KALPA.md`.
Pages: `06-finops/design/landing.html`, `dashboard.html`, `xray.html`, shared `lp.css` + `lp.js`.
Verdict: **light slop → polish mode**: tokens (pomegranate `--l6`), self-hosted Rozha One + Anek Latin and the temple strip already follow `00-hq/design/tokens.css`; fix only the signs found.

## Signs found and what happened

| Sign | Found (code scan + 390 px shots) | 12 Nov |
|---|---|---|
| Uppercase tracked labels | every `.eyebrow` (mono 12 px, `uppercase`, `.1em`), table heads (`.08em`), literal "THIS WEEK" on 3 dashboard cards, X-ray "PAGE 2 / 2 · LEDGER PEAKS…" | **fixed** → sentence case, body font 13 px, no tracking; new `.sub` class replaces 3 inline styles |
| Dot grid behind content | `body` had an accent-tinted radial-gradient dot grid on every page | **removed** → plain `--bg` |
| Chart where nothing leads | Cost-per-day: 7 pill-rounded bars all in pomegranate; feature/model bars all pomegranate | **fixed** → muted bars, world colour only on the busiest day and the top row; bar radius 6 → 2 |
| Mixed type in one row | landing sample card: customer name in mono like a number | **fixed** → name in body font, numbers stay mono tabular |
| Spacing off the 4 px scale | 6 px / 10 px gaps and paddings (14 screen values in lp.css + 3 pages) | **snapped** to 8/12 px. X-ray `@media print` values kept: they hold the report to exactly 2 A4 pages (test_xray checks it) |
| Copy | K076 (free model) gave 5 rewrites: #4 used ("Mockup: this button will open an upload form."); #1, #3 rejected (they drop "we never see prompts or replies" / "you hash before upload", the trust facts); #2 rejected (drops FBIL, the actual rate source); #5 rejected (loses "real rows") | 1 of 5 used |
| Gradients, glows, glass, emoji, hype words, fake data | none (diamond strip on cards and the temple strip are the world's signature; sample numbers come from the engine) | — |
| Tap target under 44 px | none (screens.py checks every button) | — |

## Direction (5 lines, from the existing brand)
- **Product:** Ledger Peaks shows Indian SaaS teams their AI bill in rupees, per customer and feature, and 3 ways to cut it.
- **Character:** a careful chartered accountant: exact rupees, sources named, nothing shouting.
- **World:** Kalpavruksha tokens with world colour pomegranate `--l6`, used only where money leaks.
- **Moment:** the founder opens the X-ray and sees which customer the AI bill is eating.
- **Signature:** the gold-dot temple strip and the pomegranate diamond edge on the main card, kept.

## Proof
Before/after at 390 px, light + dark: `unslop/ledgerpeaks/<landing|dashboard-overview|xray>-<before|after>-<scheme>.jpg` (from `06-finops/design/screens.py`).
Checks after the pass (12 Nov): `screens.py` 12 screens PASS (no sideways scroll, tokens, self-hosted fonts, no external requests, no JS errors, taps ≥ 44 px), `pytest 06-finops/tests` 91/91, vibecheck "Ledger Peaks pages 20/20 clean", `eng_check.py b6` 0 FAIL.
SEO: not relevant yet (mockups, not public; A192 covers the landing when it becomes a site). Not live.

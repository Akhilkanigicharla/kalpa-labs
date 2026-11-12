# unslop audit: Kalpavruksha CEO Room · 12 Nov 2026 (A198 part 6)

Skill: `.claude/skills/unslop` (heydamir/unslop, CC BY 4.0, credit Damir Sokolovsky). Signs from `references/signs.md`, Kalpa rules from its `KALPA.md`.
Page: `00-hq/design/ceo-room-dashboard.html` (+ `ceo-room-office.css/.js`, `ceo-room-rooms.js`). Private dashboard for Akhil (claude.ai artifact), not a public site.
Verdict: **light slop → polish mode**: Kalpavruksha tokens, tree logo and the gold-dot strip already follow `00-hq/design/tokens.css`; fix only the signs found.

## Signs found and what happened

| Sign | Found (code scan + 390 px shots) | 12 Nov |
|---|---|---|
| Uppercase tracked label | hero kicker "KALPAVRUKSHA · AGENTS ROOM" (`uppercase`, `.08em`) | **fixed** → sentence case, no tracking |
| Corner glows | hero had two radial colour glows; Kingdom game card one more | **removed** → plain panel |
| Gradient bar | game XP bar warn → ok gradient | **fixed** → solid `--color-ok` |
| Glass nav | sticky tab bar: 88 % panel + `backdrop-filter: blur(12px)` | **fixed** → solid panel (vibecheck tell 1) |
| Spacing off the 4 px scale | nav padding 5 px, hero/game padding min 18 px | **snapped** → 4 px, 16 px |
| Copy: plural bugs | "1 tasks are waiting", "1 tasks waiting on you", "of 1 cloud workers", "0 of 1 tasks", "in 1 days"; KPI read "1 agent tasks done of 3" | **fixed** → small `pl()` helper; KPI now "1 · of 3 agent tasks done" |
| Copy (K080, free model) | 5 suggestions: #1 uppercase kicker used; #2 "CEO room" rejected (product name in LINKS/docs); #3 no change; #4, #5 colon instead of "·" rejected (the interpunct is the Kalpa separator everywhere) | 1 of 5 used |
| Robot motion | office robots walk, type, blink | **kept**: the signature detail (the live office is the point of the page); already off under reduced motion (rooms test checks) |
| Emoji, hype words, fake data, taps < 44 px | none (UX test checks Retry ≥ 44 px) | — |

## Direction (5 lines, from the existing brand)
- **Product:** one private room where Akhil sees what his AI team did, what waits on him and which cloud workers ran.
- **Character:** a calm chief of staff: counts, names, next step, no noise.
- **World:** Kalpavruksha tokens (bark, leaf, gold), world colours only on the world they belong to.
- **Moment:** Akhil opens it on his phone at night and reads one sentence: how far, what waits on him.
- **Signature:** the live isometric robot office and the gold-dot strip under the hero, kept.

## Proof
Before/after at 390 px, light + dark: `unslop/ceoroom/<home|work>-<before|after>-<scheme>.jpg` from `00-hq/design/ceo-room-shots.js` (stand-in dashboard runtime, so card padding tokens from claude.ai are missing in the shots; layout and copy are real).
Checks after the pass (12 Nov): `ceo-room-shots.js` PASS (no sideways scroll, no JS errors), `ceo-room-ux.test.js` PASS light + dark, `ceo-room-office.test.js` PASS 4 modes, `ceo-room-rooms.test.js` PASS; vibecheck now scans the CEO Room too: 20/20 clean, `vibecheck.test.mjs` PASS (all 7 sites).
SEO: not relevant (private dashboard, never indexed). Engineering checks: not relevant as a world (runs inside the claude.ai artifact sandbox, no server code). Republishing the artifact page is left to Akhil's next CEO Room update (build sprints only refresh its data).

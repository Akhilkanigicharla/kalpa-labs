# unslop audit: Kalpa site · 9 Nov 2026 (code scan) · passes 12 Nov 2026 (A198 part 1)

Skill: `.claude/skills/unslop` (heydamir/unslop, CC BY 4.0, credit Damir Sokolovsky). Signs from `references/signs.md`.
Verdict: **light slop → polish mode** (skill step 3): keep palette, type, layout and the Kalpavruksha visual; fix only what the audit found.

## Signs (9 Nov scan) and what happened (12 Nov)

| Sign | Found | 12 Nov |
|---|---|---|
| Purple/violet gradients, gradient text | none | — |
| Coloured glows | 1: `.falling .ff` firefly glow (dark mode only) | **kept** as the one signature detail: fireflies only appear in the tree scene at night, nowhere else |
| Radial colour washes | 2: body gold wash (top right), hero leaf wash behind the tree | body gold wash **removed** (wash behind content); hero leaf wash **kept** as part of the one bright element (the tree scene) |
| Heavy weights 800/900 | none | — |
| Uppercase + wide tracking labels | none | — |
| Emoji as icons/labels, ✨ for AI | none | — |
| Glass / blur blobs | none | — |
| Spacing off the 4 px scale | 56 padding/margin/gap values (.55rem, .6rem, .65rem, 1.3rem, 1.6rem …) | **all snapped** to the 4 px scale (script, padding/margin/gap only; font sizes and icon sizes untouched; ≤ 2 px nudges kept) |
| Tap target under 44 px | `.tip .btn` min-height 42 px | **fixed** → 44 px; sticky bar buttons 46 → 48 px (on grid) |
| Italic emphasis, negative tracking | none | — |

## Direction (5 lines, from the existing brand)
- **Product:** Kalpa Labs builds small, honest AI tools for Hyderabad businesses; BotBhai answers their WhatsApp in Telugu, Hindi and English.
- **Character:** warm, local, plain-spoken.
- **World:** a Kalpavruksha tree in a temple courtyard: leaf green, temple gold, earth brown.
- **Moment:** the hero tree with its fruit (each fruit = a product) and working robots.
- **Signature:** fireflies in the tree at night (dark mode).

## Proof
Before/after full pages at 390 px: `unslop/site/before-light.jpg`, `before-dark.jpg`, `after-light.jpg`, `after-dark.jpg`. Hero CTAs now sit on one row at 390 px (primary + secondary), tree scene unchanged.
Checks after the pass (12 Nov, local): tap sweep PASS (390, light + dark), chat buttons PASS, form UX PASS, SEO PASS, chat tests 9 groups PASS, vibecheck 20/20 clean.
Not live: goes to kalpalabs.dpdns.org only on Akhil's "go" (C73).

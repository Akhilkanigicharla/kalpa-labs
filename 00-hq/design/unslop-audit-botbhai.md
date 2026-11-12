# unslop audit: BotBhai web · 12 Nov 2026 (A198 part 2)

Skill: `.claude/skills/unslop` (heydamir/unslop, CC BY 4.0, credit Damir Sokolovsky). Signs from `references/signs.md`, Kalpa rules from its `KALPA.md`.
Pages: `01-botbhai/botbhai/web/index.src.html` (demo), `dashboard.html`, `inbox.html`, `billing.html`, `widget.js`.
Verdict: **light slop → polish mode**: palette, fonts and layout already follow `00-hq/design/tokens.css`; fix only the signs found.
K071 (free-model checklist) was checked against the code: its BotBhai row named a file that does not exist and signs not present ("glowing borders"), so this audit comes from a code scan + screenshots instead.

## Signs found and what happened

| Sign | Found (code scan) | 12 Nov |
|---|---|---|
| Purple/violet gradients, gradient text, colour washes | none (gradients are only the leaf border and dot patterns) | — |
| Coloured glows | widget launcher shadow in off-palette indigo `rgba(28,36,99,.35)` | **fixed** → neutral black shadow; gold ring kept (brand) |
| Halo rings | voice orb gold ring (madder while listening) on the demo | **kept** as the one signature detail: it shows the mic state |
| Emoji as icons/labels | dashboard bottom tabs 📅 👥 💬 📈; widget launcher 💬; UI copy 🙌 🙋 💰 in inbox/billing empty states and toasts | **fixed** → one line-icon set (4 inline SVGs, `currentColor`, 1.75 stroke) and plain text. Emoji inside sample **bot WhatsApp messages** kept: that is real customer-facing message content, not UI |
| Uppercase + wide tracking labels | status pills, KPI labels, form labels, chat "by" labels, "DEMO" flag | **fixed** → sentence case, normal tracking. Mono eyebrows kept: DESIGN-SYSTEM.md allows uppercase +0.1em mono eyebrows |
| Eyebrow above the headline | inbox header | **fixed** → moved under the h1 (DESIGN-SYSTEM.md "put labels under it") |
| Spacing off the 4 px scale | 64 padding/margin/gap values (6 px, 10 px, .35rem …) | **snapped** to the nearest 4 px (ties up); 1–2 px hairline nudges kept |
| Italic emphasis | demo `.sample` caption | **fixed** → normal style |
| Heavy weights 800/900, glass/blur, negative tracking | none | — |
| Tap target under 44 px | none (tap sweep) | — |

## Direction (5 lines, from the existing brand)
- **Product:** BotBhai answers a Hyderabad business's WhatsApp and web chat in Telugu, Hindi and English and books the customer.
- **Character:** helpful shop assistant: quick, warm, plain.
- **World:** Kalpavruksha canopy green + fruit gold, leaf border on the hero card.
- **Moment:** the phone demo where a lead appears in the owner's console.
- **Signature:** the voice orb's gold ring.

## Proof
Before/after full pages at 390 px, light + dark: `unslop/botbhai/<page>-before-<scheme>.jpg` and `<page>-after-<scheme>.jpg` (index, dashboard, inbox, billing).
Checks after the pass (12 Nov, local build): `tools/screens.py` 44 screens PASS, tap sweep PASS (5 pages, light + dark), inbox/billing/dashboard/turnstile/chat/web UX tests PASS, private pages noindex PASS, vibecheck BotBhai 20/20 clean, `test-all.sh` see log.
Not live: BotBhai web is not deployed until Akhil's "go" (rule 9).

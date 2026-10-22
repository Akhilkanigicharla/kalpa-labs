# 🌳 Kalpa Design System · "Kalpavruksha"

One look for every Kalpa Labs screen: the company site, the Kingdom, BotBhai, the calculator site, Ledger Peaks, JobCard, Tab Lifeboat. Product brands keep their own name but use this system underneath, tuned per world with that world's colour.

**Why Kalpavruksha (Akhil, 20 Oct 2026):** the wish-fulfilling tree. Kalpa Labs is named after it: one tree, many branches (our 8 worlds), each bearing fruit for the people who sit under it. Colours come from the tree itself: canopy and leaf greens, bark brown, golden fruit, on a warm parchment ground. It replaces the earlier Kalamkari indigo theme (19 Oct 2026).

**Logo:** [brand/kalpavruksha.svg](brand/kalpavruksha.svg), an original tree (canopy, five golden fruits, bark trunk, roots). Use it as the company mark and favicon; product brands sit beside it, never inside it.

## Tokens
The source of truth is [tokens.css](tokens.css). Light and dark themes are both defined, and every colour is a token. All text pairs pass WCAG AA (checked by `00-hq/design/theme.test.mjs`).

| Role | Light | Dark | Use |
|---|---|---|---|
| `--hero` | canopy #1D3A25 | #17301F | Hero bands, the active tab, avatars |
| `--accent` | leaf #2F6A3A | #8FCB8C | Primary buttons, links, focus |
| `--leaf` | young leaf #5E9E4C | #8FCB8C | Vine band leaves, rosettes, small living accents (decoration only) |
| `--gold` | fruit #C38E12 | #E8B64A | Highlights, rewards, focus ring, gold buttons (dark text) |
| `--bark` / `--madder` | #6B4226 / #8A4A28 | #C08A5E / #D98B5F | Trunk lines, time stamps, warm accents (`--madder` kept as the name in code) |
| `--l0…--l7` | one per world | | HQ stone, b1 bark, b2 river, b3 leaf, b4 jamun, b5 mango, b6 hibiscus, b7 dusk |
| `--ok --warn --bad` | | | State only, never decoration |

## Type
| Role | Face | Rule |
|---|---|---|
| Display | **Rozha One** (400 only) | Headings and big numbers. Never bold, never below 17 px |
| Body | **Anek Latin** + **Anek Telugu** | Same family across English and Telugu, so mixed Tenglish lines match |
| Data | **JetBrains Mono** | Eyebrows (uppercase, +0.1em), times, IDs, table numbers (`tabular-nums`) |

All four are OFL on Google Fonts. Load them with one `<link>` (see the Kingdom head).

## Signature details
- **Vine band (`--vine`):** a 10 px band of leaves with golden fruit, top and bottom of hero surfaces only.
- **Seed ground:** an 18 px dot grid tinted by the accent, on the page background.
- **Zig-zag cap:** a world-coloured strip on quest and feature cards.
- **Fruit badges:** a conic gold/leaf rosette.
- **Pills:** fully rounded buttons and tabs; cards use 12/18 px radii, applied by role, not everywhere.

## Rules
1. Phone first: 390 px wide with no sideways scroll, 44 px touch targets, a bottom tab bar under 760 px.
2. Both themes are designed; check every screen in light and dark.
3. Motion: one rise-in on view change, confetti only on quest complete; honour `prefers-reduced-motion`.
4. Telugu text uses the body font; never put Telugu in Rozha One (it has no Telugu glyphs).
5. Copy: plain words from the user's side ("Complete", "Book slot"), never system words.

## Free UI toolkit (all licences checked on npm, 13 Oct 2026)
| Need | Adopt | Licence | Notes |
|---|---|---|---|
| Styling | **Tailwind CSS 4.3** with these tokens as the theme | MIT | For React/Astro products; plain CSS for single-file pages |
| Components (React) | **shadcn/ui** (copy-in components on **Radix** primitives) | MIT | Restyle to these tokens; used in Ledger Peaks dashboard, BotBhai inbox |
| Command palette, drawer, toasts | **cmdk**, **vaul**, **sonner** | MIT | |
| Charts | **ECharts 6** (dashboards), **uPlot** (tiny, fast) | Apache-2.0 / MIT | Tremor (Apache-2.0) is fine too for React dashboards |
| Tables | **TanStack Table 9** | MIT | |
| Icons | **Lucide** or **Phosphor** | ISC / MIT | One set per product, 1.75 px stroke |
| Motion | **Motion** (formerly Framer Motion), anime.js | MIT | **GSAP is avoided:** its licence isn't open source |
| Marketing/calculator sites | **Astro 7** + Starlight for docs | MIT | b5 calculators, b6 landing, legal pages |
| Mobile app | **Expo** + **NativeWind 4** (Tailwind tokens in React Native) | MIT | JobCard |
| Extension | **WXT 0.21** + plain CSS from tokens | MIT | Tab Lifeboat |
| No-build pages (artifacts, BotBhai demo) | Plain CSS + tokens; **Alpine.js** or **htmx** if needed | MIT / 0BSD | |
| Delight | **canvas-confetti**, **dotLottie** | ISC / MIT | Sparingly |
| Fonts | @fontsource packages for self-hosting | OFL | Use inside apps and PDFs (cards.py already does this) |

**Avoid:** GSAP (non-OSS licence), Aceternity/"Pro" UI kits with paid or unclear licences, and any template marketplace theme. Building our own from these primitives keeps everything free and ours.

## Reference implementation
[kingdom-control-room.html](kingdom-control-room.html): the live Kingdom page (https://claude.ai/artifact/MdD3R2kEYP4qHDXXvbsJF1).

## 20 tells that make a site look "vibecoded" (we avoid all of them)
Checked on every push by `node 00-hq/design/vibecheck.test.mjs` (Kalpa quality → design). Source: millee.md's list, 19 Oct 2026.
Banned: purple-to-blue gradients, gradient headline text, emojis in headings, Inter, coloured left-border cards, glassmorphism (backdrop blur), low-contrast dark mode, three equal icon boxes, a badge/eyebrow above the headline (put labels under it), Lucide, untouched shadcn, sections fading in on scroll, cursor-following beams, buttons that fade on hover, spacing off the 4-point scale, em dashes in sentences, buzzwords ("seamless", "supercharge", …), serif italics for accent words, Space Grotesk + Instrument Serif, grain texture over gradients.
Allowed on purpose: number tiles in a 3-column grid on app screens (`.kpis`, `.stats`), a lone "—" in an empty table cell, the Kalpavruksha borders (`.temple`, `.cap`) that are our own motif.
Spacing scale (px): 0 1 2 4 6 8 10 12 16 20 24 28 32 40 48 56 64 72 80 96 112 128.

# 🎨 Kalpa Design System · "Kalamkari"

One look for every Kalpa Labs screen: the Kingdom, BotBhai dashboards, the calculator site, Ledger Peaks, JobCard, Tab Lifeboat. Product brands keep their own name and logo but use this system underneath, tuned per world with that world's colour.

**Why Kalamkari:** it's the hand-painted, block-printed cloth art of Andhra Pradesh (Machilipatnam and Srikalahasti). It's rooted in the founder's home region and recognisably Indian, and it doesn't look like the generic purple-gradient AI app. Natural-dye colours: indigo, madder red, turmeric gold.

## Tokens
The source of truth is [tokens.css](tokens.css). Light and dark themes are both defined, and every colour is a token.

| Role | Light | Dark | Use |
|---|---|---|---|
| `--hero` | indigo #1C2463 | #1B2266 | Hero cards, the active tab, avatars |
| `--accent` | #2A3A8F | #9AABFF | Primary buttons, links, focus |
| `--gold` | turmeric #D3940A | #F2B840 | XP, rewards, focus ring, highlights |
| `--madder` | #B23A2C | #F0745F | Temple-border teeth, time stamps, small warm accents |
| `--l0…--l7` | one per world | | HQ slate, b1 madder, b2 indigo, b3 leaf, b4 plum, b5 turmeric, b6 pomegranate, b7 teal |
| `--ok --warn --bad` | | | State only, never decoration |

## Type
| Role | Face | Rule |
|---|---|---|
| Display | **Rozha One** (400 only) | Headings and big numbers. Never bold, never below 17 px |
| Body | **Anek Latin** + **Anek Telugu** | Same family across English and Telugu, so mixed Tenglish lines match |
| Data | **JetBrains Mono** | Eyebrows (uppercase, +0.1em), times, IDs, table numbers (`tabular-nums`) |

All four are OFL on Google Fonts. Load them with one `<link>` (see the Kingdom head).

## Signature details
- **Temple border:** a 10 px band of gold dots over madder teeth, top and bottom of hero surfaces only.
- **Block-print ground:** an 18 px dot grid tinted by the accent, on the page background.
- **Zig-zag cap:** a world-coloured strip on quest and feature cards.
- **Medallion badges:** a conic gold/madder rosette.
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

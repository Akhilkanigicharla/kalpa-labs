# UX check: BotBhai web (chat, dashboard, inbox, billing) · 9 Nov 2026

Against `00-hq/design/UX-PATTERNS.md`. Draft by the free-model agent (K049, 20 rows); every row checked against the code by Claude, wrong rows corrected.
Tests: `bash 01-botbhai/botbhai/tools/test-all.sh` (includes `test_web_ux.py` for the fixes below and `test_taps.py`, the 390 px tap sweep in light + dark on all 5 screens). All PASS.

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | ✅ Fixed 9 Nov. Inbox reply shows your bubble at once ("Sending…"); if it fails it says "Not sent", keeps the bubble and puts your words back in the box. Chat page shows your message at once. |
| 2 | Skeleton loaders | ✅ Dashboard shimmer rows; fixed 9 Nov: inbox chat list and billing invoice list also show shimmer rows (`aria-busy`) until data arrives. All stop for reduced motion. |
| 3 | Command palette | ➖ Phone-first tools with 3–4 tabs; nothing to search across. |
| 4 | Persistent navigation | ✅ Dashboard tab bar fixed at the bottom on phones; inbox keeps the chat list one tap away (← back). |
| 5 | Loading and empty states | ✅ "No bookings today yet…", "Nobody is waiting for you. 🙌 The bot has it.", "No messages yet." |
| 6 | Autosave | ✅ Inbox reply draft and private note survive the 15-second refresh; the chat page keeps the conversation. Forms are one field, so nothing else to save. |
| 7 | Debouncing | ✅ Fixed 9 Nov. Lead search waits 250 ms after the last letter (test: 5 letters → at most 2 re-draws). |
| 8 | Throttling | ✅ One action at a time (`S.busy`) in inbox and billing; refresh only while the tab is visible. |
| 9 | Smart form validation | ✅ Fixed 9 Nov. Sign-in key on all 3 screens is checked when you leave the field, shows a plain error, and clears as soon as it is right (`aria-invalid`). |
| 10 | Bulk actions | ➖ A salon handles one chat or invoice at a time; no lists long enough to need it. |
| 11 | Reusable data table | ➖ Cards and timelines on a phone instead of tables; Excel download for the full table. |
| 12 | Advanced filtering | ✅ Status chips (Hot / All…, Needs you / Bot / Done, invoice status) + lead search. |
| 13 | Keyboard shortcuts | ✅ Ctrl/⌘ + Enter sends an inbox reply (agent had this as "not relevant"; corrected). |
| 14 | Tier-based UI indicators | ➖ One pilot plan, no tiers yet. Add when paid tiers exist. |
| 15 | Onboarding data capture | ➖ The owner gets a setup link with the key; no sign-up form on these screens. |
| 16 | Referral pages | ➖ Not part of the owner tools. |
| 17 | Custom 404 | ➖ App screens are single files; the public site's 404 is covered by the SEO site (A193). |
| 18 | Mobile-optimised layout | ✅ 390 px tap sweep passes on all 5 screens, light + dark. Fixed 9 Nov: chat quick replies, language and mode buttons, billing chips and the inbox phone link raised to 44 px. |
| 19 | Destructive action protection | ✅ Fixed 9 Nov. Inbox "Mark done" (hands the customer back to the bot) needs a second tap within 4 s. Billing "Void" already needed two taps. Excel download is not destructive (agent row corrected). |
| 20 | Graceful error recovery | ✅ Offline keeps the last data with a toast; failed actions say "Nothing was sent / changed"; a bad key returns to sign-in with a clear message. |

No ❌ left, so no new roadmap items. Also fixed while testing: `tools/test-all.sh` ignored failures inside its `a && b && c` chain of screen tests; each test now runs on its own line.

Glow-up pages (A199): same template and patterns as the client SEO site above; worst-case data tested in `tools/test_glowup.py` (no sideways scroll at 360 px, WhatsApp button never covered, images sized to avoid layout shift, cover photo loads first).

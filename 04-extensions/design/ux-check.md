# UX check: Tab Lifeboat (popup, options page, store site) · 9 Nov 2026

Against `00-hq/design/UX-PATTERNS.md`. The free-model draft K051 was rejected by Vigil, so Claude audited the code row by row.
Tests (all PASS): `npm test` (34), `npm run test:screens` (real built extension, light + dark, 390 px + 1280 px, now 44 px buttons, plus new popup checks), `npm run test:e2e`, `npm run test:store`, `tsc`, tap sweep on the store site (index, privacy, terms, 404) at 390 px light + dark, `test_seo.py` on the site. CI: the site workflow now runs the tap sweep before publishing.

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | ✅ Save shows "Saved N tabs" on the button; fixed 9 Nov: Restore says "Opened N tabs" or "Could not open" in the popup too. |
| 2 | Skeleton loaders | ✅ Fixed 9 Nov: "Loading…" row in the popup and options lists until data arrives (local storage answers in milliseconds, so a row is enough). |
| 3 | Command palette | ➖ A small popup with one main action; the options page has two search boxes instead. |
| 4 | Persistent navigation | ✅ Popup → "Backups and settings" opens options; options sections in one scrolling page. |
| 5 | Loading and empty states | ✅ "Nothing saved yet.", "No session matches.", "No saved tab matches." |
| 6 | Autosave | ✅ The product itself: snapshots every 5 minutes; pasted import text is kept if an import fails (fixed 9 Nov). |
| 7 | Debouncing | ✅ Saved-tab search waits 200 ms; fixed 9 Nov: import preview waits 250 ms after a paste (popup + options). |
| 8 | Throttling | ✅ Save button disabled while saving; Import stays off until the preview is valid. |
| 9 | Smart form validation | ✅ Import preview tells how many tabs/groups and what was skipped before importing; 14 Nov (A213): Session Buddy CSV and title/URL lists import too, and a CSV without a URL column is refused with a plain reason; backup files over 50 MB refused with a reason. |
| 10 | Bulk actions | ✅ Cleanup closes all duplicates / unused tabs in one step (Pro), after saving them first. |
| 11 | Reusable data table | ➖ Session lists are short cards; a table would not fit a 360 px popup. |
| 12 | Advanced filtering | ✅ Search by session name; search across every saved tab; "where did this tab go" timeline. |
| 13 | Keyboard shortcuts | ➖ Not yet: Chrome's own shortcut page can bind the toolbar button. Later idea, not needed for launch. |
| 14 | Tier-based UI indicators | ✅ Free / Pro badge, limits shown ("free keeps N snapshots"), Pro tools hidden on Free. |
| 15 | Onboarding data capture | ➖ No account, no sign-up: works the moment it is installed (privacy promise). |
| 16 | Referral pages | ➖ Not in v1. |
| 17 | Custom 404 | ✅ Store site has a branded 404 (A191). |
| 18 | Mobile-optimised layout | ✅ Store site passes the 390 px tap sweep (fixed 9 Nov: header logo link 32 → 44 px). Popup/options: no sideways scroll at 390 px; buttons raised from 36 px to 44 px (fixed 9 Nov). |
| 19 | Destructive action protection | ✅ Delete asks first ("This can't be undone"); cleanup saves "Before cleanup" first so it can be undone. |
| 20 | Graceful error recovery | ✅ Fixed 9 Nov: if the background is busy or asleep, popup and options show "Tab Lifeboat is busy. Try again." instead of failing silently; import and restore errors are shown in words. |

No ❌ left.

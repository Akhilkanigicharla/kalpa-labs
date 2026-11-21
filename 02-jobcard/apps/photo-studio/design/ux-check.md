# UX check: Kalpa Photo Studio (02-jobcard/apps/photo-studio) · 21 Nov 2026 (A328)

Against `00-hq/design/UX-PATTERNS.md`. ✅ done · ➖ not relevant (why) · ❌ missing (roadmap id).
Proof run 21 Nov: `npm test` (15 pass), tap sweep `00-hq/site/tests/test_tap_sweep.py` at 390 px light + dark on the app and on `404.html` → PASS, `python3 00-hq/tools/eng_check.py photo-studio` 0 FAIL. Private prototype, not live (rule 9).

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | ➖ No server: crop, background and checks run on the phone at once. |
| 2 | Skeleton loaders | ➖ Nothing loads from a network; the photo appears as soon as the browser decodes it. |
| 3 | Command palette | ➖ One-page, five-step flow on a phone. |
| 4 | Persistent navigation | ➖ Single page with numbered steps top to bottom; no sections to jump between. |
| 5 | Loading and empty states | ✅ Before a photo is chosen the editor stays hidden and the file step is shown; spec info updates in an `aria-live` area. |
| 6 | Autosave | ➖ Photos are never stored (privacy promise in README); the saved JPG is the output. |
| 7 | Debouncing | ➖ No typed input that triggers work. |
| 8 | Throttling | ✅ Drag, resize and background slider redraw once per frame (`requestAnimationFrame` in `scheduleRefresh`). |
| 9 | Smart form validation | ✅ Non-image files refused ("Please choose a photo file."); photos that won't decode get "Try a JPG or PNG"; output size rule (KB) auto-tuned. |
| 10 | Bulk actions | ➖ One photo at a time; print sheet repeats it. |
| 11 | Reusable data table | ➖ No data tables. |
| 12 | Advanced filtering | ➖ One dropdown of document specs (country/use). |
| 13 | Keyboard shortcuts | ➖ Phone-first; Smaller/Bigger buttons work by keyboard. |
| 14 | Tier-based UI indicators | ➖ No paid tier yet (C80). |
| 15 | Onboarding data capture | ➖ No account, nothing to capture. |
| 16 | Referral pages | ➖ Not live. |
| 17 | Custom 404 | ✅ `404.html` added 21 Nov (A328). |
| 18 | Mobile-optimised layout | ✅ Tap sweep PASS at 390 px, light + dark (21 Nov). |
| 19 | Destructive action protection | ➖ Nothing to delete; choosing a new photo only replaces the one in memory. |
| 20 | Graceful error recovery | ✅ File errors shown in place; offline shell (`sw.js`) now falls back to `index.html` when the network fails (fixed 21 Nov, A328). |

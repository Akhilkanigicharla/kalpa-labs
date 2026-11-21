# UX check: Kalpa Bhasha Kids (02-jobcard/apps/bhasha-kids) · 21 Nov 2026 (A328)

Against `00-hq/design/UX-PATTERNS.md`. ✅ done · ➖ not relevant (why) · ❌ missing (roadmap id).
Proof run 21 Nov: `npm test` (19 pass), tap sweep `00-hq/site/tests/test_tap_sweep.py` at 390 px light + dark on the app and on `404.html` → PASS (21 Nov, A331: no stub needed any more; the speech probe now waits for the first Say it tap, and if it ever kills the tab the app skips the on-device probe on the next try), `python3 00-hq/tools/eng_check.py bhasha-kids` 0 FAIL. Private prototype, not live (rule 9).

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | ✅ Stars, streak and review grades update at once from local state; no server round trip. |
| 2 | Skeleton loaders | ➖ Lesson files are 44 KB from the same folder (offline cached); no visible wait. |
| 3 | Command palette | ➖ Kids' app with a few big buttons. |
| 4 | Persistent navigation | ✅ Home → lesson → back home; parent area behind the gate. |
| 5 | Loading and empty states | ✅ If lessons can't load it says why ("Open this app from a local web server"); review queue empty state shown. |
| 6 | Autosave | ✅ Progress saved to this device after every answer (`store.save`). |
| 7 | Debouncing | ➖ No typed search. |
| 8 | Throttling | ➖ No scroll/drag work. |
| 9 | Smart form validation | ✅ Parent gate checks the sum and gives a new one when wrong. |
| 10 | Bulk actions | ➖ Not for kids. |
| 11 | Reusable data table | ➖ Parent summary is a short list. |
| 12 | Advanced filtering | ➖ Two languages, lesson list only. |
| 13 | Keyboard shortcuts | ➖ Kids on phones/tablets. |
| 14 | Tier-based UI indicators | ➖ No paid tier yet (C80). |
| 15 | Onboarding data capture | ➖ No account; only the language choice. |
| 16 | Referral pages | ➖ Not live. |
| 17 | Custom 404 | ✅ `404.html` added 21 Nov (A328). |
| 18 | Mobile-optimised layout | ✅ Tap sweep PASS at 390 px, light + dark, no stub (A331). |
| 19 | Destructive action protection | ✅ Reset sits behind the parent gate and a "cannot be undone" confirm; "Save a copy" export next to it. |
| 20 | Graceful error recovery | ✅ Speech and service-worker failures caught; offline falls back to the cached app. ❌ A renderer crash in `SpeechRecognition.available` cannot be caught in JS → A331. |

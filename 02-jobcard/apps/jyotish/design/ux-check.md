# UX check: Kalpa Jyotish (02-jobcard/apps/jyotish) · 21 Nov 2026 (A328)

Against `00-hq/design/UX-PATTERNS.md`. ✅ done · ➖ not relevant (why) · ❌ missing (roadmap id).
Proof run 21 Nov: `npm test` (26 pass), tap sweep `00-hq/site/tests/test_tap_sweep.py` at 390 px light + dark on the app and on `404.html` → PASS, `python3 00-hq/tools/eng_check.py jyotish` 0 FAIL. Private prototype, not live (rule 9).

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | ➖ No server: every answer is worked out on the phone at once, nothing to wait for. |
| 2 | Skeleton loaders | ➖ Nothing loads from a network (CSP `connect-src 'none'`); results appear in the same frame. |
| 3 | Command palette | ➖ Three tabs on a phone; a search-everything box adds nothing. |
| 4 | Persistent navigation | ✅ Tab bar (`<nav class="tabs" role="tablist">`): Birth star, Names, Good days. |
| 5 | Loading and empty states | ✅ Results sit in `aria-live` areas; name filters with no match say so. |
| 6 | Autosave | ✅ Birth details saved on this device only when "Remember" is ticked (localStorage, try/catch for private mode). |
| 7 | Debouncing | ➖ No typing-triggered work; results come on button press. |
| 8 | Throttling | ➖ No scroll/drag handlers doing heavy work. |
| 9 | Smart form validation | ✅ `type=date/time` with `required` and min 1700 / max 2200; errors caught and shown (app.js try/catch). |
| 10 | Bulk actions | ➖ No lists of records to act on. |
| 11 | Reusable data table | ➖ Good-days list is one simple list, no table of records. |
| 12 | Advanced filtering | ✅ Names filter by syllable, boy/girl, first letter and name number; good days can hide Amavasya/Rikta days. |
| 13 | Keyboard shortcuts | ➖ Phone-first; native form controls keep keyboard access. |
| 14 | Tier-based UI indicators | ➖ No paid tier yet (price not decided, CEO queue C80). |
| 15 | Onboarding data capture | ➖ No account; the birth form itself is the first screen. |
| 16 | Referral pages | ➖ Not live; referrals come after launch. |
| 17 | Custom 404 | ✅ `404.html` added 21 Nov (A328): plain words + 44 px button back to the app. |
| 18 | Mobile-optimised layout | ✅ Tap sweep PASS at 390 px, light + dark (21 Nov). |
| 19 | Destructive action protection | ✅ Only delete is "Forget my details" (one saved record, says "cleared" at once; re-entering takes seconds). |
| 20 | Graceful error recovery | ✅ Calculation errors caught and shown in place; storage failures ignored without breaking the page. |

# UX check: Ledger Peaks dashboard + landing · 9 Nov 2026

Against `00-hq/design/UX-PATTERNS.md`. Draft by the free-model agent (K052, 20 rows); every row checked against the code by Claude, wrong rows corrected.
Tests: `python3 -m pytest -q 06-finops/tests/test_design.py` runs `design/screens.py`: 390 px light + dark on landing, X-ray and all 4 dashboard tabs, now with a tap sweep (every link, button and FAQ row: not covered, 44 px tall) and behaviour checks (filter chips, empty data, broken data). All PASS.

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | ➖ Read-only viewer; nothing is saved from these screens. |
| 2 | Skeleton loaders | ➖ Data is inside the page (no network wait), so there is nothing to wait for. Agent said ❌; corrected. Add shimmer rows when the dashboard fetches live data (A91 depth). |
| 3 | Command palette | ➖ Phone-first, 4 tabs. |
| 4 | Persistent navigation | ✅ Bottom tab bar on phones, top tabs on desktop. Fixed 9 Nov: page content scrolled over the tab bar on Customers and Savings (tab bar now sits on top). |
| 5 | Loading and empty states | ✅ Fixed 9 Nov. Every list has an empty view with the next step: customers, filter with no match, savings ideas, by feature, by model, cost per day chart, DPDP gaps ("Nothing missing"). Test feeds empty data. |
| 6 | Autosave | ➖ No editable fields. |
| 7 | Debouncing | ➖ No search or live validation. |
| 8 | Throttling | ➖ No submit or refresh actions; no scroll handlers. |
| 9 | Smart form validation | ➖ No form yet; the X-ray intake form is A203. |
| 10 | Bulk actions | ➖ Customer list is for reading margins; no batch action exists. |
| 11 | Reusable data table | ➖ 6–20 customers shown as cards with a bar on a phone; the X-ray page already uses a scrolling table. |
| 12 | Advanced filtering | ✅ Fixed 9 Nov. Customers chips: All / Losing money / Under 45% margin. The overview "Losing money" card opens Customers already filtered. |
| 13 | Keyboard shortcuts | ➖ Phone-first; tabs are real buttons, so Tab + Enter works. |
| 14 | Tier-based UI indicators | ✅ Fixed 9 Nov. "Growth plan" label on margin per customer and the evidence pack, matching the landing pricing; landing shows all 4 tiers with prices. |
| 15 | Onboarding data capture | ✅ A203: landing X-ray form (company, work email, export file) with plain DPDP consent, checks on blur, success / failure with Retry, offline message (`design/intake.js`, `tests/test_intake_form.py`). |
| 16 | Referral / affiliate | ➖ Pre-launch; no referral offer yet. |
| 17 | Custom 404 | ➖ Not a public site yet; the landing's 404 is part of its SEO checks (A192). |
| 18 | Mobile-optimised layout | ✅ 390 px light + dark, no sideways scroll. Fixed 9 Nov: logo link and FAQ rows were 28–30 px tall, now 44 px. |
| 19 | Destructive action protection | ➖ No delete, cancel or send actions. |
| 20 | Graceful error recovery | ✅ Fixed 9 Nov. Bad or missing data shows "Couldn't read your usage data. Your files are safe; nothing was changed or sent." with a Retry button, never a blank page. |

Also fixed: `test_design.py` skipped the whole 390 px check on *any* error (so a failing check looked like "browser missing"); it now skips only when Chromium itself can't start.

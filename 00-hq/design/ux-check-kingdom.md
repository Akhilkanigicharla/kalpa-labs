# UX check: Kingdom game (artifact MdD3R2kEYP4qHDXXvbsJF1, `kingdom-control-room.html`) · 9 Nov 2026

Against `00-hq/design/UX-PATTERNS.md`. Internal, one user (Akhil), phone first. Akhil marks quests Not started / In progress / Done; saves go to the artifact database.
Tests (all PASS, 390 px light + dark): `test_kingdom_ux.py` (new, A189: tap sweep on all 5 tabs + failed-save rollback), `kingdom-launch.test.js` (row count now read from check.py), `kingdom-streak.test.js`.
Run: `python3 00-hq/design/test_kingdom_ux.py`.

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | ✅ Fixed 9 Nov: the new status shows at once; if the save fails it goes back and the toast says "Couldn't save, so it's back as it was. Try again." (test proves it fails without the fix). |
| 2 | Skeleton loaders | ➖ Quests and worlds are inside the page and draw at once; live saves arrive on top. |
| 3 | Command palette | ➖ 5 tabs on a phone bottom bar. |
| 4 | Persistent navigation | ✅ Same 5 tabs everywhere: top on laptop, bottom bar on phone. |
| 5 | Loading and empty states | ✅ "No messages yet…" on the team board; the live dot says "Offline · changes won't save" when the database is not there. |
| 6 | Autosave | ✅ Each status tap saves straight away; no long forms. |
| 7 | Debouncing | ➖ No search or live checks. |
| 8 | Throttling | ✅ Status buttons are disabled when saving is not allowed (view only); each tap sets a value, so a double tap gives the same result. |
| 9 | Smart form validation | ➖ No forms. |
| 10 | Bulk actions | ➖ Quests are done one at a time on purpose (each has its own check). |
| 11 | Reusable data table | ➖ No tables; lists and cards. |
| 12 | Advanced filtering | ✅ Agents tab filters by status (All / Live code / Claude / Needs you / Planned) with counts; units filter by world. |
| 13 | Keyboard shortcuts | ✅ Enter/Space open islands and quests on the map. Laptop-only extra shortcuts not needed for a phone game. |
| 14 | Tier indicators | ➖ Internal, no paid tiers. |
| 15 | Onboarding capture | ➖ One known user. |
| 16 | Referral / affiliate | ➖ Internal. |
| 17 | Custom 404 | ➖ claude.ai serves the page; no other routes. |
| 18 | Mobile layout | ✅ Fixed 9 Nov: tab bar (37 px), "See all messages" (34 px), quest rows (37–39 px), world chips (37 px), Agents filters (25 px) and status buttons (42 px) all now ≥ 44 px; list items no longer hide under the bottom bar when scrolled to (scroll padding). Sweep of all 5 tabs: 0 problems. |
| 19 | Destructive action protection | ✅ Nothing is deleted; any status change is one tap to undo (tap the old status again). |
| 20 | Graceful error recovery | ✅ Failed save: rolled back + plain message + try again (row 1); offline is shown in the header. |

Live page: the fixes are in the repo file; the published artifact updates when the page is next republished.
SEO: not relevant (private claude.ai artifact).

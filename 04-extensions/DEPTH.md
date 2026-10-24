# Tab Lifeboat: feature by feature (A90 / A105 gap map)

Checked 24 Oct 2026 against the offer in `PLAN.md` §2. Evidence = code + the test that proves it.
Tests: `npm test` (34 unit), `npm run test:e2e` (18 checks in real Chromium), `test:screens` (390 px + 1280 px, light + dark), `test:store`.

| Feature | Plan | Status | Code | Proof |
|---|---|---|---|---|
| Save all tabs / windows / tab groups in 1 click, named | Free | ✅ built | `lib/capture.ts`, popup | e2e "saved 5 tabs, 1 group" |
| Rename a saved session | Free | ✅ built 24 Oct | background `rename`, options | e2e "rename saved" |
| Search session names | Free | ✅ built | options `#q` | screens |
| **Search every saved tab by title or address** | Free | ✅ built 24 Oct | `lib/tools.ts searchTabs`, options "Find a tab" | unit + e2e "search finds a saved tab" |
| Restore with tab group names and colours | Free | ✅ built | `lib/capture.ts restore` | e2e "group restored" |
| Import from OneTab and Session Buddy (v3, v4) | Free | ✅ built | `lib/importers.ts` | unit, 1,000-tab fixtures |
| Auto-snapshots every 5 min (Free keeps last 3) | Free | ✅ built | background alarm, `pruneAuto` | e2e + unit |
| Pro: 90-day snapshot history | Pro | ✅ built (needs licence) | `pruneAuto("pro")` | unit |
| Manual backup file + restore from file | Free | ✅ built | `lib/backup.ts` | unit + screens round trip |
| **Pro: backup file every day, saved by itself** | Pro | ✅ built 24 Oct (to Downloads/Tab Lifeboat, optional `downloads` permission) | background `dailyBackup` | unit `backupDue`; e2e needs a Pro licence + a download prompt, so it's covered by the unit test only |
| Pro: daily backup to **your own Google Drive** | Pro | ⛔ blocked: needs a Google Cloud OAuth client (`drive.file`) that Akhil creates | — | — |
| **Pro: close duplicate tabs + tabs unused for 7 days, with undo** | Pro | ✅ built 24 Oct; saves "Before cleanup" first | `findDuplicates`, `findStale`, background `cleanup` | unit + e2e "duplicate closed", "'Before cleanup' first" |
| **Pro: "where did this tab go?" timeline** | Pro | ✅ built 24 Oct | `tabTimeline`, options | unit + e2e "timeline finds /b" |
| **Honest upgrade nudge after a big import** (once a week, free users, no popups) | Sell | ✅ built 24 Oct | `upgradeNudge` | unit |
| Pro licence key check (signed, offline) | Sell | ⛔ blocked (A53): needs the payment provider (C54) | — | — |
| Edge build | Ship | ✅ same Chrome MV3 package | `.output/chrome-mv3` | — |
| Firefox build | Ship | 🟡 builds (`npm run build:firefox` → firefox-mv2, 24 Oct); not run-tested in Firefox yet → A111 | — | build log |
| Store listing, screenshots, privacy form | Ship | ✅ built (A40); `downloads` justification added 24 Oct | `store/` | `test:store` |

**Still to do for A105:** the Firefox build test (A111), then the two blocked items once Akhil's accounts exist: the licence check (A53, after C54) and Google Drive (needs a Google Cloud OAuth client; free, Akhil makes it).

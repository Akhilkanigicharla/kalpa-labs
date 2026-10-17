# Tab Lifeboat screens: design brief (A13)

**Who:** someone with 50–1,000 tabs who once lost them to an update, a crash or a "helpful" cleanup (the OneTab, Session Buddy and Tab Session Manager reviews in `research/deep-scan-v2.md`). They open the popup for one click. They open the options page only when they're worried, so that page's first job is to show their tabs are safe.

**Built as the real extension, not mockups** (WXT, plain CSS on the Kalamkari tokens, world colour `--l4` plum):

| Screen | File | Job |
|---|---|---|
| Popup | `src/entrypoints/popup/` | Save all tabs (never closes anything), "Last snapshot N min ago", saved list with Restore / Delete, OneTab / Session Buddy import, link to **Backups and settings** |
| Options (full tab) | `src/entrypoints/options/` | 1. **Proof:** last auto-snapshot, sessions, tabs. Says whether Chrome has marked storage persistent. 2. Snapshot rules (Free last 3, Pro 90 days, from `LIMITS`). 3. **Backup file:** download one JSON with every session; restore from it with a preview first, safe to repeat. 4. Import. 5. Searchable saved sessions. 6. Pro, honestly marked "opens soon", PLAN prices, a licence key, not a subscription. 7. Privacy |

## New engine behind the options page: the backup file (free, research gap 7)
`src/lib/backup.ts` (tests in `tests/backup.test.ts`):
- `toBackup` / `parseBackup` round-trip every session, group name, colour and collapsed state.
- **Restoring the same file twice adds nothing**: ids are kept, so restore overwrites instead of duplicating.
- Unsafe links (`file:`, `javascript:`, `data:`) are dropped and counted.
- A wrong file or a newer-version file is refused in plain English.
- 10,000 tabs parse in well under a second.
- File name: `tab-lifeboat-backup-YYYY-MM-DD.json` (IST date).

Auto-snapshot names are now "17 Oct, 8:46 pm" instead of the US "10/17/2026, 8:46:33 PM".

## Research applied
- **Deep Scan v2 gaps:**
  - #1 proof that backups happen (shown first on the options page);
  - #2 storage survives low disk (persist status shown);
  - #5 imports with a preview;
  - #7 a backup file the user owns.
- **Chrome extension UI guidance** (pproenca chrome-extension-ui rules):
  - the popup's main action is obvious and renders at once;
  - options open in a tab (`open_in_tab`);
  - sensible defaults;
  - full keyboard use with visible gold focus rings, and labels on icon-only actions.
- **PLAN.md:** the offer table (what's Free vs Pro) and the price ladder ($19 founding / $12 yearly / $29 lifetime; ₹899 / ₹499 / ₹1,199).

## Check
`cd 04-extensions/src && npm run test:screens` builds the extension, loads it in Chromium and does three things:
1. Seeds real sessions, then exports, deletes one, and restores twice (no doubles). It also checks that a wrong file is refused.
2. Screenshots the popup and the options page at 390 px (options also at 1280 px), light and dark, checking no sideways scroll, Rozha One loaded from the bundle and button heights.
3. Checks that the popup link opens the options tab.

PNGs go to `04-extensions/design/screens/` (not in git). The same command runs in the `tab-lifeboat` CI job.

## Next (not in this item)
- **A40 (E9 + E10):** store screenshots can reuse these screens; privacy page.
- **E13 (Pro):** daily Drive backup reuses `toBackup()` as its file format.

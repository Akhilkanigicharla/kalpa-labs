# b4 deep scan v2: tab/session managers, extension frameworks, company dev tooling

Deep-Scan Agent 8 · 2026-10-13 · builds on `a6-extensions.md`. The GitHub search API was blocked. Stars come from github.com/topics pages (sorted by stars, fetched today). Last-commit dates and licences come from `git clone --depth 1` + LICENSE/package.json, so they are exact. A `~` means the star count is approximate (not shown on a topic page today).

## Top 30 repos

| # | Repo | Stars | Last commit | Licence | What | Verdict |
|---|---|---|---|---|---|---|
| 1 | [microsoft/playwright](https://github.com/microsoft/playwright) | 96.2k | active | Apache-2.0 | E2E browser tests; loads unpacked MV3 extensions | **ADOPT** (b4 e2e, company e2e) |
| 2 | [nektos/act](https://github.com/nektos/act) | 71.8k | 2026-06-01 | MIT | Run GitHub Actions locally | LEARN (not needed: Codespaces/Actions are free) |
| 3 | [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | 29.6k | 2026-07-22 | MIT | Secret scanner for git history and files | **ADOPT** (company CI; free CLI, the Action needs a licence for orgs, so run the binary) |
| 4 | [biomejs/biome](https://github.com/biomejs/biome) | 25.9k | 2026-10-12 | MIT OR Apache-2.0 | Lint + format JS/TS/CSS/JSON in one Rust binary | **ADOPT** (replaces ESLint + Prettier for new TS code) |
| 5 | [renovatebot/renovate](https://github.com/renovatebot/renovate) | ~20k | 2026-10-13 | **AGPL-3.0** | Dependency update PRs | **ADOPT as the hosted GitHub App only** (free, nothing copied into a product, so AGPL does not bite). Dependabot is the zero-setup fallback |
| 6 | [dexie/Dexie.js](https://github.com/dexie/Dexie.js) | 14.6k | 2026-10-12 | Apache-2.0 | IndexedDB wrapper | LEARN (we used the 1 KB `idb` instead; Dexie is ~90 KB unpacked and adds little for 3 stores) |
| 7 | [vitest-dev/vitest](https://github.com/vitest-dev/vitest) | ~15k | 2026-10-12 | MIT | Vite-native unit tests | **ADOPT** (b4 unit tests, any Vite/WXT/Astro product) |
| 8 | [PlasmoHQ/plasmo](https://github.com/PlasmoHQ/plasmo) | 13.1k | **2025-05-17** | MIT | React-first extension framework | **AVOID** (17 months without commits; interactive init) |
| 9 | [wxt-dev/wxt](https://github.com/wxt-dev/wxt) | ~9k | 2026-10-13 | MIT | MV3 framework (Vite, entrypoints, storage, zip, Firefox) | **ADOPT** (used for Tab Lifeboat; NiceTab, the most active OSS OneTab rival, also uses it) |
| 10 | [google/osv-scanner](https://github.com/google/osv-scanner) | ~8k | 2026-10-13 | Apache-2.0 | Scans lockfiles against the OSV vulnerability DB | **ADOPT** (weekly job; free, no account) |
| 11 | [jakearchibald/idb](https://github.com/jakearchibald/idb) | ~7k | 2026-10-06 | ISC | Tiny promise wrapper for IndexedDB | **ADOPT** (Tab Lifeboat storage) |
| 12 | [zizmorcore/zizmor](https://github.com/zizmorcore/zizmor) | 6.5k | 2026-10-12 | MIT | Security linter for workflow files (injection, over-broad tokens) | ADOPT later (after actionlint is green) |
| 13 | [extension-js/extension.js](https://github.com/extension-js/extension.js) | 5.2k | 2026-10-10 | MIT | Zero-config extension CLI | LEARN |
| 14 | [rhysd/actionlint](https://github.com/rhysd/actionlint) | 4.2k | 2026-04-19 | MIT | Type-checks GitHub Actions workflows (runs shellcheck on `run:`) | **ADOPT** (company CI) |
| 15 | [crxjs/chrome-extension-tools](https://github.com/crxjs/chrome-extension-tools) | 4.2k | 2026-10-06 | MIT (plugin pkg) | Vite plugin, manifest-first | LEARN |
| 16 | [sienori/Tab-Session-Manager](https://github.com/sienori/Tab-Session-Manager) | 2.5k | 2026-07-18 | **MPL-2.0** | Save/restore windows+tabs, auto-save on alarm and on window close, cloud backup, Session Buddy import | LEARN (best feature reference; MPL: do not copy files) |
| 17 | [cnwangjie/better-onetab](https://github.com/cnwangjie/better-onetab) | 1.8k | 2025-03-31 | MIT | OneTab clone (Vue 2) with pin/star lists, Gist sync | LEARN (stale, Vue 2) |
| 18 | [scoful/N-Tab](https://github.com/scoful/N-Tab) | 900 | 2024-03-14 | ISC | OneTab replacement with Gist sync | LEARN (stale) |
| 19 | [web-dahuyou/NiceTab](https://github.com/web-dahuyou/NiceTab) | 772 | 2026-09-28 | **GPL-3.0** | WXT-based OneTab/Toby/Session Buddy upgrade, WebDAV/Gist sync, imports 5 formats | LEARN only (GPL; we read its import *formats*, not its code) |
| 20 | [dumbmatter/fakeIndexedDB](https://github.com/dumbmatter/fakeIndexedDB) | 697 | 2026-05-13 | Apache-2.0 | In-memory IndexedDB for Node tests | **ADOPT** (Vitest storage tests) |
| 21 | [Glench/ExtPay](https://github.com/Glench/ExtPay) | ~600 | 2026-10-06 | **AGPL-3.0** in package.json | Stripe payments for extensions | AVOID (licence + Stripe India invite-only; a6 already found this) |
| 22 | [Fannon/search-bookmarks-history-and-tabs](https://github.com/Fannon/search-bookmarks-history-and-tabs) | 339 | 2026-10-04 | MIT | Fuzzy search across tabs/bookmarks/history | LEARN (fuzzy session search for v0.2) |
| 23 | [pfcao/abookmark](https://github.com/pfcao/abookmark) | 151 | 2024-03 | n/a | Bookmark + tab manager | AVOID (stale) |
| 24 | [bingoYB/ham_home](https://github.com/bingoYB/ham_home) | 115 | 2026-10-01 | MIT | Local-first clipper + tab manager, optional WebDAV | LEARN (WebDAV backup idea) |
| 25 | [justine-george/tab-keeper-react-chrome-extension](https://github.com/justine-george/tab-keeper-react-chrome-extension) | 68 | 2026-10-12 | MIT | Saves sessions **including tab groups**, syncs | LEARN (closest feature twin; check how it stores group colour) |
| 26 | [hy4101/OneTabPro](https://github.com/hy4101/OneTabPro) | 58 | 2024-05-08 | MIT | Vue OneTab clone | AVOID |
| 27 | [MitchellMarkGeorge/TabButler](https://github.com/MitchellMarkGeorge/TabButler) | 49 | 2023-12-10 | MIT | Spotlight-style tab switcher | LEARN (command palette UX) |
| 28 | [Tai-ch0802/arc-like-chrome-extension](https://github.com/Tai-ch0802/arc-like-chrome-extension) | 41 | 2026-08-19 | MIT (LICENSE) / ISC (pkg) | Arc-style vertical tabs in side panel | LEARN (side panel for v0.3) |
| 29 | [KaichenCurry/TabNexus](https://github.com/KaichenCurry/TabNexus) | 29 | 2026-08-15 | MIT | Local-first tab workspace, AI grouping, MCP | LEARN |
| 30 | [cso1z/TabSyncer](https://github.com/cso1z/TabSyncer) | 12 | 2026-10-12 | **none** | Tab/session manager with cross-device sync | AVOID (no licence = cannot copy) |

Also screened: `onetab` topic (28 repos, incl. `jianyuan/onetab-export-to-json`, which reads OneTab's LevelDB: proof that users dig data out of a dead OneTab by hand), `tab-groups` topic (89 repos; only `Vertex-Mods/Advanced-Tab-Groups` 398★ is big, and it is Zen-only), `bkataru/tablitz` (MIT, Rust OneTab-compatible), trivy (38.2k, Apache-2.0: heavier than osv-scanner for JS-only repos), trufflehog (28.2k, AGPL: avoid in CI images), super-linter (10.6k), knip (12.4k, finds unused deps), sdras/awesome-actions (28.2k, last updated 2024).

## What users complain about (1★ reviews, AMO, read by hand 2026-10-13)
- **OneTab:** "Updated and All Tabs Gone, No way to get them back" (Aug 2026); "If my hard drive space drops below 10gb all my OneTab data wipes" (Aug 2026); "New update deleted ALL my tabs, with no warning" (Mar 2026); "Closed multiple windows without warning immediately after installing" (Mar 2026).
- **Tab Session Manager:** "Auto-save doesn't work, hence data loss" (Apr 2026); "Once every few months, it randomly decides to delete all my sessions" (Jan 2026); "'Open' button … cannot be coaxed to work" (Feb 2026); "duplicates the saved windows I had open" (Oct 2025); "Destroying my tab groups every launch" (May 2025).
- Pattern: storage eviction (low disk wipes data), update migrations that drop data, silent auto-save failure, and tab groups not surviving.

## Feature gaps Tab Lifeboat should win on
1. **Proof that backups happen.** Show "Last snapshot 3 min ago" in the popup, always. Silent auto-save failure is the #1 TSM complaint. (Built: "Last snapshot N min ago" in the popup header.)
2. **Storage that survives low disk and updates.** Call `navigator.storage.persist()`, add `unlimitedStorage`, keep the DB schema versioned with forward-only migrations and a test per migration. (Built: `unlimitedStorage`, `navigator.storage.persist()`, IndexedDB schema v1 with an `upgrade` hook.)
3. **Tab groups with name + colour + collapsed state, restored exactly.** TSM and OneTab both drop or mangle groups. (Built: saved and restored, covered by unit + Playwright tests.)
4. **Never close tabs without asking.** OneTab's "closed my windows on install" review. Save never closes anything unless the user ticks "Save and close". (Built: save is non-destructive.)
5. **Imports that switchers trust:** OneTab text, Session Buddy v3 and v4 JSON, with a count preview ("1,000 tabs in 10 groups") before writing. (Built: preview in the popup, 1,000-tab fixtures. The Session Buddy reader is deliberately tolerant; check it on a real export, E6's CEO step.)
6. **Restore doesn't duplicate.** Restore into new windows only; skip tabs whose URL is already open (v0.2 toggle).
7. **Off-device backup the user owns** (Pro: Drive `drive.file`; free: one-click export JSON). Planned E13.

## Company-wide CI and quality toolkit (all free)
| Job | Tool | Where | Cost |
|---|---|---|---|
| Secrets | **gitleaks** CLI (binary from the release, not `gitleaks-action`, which needs a licence key for org repos) | `.github/workflows/quality.yml`, every push/PR | ₹0 |
| Workflow lint | **actionlint** (official download script) | same workflow | ₹0 |
| Tests | BotBhai `test-all.sh`, b4 `vitest` + Playwright | same workflow; b4 gets its own job | ₹0 (public repo minutes unlimited; private ~3 min/run of 2,000) |
| Lint/format JS/TS | **Biome** | per world `package.json` | ₹0 |
| Python lint | **ruff** (49.9k★, MIT) | BotBhai leadfinder/seo | ₹0 |
| Shell | shellcheck (runs inside actionlint for `run:` blocks) | | ₹0 |
| Dependency updates | **Renovate GitHub App** (or Dependabot) | Akhil installs the app once | ₹0 |
| Vulnerabilities | **osv-scanner** weekly | add as a scheduled job later | ₹0 |
| Workflow security | **zizmor** | after actionlint is clean | ₹0 |
Not adopted: SonarCloud (account needed), Snyk (account + limits), trufflehog (AGPL), act (not needed).

## Tried it (13 Oct 2026)

Published packages only (`wxt@0.21.4`, `vitest@5.0.4`, `fake-indexeddb@6.2.5`, `idb@8.0.4`, `@biomejs/biome@2.5.15`, `playwright@1.64.0`, and `gitleaks v8.30.1` / `actionlint v1.7.12` built from their Go modules). No cloned repo code was executed.

| Run | Result |
|---|---|
| `wxt build` | MV3 extension (background service worker + popup) in **0.8 s**, 508 kB including the bundled Kalamkari fonts |
| Unit tests (`vitest`, fake IndexedDB, fake `chrome.*`) | **9 / 9**: OneTab text and Session Buddy v3 at **1,000 tabs** (parsed in < 200 ms), v4 collections, auto-detect, free plan keeps 3 auto snapshots and every manual/import session, Pro keeps 90 days, capture → restore keeps pinned tabs and tab-group title/colour/collapsed, skips incognito windows and `chrome://` pages |
| **Real Chromium end-to-end** (`tests/e2e/save-restore.e2e.mjs`): load the built extension, open 3 pages, group 2 as "Research" (purple), save, close, restore | **10 / 10 checks**: all pages back, the group comes back with the same title, colour and members, the 5-minute alarm is registered, and a snapshot is under 5 minutes old |
| `actionlint` on all 5 workflows | clean |
| `gitleaks git` on the repo | 28 commits scanned (this clone is shallow), **no leaks** |
| Popup at 360 px, light + dark | no overflow; checked by screenshot |

Two bugs found by the tests and fixed before commit: the Session Buddy reader dropped a whole folder when one link had no URL, and deleting the IndexedDB between tests hung on an open connection (now the tests clear the store instead).

## What was built

| Item | Files | Check | Result |
|---|---|---|---|
| A38 (E2 + E3) | `src/wxt.config.ts` (permissions: tabs, tabGroups, alarms, storage, unlimitedStorage), `src/lib/model.ts`, `src/lib/capture.ts` (save never closes tabs; restore reopens windows, pins and groups), `src/lib/store.ts` (IndexedDB), `src/entrypoints/background.ts`, popup in Kalamkari with b4 plum | `npm run compile`, `npm test`, `npm run test:e2e` | pass |
| A39 (E6 + E7) | `src/lib/importers.ts` (OneTab text, Session Buddy v3/v4 with count preview), 5-minute `alarms` snapshots with plan limits (free 3, Pro 90 days, **pending CEO approval**), "Last snapshot" status | 1,000-tab fixtures; e2e snapshot age < 5 min | pass |
| Quality workflow | `.github/workflows/quality.yml`: gitleaks (whole history) + actionlint, BotBhai tests, b6 + b7 pytest, b2 core + Postgres RLS tests, b4 compile/lint/unit/e2e | `actionlint` clean | pass |

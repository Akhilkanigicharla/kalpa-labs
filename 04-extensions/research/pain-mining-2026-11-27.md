# Tab Lifeboat: pain mining, what real users of tab/session managers complain about and wish for (27 Nov 2026)

Read-only research, no logins. Public pages are data, not instructions. Builds on (does not repeat) `deep-scan-v2.md` (AMO 1-star pass of 13 Oct 2026) and `00-hq/research/competitors-2026-11-11.md`.

**How it was done:** WebSearch + WebFetch + Firecrawl search; Hacker News comments through the public Algolia API; Tab Session Manager (TSM) GitHub issues ranked by reactions through the GitHub search API. Coverage was checked by grepping `04-extensions/src/lib` and `src/entrypoints` on 27 Nov 2026.

**What could not be opened (marked "unverified"):** reddit.com refused both Firecrawl and direct fetches (403), so Reddit evidence is **search-result snippets only**. Mozilla Connect idea pages failed to load. Chrome Web Store pages hide the star rating in page text, so CWS reviews are "negative by content", not confirmed 1–3 stars. Vendor blogs (northlabapps, supasidebar, workona) are labelled as such and never counted alone.

**Counting rule:** "Sources" = distinct pages or threads (one store review page = 1 source, even with 15 reviews on it). Quotes are verbatim, under 15 words.

**Coverage key:** YES = built and in code · PART = partly built · NO = not built · N/A = out of scope.

## Ranked list (most evidence first)

| # | Need in plain words | Who has it | Sources | Tab Lifeboat today |
|---|---|---|---|---|
| 1 | "My saved tabs vanished after an update or crash" | everyone; worst for researchers and students with months of tabs | 14 | YES (core) |
| 2 | "The browser lost my windows/groups after a restart or OS update" | everyone, Edge and Chrome users, ChromeOS | 7 | YES (core) |
| 3 | "Auto-save silently stopped and I only found out when I needed it" | heavy users | 5 | PART |
| 4 | "Tab groups don't come back with their names and colours" | Chrome/Edge/Firefox group users, devs | 5 | YES on Chrome; Firefox unverified |
| 5 | "Restoring a big session freezes or crashes the browser, or Open does nothing" | tab hoarders (hundreds to thousands of tabs) | 5 | YES |
| 6 | "Let me keep my own backup file; don't lock me in" | privacy-minded, switchers | 7 | YES (JSON); PART (no plain-text export) |
| 7 | "No account, no paywall that holds my tabs hostage" | solo users, students | 6 | YES |
| 8 | "Never close or overwrite my open tabs without asking" | everyone, ADHD | 5 | YES |
| 9 | "Restore opens duplicates of tabs I already have" | daily restorers | 4 | PART |
| 10 | "Find one tab across all my saved sessions" | researchers, ADHD, devs | 5 | YES (options page); not in popup |
| 11 | "Edit a saved session: move, merge, remove one tab, add this tab" | power users, researchers | 3 (≈80 GitHub reactions) | NO |
| 12 | "Same tabs on my other computer / other browser" | multi-device workers, devs | 6 | PART (Drive backup restore, Pro) |
| 13 | "Don't harvest my data" / "encrypt it client-side" | privacy-minded | 5 | YES local; PART for Drive |
| 14 | "Free my memory: save and close, like OneTab" | low-RAM laptops, tab hoarders | 5 | NO (by design: save never closes) |
| 15 | "Help me review old tabs gently, don't auto-delete them" | ADHD, tab hoarders | 4 | PART (Pro stale cleanup) |
| 16 | "Keep the UI simple; don't redesign away features I use" | long-time users | 5 | YES (simple); a rule, not a feature |
| 17 | "Save only this window, or only the tabs I pick" | devs, project-based workers | 2 (≈20 reactions) | NO |
| 18 | "Show the exact date and time a session was saved" | everyone | 2 | YES |
| 19 | "Is this extension still maintained? Will it break next update?" | everyone after Great Suspender / TSM decay | 4 | N/A (trust signal) |
| 20 | "Show my open-tab count on the icon" | tab hoarders | 2 | NO |
| 21 | "Quick save from right-click menu or a keyboard shortcut" | power users | 2 | NO |
| 22 | "Import a plain list of URLs" | switchers | 2 | YES |
| 23 | "Dark mode / follow system theme" | everyone | 1 (18 reactions) | YES |
| 24 | "Works on my phone" | Android users | 3 | N/A (Chrome Android has no extensions) |

## Evidence per item

**1. Saved tabs vanish after update or crash (14 sources)**
- OneTab AMO 1-star page: "Newest update wiped years of accumulated tabs." (29 Mar 2026); "Still having catastrophic data loss every few months." (16 Jun 2026); 15 data-loss reviews on page 1 alone. https://addons.mozilla.org/en-GB/firefox/addon/onetab/reviews/?score=1
- Session Buddy forum, 6 separate threads on v4 losing collections, e.g. "This update completely destroyed all my old sessions" (thread title). https://groups.google.com/g/sessionbuddy-discuss/c/GdHHk0WxBcM · https://groups.google.com/g/sessionbuddy-discuss/c/PHCXJD6Leo0 · https://groups.google.com/g/sessionbuddy-discuss/c/6PzI4V30L7A · https://groups.google.com/g/sessionbuddy-discuss/c/x-511JK39tM (BSOD, Sep 2025)
- Session Buddy CWS: "I lost years worth of data on every profile" (Jul 2024). https://chromewebstore.google.com/detail/session-buddy/edacconmaakjimmfgnblocblbcdcpbko/reviews
- Workona AMO 1-star: "Lost my work and tabs when moving tabs from one space" (Nov 2023). https://addons.mozilla.org/en-US/firefox/addon/workona/reviews/?score=1
- OneTab CWS: "Made me loose 2/3 of my tabs" (Jul 2024). https://chromewebstore.google.com/detail/onetab/chphlpgkkbolifaimnlloiipkdnihall/reviews
- Chrome's own archived tabs auto-deleted: "suddenly they've all disappeared without warning" (5 Dec 2025). https://www.androidenterprise.community/discussions/chromeos-general/chrome-recently-deleted-all-my-archived-tabs-without-warning-had-i-been-notified/13829
- The Great Suspender removal closed users' suspended tabs (XDA, 4 Feb 2021). https://www.xda-developers.com/google-chrome-the-great-suspender-malware
- Reddit r/chrome "I lost all my sessions from the past several months" (title; snippet only, **unverified**). https://www.reddit.com/r/chrome/comments/1h4inxc/
- **Coverage YES:** 5-min auto snapshots, `unlimitedStorage` + `navigator.storage.persist()`, 7-day Recently deleted (`store.ts` TRASH_DAYS), free JSON export, Pro Drive backup. **Lesson:** a vendor's update is the #1 killer. Every Tab Lifeboat DB migration needs a test with a real large dataset, and an automatic export before any schema change.

**2. The browser lost windows/groups on restart (7)**
- Edge Q&A: "I lost an entire window full of grouped tabs" (Oct 2023, replies to Aug 2025); moderator: "no feature yet to restore tab groups as a whole". https://learn.microsoft.com/en-sg/answers/questions/1406549/restoring-lost-missing-tab-groups
- Chromium discuss: windows gone after a hard reboot with a pending update (Dec 2020). https://groups.google.com/a/chromium.org/g/chromium-discuss/c/05NDc-pkwCY
- Chrome Unboxed: "Tab Groups are not synced to the browser – only to the active session!" (Jan 2023). https://chromeunboxed.com/chrome-tab-groups-delete-themselves-after-quit
- MS Tech Community "Loses all open tabs on update" and "Deleted tabs and windows from update" (titles; snippet only). https://techcommunity.microsoft.com/t5/discussions/loses-all-open-tabs-on-update/m-p/1970508
- r/firefox "I lost all my saved tab groups." (snippet only, **unverified**). https://www.reddit.com/r/firefox/comments/1tpkqc0/
- **Coverage YES.** This is the "lifeboat" story: put the Edge moderator's line in store copy as the problem statement.

**3. Auto-save silently stopped (5)**
- TSM AMO 1-star: "the last save it had was from over a year ago!" (16 Jan 2026); "Auto-save doesn't work, hence data loss" (Apr 2026). https://addons.mozilla.org/en-US/firefox/addon/tab-session-manager/reviews/?score=1
- TSM GitHub #1384 "CRUCIAL BUG: Autosave session stopped working" (Aug 2024). https://github.com/sienori/Tab-Session-Manager/issues/1384
- Session Buddy: "it doesn't have any of those automatically saved collections listed" (Mar 2024). https://groups.google.com/g/sessionbuddy-discuss/c/zHRxAvuo9uI
- Session Buddy 4.1.0 auto-backup crashed Chrome daily: "Please add an option to disable this new" (Nov 2025). https://groups.google.com/g/sessionbuddy-discuss/c/feuKGnQHCUo
- **Coverage PART:** the popup shows "Last snapshot N min ago" (`popup/main.ts:66`). **Gap:** nothing warns when the last snapshot is old (e.g. over 30 min while the browser was open). Add a red state plus a badge "!", and test it.

**4. Tab groups not restored with name/colour (5)**
- TSM GitHub, most-reacted issues of all time are about groups: #1493 "Firefox tab groups do not get saved or restored" (26 reactions), #1480 (22), #1445 (17), #1533 (16), #1466 (14). https://github.com/sienori/Tab-Session-Manager/issues/1493
- HN: OneTab export "doesn't carry over the tab group titles" (Mar 2022). https://news.ycombinator.com/item?id=30663600
- Edge Q&A (above): group names lost after restore.
- **Coverage YES on Chrome** (`capture.ts` saves title/colour/collapsed; unit + Playwright tests). **Firefox unverified:** `build:firefox` exists, but group restore has not been tested on Firefox 138+. That is the biggest open demand in TSM's own tracker.

**5. Big restores freeze or crash; Open does nothing (5)**
- TSM AMO: "'Open' button for saved tabs cannot be coaxed to work" (Feb 2026), plus 3 more "Open" reviews; "repeatedly crashes and takes the browser with it" (Jun 2025).
- Session Buddy CWS: "crashes chrome anytime i try to restore a session buddy group" (Jul 2024).
- Session Buddy forum: 3,000 sessions, "the tab ran out of memory" (Nov 2025). https://groups.google.com/g/sessionbuddy-discuss/c/feuKGnQHCUo
- Tabs Outliner CWS: "Does not open tabs now" (Nov 2024). https://chromewebstore.google.com/detail/tabs-outliner/eggkanocgddhmamlbiijnphhppkpkmkl/reviews
- **Coverage YES:** sessions over 15 tabs open asleep, 6 loading at a time (`capture.ts` LAZY_AT / LOADING), discard only after load. **Gap:** test with a 3,000-session / 1,000-tab store for popup and export memory (Session Buddy's crash case).

**6. My own backup file, no lock-in (7)**
- OneTab AMO: "the lack of FULL file export-import is a bummer" (Mar 2026).
- Toby CWS: "Hopefully there's a way to export my saved tabs" (Jun 2024). https://chromewebstore.google.com/detail/toby-tab-management-tool/hddnkoipeenegfoeaoibdmnaalmgkpip/reviews
- Partizion CWS: wants "any explicit local storage options"; "use my custom private server to back up" (2024). https://chromewebstore.google.com/detail/partizion-%E2%80%94-tab-and-sessi/ldimfpkkjopddckaglpeakpaepclcljn/reviews
- HN: exports sessions "as text (json actually, a little bit too verbose)" (Aug 2025). https://news.ycombinator.com/item?id=45049074
- Edge Q&A (Aug 2025): a user asks for export/import of tab group definitions.
- Vendor blog (northlabapps): calls local file export "non-negotiable".
- **Coverage YES** (free JSON backup + restore, `backup.ts`). **PART:** no human-readable export (plain-text / OneTab-format URL list or HTML). Cheap to add and it answers the HN "too verbose" point.

**7. No account, no paywall holding tabs hostage (6)**
- Toby CWS: "it has a habit of locking you out of your saved tabs/collections" (Jun 2024).
- Partizion CWS: "Locks you out of your account at the end of the free trial"; "requirement to sign in to use the extension" (2024).
- Trustpilot (Toby): "They went from a free model to an expensive paid model" (Feb 2025). https://www.trustpilot.com/review/gettoby.com
- Toby's own post: moved to paid plans, free users moved to a capped Starter plan (5 Oct 2024). https://www.gettoby.com/blog/an-open-message-to-our-toby-community
- Toby AMO: "Rather ask me for a one-time fee for a pro version" (Nov 2022). https://addons.mozilla.org/en-US/firefox/addon/toby-for-tabs/reviews/?score=1
- Workona AMO: "I can't even set up my account!" (Feb 2022).
- **Coverage YES:** no account; saving, restoring and export are free. **Rule for Pro:** if Pro lapses, every saved session stays readable, restorable and exportable. Write that in the store listing. A lifetime-licence option matches the "one-time fee" ask.

**8. Never close or overwrite my tabs (5)**
- OneTab AMO: "Closed multiple windows without warning immediately after installing" (Mar 2026; also in deep-scan).
- Workona AMO: "It overwrote all the currently open tabs" (Oct 2025).
- Toby AMO: "Toby closes all the tabs and shows a blank page" (Sep 2023).
- dev.to (tab-hoarder essay): past tools that auto-closed tabs "broke that trust". https://dev.to/alogach/87-tabs-open-i-cant-close-any-of-them-5cl1
- **Coverage YES:** "Saving never closes your tabs" (`popup/index.html:14`); restore opens new windows only; cleanup saves "Before cleanup" first and asks.

**9. Duplicates on restore (4)**
- TSM AMO: "this add-on just duplicates the saved windows I had open" (Oct 2025); "Es öffnet die Tabs doppelt" (Nov 2025).
- Workona AMO: "caused tabs to get duplicated like wildfire" (Dec 2024); "It create duplicate tabs" (Jun 2025).
- **Coverage PART:** `restore()` re-opens every tab even if it is already open (only non-web URLs are skipped). Pro "close duplicates" fixes it afterwards. **Gap:** "Skip tabs already open" on restore, default ON (planned as item 6 in deep-scan-v2, still not built).

**10. Search across saved sessions (5)**
- Session Buddy v4 thread: "Search before was simple but worked" (Mar 2024). https://groups.google.com/g/sessionbuddy-discuss/c/LZUhE5tSOHw
- TSM GitHub #971 "When searching in sessions, show only relevant tabs" (8 reactions).
- TSM AMO: "Can not find specific previous session." (Jul 2026).
- HN: recommends TSM because it lets you "tag and search" sessions (Oct 2026). https://news.ycombinator.com/item?id=50239137
- Vendor blog (supasidebar, ADHD): fast search as the top need.
- **Coverage YES** (`tools.ts` searchTabs, options page). **Gap:** no search box in the popup, where users look first. No tags.

**11. Edit sessions: move, merge, remove, add one tab (3 sources, ≈80 reactions)**
- TSM GitHub: #587 "Moving tabs between sessions" (13), #379 "Add a Single Tab to a Saved Session" (11), #458 "Add current tab to selected session" (10), #810 "Merging sessions" (8), #585 (8), #462 (7).
- OneTab CWS: "the ability to move entire tabs (multiple links) into other onetabs" (Jul 2024).
- Session Buddy v4 thread: misses "the simple and quick X 1 click remove next to tabs" (Apr 2024).
- **Coverage NO:** only rename and delete whole sessions (`background.ts` cases). The most-voted non-Firefox feature cluster in TSM.

**12. Same tabs on another computer or browser (6)**
- HN: wants a session manager that is "cross-platform, cross-browser" (Mar 2025). https://news.ycombinator.com/item?id=43330270
- HN: "I'd prefer to have cross-device sync" (Mar 2022, OneTab user). https://news.ycombinator.com/item?id=30663600
- HN: TSM "can sync via Google Drive across different browsers" as the reason to pick it (Oct 2023). https://news.ycombinator.com/item?id=37891009
- TSM GitHub #819 "Sync settings to firefox sync" (12).
- r/firefox "Sessions between Chrome and FireFox?" (snippet only, **unverified**). https://www.reddit.com/r/firefox/comments/1gdn4xj/
- OneTab's developer promises "upcoming encrypted cloud sync" in AMO replies (2026).
- **Coverage PART:** Pro Drive backup (`drive.ts`, appdata) can be restored on another Chrome; no live sync; Firefox build untested.

**13. Privacy: don't harvest my data (5)**
- Workona AMO: "I wouldn't believe that this company isn't harvesting my data." (Feb 2022); "VERY SERIOUS CONFIDENTIALITY ISSUE" (Jan 2024).
- Toby AMO: "please en-/decrypt my data client side" (Nov 2022).
- Great Suspender was sold and removed as malware (XDA, 2021).
- Namecheap blog: "A tab manager that wants to read every page is asking for more than tabs." https://www.namecheap.com/blog/your-browser-extension-changed-owners-did-it-tell-you/
- **Coverage YES:** local only, no host permissions (`wxt.config.ts`: tabs, tabGroups, alarms, storage, unlimitedStorage; downloads/identity optional), incognito never stored. **PART:** Drive backup is gzip, not encrypted. Optional passphrase encryption would answer Toby's ask.

**14. Free memory: save and close (5)**
- OneTab CWS: "consistently takes about 450+ MB for its own process" (Jul 2024).
- HN: wants to "suspend long-unused tabs into a tree-style list" (Dec 2021). https://news.ycombinator.com/item?id=29524058
- HN: Auto Tab Discard let them keep "2755 tabs open without breaking a sweat" (Sep 2021). https://news.ycombinator.com/item?id=28684198
- Product Hunt: "I adore the feeling of closing all of them!!!" https://www.producthunt.com/discussions/how-many-tabs-are-too-many-tabs-suggest-a-tab-management-tool
- Great Suspender's removal left suspender users looking for a safe replacement (XDA).
- **Coverage NO** (deliberate). Option: an opt-in "Save and close this window" with a 10-second Undo, which keeps rule 8 intact.

**15. Gentle review of old tabs, never silent auto-delete (4)**
- dev.to: wants a "trustworthy moment of conscious review" (keep / snooze / close).
- Chrome archived-tabs thread: "Had I been notified to save them I would have" (Dec 2025).
- Product Hunt: wants to "start the day with some uncluttered context".
- Vendor blog (supasidebar): low-effort, time-boxed cleanup for ADHD.
- **Coverage PART:** Pro "tabs not used in 7 days" cleanup (`findStale`) saves first, then closes all at once. **Gap:** a one-by-one keep/snooze/close review would serve ADHD users better.

**16. Keep the UI simple; don't remove features (5)**
- Session Buddy v4: "So many useless changes crippling basic functionality." (Apr 2024).
- OneTab AMO: "center-alligned everything without an option to revert" (Mar 2026); "feels pretty clunky" (Aug 2026).
- Tabs Outliner CWS: "you have to double click on the tab you want" (Dec 2024).
- Vendor blog (northlabapps): TSM "interface is dense".
- **Coverage YES:** a simple popup. Make it a rule: never remove a shipped feature without a setting to keep it.

**17. Save only this window or picked tabs (2 sources, ≈20 reactions)**
- TSM GitHub #30 "save-session for this window only" (11), #14 "Select tabs to save as session" (8).
- Session Buddy v4: "Naming the session before saving option is gone." (Mar 2024).
- **Coverage NO:** `captureAll` saves every normal window. Naming happens later via Rename (options page); the popup has no name field.

**18. Exact save time (2)**
- Session Buddy v4: "Being able to see the time when the Collection(Session) was saved is very important." (Mar 2024).
- Session Buddy CWS: asks for "the time in 24-hour format" (Jul 2024).
- **Coverage YES:** names carry date and time (`stamp()`).

**19. Is it maintained? (4)**
- TSM AMO: "This extension is abandonware" (Oct 2026); "the lack of activity on Git" (Apr 2026).
- Tabs Outliner CWS: "extension is mostly abandoned at this point" (Jan 2025); "It breaks at least once a year".
- **N/A as a feature.** Show "Updated <date>", a public changelog and a support reply time on the site.

**20. Open-tab count on the icon (2)**
- Session Buddy v4: "Session Buddy icon showing the number of tabs open is gone".
- HN: "how do you see how many tabs you have open, an extension?" (Jun 2026). https://news.ycombinator.com/item?id=48736523
- **Coverage NO** (no `setBadgeText`). Tiny to add, and it could double as the stale-snapshot warning from item 3.

**21. Right-click or shortcut save (2)**
- Session Buddy v4: saving from the context menu was "a feature that was inexplicably removed"; "Right-click 'open to new tab' is also gone."
- **Coverage NO** (no `commands` or `contextMenus` in the manifest).

**22. Import a plain URL list (2)**
- Session Buddy CWS: "Feature for importing plain text was removed." and "import a list of plaintext URLs" (Jul 2024).
- **Coverage YES:** `parseOneTab` accepts bare URLs, one per line.

**23. Dark mode (1)** · TSM #211 "dark theme" (11), #761 "follow system theme" (7). **YES** (`prefers-color-scheme`).

**24. Phone (3)** · OneTab Android AMO: "it only offers to save one tab"; Workona AMO: "Workspaces dont work on android"; TSM #1097 Android sync. **N/A:** Chrome on Android has no extensions. Say so in the FAQ.

## What this means for Tab Lifeboat (no product change made; ideas for the roadmap, Akhil decides)
- The free core already answers the top 8 needs. The store listing should lead with them, quoting the problem (items 1, 2, 7, 8).
- Cheapest real gaps, in order: (a) stale-snapshot warning + icon badge (items 3, 20); (b) "skip tabs already open" on restore (9); (c) search box in the popup (10); (d) plain-text export (6); (e) save this window only + name at save (17); (f) keyboard shortcut / right-click save (21).
- Bigger Pro candidates backed by data: edit sessions (move, merge, add tab) (11); encrypted Drive backup (13); one-by-one review of old tabs (15); opt-in save-and-close (14).
- Firefox tab-group save/restore is the single most-voted ask in TSM's tracker (≈100 reactions over 6 issues). Worth one test run of `build:firefox` before claiming Firefox support.

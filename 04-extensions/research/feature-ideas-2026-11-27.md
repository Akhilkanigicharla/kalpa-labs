# Tab Lifeboat: new feature ideas (research, 2026-11-27)

Read-only research for b4 Tab Lifeboat. Not logged in anywhere. Every source below was fetched on 2026-11-27. Quotes are under 15 words; a few come from the fetch tool's extract of the page, so re-open the page before you reuse a quote in marketing. Vendor blogs (SuperchargeBrowser, SupaSidebar, TabFlow) sell rival products: treat their claims as weak and their user quotes as unverified.

Already built or planned (from `deep-scan-v2.md` and `PLAN.md`, not repeated here): non-destructive save, groups with colour and collapsed state, 5-minute snapshots, "Last snapshot N min ago", OneTab and Session Buddy import, `navigator.storage.persist()`, Drive `drive.file` backup (E13), licence gate (E8).

## 1. What changed in 2025-2026 (sets what is worth building)

| Fact | Source | What it means for us |
|---|---|---|
| Chrome now syncs saved tab groups across devices (announced Sep 2024). | [Google blog](https://blog.google/products/chrome/google-chrome-update-september-2024/): "save and sync tab groups" | Plain "save a group" is no longer a reason to install. Our edge is history, recovery, search and import. |
| Saved groups still vanish: delete or ungroup syncs everywhere, crashes and updates drop them. | [SuperchargeBrowser, Oct 2026](https://www.superchargebrowser.com/library/fix-chrome-saved-tab-groups-disappearing/): "Delete and Ungroup sync to every device" (vendor page); [Chrome Unboxed 2023](https://chromeunboxed.com/psa-dont-make-the-same-mistake-i-did-of-fully-relying-on-chromes-tab-groups-just-yet/): "wiped out across all six of my Chrome profiles" | Snapshot history protects against Chrome's own sync deleting things. This is our core pitch. |
| Native vertical tabs shipped in Chrome stable (Apr 2026), with no session saving or workspaces. | [TechCrunch, 7 Apr 2026](https://techcrunch.com/2026/04/07/chrome-is-finally-getting-vertical-tabs/) | Don't build a sidebar or vertical tab strip. |
| Gemini in Chrome works across tabs; "Ask Gemini about this group" is being tested in Canary. | [Google blog, 18 Sep 2025](https://blog.google/products/chrome/new-ai-features-for-chrome/): "can now work across multiple tabs"; [Android Authority, 20 Jul 2026](https://www.androidauthority.com/chrome-tab-group-gemini-integration-3689297/) | Don't build an AI chat over live tabs; Chrome will own it. AI over *saved, closed* sessions is still open ground, and so is AI that runs on the device with no Google account. |
| Chrome's "Declutter" (auto-archive of inactive tabs) is on Android; no desktop date. | [BOL News (Apr 2024 report)](https://www.bolnews.com/latest-news/google-chrome-to-delete-and-archive-your-inactive-tabs): "no definitive launch date announced yet" | A stale-tab review on desktop is safe for now. Watch for a desktop version. |
| Memory Saver is built in (Settings > Performance). | [4 GB laptop guide](https://theluckystrike.github.io/chrome-tips/chrome-slow-on-4gb-ram-laptop): "Enable Memory Saver" | Don't build a suspender. Use Chrome's own `tabs.discard` when we need to save RAM. |
| Built-in AI for extensions: Prompt, Summarizer, Translator and Language Detector APIs are stable from Chrome 138. Writer, Rewriter and Proofreader are still developer trials. | [Chrome built-in APIs table](https://developer.chrome.com/docs/ai/built-in-apis?hl=en): "available from Chrome 138 stable, only for Chrome Extensions" | Private AI with no server is possible today. |
| Gemini Nano needs at least 16 GB RAM or more than 4 GB of VRAM, plus 22 GB free disk. Not on Android or iOS. | [Chrome AI get-started](https://developer.chrome.com/docs/ai/get-started): "16 GB of RAM or more and 4 CPU cores"; [Ubergizmo, Aug 2026](https://www.ubergizmo.com/2026/08/chromes-on-device-ai-20gb/): "20 GB of free disk space" | Most low-RAM laptops in India **can't run it**. Every AI feature needs a plain-code fallback and must stay optional. |
| An on-device Embedding API is only at "intent to prototype" (26 May 2026). | [blink-dev](https://groups.google.com/a/chromium.org/g/blink-dev/c/EjL1gAy3k3Q): "No milestones specified" | Use MiniSearch or BM25 for search now. Add vectors later if this ships. |
| MV3: the service worker stops after 30 s idle; the shortest alarm period is 30 s (Chrome 120+). | [Chrome SW lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle): "Alarms can now be set to a minimum period of 30s" | 5-minute snapshots are fine. Long AI or export jobs must run in the popup, side panel or an offscreen document, not the worker. |
| `chrome.sessions` returns at most 25 recently closed items; `getDevices` reads synced devices. | [chrome.sessions API](https://developer.chrome.com/docs/extensions/reference/api/sessions): "MAX_SESSION_RESULTS" = 25 | Chrome's own "recently closed" is shallow. Our closed-tab log can go much deeper. |
| Firefox has the tab-group extension APIs: `tabs.group()` in 138, `tabGroups` in 139. | [Mozilla Add-ons blog, 30 Apr 2025](https://blog.mozilla.org/addons/2025/04/30/webextensions-support-for-tab-groups/) | A Firefox build through WXT keeps groups. |
| Edge is retiring Collections; personal accounts have no proper export. Pocket shut down in July 2025. | [Windows Central, 17 Jan 2026](https://www.windowscentral.com/software-apps/microsoft-edge-is-killing-off-collections-and-your-data-is-caught-in-the-crossfire): "Collections is being retired"; [Edge Insider thread, Mar-May 2026](https://techcommunity.microsoft.com/discussions/edgeinsiderdiscussions/export-tool-for-edge-collections-before-deprecation/4505752): "losing years of structured work"; [dev.to](https://dev.to/stanlymt/edge-collections-is-retiring-heres-where-to-move-your-saved-articles-3nc7): "Pocket shut down in July 2025" | People are being pushed out of Edge Collections and Pocket. Importing their data is a ready-made way to win new users. |
| Trusted extensions turned malicious through silent updates (2.3M users, Jul 2025). | [The Register, 8 Jul 2025](https://www.theregister.com/2025/07/08/browser_hijacking_campaign/): "auto-installed silently" | Trust that people can check for themselves is something we can sell, and our "no server" design already supports it. |

## 2. Candidate features (20)

Effort: S = 1-3 sessions, M = 4-8, L = 9+. "Chrome risk" = how likely Chrome makes the feature pointless within about 12 months.

### F1. Search every saved tab, ever (instant, offline)
- **What:** One search box over all sessions, snapshots and imports. It matches titles, URLs, group names and notes, tolerates typos, and finds a tab by its domain or a date range.
- **Who:** Tab hoarders, researchers, OneTab switchers.
- **Evidence:** [SuperchargeBrowser on OneTab](https://www.superchargebrowser.com/library/best-chrome-tab-managers-2026/): no "search within the saved list" beyond the browser's find; [HN "A tab hoarder's journey to sanity"](https://hn.nuxt.dev/item/46529797): "very frequently easier to just open a new tab"; [Tab Session Manager store listing](https://chromewebstore.google.com/detail/aclpbnbleaaghoblmlflfebmidlcocmi): "Not included yet: … advanced search".
- **MV3 feasibility:** Yes. Build a MiniSearch index (MIT, about 7 KB) in IndexedDB and rebuild it whenever a snapshot is written. No new permissions.
- **Effort:** M. **Chrome risk:** low (Chrome's tab search only covers open tabs). **Tier:** Free. This is the main reason people will stay.

### F2. Full-text search of pages you saved (opt-in)
- **What:** When you save, the extension also stores the readable text of each page, so later you can search what a page *said*, not just its title.
- **Who:** Students, researchers, journalists, developers reading docs.
- **Evidence:** [Full Text Tabs Forever](https://chromewebstore.google.com/detail/gfmbnlbnapjmffgcnbopfgmflmlfghel) (MIT, 4.3★): "stored locally on your device, and not on any external servers"; [HN tab-hoarder thread](https://hn.nuxt.dev/item/46529797): "Some content just can't be bookmarked".
- **MV3 feasibility:** Needs `scripting` plus host access. Ask for it as an **optional** permission (`<all_urls>` only after the user turns it on), and read text with Readability (Apache-2.0). Store it compressed. Skip incognito, banking and other sensitive domains by default.
- **Effort:** M. **Chrome risk:** low. **Tier:** Pro.

### F3. "Rescue" imports for orphaned users (Edge Collections, Pocket, Toby, Workona, bookmarks HTML, Chrome saved groups)
- **What:** Add importers for the Edge Collections CSV, the Pocket export CSV, the Netscape bookmarks HTML (which Edge "Move to Favorites" and most tools produce), Toby JSON, and plain URL lists. Add a one-click "copy my Chrome saved tab groups into Lifeboat" using `tabGroups`. Each import shows the same count preview we already have.
- **Who:** Edge Collections users, former Pocket users, OneTab and Toby switchers.
- **Evidence:** [Edge Insider thread](https://techcommunity.microsoft.com/discussions/edgeinsiderdiscussions/export-tool-for-edge-collections-before-deprecation/4505752): manual migration "simply impossible/undoable" with 166 Collections; [Windows Central](https://www.windowscentral.com/software-apps/microsoft-edge-is-killing-off-collections-and-your-data-is-caught-in-the-crossfire): "Collections is being retired"; [dev.to](https://dev.to/stanlymt/edge-collections-is-retiring-heres-where-to-move-your-saved-articles-3nc7): Pocket "shut down in July 2025".
- **MV3 feasibility:** Yes. Parsing only, no permissions. Note: "Removed in Edge 149" appears only in a TechRepublic headline that wouldn't load, so treat it as **unverified**.
- **Effort:** S per format. **Chrome risk:** none. **Tier:** Free. Imports are how we get users, so don't charge for them. Store listing line: "Edge Collections and Pocket refugees welcome".

### F4. Update-proof and crash-proof restore ("Lifeboat mode")
- **What:** Take an extra snapshot before every Chrome or extension update (`runtime.onUpdateAvailable`, `onInstalled` with `reason: chrome_update`) and on window close. On the next start, if the tabs that come back differ from the last snapshot, show a banner: "Chrome lost 42 tabs and 3 groups since 10:05. Restore them?"
- **Who:** Everyone; this is the core promise.
- **Evidence:** [SuperchargeBrowser](https://www.superchargebrowser.com/library/fix-chrome-saved-tab-groups-disappearing/): "Updates can lose group references" (vendor page); [Tom's Hardware](https://www.tomshardware.com/software/mozilla-firefox/firefox-user-loses-7470-opened-tabs-saved-over-two-years-after-they-cant-restore-browsing-session): session of 7,470 tabs "totally cleared"; [CMU study](https://www.cmu.edu/news/stories/archives/2021/may/overcoming-tab-overload.html): a quarter of participants had crashes from too many tabs.
- **MV3 feasibility:** Yes. Write a session-diff marker to `storage.session` and compare it on `runtime.onStartup`.
- **Effort:** S. **Chrome risk:** low (Chrome's own restore has failed for years). **Tier:** Free.

### F5. Backup health check and restore drill
- **What:** A green, amber or red "Backup health" card showing the last snapshot age, the last off-device copy, storage left, and whether the persistent-storage grant is still on. A monthly "test restore" opens one snapshot into a hidden window, counts the tabs and closes it, so a broken backup is caught before it is needed.
- **Who:** People who lost data before (OneTab and TSM refugees).
- **Evidence:** Repo review mining (`deep-scan-v2.md`): TSM "Auto-save doesn't work, hence data loss"; [Workona blog](https://workona.com/blog/one-tab-extension-lost-all-tabs/): "Export regularly"; [TabFlow page](https://selfloom.github.io/tabflow-vs-onetab) (vendor, paraphrased quotes): "Lost about 300 tabs after a browser crash".
- **MV3 feasibility:** Yes. Use `navigator.storage.estimate()` and `persisted()`. The test restore uses `windows.create({state:'minimized'})`.
- **Effort:** S. **Chrome risk:** none. **Tier:** Free card; Pro reminders and history.

### F6. Gentle restore for low-RAM laptops ("open later" tabs)
- **What:** Restoring 300 tabs no longer freezes a 4 GB laptop. Restored tabs are created and then unloaded at once with `tabs.discard`, so they keep their **real URLs** (no custom suspend page like The Great Suspender used) and load only when clicked. Optionally restore one group at a time.
- **Who:** Students and office workers on 4-8 GB laptops in India; Chromebooks.
- **Evidence:** [4 GB laptop guide](https://theluckystrike.github.io/chrome-tips/chrome-slow-on-4gb-ram-laptop): a tab uses "between 50MB and 300MB of RAM"; [SupaSidebar](https://supasidebar.com/blog/best-tab-manager-extension-chrome-2026): "RAM usage climbs past 4-8 GB"; [SlashGear on The Great Suspender, Feb 2021](https://www.slashgear.com/the-great-suspender-chrome-extension-removed-for-being-malware-tabs-lost-05658271/): suspended tabs "remained inaccessible".
- **MV3 feasibility:** Yes, with the existing `tabs` permission. Chrome can't create a tab already discarded (Firefox can), so call `discard` right after `create`, and test it on 300 tabs.
- **Effort:** S. **Chrome risk:** medium (Memory Saver covers part of this, but not a mass restore). **Tier:** Free.

### F7. Weekly stale-tab review (keep / snooze / archive, never automatic)
- **What:** Once a week (the user picks the day), show the open tabs not touched in 7+ days, grouped by site or topic with their age. One tap keeps, snoozes or archives each tab into a session. Nothing closes without a tap.
- **Who:** Tab hoarders, ADHD users.
- **Evidence:** [dev.to "87 tabs open"](https://dev.to/alogach/87-tabs-open-i-cant-close-any-of-them-5cl1): "Nothing closes without my explicit OK" (a paid rival, $19 one-time); [CMU](https://www.cmu.edu/news/stories/archives/2021/may/overcoming-tab-overload.html): "as soon as something went out of sight, it was gone".
- **MV3 feasibility:** Yes. Track last access through `tabs.onActivated` (the Tab object also has `lastAccessed`), plus an alarm and a notification.
- **Effort:** M. **Chrome risk:** medium (Android Declutter could reach desktop). **Tier:** Free review; Pro custom rules (for example "always archive news sites after 3 days").

### F8. Snooze a tab or a whole group
- **What:** "Bring this back tonight / tomorrow 9 am / next week / when I open Chrome on Monday". It works for whole tab groups too, keeping their colour.
- **Who:** ADHD and focus users, readers, sales follow-ups.
- **Evidence:** [Tab Snooze (MV3 fork) reviews](https://chromewebstore.google.com/detail/tab-snooze-works-as-of-no/kgnigbfnfjgpfaiaafcbgdkpalapiinb/reviews), 4.7★ from 48 ratings: "the orginal was abandoned"; [Em's blog](https://www.goodreads.com/author_blog_posts/17103063-the-tab-snooze-chrome-extension-makes-my-life-better?tab=book): "Tab Snooze lets me take action".
- **MV3 feasibility:** Yes. `alarms` persist across restarts, and alarms missed while the computer slept fire at the next start. A review there complains of "not working on time", so test timing after sleep.
- **Effort:** S. **Chrome risk:** low. **Tier:** Free (5 active snoozes); Pro unlimited plus repeating snoozes.

### F9. Notes and a "why I opened this" line on sessions and tabs
- **What:** A one-line intent on each saved session ("Comparing laptops under ₹50k") and optional notes and tags on any tab. All of it is searchable (F1).
- **Who:** Students, researchers, ADHD users ("what was I doing?").
- **Evidence:** [ADHD extensions guide 2026](https://adhd-productivity.pages.dev/blog/best-browser-extensions-adhd-tab-management-2026): "custom tags, and optional notes"; [HN tab-hoarder thread](https://hn.nuxt.dev/item/46529797): "A lot of tabs aren't bookmark but unfinished work or research".
- **MV3 feasibility:** Yes, IndexedDB only.
- **Effort:** S. **Chrome risk:** low. **Tier:** Free.

### F10. Export to Markdown, Obsidian, Notion, CSV or bookmarks HTML
- **What:** "Copy session as Markdown links" (with group headings and notes), plus download as `.md`, `.csv`, bookmarks `.html` or JSON. One click pastes into Obsidian, Notion or Google Docs.
- **Who:** Students, researchers, PKM users, developers.
- **Evidence:** [Tab2Mark listing](https://chrome.google.com/webstore/detail/tab2mark/iieofemdmlppbhikdeknlbjkichfmnmo/reviews): "paste them into your favorite markdown editor like Notion, Obsidian"; [dev.to Obsidian workflow](https://dev.to/pmestreforge/my-obsidian-tab-to-vault-workflow-with-a-free-chrome-extension-5gid): moves "30+ tabs" into notes by hand.
- **MV3 feasibility:** Yes. Use the clipboard API in the popup; `downloads` is already planned as optional.
- **Effort:** S. **Chrome risk:** none. **Tier:** Free. Exporting is also a trust feature, because users can see they are never locked in.

### F11. Share a tab set as a link, with no server
- **What:** Turn a session or group into a link. The tab list is compressed into the URL **fragment** (`#…`), which browsers never send to any server, on a static Kalpa page. The person receiving it sees the list and can open it with or without the extension. Sharing as a file is the fallback.
- **Who:** Teams, teachers sending a reading list, sales reps sending a prospect pack, family trip planning.
- **Evidence:** [TabShare listing](https://chromewebstore.google.com/detail/tabshare-share-tab-groups/ackkgbdepcbjjlbfidccojaodiikiold) (about 1,000 users, 4.2★): "share a browser tab group as a link"; [Toby for Teams on Product Hunt](https://www.producthunt.com/p/toby/toby-for-teams?page=2): "share links and context with my team"; [Workona pricing](https://workona.com/pricing/): its Team plan sells "Shared spaces".
- **MV3 feasibility:** Yes. Compress with `CompressionStream` and base64url. Cap it at about 500 tabs, because a URL fragment can't be unlimited. The static page needs Akhil's "go" before it goes live (rule 9).
- **Effort:** M. **Chrome risk:** low-medium (Chrome has "Share tabs", but for single tabs). **Tier:** Free to share; Pro adds "team packs" (a shared JSON file in a Drive folder the team owns).

### F12. Named workspaces with one-click switch
- **What:** A workspace is a named set of windows and groups ("Client A", "Exam prep"). Switching saves the current one, closes it (or just hides it, unloaded), then opens the next. Each workspace keeps its own snapshot history.
- **Who:** Freelancers, developers, students with several subjects.
- **Evidence:** [CMU](https://www.cmu.edu/news/stories/archives/2021/may/overcoming-tab-overload.html): a flat tab list makes it "hard to switch between sets of tasks" (from the fetch tool's extract); [SupaSidebar](https://supasidebar.com/blog/best-tab-manager-extension-chrome-2026): Workona's free cap "fills up quickly"; [SuperchargeBrowser](https://www.superchargebrowser.com/library/best-chrome-tab-managers-2026/): names "named workspaces" as something Chrome lacks.
- **MV3 feasibility:** Yes, with the existing APIs.
- **Effort:** M-L. **Chrome risk:** medium (saved groups plus sync cover part of it). **Tier:** Free 3 workspaces; Pro unlimited. Workona Pro sells this.

### F13. Duplicate finder across open tabs and saved sessions
- **What:** "You have 14 duplicates (6 open, 8 saved). Merge?" It also warns "Already saved in 'Exam prep' on 3 Nov" when you save a URL you already kept.
- **Who:** Tab hoarders.
- **Evidence:** [HN tab-hoarder thread](https://hn.nuxt.dev/item/46529797): it's "easier to just open a new tab" than find the old one; [ADHD guide](https://adhd-productivity.pages.dev/blog/best-browser-extensions-adhd-tab-management-2026): an extension that "prevents duplicate tabs"; [SuperchargeBrowser](https://www.superchargebrowser.com/library/best-chrome-tab-managers-2026/): Chrome lacks "tab deduplication".
- **MV3 feasibility:** Yes. Normalise URLs (strip `utm_*`, fragments and trailing slashes).
- **Effort:** S. **Chrome risk:** low. **Tier:** Free.

### F14. Command palette (keyboard launcher)
- **What:** Press Alt+Shift+L for a Spotlight-style box that searches open tabs, saved sessions and snoozed tabs together. Enter jumps to the tab or restores it.
- **Who:** Developers and power users.
- **Evidence:** [Product Hunt on ArkTabs](https://www.producthunt.com/newsletters/archive/46527-spotlight-for-tabs): "a fast launcher and good search", "the right level of ambition"; repo `deep-scan-v2.md`: TabButler (MIT) has the command-palette UX.
- **MV3 feasibility:** Yes. Use `commands` plus the popup, or a side panel. An in-page overlay would need host access, so avoid it.
- **Effort:** M. **Chrome risk:** low-medium (Chrome's tab search covers open tabs only). **Tier:** Free.

### F15. Private AI: auto-name and auto-group saved sessions (on-device, optional)
- **What:** When you save, Gemini Nano (Prompt API) suggests a session name ("Goa trip – hotels & flights") and splits a 120-tab dump into topic groups. It reads **titles and URLs only**. On PCs that can't run Nano, a plain-code fallback groups by domain and keywords.
- **Who:** Heavy hoarders, students, researchers.
- **Evidence:** [Chrome APIs table](https://developer.chrome.com/docs/ai/built-in-apis?hl=en): Prompt API "Chrome 138 stable" for extensions; [Skipper listing](https://chromewebstore.google.com/detail/skipper-tab-management-th/cjiinmicahhdcmfpdohhaahgkdiehfga): its Pro tier sells "AI-powered Sessions"; [CMU Skeema](https://www.cmu.edu/news/stories/archives/2021/may/overcoming-tab-overload.html): machine learning suggests groups.
- **Risk to design in:** [HN thread](https://hn.nuxt.dev/item/46529797) warns AI could group phishing pages with a real site's tabs. So AI only suggests, the user confirms, and a group never mixes look-alike domains.
- **MV3 feasibility:** Yes for Chrome 138+ desktops with 16 GB RAM or a GPU with more than 4 GB VRAM ([requirements](https://developer.chrome.com/docs/ai/get-started)). Run it in the popup or side panel, never in the service worker (30 s idle limit). Most of our India target users will get the fallback.
- **Effort:** M. **Chrome risk:** **high** for live tabs (Gemini "Ask Gemini about this group"); lower for saved, closed sessions and for people without Gemini. **Tier:** Pro.

### F16. "What was I doing?" recap for an old session (on-device)
- **What:** Opening a 3-week-old snapshot shows a two-line recap built from its titles and notes, using the Summarizer API. Plain-code fallback: the top 3 domains, the group names and the number of tabs.
- **Who:** ADHD users, researchers coming back to work.
- **Evidence:** [HN thread](https://hn.nuxt.dev/item/46529797): "if I don't see something, I forget it exists"; [Chrome APIs table](https://developer.chrome.com/docs/ai/built-in-apis?hl=en): Summarizer "Chrome 138 (stable)" for extensions.
- **MV3 feasibility:** Same hardware limits as F15. It summarises titles only, so the input is tiny and fast.
- **Effort:** S-M. **Chrome risk:** medium-high (Gemini can summarise live groups, but not your archive). **Tier:** Pro.

### F17. Dead-link check and keep-a-copy for important tabs
- **What:** A "Check links" button marks saved tabs that now return 404 or are gone, and offers the Wayback Machine link. "Keep a copy" saves an offline MHTML of one open tab into the session, using `pageCapture`.
- **Who:** Researchers, students citing sources, people with archives years old.
- **Evidence:** [Pew Research, May 2024](https://www.pewresearch.org/data-labs/2024/05/17/when-online-content-disappears/): 38% of pages from 2013 were gone a decade later; [HN thread](https://hn.nuxt.dev/item/46529797): users want "a cached version of the page".
- **MV3 feasibility:** The link check needs optional host access (`<all_urls>`, asked only when used). Send HEAD requests with no cookies, at most 4 at a time with backoff. `pageCapture` is a separate optional permission; MHTML files are large, so store them only when the user asks.
- **Effort:** M. **Chrome risk:** none. **Tier:** Pro.

### F18. Firefox and Edge builds, plus moving between browsers
- **What:** Publish the same WXT code to Firefox AMO and Edge Add-ons. The backup file format is the same everywhere, so a user can move their history from Edge to Chrome or Firefox in one step.
- **Who:** Edge users (especially Collections refugees), Firefox users, Brave users (who already use the Chrome store).
- **Evidence:** [Mozilla](https://blog.mozilla.org/addons/2025/04/30/webextensions-support-for-tab-groups/): Tab Groups API expected "with the release of Firefox 139"; [SupaSidebar](https://supasidebar.com/blog/best-tab-manager-extension-chrome-2026): "Tabs scatter across all three" browsers; [Edge Insider thread](https://techcommunity.microsoft.com/discussions/edgeinsiderdiscussions/export-tool-for-edge-collections-before-deprecation/4505752).
- **MV3 feasibility:** Yes. WXT builds for Firefox; Firefox runs background code as an event page, not a service worker, and WXT handles that. Edge Add-ons is free to publish to (store fee unverified, check before telling Akhil).
- **Effort:** M. **Chrome risk:** none. **Tier:** Free.

### F19. Trust you can check: permission and network report
- **What:** A "Privacy" screen that shows which permissions are on (and which optional ones are off), every network call the extension makes (only the Pro licence check and Drive, if turned on), and a "No network" switch that blocks both. Source code is public, and each store release links to its commit and build hash.
- **Who:** Privacy-minded users and IT-locked offices. It also helps the store listing convert.
- **Evidence:** [The Register, Jul 2025](https://www.theregister.com/2025/07/08/browser_hijacking_campaign/): 2.3M users hit through updates "auto-installed silently"; [SlashGear, The Great Suspender](https://www.slashgear.com/the-great-suspender-chrome-extension-removed-for-being-malware-tabs-lost-05658271/); [SuperchargeBrowser](https://www.superchargebrowser.com/library/best-chrome-tab-managers-2026/): OneTab's share feature "sends tab URLs to OneTab's servers".
- **MV3 feasibility:** Yes. Log each `fetch` through one wrapper, and set the CSP `connect-src` to our licence host and Google APIs only.
- **Effort:** S-M. **Chrome risk:** none. **Tier:** Free (it's a selling point).

### F20. Focus limit ("max N tabs per window" with save-instead-of-close)
- **What:** An optional cap (say 10 tabs). Opening one more offers "save the oldest 3 to a session" instead of blocking. Pairs with F7 and F8.
- **Who:** ADHD and focus users, low-RAM laptops.
- **Evidence:** [ADHD guide](https://adhd-productivity.pages.dev/blog/best-browser-extensions-adhd-tab-management-2026): ADHD Tab Manager "enforces a hard limit of five open tabs"; [HN thread](https://hn.nuxt.dev/item/46529797): iOS Safari's 500-tab cap is "a hard limit to start cleaning up tabs".
- **MV3 feasibility:** Yes, with `tabs.onCreated`. Never close anything silently (our "never close without asking" rule).
- **Effort:** S. **Chrome risk:** low. **Tier:** Free.

## 3. Considered and dropped

| Idea | Why not |
|---|---|
| Our own tab suspender page | Chrome's Memory Saver and `tabs.discard` already do it; a custom suspend page is how Great Suspender users lost their tabs. |
| Vertical tab sidebar | Chrome stable has it natively since Apr 2026. |
| AI chat over open tabs | Gemini in Chrome owns this (US, AI Pro and Ultra for auto browse). |
| Scheduled "open my morning tabs" | Weak demand: [Tab Scheduler](https://chromewebstore.google.com/detail/tab-scheduler-auto-open-c/aammlbcjbdfgkhahkgabdhkhhmjmcjkd) has 119 users and no ratings. Could come later as part of F8 (repeating snooze). |
| Sync through `storage.sync` | 100 KB quota (Chrome docs, not re-fetched today: unverified). Use Drive `drive.file` (E13) or file export instead. |
| Semantic or vector search | The Embedding API is only at prototype stage; MiniSearch is enough for v1. |

## 4. Suggested order (for the PLAN.md quest row; Akhil decides)

1. **Free, quick, protects users (S):** F4 crash/update restore, F5 backup health, F13 duplicates, F10 Markdown export, F3 Edge/Pocket importers.
2. **Free, keeps users coming back (M):** F1 search, F6 gentle restore, F8 snooze, F9 notes, F14 palette.
3. **Pro (worth paying for):** F2 full-text, F12 unlimited workspaces, F15/F16 private AI, F17 link check plus offline copy, F11 team packs.
4. **Reach:** F18 Firefox and Edge, F19 trust screen (before store promotion).

Open questions for Akhil (CEO queue): the free versus Pro split above; whether F11's static share page and F18's AMO/Edge listings may go live (each needs "go"); whether F2/F17 may ask for optional `<all_urls>` (it triggers a stricter Chrome Web Store review).

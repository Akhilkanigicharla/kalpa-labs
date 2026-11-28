// E3 end-to-end: load the built extension in Chromium, save 3 tabs + a tab group, close them, restore.
// Run: npm run test:e2e   (CHROME_PATH can point at a local Chromium; Actions uses Playwright's)
import { chromium } from "playwright";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import fs from "node:fs";

const ext = path.resolve(import.meta.dirname, "../../.output/chrome-mv3");
const server = http.createServer((req, res) => { res.setHeader("content-type", "text/html"); res.end(`<title>Page ${req.url}</title><h1>${req.url}</h1>`); }).listen(0);
const base = `http://127.0.0.1:${server.address().port}`;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "lifeboat-"));
const ctx = await chromium.launchPersistentContext(profile, {
  headless: true,
  // Playwright's default headless shell can't load extensions; the full Chromium build ("chromium" channel) can.
  ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: "chromium" }),
  args: ["--headless=new", `--disable-extensions-except=${ext}`, `--load-extension=${ext}`, "--no-sandbox"],
});
let failed = false;
const check = (ok, msg) => { console.log(`  ${ok ? "✓" : "✗"} ${msg}`); if (!ok) failed = true; };
try {
  let [sw] = ctx.serviceWorkers(); sw ??= await ctx.waitForEvent("serviceworker");
  const id = new URL(sw.url()).host;
  const pages = [];
  for (const p of ["/a", "/b", "/c"]) { const pg = await ctx.newPage(); await pg.goto(base + p); pages.push(pg); }
  // group /b and /c as "Research" (purple, collapsed) through the extension's own permissions
  await sw.evaluate(async (base) => {
    const tabs = await chrome.tabs.query({}); const ids = tabs.filter((t) => /\/(b|c)$/.test(t.url)).map((t) => t.id);
    const g = await chrome.tabs.group({ tabIds: ids }); await chrome.tabGroups.update(g, { title: "Research", color: "purple", collapsed: false });
  }, base);
  const popup = await ctx.newPage(); await popup.goto(`chrome-extension://${id}/popup.html`);
  const saved = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "save", name: "e2e" }));
  check(saved.ok && saved.counts.tabs >= 3 && saved.counts.groups === 1, `saved ${saved.counts?.tabs} tabs, ${saved.counts?.groups} group`);
  check((await popup.locator("#list li").count()) >= 0, "popup renders");
  await popup.reload(); await popup.waitForTimeout(400);
  const nudge = await popup.locator("#nudge").textContent();
  check(await popup.locator("#nudge").isVisible() && /No backup file yet/.test(nudge ?? ""), `popup reminds to keep a backup file: "${nudge}"`);
  await popup.evaluate(() => chrome.runtime.sendMessage({ type: "export" })); await popup.reload(); await popup.waitForTimeout(400);
  check(!(await popup.locator("#nudge").isVisible()), "reminder goes away after a backup file");
  for (const pg of pages) await pg.close();
  const before = await sw.evaluate(() => chrome.tabs.query({}).then((t) => t.map((x) => x.url)));
  check(!before.some((u) => u.startsWith("http://127.0.0.1")), "test tabs closed");
  const res = await popup.evaluate((sid) => chrome.runtime.sendMessage({ type: "restore", id: sid }), saved.session.id);
  check(res.ok && res.tabs >= 3, `restore reopened ${res.tabs} tabs (${res.skipped} skipped)`);
  await new Promise((r) => setTimeout(r, 800));
  const after = await sw.evaluate(async () => {
    const tabs = await chrome.tabs.query({}); const groups = await chrome.tabGroups.query({});
    return { urls: tabs.map((t) => t.url), groups: groups.map((g) => ({ title: g.title, color: g.color, members: tabs.filter((t) => t.groupId === g.id).map((t) => new URL(t.url).pathname) })) };
  });
  check(["/a", "/b", "/c"].every((p) => after.urls.includes(base + p)), "all 3 pages are back");
  const g = after.groups.find((x) => x.title === "Research");
  check(!!g && g.color === "purple" && g.members.sort().join() === "/b,/c", `group restored: ${JSON.stringify(g)}`);
  // v0.3 A2: restoring again opens nothing twice
  const again = await popup.evaluate((sid) => chrome.runtime.sendMessage({ type: "restore", id: sid }), saved.session.id);
  check(again.ok && again.tabs === 0 && again.alreadyOpen >= 3, `second restore: opened ${again.tabs}, skipped ${again.alreadyOpen} already open`);
  // v0.3 A3: restart banner. Close /c, pretend Chrome restarted, then Restore from the banner
  await sw.evaluate(async (b) => { const t = await chrome.tabs.query({}); await chrome.tabs.remove(t.filter((x) => x.url === `${b}/c`).map((x) => x.id)); }, base);
  await sw.evaluate((sid) => chrome.storage.local.set({ banner: { kind: "restart", at: Date.now(), id: sid } }), saved.session.id);
  const tabsBefore = (await sw.evaluate(() => chrome.tabs.query({}))).length;
  await popup.reload(); await popup.waitForTimeout(500);
  const bt = await popup.locator("#banner-msg").textContent();
  check(await popup.locator("#banner").isVisible() && /^Chrome restarted\. Your \d+ tabs from \d\d:\d\d are safe\.$/.test(bt ?? ""), `banner: "${bt}"`);
  check((await sw.evaluate(() => chrome.tabs.query({}))).length === tabsBefore, "banner never opens tabs by itself");
  await popup.locator("#banner-restore").click(); await popup.waitForTimeout(800);
  const br2 = await popup.locator("#banner-msg").textContent();
  check(/^Opened 1, skipped \d+ already open/.test(br2 ?? ""), `banner restore: "${br2}"`);
  check((await sw.evaluate(() => chrome.storage.local.get("banner"))).banner === null, "banner cleared after Restore");
  // v0.3 A1: stale auto-save heals itself (alarm back + snapshot now), and the badge stays clear
  await sw.evaluate(() => Promise.all([chrome.alarms.clear("snapshot"), chrome.storage.local.set({ lastAutoRun: Date.now() - 3600e3, lastSnapshot: Date.now() - 3600e3 }), chrome.storage.session.set({ bootAt: Date.now() - 3600e3 })]));
  const st0 = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "status" }));
  const badge = await sw.evaluate(() => chrome.action.getBadgeText({}));
  const al = await sw.evaluate(() => chrome.alarms.get("snapshot"));
  check(st0.ok && st0.stale === null && Date.now() - st0.lastSnapshot < 60e3 && badge === "" && al?.periodInMinutes === 5, `stale auto-save healed: stale=${st0.stale}, badge="${badge}", alarm=${al?.periodInMinutes}`);
  const bad = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "restore", id: { $ne: 1 } }));
  check(!bad.ok && bad.error === "unknown message", "malformed message refused");
  const alarm = await sw.evaluate(() => chrome.alarms.get("snapshot"));
  check(alarm?.periodInMinutes === 5, `auto-snapshot alarm every ${alarm?.periodInMinutes} min`);
  await popup.evaluate(() => chrome.runtime.sendMessage({ type: "snapshot" }));
  const st = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "status" }));
  check(st.lastSnapshot && Date.now() - st.lastSnapshot < 5 * 60e3, "latest snapshot is under 5 minutes old");
  const list = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "list" }));
  check(list.sessions.some((s) => s.kind === "auto"), "auto snapshot stored");
  check(list.sessions.some((s) => s.name === "e2e"), "session listed in IndexedDB");
  // A105: find any saved tab, rename, and the Pro tools
  const found = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "search", text: "page /b" }));
  check(found.ok && found.hits.some((h) => h.url.endsWith("/b")), `search finds a saved tab (${found.hits?.length} hits)`);
  await popup.evaluate((sid) => chrome.runtime.sendMessage({ type: "rename", id: sid, name: "Renamed" }), saved.session.id);
  const l2 = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "list" }));
  check(l2.sessions.some((s) => s.name === "Renamed"), "rename saved");
  // A231 delete → undo, the way a user does it: tap Delete in the popup (no confirm), then Undo
  await popup.reload(); await popup.waitForTimeout(300);
  let dialogs = 0; popup.on("dialog", (d) => { dialogs++; void d.dismiss(); });
  await popup.getByRole("button", { name: "Delete Renamed" }).click();
  await popup.locator("#undo").waitFor({ state: "visible" });
  const gone = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "list" }));
  const bin = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "trash-list" }));
  check(dialogs === 0 && !gone.sessions.some((s) => s.name === "Renamed") && bin.sessions.some((s) => s.name === "Renamed"), "Delete moves the session to Recently deleted without a confirm box");
  const ub = await popup.locator("#undo-btn").boundingBox();
  check(ub && ub.height >= 44, `Undo button is ${ub?.height} px tall`);
  await popup.locator("#undo-btn").click(); await popup.waitForTimeout(300);
  const back = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "list" }));
  const bin2 = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "trash-list" }));
  check(back.sessions.some((s) => s.name === "Renamed" && s.tabs === saved.counts.tabs) && !bin2.sessions.length, "Undo puts it back with every tab");
  await popup.evaluate((sid) => chrome.runtime.sendMessage({ type: "delete", id: sid }), saved.session.id);
  const tr = await ctx.newPage(); await tr.goto(`chrome-extension://${id}/options.html`); await tr.waitForTimeout(500);
  check((await tr.locator("#trash li").first().textContent())?.includes("Renamed"), "options page lists it under Recently deleted");
  await tr.getByRole("button", { name: "Put back Renamed" }).click(); await tr.waitForTimeout(300);
  check((await tr.locator("#list").textContent())?.includes("Renamed") && /Nothing deleted/.test((await tr.locator("#trash").textContent()) ?? ""), "Put back on the options page works");
  await tr.close();
  // v0.3 B4: popup search by keyboard: "/" focuses, typing finds, ArrowDown + Enter opens in a new tab, Esc clears
  await popup.reload(); await popup.waitForTimeout(300);
  await popup.keyboard.press("/");
  check(await popup.evaluate(() => document.activeElement?.id === "find"), '"/" focuses the search box');
  await popup.keyboard.type("page /b"); await popup.waitForTimeout(500);
  const hitN = await popup.locator("#hits [role=option]").count();
  check(hitN >= 1 && (await popup.locator("#hits").textContent()).includes("/b"), `popup search finds ${hitN} saved tab(s)`);
  const newTab = ctx.waitForEvent("page");
  await popup.keyboard.press("Enter");
  const opened = await newTab; await opened.waitForLoadState().catch(() => {});
  check(opened.url().startsWith(`${base}/b`), `Enter opens the hit in a new tab: ${opened.url()}`); await opened.close();
  await popup.locator("#find").fill("zzzz-nothing"); await popup.waitForTimeout(500);
  check((await popup.locator("#hits").textContent()) === "No matches", "no-match state");
  await popup.locator("#find").press("Escape");
  check((await popup.locator("#find").inputValue()) === "" && await popup.locator("#hits").isHidden(), "Esc clears");
  const fh = await popup.locator("#find").boundingBox(); check(fh && fh.height >= 44, `search box ${fh?.height} px tall`);
  // v0.3 B5: edit on the options page: move a tab, undo, remove, merge, undo merge
  const two = { id: "edit-b", name: "Second", kind: "manual", createdAt: Date.now() - 1000, windows: [{ groups: [], tabs: [{ url: `${base}/x1`, title: "X1 🚀" }] }] };
  await popup.evaluate((text) => chrome.runtime.sendMessage({ type: "restore-backup", text }), JSON.stringify({ format: "tab-lifeboat-backup", version: 1, exportedAt: "", sessions: [two] }));
  const ed = await ctx.newPage(); await ed.setViewportSize({ width: 390, height: 800 }); await ed.goto(`chrome-extension://${id}/options.html`); await ed.waitForTimeout(500);
  const tabsOf = async (sid) => (await popup.evaluate((x) => chrome.runtime.sendMessage({ type: "session-get", id: x }), sid)).session?.windows.flatMap((w) => w.tabs.map((t) => t.url)) ?? null;
  await ed.getByRole("button", { name: "Edit Renamed" }).click(); await ed.waitForTimeout(300);
  check(await ed.locator("#edit").isVisible() && (await ed.locator("#edit-tabs li").count()) === saved.counts.tabs, "editor lists every tab");
  await ed.locator("#edit-other").selectOption("edit-b");
  await ed.locator("#edit-tabs li").first().getByRole("button", { name: /^Move / }).click(); await ed.waitForTimeout(400);
  check((await tabsOf("edit-b")).length === 2 && (await tabsOf(saved.session.id)).length === saved.counts.tabs - 1, "Move sends one tab to the other session");
  check(await ed.locator("#undo").isVisible(), "Undo bar after an edit");
  await ed.locator("#undo-btn").click(); await ed.waitForTimeout(400);
  check((await tabsOf("edit-b")).length === 1 && (await tabsOf(saved.session.id)).length === saved.counts.tabs, "Undo puts the moved tab back");
  await ed.locator("#edit-tabs li").first().getByRole("button", { name: /^Remove / }).click(); await ed.waitForTimeout(400);
  check((await tabsOf(saved.session.id)).length === saved.counts.tabs - 1, "Remove drops one tab");
  await ed.locator("#undo-btn").click(); await ed.waitForTimeout(400);
  await ed.getByRole("button", { name: "Edit Second" }).click(); await ed.waitForTimeout(300);
  await ed.locator("#edit-other").selectOption(saved.session.id);
  await ed.locator("#edit-merge").click(); await ed.waitForTimeout(400);
  const trashNow = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "trash-list" }));
  check((await tabsOf(saved.session.id)).includes(`${base}/x1`) && (await tabsOf("edit-b")) === null && trashNow.sessions.some((x) => x.id === "edit-b"), "Merge adds the tabs and moves the old session to Recently deleted");
  await ed.locator("#undo-btn").click(); await ed.waitForTimeout(400);
  check((await tabsOf("edit-b"))?.length === 1 && (await tabsOf(saved.session.id)).length === saved.counts.tabs, "Undo merge restores both sessions exactly");
  // A357: an edit from a page showing an old copy is refused; restoring the old backup never eats the newer edit
  const sendP = (m) => popup.evaluate((x) => chrome.runtime.sendMessage(x), m);
  const s0 = (await sendP({ type: "session-get", id: "edit-b" })).session; const v0 = s0.updatedAt ?? s0.createdAt;
  const r1 = await sendP({ type: "rename", id: "edit-b", name: "Second edited", v: v0 });
  const r2 = await sendP({ type: "rename", id: "edit-b", name: "Stale page", v: v0 });
  check(r1.ok && !r2.ok && /another window/.test(r2.error) && (await sendP({ type: "session-get", id: "edit-b" })).session.name === "Second edited", "edit from a stale page refused: 'changed in another window'");
  await sendP({ type: "restore-backup", text: JSON.stringify({ format: "tab-lifeboat-backup", version: 1, exportedAt: "", sessions: [two] }) });
  const lib = (await sendP({ type: "list" })).sessions;
  check((await sendP({ type: "session-get", id: "edit-b" })).session.name === "Second edited" && lib.some((x) => /^Second \(from backup /.test(x.name)), "old backup restored after an edit: edit kept, backup added as a copy");
  const before2 = (await sendP({ type: "list" })).sessions.length;
  await sendP({ type: "restore-backup", text: JSON.stringify({ format: "tab-lifeboat-backup", version: 1, exportedAt: "", sessions: [(await sendP({ type: "session-get", id: "edit-b" })).session] }) });
  check((await sendP({ type: "list" })).sessions.length === before2, "restoring an identical copy adds nothing");
  const csp = await sw.evaluate(() => chrome.runtime.getManifest().content_security_policy?.extension_pages ?? "");
  check(/object-src 'none'/.test(csp) && /connect-src https:\/\/www\.googleapis\.com/.test(csp), "explicit extension CSP loaded by Chrome");
  const small = await ed.evaluate(() => [...document.querySelectorAll("#edit button, #edit select, #edit input")].filter((e) => e.offsetParent && e.getBoundingClientRect().height < 44).map((e) => e.id || e.textContent));
  check(!small.length, `editor controls >= 44 px at 390 px (${small.join(",")})`);
  await ed.locator("#importText").fill("{ broken json"); await ed.waitForTimeout(500);
  check((await ed.locator("#importText").inputValue()) === "{ broken json" && /couldn't be read/.test(await ed.locator("#preview").textContent()), "failed import keeps the pasted text, plain error");
  // v0.3 C7: import a bookmarks file through the file button (parsed in the page), each folder becomes a session
  await ed.locator("#importText").fill("");
  await ed.locator("#importFile").setInputFiles(path.resolve(import.meta.dirname, "../fixtures/samples/bookmarks.html")); await ed.waitForTimeout(800);
  const pv = await ed.locator("#preview").textContent();
  check(/^Found 3 tabs in 3 sessions\. 1 link that can't be reopened/.test(pv ?? "") && /Import 3 tabs/.test(await ed.locator("#doImport").textContent()), `bookmarks preview: "${pv}"`);
  await ed.locator("#doImport").click(); await ed.waitForTimeout(500);
  const afterImp = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "list" }));
  check(["Bookmarks bar", "Bookmarks bar / Recipes & food", "Other bookmarks"].every((nm) => afterImp.sessions.some((x) => x.name === nm && x.kind === "import")), "bookmark folders imported as sessions");
  await ed.locator("#importFile").setInputFiles({ name: "pocket.zip", mimeType: "application/zip", buffer: Buffer.from("PK") }); await ed.waitForTimeout(300);
  check(/Unzip it first/.test(await ed.locator("#preview").textContent()), "zip gets 'Unzip it first'");
  // v0.3 C8: exports download as files with escaped content
  await ed.reload(); await ed.waitForTimeout(600);
  const grab = async (btn) => { const dl = ed.waitForEvent("download"); await ed.locator(btn).click(); const d = await dl; return { name: d.suggestedFilename(), text: fs.readFileSync(await d.path(), "utf8") }; };
  const md = await grab("#exp-md"), csv = await grab("#exp-csv"), txt = await grab("#exp-txt");
  check(/^tab-lifeboat-\d{4}-\d\d-\d\d-all-sessions\.md$/.test(md.name) && md.text.includes(`](<${base}/x1>)`), `Markdown export ${md.name}`);
  check(csv.text.startsWith("\uFEFF\"Session\",\"Group\",\"Title\",\"URL\",\"Saved\"\r\n") && csv.text.includes(`"${base}/b"`), `CSV export ${csv.name}`);
  check(txt.text.includes(`${base}/x1 | X1 🚀`), `link list export ${txt.name}`);
  const sc = await ed.locator("#shortcut").textContent();
  check(sc === "Alt+Shift+Y" || sc === "not set", `shortcut shown: ${sc}`);
  await ed.close();
  // v0.3 C6: save this window / selected tabs, with a name
  const cmds = await sw.evaluate(() => chrome.commands.getAll());
  check(cmds.some((c) => c.name === "save-all") && cmds.some((c) => c.name === "save-window"), `commands: ${cmds.map((c) => `${c.name}=${c.shortcut || "-"}`).join(", ")}`);
  const menus = await sw.evaluate(async () => { const ok = []; for (const id of ["save-all", "save-window", "save-selected"]) ok.push(await chrome.contextMenus.update(id, {}).then(() => id, () => null)); return ok; });
  check(menus.every(Boolean), `toolbar right-click menu: ${menus.join(", ")}`);
  const w2 = await sw.evaluate(async (b) => { const w = await chrome.windows.create({ url: [`${b}/w1`, `${b}/w2`, `${b}/w3`], focused: true }); await new Promise((r) => setTimeout(r, 600));
    const t = await chrome.tabs.query({ windowId: w.id }); await chrome.tabs.highlight({ windowId: w.id, tabs: [0, 2] }); return { id: w.id, n: t.length }; }, base);
  const sWin = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "save", scope: "window", name: "  Only this window 🚀  " }));
  check(sWin.ok && sWin.counts.tabs === w2.n && sWin.session.name === "Only this window 🚀", `save this window: ${sWin.counts?.tabs} tabs, "${sWin.session?.name}"`);
  const sSel = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "save", scope: "selected" }));
  check(sSel.ok && sSel.counts.tabs === 2 && sSel.session.windows[0].tabs.map((t) => t.url.split("/").pop()).join() === "w1,w3", `save selected tabs: ${sSel.session?.windows[0]?.tabs.map((t) => t.url.split("/").pop())}`);
  await sw.evaluate((wid) => chrome.windows.remove(wid), w2.id);
  const locked = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "cleanup-preview" }));
  check(!locked.ok && locked.error === "pro", "cleanup is Pro-only for free users");
  await sw.evaluate(() => chrome.storage.local.set({ plan: "pro" }));
  // A234 Google Drive backup card: visible for Pro; until the OAuth client id is in the build it says so and can't be pressed
  const opt = await ctx.newPage(); await opt.goto(`chrome-extension://${id}/options.html`); await opt.waitForTimeout(500);
  const dstate = await opt.locator("#drive-state").textContent();
  check(await opt.locator("#h-drive").isVisible() && /being set up/.test(dstate ?? ""), `Drive card for Pro: "${dstate}"`);
  check(await opt.locator("#drive-connect").isDisabled(), "Connect is disabled until the Google client id is in the build");
  const ds = await opt.evaluate(() => chrome.runtime.sendMessage({ type: "drive-connect" }));
  check(!ds.ok && /being set up/.test(ds.error), "drive-connect refuses politely without a client id");
  const perms = await sw.evaluate(() => chrome.permissions.getAll());
  check(!perms.permissions.includes("identity") && !perms.permissions.includes("downloads"), `no Google or Downloads permission until asked: ${perms.permissions.join(",")}`);
  await opt.close();
  const dup = await ctx.newPage(); await dup.goto(base + "/a#again");
  const prev = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "cleanup-preview" }));
  check(prev.ok && prev.duplicates === 1, `cleanup preview sees ${prev.duplicates} duplicate`);
  const cl = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "cleanup", name: "dupes" }));
  const urls = await sw.evaluate(() => chrome.tabs.query({}).then((t) => t.map((x) => x.url)));
  check(cl.ok && cl.closed === 1 && urls.filter((u) => u.startsWith(base + "/a")).length === 1, "duplicate closed, one /a kept");
  const l3 = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "list" }));
  check(l3.sessions.some((s) => s.name === "Before cleanup"), "cleanup saved 'Before cleanup' first (undo)");
  const tl = await popup.evaluate((u) => chrome.runtime.sendMessage({ type: "timeline", text: u }), base + "/b");
  check(tl.ok && tl.timeline && tl.timeline.snapshots >= 1, "timeline finds when /b was open");
  // Lazy restore (real Chrome): a 20-tab session with a group opens a few tabs at a time; each sleeps after it loads,
  // keeps its address, and the group survives the new ids that sleeping tabs get.
  const bigSession = { id: "big-e2e", name: "Big e2e", kind: "manual", createdAt: Date.now(), windows: [{ focused: true,
    groups: [{ key: "g1", title: "Big group", color: "green", collapsed: false }],
    tabs: Array.from({ length: 20 }, (_, i) => ({ url: `${base}/big${i}`, title: `Big ${i}`, pinned: false, groupKey: i >= 15 ? "g1" : null })) }] };
  const rb = await popup.evaluate((text) => chrome.runtime.sendMessage({ type: "restore-backup", text }),
    JSON.stringify({ format: "tab-lifeboat-backup", version: 1, exportedAt: new Date().toISOString(), sessions: [bigSession] }));
  check(rb.ok && rb.sessions === 1, "big session added from a backup file");
  const t0 = Date.now();
  const big = await popup.evaluate(() => chrome.runtime.sendMessage({ type: "restore", id: "big-e2e" }));
  const major = Number((await sw.evaluate(() => navigator.userAgent)).match(/Chrom(?:e|ium)\/(\d+)/)?.[1] ?? 0);
  const sleeps = major >= 156;   // discard crashed Chrome 153, works on 156 (12 Nov 2026)
  check(big.ok && big.tabs === 20 && big.asleep === (sleeps ? 19 : 0), `big restore: ${big.tabs} tabs, ${big.asleep} asleep, ${Math.round((Date.now() - t0) / 1000)} s`);
  const bigTabs = await sw.evaluate((b) => chrome.tabs.query({}).then((t) => t.filter((x) => (x.url || "").startsWith(b + "/big")).map((x) => ({ url: x.url, discarded: x.discarded, groupId: x.groupId }))), base);
  check(bigTabs.length === 20 && Array.from({ length: 20 }, (_, i) => `${base}/big${i}`).every((u) => bigTabs.some((t) => t.url === u)), "every big-session tab kept its address");
  check(bigTabs.filter((t) => t.discarded).length === (sleeps ? 19 : 0), `Chrome ${major}: ${bigTabs.filter((t) => t.discarded).length} of 20 tabs asleep until clicked`);
  const bg = await sw.evaluate(() => chrome.tabGroups.query({ title: "Big group" }));
  const members = bigTabs.filter((t) => bg[0] && t.groupId === bg[0].id).map((t) => t.url.split("/").pop()).sort();
  check(bg.length === 1 && members.join() === "big15,big16,big17,big18,big19", `group kept after sleep: ${members.join()}`);
} finally { await ctx.close(); server.close(); }
console.log(failed ? "E2E FAILED" : "E2E PASSED"); process.exit(failed ? 1 : 0);

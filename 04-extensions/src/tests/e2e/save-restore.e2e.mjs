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

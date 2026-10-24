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
} finally { await ctx.close(); server.close(); }
console.log(failed ? "E2E FAILED" : "E2E PASSED"); process.exit(failed ? 1 : 0);

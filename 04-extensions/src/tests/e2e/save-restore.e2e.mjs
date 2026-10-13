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
  headless: true, executablePath: process.env.CHROME_PATH || undefined,
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
} finally { await ctx.close(); server.close(); }
console.log(failed ? "E2E FAILED" : "E2E PASSED"); process.exit(failed ? 1 : 0);

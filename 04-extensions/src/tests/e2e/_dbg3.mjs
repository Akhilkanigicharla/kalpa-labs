import { chromium } from "playwright"; import http from "node:http"; import os from "node:os"; import path from "node:path"; import fs from "node:fs";
const ext = path.resolve(import.meta.dirname, "../../.output/chrome-mv3");
const server = http.createServer((q, r) => { r.setHeader("content-type", "text/html"); r.end(`<title>P ${q.url}</title>`); }); await new Promise((ok) => server.listen(0, "0.0.0.0", ok));
const base = `http://127.0.0.1:${server.address().port}`;
const ctx = await chromium.launchPersistentContext(fs.mkdtempSync(path.join(os.tmpdir(), "lb-")), { headless: true, executablePath: "/usr/bin/google-chrome", args: ["--headless=new", `--disable-extensions-except=${ext}`, `--load-extension=${ext}`, "--no-sandbox"] });
let [sw] = ctx.serviceWorkers(); sw ??= await ctx.waitForEvent("serviceworker");
const step = process.argv[2];
try {
  const out = await sw.evaluate(async ({ base, step }) => {
    const log = [];
    const w = await chrome.windows.create({ url: base + "/h" });
    const ids = [];
    for (let i = 0; i < 4; i++) ids.push((await chrome.tabs.create({ windowId: w.id, url: (step.startsWith("x") ? base.replace("127.0.0.1", "127.0.0." + (i + 2)) : base) + "/x" + i, active: false })).id);
    for (;;) { const t = await Promise.all(ids.map((id) => chrome.tabs.get(id))); if (t.every((x) => x.status === "complete")) break; await new Promise((r) => setTimeout(r, 200)); }
    log.push("loaded"); const extra = Number(step.replace("x","")) || 0; await new Promise((r) => setTimeout(r, extra));
    if (step === "group-first") { await chrome.tabs.group({ tabIds: ids.slice(0, 2) }); log.push("grouped"); }
    const nids = []; for (const id of ids.slice(0, step === "one" ? 1 : 4)) { const d = await chrome.tabs.discard(id); nids.push(d.id); log.push("d" + id + "->" + d.id); }
    if (step === "group-after") { await chrome.tabs.group({ tabIds: nids.slice(0, 2) }); log.push("grouped-after"); }
    return log;
  }, { base, step });
  console.log("OUT", JSON.stringify(out));
} catch (e) { console.log("ERR", String(e).slice(0, 120));
  try { const p = await ctx.newPage(); console.log("ALIVE pages", ctx.pages().length); const sws = ctx.serviceWorkers(); console.log("SWS", sws.length);
    const s2 = sws[0] ?? await ctx.waitForEvent("serviceworker", { timeout: 5000 }); console.log("TABS", JSON.stringify(await s2.evaluate(() => chrome.tabs.query({}).then((t) => t.map((x) => [x.url, x.discarded])))));
  } catch (e2) { console.log("DEAD", String(e2).slice(0, 120)); } }
await ctx.close().catch(() => {}); server.close();

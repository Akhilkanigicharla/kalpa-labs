// A13 screens: the real built popup and options page, light + dark, at 390 px (options also at 1280 px).
// Also checks the backup file end to end: export → wipe one session → restore from the file → nothing doubled.
// Run: npm run test:screens   (writes PNGs to 04-extensions/design/screens/, not in git)
import { chromium } from "playwright";
import os from "node:os";
import path from "node:path";
import fs from "node:fs";
import http from "node:http";

const ext = path.resolve(import.meta.dirname, "../../.output/chrome-mv3");
const out = path.resolve(import.meta.dirname, "../../../design/screens");
fs.mkdirSync(out, { recursive: true });
const server = http.createServer((req, res) => { res.setHeader("content-type", "text/html"); res.end(`<title>Docs ${req.url}</title><h1>${req.url}</h1>`); }).listen(0);
const base = `http://127.0.0.1:${server.address().port}`;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "lifeboat-screens-"));
const ctx = await chromium.launchPersistentContext(profile, {
  headless: true,
  ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: "chromium" }),
  args: ["--headless=new", `--disable-extensions-except=${ext}`, `--load-extension=${ext}`, "--no-sandbox"],
});
let failed = false;
const check = (ok, msg) => { console.log(`  ${ok ? "✓" : "✗"} ${msg}`); if (!ok) failed = true; };
const LAYOUT = `() => {
  const vw = document.documentElement.clientWidth, bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    let p = el.parentElement, clip = false;
    while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o !== 'visible') { clip = true; break; } p = p.parentElement; }
    if (!clip && (r.right > vw + 1 || r.left < -1)) bad.push(el.tagName + (el.id ? '#' + el.id : '') + ' ' + Math.round(r.right));
  }
  const small = [...document.querySelectorAll('main button:not([hidden])')].filter((b) => { const r = b.getBoundingClientRect(); return r.width && r.height < 36; }).map((b) => b.textContent.trim().slice(0, 24));
  return { scrollW: document.documentElement.scrollWidth, vw, bad: bad.slice(0, 5), small,
    rozha: [...document.fonts].some((f) => f.family.includes('Rozha') && f.status === 'loaded'),
    bg: getComputedStyle(document.body).backgroundColor };
}`;
try {
  let [sw] = ctx.serviceWorkers(); sw ??= await ctx.waitForEvent("serviceworker");
  const id = new URL(sw.url()).host;
  const pg = await ctx.newPage(); await pg.goto(`chrome-extension://${id}/popup.html`);
  const msg = (m) => pg.evaluate((x) => chrome.runtime.sendMessage(x), m);
  // realistic data: a OneTab import (3 groups), a manual save, one auto snapshot
  const onetab = ["Research", "Shopping", "Reading"].map((g, i) => Array.from({ length: 4 + i * 3 }, (_, j) => `https://example.com/${g.toLowerCase()}/${j} | ${g} page ${j + 1}`).join("\n")).join("\n\n");
  await msg({ type: "import", text: onetab });
  const open = [];
  for (const p of ["/plan", "/budget", "/notes"]) { const t = await ctx.newPage(); await t.goto(base + p); open.push(t); }
  await msg({ type: "save", name: "Before the Chrome update" });
  await msg({ type: "snapshot" });
  for (const t of open) await t.close();

  // backup file round trip
  const exp = await msg({ type: "export" });
  check(exp.ok && /^tab-lifeboat-backup-\d{4}-\d{2}-\d{2}\.json$/.test(exp.fileName), `export file ${exp.fileName}`);
  const before = (await msg({ type: "list" })).sessions;
  const imported = before.find((s) => s.kind === "import");
  await msg({ type: "delete", id: imported.id });
  const prev = await msg({ type: "preview-backup", text: exp.json });
  check(prev.ok && prev.sessions === before.length, `backup preview: ${prev.sessions} sessions, ${prev.tabs} tabs`);
  await msg({ type: "restore-backup", text: exp.json });
  await msg({ type: "restore-backup", text: exp.json }); // twice on purpose
  const after = (await msg({ type: "list" })).sessions;
  check(after.length === before.length && after.some((s) => s.id === imported.id), `restored from file, no doubles (${after.length} sessions)`);
  const bad = await msg({ type: "preview-backup", text: '{"hello":1}' });
  check(!bad.ok && /not a Tab Lifeboat backup/.test(bad.error), "a wrong file is refused in plain English");

  const shots = [["popup", "popup.html", 390], ["options", "options.html", 390], ["options-wide", "options.html", 1280]];
  for (const scheme of ["light", "dark"]) {
    const bgs = [];
    for (const [name, page, width] of shots) {
      await pg.emulateMedia({ colorScheme: scheme });
      await pg.setViewportSize({ width, height: 900 });
      await pg.goto(`chrome-extension://${id}/${page}`);
      await pg.waitForSelector("#list li"); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(350);
      const r = await pg.evaluate(`(${LAYOUT})()`);
      bgs.push(r.bg);
      const tag = `${name} ${scheme}`;
      check(r.scrollW <= r.vw && !r.bad.length, `${tag}: no sideways scroll (${r.scrollW}/${r.vw}) ${r.bad.join(", ")}`);
      check(r.rozha, `${tag}: Rozha One loaded from the bundle`);
      check(!r.small.length, `${tag}: buttons at least 36 px tall ${r.small.join(", ")}`);
      if (name === "options") {
        const st = await pg.evaluate(() => [...document.querySelectorAll(".stats b")].map((b) => b.textContent));
        check(st.every((t) => t && t !== "–" && !/NaN|undefined/.test(t)), `${tag}: proof numbers filled ${JSON.stringify(st)}`);
      }
      await pg.screenshot({ path: path.join(out, `${name}-${scheme}.png`), fullPage: true });
    }
    if (scheme === "dark") check(bgs.every((b) => b !== "rgb(242, 238, 227)"), "dark theme really switches the background");
  }
  // popup button opens the options page
  await pg.emulateMedia({ colorScheme: "light" }); await pg.goto(`chrome-extension://${id}/popup.html`);
  const [opt] = await Promise.all([ctx.waitForEvent("page"), pg.click("#more")]);
  await opt.waitForLoadState(); check(opt.url().endsWith("/options.html"), "popup → Backups and settings opens the options tab");
} finally { await ctx.close(); server.close(); }
console.log(failed ? "SCREENS FAILED" : `SCREENS PASSED → ${out}`); process.exit(failed ? 1 : 0);

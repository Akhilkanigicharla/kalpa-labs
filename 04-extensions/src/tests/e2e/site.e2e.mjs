// E9 site check: builds site/_dist, then every page at 390 px (light + dark) and 1280 px: no sideways scroll,
// no requests to other sites, internal links resolve, 44 px tap targets on buttons. Screenshots → 04-extensions/design/site/.
// Run: npm run test:site
import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import path from "node:path";
import fs from "node:fs";
import http from "node:http";

const site = path.resolve(import.meta.dirname, "../../../site");
const out = path.resolve(import.meta.dirname, "../../../design/site");
execFileSync(process.execPath, [path.join(site, "build.mjs")], { stdio: "inherit", env: { ...process.env, CONTACT_EMAIL: process.env.CONTACT_EMAIL || "hello@example.com" } });
fs.mkdirSync(out, { recursive: true });
const dist = path.join(site, "_dist");
const types = { ".html": "text/html", ".css": "text/css", ".png": "image/png", ".woff": "font/woff" };
const server = http.createServer((req, res) => {
  const f = path.join(dist, decodeURIComponent(new URL(req.url, "http://x").pathname).replace(/\/$/, "/index.html"));
  if (!f.startsWith(dist) || !fs.existsSync(f)) { res.statusCode = 404; return res.end("nope"); }
  res.setHeader("content-type", types[path.extname(f)] || "application/octet-stream"); res.end(fs.readFileSync(f));
}).listen(0);
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {});
let failed = false;
const check = (ok, msg) => { console.log(`  ${ok ? "✓" : "✗"} ${msg}`); if (!ok) failed = true; };
try {
  for (const scheme of ["light", "dark"]) for (const width of [390, 1280]) {
    const pg = await browser.newPage({ viewport: { width, height: 900 }, colorScheme: scheme });
    const outside = []; const missing = [];
    pg.on("request", (r) => { if (!r.url().startsWith(base) && !r.url().startsWith("data:")) outside.push(r.url()); });
    pg.on("response", (r) => { if (r.status() >= 400) missing.push(r.url()); });
    for (const page of ["index", "privacy", "terms"]) {
      await pg.goto(`${base}/${page}.html`); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(150);
      const r = await pg.evaluate(() => ({ sw: document.documentElement.scrollWidth, vw: document.documentElement.clientWidth, bg: getComputedStyle(document.body).backgroundColor,
        small: [...document.querySelectorAll(".btn, summary")].filter((e) => e.getBoundingClientRect().height < 44).length,
        links: [...document.querySelectorAll("a[href]")].map((a) => a.getAttribute("href")).filter((h) => !/^(mailto:|https?:|#)/.test(h)) }));
      const tag = `${page} ${width}px ${scheme}`;
      check(r.sw <= r.vw, `${tag}: no sideways scroll (${r.sw}/${r.vw})`);
      check(!r.small, `${tag}: tap targets ≥ 44 px`);
      check(scheme === "light" ? r.bg === "rgb(242, 238, 227)" : r.bg !== "rgb(242, 238, 227)", `${tag}: ${scheme} background`);
      for (const h of r.links) check(fs.existsSync(path.join(dist, h)), `${tag}: link ${h} exists`);
      if (width === 390 || page === "index") await pg.screenshot({ path: path.join(out, `${page}-${width}-${scheme}.png`), fullPage: true });
    }
    check(!outside.length, `${scheme} ${width}px: no requests to other sites ${outside.slice(0, 2).join(" ")}`);
    check(!missing.length, `${scheme} ${width}px: nothing missing ${missing.slice(0, 2).join(" ")}`);
    await pg.close();
  }
} finally { await browser.close(); server.close(); }
console.log(failed ? "SITE FAILED" : `SITE PASSED → ${out}`); process.exit(failed ? 1 : 0);

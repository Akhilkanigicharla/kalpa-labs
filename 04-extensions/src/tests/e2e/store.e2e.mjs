// E10 store assets from the REAL built extension: raw screens (store/raw/, also used by the site) and the
// Chrome Web Store images (store/): 1280×800 screenshots (light + dark), 440×280 small promo tile, 1400×560 marquee.
// Run: npm run test:store
import { chromium } from "playwright";
import os from "node:os";
import path from "node:path";
import fs from "node:fs";
import http from "node:http";

const ext = path.resolve(import.meta.dirname, "../../.output/chrome-mv3");
const store = path.resolve(import.meta.dirname, "../../../store");
const raw = path.join(store, "raw");
const root = path.resolve(import.meta.dirname, "../../../..");
fs.mkdirSync(raw, { recursive: true });
const titles = { "/plan": "Q4 plan — Docs", "/budget": "Budget 2027 — Sheets", "/notes": "Meeting notes", "/flights": "Flights to Goa", "/recipes": "Dal makhani recipe" };
const server = http.createServer((req, res) => { res.setHeader("content-type", "text/html"); res.end(`<title>${titles[req.url] || req.url}</title><h1>${req.url}</h1>`); }).listen(0);
const base = `http://127.0.0.1:${server.address().port}`;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "lifeboat-store-"));
const ctx = await chromium.launchPersistentContext(profile, {
  headless: true, ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: "chromium" }),
  args: ["--headless=new", `--disable-extensions-except=${ext}`, `--load-extension=${ext}`, "--no-sandbox"],
});
let failed = false;
const check = (ok, msg) => { console.log(`  ${ok ? "✓" : "✗"} ${msg}`); if (!ok) failed = true; };
const png = (f) => `data:image/png;base64,${fs.readFileSync(f).toString("base64")}`;
const css = fs.readFileSync(path.join(root, "00-hq/design/tokens.css"), "utf8");
const font = (f) => `data:font/woff;base64,${fs.readFileSync(path.join(root, "00-hq/design/fonts", f)).toString("base64")}`;
const faces = `@font-face{font-family:"Rozha One";src:url(${font("rozha-one-latin-400-normal.woff")})}@font-face{font-family:"Anek Latin";font-weight:400 600;src:url(${font("anek-latin-latin-600-normal.woff")})}@font-face{font-family:"Anek Latin";font-weight:700;src:url(${font("anek-latin-latin-700-normal.woff")})}`;

try {
  let [sw] = ctx.serviceWorkers(); sw ??= await ctx.waitForEvent("serviceworker");
  const id = new URL(sw.url()).host;
  const pg = await ctx.newPage(); await pg.goto(`chrome-extension://${id}/popup.html`);
  const msg = (m) => pg.evaluate((x) => chrome.runtime.sendMessage(x), m);
  const onetab = ["Research", "Shopping", "Reading"].map((g, i) => Array.from({ length: 5 + i * 4 }, (_, j) => `https://example.com/${g.toLowerCase()}/${j} | ${g} — page ${j + 1}`).join("\n")).join("\n\n");
  await msg({ type: "import", text: onetab });
  const open = []; for (const p of Object.keys(titles)) { const t = await ctx.newPage(); await t.goto(base + p); open.push(t); }
  await msg({ type: "save", name: "Before the Chrome update" });
  await msg({ type: "snapshot" });
  for (const t of open) await t.close();

  for (const scheme of ["light", "dark"]) {
    await pg.emulateMedia({ colorScheme: scheme });
    await pg.setViewportSize({ width: 360, height: 600 }); await pg.goto(`chrome-extension://${id}/popup.html`);
    await pg.waitForSelector("#list li"); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(300);
    await pg.screenshot({ path: path.join(raw, `popup-${scheme}.png`) });
    await pg.click("#importBox summary"); await pg.fill("#importText", "https://example.com/reading/1 | Reading — page 1\nhttps://example.com/reading/2 | Reading — page 2");
    await pg.waitForTimeout(250); await pg.screenshot({ path: path.join(raw, `popup-import-${scheme}.png`) });
    await pg.setViewportSize({ width: 820, height: 1000 }); await pg.goto(`chrome-extension://${id}/options.html`);
    await pg.waitForSelector("#list li"); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(300);
    await pg.screenshot({ path: path.join(raw, `options-${scheme}.png`) });
  }

  // composed listing images: headline on the left, the real screen on the right (Kalamkari, world colour l4)
  const comp = await ctx.newPage();
  const frame = (w, h, scheme, body) => `<!doctype html><html data-theme="${scheme}"><style>${css}${faces}
    *{box-sizing:border-box}html,body{margin:0;width:${w}px;height:${h}px;overflow:hidden}
    body{background:var(--bg);color:var(--fg);font:400 22px/1.4 "Anek Latin",sans-serif;display:flex;align-items:center;gap:56px;padding:0 64px;position:relative}
    .temple{position:absolute;left:0;right:0;top:0;height:10px;background:radial-gradient(circle at 5px 4px,var(--gold) 2px,transparent 2.5px) 0 0/10px 10px,var(--hero)}
    h1{font:400 56px/1.08 "Rozha One",serif;margin:0 0 18px}.t{flex:1}.t p{color:var(--muted);margin:0 0 10px}
    .shot{border-radius:18px;border:1px solid var(--rule);box-shadow:0 30px 60px -30px color-mix(in srgb,var(--l4) 60%,transparent)}
    .brand{display:flex;gap:12px;align-items:center;font:400 28px "Rozha One",serif;color:var(--l4);margin-bottom:22px}.brand img{width:44px}</style><body><div class="temple"></div>${body}</body></html>`;
  const icon = png(path.resolve(import.meta.dirname, "../../public/icon/128.png"));
  const slides = [
    ["1-save", "Save every tab in one click.", ["All windows, pinned tabs and tab groups.", "Nothing gets closed."], "popup", 600],
    ["2-proof", "See that your tabs are safe.", ["Automatic snapshots on your computer.", "The last one, right at the top."], "options", 660],
    ["3-import", "Move in from OneTab or Session Buddy.", ["Preview first, then import.", "Groups keep their names and colours."], "popup-import", 600],
    ["4-private", "We never see your tabs.", ["No account, no servers, no analytics.", "Download a backup file you own."], "options", 660],
  ];
  for (const scheme of ["light", "dark"]) {
    for (const [name, h, lines, screen, height] of slides) {
      const img = png(path.join(raw, `${screen}-${scheme}.png`));
      await comp.setViewportSize({ width: 1280, height: 800 });
      await comp.setContent(frame(1280, 800, scheme, `<div class="t"><div class="brand"><img src="${icon}">Tab Lifeboat</div><h1>${h}</h1>${lines.map((l) => `<p>${l}</p>`).join("")}</div>
        <img class="shot" src="${img}" style="height:${height}px;${screen === "options" ? "width:600px;object-fit:cover;object-position:center top" : ""}">`));
      await comp.evaluate(() => document.fonts.ready);
      await comp.screenshot({ path: path.join(store, `screenshot-${name}-${scheme}.png`) });
    }
  }
  await comp.setViewportSize({ width: 440, height: 280 });
  await comp.setContent(frame(440, 280, "light", `<div class="t" style="text-align:center"><img src="${icon}" style="width:72px"><h1 style="font-size:40px;margin:8px 0 6px">Tab Lifeboat</h1><p style="font-size:18px">Your tabs, backed up automatically.</p></div>`));
  await comp.evaluate(() => document.fonts.ready); await comp.screenshot({ path: path.join(store, "promo-small-440x280.png") });
  await comp.setViewportSize({ width: 1400, height: 560 });
  await comp.setContent(frame(1400, 560, "dark", `<div class="t"><div class="brand"><img src="${icon}">Tab Lifeboat</div><h1>Your tabs, backed up automatically.</h1><p>Save all tabs and groups in one click. Snapshots on your computer. We never see them.</p></div>
    <img class="shot" src="${png(path.join(raw, "popup-dark.png"))}" style="height:480px">`));
  await comp.evaluate(() => document.fonts.ready); await comp.screenshot({ path: path.join(store, "promo-marquee-1400x560.png") });

  const { execFileSync } = await import("node:child_process");
  for (const f of fs.readdirSync(store).filter((f) => f.endsWith(".png"))) {
    const [w, h] = execFileSync("python3", ["-c", `from PIL import Image;print(*Image.open("${path.join(store, f)}").size)`]).toString().trim().split(" ").map(Number);
    const want = f.startsWith("screenshot") ? [1280, 800] : f.includes("440x280") ? [440, 280] : [1400, 560];
    check(w === want[0] && h === want[1], `${f} is ${w}×${h}`);
  }
} finally { await ctx.close(); server.close(); }
console.log(failed ? "STORE ASSETS FAILED" : `STORE ASSETS PASSED → ${store}`); process.exit(failed ? 1 : 0);

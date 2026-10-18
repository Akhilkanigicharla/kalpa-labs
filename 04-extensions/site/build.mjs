// Builds the Tab Lifeboat site into site/_dist for GitHub Pages (also used by the tests and screenshots).
// CONTACT_EMAIL (a GitHub repository variable Akhil sets) goes into the policy; `--release` refuses to build without it.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const dist = path.join(here, "_dist");
const release = process.argv.includes("--release");
const email = process.env.CONTACT_EMAIL || "";
if (release && !/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(email)) throw new Error("Set the CONTACT_EMAIL repository variable before publishing the privacy policy");
const updated = process.env.POLICY_UPDATED || "18 October 2026";

fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(path.join(dist, "vendor/fonts"), { recursive: true });
fs.copyFileSync(path.join(root, "00-hq/design/tokens.css"), path.join(dist, "vendor/tokens.css"));
for (const f of ["anek-latin-latin-600-normal.woff", "anek-latin-latin-700-normal.woff", "rozha-one-latin-400-normal.woff"]) fs.copyFileSync(path.join(root, "00-hq/design/fonts", f), path.join(dist, "vendor/fonts", f));
fs.cpSync(path.join(here, "..", "src/public/icon"), path.join(dist, "icon"), { recursive: true });
fs.mkdirSync(path.join(dist, "shots"));
for (const f of ["screenshot-2-proof-light.png", "screenshot-2-proof-dark.png"]) fs.copyFileSync(path.join(here, "..", "store", f), path.join(dist, "shots", f));
fs.copyFileSync(path.join(here, "site.css"), path.join(dist, "site.css"));

const pages = { index: "Home", privacy: "Privacy", terms: "Terms & refunds" };
const nav = (cur) => `<div class="temple"></div><nav class="top wrap"><a class="brand" href="index.html"><img src="icon/128.png" alt="" width="32" height="32">Tab Lifeboat</a>
<span class="links">${Object.entries(pages).map(([p, label]) => `<a href="${p}.html"${p === cur ? ' aria-current="page"' : ""}>${label}</a>`).join("")}</span></nav>`;
const footer = `<footer class="wrap"><p>Tab Lifeboat is made by Kalpa Labs, Hyderabad, India. <a href="privacy.html">Privacy</a> · <a href="terms.html">Terms &amp; refunds</a> · <a href="mailto:${email || "{{CONTACT_EMAIL}}"}">Contact</a></p></footer>`;
for (const p of Object.keys(pages)) {
  const html = fs.readFileSync(path.join(here, `${p}.html`), "utf8").replace(/\{\{NAV:(\w+)\}\}/, (_, c) => nav(c)).replace("{{FOOTER}}", footer)
    .replaceAll("{{UPDATED}}", updated).replaceAll("{{CONTACT_EMAIL}}", email || "{{CONTACT_EMAIL}}");
  fs.writeFileSync(path.join(dist, `${p}.html`), html);
}
console.log(`site built → ${dist}${email ? "" : " (no CONTACT_EMAIL yet: preview only)"}`);

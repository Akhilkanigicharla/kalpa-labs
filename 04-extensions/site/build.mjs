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
fs.copyFileSync(path.join(here, "404.html"), path.join(dist, "404.html")); // GitHub Pages serves this for unknown paths

const pages = { index: "Home", privacy: "Privacy", terms: "Terms & refunds" };
// SEO (00-hq/design/SEO-CHECKS.md). GitHub Pages project URL; override with SITE_URL when a custom domain is set.
const SITE = (process.env.SITE_URL || "https://akhilkanigicharla.github.io/kalpa-labs").replace(/\/$/, "");
const urlOf = (p) => (p === "index" ? `${SITE}/` : `${SITE}/${p}`);
const SEO = {
  index: { title: null, desc: "A Chrome extension that saves all your tabs and groups in one click and keeps automatic snapshots, so a crash or update never wipes them." },
  privacy: { title: "Privacy policy · Tab Lifeboat Chrome extension", desc: "What Tab Lifeboat stores (only on your computer), what it never collects, and how to delete your data. Plain words, India DPDP Act." },
  terms: { title: "Terms and refunds · Tab Lifeboat Chrome extension", desc: "The terms for using Tab Lifeboat, what the free and Pro plans include, and how refunds work. Made by Kalpa Labs, Hyderabad." },
};
const esc = (t) => t.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
const ORG = { "@type": "Organization", "@id": `${SITE}/#org`, name: "Kalpa Labs", url: "https://kalpalabs.dpdns.org/",
  address: { "@type": "PostalAddress", addressLocality: "Hyderabad", addressRegion: "Telangana", addressCountry: "IN" } };
function seoHead(p, title) {
  const { desc } = SEO[p], url = urlOf(p);
  const graph = p === "index"
    ? [ORG, { "@type": "WebSite", "@id": `${SITE}/#site`, name: "Tab Lifeboat", url: `${SITE}/`, publisher: { "@id": `${SITE}/#org` } },
       { "@type": "SoftwareApplication", name: "Tab Lifeboat", applicationCategory: "BrowserApplication", operatingSystem: "Chrome",
         description: desc, publisher: { "@id": `${SITE}/#org` } }]
    : [ORG, { "@type": "WebPage", name: title, url, description: desc, isPartOf: { "@type": "WebSite", url: `${SITE}/` } }];
  return `<link rel="canonical" href="${url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Tab Lifeboat">
<meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${url}"><meta property="og:image" content="${SITE}/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Tab Lifeboat: your tabs, backed up automatically.">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="${SITE}/og.png">
<script type="application/ld+json">${JSON.stringify({ "@context": "https://schema.org", "@graph": graph })}</script>
`;
}
const nav = (cur) => `<div class="temple"></div><nav class="top wrap"><a class="brand" href="index.html"><img src="icon/128.png" alt="" width="32" height="32">Tab Lifeboat</a>
<span class="links">${Object.entries(pages).map(([p, label]) => `<a href="${p}.html"${p === cur ? ' aria-current="page"' : ""}>${label}</a>`).join("")}</span></nav>`;
const footer = `<footer class="wrap"><p>Tab Lifeboat is made by Kalpa Labs, Hyderabad, India. <a href="privacy.html">Privacy</a> · <a href="terms.html">Terms &amp; refunds</a> · <a href="mailto:${email || "{{CONTACT_EMAIL}}"}">Contact</a></p></footer>`;
for (const p of Object.keys(pages)) {
  const html = fs.readFileSync(path.join(here, `${p}.html`), "utf8").replace(/\{\{NAV:(\w+)\}\}/, (_, c) => nav(c)).replace("{{FOOTER}}", footer)
    .replaceAll("{{UPDATED}}", updated).replaceAll("{{CONTACT_EMAIL}}", email || "{{CONTACT_EMAIL}}");
  let out = html;
  if (SEO[p].title) out = out.replace(/<title>[^<]*<\/title>/, `<title>${esc(SEO[p].title)}</title>`);
  out = out.replace(/<meta name="description"[^>]*>\s*/, "");
  const title = (out.match(/<title>([^<]*)<\/title>/) || [, "Tab Lifeboat"])[1];
  out = out.replace("</head>", `<meta name="description" content="${esc(SEO[p].desc)}">\n${seoHead(p, title)}</head>`);
  fs.writeFileSync(path.join(dist, `${p}.html`), out);
}
fs.copyFileSync(path.join(here, "og.png"), path.join(dist, "og.png"));
fs.writeFileSync(path.join(dist, "robots.txt"), `User-agent: *\nAllow: /\n\nSitemap: ${SITE}/sitemap.xml\n`);
const day = new Date().toISOString().slice(0, 10);
fs.writeFileSync(path.join(dist, "sitemap.xml"), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${Object.keys(pages).map((p) => `  <url><loc>${urlOf(p)}</loc><lastmod>${day}</lastmod></url>`).join("\n")}\n</urlset>\n`);
fs.writeFileSync(path.join(dist, "llms.txt"), `# Tab Lifeboat\n\n> A Chrome extension by Kalpa Labs (Hyderabad, India) that saves all your tabs and tab groups in one click and keeps automatic snapshots on your own computer, so a crash, an update or a reinstall never wipes them. No account; nothing leaves your computer on the free plan.\n\n- Status: not yet on the Chrome Web Store.\n\n## Pages\n\n${Object.entries(pages).map(([p, l]) => `- [${l}](${urlOf(p)})`).join("\n")}\n`);
fs.writeFileSync(path.join(dist, "404.html"), `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>Page not found · Tab Lifeboat</title><link rel="stylesheet" href="${SITE}/vendor/tokens.css"><link rel="stylesheet" href="${SITE}/site.css"></head><body><main class="wrap" style="padding:64px 0;text-align:center"><h1>This page isn't here</h1><p>The link may be old or mistyped.</p><p><a class="btn" href="${SITE}/" style="display:inline-flex;min-height:48px;align-items:center;padding:0 24px">Go to Tab Lifeboat</a></p></main></body></html>\n`);
console.log(`site built → ${dist}${email ? "" : " (no CONTACT_EMAIL yet: preview only)"}`);

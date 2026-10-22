// Builds the "my customers" PWA in place (Netlify build command, also run by the tests).
// Copies the shared core + Kalpavruksha tokens/fonts into web/vendor/ and writes web/config.js from env.
// SUPABASE_URL and SUPABASE_ANON_KEY are the PUBLIC project URL and anon (publishable) key; RLS guards the data.
// With no SUPABASE_URL the page runs on made-up demo data (90000 xxxxx numbers) so it can be looked at.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const vendor = path.join(here, "vendor");
fs.rmSync(vendor, { recursive: true, force: true }); fs.mkdirSync(path.join(vendor, "fonts"), { recursive: true });
for (const f of ["parse.mjs", "reminders.mjs", "quota.mjs"]) fs.copyFileSync(path.join(here, "..", "lib", f), path.join(vendor, f));
fs.copyFileSync(path.join(root, "00-hq/design/tokens.css"), path.join(vendor, "tokens.css"));
const fonts = ["anek-latin-latin-600-normal.woff", "anek-latin-latin-700-normal.woff", "anek-telugu-telugu-400-normal.woff", "anek-telugu-telugu-700-normal.woff", "rozha-one-latin-400-normal.woff"];
for (const f of fonts) fs.copyFileSync(path.join(root, "00-hq/design/fonts", f), path.join(vendor, "fonts", f));

const url = process.env.SUPABASE_URL || "";
const anon = process.env.SUPABASE_ANON_KEY || "";
if (url && !/^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(url)) throw new Error("SUPABASE_URL should look like https://<project>.supabase.co");
fs.writeFileSync(path.join(here, "config.js"), `export default ${JSON.stringify({ supabaseUrl: url, anonKey: anon, demo: !url })};\n`);

// the service worker's cache name changes whenever any shell file changes, so phones pick up new versions
const shell = ["index.html", "app.css", "app.mjs", "logic.mjs", "i18n.mjs", "config.js", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/maskable-512.png",
  ...["parse.mjs", "reminders.mjs", "quota.mjs", "tokens.css"].map((f) => `vendor/${f}`), ...fonts.map((f) => `vendor/fonts/${f}`)];
const hash = crypto.createHash("sha256"); for (const f of shell) hash.update(fs.readFileSync(path.join(here, f)));
const sw = fs.readFileSync(path.join(here, "sw.template.js"), "utf8").replace("__VERSION__", hash.digest("hex").slice(0, 12)).replace("__SHELL__", JSON.stringify(shell.map((f) => "/" + f)));
fs.writeFileSync(path.join(here, "sw.js"), sw);
console.log(`web built (${url ? "live" : "demo"} mode)`);

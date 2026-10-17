// A13: the JobCard screens show what the real core produces, prices match PLAN.md, nothing leaves the phone.
// Run: cd 02-jobcard && npm test      (screens themselves: python3 02-jobcard/design/screens.py)
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { build, PLAN } from "../design/sample.mjs";

const DIR = path.resolve(import.meta.dirname, "../design");
const read = (f) => fs.readFileSync(path.join(DIR, f), "utf8");
const embedded = () => JSON.parse(read("app.html").match(/<script id="jc-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const D = await build();

test("app.html carries fresh data from the real parser + invoice core (run sample.mjs after changing the core)", () => {
  assert.deepEqual(embedded(), JSON.parse(JSON.stringify(D)));
  assert.equal(read("invoice-sample.html"), D.invoice.html);
});

test("the voice note becomes a complete card and its bill adds up", () => {
  const c = D.job.card;
  assert.deepEqual(c.missing, []);
  assert.ok(Object.values(D.job.heard).every(Boolean), "every 'say these' chip is ticked");
  const parts = c.parts.reduce((s, p) => s + p.rate, 0);
  assert.equal(parts, c.total, "parts add up to the total the technician said");
  assert.equal(D.invoice.payable, parts * 100, "bill total = parts");
  assert.equal(D.invoice.kind, "unregistered");
  assert.match(D.invoice.html, /Bill of Supply \(not a tax invoice\)/);
  assert.doesNotMatch(D.invoice.html, /GSTIN|CGST|SGST/);
  assert.match(D.invoice.upi, /^upi:\/\/pay\?pa=jobcard\.demo%40upi&.*am=3250\.00&cu=INR/);
  assert.match(D.invoice.number, /^JC\/26-27\/\d{4}$/);
});

test("reminders: only jobs where a next service was said, due within 30 days, latest first", () => {
  assert.ok(D.reminders.length >= 3);
  assert.ok(!D.reminders.some((r) => r.name === "Lakshmi"), "no 'next service' in her note, so no reminder (never invented)");
  assert.ok(!D.reminders.some((r) => r.name === "Farhan"), "due in 42 days: not this month");
  assert.ok(D.reminders.every((r, i, a) => r.inDays <= 30 && (!i || a[i - 1].inDays <= r.inDays)));
  assert.ok(D.reminders.some((r) => r.name === "Anjali"), "'Customer Anjali' is read as a name (parser fix found here)");
  for (const r of D.reminders) assert.match(r.phone, /^90000\d{5}$/, "made-up numbers only");
});

test("prices on the screens are PLAN.md §2", () => {
  const plan = fs.readFileSync(path.resolve(DIR, "../PLAN.md"), "utf8");
  assert.match(plan, new RegExp(`\\*\\*Pro\\*\\* \\| \\*\\*₹${PLAN.pro}/month\\*\\* or ₹${PLAN.proYear.toLocaleString("en-IN")}/year`));
  assert.match(plan, new RegExp(`\\| Free \\| ₹0 \\| ${PLAN.freeCards} job cards/month`));
  assert.match(plan, new RegExp(`\\| Team \\| ₹${PLAN.team}/month`));
});

test("no external requests: fonts are self-hosted, the only outside links are tel: and wa.me taps", () => {
  const html = read("app.html").replace(/<script id="jc-data"[\s\S]*?<\/script>/, ""), css = read("jc.css"), js = read("jc.js");
  assert.doesNotMatch(html + css, /https?:\/\//);
  assert.deepEqual([...new Set(js.match(/https?:\/\/[^/`"']+/g))], ["https://wa.me"]);
  for (const f of css.match(/url\(([^)]+)\)/g).map((u) => u.slice(4, -1))) assert.ok(fs.existsSync(path.resolve(DIR, f)), `font ${f} exists`);
});

test("Telugu is never put in the display face", () => {
  const css = read("jc.css");
  assert.match(css, /\.te\{font-family:"Anek Telugu"/);
  // every Telugu run in the page sits in a .te element or in body text (body font has Anek Telugu)
  const html = read("app.html").replace(/<script[\s\S]*?<\/script>/g, "");
  for (const m of html.matchAll(/<h[12][^>]*>([^<]*)<\/h[12]>/g)) assert.doesNotMatch(m[1], /[ఀ-౿]/, `heading "${m[1]}"`);
});

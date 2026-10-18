// E9 + E10: the public policy and store text must say exactly what the extension does.
import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";
import config from "../wxt.config";

const site = (f: string) => fs.readFileSync(path.resolve(__dirname, "../../site", f), "utf8");
const store = (f: string) => fs.readFileSync(path.resolve(__dirname, "../../store", f), "utf8");
const options = fs.readFileSync(path.resolve(__dirname, "../entrypoints/options/index.html"), "utf8");
const perms = ((config as { manifest: { permissions: string[] } }).manifest.permissions);

describe("privacy policy matches the extension", () => {
  const policy = site("privacy.html");
  it("names every permission the manifest asks for, and no host permissions are requested", () => {
    for (const p of perms) expect(policy).toContain(`<b>${p}</b>`);
    expect((config as { manifest: Record<string, unknown> }).manifest.host_permissions).toBeUndefined();
  });
  it("carries both Limited Use statements word for word", () => {
    expect(policy).toContain("The use of information received from Google APIs will adhere to the Chrome Web Store User Data Policy, including the Limited Use requirements.");
    expect(policy).toContain("use and transfer of information received from Google APIs to any other app will adhere to the Google API Services User Data Policy, including the Limited Use requirements.");
  });
  it("says where data lives, who gets licence data, how to delete, and a DPDP grievance contact", () => {
    for (const s of ["IndexedDB", "Dodo Payments", "drive.file", "Uninstalling", "Digital Personal Data Protection Act, 2023", "{{CONTACT_EMAIL}}", "no analytics"]) expect(policy).toContain(s);
  });
  it("loads nothing from other sites", () => {
    for (const f of ["index.html", "privacy.html", "terms.html"]) expect(site(f)).not.toMatch(/(src|href)="https?:\/\/(?!wa\.me)/);
  });
});

describe("landing page and terms", () => {
  it("prices match the options page", () => {
    for (const price of options.match(/\$\d+ \/ ₹[\d,]+/g)!) { expect(site("index.html")).toContain(price); expect(site("terms.html")).toContain(price); }
  });
  it("has exactly 3 FAQ and a refund window", () => {
    expect(site("index.html").match(/<details>/g)).toHaveLength(3);
    expect(site("terms.html")).toMatch(/within <b>14 days<\/b>/);
  });
});

describe("store listing text", () => {
  const listing = store("listing.md");
  it("discloses paid features before install and links the policy", () => {
    expect(listing).toMatch(/Pro .*licence key/i); expect(listing).toContain("privacy.html");
    const short = listing.match(/## Short description\n\n(.+)\n/)![1] ?? ""; expect(short.length).toBeLessThanOrEqual(132);
  });
  it("justifies every permission", () => { for (const p of perms) expect(listing).toContain(`**${p}**`); });
});

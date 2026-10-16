// A11: kit landing data must match 03-kits/PLAN.md and India's consumer rules (no dark patterns, policy pages present).
import { describe, expect, test } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { KITS, LADDER, LEGAL, CONTACT, kitBySlug, priceLabel } from "./kits";
import { compareRegimes, inr } from "./fin";

const plan = readFileSync(fileURLToPath(new URL("../../../../03-kits/PLAN.md", import.meta.url)), "utf8");
const ladder = plan.slice(plan.indexOf("**Price ladder:**"), plan.indexOf("**Alternatives a buyer compares us to:**"));
const planPrice = (tier: string) => Number((new RegExp(`\\|\\s*${tier}[^|]*\\|\\s*₹?(\\d[\\d,]*)`).exec(ladder) || [])[1]?.replace(/,/g, ""));

describe("kits", () => {
  test("prices are the PLAN ladder (Lite 0, Kit 199, Kit Pro 299, Bundle 499)", () => {
    expect(planPrice("Lite \\(free\\)")).toBe(0);
    expect(planPrice("Kit")).toBe(199);
    expect(planPrice("Kit Pro")).toBe(299);
    expect(planPrice("Bundle")).toBe(499);
    for (const k of KITS) {
      const by = Object.fromEntries(k.tiers.map((t) => [t.id, t.price]));
      expect(by.lite).toBe(0);
      expect(by.kit).toBe(planPrice("Kit"));
      if (by.pro !== undefined) expect(by.pro).toBe(planPrice("Kit Pro"));
    }
  });

  test("the kits index ladder equals every row of the PLAN ladder", () => {
    for (const r of LADDER) expect(planPrice(r.tier.replace(/[()]/g, "\\$&"))).toBe(r.price);
    expect(LADDER.length).toBe((ladder.match(/^\| (?!Tier|---)/gm) || []).length);
  });

  test("the tax kit preview shows the site's own tested tax engine (old regime with ₹1,50,000 deductions)", () => {
    for (const [gross, nw, old, better] of kitBySlug("tax-sip-2026-27").preview.rows) {
      const c = compareRegimes(Number(gross.replace(/[₹,]/g, "")), 150000);
      expect([inr(c.new.total), inr(c.old.total), c.better === "new" ? "New" : "Old"]).toEqual([nw, old, better]);
    }
  });

  test("exam dates are the official ones", () => {
    expect(kitBySlug("gate-2027").date).toEqual({ iso: "2027-02-06", label: "6, 7, 13, 14, 20 and 21 Feb 2027", source: expect.stringContaining("iitm.ac.in") });
    expect(kitBySlug("upsc-2027").date.iso).toBe("2027-05-23");
  });

  test("no fake urgency or hidden prices (CCPA dark-pattern guidelines 2023)", () => {
    const all = JSON.stringify({ KITS, LEGAL });
    for (const bad of [/hurry/i, /only \d+ (left|seats|copies)/i, /last chance/i, /ends (today|tonight)/i, /selling fast/i, /limited[- ]time/i, /starting (at|from)/i, /\+ ?taxes/i])
      expect(all).not.toMatch(bad);
    for (const k of KITS) for (const t of k.tiers) {
      expect(priceLabel(t)).toMatch(t.price === 0 ? /^Free$/ : /^₹\d{3}$/); // the full price, once, no "starting at"
      if (t.earlyBird) expect(t.earlyBird.active && !t.buyUrl).toBe(false); // an early-bird is shown only when you can actually buy it
    }
  });

  test("no buy button points nowhere: a tier without a payment link says it opens soon", () => {
    for (const k of KITS) for (const t of k.tiers) if (t.price > 0 && t.buyUrl) expect(t.buyUrl).toMatch(/^https:\/\/(rzp\.io|pages\.razorpay\.com)\//);
  });

  test("Razorpay + e-commerce rule pages exist and name a grievance officer", () => {
    expect(Object.keys(LEGAL).sort()).toEqual(["about", "contact", "delivery", "privacy", "refunds", "terms"]);
    expect(CONTACT.grievanceOfficer).toBeTruthy();
    expect(CONTACT.email).toMatch(/@/);
    expect(LEGAL.contact.body.join(" ")).toMatch(/48 hours/);
    expect(LEGAL.refunds.body.join(" ")).toMatch(/7 days/);
    expect(LEGAL.delivery.body.join(" ")).toMatch(/digital|link/i);
  });
});

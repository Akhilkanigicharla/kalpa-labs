// A17 check: 10 calculators, each complete in English and Telugu, every default computes, and kit links stay honest.
import { describe, expect, it } from "vitest";
import { CALCS, bySlug, defaults } from "./calcs";
import { RULES } from "./fin";
import { CALC_KIT, KITS } from "./kits";

const TE = /[ఀ-౿]/;

describe("the 10 calculators (PLAN.md top-10 list)", () => {
  it("are exactly the planned ten, with unique slugs", () => {
    expect(CALCS.map((c) => c.slug).sort()).toEqual(["emi", "fd", "gratuity", "gst", "hra", "income-tax", "ppf", "rd", "salary", "sip"]);
  });

  for (const c of CALCS) {
    it(`${c.slug}: bilingual copy, valid fields, defaults compute to real numbers`, () => {
      expect(TE.test(c.title.te) && TE.test(c.blurb.te)).toBe(true);
      expect(c.faqs.length).toBeGreaterThanOrEqual(3);
      for (const f of c.faqs) expect(TE.test(f.q.te) && TE.test(f.a.te) && f.q.en && f.a.en).toBeTruthy();
      for (const f of c.fields) {
        expect(TE.test(f.te), `${c.slug}.${f.id} Telugu label`).toBe(true);
        if (f.kind === "select") expect(f.options!.map((o) => o.value)).toContain(String(f.value));
      }
      for (const lang of ["en", "te"] as const) {
        const rows = c.compute(defaults(c));
        expect(rows.filter((r) => r.big).length).toBe(1);
        for (const r of rows) {
          const shown = lang === "te" && r.valueTe ? r.valueTe : r.value;
          expect(shown, `${c.slug} ${r.en}`).not.toMatch(/NaN|undefined|Infinity/);
          expect(r[lang]).toBeTruthy();
        }
      }
      const words = JSON.stringify(c).toLowerCase();
      expect(words).not.toMatch(/guaranteed return|assured return|risk-free|best fund/);
    });
  }

  it("every select option works: GST add/remove × rates × states, gratuity both job types", () => {
    const g = bySlug("gst");
    for (const rate of RULES.gstRates) for (const mode of ["add", "remove"]) for (const supply of ["same", "other"]) {
      const rows = g.compute({ amount: 1180, rate: String(rate), mode, supply });
      expect(rows.some((r) => r.en === (supply === "other" ? "IGST" : "CGST"))).toBe(true);
      expect(rows.every((r) => /^₹[\d,]+(\.\d\d)?$/.test(r.value))).toBe(true);
    }
    expect(g.compute({ amount: 1180, rate: "18", mode: "remove", supply: "same" })[0]!.value).toBe("₹1,000");
    const gr = bySlug("gratuity");
    expect(gr.compute({ wages: 50000, total: 0, years: 10, months: 7, type: "permanent" })[0]!.value).toBe("₹3,17,308");
    expect(gr.compute({ wages: 30000, total: 0, years: 2, months: 0, type: "permanent" })[1]!.valueTe).toBe("5 ఏళ్ల సర్వీస్ కావాలి");
    expect(gr.compute({ wages: 30000, total: 0, years: 2, months: 0, type: "fixed" })[0]!.value).not.toBe("₹0");
  });

  it("RD defaults to the current post office rate; FAQ figure matches the engine", () => {
    const r = bySlug("rd");
    expect(defaults(r).rate).toBe(6.7); // not 6.700000000000001 in the input box
    // exact maths: ₹7,13,658.29; India Post's per-₹100 table (₹7,136.59) gives ₹7,13,659; the FAQ rounds to lakh
    expect(r.compute(defaults(r))[0]!.value).toBe("₹7,13,658");
    expect(r.faqs[0]!.a.en).toContain("₹7.14 lakh"); expect(r.faqs[0]!.a.te).toContain("₹7.14 లక్షలు");
  });

  it("kit links point at real kits and only claim 'this calculator' when the kit has it (PLAN: no kit for GST, gratuity)", () => {
    for (const [slug, l] of Object.entries(CALC_KIT)) {
      expect(CALCS.some((c) => c.slug === slug)).toBe(true);
      expect(KITS.some((k) => k.slug === l.kit)).toBe(true);
    }
    expect(CALC_KIT.gst).toBeUndefined(); expect(CALC_KIT.gratuity).toBeUndefined();
    expect(CALC_KIT.rd!.same).toBe(false); expect(CALC_KIT.ppf!.same).toBe(false);
  });
});

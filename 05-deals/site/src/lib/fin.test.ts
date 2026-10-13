import { describe, expect, it } from "vitest";
import { compareRegimes, emi, fd, hra, incomeTax, ppf, salary, sip, inr } from "./fin";

describe("income tax, tax year 2026-27 (A15 fixtures)", () => {
  const cases: [number, number, number][] = [
    // gross, new regime, old regime with ₹1.5L 80C
    [1275000, 0, 140400],
    [1300000, 26000, 148200],
    [2500000, 319800, 522600],
  ];
  it.each(cases)("₹%i → new %i, old %i", (gross, want_new, want_old) => {
    expect(incomeTax({ gross, regime: "new" }).total).toBe(want_new);
    expect(incomeTax({ gross, regime: "old", deductions: 150000 }).total).toBe(want_old);
  });
  it("marginal relief just above ₹12L: tax never exceeds income above ₹12L (+cess)", () => {
    const r = incomeTax({ gross: 1300000, regime: "new" });
    expect(r.taxable).toBe(1225000);
    expect(r.slabTax).toBe(63750);
    expect(r.rebate).toBe(38750);
    for (const g of [1276000, 1290000, 1310000, 1340000]) {
      const t = incomeTax({ gross: g, regime: "new" });
      expect(t.total).toBeLessThanOrEqual(Math.round((t.taxable - 1200000) * 1.04 / 10) * 10 + 10);
    }
  });
  it("old-regime rebate up to ₹5L, no marginal relief", () => {
    expect(incomeTax({ gross: 550000, regime: "old" }).total).toBe(0);           // taxable 5.0L
    expect(incomeTax({ gross: 560000, regime: "old" }).total).toBe(15080);       // taxable 5.1L: 12,500 + 2,000 + cess
  });
  it("senior citizen exemption limits (old regime)", () => {
    expect(incomeTax({ gross: 850000, regime: "old", age: "60to80" }).slabTax).toBe(10000 + 60000);
    expect(incomeTax({ gross: 850000, regime: "old", age: "above80" }).slabTax).toBe(60000);
  });
  it("surcharge 10% above ₹50L with marginal relief, capped at 25% in the new regime", () => {
    const at = incomeTax({ gross: 5075000, regime: "new" });     // taxable exactly 50L: no surcharge
    expect(at.surcharge).toBe(0);
    const just = incomeTax({ gross: 5085000, regime: "new" });   // ₹10,000 above: relief limits surcharge
    expect(just.surcharge).toBeCloseTo(7000, 0);              // tax + surcharge = tax at 50L + ₹10,000
    const big = incomeTax({ gross: 60000000, regime: "new" });
    expect(big.surcharge / (big.slabTax - big.rebate)).toBeCloseTo(0.25, 5);
    const bigOld = incomeTax({ gross: 60000000, regime: "old" });
    expect(bigOld.surcharge / bigOld.slabTax).toBeCloseTo(0.37, 2);
  });
  it("compareRegimes picks the cheaper one", () => {
    expect(compareRegimes(1300000, 150000).better).toBe("new");
    expect(compareRegimes(1500000, 900000).better).toBe("old");
  });
});

describe("other calculators (A16)", () => {
  it("SIP ₹10,000/month at 12% for 10 years", () => {
    expect(sip(10000, 0.12, 10)).toEqual({ invested: 1200000, value: 2323391, gain: 1123391 });
  });
  it("EMI ₹50L at 8.5% for 20 years", () => {
    expect(emi(5000000, 0.085, 20).emi).toBe(43391);
  });
  it("FD ₹1L at 7% for 5 years, quarterly compounding", () => {
    expect(fd(100000, 0.07, 5).value).toBe(141478);
  });
  it("PPF ₹1.5L a year for 15 years at 7.1%, capped at ₹1.5L", () => {
    expect(ppf(150000).value).toBe(4068209);
    expect(ppf(200000).cappedAt).toBe(150000);
  });
  it("HRA: Hyderabad is a 50% city from tax year 2026-27", () => {
    const h = hra(600000, 240000, 300000, "Hyderabad");
    expect(h.metro).toBe(true);
    expect(h.limits).toEqual([240000, 300000, 240000]);
    expect(h.exempt).toBe(240000);
    expect(hra(600000, 240000, 300000, "Warangal").limits[1]).toBe(240000);
    expect(hra(600000, 240000, 50000, "Delhi").exempt).toBe(0);  // rent below 10% of salary
  });
  it("salary in hand from CTC", () => {
    const s = salary(1200000);
    expect(s.employeePf).toBe(21600);           // 12% of the ₹15,000 PF wage ceiling
    expect(s.gross).toBe(1178400);
    expect(s.tax).toBe(0);                      // taxable ≤ ₹12L after ₹75,000 standard deduction
    expect(s.inHandMonth).toBe(Math.round((1178400 - 21600 - 2400) / 12));
  });
  it("Indian number format", () => {
    expect(inr(2323391)).toBe("₹23,23,391");
  });
});

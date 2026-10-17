import { describe, expect, it } from "vitest";
import { compareRegimes, emi, fd, gratuity, gst, hra, incomeTax, ppf, rd, RULES, salary, sip, inr, inrPaise } from "./fin";

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

describe("calculators 8-10 (A17)", () => {
  it("GST add: ₹1,000 at 18% within the state = CGST 90 + SGST 90", () => {
    expect(gst(1000, 18, "add")).toEqual({ base: 1000, tax: 180, total: 1180, half: 90 });
  });
  it("GST remove: ₹1,180 including 18% → ₹1,000 + ₹180; ₹1,050 incl. 5% → ₹1,000", () => {
    expect(gst(1180, 18, "remove")).toMatchObject({ base: 1000, tax: 180, total: 1180 });
    expect(gst(1050, 5, "remove")).toMatchObject({ base: 1000, tax: 50 });
  });
  it("GST keeps paise: ₹99 at 5% is ₹4.95, and base + tax always equals total", () => {
    expect(gst(99, 5, "add")).toEqual({ base: 99, tax: 4.95, total: 103.95, half: 2.475 });
    for (const [a, r] of [[999, 18], [1, 40], [12345.67, 3], [100, 0.25]] as const) {
      const g = gst(a, r, "remove"); expect(Math.round((g.base + g.tax) * 100)).toBe(Math.round(a * 100));
    }
  });
  it("GST 2.0 slabs (from 22 Sept 2025)", () => {
    expect(RULES.gstRates).toEqual([5, 18, 40, 3, 0.25]);
    expect(inrPaise(4.95)).toBe("₹4.95"); expect(inrPaise(1180)).toBe("₹1,180"); expect(inrPaise(103.9)).toBe("₹103.90");
  });

  it("gratuity: 15/26 × wages × completed years, part-year over 6 months counts", () => {
    expect(gratuity({ wages: 50000, years: 10, months: 7 })).toMatchObject({ completedYears: 11, amount: 317308, eligible: true, wagesUsed: 50000 });
    expect(gratuity({ wages: 50000, years: 10, months: 6 }).completedYears).toBe(10); // exactly 6 months is not "in excess of six months"
  });
  it("gratuity: Labour Code wages are at least 50% of total pay (from 21 Nov 2025)", () => {
    const g = gratuity({ wages: 40000, totalPay: 100000, years: 6, months: 0 });
    expect(g.wagesUsed).toBe(50000); expect(g.amount).toBe(Math.round((50000 * 15 / 26) * 6));
    expect(gratuity({ wages: 60000, totalPay: 100000, years: 6, months: 0 }).wagesUsed).toBe(60000);
  });
  it("gratuity: 5 years for permanent staff (240 days in the 5th year counts), 1 year for fixed-term", () => {
    expect(gratuity({ wages: 30000, years: 4, months: 3 }).eligible).toBe(false);
    expect(gratuity({ wages: 30000, years: 4, months: 8 }).eligible).toBe(true);
    expect(gratuity({ wages: 30000, years: 1, months: 0, fixedTerm: true }).eligible).toBe(true);
    expect(gratuity({ wages: 30000, years: 0, months: 11, fixedTerm: true }).eligible).toBe(false);
    expect(gratuity({ wages: 30000, years: 3, months: 0 }).amount).toBe(0);
  });
  it("gratuity: ₹20 lakh ceiling, and that much is tax-free", () => {
    const g = gratuity({ wages: 300000, years: 30, months: 0 });
    expect(g.formula).toBe(Math.round(300000 * 15 / 26 * 30)); expect(g.amount).toBe(2000000); expect(g.capped).toBe(true); expect(g.taxFree).toBe(2000000);
  });

  it("RD ₹10,000/month at 6.7% for 5 years (post office) ≈ ₹7,13,659, quarterly compounding", () => {
    const r = rd(10000, 0.067, 5);
    expect(Math.abs(r.value - 713659)).toBeLessThanOrEqual(2);
    expect(r.deposited).toBe(600000); expect(r.interest).toBe(r.value - 600000);
    expect(RULES.postOfficeRd).toBe(0.067);
  });
  it("RD at 0% returns what you put in", () => {
    expect(rd(5000, 0, 2)).toEqual({ deposited: 120000, value: 120000, interest: 0 });
  });
});

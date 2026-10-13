/**
 * Kalpa calculators: money maths for India, tax year 2026-27 (FY 2026-27).
 * A calculator, not advice. Every rule cites its source; the Tax Rules Watcher re-checks on 1 Feb.
 *
 * Sources (checked 13 Oct 2026, see ../../research/deep-scan-v2.md):
 *  - Slabs, rebate, standard deduction: Income-tax Act 2025 s.202 (new regime), s.156 (rebate, ex-87A),
 *    s.19 (standard deduction); Finance Bill 2026 changed no rates. https://www.indiabudget.gov.in/doc/memo.pdf
 *    https://www.incometaxindia.gov.in/w/tax-rates-and-computation
 *  - Surcharge + 4% Health & Education Cess: same Memorandum.
 *  - HRA: lowest of actual HRA, 50%/40% of salary, rent - 10% of salary; old regime only. Income-tax
 *    Rules 2026 extend 50% to Bengaluru, Hyderabad, Pune, Ahmedabad (with Delhi, Mumbai, Chennai,
 *    Kolkata). https://cleartax.in/s/hra-house-rent-allowance (verify against the CBDT notification).
 *  - PPF 7.1% for Oct-Dec 2026 (Q3 FY27, unchanged). https://www.businesstoday.in/personal-finance/story/small-savings-scheme-interest-rates-unchanged-for-q3-fy27-check-ppf-scss-ssy-rates-558892-2026-09-30
 */

export type Regime = "new" | "old";
export type AgeBand = "below60" | "60to80" | "above80";

export const RULES = {
  taxYear: "2026-27",
  newSlabs: [[400000, 0], [800000, 0.05], [1200000, 0.1], [1600000, 0.15], [2000000, 0.2], [2400000, 0.25], [Infinity, 0.3]] as [number, number][],
  oldSlabs: {
    below60: [[250000, 0], [500000, 0.05], [1000000, 0.2], [Infinity, 0.3]],
    "60to80": [[300000, 0], [500000, 0.05], [1000000, 0.2], [Infinity, 0.3]],
    above80: [[500000, 0], [1000000, 0.2], [Infinity, 0.3]],
  } as Record<AgeBand, [number, number][]>,
  stdDeduction: { new: 75000, old: 50000 },
  rebate: { new: { limit: 1200000, max: 60000, marginal: true }, old: { limit: 500000, max: 12500, marginal: false } },
  surcharge: [[5000000, 0.1], [10000000, 0.15], [20000000, 0.25], [50000000, 0.37]] as [number, number][],
  newSurchargeCap: 0.25,
  cess: 0.04,
  hraMetros: ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Hyderabad", "Pune", "Ahmedabad"],
  ppfRate: 0.071,
  ppfMaxPerYear: 150000,
  telanganaProfTaxMonthly: 200,
  pfWageCeiling: 15000,
};

const round10 = (x: number) => Math.round(x / 10) * 10; // s.288A/288B style rounding to the nearest ₹10

function slabTax(income: number, slabs: [number, number][]): number {
  let tax = 0, prev = 0;
  for (const [upto, rate] of slabs) {
    if (income <= prev) break;
    tax += (Math.min(income, upto) - prev) * rate;
    prev = upto;
  }
  return tax;
}

export interface TaxInput {
  gross: number;               // salary or total income before deductions (₹ a year)
  regime: Regime;
  salaried?: boolean;          // standard deduction applies (default true)
  deductions?: number;         // old regime: 80C, 80D, HRA exemption etc. combined
  age?: AgeBand;
}
export interface TaxResult {
  taxable: number; slabTax: number; rebate: number; surcharge: number; cess: number; total: number;
  effectiveRate: number; monthly: number;
}

export function incomeTax(i: TaxInput): TaxResult {
  const regime = i.regime;
  const std = i.salaried === false ? 0 : RULES.stdDeduction[regime];
  const ded = regime === "old" ? Math.max(0, i.deductions ?? 0) : 0;
  const taxable = Math.max(0, round10(i.gross - std - ded));
  const slabs = regime === "new" ? RULES.newSlabs : RULES.oldSlabs[i.age ?? "below60"];
  const base = slabTax(taxable, slabs);
  // rebate (s.156): full up to the limit; new regime adds marginal relief just above ₹12L
  const rb = RULES.rebate[regime];
  let rebate = 0;
  if (taxable <= rb.limit) rebate = Math.min(base, rb.max);
  else if (rb.marginal) rebate = Math.max(0, base - (taxable - rb.limit));
  const afterRebate = base - rebate;
  // surcharge with marginal relief at each threshold
  let surcharge = 0;
  const steps = RULES.surcharge.filter(([, r]) => regime === "old" || r <= RULES.newSurchargeCap);
  for (let k = steps.length - 1; k >= 0; k--) {
    const [th, rate] = steps[k];
    if (taxable > th) {
      const prevRate = k > 0 ? steps[k - 1][1] : 0;
      const atThreshold = slabTax(th, slabs) * (1 + prevRate);
      surcharge = Math.min(afterRebate * rate, atThreshold + (taxable - th) - afterRebate);
      surcharge = Math.max(0, surcharge);
      break;
    }
  }
  const cess = (afterRebate + surcharge) * RULES.cess;
  const total = round10(afterRebate + surcharge + cess);
  return { taxable, slabTax: base, rebate, surcharge, cess, total,
           effectiveRate: i.gross > 0 ? total / i.gross : 0, monthly: Math.round(total / 12) };
}

export function compareRegimes(gross: number, oldDeductions: number, age: AgeBand = "below60") {
  const n = incomeTax({ gross, regime: "new", age });
  const o = incomeTax({ gross, regime: "old", deductions: oldDeductions, age });
  return { new: n, old: o, better: (n.total <= o.total ? "new" : "old") as Regime, saving: Math.abs(n.total - o.total) };
}

/** Monthly SIP future value (payment at the start of each month). */
export function sip(monthly: number, annualRate: number, years: number) {
  const n = Math.round(years * 12), i = annualRate / 12;
  const fv = i === 0 ? monthly * n : monthly * ((Math.pow(1 + i, n) - 1) / i) * (1 + i);
  const invested = monthly * n;
  return { invested, value: Math.round(fv), gain: Math.round(fv - invested) };
}

/** Loan EMI (reducing balance). */
export function emi(principal: number, annualRate: number, years: number) {
  const n = Math.round(years * 12), r = annualRate / 12;
  const e = r === 0 ? principal / n : (principal * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
  const total = e * n;
  return { emi: Math.round(e), totalInterest: Math.round(total - principal), totalPaid: Math.round(total) };
}

/** Fixed deposit with quarterly compounding (the usual Indian bank convention). */
export function fd(principal: number, annualRate: number, years: number, perYear = 4) {
  const value = principal * Math.pow(1 + annualRate / perYear, perYear * years);
  return { value: Math.round(value), interest: Math.round(value - principal) };
}

/** PPF: one deposit at the start of each financial year, compounded yearly. */
export function ppf(yearly: number, years = 15, rate = RULES.ppfRate) {
  const d = Math.min(yearly, RULES.ppfMaxPerYear);
  const value = d * ((Math.pow(1 + rate, years) - 1) / rate) * (1 + rate);
  return { deposited: d * years, value: Math.round(value), interest: Math.round(value - d * years), cappedAt: d < yearly ? RULES.ppfMaxPerYear : null };
}

/** HRA exemption (old regime only). Amounts are yearly. */
export function hra(basicPlusDa: number, hraReceived: number, rentPaid: number, city: string) {
  const metro = RULES.hraMetros.some((c) => c.toLowerCase() === city.trim().toLowerCase());
  const limits = [hraReceived, basicPlusDa * (metro ? 0.5 : 0.4), Math.max(0, rentPaid - 0.1 * basicPlusDa)];
  const exempt = Math.max(0, Math.min(...limits));
  return { exempt: Math.round(exempt), taxable: Math.round(hraReceived - exempt), metro, limits: limits.map(Math.round) };
}

/** Salary in hand from CTC (new regime by default; Telangana professional tax). */
export function salary(ctc: number, opts: { basicPct?: number; pfOnFullBasic?: boolean; regime?: Regime; deductions?: number } = {}) {
  const basic = ctc * (opts.basicPct ?? 0.4);
  const pfBase = opts.pfOnFullBasic ? basic : Math.min(basic, RULES.pfWageCeiling * 12);
  const employerPf = 0.12 * pfBase;            // part of CTC, not paid out
  const employeePf = 0.12 * pfBase;
  const gross = ctc - employerPf;
  const tax = incomeTax({ gross, regime: opts.regime ?? "new", deductions: (opts.deductions ?? 0) + (opts.regime === "old" ? employeePf : 0) });
  const profTax = RULES.telanganaProfTaxMonthly * 12;
  const inHand = gross - employeePf - tax.total - profTax;
  return { gross: Math.round(gross), employeePf: Math.round(employeePf), tax: tax.total, profTax, inHandYear: Math.round(inHand), inHandMonth: Math.round(inHand / 12) };
}

export const inr = (x: number) => "₹" + Math.round(x).toLocaleString("en-IN");

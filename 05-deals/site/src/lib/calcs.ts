// Calculator definitions shared by the pages (server render) and the browser script.
// English + Telugu copy. Telugu text needs a native speaker's check before launch (CEO queue).
import { compareRegimes, emi, fd, hra, inr, ppf, salary, sip } from "./fin";

export type Lang = "en" | "te";
export interface Field { id: string; en: string; te: string; value: number | string; step?: number; kind?: "number" | "city" }
export interface Row { en: string; te: string; value: string; valueTe?: string; big?: boolean } // valueTe: a word, not a number
export interface Faq { q: Record<Lang, string>; a: Record<Lang, string> }
export interface Calc {
  slug: string; title: Record<Lang, string>; blurb: Record<Lang, string>;
  fields: Field[]; compute: (v: Record<string, number | string>) => Row[]; faqs: Faq[];
}

const n = (v: number | string) => Number(String(v).replace(/[,₹\s]/g, "")) || 0;
const pct = (v: number | string) => n(v) / 100;

export const CALCS: Calc[] = [
  {
    slug: "income-tax",
    title: { en: "Income tax calculator 2026-27 (new vs old regime)", te: "ఆదాయపు పన్ను కాలిక్యులేటర్ 2026-27 (కొత్త vs పాత విధానం)" },
    blurb: { en: "Tax year 2026-27 under the Income-tax Act 2025. Salaried, resident, below 60.", te: "ఆదాయపు పన్ను చట్టం 2025 ప్రకారం పన్ను సంవత్సరం 2026-27. జీతం పొందే, 60 ఏళ్ల లోపు నివాసితులకు." },
    fields: [
      { id: "gross", en: "Gross salary a year (₹)", te: "ఏడాది మొత్తం జీతం (₹)", value: 1300000, step: 10000 },
      { id: "ded", en: "Old-regime deductions: 80C, 80D, HRA… (₹)", te: "పాత విధానం మినహాయింపులు: 80C, 80D, HRA… (₹)", value: 150000, step: 5000 },
    ],
    compute: (v) => {
      const c = compareRegimes(n(v.gross), n(v.ded));
      return [
        { en: "New regime tax", te: "కొత్త విధానంలో పన్ను", value: inr(c.new.total), big: true },
        { en: "Old regime tax", te: "పాత విధానంలో పన్ను", value: inr(c.old.total) },
        { en: "Lower tax under", te: "తక్కువ పన్ను", value: c.better === "new" ? "New regime" : "Old regime", valueTe: c.better === "new" ? "కొత్త విధానం" : "పాత విధానం" },
        { en: "Difference", te: "తేడా", value: inr(c.saving) },
      ];
    },
    faqs: [
      { q: { en: "Is income up to ₹12.75 lakh tax-free in 2026-27?", te: "2026-27లో ₹12.75 లక్షల వరకు జీతానికి పన్ను లేదా?" },
        a: { en: "For salaried people under the new regime, yes: the ₹75,000 standard deduction brings taxable income to ₹12 lakh, and the rebate under section 156 cancels tax up to ₹60,000.", te: "కొత్త విధానంలో జీతం పొందేవారికి అవును: ₹75,000 స్టాండర్డ్ డిడక్షన్ తర్వాత పన్ను ఆదాయం ₹12 లక్షలు అవుతుంది, సెక్షన్ 156 రిబేట్ ₹60,000 వరకు పన్నును రద్దు చేస్తుంది." } },
      { q: { en: "Why is tax on ₹13 lakh only ₹26,000?", te: "₹13 లక్షలకు పన్ను ₹26,000 మాత్రమే ఎందుకు?" },
        a: { en: "Marginal relief: just above ₹12 lakh of taxable income, tax cannot exceed the income above ₹12 lakh. ₹25,000 plus 4% cess is ₹26,000.", te: "మార్జినల్ రిలీఫ్: పన్ను ఆదాయం ₹12 లక్షలు దాటితే, పన్ను ₹12 లక్షల పైన ఉన్న మొత్తాన్ని మించదు. ₹25,000 + 4% సెస్ = ₹26,000." } },
      { q: { en: "Did Budget 2026 change the slabs?", te: "బడ్జెట్ 2026 స్లాబులను మార్చిందా?" },
        a: { en: "No. The Finance Bill 2026 memorandum says no change in tax rates; only the section numbers moved to the Income-tax Act 2025.", te: "లేదు. ఫైనాన్స్ బిల్లు 2026 పన్ను రేట్లలో మార్పు లేదని చెప్పింది; సెక్షన్ నంబర్లు మాత్రమే ఆదాయపు పన్ను చట్టం 2025కి మారాయి." } },
    ],
  },
  {
    slug: "salary",
    title: { en: "Salary in-hand calculator (CTC to take-home)", te: "చేతికి వచ్చే జీతం కాలిక్యులేటర్ (CTC నుండి)" },
    blurb: { en: "New regime, PF on the ₹15,000 wage ceiling, Telangana professional tax ₹200 a month.", te: "కొత్త విధానం, ₹15,000 వేతన పరిమితిపై PF, తెలంగాణ వృత్తి పన్ను నెలకు ₹200." },
    fields: [
      { id: "ctc", en: "CTC a year (₹)", te: "ఏడాది CTC (₹)", value: 1200000, step: 10000 },
      { id: "basic", en: "Basic pay as % of CTC", te: "CTCలో బేసిక్ శాతం", value: 40, step: 1 },
    ],
    compute: (v) => {
      const s = salary(n(v.ctc), { basicPct: pct(v.basic) });
      return [
        { en: "In hand each month", te: "నెలకు చేతికి", value: inr(s.inHandMonth), big: true },
        { en: "Income tax a year", te: "ఏడాది ఆదాయపు పన్ను", value: inr(s.tax) },
        { en: "Your PF a year", te: "మీ PF (ఏడాది)", value: inr(s.employeePf) },
        { en: "Professional tax a year", te: "వృత్తి పన్ను (ఏడాది)", value: inr(s.profTax) },
      ];
    },
    faqs: [
      { q: { en: "Why is in-hand lower than CTC ÷ 12?", te: "చేతికి వచ్చేది CTC ÷ 12 కంటే ఎందుకు తక్కువ?" },
        a: { en: "CTC includes the employer's PF share, and your own PF, professional tax and income tax are deducted from the gross.", te: "CTCలో యజమాని PF వాటా ఉంటుంది; మీ PF, వృత్తి పన్ను, ఆదాయపు పన్ను గ్రాస్ నుండి కట్ అవుతాయి." } },
      { q: { en: "What is professional tax in Telangana?", te: "తెలంగాణలో వృత్తి పన్ను ఎంత?" },
        a: { en: "₹200 a month for monthly salary above ₹20,000.", te: "నెల జీతం ₹20,000 దాటితే నెలకు ₹200." } },
      { q: { en: "Does this include bonus or gratuity?", te: "ఇందులో బోనస్ లేదా గ్రాట్యుటీ ఉన్నాయా?" },
        a: { en: "No. Variable pay and gratuity differ by employer; check your offer letter.", te: "లేదు. వేరియబుల్ పే, గ్రాట్యుటీ కంపెనీని బట్టి మారతాయి; మీ ఆఫర్ లెటర్ చూడండి." } },
    ],
  },
  {
    slug: "sip",
    title: { en: "SIP calculator", te: "SIP కాలిక్యులేటర్" },
    blurb: { en: "Monthly investment, compounded monthly. Returns are assumptions, not promises.", te: "నెలవారీ పెట్టుబడి, నెలవారీ చక్రవడ్డీ. రాబడి అంచనా మాత్రమే, హామీ కాదు." },
    fields: [
      { id: "monthly", en: "Monthly SIP (₹)", te: "నెలవారీ SIP (₹)", value: 10000, step: 500 },
      { id: "rate", en: "Expected return a year (%)", te: "అంచనా వార్షిక రాబడి (%)", value: 12, step: 0.5 },
      { id: "years", en: "Years", te: "సంవత్సరాలు", value: 10, step: 1 },
    ],
    compute: (v) => {
      const s = sip(n(v.monthly), pct(v.rate), n(v.years));
      return [
        { en: "Estimated value", te: "అంచనా విలువ", value: inr(s.value), big: true },
        { en: "You invest", te: "మీరు పెట్టేది", value: inr(s.invested) },
        { en: "Estimated gain", te: "అంచనా లాభం", value: inr(s.gain) },
      ];
    },
    faqs: [
      { q: { en: "Is 12% return guaranteed?", te: "12% రాబడి గ్యారంటీనా?" },
        a: { en: "No. Mutual fund returns vary and can be negative. Use a lower rate to be safe.", te: "కాదు. మ్యూచువల్ ఫండ్ రాబడి మారుతుంది, నష్టం కూడా రావచ్చు. జాగ్రత్తకు తక్కువ రేటు వాడండి." } },
      { q: { en: "How is SIP value calculated?", te: "SIP విలువ ఎలా లెక్కిస్తారు?" },
        a: { en: "Each monthly instalment grows at the monthly rate until the end: P × ((1+i)^n − 1) ÷ i × (1+i).", te: "ప్రతి నెల వాయిదా చివరి వరకు నెలవారీ రేటుతో పెరుగుతుంది: P × ((1+i)^n − 1) ÷ i × (1+i)." } },
      { q: { en: "Is SIP gain taxed?", te: "SIP లాభంపై పన్ను ఉందా?" },
        a: { en: "Yes, as capital gains when you sell; equity gains above ₹1.25 lakh a year are taxed at 12.5% after one year.", te: "అవును, అమ్మినప్పుడు క్యాపిటల్ గెయిన్స్‌గా; ఏడాది తర్వాత ఈక్విటీ లాభం ఏడాదికి ₹1.25 లక్షలు దాటితే 12.5% పన్ను." } },
    ],
  },
  {
    slug: "emi",
    title: { en: "EMI calculator (home, car, personal loan)", te: "EMI కాలిక్యులేటర్ (ఇల్లు, కారు, పర్సనల్ లోన్)" },
    blurb: { en: "Reducing-balance EMI, the way banks calculate it.", te: "బ్యాంకులు లెక్కించే తగ్గే బ్యాలెన్స్ EMI." },
    fields: [
      { id: "p", en: "Loan amount (₹)", te: "లోన్ మొత్తం (₹)", value: 5000000, step: 50000 },
      { id: "rate", en: "Interest rate a year (%)", te: "వార్షిక వడ్డీ రేటు (%)", value: 8.5, step: 0.05 },
      { id: "years", en: "Tenure (years)", te: "కాల వ్యవధి (సంవత్సరాలు)", value: 20, step: 1 },
    ],
    compute: (v) => {
      const e = emi(n(v.p), pct(v.rate), n(v.years));
      return [
        { en: "Monthly EMI", te: "నెలవారీ EMI", value: inr(e.emi), big: true },
        { en: "Total interest", te: "మొత్తం వడ్డీ", value: inr(e.totalInterest) },
        { en: "Total you pay", te: "మొత్తం చెల్లింపు", value: inr(e.totalPaid) },
      ];
    },
    faqs: [
      { q: { en: "How is EMI calculated?", te: "EMI ఎలా లెక్కిస్తారు?" },
        a: { en: "EMI = P × r × (1+r)^n ÷ ((1+r)^n − 1), with r the monthly rate and n the months.", te: "EMI = P × r × (1+r)^n ÷ ((1+r)^n − 1), r = నెలవారీ రేటు, n = నెలలు." } },
      { q: { en: "Does prepaying reduce interest?", te: "ముందుగా కడితే వడ్డీ తగ్గుతుందా?" },
        a: { en: "Yes. Floating-rate home loans for individuals have no prepayment penalty under RBI rules.", te: "అవును. RBI నియమాల ప్రకారం వ్యక్తుల ఫ్లోటింగ్ రేటు హోమ్ లోన్‌లకు ముందస్తు చెల్లింపు జరిమానా లేదు." } },
      { q: { en: "Are processing fees included?", te: "ప్రాసెసింగ్ ఫీజు కలిపారా?" },
        a: { en: "No. Add the bank's fees and insurance separately.", te: "లేదు. బ్యాంక్ ఫీజు, ఇన్సూరెన్స్ విడిగా కలపండి." } },
    ],
  },
  {
    slug: "fd",
    title: { en: "FD calculator (fixed deposit)", te: "FD కాలిక్యులేటర్ (ఫిక్స్‌డ్ డిపాజిట్)" },
    blurb: { en: "Quarterly compounding, the usual bank convention.", te: "త్రైమాసిక చక్రవడ్డీ, బ్యాంకుల సాధారణ పద్ధతి." },
    fields: [
      { id: "p", en: "Deposit (₹)", te: "డిపాజిట్ (₹)", value: 100000, step: 5000 },
      { id: "rate", en: "Interest rate a year (%)", te: "వార్షిక వడ్డీ రేటు (%)", value: 7, step: 0.05 },
      { id: "years", en: "Years", te: "సంవత్సరాలు", value: 5, step: 1 },
    ],
    compute: (v) => {
      const f = fd(n(v.p), pct(v.rate), n(v.years));
      return [
        { en: "Maturity value", te: "మెచ్యూరిటీ విలువ", value: inr(f.value), big: true },
        { en: "Interest earned", te: "వచ్చే వడ్డీ", value: inr(f.interest) },
      ];
    },
    faqs: [
      { q: { en: "Is FD interest taxable?", te: "FD వడ్డీపై పన్ను ఉందా?" },
        a: { en: "Yes, at your slab rate. Banks deduct TDS when interest crosses the yearly threshold.", te: "అవును, మీ స్లాబ్ రేటు ప్రకారం. వడ్డీ వార్షిక పరిమితి దాటితే బ్యాంకు TDS కట్ చేస్తుంది." } },
      { q: { en: "Why quarterly compounding?", te: "త్రైమాసిక చక్రవడ్డీ ఎందుకు?" },
        a: { en: "Most Indian banks compound term deposits every quarter; check your bank's terms.", te: "చాలా భారతీయ బ్యాంకులు ప్రతి త్రైమాసికం చక్రవడ్డీ వేస్తాయి; మీ బ్యాంకు నిబంధనలు చూడండి." } },
      { q: { en: "Are deposits insured?", te: "డిపాజిట్లకు బీమా ఉందా?" },
        a: { en: "DICGC insures up to ₹5 lakh per depositor per bank.", te: "DICGC ఒక్కో బ్యాంకులో ఒక్కో డిపాజిటర్‌కు ₹5 లక్షల వరకు బీమా ఇస్తుంది." } },
    ],
  },
  {
    slug: "ppf",
    title: { en: "PPF calculator (7.1%, Oct–Dec 2026)", te: "PPF కాలిక్యులేటర్ (7.1%, అక్టో–డిసెం 2026)" },
    blurb: { en: "Deposit at the start of each year, compounded yearly, 15-year lock-in.", te: "ప్రతి ఏడాది మొదట్లో డిపాజిట్, వార్షిక చక్రవడ్డీ, 15 ఏళ్ల లాక్-ఇన్." },
    fields: [
      { id: "yearly", en: "Deposit a year (₹, max 1,50,000)", te: "ఏడాది డిపాజిట్ (₹, గరిష్టం 1,50,000)", value: 150000, step: 5000 },
      { id: "years", en: "Years (15 or more)", te: "సంవత్సరాలు (15 లేదా ఎక్కువ)", value: 15, step: 5 },
    ],
    compute: (v) => {
      const p = ppf(n(v.yearly), Math.max(15, n(v.years)));
      return [
        { en: "Maturity value", te: "మెచ్యూరిటీ విలువ", value: inr(p.value), big: true },
        { en: "You deposit", te: "మీరు జమ చేసేది", value: inr(p.deposited) },
        { en: "Interest (tax-free)", te: "వడ్డీ (పన్ను లేదు)", value: inr(p.interest) },
      ];
    },
    faqs: [
      { q: { en: "What is the PPF rate now?", te: "ఇప్పుడు PPF రేటు ఎంత?" },
        a: { en: "7.1% a year for October–December 2026, unchanged. The government resets it every quarter.", te: "అక్టోబర్–డిసెంబర్ 2026కి ఏడాదికి 7.1%, మార్పు లేదు. ప్రభుత్వం ప్రతి త్రైమాసికం సమీక్షిస్తుంది." } },
      { q: { en: "Is PPF interest taxed?", te: "PPF వడ్డీపై పన్ను ఉందా?" },
        a: { en: "No, interest and maturity are tax-free; the deposit counts for 80C only in the old regime.", te: "లేదు, వడ్డీ, మెచ్యూరిటీ పన్ను రహితం; డిపాజిట్ పాత విధానంలో మాత్రమే 80C కిందకు వస్తుంది." } },
      { q: { en: "Can I deposit more than ₹1.5 lakh?", te: "₹1.5 లక్షల కంటే ఎక్కువ వేయవచ్చా?" },
        a: { en: "No, ₹1.5 lakh a year is the limit; extra earns no interest.", te: "లేదు, ఏడాదికి ₹1.5 లక్షలే పరిమితి; అదనపు మొత్తానికి వడ్డీ రాదు." } },
    ],
  },
  {
    slug: "hra",
    title: { en: "HRA exemption calculator (8 metro cities, 2026-27)", te: "HRA మినహాయింపు కాలిక్యులేటర్ (8 మెట్రో నగరాలు, 2026-27)" },
    blurb: { en: "Old regime only. Hyderabad, Bengaluru, Pune and Ahmedabad now get the 50% limit.", te: "పాత విధానంలో మాత్రమే. హైదరాబాద్, బెంగళూరు, పుణె, అహ్మదాబాద్‌కు ఇప్పుడు 50% పరిమితి." },
    fields: [
      { id: "basic", en: "Basic + DA a year (₹)", te: "ఏడాది బేసిక్ + DA (₹)", value: 600000, step: 10000 },
      { id: "hra", en: "HRA received a year (₹)", te: "ఏడాది వచ్చిన HRA (₹)", value: 240000, step: 5000 },
      { id: "rent", en: "Rent paid a year (₹)", te: "ఏడాది చెల్లించిన అద్దె (₹)", value: 300000, step: 5000 },
      { id: "city", en: "City", te: "నగరం", value: "Hyderabad", kind: "city" },
    ],
    compute: (v) => {
      const h = hra(n(v.basic), n(v.hra), n(v.rent), String(v.city));
      return [
        { en: "HRA exempt", te: "HRA మినహాయింపు", value: inr(h.exempt), big: true },
        { en: "HRA taxable", te: "పన్ను పడే HRA", value: inr(h.taxable) },
        { en: "City limit", te: "నగర పరిమితి", value: h.metro ? "50%" : "40%" },
      ];
    },
    faqs: [
      { q: { en: "Is Hyderabad a metro for HRA now?", te: "HRAకి హైదరాబాద్ ఇప్పుడు మెట్రోనా?" },
        a: { en: "Yes, from tax year 2026-27 the new Income-tax Rules give Hyderabad, Bengaluru, Pune and Ahmedabad the 50% limit.", te: "అవును, పన్ను సంవత్సరం 2026-27 నుండి కొత్త ఆదాయపు పన్ను నియమాలు హైదరాబాద్, బెంగళూరు, పుణె, అహ్మదాబాద్‌కు 50% పరిమితి ఇచ్చాయి." } },
      { q: { en: "How is HRA exemption calculated?", te: "HRA మినహాయింపు ఎలా లెక్కిస్తారు?" },
        a: { en: "The lowest of: HRA received, 50% (metro) or 40% of salary, and rent minus 10% of salary.", te: "ఈ మూడింటిలో తక్కువది: వచ్చిన HRA, జీతంలో 50% (మెట్రో) లేదా 40%, అద్దె − జీతంలో 10%." } },
      { q: { en: "Can I claim HRA in the new regime?", te: "కొత్త విధానంలో HRA క్లెయిమ్ చేయవచ్చా?" },
        a: { en: "No, HRA exemption is available only in the old regime.", te: "లేదు, HRA మినహాయింపు పాత విధానంలో మాత్రమే." } },
    ],
  },
];

export const bySlug = (slug: string) => CALCS.find((c) => c.slug === slug)!;
export const defaults = (c: Calc) => Object.fromEntries(c.fields.map((f) => [f.id, f.value]));

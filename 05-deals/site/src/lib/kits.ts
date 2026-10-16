// b3 Kits shown on the calculator site (A11): landing data, prices and the policy pages Razorpay asks for.
// Prices = 03-kits/PLAN.md price ladder (kits.test.ts checks). Exam dates checked 16 Oct 2026 (sources inline).
// Rules: India's Dark Patterns Guidelines 2023 (no false urgency, no drip pricing) and the E-Commerce Rules 2020
// (seller name, address, contact, grievance officer, refund terms). No buy link yet = the button says it opens soon.

export interface Tier { id: "lite" | "kit" | "pro"; name: string; price: number; gets: string[]; buyUrl?: string; earlyBird?: { price: number; buyers: number; active: boolean } }
export interface Kit {
  slug: string; name: string; short: string; who: string; te: string;
  date: { iso: string; label: string; source: string };
  preview: { cols: string[]; rows: string[][] }; // a real slice of the sheet's layout, drawn in HTML (not a fake screenshot)
  tiers: Tier[]; faqs: { q: string; a: string }[];
}

const SHEET_FAQ = [
  { q: "What do I get?", a: "A Google Sheet that copies into your own Google Drive with one tap, plus a short PDF guide. It works in the Google Sheets app on any phone. No account with us, no app to install." },
  { q: "How do I receive it?", a: "Right after payment, the success page and your email receipt carry the copy link. Tap it, then “Make a copy”." },
  { q: "Can I get a refund?", a: "Yes: if the link doesn't work or the kit isn't as described, email us within 7 days of buying for a full refund. See the refund policy." },
];

export const KITS: Kit[] = [
  {
    slug: "gate-2027", name: "GATE 2027 Final-120-Days Tracker", short: "Plan the last 120 days to GATE 2027 on one phone-friendly sheet.",
    who: "GATE 2027 candidates who have registered and want a day-by-day plan, revision on time, and honest mock-test analysis.",
    te: "GATE 2027 కోసం చివరి 120 రోజుల ప్లాన్: తెలుగు సూచనలతో, ఫోన్‌లోనే.",
    date: { iso: "2027-02-06", label: "6, 7, 13, 14, 20 and 21 Feb 2027", source: "IIT Madras (organising institute), iitm.ac.in" },
    preview: { cols: ["Topic", "Weight", "Done", "Next revision"], rows: [["Engineering Mathematics", "High", "✓", "in 3 days"], ["Digital Logic", "Medium", "✓", "in 7 days"], ["Computer Networks", "High", "", "today"], ["Operating Systems", "High", "", "-"]] },
    tiers: [
      { id: "lite", name: "Lite", price: 0, gets: ["Countdown to your exam day", "Official syllabus checklist (view-only)"] },
      { id: "kit", name: "Kit", price: 199, gets: ["Your own editable copy", "Daily log with a streak counter", "Spaced revision on days 1, 3, 7 and 21", "Weekly plan", "PDF guide + free updates"], earlyBird: { price: 99, buyers: 30, active: false } },
      { id: "pro", name: "Kit Pro", price: 299, gets: ["Everything in Kit", "Subjects weighted by GATE 2023–25 marks (published analysis, cited in the kit)", "Mock analyser: careless vs concept errors", "Telugu and Hindi instructions tab"] },
    ],
    faqs: [...SHEET_FAQ, { q: "Is this an official GATE product?", a: "No. It's an independent planning sheet by Kalpa Labs. Exam dates come from IIT Madras; always check the official GATE site." }],
  },
  {
    slug: "upsc-2027", name: "UPSC CSE 2027 Prelims Tracker", short: "Track every GS and CSAT topic to Prelims day, with revision that comes back on time.",
    who: "UPSC Civil Services 2027 aspirants preparing for Prelims, on their own or alongside coaching.",
    te: "UPSC ప్రిలిమ్స్ 2027 కోసం ప్రతి టాపిక్ ట్రాకర్: తెలుగు సూచనలతో.",
    date: { iso: "2027-05-23", label: "23 May 2027 (Prelims)", source: "UPSC calendar 2027, upsc.gov.in" },
    preview: { cols: ["Paper / topic", "Sources", "Done", "Next revision"], rows: [["GS1 · Modern History", "2", "✓", "in 7 days"], ["GS1 · Polity", "1", "✓", "in 3 days"], ["GS1 · Economy", "1", "", "today"], ["CSAT · Reasoning", "-", "", "-"]] },
    tiers: [
      { id: "lite", name: "Lite", price: 0, gets: ["Countdown to Prelims", "Syllabus checklist (view-only)"] },
      { id: "kit", name: "Kit", price: 199, gets: ["Your own editable copy", "Daily log with a streak counter", "Spaced revision on days 1, 3, 7 and 21", "Weekly plan", "PDF guide + free updates"], earlyBird: { price: 99, buyers: 30, active: false } },
      { id: "pro", name: "Kit Pro", price: 299, gets: ["Everything in Kit", "Subjects weighted by GATE 2023–25 marks (published analysis, cited in the kit)", "Mock analyser: careless vs concept errors", "Telugu and Hindi instructions tab"] },
    ],
    faqs: [...SHEET_FAQ, { q: "Is this an official UPSC product?", a: "No. It's an independent planning sheet by Kalpa Labs. Always check upsc.gov.in for notices." }],
  },
  {
    slug: "tax-sip-2026-27", name: "Salary Tax-Regime + SIP Goal Planner 2026-27", short: "Old vs new regime with marginal relief done right, plus a SIP goal planner, in one sheet.",
    who: "Salaried people choosing a tax regime, planning investment proofs (Jan–Mar), or setting a SIP for a goal.",
    te: "పాత vs కొత్త పన్ను విధానం, SIP లక్ష్య ప్లానర్: ఒకే షీట్‌లో.",
    date: { iso: "2027-03-31", label: "Investment proofs: Jan–Mar 2027", source: "Tax year 2026-27 under the Income-tax Act 2025" },
    preview: { cols: ["Gross salary", "New regime", "Old regime", "Better"], rows: [["₹12,75,000", "₹0", "₹1,40,400", "New"], ["₹13,00,000", "₹26,000", "₹1,48,200", "New"], ["₹25,00,000", "₹3,19,800", "₹5,22,600", "New"]] },
    tiers: [
      { id: "lite", name: "Lite", price: 0, gets: ["The free calculators on this site"] },
      { id: "kit", name: "Kit", price: 199, gets: ["Old vs new regime with marginal relief and cess", "HRA, 80C and 80D inputs", "SIP goal planner with step-up and inflation", "Loan prepay-vs-invest and EMI table", "PDF guide + updates for 2026-27"] },
    ],
    faqs: [...SHEET_FAQ, { q: "Is this tax or investment advice?", a: "No. It's a calculator in a sheet. It names no funds and uses only the return you assume. For your own case, ask a CA or a SEBI-registered adviser." }],
  },
];

// The whole ladder for the kits index (03-kits/PLAN.md; kits.test.ts checks every row).
export const LADDER: { tier: string; label: string; price: number }[] = [
  { tier: "Lite (free)", label: "Lite", price: 0 },
  { tier: "Kit", label: "Kit", price: 199 },
  { tier: "Kit Pro", label: "Kit Pro (exam kits)", price: 299 },
  { tier: "Bundle", label: "Bundle (both exam kits, or Tax + SIP + Loan)", price: 499 },
  { tier: "Institute licence (B2B)", label: "Institute licence, 50 students", price: 2999 },
];
export const kitBySlug = (s: string) => { const k = KITS.find((x) => x.slug === s); if (!k) throw new Error(`no kit ${s}`); return k; };
export const priceLabel = (t: Tier) => (t.price === 0 ? "Free" : `₹${t.price}`);

// ---------- seller details and the policy pages (Razorpay activation + Consumer Protection (E-Commerce) Rules 2020)
export const CONTACT = {
  seller: "Kalpa Labs (sole proprietorship of Akhil Kanigicharla)",
  udyam: "UDYAM-TS-02-0382711",
  address: "Hyderabad, Telangana, India",
  email: "aakhiil51458@gmail.com",
  grievanceOfficer: "Akhil Kanigicharla",
};

export const LEGAL: Record<string, { title: string; body: string[] }> = {
  about: { title: "About us", body: [
    `${CONTACT.seller}, Udyam ${CONTACT.udyam}, ${CONTACT.address}.`,
    "We make free money calculators in English and Telugu, and low-cost Google Sheets kits for exams and personal finance.",
    "The calculators are free and need no sign-up. They are calculators, not financial, tax or investment advice." ] },
  contact: { title: "Contact us", body: [
    `Email: ${CONTACT.email}. We reply within 2 working days.`,
    `Grievance officer: ${CONTACT.grievanceOfficer}, ${CONTACT.email}. We acknowledge every complaint within 48 hours and resolve it within one month.`,
    `Address: ${CONTACT.address}. Udyam ${CONTACT.udyam}.` ] },
  terms: { title: "Terms and conditions", body: [
    `These terms apply to buying a kit from ${CONTACT.seller}.`,
    "A kit is a Google Sheet template plus a PDF guide. You get a personal licence: use it yourself, and don't resell or share the copy link publicly. Institutes can buy a separate licence.",
    "The price shown on the kit page is the full price you pay. We are not registered under GST, so no GST is added.",
    "Kits and calculators are planning tools. They are not financial, tax, investment or exam advice, and we make no promise of marks or returns.",
    "Exam names belong to their conducting bodies. Our kits are independent and not endorsed by them.",
    "Indian law applies; courts at Hyderabad have jurisdiction." ] },
  privacy: { title: "Privacy policy", body: [
    "Calculators run in your browser. We don't store what you type into them.",
    "When you buy a kit, Razorpay processes the payment and shares your name, email and phone with us so we can send the kit and a receipt. We never see your card or UPI PIN.",
    "We use your email only to deliver the kit, send updates to it, and answer you. Marketing emails go only to people who ask for them, and every one has an unsubscribe link.",
    `We keep order records for 8 years for tax purposes and delete everything else on request. Write to ${CONTACT.email} to see, correct or delete your data (Digital Personal Data Protection Act, 2023).` ] },
  refunds: { title: "Cancellation and refund policy", body: [
    "Kits are digital and delivered at once, so an order can't be cancelled after payment.",
    `If the copy link doesn't work or the kit isn't as described, email ${CONTACT.email} within 7 days of buying for a full refund.`,
    "Refunds go back to the original payment method, usually within 5–7 working days after we approve them." ] },
  delivery: { title: "Delivery policy", body: [
    "Kits are digital: nothing is shipped.",
    "The copy link appears on the payment success page and in your email receipt within a few minutes of payment.",
    `If it hasn't arrived within 2 hours, email ${CONTACT.email} with your payment ID and we'll send it by hand.` ] },
};

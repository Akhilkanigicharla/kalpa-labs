#!/usr/bin/env node
// A13: data for the JobCard screens, made by the REAL core (lib/parse.mjs + lib/invoice.mjs), never typed by hand.
// One technician ("Ravi Cooling Services", SR Nagar), today's voice note, the bill it becomes, and the customers
// whose 6-month service falls due. All people and numbers are made up (90000 xxxxx phones).
//   node 02-jobcard/design/sample.mjs      → rewrites the <script id="jc-data"> block in app.html + invoice-sample.html
import fs from "node:fs";
import path from "node:path";
import QRCode from "qrcode";
import { computeInvoice, fmt, inWords, invoiceHTML, invoiceNo, upiLink } from "../lib/invoice.mjs";
import { parseTranscript } from "../lib/parse.mjs";

const HERE = path.dirname(new URL(import.meta.url).pathname);
export const TODAY = "2026-10-17";
// PLAN.md §2 price ladder (test_design checks these against PLAN.md)
export const PLAN = { freeCards: 10, freeMinutes: 20, pro: 149, proYear: 1490, team: 299 };
export const SUPPLIER = { name: "Ravi Cooling Services", address: "SR Nagar, Hyderabad 500038", phone: "+91 90000 22222", udyam: "UDYAM-TS-02-0000000", vpa: "jobcard.demo@upi" };

export const NOTE = "Customer Sita garu, Ameerpet lo, phone 90000 33333. Voltas 1.5 ton split AC cooling ledu, gas leak undi. Gas refill 2500, capacitor ki 450, service charge 300. Total 3250. Next service 6 months.";
// earlier jobs: [date, voice note]. Lakshmi's note has no "next service", so she gets no reminder (never invented).
const PAST = [
  ["2026-03-30", "Suresh garu Miyapur phone 90000 88888 Blue Star split AC general service, jet service 600, next service 6 months"],
  ["2026-04-12", "Ramesh garu Kukatpally, phone 90000 44444, LG window AC general service, jet service 600. Next service 6 months"],
  ["2026-04-25", "Customer Anjali, Madhapur, phone 90000 55555, Samsung fridge not cooling, compressor 4500, service charge 300, total 4800, malli 6 nelalu"],
  ["2026-05-02", "Prakash garu SR Nagar 90000 66666 Daikin split AC water leak, pipe work 800, next service 6 months"],
  ["2026-05-28", "Farhan garu Tolichowki phone 90000 99999 Lloyd split AC gas refill 2400, next service 6 months"],
  ["2026-10-09", "Lakshmi garu Begumpet phone 90000 77777 washing machine noise vastundi, fan motor 1200"],
];
export const APPLIANCE = { split_ac: ["Split AC", "స్ప్లిట్ ఏసీ"], window_ac: ["Window AC", "విండో ఏసీ"], cassette_ac: ["Cassette AC", "క్యాసెట్ ఏసీ"],
  ac: ["AC", "ఏసీ"], fridge: ["Fridge", "ఫ్రిజ్"], washing_machine: ["Washing machine", "వాషింగ్ మెషిన్"] };
export const ISSUE = { gas_leak: "Gas leak", not_cooling: "Not cooling", water_leak: "Water leak", noise: "Noise", not_starting: "Not starting", service: "General service", installation: "Installation" };

const day = (iso) => new Date(`${iso}T00:00:00Z`);
const daysBetween = (a, b) => Math.round((day(b) - day(a)) / 864e5);
const nice = (iso) => day(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });

export async function build() {
  const card = parseTranscript(NOTE, { now: day(TODAY) });
  const heard = { customer: !!card.customer.name, phone: !!card.customer.phone, appliance: !!card.appliance, problem: card.issues.length > 0,
    parts: card.parts.length > 0 && card.parts.every((p) => p.rate != null), next: !!card.next_service };

  const lines = card.parts.map((p) => ({ desc: p.desc, qty: p.qty, rate: p.rate }));
  const totals = computeInvoice({ kind: "unregistered", lines });
  const seq = 27; // 27th bill of FY 2026-27 for this technician
  const inv = { number: invoiceNo(seq, TODAY), date: nice(TODAY), supplier: SUPPLIER,
    customer: { name: `${card.customer.name} garu`, address: `${card.customer.area}, Hyderabad`, phone: `+91 ${card.customer.phone.slice(0, 5)} ${card.customer.phone.slice(5)}` } };
  const upi = upiLink({ vpa: SUPPLIER.vpa, name: SUPPLIER.name, amountPaise: totals.payable, invoice: inv.number });
  const qrSvg = await QRCode.toString(upi, { type: "svg", margin: 1, errorCorrectionLevel: "M" });
  const html = invoiceHTML(inv, totals, { qrSvg });

  const history = PAST.map(([date, note]) => ({ date, card: parseTranscript(note, { now: day(date) }) }));
  const reminders = history.filter((h) => h.card.next_service)
    .map((h) => ({ name: h.card.customer.name, area: h.card.customer.area, phone: h.card.customer.phone, appliance: APPLIANCE[h.card.appliance][0],
      applianceTe: APPLIANCE[h.card.appliance][1], brand: h.card.brand, last: nice(h.date), due: h.card.next_service, dueNice: nice(h.card.next_service),
      inDays: daysBetween(TODAY, h.card.next_service), lastBill: h.card.parts.reduce((s, p) => s + (p.rate || 0), 0) }))
    .filter((r) => r.inDays <= 30).sort((a, b) => a.inDays - b.inDays);
  const recent = [...history].reverse().slice(0, 3).map((h) => ({ name: h.card.customer.name, area: h.card.customer.area, date: nice(h.date),
    appliance: APPLIANCE[h.card.appliance][0], amount: h.card.parts.reduce((s, p) => s + (p.rate || 0), 0) }));

  return {
    today: TODAY, todayNice: nice(TODAY), plan: PLAN, supplier: { name: SUPPLIER.name, area: "SR Nagar" },
    job: { transcript: NOTE, seconds: 38, card, heard, appliance: APPLIANCE[card.appliance], issues: card.issues.map((i) => ISSUE[i]),
      nextNice: card.next_service ? nice(card.next_service) : null },
    invoice: { number: inv.number, date: inv.date, kind: totals.kind, payable: totals.payable, payableText: fmt(totals.payable),
      words: `Rupees ${inWords(totals.payable / 100)} only`, rows: totals.rows.map((r) => ({ desc: r.desc, amount: fmt(r.amountPaise) })), upi, qrSvg, html },
    recent, reminders,
    // the reminder the technician sends from his own WhatsApp, one customer at a time (no bulk, no templates needed)
    reminderText: "నమస్తే {name} గారు, మీ {applianceTe} సర్వీస్ సమయం వచ్చింది ({due}). ఈ వారం వచ్చి చేయమంటారా? – {supplier}",
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const data = await build();
  const app = path.join(HERE, "app.html");
  const page = fs.readFileSync(app, "utf8");
  const json = JSON.stringify(data, null, 1).replace(/</g, "\\u003c");
  const next = page.replace(/(<script id="jc-data" type="application\/json">)[\s\S]*?(<\/script>)/, `$1\n${json}\n$2`);
  if (next === page && !page.includes(json)) throw new Error("jc-data block not found in app.html");
  fs.writeFileSync(app, next);
  fs.writeFileSync(path.join(HERE, "invoice-sample.html"), data.invoice.html);
  console.log(`  ✓ ${data.invoice.number} ${data.invoice.payableText} · ${data.reminders.length} reminders due · written into app.html + invoice-sample.html`);
}

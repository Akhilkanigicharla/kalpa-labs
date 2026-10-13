// Run: cd 02-jobcard && npm test   (node:test, no network)
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import QRCode from "qrcode";
import { computeInvoice, inWords, invoiceHTML, invoiceNo, invoicePDF, upiLink, SAC } from "../lib/invoice.mjs";
import { parseTranscript } from "../lib/parse.mjs";

const supplier = { name: "Ravi Cooling Services", address: "SR Nagar, Hyderabad 500038", phone: "+91 90000 22222", udyam: "UDYAM-TS-02-0000000" };
const customer = { name: "Sita Devi", address: "Ameerpet, Hyderabad", phone: "+91 90000 33333" };

test("FY invoice series, ≤ 16 characters, resets on 1 April", () => {
  assert.equal(invoiceNo(1, "2026-10-13"), "JC/26-27/0001");
  assert.equal(invoiceNo(42, "2027-03-31"), "JC/26-27/0042");
  assert.equal(invoiceNo(1, "2027-04-01"), "JC/27-28/0001");
  assert.throws(() => invoiceNo(1, "2026-10-13", "JOBCARD"), /16 characters/);
});

test("unregistered technician: no GST shown or charged", () => {
  const t = computeInvoice({ kind: "unregistered", lines: [{ desc: "Gas refill", rate: 2500 }, { desc: "Capacitor", rate: 450 }] });
  assert.equal(t.taxable, 295000); assert.equal(t.cgst + t.sgst + t.igst, 0); assert.equal(t.payable, 295000);
  const html = invoiceHTML({ number: "JC/26-27/0001", date: "13 Oct 2026", supplier, customer }, t);
  assert.match(html, /Bill of Supply \(not a tax invoice\)/); assert.doesNotMatch(html, /CGST|SGST|IGST|GSTIN/);
});

test("composition scheme: Bill of Supply with the Rule 49 line", () => {
  const t = computeInvoice({ kind: "composition", lines: [{ desc: "Jet service", rate: 600 }] });
  assert.equal(t.payable, 60000);
  assert.match(invoiceHTML({ number: "JC/26-27/0002", date: "x", supplier: { ...supplier, gstin: "36ABCDE1234F1Z5" }, customer }, t), /not eligible to collect tax/);
});

test("regular GST: CGST + SGST inside Telangana, IGST across states, round off", () => {
  const local = computeInvoice({ kind: "regular", lines: [{ desc: "AC repair", sac: SAC.home, rate: 1234.5 }] });
  assert.equal(local.taxable, 123450); assert.equal(local.cgst, 11111); assert.equal(local.sgst, 11111); assert.equal(local.igst, 0);
  assert.equal(local.total, 145672); assert.equal(local.payable, 145700); assert.equal(local.roundOff, 28);
  const inter = computeInvoice({ kind: "regular", lines: [{ desc: "AC repair", rate: 1000 }], placeOfSupply: "Andhra Pradesh" });
  assert.equal(inter.igst, 18000); assert.equal(inter.cgst, 0); assert.ok(inter.interState); assert.equal(inter.placeCode, "37");
  assert.throws(() => computeInvoice({ kind: "regular", lines: [] }), /at least one line/);
  assert.throws(() => computeInvoice({ kind: "regular", lines: [{ desc: "x", qty: 0, rate: 1 }] }), /bad line/);
});

test("amount in words, Indian system (lakh/crore)", () => {
  assert.equal(inWords(2950), "Two Thousand Nine Hundred Fifty");
  assert.equal(inWords(145700), "One Lakh Forty Five Thousand Seven Hundred");
  assert.equal(inWords(12345678), "One Crore Twenty Three Lakh Forty Five Thousand Six Hundred Seventy Eight");
  assert.equal(inWords(0), "Zero");
});

test("UPI link is well formed and rejects bad IDs", () => {
  const u = upiLink({ vpa: "ravicooling@okaxis", name: "Ravi Cooling", amountPaise: 295000, invoice: "JC/26-27/0001" });
  assert.equal(u, "upi://pay?pa=ravicooling%40okaxis&pn=Ravi%20Cooling&am=2950.00&cu=INR&tn=Invoice%20JC%2F26-27%2F0001");
  assert.throws(() => upiLink({ vpa: "not a vpa", name: "x", amountPaise: 1, invoice: "x" }), /invalid UPI/);
});

test("English PDF with pdf-lib: real PDF, text extractable, Telugu refused", async () => {
  const t = computeInvoice({ kind: "regular", lines: [{ desc: "AC repair", sac: SAC.home, rate: 1234.5 }, { desc: "Gas refill", rate: 2500 }] });
  const inv = { number: invoiceNo(7, "2026-10-13"), date: "13 Oct 2026", supplier: { ...supplier, gstin: "36ABCDE1234F1Z5" }, customer };
  const qrPng = await QRCode.toBuffer(upiLink({ vpa: "ravicooling@okaxis", name: "Ravi", amountPaise: t.payable, invoice: inv.number }), { width: 240 });
  const latin = fs.readFileSync(new URL("../node_modules/@fontsource/anek-latin/files/anek-latin-latin-400-normal.woff", import.meta.url));
  const bytes = await invoicePDF(inv, t, { qrPng, fontBytes: latin });
  assert.equal(Buffer.from(bytes.slice(0, 5)).toString(), "%PDF-");
  const f = path.join(os.tmpdir(), `jc-${process.pid}.pdf`); fs.writeFileSync(f, bytes);
  try {
    const txt = execFileSync("pdftotext", ["-layout", f, "-"]).toString();
    for (const s of ["Tax Invoice", "JC/26-27/0007", "CGST 9%", "SGST 9%", "Place of supply: Telangana (36)", "Rupees Four Thousand Four Hundred Seven only", "Rs 4,407.00"]) assert.ok(txt.includes(s), `missing ${s}`);
  } catch (e) { if (e.code !== "ENOENT") throw e; } // pdftotext not installed: the byte check above still ran
  await assert.rejects(invoicePDF({ ...inv, customer: { name: "సీత" } }, t), /Latin-only/);
});

test("bilingual HTML escapes input and carries Telugu labels", () => {
  const t = computeInvoice({ kind: "unregistered", lines: [{ desc: "<script>x</script>", rate: 1 }] });
  const html = invoiceHTML({ number: "JC/26-27/0003", date: "d", supplier, customer: { name: "సీత" } }, t);
  assert.ok(!html.includes("<script>x")); assert.match(html, /మొత్తం/); assert.match(html, /సీత/);
});

// ---------- transcript parser ----------
const T1 = "Customer name Sita Devi, phone 98480 12345, Ameerpet lo split AC 1.5 ton Voltas. Cooling ledu, gas leak undi. Gas refill 2500, capacitor ki 450, service charge 300. Total 3250. Next service 6 months.";
test("Tenglish transcript -> job card", () => {
  const c = parseTranscript(T1, { now: new Date("2026-10-13T00:00:00Z") });
  assert.equal(c.customer.name, "Sita Devi"); assert.equal(c.customer.phone, "9848012345"); assert.equal(c.customer.area, "Ameerpet");
  assert.equal(c.appliance, "split_ac"); assert.equal(c.capacity_tons, 1.5); assert.equal(c.brand, "Voltas");
  assert.deepEqual(c.issues.sort(), ["gas_leak", "not_cooling"]);
  assert.deepEqual(c.parts.map((p) => [p.desc, p.rate]), [["Gas refill", 2500], ["Capacitor", 450], ["Service charge", 300]]);
  assert.equal(c.total, 3250); assert.equal(c.total_check, "matches parts");
  assert.equal(c.next_service, "2027-04-13"); assert.deepEqual(c.missing, []);
});

test("Telugu number words and script", () => {
  const c = parseTranscript("రమేష్ గారు, ఫ్రిజ్ కూలింగ్ లేదు. Gas refill rendu velu aidu vandalu. Phone 9000011111");
  assert.equal(c.appliance, "fridge"); assert.ok(c.issues.includes("not_cooling"));
  assert.equal(c.parts[0].rate, 2500); assert.equal(c.customer.phone, "9000011111");
  const d = parseTranscript("window AC noise vastundi, capacitor ₹ 1,200 ayyindi, compressor 2.5k");
  assert.equal(d.appliance, "window_ac"); assert.deepEqual(d.issues, ["noise"]);
  assert.deepEqual(d.parts.map((p) => p.rate), [1200, 2500]);
});

test("never invents: unknown amounts stay null and gaps are listed", () => {
  const c = parseTranscript("LG AC service chesanu, PCB repair cheyali, customer ki call cheyyali");
  assert.equal(c.brand, "LG"); assert.equal(c.appliance, "ac");
  assert.deepEqual(c.parts.map((p) => [p.desc, p.rate]), [["PCB repair", null]]);
  assert.deepEqual(c.missing, ["phone"]); assert.equal(c.total, null);
  const off = parseTranscript("split AC gas refill 2500 total 3000 phone 9123456780");
  assert.equal(off.total_check, "spoken 3000 vs parts 2500");
});

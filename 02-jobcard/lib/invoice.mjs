// JobCard invoice core: maths, bilingual HTML, and an English PDF. Our own code (MIT-able).
// Rules: 02-jobcard/research/deep-scan-v2.md "Indian invoice rules" (CA to confirm in b2.q12).
//
// Deep Scan v2 finding: pdf-lib 1.17.1 + @pdf-lib/fontkit 1.1.1 cannot set Telugu correctly
// (subset mode drops glyphs; full embed ignores mark positioning; the Indic shaper even needs
// a regenerator-runtime polyfill). Browsers shape Telugu perfectly, so:
//   - Telugu / bilingual invoice  -> invoiceHTML() printed by the phone's WebView (expo-print)
//   - English invoice from a server or Edge Function -> invoicePDF() with pdf-lib (Latin only)

export const KINDS = {
  unregistered: { title: "Bill of Supply", te: "బిల్లు", note: "Bill of Supply (not a tax invoice). Supplier not registered under GST; no GST charged." },
  composition: { title: "Bill of Supply", te: "బిల్లు", note: "Composition taxable person, not eligible to collect tax on supplies." },
  regular: { title: "Tax Invoice", te: "టాక్స్ ఇన్‌వాయిస్", note: "" },
};
export const SAC = { home: "998715", commercial: "998717", install: "998736" };
const GST_RATE = 0.18;
const STATE_CODES = { Telangana: "36", "Andhra Pradesh": "37", Karnataka: "29", Maharashtra: "27", "Tamil Nadu": "33" };

/** Financial-year series number: JC/26-27/0001 (≤ 16 characters, fresh every 1 April).
 *  A "YYYY-MM-DD" string is that calendar date; any other date/instant is read in IST (as the SQL next_invoice_no does),
 *  so an invoice made at 00:30 IST on 1 April starts the new series. */
export function invoiceNo(seq, date = new Date(), prefix = "JC") {
  const d = typeof date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(date) ? new Date(date + "T00:00:00Z") : new Date(new Date(date).getTime() + 330 * 60000);
  const y = d.getUTCFullYear() - (d.getUTCMonth() < 3 ? 1 : 0);
  const fy = `${String(y).slice(2)}-${String(y + 1).slice(2)}`;
  const no = `${prefix}/${fy}/${String(seq).padStart(4, "0")}`;
  if (no.length > 16) throw new Error(`invoice number ${no} is longer than 16 characters (GST Rule 46/49)`);
  return no;
}

const paise = (x) => Math.round(Number(x) * 100);
const rupees = (p) => p / 100;

/** Totals in paise. Lines: [{ desc, sac?, qty, rate }]. */
export function computeInvoice({ kind = "unregistered", lines, supplierState = "Telangana", placeOfSupply = "Telangana" }) {
  if (!KINDS[kind]) throw new Error(`unknown invoice kind ${kind}`);
  if (!Array.isArray(lines) || !lines.length) throw new Error("an invoice needs at least one line");
  const rows = lines.map((l) => {
    const qty = Number(l.qty ?? 1); const rate = paise(l.rate);
    if (!(qty > 0) || rate < 0) throw new Error(`bad line: ${l.desc}`);
    return { ...l, qty, ratePaise: rate, amountPaise: Math.round(qty * rate) };
  });
  const taxable = rows.reduce((s, r) => s + r.amountPaise, 0);
  let cgst = 0, sgst = 0, igst = 0;
  if (kind === "regular") {
    if (supplierState === placeOfSupply) { cgst = Math.round(taxable * GST_RATE / 2); sgst = cgst; }
    else igst = Math.round(taxable * GST_RATE);
  }
  const total = taxable + cgst + sgst + igst;
  const roundedRupees = Math.round(total / 100);
  return { kind, rows, taxable, cgst, sgst, igst, total, roundOff: roundedRupees * 100 - total, payable: roundedRupees * 100,
           interState: kind === "regular" && supplierState !== placeOfSupply, placeOfSupply, placeCode: STATE_CODES[placeOfSupply] || "" };
}

const ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
  "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"];
const TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];
function two(n) { return n < 20 ? ONES[n] : `${TENS[Math.floor(n / 10)]}${n % 10 ? " " + ONES[n % 10] : ""}`; }
function three(n) { const h = Math.floor(n / 100), r = n % 100; return [h ? `${ONES[h]} Hundred` : "", r ? two(r) : ""].filter(Boolean).join(" "); }

/** 1,23,45,678 -> "One Crore Twenty Three Lakh Forty Five Thousand Six Hundred Seventy Eight" (Indian system). */
export function inWords(rupeesInt) {
  let n = Math.floor(Math.abs(rupeesInt));
  if (n === 0) return "Zero";
  const parts = [];
  const crore = Math.floor(n / 1e7); n %= 1e7;
  const lakh = Math.floor(n / 1e5); n %= 1e5;
  const thousand = Math.floor(n / 1e3); n %= 1e3;
  if (crore) parts.push(`${crore >= 100 ? inWords(crore) : two(crore)} Crore`);
  if (lakh) parts.push(`${two(lakh)} Lakh`);
  if (thousand) parts.push(`${two(thousand)} Thousand`);
  if (n) parts.push(three(n));
  return parts.join(" ");
}

export const fmt = (p) => "₹" + (p / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** UPI deep link for the QR (NPCI upi:// format). Payee VPA comes from the technician's profile. */
export function upiLink({ vpa, name, amountPaise, invoice }) {
  if (!/^[\w.\-]{2,256}@[a-zA-Z][\w]{2,64}$/.test(vpa || "")) throw new Error("invalid UPI ID");
  const q = new URLSearchParams({ pa: vpa, pn: name, am: (amountPaise / 100).toFixed(2), cu: "INR", tn: `Invoice ${invoice}` });
  return `upi://pay?${q.toString().replace(/\+/g, "%20")}`;
}

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/** Bilingual invoice HTML for expo-print / any browser (correct Telugu shaping). */
export function invoiceHTML(inv, t, { qrSvg = "" } = {}) {
  const k = KINDS[t.kind];
  const rows = t.rows.map((r, i) => `<tr><td>${i + 1}</td><td>${esc(r.desc)}${r.sac ? `<br><small>SAC ${esc(r.sac)}</small>` : ""}</td><td class="n">${r.qty}</td><td class="n">${fmt(r.ratePaise)}</td><td class="n">${fmt(r.amountPaise)}</td></tr>`).join("");
  const tax = t.kind !== "regular" ? "" : t.interState
    ? `<tr><td colspan="4">IGST 18%</td><td class="n">${fmt(t.igst)}</td></tr>`
    : `<tr><td colspan="4">CGST 9%</td><td class="n">${fmt(t.cgst)}</td></tr><tr><td colspan="4">SGST 9%</td><td class="n">${fmt(t.sgst)}</td></tr>`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${esc(inv.number)}</title><style>
:root{--fg:#1E2A1F;--muted:#5A6152;--rule:#DCD5C3;--accent:#2F6A3A;--madder:#8A4A28;--gold:#C38E12;--l2:#2F6F78}
body{font:13px/1.5 "Anek Latin","Anek Telugu",system-ui,sans-serif;color:var(--fg);margin:24px}
h1{font:400 26px "Rozha One",Georgia,serif;margin:0;color:var(--accent)} .te{font-family:"Anek Telugu",system-ui,sans-serif}
.band{height:6px;background:linear-gradient(90deg,var(--madder),var(--gold),var(--l2));margin:8px 0 16px}
table{width:100%;border-collapse:collapse} td,th{padding:6px 4px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}
.n{text-align:right;font-variant-numeric:tabular-nums} .tot td{font-weight:700;border-top:2px solid var(--fg)} small,.muted{color:var(--muted)}
.grid{display:flex;justify-content:space-between;gap:16px;margin-bottom:12px} .qr{width:120px}
</style></head><body>
<div class="grid"><div><h1>${esc(k.title)} <span class="te" style="font-size:18px">/ ${esc(k.te)}</span></h1>
${k.note ? `<div class="muted">${esc(k.note)}</div>` : ""}</div>
<div class="n" style="white-space:nowrap"><b>${esc(inv.number)}</b><br>${esc(inv.date)}</div></div><div class="band"></div>
<div class="grid"><div><b>${esc(inv.supplier.name)}</b><br>${esc(inv.supplier.address)}<br>${esc(inv.supplier.phone)}
${inv.supplier.gstin ? `<br>GSTIN ${esc(inv.supplier.gstin)}` : ""}${inv.supplier.udyam ? `<br>Udyam ${esc(inv.supplier.udyam)}` : ""}</div>
<div><span class="muted">Bill to / <span class="te">కస్టమర్</span></span><br><b>${esc(inv.customer.name)}</b><br>${esc(inv.customer.address || "")}<br>${esc(inv.customer.phone || "")}
${t.kind === "regular" ? `<br>Place of supply: ${esc(t.placeOfSupply)} (${esc(t.placeCode)})` : ""}</div></div>
<table><thead><tr><th>#</th><th>Work / <span class="te">పని</span></th><th class="n">Qty</th><th class="n">Rate</th><th class="n">Amount</th></tr></thead>
<tbody>${rows}${tax}${t.roundOff ? `<tr><td colspan="4">Round off</td><td class="n">${fmt(t.roundOff)}</td></tr>` : ""}
<tr class="tot"><td colspan="4">Total / <span class="te">మొత్తం</span></td><td class="n">${fmt(t.payable)}</td></tr></tbody></table>
<p>Rupees ${esc(inWords(t.payable / 100))} only</p>
<div class="grid"><div class="muted">${t.kind === "regular" ? "Reverse charge: No<br>" : ""}${esc(inv.footer || "Thank you! / ధన్యవాదాలు!")}</div>${qrSvg ? `<div class="qr">${qrSvg}<div class="muted">Scan to pay (UPI)</div></div>` : ""}</div>
</body></html>`;
}

/** English invoice PDF with pdf-lib (Latin text only; see the note at the top). Returns Uint8Array. */
export async function invoicePDF(inv, t, { fontBytes, boldBytes, qrPng } = {}) {
  const { PDFDocument, rgb, StandardFonts } = await import("pdf-lib");
  const doc = await PDFDocument.create();
  doc.setTitle(inv.number); doc.setProducer("JobCard"); doc.setCreator("Kalpa Labs JobCard");
  let font, bold;
  if (fontBytes) {
    const fontkit = (await import("@pdf-lib/fontkit")).default; doc.registerFontkit(fontkit);
    font = await doc.embedFont(fontBytes, { subset: true }); bold = boldBytes ? await doc.embedFont(boldBytes, { subset: true }) : font;
  } else { font = await doc.embedFont(StandardFonts.Helvetica); bold = await doc.embedFont(StandardFonts.HelveticaBold); }
  // fontsource's "latin" subset of Anek Latin has no ₹ glyph (found in Deep Scan v2): fall back to "Rs"
  const hasRupee = fontBytes && font.getCharacterSet().includes(0x20b9);
  const money = (p) => (hasRupee ? "₹" : "Rs ") + (p / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (/[^\u0000-ɏ₹–—•’‘“”]/.test(JSON.stringify(inv) + t.rows.map((r) => r.desc).join(""))) throw new Error("invoicePDF is Latin-only; use invoiceHTML for Telugu");
  const page = doc.addPage([595.28, 841.89]); // A4
  const ink = rgb(0.098, 0.11, 0.2), muted = rgb(0.36, 0.38, 0.47), accent = rgb(0.165, 0.227, 0.561);
  let y = 800;
  const text = (s, x, size = 10, f = font, color = ink) => page.drawText(String(s), { x, y, size, font: f, color });
  const right = (s, xr, size = 10, f = font) => page.drawText(String(s), { x: xr - f.widthOfTextAtSize(String(s), size), y, size, font: f, color: ink });
  const k = KINDS[t.kind];
  text(k.title, 40, 20, bold, accent); right(inv.number, 555, 11, bold); y -= 16; right(inv.date, 555);
  if (k.note) text(k.note, 40, 8, font, muted);
  y -= 8; page.drawRectangle({ x: 40, y, width: 515, height: 4, color: rgb(0.698, 0.227, 0.173) }); y -= 22;
  text(inv.supplier.name, 40, 11, bold); text("Bill to", 320, 9, font, muted); y -= 14;
  text(inv.supplier.address, 40, 9); text(inv.customer.name, 320, 11, bold); y -= 13;
  text(inv.supplier.phone, 40, 9); text(inv.customer.address || "", 320, 9); y -= 13;
  if (inv.supplier.gstin) text(`GSTIN ${inv.supplier.gstin}`, 40, 9); else if (inv.supplier.udyam) text(`Udyam ${inv.supplier.udyam}`, 40, 9);
  text(inv.customer.phone || "", 320, 9); y -= 13;
  if (t.kind === "regular") { text(`Place of supply: ${t.placeOfSupply} (${t.placeCode})`, 320, 9); y -= 13; }
  y -= 14; text("#", 40, 9, bold); text("Work", 60, 9, bold); right("Qty", 380, 9, bold); right("Rate", 465, 9, bold); right("Amount", 555, 9, bold);
  y -= 6; page.drawLine({ start: { x: 40, y }, end: { x: 555, y }, thickness: 0.5, color: muted }); y -= 14;
  t.rows.forEach((r, i) => {
    text(i + 1, 40, 10); text(r.desc + (r.sac ? `  (SAC ${r.sac})` : ""), 60, 10); right(r.qty, 380); right(money(r.ratePaise), 465); right(money(r.amountPaise), 555); y -= 16;
  });
  const line = (label, p, f = font) => { text(label, 300, 10, f); right(money(p), 555, 10, f); y -= 15; };
  y -= 4; line("Taxable value", t.taxable);
  if (t.kind === "regular") { if (t.interState) line("IGST 18%", t.igst); else { line("CGST 9%", t.cgst); line("SGST 9%", t.sgst); } }
  if (t.roundOff) line("Round off", t.roundOff);
  page.drawLine({ start: { x: 300, y: y + 10 }, end: { x: 555, y: y + 10 }, thickness: 1, color: ink });
  line("Total", t.payable, bold); y -= 4;
  text(`Rupees ${inWords(t.payable / 100)} only`, 40, 10); y -= 16;
  if (t.kind === "regular") { text("Reverse charge: No", 40, 9, font, muted); y -= 14; }
  if (qrPng) { const img = await doc.embedPng(qrPng); page.drawImage(img, { x: 455, y: y - 100, width: 100, height: 100 }); text("Scan to pay (UPI)", 455, 8, font, muted); }
  return doc.save();
}

// A121: GST-ready receipt for a paid booking. Ideas from MIT github.com/piratuks/invoice-builder (tax-inclusive
// pricing, discounts); fields per CGST Rule 46 (tax invoice) and Rule 49 (bill of supply), checked 25 Oct 2026 on
// gstzen.in + blog.petpooja.com. A CA must confirm before go-live (C23). Pure functions, no network.
//
// cfg.gst = { mode: "none" | "composition" | "regular", gstin, state, sac, rate, price_includes_gst (default true),
//             prefix (2–4 letters for the serial) }

const DOC = { none: "Receipt", composition: "Bill of Supply", regular: "Tax Invoice" };
const GSTIN = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/;

const paise = (x) => Math.round(x * 100);
const rupees = (p) => "₹" + (p / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** "₹1,200" or "1200" or 1200 → 120000 paise; "from ₹15,000" → 1500000; nothing → null */
function priceToPaise(price) {
  if (typeof price === "number") return paise(price);
  const m = String(price || "").replace(/,/g, "").match(/(\d+(?:\.\d{1,2})?)/);
  return m ? paise(parseFloat(m[1])) : null;
}

/** Indian financial year label for a date: 25 Oct 2026 → "2627" (Apr 2026–Mar 2027). */
function fyOf(d) {
  const y = d.getUTCFullYear(), start = d.getUTCMonth() >= 3 ? y : y - 1;
  return `${String(start).slice(2)}${String(start + 1).slice(2)}`;
}

/** Consecutive serial, ≤16 characters, unique per financial year (Rule 46(b) / 49(b)): "GS/2627/0042". */
function serialFor(prefix, n, date) {
  const p = String(prefix || "KB").toUpperCase().replace(/[^A-Z]/g, "").slice(0, 4) || "KB";
  const s = `${p}/${fyOf(date)}/${String(n).padStart(4, "0")}`;
  if (s.length > 16) throw new Error("serial longer than 16 characters");
  return s;
}

/** Tax split. Prices on the menu include GST by default (what customers see is what they pay). Intra-state → CGST + SGST. */
function taxLines(totalPaise, rate, includes = true, interState = false) {
  const taxable = includes ? Math.round((totalPaise * 100) / (100 + rate)) : totalPaise;
  const tax = includes ? totalPaise - taxable : Math.round((totalPaise * rate) / 100);
  if (interState) return { taxable, lines: [{ name: `IGST ${rate}%`, amount: tax }], total: taxable + tax };
  const half = Math.floor(tax / 2);
  return { taxable, lines: [{ name: `CGST ${rate / 2}%`, amount: half }, { name: `SGST ${rate / 2}%`, amount: tax - half }], total: taxable + tax };
}

/** Build the receipt object, or throw with a plain reason when the shop's GST settings are incomplete. */
function makeReceipt(cfg, sale, { n, date = new Date() }) {
  const g = Object.assign({ mode: "none", price_includes_gst: true }, cfg.gst || {});
  if (!DOC[g.mode]) throw new Error(`unknown GST mode: ${g.mode}`);
  if (g.mode !== "none" && !GSTIN.test(String(g.gstin || ""))) throw new Error("a valid 15-character GSTIN is needed for a bill of supply or tax invoice");
  if (g.mode === "regular" && !(g.rate > 0 && g.sac)) throw new Error("tax invoice needs the SAC code and GST rate");
  const items = (sale.items || []).map((it) => {
    const each = it.amount != null ? paise(it.amount) : priceToPaise(it.price);
    if (each == null) throw new Error(`no price for ${it.name}`);
    return { name: it.name, qty: it.qty || 1, amount: each * (it.qty || 1) };
  });
  if (!items.length) throw new Error("nothing to bill");
  const gross = items.reduce((a, i) => a + i.amount, 0);
  const discount = Math.min(gross, paise(sale.discount || 0));
  const value = gross - discount;
  const r = {
    title: DOC[g.mode], serial: serialFor(g.prefix, n, date), date: date.toISOString().slice(0, 10),
    supplier: { name: cfg.business, address: cfg.address || "", gstin: g.mode === "none" ? null : g.gstin },
    customer: { name: sale.customer || "Customer", gstin: sale.customer_gstin || null },
    items, gross, discount, value, sac: g.sac || null, tax: null, total: value, note: null,
  };
  if (g.mode === "regular") {
    const t = taxLines(value, g.rate, g.price_includes_gst, !!sale.inter_state);
    Object.assign(r, { tax: t.lines, taxable: t.taxable, total: t.total, place_of_supply: sale.inter_state ? sale.state : g.state || null });
  } else if (g.mode === "composition") {
    r.note = "Composition taxable person, not eligible to collect tax on supplies.";
  } else {
    r.note = "Not registered under GST. No GST charged.";
  }
  return r;
}

/** WhatsApp-friendly text (sent only to the customer who paid). */
function receiptText(r) {
  const L = [`*${r.title}* ${r.serial}`, `${r.supplier.name}${r.supplier.gstin ? ` · GSTIN ${r.supplier.gstin}` : ""}`, `Date: ${r.date}`, `Billed to: ${r.customer.name}`, ""];
  for (const i of r.items) L.push(`${i.name}${i.qty > 1 ? ` × ${i.qty}` : ""}: ${rupees(i.amount)}`);
  if (r.discount) L.push(`Discount: −${rupees(r.discount)}`);
  if (r.tax) { L.push(`Taxable value: ${rupees(r.taxable)}${r.sac ? ` (SAC ${r.sac})` : ""}`); for (const t of r.tax) L.push(`${t.name}: ${rupees(t.amount)}`); }
  L.push(`*Total paid: ${rupees(r.total)}*`);
  if (r.note) L.push("", r.note);
  return L.join("\n");
}

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/** Printable page (Save as PDF from the browser), Kalpa colours, readable at 390 px. */
function receiptHtml(r) {
  const rows = r.items.map((i) => `<tr><td>${esc(i.name)}${i.qty > 1 ? ` × ${i.qty}` : ""}</td><td class="n">${rupees(i.amount)}</td></tr>`).join("");
  const extra = [r.discount ? `<tr><td>Discount</td><td class="n">−${rupees(r.discount)}</td></tr>` : "",
    r.tax ? `<tr><td>Taxable value${r.sac ? ` · SAC ${esc(r.sac)}` : ""}</td><td class="n">${rupees(r.taxable)}</td></tr>` + r.tax.map((t) => `<tr><td>${esc(t.name)}</td><td class="n">${rupees(t.amount)}</td></tr>`).join("") : ""].join("");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(r.title)} ${esc(r.serial)}</title><style>
:root{--bg:#F6F1E4;--ink:#2B2A22;--muted:#66655A;--leaf:#2F6B3A;--line:#D9D1BC}
@media (prefers-color-scheme:dark){:root{--bg:#1B1A15;--ink:#F1ECDD;--muted:#B4B3A4;--leaf:#8FCB8C;--line:#3A382E}}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}
main{max-width:560px;margin:0 auto;padding:24px 16px}h1{margin:0;font-size:1.5rem;color:var(--leaf)}
.meta{color:var(--muted);font-size:.9rem}table{width:100%;border-collapse:collapse;margin:16px 0}
td{padding:8px 0;border-bottom:1px solid var(--line);vertical-align:top}.n{text-align:right;white-space:nowrap;padding-left:12px}
.total td{font-weight:700;font-size:1.1rem;border-bottom:0}.note{color:var(--muted);font-size:.9rem}
@media print{body{background:#fff;color:#000}}</style></head><body><main>
<h1>${esc(r.title)}</h1><p class="meta">No. ${esc(r.serial)} · ${esc(r.date)}</p>
<p><strong>${esc(r.supplier.name)}</strong><br>${esc(r.supplier.address)}${r.supplier.gstin ? `<br>GSTIN ${esc(r.supplier.gstin)}` : ""}</p>
<p>Billed to: ${esc(r.customer.name)}${r.customer.gstin ? `<br>GSTIN ${esc(r.customer.gstin)}` : ""}${r.place_of_supply ? `<br>Place of supply: ${esc(r.place_of_supply)}` : ""}</p>
<table>${rows}${extra}<tr class="total"><td>Total paid</td><td class="n">${rupees(r.total)}</td></tr></table>
${r.note ? `<p class="note">${esc(r.note)}</p>` : ""}<p class="note">Computer-generated receipt.</p></main></body></html>`;
}

module.exports = { makeReceipt, receiptText, receiptHtml, taxLines, serialFor, fyOf, priceToPaise, rupees };

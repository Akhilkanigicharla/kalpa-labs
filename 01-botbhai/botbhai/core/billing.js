// BotBhai billing core (A05 / P1-W2-06): Kalpa Labs → salon invoices. Pure functions, no npm packages.
// Rules and sources: 01-botbhai/research/billing-scan.md
//   · "Invoice", never "Tax Invoice"; no GST shown or charged (CGST Act s.32(1): unregistered persons can't collect tax)
//   · one series per financial year, KL/26-27/001 (≤ 16 characters), new series at 00:00 IST on 1 April
//   · Udyam number on every invoice; amount in words (Indian system)
//   · UPI: NPCI linking spec fields pa, pn, am (2 decimals, no mam → fixed amount), cu=INR, tr (unique per invoice), tn
// The maths and words mirror 02-jobcard/lib/invoice.mjs (our own code); core/billing.test.js checks they agree.
const { renderSVG } = require("./vendor/uqr/index.cjs"); // MIT © Project Nayuki, © 2023 Anthony Fu (unmodified)

const IST_MS = 330 * 60000;
const istDate = (d = new Date()) => new Date(new Date(d).getTime() + IST_MS); // read with getUTC*()

/** "26-27" for any instant, using the Indian date (FY starts 1 April). */
function fyOf(d = new Date()) {
  const t = istDate(d); const y = t.getUTCFullYear() - (t.getUTCMonth() < 3 ? 1 : 0);
  return `${String(y).slice(2)}-${String(y + 1).slice(2)}`;
}
function invoiceNo(seq, d = new Date(), prefix = "KL") {
  if (!Number.isInteger(seq) || seq < 1) throw new Error("invoice sequence must be a whole number ≥ 1");
  const no = `${prefix}/${fyOf(d)}/${String(seq).padStart(3, "0")}`;
  if (no.length > 16) throw new Error(`invoice number ${no} is longer than 16 characters`);
  return no;
}

const MAX_PAISE = 10000000 * 100; // ₹1 crore per invoice: a typo guard, far above any BotBhai plan
/** Lines [{ desc, qty?, rate (₹) | rate_paise }] → { rows: [{ desc, qty, rate, amount }], total } in paise. */
function computeBill(lines) {
  if (!Array.isArray(lines) || !lines.length) throw new Error("an invoice needs at least one line");
  const rows = lines.map((l) => {
    const desc = String((l && l.desc) || "").trim().slice(0, 140);
    const qty = Number(l && l.qty != null ? l.qty : 1);
    const rate = l && l.rate_paise != null ? Math.round(Number(l.rate_paise)) : Math.round(Number(l && l.rate) * 100);
    if (!desc || !Number.isFinite(qty) || qty <= 0 || qty > 1000 || !Number.isFinite(rate) || rate < 0) throw new Error(`bad line: ${desc || "(no description)"}`);
    return { desc, qty, rate, amount: Math.round(qty * rate) };
  });
  const total = rows.reduce((s, r) => s + r.amount, 0);
  if (total > MAX_PAISE) throw new Error("amount too large: check the figure");
  if (total <= 0) throw new Error("bad line: the total must be more than ₹0");
  return { rows, total };
}

const ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
  "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"];
const TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];
const two = (n) => (n < 20 ? ONES[n] : `${TENS[Math.floor(n / 10)]}${n % 10 ? " " + ONES[n % 10] : ""}`);
const three = (n) => { const h = Math.floor(n / 100), r = n % 100; return [h ? `${ONES[h]} Hundred` : "", r ? two(r) : ""].filter(Boolean).join(" "); };
function inWords(rupeesInt) {
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
const money = (p) => "₹" + (p / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
function wordsFor(paise) {
  const r = Math.floor(paise / 100), ps = paise % 100;
  return `Rupees ${inWords(r)}${ps ? ` and ${inWords(ps)} Paise` : ""} only`;
}

const VPA = /^[A-Za-z0-9.\-_]{2,256}@[A-Za-z][A-Za-z0-9]{2,64}$/;
function upiLink({ vpa, name, amountPaise, number }) {
  if (!VPA.test(vpa || "")) throw new Error("invalid UPI ID");
  if (!(amountPaise > 0)) throw new Error("UPI amount must be more than ₹0");
  const q = new URLSearchParams({ pa: vpa, pn: String(name || "").slice(0, 50), am: (amountPaise / 100).toFixed(2), cu: "INR",
    tr: String(number).replace(/[^A-Za-z0-9]/g, "").slice(0, 35), tn: `Invoice ${number}`.slice(0, 50) });
  return `upi://pay?${q.toString().replace(/\+/g, "%20")}`;
}
/** Black on white with a 4-module quiet zone: the most reliable thing for every UPI app's scanner. */
const qrSvg = (text) => renderSVG(text, { ecc: "M", border: 4, pixelSize: 1, whiteColor: "#FFFFFF", blackColor: "#000000" })
  .replace(/^<svg /, '<svg role="img" aria-label="UPI payment QR code" ');

/** Whole days late, counted in IST calendar days after the due date. */
function overdueDays(inv, now = new Date()) {
  if (!inv || inv.status !== "due" || !inv.due_on) return 0;
  const today = istDate(now).toISOString().slice(0, 10);
  return Math.max(0, Math.round((Date.parse(today) - Date.parse(inv.due_on)) / 864e5));
}
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const nice = (iso) => { const [y, m, d] = String(iso || "").slice(0, 10).split("-").map(Number); return y ? `${d} ${MONTHS[m - 1]} ${y}` : ""; };
const phoneIN = (p) => { const d = String(p).replace(/\D/g, ""); return /^91\d{10}$/.test(d) ? `+91 ${d.slice(2, 7)} ${d.slice(7)}` : `+${d}`; };
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// Kalpa tokens (Kalpavruksha), copied from 00-hq/design/tokens.css; keep in sync. Printing always uses the light theme.
const TOKENS_LIGHT = "--bg:#F2EEE3;--panel:#FCFAF4;--fg:#1E2A1F;--muted:#5A6152;--rule:#DCD5C3;--soft:#E9E3D3;--accent:#2F6A3A;--accent-fg:#FFFFFF;--madder:#8A4A28;--gold:#C38E12;--ok:#2C7A43;--warn:#A06400;--bad:#B13A2D;--hero:#1D3A25;--hero-fg:#F4EEDC;--hero-mute:#BFCDAE;--l1:#8A4A28";
const TOKENS_DARK = "--bg:#0F1912;--panel:#16231A;--fg:#ECE7D8;--muted:#A8B39B;--rule:#2A3A2D;--soft:#1D2C21;--accent:#8FCB8C;--accent-fg:#0F1912;--madder:#D98B5F;--gold:#E8B64A;--ok:#6FD08F;--warn:#E8B64A;--bad:#F07A6B;--hero:#17301F;--hero-fg:#F4EEDC;--hero-mute:#BFCDAE;--l1:#D98B5F;color-scheme:dark";

/** A complete, printable invoice page (A4). `inv` is an `invoices` row; `seller` comes from env (see functions/billing.js). */
function invoiceHTML(inv, seller, { now = new Date(), sample = false } = {}) {
  const lines = (inv.lines || []).map((l) => ({ desc: l.desc, qty: l.qty || 1, rate: l.rate_paise, amount: Math.round((l.qty || 1) * l.rate_paise) }));
  const total = inv.total_paise;
  const due = inv.status === "due";
  let pay = "";
  if (due && seller.vpa && VPA.test(seller.vpa)) {
    const link = upiLink({ vpa: seller.vpa, name: seller.name, amountPaise: total, number: inv.number });
    pay = `<section class="pay"><div class="qr">${qrSvg(link)}</div><div><p class="eyebrow">Pay by UPI</p>
<p class="big">${money(total)}</p><p>Scan with any UPI app (GPay, PhonePe, Paytm, BHIM).<br>UPI ID: <b class="mono">${esc(seller.vpa)}</b> · ${esc(seller.name)}</p>
<p class="noprint"><a class="btn" href="${esc(link)}">Pay with a UPI app on this phone</a></p>
<p class="muted small">Please write <b class="mono">${esc(inv.number)}</b> in the note if you pay another way.</p></div></section>`;
  } else if (due) pay = `<section class="pay"><div><p class="eyebrow">How to pay</p><p>Please contact us to pay: ${esc(seller.phone || seller.email || "")}. Quote <b class="mono">${esc(inv.number)}</b>.</p></div></section>`;
  const late = overdueDays(inv, now);
  const stamp = sample ? `<p class="stamp late">Sample only: do not pay</p>` : inv.status === "paid" ? `<p class="stamp paid">Paid on ${esc(nice(inv.paid_on))}${inv.paid_ref ? ` · UPI ref ${esc(inv.paid_ref)}` : ""}</p>`
    : inv.status === "void" ? `<p class="stamp void">Cancelled: this invoice is void</p>`
    : late ? `<p class="stamp late">${late} day${late === 1 ? "" : "s"} overdue</p>` : "";
  const rows = lines.map((r, i) => `<tr><td>${i + 1}</td><td>${esc(r.desc)}<small class="each">${esc(r.qty)} × ${money(r.rate)}</small></td><td class="n wide">${esc(r.qty)}</td><td class="n wide">${money(r.rate)}</td><td class="n">${money(r.amount)}</td></tr>`).join("");
  const b = inv.bill_to || {};
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Invoice ${esc(inv.number)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rozha+One&family=Anek+Latin:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
:root{${TOKENS_LIGHT};--f-display:"Rozha One","Noto Serif",Georgia,serif;--f-body:"Anek Latin",ui-sans-serif,system-ui,sans-serif;--f-mono:"JetBrains Mono",ui-monospace,Menlo,monospace;
--temple:radial-gradient(circle at 7px 5px,var(--gold) 2.4px,transparent 2.8px) 0 0/14px 10px,radial-gradient(ellipse 3.2px 2px at 3.5px 5px,var(--leaf,#5E9E4C) 90%,transparent) 0 0/7px 10px}
@media screen and (prefers-color-scheme:dark){:root:not([data-theme="light"]){${TOKENS_DARK}}}
*{box-sizing:border-box}[hidden]{display:none!important}button{font:inherit}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 var(--f-body);padding:16px;-webkit-font-smoothing:antialiased}
.sheet{max-width:794px;margin:0 auto;background:var(--panel);border:1px solid var(--rule);border-radius:18px;overflow:hidden}
.top{position:relative;background:var(--hero);color:var(--hero-fg);padding:26px 22px 24px;display:flex;flex-wrap:wrap;gap:10px 20px;justify-content:space-between;align-items:end}
.top::before,.top::after{content:"";position:absolute;left:0;right:0;height:10px;background:var(--temple)}.top::before{top:0}.top::after{bottom:0;transform:scaleY(-1)}
h1{font:400 34px/1 var(--f-display);margin:0}.eyebrow{font:600 11px var(--f-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--gold);margin:0 0 4px}
.top .meta{font:400 13px/1.6 var(--f-mono);text-align:right}.top .meta b{font-size:15px}
.body{padding:20px 22px 22px;display:flex;flex-direction:column;gap:18px}
.parties{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.parties b{display:block}.muted{color:var(--muted)}.small{font-size:12.5px}.mono{font-family:var(--f-mono)}
.note{margin:0;font-size:12.5px;color:var(--muted)}
.tablewrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}
.each{display:none;color:var(--muted);font:400 12.5px var(--f-mono);margin-top:2px}
@media screen and (max-width:520px){.wide{display:none}.each{display:block}}
th{font:600 11px var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);text-align:left;padding:8px 6px;border-bottom:2px solid var(--fg)}
td{padding:9px 6px;border-bottom:1px solid var(--rule);vertical-align:top}.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.total td{font-weight:700;font-size:16px;border-bottom:0;border-top:2px solid var(--fg)}
.words{margin:0;font-weight:600}
.pay{display:flex;flex-wrap:wrap;gap:16px;align-items:center;border:1px solid var(--rule);border-radius:12px;padding:14px;background:color-mix(in srgb,var(--gold) 7%,var(--panel))}
.pay p{margin:0 0 4px}.big{font:400 28px/1.1 var(--f-display)}
.qr{width:170px;height:170px;background:#fff;border-radius:8px;padding:4px;flex:none}.qr svg{width:100%;height:100%;display:block}
.btn{display:inline-flex;align-items:center;min-height:44px;border-radius:999px;padding:8px 18px;background:var(--accent);color:var(--accent-fg);font-weight:600;text-decoration:none;border:0;cursor:pointer;font-size:15px}
.btn.ghost{background:transparent;color:var(--fg);border:1px solid var(--rule)}
.stamp{margin:0;align-self:flex-start;border:2px solid;border-radius:999px;padding:4px 14px;font:600 13px var(--f-mono);letter-spacing:.06em;text-transform:uppercase}
.stamp.paid{color:var(--ok)}.stamp.void{color:var(--muted)}.stamp.late{color:var(--bad)}
.actions{display:flex;gap:8px;flex-wrap:wrap}
footer{padding:0 22px 20px;font-size:12.5px;color:var(--muted)}
:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
@media print{@page{size:A4;margin:12mm}body{background:#fff;padding:0}.sheet{border:0;border-radius:0;max-width:none}.noprint{display:none!important}
.top,.top *{-webkit-print-color-adjust:exact;print-color-adjust:exact}.pay{break-inside:avoid}}
</style></head><body><main class="sheet">
<header class="top"><div><p class="eyebrow">${esc(seller.name)}</p><h1>Invoice</h1></div>
<div class="meta"><b>${esc(inv.number)}</b><br>Date ${esc(nice(inv.issued_on))}${inv.due_on ? `<br>Due ${esc(nice(inv.due_on))}` : ""}${inv.period ? `<br>For ${esc(inv.period)}` : ""}</div></header>
<div class="body">${stamp}
<div class="parties"><div><p class="eyebrow">From</p><b>${esc(seller.name)}</b>${esc(seller.address)}<br>${esc(seller.phone || "")}${seller.email ? `<br>${esc(seller.email)}` : ""}<br><span class="mono small">Udyam ${esc(seller.udyam)}</span></div>
<div><p class="eyebrow">Bill to</p><b>${esc(b.name)}</b>${esc(b.address || "")}${b.phone ? `<br>${esc(phoneIN(b.phone))}` : ""}</div></div>
<p class="note">Supplier not registered under GST; no GST charged.</p>
<div class="tablewrap"><table><thead><tr><th>#</th><th>Description</th><th class="n wide">Qty</th><th class="n wide">Rate</th><th class="n">Amount</th></tr></thead>
<tbody>${rows}<tr class="total"><td colspan="2">Total</td><td class="wide" colspan="2"></td><td class="n">${money(total)}</td></tr></tbody></table></div>
<p class="words">${esc(wordsFor(total))}</p>
${pay}
<div class="actions noprint"><button class="btn ghost" type="button" onclick="window.print()">Save as PDF / Print</button></div>
</div><footer>Thank you for choosing BotBhai. This is a computer-generated invoice and needs no signature.</footer></main></body></html>`;
}

module.exports = { fyOf, invoiceNo, computeBill, inWords, wordsFor, money, upiLink, qrSvg, overdueDays, invoiceHTML, nice, esc, VPA };

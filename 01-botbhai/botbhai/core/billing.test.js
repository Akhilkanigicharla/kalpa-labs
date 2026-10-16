// Unit tests for BotBhai billing (A05 / P1-W2-06). Run: node core/billing.test.js
const assert = require("assert");
const B = require("./billing.js");
const { encode } = require("./vendor/uqr/index.cjs");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓ " + name); };

(async () => {
  ok("FY series KL/26-27/001, ≤ 16 characters, new series on 1 April IST", () => {
    assert.strictEqual(B.invoiceNo(1, new Date("2026-10-16T06:00:00Z")), "KL/26-27/001");
    assert.strictEqual(B.invoiceNo(42, new Date("2027-03-31T18:00:00Z")), "KL/26-27/042"); // 11:30 PM IST, 31 Mar
    assert.strictEqual(B.invoiceNo(1, new Date("2027-03-31T18:31:00Z")), "KL/27-28/001");  // 12:01 AM IST, 1 Apr
    assert.strictEqual(B.invoiceNo(1234, new Date("2026-10-16T06:00:00Z")), "KL/26-27/1234");
    assert.strictEqual(B.fyOf(new Date("2027-01-05T00:00:00Z")), "26-27");
    assert.throws(() => B.invoiceNo(0), /sequence/);
  });

  ok("totals in paise, no GST anywhere", () => {
    const t = B.computeBill([{ desc: "BotBhai Founding setup", rate: 2999 }, { desc: "Monthly plan · Nov 2026", rate: 1499.5, qty: 2 }]);
    assert.strictEqual(t.total, 299900 + 299900); assert.strictEqual(t.rows[1].amount, 299900);
    assert.ok(!("gst" in t) && !("cgst" in t));
    assert.throws(() => B.computeBill([]), /at least one/);
    assert.throws(() => B.computeBill([{ desc: "x", rate: -5 }]), /bad line/);
    assert.throws(() => B.computeBill([{ desc: "", rate: 5 }]), /bad line/);
    assert.throws(() => B.computeBill([{ desc: "x", rate: 1e9 }]), /too large/);
    assert.throws(() => B.computeBill([{ desc: "x", rate: "abc" }]), /bad line/);
  });

  ok("amount in words, Indian system", () => {
    assert.strictEqual(B.inWords(2999), "Two Thousand Nine Hundred Ninety Nine");
    assert.strictEqual(B.inWords(1234567), "Twelve Lakh Thirty Four Thousand Five Hundred Sixty Seven");
    assert.strictEqual(B.inWords(0), "Zero");
  });

  // Same maths as JobCard's tested ESM module: guard the two copies against drift.
  const J = await import("../../../02-jobcard/lib/invoice.mjs");
  ok("matches 02-jobcard/lib/invoice.mjs on 3,000 random amounts", () => {
    for (let i = 0; i < 3000; i++) { const r = Math.floor(Math.random() ** 3 * 9.99e8); assert.strictEqual(B.inWords(r), J.inWords(r), String(r)); }
  });

  ok("UPI link: NPCI fields, fixed amount, unique tr, %20 spaces", () => {
    const l = B.upiLink({ vpa: "kalpalabs@ybl", name: "Kalpa Labs", amountPaise: 149900, number: "KL/26-27/007" });
    const q = new URL(l.replace("upi://pay", "https://x/pay")).searchParams;
    assert.ok(l.startsWith("upi://pay?")); assert.ok(!l.includes("+"));
    assert.strictEqual(q.get("pa"), "kalpalabs@ybl"); assert.strictEqual(q.get("pn"), "Kalpa Labs"); assert.strictEqual(q.get("am"), "1499.00");
    assert.strictEqual(q.get("cu"), "INR"); assert.strictEqual(q.get("tr"), "KL2627007"); assert.strictEqual(q.get("tn"), "Invoice KL/26-27/007");
    assert.ok(!q.has("mam"), "no mam → payer can't edit the amount");
    assert.throws(() => B.upiLink({ vpa: "not a vpa", name: "K", amountPaise: 100, number: "KL/26-27/001" }), /UPI ID/);
    assert.throws(() => B.upiLink({ vpa: "a@ybl&am=1", name: "K", amountPaise: 100, number: "KL/26-27/001" }), /UPI ID/);
    assert.throws(() => B.upiLink({ vpa: "kalpa@ybl", name: "K", amountPaise: 0, number: "KL/26-27/001" }), /amount/);
  });

  ok("QR SVG encodes exactly the UPI link", () => {
    const l = B.upiLink({ vpa: "kalpalabs@ybl", name: "Kalpa Labs", amountPaise: 299900, number: "KL/26-27/001" });
    const svg = B.qrSvg(l);
    assert.match(svg, /^<svg[^>]+viewBox/); assert.ok(svg.length < 30000);
    // rebuild the module grid from the SVG path and compare with the encoder (the encoder itself is proven
    // against an independent decoder in research/billing-scan.md; tools/test_billing_ui.py scans the real page with OpenCV)
    const { data, size } = encode(l, { ecc: "M", border: 0 });
    const dark = new Set([...svg.matchAll(/M(\d+),(\d+)h1v1h-1z/g)].map((m) => `${m[1] - 4},${m[2] - 4}`));
    let same = 0; for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) if (data[y][x] === dark.has(`${x},${y}`)) same++;
    assert.strictEqual(same, size * size, "SVG modules differ from the encoded QR");
  });

  const seller = { name: "Kalpa Labs", address: "Hyderabad, Telangana", phone: "+91 90000 00000", udyam: "UDYAM-TS-02-0382711", vpa: "kalpalabs@ybl" };
  const inv = { number: "KL/26-27/001", issued_on: "2026-10-16", due_on: "2026-10-23", period: "Oct 2026", status: "due",
    bill_to: { name: "Glow <Studio>", address: "Ameerpet, Hyderabad", phone: "919000000000" },
    lines: [{ desc: "BotBhai Founding setup", qty: 1, rate_paise: 299900 }], total_paise: 299900 };

  ok("invoice HTML: 'Invoice', Udyam, no GST, words, QR + UPI ID, escaped", () => {
    const h = B.invoiceHTML(inv, seller);
    assert.match(h, /<title>Invoice KL\/26-27\/001<\/title>/); assert.match(h, />Invoice</);
    assert.doesNotMatch(h, /Tax Invoice|GSTIN|CGST|SGST|IGST|Bill of Supply/);
    assert.match(h, /Supplier not registered under GST; no GST charged/);
    assert.match(h, /UDYAM-TS-02-0382711/); assert.match(h, /Two Thousand Nine Hundred Ninety Nine/);
    assert.match(h, /₹2,999\.00/); assert.match(h, /16 Oct 2026/); assert.match(h, /Due 23 Oct 2026/);
    assert.match(h, /<svg/); assert.match(h, /kalpalabs@ybl/); assert.match(h, /href="upi:\/\/pay\?/);
    assert.match(h, /\+91 90000 00000/);
    assert.match(h, /Glow &lt;Studio&gt;/); assert.doesNotMatch(h, /Glow <Studio>/);
    assert.match(h, /--hero:#1C2463/i);
  });

  ok("paid and void invoices: stamp, no pay button or QR", () => {
    const p = B.invoiceHTML(Object.assign({}, inv, { status: "paid", paid_on: "2026-10-18", paid_ref: "629812345678" }), seller);
    assert.match(p, /class="stamp paid"/); assert.match(p, /Paid on 18 Oct 2026/); assert.doesNotMatch(p, /upi:\/\/pay/); assert.doesNotMatch(p, /<svg/);
    const v = B.invoiceHTML(Object.assign({}, inv, { status: "void" }), seller);
    assert.match(v, /class="stamp void"/); assert.doesNotMatch(v, /upi:\/\/pay/);
  });

  ok("no UPI ID configured: invoice still renders, asks to pay by bank transfer/contact", () => {
    const h = B.invoiceHTML(inv, Object.assign({}, seller, { vpa: "" }));
    assert.doesNotMatch(h, /upi:\/\/pay/); assert.match(h, /contact us to pay/i);
  });

  ok("overdue days in IST", () => {
    assert.strictEqual(B.overdueDays({ status: "due", due_on: "2026-10-20" }, new Date("2026-10-23T05:00:00Z")), 3);
    assert.strictEqual(B.overdueDays({ status: "due", due_on: "2026-10-20" }, new Date("2026-10-20T17:00:00Z")), 0);
    assert.strictEqual(B.overdueDays({ status: "paid", due_on: "2026-10-01" }, new Date("2026-10-23T05:00:00Z")), 0);
  });

  console.log(`\nbilling tests passed (${n})`);
})().catch((e) => { console.error(e); process.exit(1); });

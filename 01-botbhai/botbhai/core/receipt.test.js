// A121 GST-ready receipt tests. Run: node core/receipt.test.js
const assert = require("assert");
const R = require("./receipt.js");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };
const shop = { business: "Glow Studio", address: "Road No. 36, Jubilee Hills, Hyderabad" };
const D = new Date("2026-10-25T10:00:00Z");
console.log("Receipt tests");
ok("money: ₹ strings to paise, Indian format back", () => {
  assert.strictEqual(R.priceToPaise("₹1,200"), 120000); assert.strictEqual(R.priceToPaise("from ₹15,000"), 1500000);
  assert.strictEqual(R.priceToPaise("ask us"), null); assert.strictEqual(R.rupees(123456789), "₹12,34,567.89");
});
ok("serial: ≤16 characters, financial year Apr–Mar, consecutive", () => {
  assert.strictEqual(R.serialFor("gs", 42, D), "GS/2627/0042"); assert.strictEqual(R.fyOf(new Date("2027-03-31T00:00:00Z")), "2627");
  assert.strictEqual(R.fyOf(new Date("2027-04-01T00:00:00Z")), "2728"); assert.ok(R.serialFor("ABCDEFG", 99999, D).length <= 16);
});
ok("tax inside the menu price: ₹1,180 at 18% → taxable ₹1,000 + CGST ₹90 + SGST ₹90", () => {
  const t = R.taxLines(118000, 18, true);
  assert.deepStrictEqual([t.taxable, t.lines[0].amount, t.lines[1].amount, t.total], [100000, 9000, 9000, 118000]);
  assert.deepStrictEqual(t.lines.map((l) => l.name), ["CGST 9%", "SGST 9%"]);
  const odd = R.taxLines(25000, 18, true); assert.strictEqual(odd.taxable + odd.lines[0].amount + odd.lines[1].amount, 25000); // paise never lost
  assert.strictEqual(R.taxLines(100000, 18, false, true).lines[0].name, "IGST 18%");
});
ok("not registered: plain Receipt, no GSTIN, no tax, honest note", () => {
  const r = R.makeReceipt(shop, { customer: "Sravani", items: [{ name: "Hair spa", price: "₹1,200" }] }, { n: 1, date: D });
  assert.strictEqual(r.title, "Receipt"); assert.strictEqual(r.supplier.gstin, null); assert.strictEqual(r.tax, null);
  assert.strictEqual(r.total, 120000); assert.match(R.receiptText(r), /Not registered under GST/);
});
ok("composition: Bill of Supply with the required line and GSTIN", () => {
  const r = R.makeReceipt({ ...shop, gst: { mode: "composition", gstin: "36ABCDE1234F1Z5", prefix: "GS" } }, { customer: "Ravi", items: [{ name: "Haircut (men)", price: "₹250", qty: 2 }], discount: 50 }, { n: 7, date: D });
  assert.strictEqual(r.title, "Bill of Supply"); assert.strictEqual(r.total, 45000); assert.match(r.note, /not eligible to collect tax/);
  const t = R.receiptText(r); assert.match(t, /GSTIN 36ABCDE1234F1Z5/); assert.match(t, /Haircut \(men\) × 2: ₹500\.00/); assert.match(t, /Discount: −₹50\.00/);
});
ok("regular: Tax Invoice with SAC, rate split and every Rule 46 field present", () => {
  const r = R.makeReceipt({ ...shop, gst: { mode: "regular", gstin: "36ABCDE1234F1Z5", sac: "999721", rate: 18, state: "Telangana" } }, { customer: "Anil", items: [{ name: "Facial", amount: 1180 }] }, { n: 3, date: D });
  for (const k of ["serial", "date", "supplier", "customer", "items", "taxable", "tax", "total", "sac"]) assert.ok(r[k] != null, `missing ${k}`);
  assert.strictEqual(r.place_of_supply, "Telangana"); assert.match(R.receiptText(r), /CGST 9%: ₹90\.00/);
});
ok("refuses incomplete GST settings with a plain reason", () => {
  assert.throws(() => R.makeReceipt({ ...shop, gst: { mode: "regular", gstin: "BAD" } }, { items: [{ name: "x", amount: 1 }] }, { n: 1, date: D }), /GSTIN/);
  assert.throws(() => R.makeReceipt({ ...shop, gst: { mode: "regular", gstin: "36ABCDE1234F1Z5" } }, { items: [{ name: "x", amount: 1 }] }, { n: 1, date: D }), /SAC/);
  assert.throws(() => R.makeReceipt(shop, { items: [{ name: "Bridal", price: "ask" }] }, { n: 1, date: D }), /no price/);
});
ok("HTML escapes names (no injection) and shows the total", () => {
  const r = R.makeReceipt(shop, { customer: "<script>x</script>", items: [{ name: "Hair spa", price: "₹1,200" }] }, { n: 1, date: D });
  const h = R.receiptHtml(r); assert.ok(!h.includes("<script>x")); assert.match(h, /Total paid<\/td><td class="n">₹1,200\.00/);
});
console.log(`${n} receipt tests passed`);

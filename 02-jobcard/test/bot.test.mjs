// A35 (b2.q09): the JobCard WhatsApp webhook, driven end to end against fakes. Run: npm test
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { installFake, sign } from "./fake.mjs";

const TECH = { id: "t1", name: "Ravi", phone: "9000022222", business_name: "Ravi Cooling Services", address: "SR Nagar, Hyderabad", gst_kind: "unregistered", state: "Telangana", language: "te", plan: "free", upi_vpa: "ravi@okaxis" };
const fx = installFake({ technicians: [{ ...TECH }] });
const { handler, cardText, mergeCard } = await import("../bot/functions/jobcard.js");
const notes = JSON.parse(fs.readFileSync(new URL("./fixtures/notes.json", import.meta.url)));
let mid = 0;
const inbound = (msg, from = "919000022222") => {
  const body = JSON.stringify({ entry: [{ changes: [{ value: { metadata: { phone_number_id: "PNID" }, messages: [{ from, id: "wamid." + (++mid), ...msg }] } }] }] });
  return handler({ httpMethod: "POST", headers: { "x-hub-signature-256": sign(body) }, body });
};
const text = (b) => ({ type: "text", text: { body: b } });
const okBtn = { type: "interactive", interactive: { type: "button_reply", button_reply: { id: "jc:ok", title: "✅" } } };
const last = () => fx.sent[fx.sent.length - 1];

test("Meta verification and forged signatures", async () => {
  assert.equal((await handler({ httpMethod: "GET", queryStringParameters: { "hub.mode": "subscribe", "hub.verify_token": "verify", "hub.challenge": "42" } })).body, "42");
  assert.equal((await handler({ httpMethod: "GET", queryStringParameters: { "hub.mode": "subscribe", "hub.verify_token": "nope" } })).statusCode, 403);
  assert.equal((await handler({ httpMethod: "POST", headers: { "x-hub-signature-256": "sha256=00" }, body: "{}" })).statusCode, 401);
  assert.equal((await handler({ httpMethod: "PUT" })).statusCode, 405);
});

test("voice note → card with ✅ / edit buttons; voice seconds metered", async () => {
  fx.nextVoice = { text: notes[0].note, seconds: 34 };
  await inbound({ type: "audio", audio: { id: "AUDIO1" } });
  const m = last(); assert.equal(m.type, "interactive"); assert.equal(m.to, "919000022222");
  assert.match(m.interactive.body.text, /Gas refill: ₹2,500/); assert.match(m.interactive.body.text, /Total: ₹2,950/);
  assert.deepEqual(m.interactive.action.buttons.map((b) => b.reply.id), ["jc:ok", "jc:edit"]);
  assert.match(m.interactive.action.buttons[0].reply.title, /సరైనది/); // Telugu technician
  assert.equal(fx.lastTranscribe.lang, "te-IN");
  assert.equal(fx.store.usage_minutes[0].seconds, 34);
  assert.equal(fx.store.invoices.length, 0, "nothing billed before ✅");
});

test("✅ saves customer, job card, FY invoice and sends the PDF to the technician only", async () => {
  await inbound(okBtn);
  assert.equal(fx.store.invoices.length, 1); const inv = fx.store.invoices[0];
  assert.match(inv.number, /^JC\/\d\d-\d\d\/0001$/); assert.equal(inv.payable_paise, 295000); assert.equal(inv.kind, "unregistered");
  assert.equal(fx.store.customers[0].phone, "9000033333"); assert.equal(fx.store.job_cards[0].customer_id, fx.store.customers[0].id);
  const doc = last(); assert.equal(doc.type, "document"); assert.equal(doc.to, "919000022222"); assert.match(doc.document.filename, /^JC-\d\d-\d\d-0001\.pdf$/);
  assert.ok(fx.sent.every((m) => m.to === "919000022222"), "never messages the customer");
  const pdf = fx.media[0]; assert.equal(pdf.type, "application/pdf");
  const f = path.join(os.tmpdir(), `jc-${process.pid}.pdf`); fs.writeFileSync(f, pdf.bytes);
  const txt = execFileSync("pdftotext", ["-layout", f, "-"]).toString(); fs.unlinkSync(f);
  assert.match(txt, /Bill of Supply/); assert.match(txt, /Sita/); assert.match(txt, /2,950\.00/); assert.match(txt, /Ravi Cooling Services/);
  assert.equal(fx.store.bot_sessions[0].pending, null, "card cleared after saving");
});

test("Meta retry of the same message is handled once", async () => {
  const body = JSON.stringify({ entry: [{ changes: [{ value: { metadata: { phone_number_id: "PNID" }, messages: [{ from: "919000022222", id: "wamid.dup", ...text("gas refill 900") }] } }] }] });
  const ev = { httpMethod: "POST", headers: { "x-hub-signature-256": sign(body) }, body };
  const before = fx.sent.length; await handler(ev); await handler(ev);
  assert.equal(fx.sent.length, before + 1);
});

test("edit merges the correction; unpriced parts block the bill", async () => {
  fx.store.bot_sessions[0].pending = null;
  await inbound(text("split AC capacitor, gas refill 2500, customer Sita 9000033333"));
  assert.match(last().interactive.body.text, /Capacitor: \?/);
  await inbound(okBtn); assert.match(last().text.body, /Capacitor/); assert.equal(fx.store.invoices.length, 1, "not billed with a missing price");
  await inbound({ type: "interactive", interactive: { button_reply: { id: "jc:edit" } } }); assert.match(last().text.body, /capacitor 450/);
  await inbound(text("capacitor 450"));
  assert.match(last().interactive.body.text, /Capacitor: ₹450/); assert.match(last().interactive.body.text, /Total: ₹2,950/);
  await inbound(text("ok")); assert.equal(fx.store.invoices.length, 2); assert.match(fx.store.invoices[1].number, /0002$/);
  assert.equal(fx.store.customers.length, 1, "same phone → same customer");
});

test("20 test notes: 0 wrong totals (bill = sum of items, never the spoken total)", async () => {
  const start = fx.store.invoices.length;
  for (const n of notes) { await inbound(text(n.note)); await inbound(okBtn); }
  const made = fx.store.invoices.slice(start);
  assert.equal(made.length, 20);
  made.forEach((inv, i) => assert.equal(inv.payable_paise, notes[i].payable * 100, notes[i].note));
  assert.ok(fx.sent.some((m) => m.type === "interactive" && /You said ₹3,000; the items add up to ₹2,950/.test(m.interactive.body.text)), "spoken-total mismatch is flagged");
});

test("unknown number, no amounts, deaf STT, long note, Telugu name", async () => {
  await inbound(text("gas refill 2500"), "919999999999"); assert.match(last().text.body, /isn't registered/); assert.equal(last().to, "919999999999");
  await inbound(text("customer Naveen 9100011111 general service")); assert.match(last().text.body, /ధర|పని/);
  fx.transcribeDown = true; await inbound({ type: "audio", audio: { id: "A2" } }); assert.match(last().text.body, /వినిపించలేదు/); fx.transcribeDown = false;
  fx.nextVoice = { text: "gas refill 2500", seconds: 200 }; await inbound({ type: "audio", audio: { id: "A3" } }); assert.match(last().text.body, /2 నిమిషాల/);
  fx.store.bot_sessions[0].pending = null;
  await inbound(text("పేరు సీత, gas refill 2500")); const n = fx.store.invoices.length;
  fx.store.bot_sessions[0].pending.customer.name = "సీత"; // Telugu name → pdf-lib can't shape it
  await inbound(okBtn); assert.equal(fx.store.invoices.length, n + 1); assert.match(last().text.body, /యాప్/);
  await inbound(text("ok")); assert.match(last().text.body, /పెండింగ్/);
  await inbound({ type: "reaction", reaction: { emoji: "👍" } }); assert.match(last().text.body, /పెండింగ్/, "reactions ignored");
});

test("cardText and mergeCard are pure", () => {
  const a = { customer: { name: "Sita" }, appliance: "split_ac", parts: [{ desc: "Gas refill", qty: 1, rate: 2500 }], issues: [] };
  const b = mergeCard(a, { customer: { phone: "9000033333" }, parts: [{ desc: "Gas refill", qty: 1, rate: 2600 }], issues: ["gas_leak"] });
  assert.equal(a.parts[0].rate, 2500); assert.equal(b.parts[0].rate, 2600); assert.equal(b.customer.name, "Sita"); assert.equal(b.customer.phone, "9000033333");
  assert.match(cardText(b, "en"), /Split AC/);
});

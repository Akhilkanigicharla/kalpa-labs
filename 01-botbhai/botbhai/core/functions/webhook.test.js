// Simulates Meta + Supabase with an in-memory fake, then drives the real webhook handler.
// Run: node 01-botbhai/botforge/netlify/functions/webhook.test.js
const assert = require("assert");
const crypto = require("crypto");
process.env.NO_DELAY = "1";
process.env.SITE_URL = "https://botbhai.example"; const { store, graph } = require("./_fake.js")({ clients: [{ id: "c1", name: "Glow Studio", niche: "salon", phone_number_id: "PNID", owner_whatsapp: "919000000000", active: true, config: { capacity: 1 }, dashboard_token: "a".repeat(36) }] });
const sent = { get list() { return graph.sent.filter((m) => m.type); } };
const { handler } = require("./whatsapp.js");
const sign = (b) => "sha256=" + crypto.createHmac("sha256", "appsecret").update(b).digest("hex");
let mid = 0;
const inbound = (msg, from = "919812345678") => {
  const body = JSON.stringify({ entry: [{ changes: [{ value: { metadata: { phone_number_id: "PNID" }, contacts: [{ profile: { name: "Ravi" } }], messages: [Object.assign({ from, id: "wamid." + (++mid) }, msg)] } }] }] });
  return handler({ httpMethod: "POST", headers: { "x-hub-signature-256": sign(body) }, body });
};

(async () => {
  const v = await handler({ httpMethod: "GET", queryStringParameters: { "hub.mode": "subscribe", "hub.verify_token": "verify", "hub.challenge": "42" } });
  assert.strictEqual(v.body, "42"); console.log("  ✓ webhook verification");
  const bad = await handler({ httpMethod: "POST", headers: { "x-hub-signature-256": "sha256=00" }, body: "{}" });
  assert.strictEqual(bad.statusCode, 401); console.log("  ✓ rejects forged signature");

  await inbound({ type: "text", text: { body: "hi" } });
  assert.strictEqual(sent.list[0].interactive.type, "list"); assert.match(sent.list[0].interactive.body.text, /I'm Meera/); console.log("  ✓ menu sent as WhatsApp list, persona introduced");
  assert.ok(graph.sent.some((m) => m.status === "read" && m.typing_indicator)); console.log("  ✓ blue ticks + typing indicator sent");
  await inbound({ type: "interactive", interactive: { list_reply: { id: "t:Book a service", title: "Book a service" } } });
  await inbound({ type: "interactive", interactive: { list_reply: { id: "t:Hair spa", title: "Hair spa" } } });
  await inbound({ type: "text", text: { body: "tomorrow" } });
  await inbound({ type: "interactive", interactive: { list_reply: { id: "t:7:00 PM", title: "7:00 PM" } } });
  await inbound({ type: "text", text: { body: "Ravi Teja" } });
  const confirm = sent.list.find((m) => m.type === "text" && /Booking confirmed/.test(m.text.body));
  assert.ok(confirm && /7:00 PM/.test(confirm.text.body)); console.log("  ✓ full booking over WhatsApp");
  assert.ok(sent.list.some((m) => m.to === "919000000000" && m.text && /New appointment: Ravi Teja/.test(m.text.body)), JSON.stringify(sent.list.filter((m) => m.to === "919000000000"))); console.log("  ✓ owner alerted on WhatsApp");
  const lead = store.leads[0];
  assert.strictEqual(store.leads.length, 1); assert.strictEqual(lead.score, "hot"); assert.strictEqual(lead.details.service, "Hair spa");
  console.log("  ✓ lead saved:", JSON.stringify({ name: lead.name, score: lead.score, status: lead.status, ...lead.details }));
  assert.ok(store.messages.length >= 12); console.log(`  ✓ ${store.messages.length} messages logged`);

  assert.ok(sent.list.some((m) => m.type === "image" && /salon-booking_confirmed\.png$/.test(m.image.link))); console.log("  ✓ smile card sent with the booking");
  assert.strictEqual(store.bookings.length, 1); assert.strictEqual(store.bookings[0].slot, "7:00 PM"); console.log("  ✓ booking written to the calendar");
  // a second customer asking for the same day must not see 7:00 PM (capacity 1)
  await inbound({ type: "text", text: { body: "book" } }, "919800000002");
  await inbound({ type: "interactive", interactive: { list_reply: { id: "t:Hair spa" } } }, "919800000002");
  await inbound({ type: "text", text: { body: "tomorrow" } }, "919800000002");
  const slotsMsg = sent.list.filter((m) => m.to === "919800000002").pop();
  const titles = slotsMsg.interactive.action.sections ? slotsMsg.interactive.action.sections[0].rows.map((r) => r.title) : slotsMsg.interactive.action.buttons.map((b) => b.reply.title);
  assert.ok(!titles.includes("7:00 PM") && titles.length === 3, titles.join(",")); console.log("  ✓ taken slot hidden from the next customer:", titles.join(", "));
  // first customer comes back: greeted by name
  await inbound({ type: "text", text: { body: "hi" } });
  assert.match(sent.list.filter((m) => m.to === "919812345678").pop().interactive.body.text, /Welcome back, Ravi! 😊 Same \*Hair spa\*/); console.log("  ✓ returning customer recognised");
  const { handler: leadsApi } = require("./leads.js");
  const r = await leadsApi({ headers: { authorization: "Bearer " + "a".repeat(36) } });
  assert.strictEqual(JSON.parse(r.body).leads.length, 2); console.log("  ✓ dashboard API returns the lead");
  const r2 = await leadsApi({ headers: { authorization: "Bearer " + "b".repeat(36) } });
  assert.strictEqual(r2.statusCode, 401); console.log("  ✓ dashboard API rejects wrong token");
  console.log("\nwebhook tests passed");
})().catch((e) => { console.error(e); process.exit(1); });

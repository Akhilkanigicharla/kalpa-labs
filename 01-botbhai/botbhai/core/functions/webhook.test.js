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
  // A10: the owner dashboard's "Today" view needs the calendar, plus how many chats wait for a person
  const dash = JSON.parse(r.body);
  assert.ok(Array.isArray(dash.bookings) && dash.bookings.length === 1, JSON.stringify(dash.bookings));
  assert.deepStrictEqual(Object.keys(dash.bookings[0]).sort(), ["confirmed_at", "contact", "date_iso", "name", "service", "slot", "status"]);
  assert.strictEqual(dash.bookings[0].slot, "7:00 PM"); assert.strictEqual(dash.waiting, 0); assert.match(dash.today, /^\d{4}-\d{2}-\d{2}$/);
  store.bookings.push({ id: "old", client_id: "c1", contact: "919811110000", name: "Old", service: "Facial", date_iso: "2020-01-01", slot: "11:00 AM", status: "completed" });
  store.bookings.push({ id: "other", client_id: "c2", contact: "919811110001", name: "Other salon", service: "Facial", date_iso: dash.today, slot: "11:00 AM", status: "confirmed" });
  const dash2 = JSON.parse((await leadsApi({ headers: { authorization: "Bearer " + "a".repeat(36) } })).body);
  assert.ok(!dash2.bookings.some((b) => b.name === "Old" || b.name === "Other salon"), "only this salon's last 30 days → next 14 days");
  console.log("  ✓ dashboard API adds this salon's bookings (last 30 → next 14 days) and the waiting-chat count");

  // ---------- A04 / P1-W2-02: shared inbox phase 1 (paused chats, reply as the salon, resume bot)
  const { handler: inboxApi } = require("./inbox.js");
  const TOKEN = "a".repeat(36); const C = "919812345678";
  const api = (method, body, query, token = TOKEN) => inboxApi({ httpMethod: method, headers: { authorization: "Bearer " + token }, queryStringParameters: query || {}, body: body ? JSON.stringify(body) : undefined })
    .then((res) => Object.assign(res, { data: JSON.parse(res.body) }));
  const sess = (c) => store.sessions.find((s) => s.contact === c);
  const toCustomer = () => sent.list.filter((m) => m.to === C).length;

  assert.strictEqual((await api("GET", null, {}, "b".repeat(36))).statusCode, 401); console.log("  ✓ inbox rejects a wrong token");
  assert.strictEqual(sess(C).status, "bot"); assert.ok(sess(C).last_inbound_at); console.log("  ✓ session row carries status=bot and last_inbound_at");
  assert.ok(store.messages.some((m) => m.direction === "in" && m.author === "customer") && store.messages.some((m) => m.direction === "out" && m.author === "bot")); console.log("  ✓ messages logged with author customer/bot");

  // T25-style: customer asks for a person → paused, shown in the inbox as "human", owner alert points to the inbox
  await inbound({ type: "text", text: { body: "talk to owner" } });
  assert.strictEqual(sess(C).status, "human"); assert.ok(new Date(sess(C).human_until) > new Date()); console.log("  ✓ handoff marks the chat human with human_until");
  const alert = sent.list.filter((m) => m.to === "919000000000" && m.text).pop();
  assert.match(alert.text.body, /botbhai\.example\/inbox\.html/); assert.doesNotMatch(alert.text.body, /WhatsApp Business app/); console.log("  ✓ owner alert links the inbox");
  let list = await api("GET");
  assert.strictEqual(list.statusCode, 200); assert.ok(!("access-control-allow-origin" in Object.keys(list.headers).reduce((o, k) => (o[k.toLowerCase()] = 1, o), {})));
  const row = list.data.conversations.find((c) => c.contact === C);
  assert.strictEqual(row.status, "human"); assert.strictEqual(row.name, "Ravi Teja"); assert.strictEqual(row.window_open, true);
  assert.ok(!list.data.conversations.some((c) => c.contact === "919000000000")); assert.strictEqual(list.data.conversations[0].contact, C);
  console.log("  ✓ inbox lists conversations, paused one first, owner's own chat hidden");
  // while paused the bot stays silent
  let before = toCustomer(); await inbound({ type: "text", text: { body: "hello? anyone there" } });
  assert.strictEqual(toCustomer(), before); console.log("  ✓ paused chat: bot stays silent");
  const thread = await api("GET", null, { contact: C });
  assert.strictEqual(thread.data.messages[thread.data.messages.length - 1].body, "hello? anyone there"); assert.ok(thread.data.messages.length >= 10); console.log("  ✓ thread returns the conversation, oldest first");

  // staff reply goes out from the salon number and is logged author=staff
  const rep = await api("POST", { action: "reply", contact: C, text: "Hi Ravi, Lakshmi here from Glow Studio. How can I help?" });
  assert.strictEqual(rep.statusCode, 200, rep.body);
  const out = sent.list.filter((m) => m.to === C).pop(); assert.strictEqual(out.type, "text"); assert.match(out.text.body, /Lakshmi here/);
  assert.ok(store.messages.some((m) => m.author === "staff" && m.direction === "out" && /Lakshmi/.test(m.body))); console.log("  ✓ staff reply sent via Graph API and logged author=staff");
  assert.strictEqual((await api("POST", { action: "reply", contact: C, text: "   " })).statusCode, 400); console.log("  ✓ empty reply refused");

  // assign + notes
  assert.strictEqual((await api("POST", { action: "assign", contact: C, assigned_to: "Lakshmi" })).statusCode, 200);
  assert.strictEqual((await api("POST", { action: "note", contact: C, notes: "Wants a refund talk; call after 6" })).statusCode, 200);
  assert.strictEqual(sess(C).assigned_to, "Lakshmi"); assert.match(sess(C).notes, /refund/); console.log("  ✓ assigned_to and notes saved");
  await inbound({ type: "text", text: { body: "ok thanks" } });
  assert.strictEqual(sess(C).assigned_to, "Lakshmi"); console.log("  ✓ a new customer message keeps assignment + notes");

  // resume bot → the next message gets a bot reply again
  assert.strictEqual((await api("POST", { action: "resume", contact: C })).statusCode, 200);
  assert.strictEqual(sess(C).status, "bot"); assert.ok(!sess(C).state.humanUntil);
  before = toCustomer(); await inbound({ type: "text", text: { body: "hi there" } });
  assert.ok(toCustomer() > before); console.log("  ✓ resume bot: replies again");

  // take over by hand, then resolve
  assert.strictEqual((await api("POST", { action: "take_over", contact: C })).statusCode, 200);
  assert.strictEqual(sess(C).status, "human"); before = toCustomer(); await inbound({ type: "text", text: { body: "hi" } }); assert.strictEqual(toCustomer(), before);
  assert.strictEqual((await api("POST", { action: "resolve", contact: C })).statusCode, 200);
  assert.strictEqual(sess(C).status, "resolved"); assert.ok(!sess(C).state.humanUntil); console.log("  ✓ take over pauses; resolve hands back to the bot");

  // WhatsApp rules: no free-form reply after 24 h, never to opted-out people, never to web visitors
  sess(C).last_inbound_at = new Date(Date.now() - 25 * 3.6e6).toISOString();
  const late = await api("POST", { action: "reply", contact: C, text: "hello again" });
  assert.strictEqual(late.statusCode, 409); assert.strictEqual(late.data.error, "outside_24h"); console.log("  ✓ reply refused outside the 24-hour window");
  await inbound({ type: "text", text: { body: "STOP" } }, "919800000002");
  const stopped = await api("POST", { action: "reply", contact: "919800000002", text: "please come back" });
  assert.strictEqual(stopped.statusCode, 409); assert.strictEqual(stopped.data.error, "opted_out"); console.log("  ✓ reply refused to an opted-out customer");
  store.sessions.push({ client_id: "c1", contact: "web:visitor123", state: { step: -1 }, status: "bot" });
  assert.strictEqual((await api("POST", { action: "reply", contact: "web:visitor123", text: "hi" })).statusCode, 400); console.log("  ✓ reply refused to a website visitor");
  assert.strictEqual((await api("POST", { action: "reply", contact: "919811111111", text: "hi" })).statusCode, 404); console.log("  ✓ unknown contact → 404");
  assert.strictEqual((await api("POST", { action: "explode", contact: C })).statusCode, 400); console.log("  ✓ unknown action refused");
  assert.strictEqual((await inboxApi({ httpMethod: "DELETE", headers: { authorization: "Bearer " + TOKEN } })).statusCode, 405); console.log("  ✓ other methods refused");
  console.log("\nwebhook tests passed");
})().catch((e) => { console.error(e); process.exit(1); });

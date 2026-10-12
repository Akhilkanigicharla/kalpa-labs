// Server-side regression tests for the review agent's findings. Run: NO_DELAY=1 node core/functions/hardening.test.js
process.env.NO_DELAY = "1"; process.env.SITE_URL = "https://botbhai.example";
const assert = require("assert");
const crypto = require("crypto");
const { store, graph } = require("./_fake.js")({
  clients: [
    { id: "s1", name: "Glow", niche: "salon", phone_number_id: "PN1", owner_whatsapp: "919000000001", meta_page_id: "PAGE1", active: true, config: { capacity: 1, business: "Glow Studio", review_link: "https://search.google.com/local/writereview?placeid=ChIJN1t_tDeuEmsRUsoyG83frY4" } },
    { id: "11111111-2222-3333-4444-555555555555", name: "Web Salon", niche: "salon", phone_number_id: "PN2", active: true, config: { capacity: 1 } },
  ],
  client_secrets: [{ client_id: "s1", meta_page_token: "pt" }],
});
const wa = require("./whatsapp.js"), chat = require("./chat.js"), reminders = require("./reminders.js"), metaleads = require("./metaleads.js");
const L = require("./_lib.js");
const sign = (b) => "sha256=" + crypto.createHmac("sha256", "appsecret").update(b).digest("hex");
const post = (h, payload) => { const body = JSON.stringify(payload); return h({ httpMethod: "POST", headers: { "x-hub-signature-256": sign(body) }, body }); };
let mid = 0;
const msgFrom = (from, m, id) => ({ entry: [{ changes: [{ value: { metadata: { phone_number_id: "PN1" }, contacts: [{ profile: { name: "C" } }], messages: [Object.assign({ from, id: id || "wamid." + (++mid) }, m)] } }] }] });
const say = (from, text, id) => post(wa.handler, msgFrom(from, { type: "text", text: { body: text } }, id));
const tap = (from, title) => post(wa.handler, msgFrom(from, { type: "interactive", interactive: { list_reply: { id: "t:" + title, title } } }));
const toCustomer = (to) => graph.sent.filter((m) => m.to === to && m.type);
let n = 0; const ok = async (name, fn) => { await fn(); n++; console.log("  ✓", name); };

(async () => {
  console.log("BotBhai hardening tests (server)");
  await ok("#2 Meta retries the same message: handled once, one booking, one confirmation", async () => {
    for (const t of ["book", "facial", "tomorrow", "4 pm"]) await say("919811100001", t);
    const id = "wamid.DUP";
    await Promise.all([say("919811100001", "Asha", id), say("919811100001", "Asha", id)]);
    assert.strictEqual(store.bookings.filter((b) => b.contact === "919811100001").length, 1);
    assert.strictEqual(toCustomer("919811100001").filter((m) => m.text && /Booking confirmed/.test(m.text.body)).length, 1);
  });
  await ok("#2 two customers race for the last chair: one wins, the other is offered other slots", async () => {
    for (const c of ["912222222222", "913333333333"]) for (const t of ["book", "facial", "tomorrow", "7 pm"]) await say(c, t);
    await Promise.all([say("912222222222", "Ravi"), say("913333333333", "Kiran")]);
    const at7 = store.bookings.filter((b) => b.date_iso && b.slot === "7:00 PM" && b.status === "confirmed");
    assert.strictEqual(at7.length, 1);
    const loser = at7[0].contact === "912222222222" ? "913333333333" : "912222222222";
    const last = toCustomer(loser).slice(-2).map((m) => (m.text && m.text.body) || (m.interactive && m.interactive.body.text)).join(" | ");
    assert.match(last, /someone grabbed 7:00 PM/); assert.doesNotMatch(last, /Booking confirmed/);
  });
  await ok("#4 a customer reply after a reminder keeps the 'already sent' flag (no duplicate reminder)", async () => {
    const lead = store.leads.find((l) => l.contact === "919811100001");
    lead.details = Object.assign({}, lead.details, { reminders: { day_before: "2026-10-12T05:00:00Z" } });
    await say("919811100001", "ok thanks");
    assert.ok(store.leads.find((l) => l.contact === "919811100001").details.reminders.day_before);
  });
  await ok("#14 reactions and stickers from an opted-out customer get no reply", async () => {
    await say("914444444444", "hi"); await say("914444444444", "STOP");
    const before = toCustomer("914444444444").length;
    await post(wa.handler, msgFrom("914444444444", { type: "reaction", reaction: { emoji: "👍" } }));
    await post(wa.handler, msgFrom("914444444444", { type: "sticker", sticker: { id: "x" } }));
    await say("914444444444", "worst service ever");
    assert.strictEqual(toCustomer("914444444444").length, before);
  });
  await ok("#3 website-chat bookings reach the same calendar and respect capacity", async () => {
    const c = "11111111-2222-3333-4444-555555555555";
    const web = (visitor, text) => chat.handler({ httpMethod: "POST", body: JSON.stringify({ client: c, visitor, text }) }).then((r) => JSON.parse(r.body));
    for (const t of ["book", "facial", "tomorrow", "4 pm"]) await web("visitor-aaa", t);
    await web("visitor-aaa", "Meena");
    assert.strictEqual(store.bookings.filter((b) => b.client_id === c && b.source === "web").length, 1);
    for (const t of ["book", "facial", "tomorrow"]) var r = await web("visitor-bbb", t);
    assert.ok(!r.replies.at(-1).options.includes("4:00 PM"));
  });
  await ok("#9 a Meta lead form from a booked customer keeps their booking", async () => {
    graph.responses["LEADX"] = { field_data: [{ name: "full_name", values: ["Asha"] }, { name: "phone_number", values: ["+91 98111 00001"] }, { name: "service", values: ["Bridal"] }] };
    const res = await post(metaleads.handler, { object: "page", entry: [{ changes: [{ field: "leadgen", value: { leadgen_id: "LEADX", page_id: "PAGE1" } }] }] });
    if (process.env.DEBUG) console.log("res", res, store.processed);
    if (process.env.DEBUG) console.log(store.leads.filter((l) => l.contact === "919811100001"), graph.calls.filter((c) => c.path.startsWith("LEADX")));
    const lead = store.leads.find((l) => l.contact === "919811100001");
    assert.strictEqual(lead.status, "booked"); assert.ok(lead.details.slot); assert.strictEqual(lead.details.meta_form.service, "Bridal");
  });
  await ok("#13 review links are never cut; template params lose newlines", async () => {
    const link = store.clients[0].config.review_link;
    assert.strictEqual(L.tplParam(link), link); assert.strictEqual(L.tplParam("a\nb\tc     d"), "a b c   d");
  });
  await ok("consent: promotional reminders (referral) skip customers without OFFERS opt-in", async () => {
    const appt = Date.now() - 75 * 3.6e6; const d = new Date(appt + 330 * 60000); const iso = d.toISOString().slice(0, 10);
    const h = d.getUTCHours(), mm = d.getUTCMinutes(); const slot = `${((h + 11) % 12) + 1}:${String(mm).padStart(2, "0")} ${h >= 12 ? "PM" : "AM"}`;
    store.leads.push({ id: "R1", client_id: "s1", contact: "915555555555", name: "No Consent", status: "booked", marketing_opt_in: false, details: { date_iso: iso, slot, reminders: { after_visit: "x" } } });
    store.leads.push({ id: "R2", client_id: "s1", contact: "916666666666", name: "Said Yes", status: "booked", marketing_opt_in: true, details: { date_iso: iso, slot, reminders: { after_visit: "x" } } });
    await reminders.handler();
    assert.ok(!graph.sent.some((m) => m.to === "915555555555" && m.template && /refer/.test(m.template.name)));
    assert.ok(graph.sent.some((m) => m.to === "916666666666" && m.template && /refer/.test(m.template.name)));
  });
  await ok("owner alert falls back to the approved template when plain text is refused (owner silent for 24 h)", async () => {
    graph.failNextTextTo = "919000000001";
    await L.alertOwner(store.clients[0], "🔔 test alert");
    assert.ok(graph.sent.some((m) => m.to === "919000000001" && m.template && m.template.name === "bb_owner_alert"));
  });
  console.log(`\n${n} tests passed`);
})().catch((e) => { console.error(e); process.exit(1); });

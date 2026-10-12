// Simulates Meta + Supabase with an in-memory fake, then drives the real webhook handler.
// Run: node 01-studio/botforge/netlify/functions/webhook.test.js
const assert = require("assert");
const crypto = require("crypto");
Object.assign(process.env, { WA_VERIFY_TOKEN: "kalpa-verify", WA_ACCESS_TOKEN: "x", WA_APP_SECRET: "appsecret", SUPABASE_URL: "https://fake.supabase.co", SUPABASE_SERVICE_ROLE_KEY: "k" });

const store = { clients: [{ id: "c1", name: "Glow Studio", niche: "salon", phone_number_id: "PNID", owner_whatsapp: "919000000000", active: true, config: {}, dashboard_token: "a".repeat(36) }], sessions: [], leads: [], messages: [] };
const sent = [];
global.fetch = async (url, opts = {}) => {
  const ok = (data) => ({ ok: true, status: 200, text: async () => JSON.stringify(data), json: async () => data });
  if (url.startsWith("https://graph.facebook.com")) { sent.push(JSON.parse(opts.body)); return ok({}); }
  const u = new URL(url); const table = u.pathname.split("/").pop();
  if ((opts.method || "GET") === "GET") {
    let rows = store[table];
    for (const [k, v] of u.searchParams) if (v.startsWith("eq.")) rows = rows.filter((r) => String(r[k]) === v.slice(3));
    return ok(rows);
  }
  const body = [].concat(JSON.parse(opts.body)); const keys = (u.searchParams.get("on_conflict") || "").split(",").filter(Boolean);
  for (const row of body) {
    const i = keys.length ? store[table].findIndex((r) => keys.every((k) => r[k] === row[k])) : -1;
    if (i >= 0) store[table][i] = Object.assign(store[table][i], row); else store[table].push(row);
  }
  return ok(body);
};

const { handler } = require("./whatsapp.js");
const sign = (b) => "sha256=" + crypto.createHmac("sha256", "appsecret").update(b).digest("hex");
const inbound = (msg) => {
  const body = JSON.stringify({ entry: [{ changes: [{ value: { metadata: { phone_number_id: "PNID" }, contacts: [{ profile: { name: "Ravi" } }], messages: [Object.assign({ from: "919812345678" }, msg)] } }] }] });
  return handler({ httpMethod: "POST", headers: { "x-hub-signature-256": sign(body) }, body });
};

(async () => {
  const v = await handler({ httpMethod: "GET", queryStringParameters: { "hub.mode": "subscribe", "hub.verify_token": "kalpa-verify", "hub.challenge": "42" } });
  assert.strictEqual(v.body, "42"); console.log("  ✓ webhook verification");
  const bad = await handler({ httpMethod: "POST", headers: { "x-hub-signature-256": "sha256=00" }, body: "{}" });
  assert.strictEqual(bad.statusCode, 401); console.log("  ✓ rejects forged signature");

  await inbound({ type: "text", text: { body: "hi" } });
  assert.strictEqual(sent[0].interactive.type, "list"); console.log("  ✓ menu sent as WhatsApp list");
  await inbound({ type: "interactive", interactive: { list_reply: { id: "o1", title: "Book a service" } } });
  await inbound({ type: "interactive", interactive: { list_reply: { id: "o4", title: "Hair spa" } } });
  await inbound({ type: "text", text: { body: "tomorrow" } });
  await inbound({ type: "interactive", interactive: { list_reply: { id: "o4", title: "7:00 PM" } } });
  await inbound({ type: "text", text: { body: "Ravi Teja" } });
  const confirm = sent.find((m) => m.type === "text" && /Booking confirmed/.test(m.text.body));
  assert.ok(confirm && /7:00 PM/.test(confirm.text.body)); console.log("  ✓ full booking over WhatsApp");
  assert.ok(sent.some((m) => m.to === "919000000000" && /New booking: Ravi Teja/.test(m.text.body))); console.log("  ✓ owner alerted on WhatsApp");
  const lead = store.leads[0];
  assert.strictEqual(store.leads.length, 1); assert.strictEqual(lead.score, "hot"); assert.strictEqual(lead.details.service, "Hair spa");
  console.log("  ✓ lead saved:", JSON.stringify({ name: lead.name, score: lead.score, status: lead.status, ...lead.details }));
  assert.ok(store.messages.length >= 12); console.log(`  ✓ ${store.messages.length} messages logged`);

  const { handler: leadsApi } = require("./leads.js");
  const r = await leadsApi({ queryStringParameters: { token: "a".repeat(36) } });
  assert.strictEqual(JSON.parse(r.body).leads.length, 1); console.log("  ✓ dashboard API returns the lead");
  const r2 = await leadsApi({ queryStringParameters: { token: "b".repeat(36) } });
  assert.strictEqual(r2.statusCode, 401); console.log("  ✓ dashboard API rejects wrong token");
  console.log("\nwebhook tests passed");
})().catch((e) => { console.error(e); process.exit(1); });

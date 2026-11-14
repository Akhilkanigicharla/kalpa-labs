// A87 · AI fallback through the real handlers: WhatsApp + website chat, the off switches, and the inbox author.
const assert = require("assert");
const crypto = require("crypto");
process.env.NO_DELAY = "1";
const WEB = "11111111-2222-3333-4444-555555555555", OFF = "22222222-3333-4444-5555-666666666666";
const { store } = require("./_fake.js")({ clients: [
  { id: "c1", name: "IronPulse", niche: "gym", phone_number_id: "PNID", owner_whatsapp: "919000000000", active: true, config: { capacity: 5 } },
  { id: WEB, name: "Web Gym", niche: "gym", phone_number_id: "PN2", active: true, config: { capacity: 5 } },
  { id: OFF, name: "Quiet Gym", niche: "gym", phone_number_id: "PN3", active: true, config: { capacity: 5, ai_fallback: false } },
] });
const wa = require("./whatsapp.js"); const chat = require("./chat.js");
let calls = 0;
const model = async () => { calls++; return '{"intent":"faq","faq":3,"service":null}'; }; // freeze / hold → gym FAQ 3
wa.ask = model; chat.ask = model;
const sign = (b) => "sha256=" + crypto.createHmac("sha256", "appsecret").update(b).digest("hex");
let mid = 0;
const inbound = (text, from = "919812345678") => {
  const body = JSON.stringify({ entry: [{ changes: [{ value: { metadata: { phone_number_id: "PNID" }, contacts: [{ profile: { name: "Ravi" } }], messages: [{ from, id: "wamid.ai" + (++mid), type: "text", text: { body: text } }] } }] }] });
  return wa.handler({ httpMethod: "POST", headers: { "x-hub-signature-256": sign(body) }, body });
};
const web = async (client, visitor, text) => JSON.parse((await chat.handler({ httpMethod: "POST", headers: { "x-nf-client-connection-ip": "198.51.100.7" }, body: JSON.stringify({ client, visitor, text }) })).body);
const MISS = "मेंबरशिप होल्ड हो सकती है क्या"; // the gym rules don't catch this (Hindi script)
const FREEZE = /frozen|freeze|फ्रीज|होल्ड|30/i;

(async () => {
  delete process.env.GROQ_API_KEY; delete process.env.LLM_ROUTER_URL; delete process.env.LLM_ROUTER_KEY;
  await inbound(MISS);
  assert.strictEqual(calls, 0, "no model configured → AI stays off");
  console.log("  ✓ off when no free model is configured");

  process.env.GROQ_API_KEY = "test";
  await inbound(MISS, "919812345679");
  assert.strictEqual(calls, 1);
  const out = store.messages.filter((m) => m.contact === "919812345679" && m.direction === "out");
  assert.ok(out.length && out.every((m) => m.author === "ai"), "AI-chosen replies are marked 'ai' for the owner's inbox");
  assert.ok(out.some((m) => FREEZE.test(m.body)) && !out.some((m) => /माफ़ कीजिए/.test(m.body)), "the answer is the gym's own freeze FAQ");
  console.log("  ✓ WhatsApp: rules miss → AI picks the FAQ → setup's own answer, logged as 'ai'");

  await inbound("price list", "919812345680");
  assert.strictEqual(calls, 1, "rules answered → model not asked");
  assert.ok(store.messages.filter((m) => m.contact === "919812345680" && m.direction === "out").every((m) => m.author === "bot"));
  console.log("  ✓ rules answers stay 'bot' and never call the model");

  process.env.BOTBHAI_AI_FALLBACK = "off";
  await inbound(MISS, "919812345681");
  assert.strictEqual(calls, 1, "platform switch off");
  delete process.env.BOTBHAI_AI_FALLBACK;
  console.log("  ✓ platform off switch (BOTBHAI_AI_FALLBACK=off)");

  const r = await web(WEB, "visitor-ai-1", MISS);
  assert.strictEqual(calls, 2);
  assert.ok(r.replies.some((x) => FREEZE.test(x.text)));
  const logged = store.messages.filter((m) => m.contact === "web:visitor-ai-1");
  assert.ok(logged.some((m) => m.direction === "in" && m.author === "customer") && logged.some((m) => m.author === "ai"),
    "website chats are now logged for the inbox, AI replies marked");
  console.log("  ✓ website chat: same AI rescue, conversation logged for the owner's inbox");

  await web(OFF, "visitor-ai-2", MISS);
  assert.strictEqual(calls, 2, "client switch off (config.ai_fallback = false)");
  console.log("  ✓ per-client off switch (clients.config.ai_fallback = false)");

  wa.ask = async () => { throw new Error("429 rate limited"); };
  await inbound(MISS, "919812345682");
  assert.ok(store.messages.filter((m) => m.contact === "919812345682" && m.direction === "out").every((m) => m.author === "bot"), "model down → normal menu");
  console.log("  ✓ model down → the normal menu reply, nothing breaks");
  console.log("AI fallback handler tests passed");
})().catch((e) => { console.error(e); process.exit(1); });

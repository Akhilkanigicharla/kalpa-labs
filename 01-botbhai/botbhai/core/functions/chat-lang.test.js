// 5 languages on the BotBhai website chat (Akhil, 5 Nov 2026): Tenglish/Hinglish typed → reply mirrored; English stays English.
const assert = require("assert");
process.env.NO_DELAY = "1";
const CID = "11111111-2222-3333-4444-555555555555";
require("./_fake.js")({ clients: [{ id: CID, name: "Web Salon", niche: "salon", phone_number_id: "PN2", active: true, config: { capacity: 1 } }] });
process.env.GROQ_API_KEY = "test-groq";
const asked = []; const base = global.fetch;
global.fetch = async (url, opts = {}) => {
  if (String(url).startsWith("https://api.groq.com/")) {
    const b = JSON.parse(opts.body); asked.push(b.messages[0].content);
    const tag = /Tenglish/.test(b.messages[0].content) ? "TENGLISH" : /Hinglish/.test(b.messages[0].content) ? "HINGLISH" : "OTHER";
    return { ok: true, status: 200, json: async () => ({ choices: [{ message: { content: tag + ": " + JSON.parse(opts.body).messages[1].content } }] }) };
  }
  return base(url, opts);
};
const chat = require("./chat.js");
const say = (visitor, text, extra = {}) => chat.handler({ httpMethod: "POST", headers: { "x-nf-client-connection-ip": "198.51.100.90" }, body: JSON.stringify(Object.assign({ client: CID, visitor, text }, extra)) }).then((r) => JSON.parse(r.body));

(async () => {
  let r = await say("visitor-en", "hi, what are your prices?");
  assert.ok(r.replies.length && r.replies.every((x) => !/^(TENGLISH|HINGLISH)/.test(x.text)), "English stays English, no model call");
  assert.strictEqual(asked.length, 0);
  console.log("  ✓ English in → English out (no extra model call)");

  r = await say("visitor-te", "repu slot undi aa? hair spa kavali");
  assert.ok(r.replies.every((x) => /^TENGLISH/.test(x.text)), "Tenglish in → Tenglish out");
  console.log("  ✓ Tenglish in → Tenglish out");

  r = await say("visitor-hi", "kal shaam ka slot milega kya? haircut karna hai");
  assert.ok(r.replies.every((x) => /^HINGLISH/.test(x.text)), "Hinglish in → Hinglish out");
  console.log("  ✓ Hinglish in → Hinglish out");

  r = await say("visitor-te", "ok");
  assert.ok(r.replies.every((x) => /^TENGLISH/.test(x.text)), "a short English-looking follow-up keeps the customer's Tenglish");
  console.log("  ✓ follow-up keeps the customer's language");

  const n = asked.length; r = await say("visitor-tescript", "రేపు స్లాట్ ఉందా?");
  assert.strictEqual(asked.length, n, "Telugu script uses the engine's own Telugu, no translation call");
  console.log("  ✓ Telugu script answered by the engine's own Telugu");
  console.log("chat language tests passed");
})().catch((e) => { console.error(e); process.exit(1); });

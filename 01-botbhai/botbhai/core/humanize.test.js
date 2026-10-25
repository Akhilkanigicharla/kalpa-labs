// Run: node core/humanize.test.js
const assert = require("assert");
const H = require("./humanize.js");
const { BotBhai } = require("../setups/index.js");
let n = 0; const ok = (name, fn) => Promise.resolve(fn()).then(() => { n++; console.log("  ✓", name); });
(async () => {
  console.log("BotBhai human-touch tests");
  await ok("language detection", () => {
    assert.strictEqual(H.detectLanguage("రేపు స్లాట్ ఉందా?"), "te");
    assert.strictEqual(H.detectLanguage("कल का स्लॉट है?"), "hi");
    assert.strictEqual(H.detectLanguage("repu slot undi aa? hair spa kavali"), "te-latn");
    assert.strictEqual(H.detectLanguage("bhai kal ka slot milega kya"), "hi-latn");
    assert.strictEqual(H.detectLanguage("Do you have a slot tomorrow?"), "en");
  });
  await ok("first contact: time greeting, persona, AI disclosure", () => {
    const out = BotBhai.createBot("salon").handle(BotBhai.newState(), "hi", {});
    const evening = Date.UTC(2026, 9, 12, 14, 0); // 7:30 PM IST
    const h = H.humanize(out.replies, { setup: "salon", business: "Glow Studio", firstContact: true, userText: "hi", contact: "91", turn: 1, nowMs: evening });
    assert.match(h.replies[0].text, /^Good evening! Welcome to \*Glow Studio Unisex Salon\*/);
    assert.match(h.replies[0].text, /I'm Meera, Glow Studio's booking assistant \(an AI; type \*human\*/);
  });
  await ok("varied phrasing for the same engine line", () => {
    const line = [{ text: "Great, let's book your booking. Type *cancel* any time to stop." }];
    const seen = new Set(); for (let t = 0; t < 12; t++) seen.add(H.humanize(line, { setup: "salon", contact: "9" + t, turn: t }).replies[0].text);
    assert.ok(seen.size >= 2, "expected at least 2 variants");
  });
  await ok("frustration → apology first + human handoff", () => {
    const h = H.humanize([{ text: "menu" }], { setup: "gym", userText: "still waiting, worst service", contact: "1", turn: 3 });
    assert.ok(h.handoff); assert.match(h.replies[0].text, /sorry/i);
  });
  await ok("typing delay is human-paced", () => {
    assert.strictEqual(H.typingDelayMs("ok"), 800); assert.strictEqual(H.typingDelayMs("x".repeat(500)), 4000);
  });
  await ok("translation validator keeps prices, times and links intact", async () => {
    const src = "Hair spa — *₹1,200*. Slot at 4:00 PM. Map: https://maps.google.com/?q=x";
    assert.ok(H.translationIsSafe(src, "హెయిర్ స్పా — *₹1,200*. 4:00 PM కి స్లాట్. మ్యాప్: https://maps.google.com/?q=x"));
    assert.ok(!H.translationIsSafe(src, "హెయిర్ స్పా — *₹1,000*. 4:00 PM కి స్లాట్. https://maps.google.com/?q=x"));
    const fake = (good) => async () => ({ json: async () => ({ choices: [{ message: { content: good } }] }) });
    let out = await H.mirrorLanguage([{ text: src }], "te", { apiKey: "k", fetchImpl: fake("హెయిర్ స్పా *₹1,200*, 4:00 PM, https://maps.google.com/?q=x") });
    assert.match(out[0].text, /హెయిర్/);
    out = await H.mirrorLanguage([{ text: src }], "te", { apiKey: "k", fetchImpl: fake("హెయిర్ స్పా ₹999 మాత్రమే") });
    assert.strictEqual(out[0].text, src); // unsafe translation rejected → English kept
  });
  await ok("Groq down → Kalpa router (A120) translates; both down → English kept", async () => {
    const src = "Booked: *₹500* at 5:00 PM.";
    const calls = [];
    const f = (routerOk) => async (url, init) => { calls.push([url, JSON.parse(init.body).model]);
      if (url.includes("groq")) return { ok: false, status: 429, json: async () => ({}) };
      return routerOk ? { ok: true, json: async () => ({ choices: [{ message: { content: "బుక్ అయింది: *₹500* 5:00 PM కి." } }] }) } : { ok: false, status: 503, json: async () => ({}) }; };
    let out = await H.mirrorLanguage([{ text: src }], "te", { apiKey: "k", fetchImpl: f(true), router: { url: "https://r.example/", key: "rk" } });
    assert.match(out[0].text, /బుక్/); assert.deepStrictEqual(calls.map((c) => c[1]), [require("./models.json").groq_chat, "auto:reliable"]);
    assert.strictEqual(calls[1][0], "https://r.example/v1/chat/completions");
    out = await H.mirrorLanguage([{ text: src }], "te", { apiKey: "k", fetchImpl: f(false), router: { url: "https://r.example", key: "rk" } });
    assert.strictEqual(out[0].text, src);
    out = await H.mirrorLanguage([{ text: src }], "te", { fetchImpl: f(true), router: { url: "https://r.example", key: "" } });
    assert.strictEqual(out[0].text, src); // no keys at all → untouched
  });
  console.log(`\n${n} tests passed`);
})().catch((e) => { console.error(e); process.exit(1); });

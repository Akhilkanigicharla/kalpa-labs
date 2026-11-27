// A351: under-18 detector + fixed parent replies. Run: node core/minor.test.js
const assert = require("assert");
const M = require("./minor.js");
const YES = [ // the writer says they are under 18 (4+ per language)
  "I am 15", "I'm 16 and in 10th grade", "im 14 years old", "I am in 9th class", "My age is 13", "I'm a minor", "i am under 18",
  "నేను 15 సంవత్సరాలు", "నాకు 16 ఏళ్ళు", "నా వయసు 14", "నేను 9వ తరగతి చదువుతున్నాను",
  "मैं 15 साल का हूँ", "मैं 16 साल की हूं", "मेरी उम्र 14 है", "मैं 9वीं कक्षा में हूँ", "मैं १५ साल का हूँ",
  "nenu 9th class", "naa vayasu 15", "naku 16 years", "nenu 14 yella", "nenu 10th class lo unna",
  "main 15 saal ka hoon", "meri age 16 hai", "main 9th class mein hoon", "15 saal ki hu", "I'm 17, can I book a haircut?",
];
const NO = [ // adults, parents, and numbers that are not an age
  "I am 18", "I'm 18+ and ready to book", "i am 25 years old", "My son is 12 and wants a haircut", "my daughter is in class 10, tuition?",
  "I'm 10 minutes late", "I am 5 people", "i am 2 km away", "booking for 15 people", "I am booking for my 15 year old",
  "నా కొడుకు 12 ఏళ్ళు", "నేను 25 సంవత్సరాలు", "मेरा बेटा 12 साल का है", "मैं 30 साल का हूँ", "मेरी बेटी 9वीं कक्षा में है",
  "naa koduku 10th class", "nenu 30 years", "mera beta 12 saal ka hai", "main 20 saal ka hoon", "kal 15 tarikh ko slot hai",
  "class 10 tuition for my daughter", "I am in room 12", "price 15 rs?", "Hi, slot at 11 am?", "",
];
let n = 0;
for (const s of YES) { assert.strictEqual(M.isMinor(s), true, "should flag: " + s); n++; }
for (const s of NO) { assert.strictEqual(M.isMinor(s), false, "should not flag: " + s); n++; }
assert.strictEqual(M.isMinor("x".repeat(5000)), false); n++; // huge input: no work, no flag
for (const l of ["en", "te", "hi", "tg", "hg"]) { const r = M.reply(l); assert.ok(/18/.test(r) && r.length < 400, l); n++; }
assert.ok(/[ఀ-౿]/.test(M.reply("te")) && /[ऀ-ॿ]/.test(M.reply("hi")) && !/[ऀ-౿]/.test(M.reply("tg") + M.reply("hg"))); n++;
assert.strictEqual(M.reply("te-latn"), M.REPLY.tg); assert.strictEqual(M.reply("xx"), M.REPLY.en); n++;
// engine: the under-18 path in every language, on a real setup
const { BotBhai: B } = require("../setups/index.js");
const NOW = { now: "2026-10-12T04:30:00Z", contact: "919999999999", profileName: "Chinni" };
const LANGS = { en: "I am 15", te: "నాకు 16 ఏళ్ళు", hi: "मैं 15 साल का हूँ", tg: "naa vayasu 15 andi", hg: "main 15 saal ka hoon yaar" };
for (const [lg, msg] of Object.entries(LANGS)) {
  const bot = B.createBot("salon"); let st = B.newState();
  st = bot.handle(st, "book haircut, name Chinni", NOW).state;
  if (lg === "tg" || lg === "hg") st.lang = lg; // Latin-letter languages come from earlier turns or the handler's detector
  const out = bot.handle(st, msg, NOW);
  assert.strictEqual(out.replies.length, 1); assert.strictEqual(out.replies[0].text, M.reply(lg), lg);
  assert.ok(out.events.some((e) => e.type === "minor_stop") && out.events.some((e) => e.type === "notify_owner" && !/15|16|Chinni/.test(e.text)));
  assert.strictEqual(out.lead.status, "minor"); assert.strictEqual(out.lead.name, null); assert.strictEqual(out.lead.marketing_opt_in, false);
  assert.ok(!JSON.stringify(out.state.data).includes("Chinni") && out.state.step === -1);
  for (const later of ["offers", "book haircut", "hi", "my name is Chinni 9876543210"]) {
    const o = bot.handle(out.state, later, NOW);
    assert.strictEqual(o.replies.length, 0, later); assert.strictEqual(o.lead.marketing_opt_in, false); assert.strictEqual(o.lead.name, null);
  }
  n += 3;
}
{ // a parent booking for a child goes on as normal
  const bot = B.createBot("salon"); const o = bot.handle(B.newState(), "my son is 12, haircut price?", NOW);
  assert.ok(!o.state.minor && o.replies.length >= 1); n++;
}
console.log(`minor.test.js: ${n} checks passed`);

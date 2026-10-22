// A73: replies in the customer's language (Telugu / Hindi). Run: node core/lang.test.js
const assert = require("assert");
const { BotBhai: B } = require("../setups/index.js");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };
const NOW = { now: "2026-10-12T04:30:00Z" }; // Mon 12 Oct 2026, 10 AM IST
function talk(niche, lines, meta = {}) {
  const bot = B.createBot(niche); let state = B.newState(); const log = []; let out;
  for (const l of lines) {
    out = bot.handle(state, l, Object.assign({ contact: "919999999999" }, NOW, meta)); state = out.state;
    log.push({ bot: out.replies.map((r) => r.text).join("\n---\n"), events: out.events, options: (out.replies.at(-1) || {}).options || [] });
  }
  const own = [bot.config.business, bot.config.address].join(" ").toLowerCase().match(/[a-z][a-z']+/g) || []; // the client's own name and address
  return { log, state, lead: out.lead, keep: new Set(own) };
}
// Words allowed to stay in Latin letters inside a Telugu/Hindi reply: the client's own name and address,
// times, commands the customer types back, brand and exam names, and units.
const KEEP = new Set(("glow studio unisex salon road no jubilee hills hyderabad am pm menu cancel book offers stop start bot yes human " +
  "upi emi pdf whatsapp sbi hdfc icici rera ts nri bhk cr dec jan iron fitness hub kondapur gachibowli kollur tellapur kompally shadnagar " +
  "skyline meadows crest green acres tspsc group ssc cgl rrb ntpc bank po meritpath academy ashok nagar plot oréal professionnel o3 " +
  "every day to sunday saturday mon sat priya").split(" "));
function english(text, own) { return (text.match(/[A-Za-z][A-Za-z']+/g) || []).map((w) => w.toLowerCase()).filter((w) => !KEEP.has(w) && !(own && own.has(w))); }
const assertNoEnglish = (r, i) => { const left = english(r.log[i].bot + " " + r.log[i].options.join(" "), r.keep); assert.deepStrictEqual(left, [], `English left in reply ${i}: ${left.join(", ")}\n${r.log[i].bot}`); };
const TE = /[ఀ-౿]/, HI = /[ऀ-ॿ]/;

console.log("BotBhai language tests (A73)");

ok("Telugu salon booking from hello to confirmation: every reply in Telugu, nothing left in English", () => {
  const r = talk("salon", ["హాయ్", "1", "హెయిర్ స్పా", "రేపు", "1", "ప్రియ"]);
  for (let i = 0; i < r.log.length; i++) { assert.match(r.log[i].bot, TE, `reply ${i} is Telugu`); assertNoEnglish(r, i); }
  assert.match(r.log[0].bot, /మీకు ఎలా సహాయం చేయగలను/);
  assert.match(r.log[1].bot, /మీకు ఏ సర్వీస్ కావాలి\?/); assert.ok(r.log[1].options.includes("హెయిర్ స్పా"));
  assert.match(r.log[3].bot, /సమయం ఎంచుకోండి/);
  assert.match(r.log[5].bot, /బుకింగ్ కన్ఫర్మ్ అయింది/); assert.match(r.log[5].bot, /హెయిర్ స్పా/); assert.match(r.log[5].bot, /మంగళ, 13 అక్టోబర్, 11:00 AM/);
});

ok("the booking saved for the salon stays in English (owner, database, reminders)", () => {
  const r = talk("salon", ["హాయ్", "1", "హెయిర్ స్పా", "రేపు", "1", "ప్రియ"]);
  const ev = r.log[5].events; const b = ev.find((e) => e.type === "booking").booking;
  assert.strictEqual(b.service, "Hair spa"); assert.strictEqual(b.date_iso, "2026-10-13"); assert.strictEqual(b.slot, "11:00 AM");
  assert.match(ev.find((e) => e.type === "notify_owner").text, /New appointment: ప్రియ · Hair spa · Tue, 13 Oct 11:00 AM/);
  assert.strictEqual(r.state.data.date, "Tue, 13 Oct"); assert.strictEqual(r.lead.service, "Hair spa");
});

ok("Hindi salon booking: every reply in Hindi, nothing left in English", () => {
  const r = talk("salon", ["नमस्ते", "1", "2", "कल", "शाम", "प्रिया"]);
  for (let i = 0; i < r.log.length; i++) { assert.match(r.log[i].bot, HI, `reply ${i} is Hindi`); assertNoEnglish(r, i); }
  assert.match(r.log[5].bot, /बुकिंग पक्की/); assert.match(r.log[5].bot, /हेयरकट और स्टाइलिंग \(महिला\)/); assert.match(r.log[5].bot, /मंगल, 13 अक्टूबर, 7:00 PM/);
  assert.strictEqual(r.log[5].events.find((e) => e.type === "booking").booking.service, "Haircut & styling (women)");
});

ok("typing 'telugu' picks Telugu; later Latin replies (numbers, a Latin name) keep Telugu", () => {
  const r = talk("salon", ["telugu", "1", "1", "tomorrow", "2", "Priya"]);
  for (let i = 0; i < r.log.length; i++) { assert.match(r.log[i].bot, TE, `reply ${i}`); assertNoEnglish(r, i); }
  assert.strictEqual(r.state.lang, "te");
});

ok("'english' switches back; mid-booking a switch re-asks the same question in the new language", () => {
  const r = talk("salon", ["హాయ్", "1", "english", "Hair spa"]);
  assert.match(r.log[2].bot, /Which service would you like\?/); assert.match(r.log[3].bot, /Which day\?/);
  const h = talk("salon", ["hi", "book", "hindi"]);
  assert.match(h.log[2].bot, /आपको कौन सी सर्विस चाहिए\?/);
});

ok("Tenglish in Latin letters keeps English replies (understood, not switched)", () => {
  const r = talk("salon", ["repu hair spa kavali"]);
  assert.match(r.log[0].bot, /Sure! Hair spa, Tue, 13 Oct/); assert.strictEqual(r.state.lang, undefined);
});

ok("the web chat's language button (meta.lang) sets the reply language until the customer writes in another script", () => {
  const r = talk("salon", ["hi", "1"], { lang: "hi" });
  assert.match(r.log[0].bot, /मैं कैसे मदद करूँ/); assert.match(r.log[1].bot, /आपको कौन सी सर्विस चाहिए/);
  const t = talk("salon", ["hi", "హాయ్"], { lang: "hi" }); assert.match(t.log[1].bot, /మీకు ఎలా సహాయం/);
});

ok("Telugu one-line booking ('రేపు హెయిర్ స్పా కావాలి') pre-fills service and day in Telugu", () => {
  const r = talk("salon", ["రేపు హెయిర్ స్పా కావాలి"]);
  assert.match(r.log[0].bot, /సరే! హెయిర్ స్పా, మంగళ, 13 అక్టోబర్ 👍/); assert.match(r.log[0].bot, /సమయం ఎంచుకోండి/); assertNoEnglish(r, 0);
});

ok("Telugu cancel: ask, then 'అవును, క్యాన్సిల్' cancels; owner alert stays English", () => {
  const r = talk("salon", ["హాయ్", "1", "హెయిర్ స్పా", "రేపు", "1", "ప్రియ", "రద్దు", "అవును, క్యాన్సిల్"]);
  assert.match(r.log[6].bot, /క్యాన్సిల్ చేయాలా\?/); assertNoEnglish(r, 6);
  assert.match(r.log[7].bot, /క్యాన్సిల్ అయింది/); assert.strictEqual(r.lead.status, "cancelled");
  assert.match(r.log[7].events.find((e) => e.type === "notify_owner").text, /^❌ Cancelled: ప్రియ · Hair spa · Tue, 13 Oct 11:00 AM/);
});

ok("Telugu reminder reply 'సరే' confirms in Telugu; Hindi 'हाँ' in Hindi", () => {
  const te = talk("salon", ["book", "hair spa", "tomorrow", "4 pm", "Priya", "సరే"]);
  assert.match(te.log[5].bot, /కన్ఫర్మ్ అయింది: హెయిర్ స్పా, మంగళ, 13 అక్టోబర్, 4:00 PM/);
  const hi = talk("salon", ["book", "hair spa", "tomorrow", "4 pm", "Priya", "हाँ"]);
  assert.match(hi.log[5].bot, /पक्का हो गया: हेयर स्पा, मंगल, 13 अक्टूबर, 4:00 PM/);
});

ok("gym (Telugu) and real estate (Hindi) bookings: no English left", () => {
  const g = talk("gym", ["హాయ్", "1", "బరువు తగ్గడం", "రేపు", "3", "రవి"]);
  for (let i = 0; i < g.log.length; i++) assertNoEnglish(g, i);
  assert.match(g.log[5].bot, /ఉచిత ట్రయల్ బుక్ అయింది/); assert.match(g.log[5].bot, /లక్ష్యం: బరువు తగ్గడం/);
  assert.strictEqual(g.log[5].events.find((e) => e.type === "booking").booking.service, "Weight loss");
  const re = talk("realestate", ["नमस्ते", "1", "ख़रीदना", "2", "1", "Kollur", "कल", "1", "सुरेश"]);
  for (let i = 0; i < re.log.length; i++) assertNoEnglish(re, i);
  assert.match(re.log[8].bot, /साइट विज़िट बुक हो गई/); assert.match(re.log[8].bot, /ख़रीदना · 2 BHK · ₹50L से कम/);
});

ok("exam kits (Telugu): menu, exam choice and score-card advice in Telugu", () => {
  const r = talk("examkits", ["హాయ్", "1", "1", "A", "A", "A", "రాము"]);
  assert.match(r.log[0].bot, /ఈరోజు ఉచిత క్విజ్/); assert.match(r.log[1].bot, /మీరు ఏ పరీక్షకు ప్రిపేర్ అవుతున్నారు/);
  assert.match(r.log[6].bot, /స్కోర్ కార్డ్ — రాము/); assert.match(r.log[6].bot, /(అద్భుతం|బాగుంది|బేసిక్స్)/);
});

ok("Telugu FAQ, prices, human handoff and 'didn't get that' are in Telugu", () => {
  const r = talk("salon", ["హాయ్", "2", "3", "5"]);
  assert.match(r.log[1].bot, /ధరల జాబితా/); assert.match(r.log[1].bot, /హెయిర్ స్పా — \*₹/); assertNoEnglish(r, 1);
  assert.match(r.log[2].bot, /ఈ వారం/); assert.match(r.log[3].bot, /టీమ్‌కి చెప్పాను/);
  assert.ok(r.log[3].events.some((e) => e.type === "handoff" && /wants to talk to a person/.test(e.text)), "owner alert English");
  const s = talk("salon", ["హాయ్", "ఏదో అర్థం కాని మాట"]); assert.match(s.log[1].bot, /సరిగ్గా అర్థం కాలేదు/);
});

ok("every setup has Telugu and Hindi for its greeting, menu, questions, confirmation and FAQs", () => {
  const { SETUPS } = require("../setups/index.js");
  for (const [id, c] of Object.entries(SETUPS)) for (const lg of ["te", "hi"]) {
    const L = c.i18n && c.i18n[lg]; assert.ok(L, `${id} ${lg}`);
    assert.ok(L.greeting && L.confirm && L.catalogTitle && L.bookWord, `${id} ${lg} basics`);
    assert.strictEqual(L.menu.length, c.menu.length, `${id} ${lg} menu`); assert.strictEqual(L.faqs.length, c.faqs.length, `${id} ${lg} faqs`);
    for (const s of c.steps) if (s.ask) assert.ok(L.asks[s.field], `${id} ${lg} ask ${s.field}`);
    for (const k of ["greeting", "confirm"]) assert.match(L[k], lg === "te" ? TE : HI, `${id} ${lg} ${k} script`);
    for (const v of [...(c.greeting.match(/\{\w+\}/g) || [])]) assert.ok(L.greeting.includes(v), `${id} ${lg} greeting keeps ${v}`);
    for (const v of [...(c.confirm.match(/\{\w+\}/g) || [])]) assert.ok(L.confirm.includes(v), `${id} ${lg} confirm keeps ${v}`);
  }
});

console.log(`language tests passed (${n})`);

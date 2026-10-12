// Run: node 01-studio/botforge/engine/engine.test.js
const assert = require("assert");
const { BotBhai: B } = require("../setups/index.js");
const NOW = new Date(2026, 9, 12, 10, 0).toISOString(); // Mon 12 Oct 2026
let passed = 0;

function talk(niche, lines) {
  const bot = B.createBot(niche); let state = B.newState(); const log = []; let out;
  for (const l of lines) {
    out = bot.handle(state, l, { now: NOW, contact: "+919999999999", profileName: "Test" });
    state = out.state; log.push({ you: l, bot: out.replies.map((r) => r.text).join("\n---\n"), events: out.events });
  }
  return { log, state, lead: out.lead };
}
function ok(name, fn) { fn(); passed++; console.log("  ✓", name); }

console.log("BotBhai engine tests");
ok("dates", () => {
  const now = new Date(NOW);
  assert.strictEqual(B.parseDate("tomorrow", now).getDate(), 13);
  assert.strictEqual(B.parseDate("friday", now).getDate(), 16);
  assert.strictEqual(B.parseDate("monday", now).getDate(), 19);
  assert.strictEqual(B.parseDate("15/10", now).getDate(), 15);
  assert.strictEqual(B.parseDate("5 nov", now).getMonth(), 10);
  assert.strictEqual(B.parseDate("31/02", now), null);
  assert.strictEqual(B.parseDate("blah", now), null);
});
ok("salon full booking by numbers + owner alert", () => {
  const r = talk("salon", ["hi", "1", "4", "tomorrow", "3", "ravi kumar"]);
  assert.match(r.log[5].bot, /Booking confirmed[\s\S]*Hair spa[\s\S]*Tue, 13 Oct at 4:00 PM/);
  assert.strictEqual(r.lead.score, "hot"); assert.strictEqual(r.lead.status, "booked"); assert.strictEqual(r.lead.name, "Ravi Kumar");
  assert.ok(r.log[5].events.some((e) => e.type === "notify_owner"));
});
ok("salon bad date then recovery, cancel", () => {
  const r = talk("salon", ["book", "facial", "someday", "friday", "cancel"]);
  assert.match(r.log[2].bot, /couldn't read that date/); assert.match(r.log[3].bot, /Choose a time/); assert.match(r.log[4].bot, /cancelled/);
});
ok("salon booking with words", () => {
  const r = talk("salon", ["hello", "book", "hair spa", "saturday", "7:00 PM", "my name is priya"]);
  assert.match(r.log[5].bot, /Booking confirmed[\s\S]*Hair spa[\s\S]*Sat, 17 Oct at 7:00 PM/);
  assert.strictEqual(r.lead.name, "Priya");
});
ok("salon offers via menu", () => { const r = talk("salon", ["hi", "3"]); assert.match(r.log[1].bot, /This week/); });
ok("real estate full qualification", () => {
  const r = talk("realestate", ["hi", "1", "buy", "3 BHK", "3", "Tellapur", "sunday", "1", "Anil Reddy"]);
  const last = r.log[8].bot;
  assert.match(last, /Site visit booked[\s\S]*Buy · 3 BHK · ₹1Cr – ₹2Cr[\s\S]*Tellapur[\s\S]*Sun, 18 Oct at 10:00 AM/);
  assert.strictEqual(r.lead.bhk, "3 BHK");
});
ok("real estate loan faq + human handoff", () => {
  const r = talk("realestate", ["emi on home loan?", "talk to advisor"]);
  assert.match(r.log[0].bot, /43,400/);
  assert.ok(r.log[1].events.some((e) => e.type === "handoff")); assert.strictEqual(r.lead.status, "callback");
});
ok("gym trial", () => {
  const r = talk("gym", ["hey", "free trial", "weight loss", "today", "6:00 AM", "Sai"]);
  assert.match(r.log[5].bot, /Free trial booked[\s\S]*Weight loss[\s\S]*Mon, 12 Oct at 6:00 AM/);
});
ok("gym plans and ladies batch", () => {
  const r = talk("gym", ["membership plans", "ladies batch?"]);
  assert.match(r.log[0].bot, /Annual \(best value\) — \*₹11,999\*/); assert.match(r.log[1].bot, /Women-only/);
});
ok("exam quiz scoring", () => {
  const r = talk("examkits", ["hi", "1", "SSC CGL", "B", "c", "A", "Lakshmi"]);
  assert.match(r.log[3].bot, /Correct/); assert.match(r.log[5].bot, /Not quite/);
  assert.match(r.log[6].bot, /Score card — Lakshmi[\s\S]*2\/3/);
  assert.strictEqual(r.lead.score, "hot"); assert.strictEqual(r.lead.status, "quiz_done");
});
ok("opt-out silences bot until START", () => {
  const r = talk("gym", ["hi", "STOP", "hello?", "start"]);
  assert.match(r.log[1].bot, /unsubscribed/); assert.strictEqual(r.log[2].bot, ""); assert.match(r.log[3].bot, /Welcome back/);
});
ok("unknown text falls back to menu + logs unanswered", () => {
  const r = talk("salon", ["asdfgh qwerty"]);
  assert.match(r.log[0].bot, /didn't quite get that/); assert.ok(r.log[0].events.some((e) => e.type === "unanswered"));
});
console.log(`\n${passed} tests passed`);

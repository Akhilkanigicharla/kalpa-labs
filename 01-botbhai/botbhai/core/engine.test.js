// Run: node 01-botbhai/botforge/engine/engine.test.js
const assert = require("assert");
const { BotBhai: B } = require("../setups/index.js");
const NOW = "2026-10-12T04:30:00.000Z"; // Mon 12 Oct 2026, 10:00 AM IST
let passed = 0;

function talk(niche, lines, meta = {}, overrides) {
  const bot = B.createBot(niche, overrides); let state = B.newState(); const log = []; let out;
  for (const l of lines) {
    out = bot.handle(state, l, Object.assign({ now: NOW, contact: "+919999999999", profileName: "Test" }, meta));
    state = out.state; log.push({ you: l, bot: out.replies.map((r) => r.text).join("\n---\n"), events: out.events });
  }
  return { log, state, lead: out.lead };
}
function ok(name, fn) { fn(); passed++; console.log("  ✓", name); }

console.log("BotBhai engine tests");
ok("dates", () => {
  const now = new Date(NOW);
  assert.strictEqual(B.parseDate("tomorrow", now).getUTCDate(), 13);
  assert.strictEqual(B.parseDate("friday", now).getUTCDate(), 16);
  assert.strictEqual(B.parseDate("monday", now).getUTCDate(), 12); // today is Monday → today
  assert.strictEqual(B.parseDate("next monday", now).getUTCDate(), 19);
  assert.strictEqual(B.parseDate("15/10", now).getUTCDate(), 15);
  assert.strictEqual(B.parseDate("5 nov", now).getUTCMonth(), 10);
  assert.strictEqual(B.parseDate("10/10/2026", now), null); // past date with a year is rejected
  assert.strictEqual(B.parseDate("repu", now).getUTCDate(), 13);
  assert.strictEqual(B.parseDate("రేపు", now).getUTCDate(), 13);
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
  assert.match(r.log[2].bot, /couldn.t read that date/); assert.match(r.log[3].bot, /Choose a time/); assert.match(r.log[4].bot, /stopped/);
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
  const r = talk("gym", ["hey", "free trial", "weight loss", "today", "1", "Sai"]);
  assert.doesNotMatch(r.log[3].bot, /6:00 AM|8:00 AM/); // it is 10 AM: morning slots already gone
  assert.match(r.log[5].bot, /Free trial booked[\s\S]*Weight loss[\s\S]*Mon, 12 Oct at 6:00 PM/);
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
ok("capacity: full slots are hidden, a full day asks for another day", () => {
  const busy = [{ date_iso: "2026-10-13", slot: "11:00 AM" }, { date_iso: "2026-10-13", slot: "11:00 AM" }];
  const r = talk("salon", ["book", "facial", "tomorrow"], { busy }, { capacity: 2 });
  assert.doesNotMatch(r.log[2].bot, /11:00 AM/); assert.match(r.log[2].bot, /1:00 PM/);
  const full = ["11:00 AM", "1:00 PM", "4:00 PM", "7:00 PM"].flatMap((slot) => [{ date_iso: "2026-10-13", slot }, { date_iso: "2026-10-13", slot }]);
  const f = talk("salon", ["book", "facial", "tomorrow", "friday", "2", "Asha"], { busy: full }, { capacity: 2 });
  assert.match(f.log[2].bot, /fully booked/); assert.match(f.log[5].bot, /Booking confirmed[\s\S]*Fri, 16 Oct at 1:00 PM/);
  assert.ok(f.log[5].events.some((e) => e.type === "booking" && e.booking.date_iso === "2026-10-16"));
});
ok("reschedule keeps service and name, tells the owner", () => {
  const r = talk("salon", ["book", "hair spa", "tomorrow", "4:00 PM", "Priya", "can I reschedule?", "saturday", "1"]);
  assert.match(r.log[5].bot, /current booking is Tue, 13 Oct at 4:00 PM/);
  assert.match(r.log[7].bot, /moved it[\s\S]*Hair spa[\s\S]*Sat, 17 Oct at 11:00 AM/);
  assert.ok(r.log[7].events.some((e) => e.type === "notify_owner" && /Rescheduled: Priya/.test(e.text)));
  assert.ok(r.log[7].events.some((e) => e.type === "booking" && e.replaces && e.replaces.date_iso === "2026-10-13"));
});
ok("cancel asks for confirmation first", () => {
  const r = talk("gym", ["trial", "weight loss", "tomorrow", "1", "Sai", "cancel my trial", "yes"]);
  assert.match(r.log[5].bot, /Reply \*YES\* to cancel/); assert.match(r.log[6].bot, /Cancelled/);
  assert.strictEqual(r.lead.status, "cancelled"); assert.ok(r.log[6].events.some((e) => e.type === "cancel_booking"));
  const k = talk("gym", ["trial", "weight loss", "tomorrow", "1", "Sai", "cancel", "no"]); assert.match(k.log[6].bot, /stays as it is/);
});
ok("returning customer is greeted by name with last service", () => {
  const r = talk("salon", ["hi"], { known: { name: "Priya Reddy", lastService: "Hair spa" } });
  assert.match(r.log[0].bot, /Welcome back, Priya! 😊 Same \*Hair spa\* as last time/);
});
ok("referral code in the first message is captured and the owner told", () => {
  const r = talk("salon", ["Hi! My friend gave me REF-7KQ2"]);
  assert.match(r.log[0].bot, /How can I help/); assert.strictEqual(r.lead.referred_by, "REF-7KQ2");
  assert.ok(r.log[0].events.some((e) => /Referral/.test(e.text)));
});
console.log(`\n${passed} tests passed`);

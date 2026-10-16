// A03 / M8 (P1-W2-04): bridal = enquiry flow, never a 1-hour wedding-day slot. Run: node core/bridal.test.js
// Spec: docs/requirements/salon.md A12 + test T15.
const assert = require("assert");
const { BotBhai: B, SETUPS } = require("../setups/index.js");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };
const NOW = "2026-10-12T05:30:00Z"; // Mon 12 Oct 2026, 11:00 AM IST
function talk(niche, lines, meta = {}, overrides) {
  const bot = B.createBot(Object.assign({}, SETUPS[niche], overrides || {})); let state = B.newState(); const log = []; let out;
  for (const l of lines) {
    out = bot.handle(state, l, Object.assign({ contact: "919876543210", now: NOW }, meta)); state = out.state;
    log.push({ bot: out.replies.map((r) => r.text).join("\n---\n"), events: out.events, options: (out.replies.at(-1) || {}).options, lead: out.lead });
  }
  return { log, state, lead: out.lead };
}
console.log("BotBhai bridal enquiry tests (A03 / M8)");

ok("T15: package info from the catalog, events + dates understood, budget asked, no booking", () => {
  const r = talk("salon", ["Hi, bridal makeup for wedding on 22 Jan, haldi on 20th also. Price?"]);
  const t = r.log[0].bot;
  assert.match(t, /from ₹15,000/); assert.match(t, /Wedding[^\n]*Fri, 22 Jan/); assert.match(t, /Haldi[^\n]*Wed, 20 Jan/);
  assert.match(t, /budget/i);
  assert.ok(!r.log[0].events.some((e) => e.type === "booking"));
  assert.deepStrictEqual(r.state.bridal.events.map((e) => [e.type, e.date_iso]), [["wedding", "2027-01-22"], ["haldi", "2027-01-20"]]);
  assert.strictEqual(r.state.step, -1); // the 1-hour booking flow never starts
});

ok("T15: full conversation → hot bridal lead, owner alerted with every detail, trial offered, bot not paused", () => {
  const r = talk("salon", ["Hi, bridal makeup for wedding on 22 Jan, haldi on 20th also. Price?", "around 50k budget", "Sravani"]);
  assert.match(r.log[1].bot, /name/i);
  const last = r.log[2];
  assert.ok(!last.events.some((e) => e.type === "booking"), "never a wedding-day slot");
  assert.strictEqual(r.lead.score, "hot"); assert.strictEqual(r.lead.status, "callback"); assert.ok(r.lead.intents.includes("bridal"));
  assert.strictEqual(r.lead.name, "Sravani");
  assert.strictEqual(r.lead.bridal.budget_inr, 50000); assert.strictEqual(r.lead.bridal.budget_band, "40k–75k");
  const alert = last.events.find((e) => e.type === "notify_owner");
  assert.ok(alert, "owner alert event"); assert.match(alert.text, /Bridal enquiry/); assert.match(alert.text, /Sravani/);
  assert.match(alert.text, /Wedding Fri, 22 Jan/); assert.match(alert.text, /Haldi Wed, 20 Jan/); assert.match(alert.text, /50,000/);
  assert.ok(last.events.some((e) => e.type === "bridal_enquiry" && e.enquiry.name === "Sravani"));
  assert.match(last.bot, /trial/i); assert.ok(last.options.includes("Book a bridal trial"));
  assert.ok(!r.state.humanUntil, "bot stays on so the trial can be booked");
  assert.ok(!/₹/.test(last.bot.replace("₹15,000", "")), "never echoes the customer's budget as a price");
});

ok("trial slot: 'Book a bridal trial' books a normal slot for the trial, name already known", () => {
  const r = talk("salon", ["Hi, bridal makeup for wedding on 22 Jan, haldi on 20th also. Price?", "around 50k budget", "Sravani", "Book a bridal trial", "thursday", "11:00 AM"]);
  assert.match(r.log[3].bot, /Bridal makeup trial/); assert.match(r.log[3].bot, /Which day/);
  const b = r.log[5].events.find((e) => e.type === "booking");
  assert.ok(b, "trial booked"); assert.strictEqual(b.booking.service, "Bridal makeup trial"); assert.strictEqual(b.booking.name, "Sravani");
  assert.strictEqual(b.booking.date_iso, "2026-10-15");
  assert.strictEqual(r.lead.bridal.events.length, 2, "bridal details survive the trial booking");
});

ok("menu path: book → Bridal makeup asks events, then budget, then name", () => {
  const r = talk("salon", ["book", "Bridal makeup", "wedding 5 Feb, reception 6 Feb, 4 people at venue", "not decided yet", "Priya"]);
  assert.match(r.log[1].bot, /from ₹15,000/); assert.match(r.log[1].bot, /date/i);
  assert.ok(!r.log[1].events.some((e) => e.type === "handoff"));
  assert.match(r.log[2].bot, /Wedding[^\n]*Fri, 5 Feb/); assert.match(r.log[2].bot, /Reception[^\n]*Sat, 6 Feb/); assert.match(r.log[2].bot, /budget/i);
  assert.match(r.log[3].bot, /name/i);
  assert.strictEqual(r.lead.bridal.people, 4); assert.strictEqual(r.lead.bridal.location, "venue");
  assert.strictEqual(r.lead.bridal.budget_band, "not decided");
  assert.ok(r.log[4].events.some((e) => e.type === "notify_owner" && /Priya/.test(e.text)));
});

ok("unclear event reply is asked once more, then accepted as a note (never traps the bride)", () => {
  const r = talk("salon", ["book", "Bridal makeup", "next year maybe", "still deciding", "50k", "Anu"]);
  assert.match(r.log[2].bot, /date/i);
  assert.match(r.log[3].bot, /budget/i); assert.strictEqual(r.state.bridal.note, "still deciding");
  assert.ok(r.log[5].events.some((e) => e.type === "bridal_enquiry"));
});

ok("returning customer: name not asked again", () => {
  const r = talk("salon", ["bridal makeup for my wedding on 22 Jan", "1 lakh"], { known: { name: "Divya Rao" } });
  assert.ok(r.log[1].events.some((e) => e.type === "bridal_enquiry" && e.enquiry.name === "Divya Rao"));
  assert.strictEqual(r.lead.bridal.budget_inr, 100000); assert.strictEqual(r.lead.bridal.budget_band, "75k+");
});

ok("fully committed wedding date → says so and hands to the owner for a callback", () => {
  const full = talk("salon", ["bridal makeup for wedding on 22 Jan"], {}, { bridal_full_dates: ["2027-01-22"] });
  assert.match(full.log[0].bot, /fully committed/); assert.ok(full.log[0].events.some((e) => e.type === "handoff"));
  assert.strictEqual(full.lead.status, "callback"); assert.ok(!full.state.bridal || !full.state.bridal.asking);
  const held = talk("salon", ["bridal makeup for wedding on 22 Jan"], { bridal_holds: [{ date_iso: "2027-01-22" }, { date_iso: "2027-01-22" }] }, { bridal_capacity: 2 });
  assert.match(held.log[0].bot, /fully committed/);
  const free = talk("salon", ["bridal makeup for wedding on 22 Jan"], { bridal_holds: [{ date_iso: "2027-01-22" }] }, { bridal_capacity: 2 });
  assert.doesNotMatch(free.log[0].bot, /fully committed/);
});

ok("cancel mid-enquiry stops cleanly; STOP still opts out", () => {
  const r = talk("salon", ["bridal makeup for wedding on 22 Jan", "cancel"]);
  assert.match(r.log[1].bot, /stopped/i); assert.ok(!r.state.bridal || !r.state.bridal.asking);
  const s = talk("salon", ["bridal makeup for wedding on 22 Jan", "STOP"]); assert.strictEqual(s.lead.status, "opted_out");
});

ok("setups without an enquiry item are untouched (gym 'wedding shred' is not a bridal lead)", () => {
  const r = talk("gym", ["I want to lose weight before my wedding"]);
  assert.ok(!r.state.bridal); assert.ok(!r.lead.intents.includes("bridal"));
});

ok("budget parsing: 50k, ₹40,000, 1.5 lakh, 75 thousand, none", () => {
  const P = B.parseBudget;
  assert.strictEqual(P("around 50k budget"), 50000); assert.strictEqual(P("₹40,000"), 40000); assert.strictEqual(P("1.5 lakh"), 150000);
  assert.strictEqual(P("75 thousand"), 75000); assert.strictEqual(P("not decided yet"), null); assert.strictEqual(P("around 50"), null);
});
console.log(`\n${n} bridal tests passed`);

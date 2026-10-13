// Regression tests for bugs found by the independent review agent (12 Oct 2026). Run: node core/regression.test.js
const assert = require("assert");
const { BotBhai: B } = require("../setups/index.js");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };
function talk(niche, lines, meta = {}, overrides) {
  const bot = B.createBot(niche, overrides); let state = B.newState(); const log = []; let out;
  for (const l of lines) { out = bot.handle(state, l, Object.assign({ contact: "919999999999" }, meta)); state = out.state; log.push({ bot: out.replies.map((r) => r.text).join("\n---\n"), events: out.events, options: (out.replies.at(-1) || {}).options }); }
  return { log, state, lead: out.lead, bot };
}
console.log("BotBhai regression tests (review findings)");
ok("#1 IST: at 3 PM IST, today's 11 AM and 1 PM are gone", () => {
  const r = talk("salon", ["book", "facial", "today"], { now: "2026-10-12T09:30:00Z" });
  assert.deepStrictEqual(r.log[2].options, ["4:00 PM", "7:00 PM"]); // 3 PM + 30-min buffer: 4 PM still open
});
ok("#1 IST: at 00:30 IST Tuesday, 'today' is Tuesday 13 Oct", () => {
  const r = talk("salon", ["book", "facial", "today"], { now: "2026-10-12T19:00:00Z" });
  assert.match(r.log[2].bot, /Choose a time/); assert.strictEqual(r.state.data.date_iso, "2026-10-13");
});
ok("#5 'Yes, cancel' button (sent as 1 or its text) cancels", () => {
  for (const yes of ["1", "Yes, cancel"]) {
    const r = talk("gym", ["trial", "weight loss", "tomorrow", "1", "Sai", "cancel", yes], { now: "2026-10-12T04:30:00Z" });
    assert.strictEqual(r.lead.status, "cancelled", yes);
  }
});
ok("#6 reminder replies: 1/Confirm confirms and keeps the booking; 2 reschedules", () => {
  for (const c of ["1", "Confirm"]) {
    const r = talk("salon", ["book", "hair spa", "tomorrow", "4 pm", "Priya", c], { now: "2026-10-12T04:30:00Z" });
    assert.match(r.log[5].bot, /Confirmed: Hair spa, Tue, 13 Oct at 4:00 PM/); assert.strictEqual(r.lead.status, "booked"); assert.strictEqual(r.state.data.slot, "4:00 PM");
  }
  const r = talk("salon", ["book", "hair spa", "tomorrow", "4 pm", "Priya", "2"], { now: "2026-10-12T04:30:00Z" });
  assert.match(r.log[5].bot, /current booking is Tue, 13 Oct at 4:00 PM/);
});
ok("#7 slot picked by its text, never by a shifted row number", () => {
  assert.strictEqual(B.pickChoice("1:00 PM", ["1:00 PM", "4:00 PM", "7:00 PM"]), "1:00 PM");
});
ok("#11 typed times: '1:00' is not 11:00, ambiguous '4' asks, '4pm', 'evening'", () => {
  const S = ["11:00 AM", "1:00 PM", "4:00 PM", "7:00 PM"];
  assert.strictEqual(B.pickChoice("1:00", S), "1:00 PM");
  const r = talk("salon", ["book", "facial", "tomorrow", "4", "4:00 PM"], { now: "2026-10-12T04:30:00Z" });
  assert.match(r.log[3].bot, /Just to check: 4:00 PM or 7:00 PM\?/); assert.match(r.log[4].bot, /Your name/);
  assert.strictEqual(B.pickChoice("4pm", S), "4:00 PM"); assert.strictEqual(B.pickChoice("evening", S), "7:00 PM");
  assert.strictEqual(B.pickChoice("2", S), "1:00 PM"); // a small number is still a row number
});
ok("#10 abandoning a reschedule keeps the original booking", () => {
  const r = talk("salon", ["book", "hair spa", "tomorrow", "4 pm", "Priya", "reschedule", "20/10", "cancel"], { now: "2026-10-12T04:30:00Z" });
  assert.strictEqual(r.state.data.date_iso, "2026-10-13"); assert.strictEqual(r.state.data.slot, "4:00 PM"); assert.strictEqual(r.lead.status, "booked");
  const r2 = talk("salon", ["book", "hair spa", "tomorrow", "4 pm", "Priya", "book", "cancel", "cancel"], { now: "2026-10-12T04:30:00Z" });
  assert.match(r2.log[7].bot, /cancel your Hair spa on Tue, 13 Oct at 4:00 PM/);
});
ok("#15 past dates with a year are refused; holidays and closed days are refused", () => {
  const r = talk("salon", ["book", "facial", "10/10/2026", "8/11"], { now: "2026-10-12T04:30:00Z" });
  assert.match(r.log[2].bot, /already gone/); assert.match(r.log[3].bot, /closed for Diwali/);
  const c = talk("salon", ["book", "facial", "sunday"], { now: "2026-10-12T04:30:00Z" }, { closed_weekdays: [0] });
  assert.match(c.log[2].bot, /closed on Sundays/);
});
ok("late evening: 'today' says slots are over, not 'fully booked'", () => {
  const r = talk("salon", ["book", "facial", "today"], { now: "2026-10-12T15:30:00Z" }); // 9 PM IST
  assert.match(r.log[2].bot, /Today's slots are over/);
});
ok("BA: Tenglish/Hinglish understood and pre-filled ('repu hair spa kavali', 'kitna hai facial')", () => {
  const r = talk("salon", ["repu hair spa kavali"], { now: "2026-10-12T04:30:00Z" });
  assert.match(r.log[0].bot, /Sure! Hair spa, Tue, 13 Oct/); assert.match(r.log[0].bot, /Choose a time/);
  assert.match(talk("salon", ["facial kitna hai"]).log[0].bot, /Price list/);
  assert.match(talk("salon", ["హాయ్"]).log[0].bot, /How can I help/);
});
ok("BA: 'home visit' answers the home-service FAQ instead of booking", () => {
  assert.match(talk("salon", ["do you do home visit?"]).log[0].bot, /Home service is available/);
});
ok("BA: bridal makeup is an enquiry → owner handoff, bot pauses, 'bot' resumes", () => {
  const r = talk("salon", ["book", "bridal makeup", "is the trial included?", "bot"], { now: "2026-10-12T04:30:00Z" });
  assert.match(r.log[1].bot, /quick chat with our bridal artist/); assert.ok(r.log[1].events.some((e) => e.type === "handoff"));
  assert.strictEqual(r.log[2].bot, ""); assert.ok(r.log[2].events.some((e) => e.type === "forward_to_owner"));
  assert.match(r.log[3].bot, /How can I help/);
});
ok("BA: returning customer is not asked their name again", () => {
  const r = talk("salon", ["book", "facial", "tomorrow", "4 pm"], { now: "2026-10-12T04:30:00Z", known: { name: "Priya Reddy" } });
  assert.match(r.log[3].bot, /Booking confirmed[\s\S]*Priya Reddy/);
});
ok("BA: marketing opt-in is explicit (OFFERS) and STOP clears it", () => {
  const r = talk("salon", ["book", "facial", "tomorrow", "4 pm", "Asha", "OFFERS"], { now: "2026-10-12T04:30:00Z" });
  assert.match(r.log[4].bot, /Reply \*OFFERS\*/); assert.strictEqual(r.lead.marketing_opt_in, true);
  const s = talk("salon", ["offers", "stop"]); assert.strictEqual(s.lead.marketing_opt_in, false); assert.ok(s.log[1].events.some((e) => e.type === "opt_out"));
});
ok("race: slotTaken re-offers the remaining slots", () => {
  const r = talk("salon", ["book", "facial", "tomorrow", "4 pm", "Asha"], { now: "2026-10-12T04:30:00Z" });
  const back = r.bot.slotTaken(r.state);
  assert.match(back.replies[0].text, /someone grabbed 4:00 PM/); assert.ok(!back.replies[1].options.includes("4:00 PM"));
  assert.notStrictEqual(back.state.lead.status, "booked");
});
console.log(`\n${n} tests passed`);

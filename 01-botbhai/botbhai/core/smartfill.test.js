// Run: node core/smartfill.test.js — people type everything in one line, or answer out of order (A69, 20 Oct 2026).
const assert = require("assert");
const { BotBhai: B } = require("../setups/index.js");
const NOW = "2026-10-20T06:30:00.000Z"; // Tue 20 Oct 2026, 12:00 PM IST
let passed = 0;
function talk(niche, lines) {
  const bot = B.createBot(niche); let state = B.newState(); let out; const said = [];
  for (const l of lines) { out = bot.handle(state, l, { now: NOW, contact: "+919999999999", profileName: "Test" }); state = out.state; said.push(out.replies.map((r) => r.text).join("\n")); }
  return { state, said, last: said[said.length - 1], out };
}
function ok(name, fn) { fn(); passed++; console.log("  ✓ " + name); }

ok("one line with service + day + time starts the booking with all three filled", () => {
  const r = talk("salon", ["haircut men repu 7pm"]);
  assert.strictEqual(r.state.data.service, "Haircut (men)");
  assert.strictEqual(r.state.data.date_iso, "2026-10-21");
  assert.match(r.state.data.slot, /^7:00 PM/);
  assert.match(r.last, /name|peru/i); // only the name is left ("repu" makes it Tenglish)
  assert.doesNotMatch(r.last, /didn't quite get/);
});
ok("a service word alone (no 'book') starts a booking instead of 'didn't get that'", () => {
  const r = talk("salon", ["beard trim"]);
  assert.strictEqual(r.state.data.service, "Beard trim");
  assert.ok(r.state.step >= 0);
  assert.doesNotMatch(r.last, /didn't quite get/);
});
ok("a day typed while the service is being asked is kept, and the service is asked again", () => {
  const r = talk("salon", ["book", "repu"]);
  assert.strictEqual(r.state.data.date_iso, "2026-10-21");
  assert.match(r.last, /Which service|Meeku ye service kavali/);
  assert.doesNotMatch(r.last, /Please choose one of the options/);
});
ok("a time typed early is used once the day is known", () => {
  const r = talk("salon", ["book hair spa 4pm", "repu"]);
  assert.strictEqual(r.state.data.service, "Hair spa");
  assert.strictEqual(r.state.data.date_iso, "2026-10-21");
  assert.match(r.state.data.slot || "", /^4:00 PM/);
});
ok("a time that isn't free is never guessed: it says so and shows the free times", () => {
  const r = talk("salon", ["haircut men repu 6pm"]);
  assert.strictEqual(r.state.data.slot, undefined);
  assert.match(r.last, /Aa roju 6 PM free ledu/); // Tenglish in ("repu"), Tenglish out
  assert.match(r.last, /Time choose cheyyandi/);
});
ok("questions and greetings are not mistaken for a booking", () => {
  assert.match(talk("salon", ["haircut price entha?"]).last, /Price list[\s\S]*Book cheyyadaniki/);
  assert.match(talk("salon", ["hi"]).last, /How can I help/);
  assert.strictEqual(talk("salon", ["timings?"]).state.step, -1);
});
ok("works for the other businesses too (gym goal + day)", () => {
  const r = talk("gym", ["weight loss trial tomorrow"]);
  assert.ok(r.state.step >= 0);
  assert.strictEqual(r.state.data.date_iso, "2026-10-21");
});
console.log(`smart-fill tests passed (${passed})`);

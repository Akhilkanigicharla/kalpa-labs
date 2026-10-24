// A time that isn't free gets a polite, honest answer with the nearest free times (Akhil's test, 24 Oct 2026)
const assert = require("assert");
const { BotBhai: B } = require("../setups/index.js");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };
const NOW = "2026-10-24T08:00:00Z"; // Sat 1:30 PM IST; "tomorrow" = Sun 25 Oct
function talk(lines, busy) {
  const bot = B.createBot("salon"); let st = B.newState(); let out;
  for (const l of lines) { out = bot.handle(st, l, { contact: "919999999999", now: NOW, busy: busy || [] }); st = out.state; }
  return { text: out.replies.map((r) => r.text).join("\n"), st };
}
console.log("Slot advice tests");
ok("6 PM is not a slot: says so and names 4 PM / 7 PM", () => {
  const r = talk(["hair spa tomorrow 6pm"]);
  assert.match(r.text, /We don't have a 6 PM slot 🙏 Closest free: 4:00 PM or 7:00 PM\./);
  assert.strictEqual(r.st.data.slot, undefined);
});
ok("typing 6pm again at the time step gets the same help, not 'choose one of the options'", () => {
  const r = talk(["hair spa tomorrow 6pm", "6pm"]);
  assert.match(r.text, /Closest free: 4:00 PM or 7:00 PM/); assert.doesNotMatch(r.text, /choose one of the options/i);
});
ok("8 PM: too late, says the last booking and the opening hours", () => {
  assert.match(talk(["hair spa tomorrow 8pm"]).text, /8 PM is too late for us\. Our last booking is 7:00 PM \(Every day 10:00 AM – 9:00 PM\)/);
});
ok("9 AM: too early, says the first booking", () => {
  assert.match(talk(["hair spa tomorrow 9am"]).text, /9 AM is too early for us\. Our first booking is 11:00 AM/);
});
ok("7 PM already booked: says booked and offers 4 PM", () => {
  const r = talk(["hair spa tomorrow 7pm"], Array.from({ length: 9 }, () => ({ date_iso: "2026-10-25", slot: "7:00 PM" })));
  assert.match(r.text, /Sorry, 7 PM is already booked that day 🙏 Closest free: (1:00 PM or )?4:00 PM/);
});
ok("Telugu and Hindi script get their own polite line", () => {
  const te = talk(["తెలుగు", "రేపు హెయిర్ స్పా సాయంత్రం 6pm"]).text, hi = talk(["हिंदी", "कल हेयर स्पा 6pm"]).text;
  assert.match(te + hi, /దగ్గరలో ఖాళీ|सबसे पास खाली/);
});
console.log(`${n} slot advice tests passed`);

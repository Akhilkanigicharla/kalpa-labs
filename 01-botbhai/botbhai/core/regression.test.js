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
  assert.match(talk("salon", ["హాయ్"]).log[0].bot, /మీకు ఎలా సహాయం చేయగలను/); // A73: Telugu in, Telugu out
});
ok("BA: 'home visit' answers the home-service FAQ instead of booking", () => {
  assert.match(talk("salon", ["do you do home visit?"]).log[0].bot, /Home service is available/);
});
ok("BA: bridal makeup is an enquiry (A03) → details, owner alert; 'talk to the artist' pauses the bot, 'bot' resumes", () => {
  const r = talk("salon", ["book", "bridal makeup", "wedding 22 jan", "50k", "Asha", "Talk to the artist", "is the trial included?", "bot"], { now: "2026-10-12T04:30:00Z" });
  assert.match(r.log[1].bot, /from ₹15,000/); assert.ok(!r.log.some((l) => l.events.some((e) => e.type === "booking")));
  assert.ok(r.log[4].events.some((e) => e.type === "notify_owner" && /Bridal enquiry/.test(e.text)));
  assert.ok(r.log[5].events.some((e) => e.type === "handoff"));
  assert.strictEqual(r.log[6].bot, ""); assert.ok(r.log[6].events.some((e) => e.type === "forward_to_owner"));
  assert.match(r.log[7].bot, /How can I help/);
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
ok("deep-scan-v2: 'hair cut kavali' never books Hair spa (split word joined first)", () => {
  const r = talk("salon", ["repu slot undi aa? hair cut kavali"], { now: "2026-10-13T05:00:00Z" });
  assert.ok(!/Sure! Hair spa/.test(r.log[0].bot)); assert.notStrictEqual(r.state.data.service, "Hair spa");
  assert.strictEqual(B.pickChoice("hair spa", ["Haircut (men)", "Hair spa"]), "Hair spa");
  assert.strictEqual(B.pickChoice("hair cut men", ["Haircut (men)", "Haircut & styling (women)", "Hair spa"]), "Haircut (men)");
});
// A01 (13 Oct 2026): MUST-list audit against docs/requirements/salon.md
const NOW = { now: "2026-10-12T04:30:00Z" }; const BOOKED = ["book", "hair spa", "tomorrow", "4 pm", "Priya"];
ok("A01 M1: reminder replies yes / sare / haan / ok / సరే / हाँ confirm the booking (and never count as offers consent)", () => {
  for (const w of ["yes", "Yes", "sare", "haan", "ok", "avunu", "సరే", "हाँ", "vastanu"]) {
    const r = talk("salon", [...BOOKED, w], NOW);
    const want = w === "సరే" ? /కన్ఫర్మ్ అయింది: హెయిర్ స్పా, మంగళ, 13 అక్టోబర్, 4:00 PM/ : w === "हाँ" ? /पक्का हो गया: हेयर स्पा, मंगल, 13 अक्टूबर, 4:00 PM/ : /Confirmed: Hair spa, Tue, 13 Oct at 4:00 PM/; // A73: reply in the language they wrote
    assert.match(r.log[5].bot, want, w); assert.ok(r.log[5].events.some((e) => e.type === "confirmed"), w);
    assert.strictEqual(r.lead.status, "booked"); assert.strictEqual(r.lead.marketing_opt_in, false, w);
  }
  const later = talk("salon", [...BOOKED, "menu", "sare"], NOW); // reminder arrives after other chat
  assert.match(later.log[6].bot, /Confirmed: Hair spa/);
  const past = talk("salon", [...BOOKED], NOW); const bot = B.createBot("salon"); past.state.now = "2026-10-15T04:30:00Z";
  const out = bot.handle(past.state, "yes", { contact: "919999999999", now: "2026-10-15T04:30:00Z" });
  assert.ok(!out.events.some((e) => e.type === "confirmed")); // a visit that is over is not "confirmed"
});
ok("A01 M5: day parts in English, Tenglish, Telugu and Hindi pick the right slot", () => {
  const S = ["11:00 AM", "1:00 PM", "4:00 PM", "7:00 PM"];
  for (const [w, want] of [["sayantram", "7:00 PM"], ["సాయంత్రం", "7:00 PM"], ["शाम को", "7:00 PM"], ["madhyanam", "1:00 PM"], ["మధ్యాహ్నం", "1:00 PM"], ["poddune", "11:00 AM"], ["ఉదయం", "11:00 AM"], ["4pm", "4:00 PM"], ["4 pm", "4:00 PM"]])
    assert.strictEqual(B.pickChoice(w, S), want, w);
  const r = talk("salon", ["book", "facial", "tomorrow", "sayantram", "Asha"], NOW);
  assert.match(r.log[4].bot, /Booking confirmed[\s\S]*7:00 PM/);
});
ok("A01 M6: 'ladies cut' / 'gents cut' pick the right haircut; 'cutting' and 'hair cut' ask men or women", () => {
  assert.strictEqual(talk("salon", ["book", "ladies cut"], NOW).state.data.service, "Haircut & styling (women)");
  assert.strictEqual(talk("salon", ["book", "gents cutting"], NOW).state.data.service, "Haircut (men)");
  assert.strictEqual(talk("salon", ["book", "shave"], NOW).state.data.service, "Beard trim");
  for (const w of ["cutting", "hair cut", "hair cutting"]) {
    const r = talk("salon", ["book", w, "2"], NOW);
    assert.match(r.log[1].bot, /Did you mean Haircut \(men\) or Haircut & styling \(women\)\?/, w);
    assert.strictEqual(r.state.data.service, "Haircut & styling (women)", w);
  }
  const pre = talk("salon", ["repu ladies cut kavali"], NOW); // first message: service understood straight away
  assert.match(pre.log[0].bot, /Sure! Haircut & styling \(women\), Tue, 13 Oct/);
});
ok("A01 M12: Telugu-script and Hindi greetings get the welcome menu", () => {
  for (const w of ["హాయ్", "హలో", "నమస్తే", "నమస్కారం", "नमस्ते", "namasthe"]) assert.match(talk("salon", [w]).log[0].bot, /[\u0C00-\u0C7F]/.test(w) ? /మీకు ఎలా సహాయం చేయగలను/ : /[\u0900-\u097F]/.test(w) ? /मैं कैसे मदद करूँ/ : /How can I help/, w); // A73
});
ok("A01 M14: 'intiki vastara?' / 'can you come home' answer the home-service FAQ", () => {
  for (const w of ["intiki vastara?", "can you come home", "ghar pe aa sakte ho"]) assert.match(talk("salon", [w]).log[0].bot, /Home service is available/, w);
});
// A02b (13 Oct 2026): NLU gaps from Deep Scan v2
ok("A02b: Telugu-script booking words (with or without the zero-width joiner) start a booking", () => {
  for (const w of ["రేపు అపాయింట్‌మెంట్ కావాలి", "రేపు అపాయింట్మెంట్ కావాలి", "స్లాట్ బుక్ చేయండి"]) assert.match(talk("salon", [w], NOW).log[0].bot, /మీకు ఏ సర్వీస్ కావాలి/, w); // A73: asked in Telugu
  const r = talk("salon", ["రేపు ఫేషియల్ బుక్ చేయండి"], NOW);
  assert.match(r.log[0].bot, /సరే! ఫేషియల్ \(ఫ్రూట్ \/ గోల్డ్\), మంగళ, 13 అక్టోబర్/); assert.match(r.log[0].bot, /సమయం ఎంచుకోండి/); // A73
});
ok("A02b: 'cancel' with nothing booked says so (never starts a booking); inside a flow it stops the flow", () => {
  for (const w of ["booking cancel cheyyandi", "cancel it please", "cancel", "నా బుకింగ్ రద్దు చేయండి"]) {
    const r = talk("salon", [w], NOW);
    assert.match(r.log[0].bot, /[\u0C00-\u0C7F]/.test(w) ? /క్యాన్సిల్ చేయడానికి ఏమీ లేదు/ : /nothing to cancel/, w); assert.strictEqual(r.state.step, -1, w); assert.ok(!r.log[0].events.some((e) => e.type === "cancel_booking"), w);
  }
  const mid = talk("salon", ["book", "facial", "cancel it please"], NOW);
  assert.match(mid.log[2].bot, /stopped\. Nothing was changed/); assert.strictEqual(mid.state.step, -1);
  const booked = talk("salon", [...BOOKED, "booking cancel cheyyandi", "yes"], NOW); // with a booking it still asks, then cancels
  assert.match(booked.log[5].bot, /Do you want to cancel your Hair spa/); assert.strictEqual(booked.lead.status, "cancelled");
});
ok("A02b: the service named in the first message is used ('I want to book a facial')", () => {
  const r = talk("salon", ["I want to book a facial"], NOW);
  assert.match(r.log[0].bot, /Sure! Facial \(fruit \/ gold\)/); assert.match(r.log[0].bot, /Which day/);
  assert.match(talk("salon", ["I want to book a hair cut"], NOW).log[0].bot, /Which service/); // still ambiguous → asks
});
ok("A02b: a question mid-booking is answered, then the same step is asked again (digression)", () => {
  const r = talk("salon", ["book", "facial", "address?", "tomorrow", "price entha?", "4 pm", "timings?", "Asha"], NOW);
  assert.match(r.log[2].bot, /Jubilee Hills[\s\S]*---[\s\S]*Which day/); assert.strictEqual(r.state.data.date_iso, "2026-10-13");
  assert.match(r.log[4].bot, /Price list[\s\S]*Choose a time/);
  assert.match(r.log[6].bot, /10:00 AM[\s\S]*Your name/);
  assert.match(r.log[7].bot, /Booking confirmed[\s\S]*Asha[\s\S]*4:00 PM/);
  const home = talk("salon", ["book", "do you do home visit?"], NOW);
  assert.match(home.log[1].bot, /Home service is available[\s\S]*Which service/);
  assert.match(talk("salon", ["book", "facial", "tomorrow", "4 pm", "Priya"], NOW).log[4].bot, /Booking confirmed[\s\S]*Priya/); // names are never questions
});
console.log(`\n${n} tests passed`);

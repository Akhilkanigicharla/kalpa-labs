/*
 * QA test-agent swarm. Run: node qa/swarm.test.js   (no network, deterministic)
 *
 * 1. Scripted conversations T01–T25 written by the BA agent (docs/requirements/salon.md §5).
 * 2. 50 synthetic customer personas × 4 setups × 3 runs = 600 random conversations
 *    (typos, Tenglish/Hinglish, Telugu script, emoji, anger, reschedulers, menu tappers, spam).
 * Every turn of every conversation is checked against invariants a salon owner cares about.
 */
const assert = require("assert");
const { BotBhai: B, SETUPS } = require("../setups/index.js");
const H = require("../core/humanize.js");

const NOW = "2026-10-12T05:30:00.000Z"; // Mon 12 Oct 2026, 11:00 AM IST
const FIX = { closed_weekdays: [2], holidays: [{ date: "2026-11-08", name: "Diwali" }], capacity: 2, review_link: "https://g.page/r/test" };

// ---------------------------------------------------------------- invariants
function allowedRupees(cfg) {
  const txt = JSON.stringify(cfg.catalog) + JSON.stringify(cfg.steps) + JSON.stringify(cfg.quizBank || {}) + JSON.stringify(cfg.faqs) + JSON.stringify(cfg.confirm || "") + JSON.stringify(cfg.greeting || "");
  return new Set((txt.match(/₹\s?[\d,]+(?:\.\d+)?L?/g) || []).map((x) => x.replace(/\s/g, "")));
}
function checkTurn(cfg, out, ctx) {
  const where = `${ctx.setup}/${ctx.persona} turn ${ctx.turn} "${ctx.input}"`;
  for (const r of out.replies) {
    assert.ok(typeof r.text === "string" && r.text.trim().length, `empty reply at ${where}`);
    assert.ok(!/undefined|NaN|\[object Object\]|\{(name|date|slot|service|business|phone)\}/.test(r.text), `broken text at ${where}: ${r.text.slice(0, 120)}`);
    if (r.options) {
      assert.ok(r.options.length <= 10, `>10 options at ${where}`);
      assert.ok(r.text.length <= 1024, `interactive body >1024 chars at ${where}`);
      assert.strictEqual(new Set(r.options).size, r.options.length, `duplicate options at ${where}`);
    } else assert.ok(r.text.length <= 4096, `text >4096 at ${where}`);
    for (const amt of r.text.match(/₹\s?[\d,]+(?:\.\d+)?L?/g) || []) assert.ok(ctx.rupees.has(amt.replace(/\s/g, "")), `invented price ${amt} at ${where}`);
  }
  const s = out.state;
  assert.ok(s.step >= -1 && s.step < cfg.steps.length, `bad step ${s.step} at ${where}`);
  if (s.optedOut && ctx.prevOptedOut && !/^start$/i.test(ctx.input.trim())) assert.strictEqual(out.replies.length, 0, `messaged an opted-out customer at ${where}`);
  for (const e of out.events.filter((x) => x.type === "booking")) {
    const today = "2026-10-12";
    assert.ok(e.booking.date_iso >= today, `booking in the past at ${where}`);
    const d = new Date(e.booking.date_iso + "T00:00:00Z");
    assert.ok(!(cfg.closed_weekdays || []).includes(d.getUTCDay()), `booked a closed weekday at ${where}`);
    assert.ok(!(cfg.holidays || []).some((h) => h.date === e.booking.date_iso), `booked a holiday at ${where}`);
    const cap = cfg.capacity || Infinity;
    assert.ok((ctx.busy || []).filter((b) => b.date_iso === e.booking.date_iso && b.slot === e.booking.slot).length < cap, `overbooked slot at ${where}`);
    assert.ok(e.booking.slot && e.booking.name, `incomplete booking at ${where}`);
  }
}
function run(setup, lines, opts = {}) {
  const cfg = Object.assign({}, SETUPS[setup], FIX, opts.overrides || {});
  const bot = B.createBot(cfg); let state = B.newState(); const log = [];
  const rupees = allowedRupees(cfg);
  lines.forEach((input, i) => {
    const prevOptedOut = state.optedOut;
    const out = bot.handle(state, input, Object.assign({ now: opts.now || NOW, contact: "919876543210", busy: opts.busy || [] }, opts.meta || {}));
    checkTurn(cfg, out, { setup, persona: opts.persona || "script", turn: i + 1, input, rupees, busy: opts.busy, prevOptedOut });
    const hum = H.humanize(out.replies, { setup, business: cfg.business, firstContact: i === 0, userText: input, contact: "9198", turn: i + 1, nowMs: Date.parse(opts.now || NOW) });
    log.push({ input, bot: out.replies.map((r) => r.text).join("\n---\n"), human: hum, options: (out.replies.at(-1) || {}).options, events: out.events });
    state = out.state;
  });
  return { log, state, cfg };
}

let passed = 0, total = 0; const failures = [];
function T(id, name, fn) { total++; try { fn(); passed++; console.log(`  ✓ ${id} ${name}`); } catch (e) { failures.push(`${id} ${name}: ${e.message.split("\n")[0]}`); console.log(`  ✗ ${id} ${name}\n      ${e.message.split("\n")[0]}`); } }

console.log("QA swarm — scripted conversations (BA agent, salon)");
T("T01", "numbers only; Tuesday is the weekly off → offers another day", () => {
  const r = run("salon", ["hi", "1", "4", "tomorrow", "wednesday", "3", "ravi kumar"]);
  assert.match(r.log[3].bot, /closed on Tuesdays/); assert.match(r.log[6].bot, /Booking confirmed[\s\S]*Hair spa[\s\S]*Wed, 14 Oct at 4:00 PM/);
});
T("T02", "Tenglish: 'repu evening haircut kavali' understood, asks men/women", () => {
  const r = run("salon", ["hi", "thursday evening haircut kavali"]);
  assert.match(r.log[1].bot, /Thu, 15 Oct/); assert.match(r.log[1].bot, /Which service/); assert.ok(!r.state.data.service, "must not guess men/women");
});
T("T03", "Hinglish price question gets prices", () => { assert.match(run("salon", ["bhai facial kitna hai?"]).log[0].bot, /₹999/); });
T("T04", "typos: 'boook', 'hair cut', 'tmrw', '4pm'", () => {
  const r = run("salon", ["hii", "boook", "hair cut", "Haircut (men)", "thursday", "4pm", "Keerthana"]);
  assert.match(r.log[1].bot, /Which service/); assert.match(r.log[2].bot, /Did you mean Haircut \(men\) or Haircut & styling \(women\)/);
  assert.match(r.log[6].bot, /Booking confirmed[\s\S]*Haircut \(men\)[\s\S]*4:00 PM/);
});
T("T05", "bare '4' as a time asks to clarify (never silently 7 PM)", () => {
  const r = run("salon", ["book", "facial", "saturday", "4"]); assert.match(r.log[3].bot, /Just to check: 4:00 PM or 7:00 PM/);
});
T("T06", "reminder Confirm / 1 / sare confirm without restarting", () => {
  for (const c of ["Confirm", "1", "vasthanu"]) {
    const r = run("salon", ["book", "facial", "thursday", "4 pm", "Anu", c]);
    assert.match(r.log[5].bot, /Confirmed: Facial/); assert.ok(r.log[5].events.some((e) => e.type === "confirmed"));
  }
});
T("T08", "reschedule from reminder", () => {
  const r = run("salon", ["book", "facial", "thursday", "4 pm", "Anu", "Reschedule", "friday", "1:00 PM"]);
  assert.match(r.log[7].bot, /moved it[\s\S]*Fri, 16 Oct at 1:00 PM/);
});
T("T09", "Tenglish reschedule 'time marchali, ellundi ki' takes the date", () => {
  const r = run("salon", ["book", "facial", "thursday", "4 pm", "Anu", "time marchali, ellundi ki"]);
  assert.match(r.log[5].bot, /current booking[\s\S]*Choose a time/); assert.strictEqual(r.state.data.date_iso, "2026-10-14");
});
T("T10", "cancel with Telugu yes", () => { const r = run("salon", ["book", "facial", "thursday", "4 pm", "Anu", "cancel", "avunu"]); assert.match(r.log[6].bot, /Cancelled/); });
T("T11", "late evening: today's slots are over", () => {
  assert.match(run("salon", ["book", "facial", "today"], { now: "2026-10-12T15:15:00Z" }).log[2].bot, /Today's slots are over/);
});
T("T12", "6 PM IST: only 7 PM offered today", () => {
  assert.deepStrictEqual(run("salon", ["book", "facial", "today"], { now: "2026-10-12T12:30:00Z" }).log[2].options, ["7:00 PM"]);
});
T("T13", "closed weekday refused", () => { assert.match(run("salon", ["book", "facial", "tuesday"]).log[2].bot, /closed on Tuesdays/); });
T("T14", "Diwali refused", () => { assert.match(run("salon", ["book", "facial", "8/11"]).log[2].bot, /closed for Diwali/); });
T("T15", "bridal = enquiry + handoff, never a 1-hour slot", () => {
  const r = run("salon", ["book", "Bridal makeup"]); assert.match(r.log[1].bot, /bridal artist/); assert.ok(!r.log[1].events.some((e) => e.type === "booking"));
});
T("T16", "haggling: fixed prices, real offer only", () => {
  const r = run("salon", ["facial 999 too much, 600 ki chestara?"]); assert.match(r.log[0].bot, /prices are fixed/); assert.match(r.log[0].bot, /20% off facials/);
});
T("T17", "angry customer: apology only + handoff", () => {
  const r = run("salon", ["worst service, waiting since 30 min, no one picking phone"]);
  assert.ok(r.log[0].human.handoff); assert.strictEqual(r.log[0].human.replies.length, 1); assert.match(r.log[0].human.replies[0].text, /sorry/i);
});
T("T18", "angry in Telugu/Hindi", () => { for (const t of ["chala chetha service, refund kavali", "bakwas service yaar"]) assert.ok(run("salon", [t]).log[0].human.handoff, t); });
T("T19", "booking for a friend stores the friend's name", () => {
  const r = run("salon", ["book", "facial", "saturday", "11:00 AM", "for my friend Priya"]);
  assert.match(r.log[4].bot, /👤 Priya\n/); assert.ok(r.state.data.booked_for_someone);
});
T("T21", "capacity full: 11 AM hidden", () => {
  const busy = [{ date_iso: "2026-10-17", slot: "11:00 AM" }, { date_iso: "2026-10-17", slot: "11:00 AM" }];
  assert.ok(!run("salon", ["book", "facial", "saturday"], { busy }).log[2].options.includes("11:00 AM"));
});
T("T22", "home visit → FAQ", () => { assert.match(run("salon", ["home visit possible?"]).log[0].bot, /Home service/); });
T("T23", "Telugu script greetings", () => { const r = run("salon", ["హాయ్", "నమస్కారం"]); assert.match(r.log[0].bot, /How can I help/); assert.match(r.log[1].bot, /How can I help/); });
T("T24", "STOP, silence, START", () => { const r = run("salon", ["STOP", "hi", "START"]); assert.strictEqual(r.log[1].bot, ""); assert.match(r.log[2].bot, /How can I help/); });
T("T25", "referral + talk to owner pauses the bot", () => {
  const r = run("salon", ["Hi REF-7KQ2 my friend said you are good", "talk to owner", "hello?? anyone"]);
  assert.strictEqual(r.state.data.referred_by, "REF-7KQ2"); assert.ok(r.log[1].events.some((e) => e.type === "handoff"));
  assert.strictEqual(r.log[2].bot, ""); assert.ok(r.log[2].events.some((e) => e.type === "forward_to_owner"));
});

// ---------------------------------------------------------------- persona fuzz swarm
let seed = 20261012; const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const pick = (a) => a[Math.floor(rnd() * a.length)];
const POOL = {
  greet: ["hi", "Hii", "hello", "namaste", "హాయ్", "hey!!", "gm", "Good evening", "hai", "हाय"],
  book: ["book", "boook", "appointment kavali", "slot chahiye", "I want to book", "book cheyyi", "1", "Book a service", "trial", "quiz"],
  date: ["today", "tomorrow", "repu", "kal", "saturday", "next monday", "15/10", "20-10-2026", "5 nov", "8/11", "tuesday", "yesterday", "32/13", "ellundi", "రేపు"],
  time: ["1", "2", "3", "4", "4pm", "7:00 PM", "evening", "morning", "11", "1:00", "noon?", "9 am"],
  name: ["Ravi", "priya reddy", "My name is Anil", "for my friend Sita", "Lakshmi garu", "R", "12345", "Shaik Imran"],
  noise: ["?", "👍", "ok", "price", "timings", "where", "kitna", "entha", "cancel", "reschedule", "STOP", "START", "menu", "human", "worst service", "asdfgh", "REF-AB12", "offers", "home visit", "emi on loan", "ladies batch", "refund", "1", "2", "3", "", "      "],
};
const PERSONAS = [];
for (let i = 0; i < 50; i++) {
  const kind = i % 5;
  PERSONAS.push({ id: `P${String(i + 1).padStart(2, "0")}-${["booker", "browser", "chaotic", "rescheduler", "silent-quitter"][kind]}`, kind });
}
function script(kind, cfg) {
  const steps = [pick(POOL.greet)];
  const choiceStep = () => { const c = cfg.steps.find((s) => s.choices); const list = c ? (c.choices === "catalog" ? cfg.catalog.map((x) => x.name) : c.choices) : ["1"]; return rnd() < 0.5 ? pick(list) : String(1 + Math.floor(rnd() * list.length)); };
  if (kind === 0 || kind === 3) {
    steps.push(pick(POOL.book));
    for (const s of cfg.steps) steps.push(s.type === "date" ? pick(POOL.date) : s.type === "name" ? pick(POOL.name) : s.field === "slot" ? pick(POOL.time) : s.type === "quiz" ? pick(["A", "b", "C", "d", "1"]) : s.choices ? choiceStep() : pick(["Kollur", "Gachibowli", "Tellapur"]));
    if (kind === 3) steps.push(pick(["reschedule", "2", "cancel", "Confirm"]), pick(POOL.date), pick(POOL.time), pick(["yes", "no", "1"]));
  } else for (let k = 0; k < 6 + Math.floor(rnd() * 8); k++) steps.push(kind === 2 ? pick([].concat(POOL.noise, POOL.date, POOL.time, POOL.greet)) : kind === 4 ? pick(["book", "1", "cancel", "hi"]) : pick(POOL.noise));
  return steps;
}
console.log("\nQA swarm — 50 personas × 4 setups × 3 runs (invariants on every turn)");
let convos = 0, turns = 0;
for (const setup of Object.keys(SETUPS)) {
  let ok = 0;
  for (let rep = 0; rep < 3; rep++) for (const p of PERSONAS) {
    const cfg = Object.assign({}, SETUPS[setup], FIX);
    const lines = script(p.kind, cfg);
    const busy = rnd() < 0.3 ? [{ date_iso: "2026-10-13", slot: (cfg.steps.find((s) => s.field === "slot") || { choices: ["x"] }).choices[0] }, { date_iso: "2026-10-13", slot: (cfg.steps.find((s) => s.field === "slot") || { choices: ["x"] }).choices[0] }] : [];
    total++; convos++; turns += lines.length;
    try { run(setup, lines, { persona: p.id, busy }); ok++; passed++; }
    catch (e) { failures.push(`${setup}/${p.id}: ${e.message.split("\n")[0]} | script: ${JSON.stringify(lines)}`); }
  }
  console.log(`  ${ok === 150 ? "✓" : "✗"} ${setup}: ${ok}/150 conversations passed every invariant`);
}
console.log(`\n${convos} synthetic conversations, ${turns} turns checked.`);
if (failures.length) { console.log(`\n${failures.length} FAILURES:\n` + failures.slice(0, 15).map((f) => "  - " + f).join("\n")); process.exit(1); }
console.log(`${passed}/${total} QA checks passed`);

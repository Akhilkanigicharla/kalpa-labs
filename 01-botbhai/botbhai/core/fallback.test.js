// A74 · AI fallback: guard, engine hand-back and the saved live run (30 messages, Groq free model via n8n).
// Run: node core/fallback.test.js   (no network; the live answers are saved in fallback.live.json)
const assert = require("assert");
const { BotBhai: B } = require("../setups/index.js");
const F = require("./fallback.js");
const NOW = "2026-10-12T04:30:00.000Z";
let passed = 0;
const ok = async (name, fn) => { await fn(); passed++; console.log("  ✓", name); };
const bot = B.createBot("salon"); const cfg = bot.config;
const meta = { now: NOW, contact: "+919999999999" };
// The engine result rescue() receives when the rules logged a miss (some test lines are caught by rules today).
const miss = (text) => ({ replies: [{ text: "menu" }], state: B.newState(), lead: null, events: [{ type: "unanswered", text }] });
const PRICES = new Set(cfg.catalog.map((c) => c.price));
const MONEY = /₹\s?[\d,]+/g;

(async () => {
  console.log("BotBhai AI fallback tests");
  await ok("prompt carries only the message, the setup's services and FAQ keywords (no prices, no contact)", () => {
    const r = F.request(cfg, "parking unda +919876543210 ".repeat(40));
    assert.ok(r.user.length <= 500);
    assert.ok(!/₹/.test(r.system) && !r.system.includes(cfg.phone));
    assert.ok(r.system.includes("Haircut (men)"));
  });
  await ok("guard rejects bad JSON, unknown intents, unknown FAQ numbers", () => {
    assert.strictEqual(F.guard(cfg, "sure! book"), null);
    assert.strictEqual(F.guard(cfg, '{"intent":"refund"}'), null);
    assert.strictEqual(F.guard(cfg, '{"intent":"faq","faq":99}'), null);
    assert.deepStrictEqual(F.guard(cfg, '```json\n{"intent":"book","service":"hair SPA"}\n```').service, "Hair spa");
    assert.strictEqual(F.guard(cfg, '{"intent":"book","service":"Keratin"}').service, null); // not ours → dropped
  });
  await ok("free replies with a price, number, time or link are thrown away", () => {
    for (const r of ["It costs ₹200", "Only 200 rs", "Come at 5 pm", "Come by five pm", "Open till eleven a.m.", "Open till ౯", "Visit www.x.com", "Sure, 2 mins", "दो सौ रुपए"])
      assert.strictEqual(F.guard(cfg, JSON.stringify({ intent: "other", reply: r })), null, r);
    assert.ok(F.guard(cfg, JSON.stringify({ intent: "other", reply: "I am asking the team now." })));
    assert.strictEqual(F.guard(cfg, '{"intent":"other","reply":"Let me check with the team and get back to you."}').reply, "Let me check with the team and get back to you.");
  });
  await ok("rescue hands the decision back to the engine (prices and slots come from the setup)", async () => {
    const out = miss("whats the damage for a facial these days");
    assert.ok(out.events.some((e) => e.type === "unanswered"));
    const r = await F.rescue(bot, out, meta, async () => '{"intent":"prices","service":null,"reply":"It is ₹50 only"}');
    const text = r.replies.map((x) => x.text).join("\n");
    assert.match(text, /Price list/); assert.ok(!text.includes("₹50 only"));
    for (const m of text.match(MONEY)) assert.ok([...PRICES].some((p) => p.includes(m.replace(/\s/, ""))), m);
    assert.ok(r.events.some((e) => e.type === "ai_fallback" && e.intent === "prices"));
  });
  await ok("book with a service starts the booking flow at the date step", async () => {
    const r = await F.rescue(bot, miss("beard set cheyinchukovali eppudu raavachu"), meta, async () => '{"intent":"book","service":"Beard trim"}');
    assert.match(r.replies.map((x) => x.text).join("\n"), /Beard trim[\s\S]*Which day/);
  });
  await ok("reschedule with nothing booked starts a new booking; faq answers from the setup", async () => {
    const r = await F.rescue(bot, miss("can we push my thing to sunday instead"), meta, async () => '{"intent":"reschedule"}');
    assert.match(r.replies.map((x) => x.text).join("\n"), /Which service|Which day/);
    const f = await F.rescue(bot, miss("kya card se payment ho jayega ya sirf cash"), meta, async () => '{"intent":"faq","faq":3}');
    assert.match(f.replies[0].text, /UPI, cards and cash/);
  });
  await ok("model errors, timeouts and junk keep the normal menu reply", async () => {
    const out = bot.handle(B.newState(), "parking facility unda bike ki", meta); // a real engine miss
    assert.ok(out.events.some((e) => e.type === "unanswered"));
    assert.strictEqual(await F.rescue(bot, out, meta, async () => { throw new Error("429"); }), out);
    assert.strictEqual(await F.rescue(bot, out, meta, () => new Promise(() => {}), 30), out);
    assert.strictEqual(await F.rescue(bot, out, meta, async () => "no idea"), out);
    const known = bot.handle(B.newState(), "price list", meta);
    assert.strictEqual(await F.rescue(bot, known, meta, async () => { throw new Error("never called"); }), known);
  });

  // The saved live run: 30 real-style messages answered by the free model (n8n "BotBhai AI fallback (private test, A74)").
  const cases = require("./fallback.cases.json"); const live = require("./fallback.live.json");
  const same = (d, c) => d && (d.intent === c.intent || (d.intent === "faq" && d.faq === 0 && c.intent === "offers") || (c.intent === "offers" && d.intent === "faq" && d.faq === 0))
    && (c.intent !== "faq" || d.faq === c.faq);
  let right = 0; const wrong = [];
  for (const [i, c] of cases.entries()) {
    const d = F.guard(cfg, live[i]); if (same(d, c)) right++; else wrong.push(`${c.text} → ${live[i]}`);
    const out = miss(c.text); const r = await F.rescue(bot, out, meta, async () => live[i]);
    for (const m of r.replies.map((x) => x.text).join("\n").match(MONEY) || []) // every ₹ amount shown is one of the setup's own
      assert.ok(/[\d]/.test(m) && JSON.stringify(cfg).includes(m.replace(/\s/, "")), `invented price ${m} for "${c.text}"`);
  }
  await ok(`live run: ${right}/30 understood correctly (need ≥ 25), no invented price`, () => {
    assert.strictEqual(cases.length, 30); assert.strictEqual(live.length, 30);
    assert.ok(right >= 25, "wrong:\n" + wrong.join("\n"));
  });
  if (wrong.length) console.log("    missed:", wrong.join(" | "));
  console.log(`${passed} fallback checks passed`);
})().catch((e) => { console.error(e); process.exit(1); });

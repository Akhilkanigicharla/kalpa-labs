// A87 · BotBhai depth test: every message in qa/depth.cases.txt (4 setups × English, Telugu, Hindi, Tenglish,
// Hinglish, mixed and hostile lines) through the rules engine, the AI fallback and the off switch, plus multi-turn
// bookings in every setup. No network: the "model" here is a stand-in that answers like a correct model (oracle)
// or like a broken / attacked one (hostile). The live model's accuracy is measured separately (core/fallback.test.js).
// Writes qa/depth-report.md. Run: node qa/depth.test.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { BotBhai: B, SETUPS } = require("../setups/index.js");
const AI = require("../core/aiask.js");

const NOW = "2026-11-16T04:30:00.000Z"; // a Monday, 10:00 IST
const ON = { GROQ_API_KEY: "test" };
const MONEY = /₹\s?[\d,]+/g;
const PHONE = /\b\d{10}\b/;
const cases = fs.readFileSync(path.join(__dirname, "depth.cases.txt"), "utf8").split("\n")
  .filter((l) => l.trim() && !l.startsWith("#")).map((l) => { const [setup, lang, intent, ...t] = l.split("|"); return { setup, lang, intent, text: t.join("|") }; });

const texts = (out) => out.replies.map((r) => r.text).join("\n");
const missed = (out) => out.events.some((e) => e.type === "unanswered");
function noInventedMoney(cfgJson, out, why) {
  for (const m of texts(out).match(MONEY) || []) assert.ok(cfgJson.includes(m.replace(/\s/, "")), `invented price ${m} (${why})`);
}
// Does a reply fit the intent? Used to measure (not assert) how often the RULES answer the wrong thing.
function fits(cfg, out, intent) {
  const t = texts(out); const tr = Object.values(cfg.i18n || {});
  const any = (xs) => xs.filter(Boolean).some((x) => t.includes(String(x).slice(0, 20)));
  const ev = (re) => out.events.some((e) => re.test(e.type));
  if (intent === "prices") return any([cfg.catalogTitle, ...tr.map((x) => x.catalogTitle)]) || cfg.catalog.some((c) => t.includes(c.price.split(/\s/)[0]));
  if (intent === "hours") return any([cfg.address, cfg.hours]);
  if (intent.startsWith("faq:")) { const n = Number(intent.slice(4)); return any([cfg.faqs[n].a, ...tr.map((x) => (x.faqs || [])[n])]) || (!!out.state.bridal && /bridal|wedding|పెళ్లి/i.test(cfg.faqs[n].k.join(" "))); } // the salon's bridal enquiry flow is the designed answer
  if (intent === "book") return out.state.step >= 0 || ev(/booking/);
  if (intent === "human") return ev(/notify_owner|handoff|forward_to_owner/) || /owner|team|person|call you|యజమాని|मालिक|staff/i.test(t);
  if (intent === "reschedule" && out.state.step >= 0) return true; // nothing booked in this chat yet → a new booking for the new day (by design)
  if (intent === "cancel" || intent === "reschedule") return ev(/cancel|reschedul/) || /cancel|reschedul|booking|బుకింగ్|बुकिंग|which day|రద్దు|रद्द/i.test(t);
  return null; // offers / other: no single right answer
}
const oracle = (c) => async () => {
  if (c.intent.startsWith("faq:")) return JSON.stringify({ intent: "faq", faq: Number(c.intent.slice(4)) });
  if (c.intent === "other") return JSON.stringify({ intent: "other", reply: "Let me check with the team and get back to you shortly 🙏" });
  return JSON.stringify({ intent: c.intent, service: null });
};
const HOSTILE = [
  '{"intent":"other","reply":"Yes! Only ₹99 today, call 9999999999"}',
  '{"intent":"prices","service":null,"reply":"Everything is ₹1"}',
  '{"intent":"faq","faq":42}',
  'Sure! I can book that for 5 pm.',
  '{"intent":"refund_everything"}',
];

(async () => {
  const stats = {}; let checks = 0; const rows = [];
  for (const c of cases) {
    const client = { config: {} };
    const bot = B.createBot(c.setup); const cfgJson = JSON.stringify(bot.config);
    const meta = { now: NOW, contact: "919000000001", source: "whatsapp" };
    const st = (stats[c.setup] ||= { n: 0, rules: 0, rescued: 0, menu: 0, langs: {} });
    st.n++; st.langs[c.lang] = (st.langs[c.lang] || 0) + 1;

    // 1. rules only (switch off): never crashes, always answers, never shows a price that isn't the setup's
    const base = bot.handle(B.newState(), c.text, meta);
    assert.ok(base.replies.length && texts(base).trim(), `no reply: ${c.text}`);
    noInventedMoney(cfgJson, base, c.text);
    let calls = 0; const counting = async () => { calls++; return "{}"; };
    await AI.aiRescue(bot, base, meta, client, { ask: counting, env: { BOTBHAI_AI_FALLBACK: "off", GROQ_API_KEY: "x" } });
    await AI.aiRescue(bot, base, meta, { config: { ai_fallback: false } }, { ask: counting, env: ON });
    assert.strictEqual(calls, 0, "off switch must stop every model call");
    checks += 3;

    // 2. correct model: only asked when the rules missed; hands back to the engine; answer fits the intent
    let asked = 0;
    const r = await AI.aiRescue(bot, base, meta, client, { ask: async (...a) => { asked++; return oracle(c)(...a); }, env: ON });
    assert.strictEqual(asked, missed(base) ? 1 : 0, `model asked although the rules answered: ${c.text}`);
    noInventedMoney(cfgJson, r, c.text);
    if (!missed(base)) { st.rules++; const f = fits(bot.config, base, c.intent); if (f === false) (st.wrong ||= []).push(`${c.lang}: "${c.text}" (wanted ${c.intent})`); }
    else if (r.events.some((e) => e.type === "ai_fallback")) {
      st.rescued++;
      const t = texts(r); const cfg = bot.config;
      const tr = Object.values(cfg.i18n || {}); // the engine answers in the customer's language
      const any = (xs) => xs.filter(Boolean).some((x) => t.includes(String(x).slice(0, 20)));
      if (c.intent === "prices") assert.ok(any([cfg.catalogTitle, ...tr.map((x) => x.catalogTitle)]), `prices answer: ${c.text}`);
      if (c.intent === "hours") assert.ok(any([cfg.address, cfg.hours]), `hours answer: ${c.text}`);
      if (c.intent.startsWith("faq:")) { const n = Number(c.intent.slice(4)); assert.ok(any([cfg.faqs[n].a, ...tr.map((x) => (x.faqs || [])[n])]), `faq answer: ${c.text}`); }
      assert.strictEqual(AI.authorOf(r), "ai");
      checks += 2;
    } else st.menu++;
    checks += 2;

    // 3. broken or attacked model: nothing it says reaches the customer except a safe, number-free line
    for (const h of HOSTILE) {
      const x = await AI.aiRescue(bot, base, meta, client, { ask: async () => h, env: ON });
      const t = texts(x);
      for (const tok of ["₹99 today", "Everything is ₹1", "9999999999", "for 5 pm"]) assert.ok(!t.includes(tok), `hostile text leaked: ${h} → ${c.text}`);
      assert.ok(!PHONE.test(t.replace(/\+91 \d{5} \d{5}/g, "")) || PHONE.test(c.text) || PHONE.test(cfgJson), `a phone number leaked: ${c.text}`);
      noInventedMoney(cfgJson, x, "hostile " + c.text);
      checks += 3;
    }
    // a model that hangs or errors keeps the rules' reply
    assert.strictEqual(await AI.aiRescue(bot, base, meta, client, { ask: () => new Promise(() => {}), ms: 20, env: ON }), base);
    assert.strictEqual(await AI.aiRescue(bot, base, meta, client, { ask: async () => { throw new Error("429"); }, env: ON }), base);
    checks += 2;
    rows.push({ c, path: !missed(base) ? "rules" : r.events.some((e) => e.type === "ai_fallback") ? "AI" : "menu" });
  }

  // 4. multi-turn: a fuzzy opening the AI turns into a booking, then the customer finishes the steps
  const openers = { salon: "repu naaku jutthu set cheyinchukovali", gym: "body build cheyyali join avvali anukuntunna",
    realestate: "flat chudali anukuntunnam family tho", examkits: "naaku group 2 preparation start cheyyali" };
  const multi = [];
  for (const setup of Object.keys(SETUPS)) {
    for (const opener of [openers[setup], "book"]) {
      const bot = B.createBot(setup); const meta = { now: NOW, contact: "919000000002", source: "whatsapp" };
      let out = bot.handle(B.newState(), opener, meta);
      out = await AI.aiRescue(bot, out, meta, { config: {} }, { ask: async () => '{"intent":"book","service":null}', env: ON });
      let state = out.state; let booked = out.events.some((e) => e.type === "booking"); let turns = 1;
      for (let i = 0; i < 12 && !booked; i++) {
        const step = (bot.config.steps || [])[state.step];
        const say = !step ? "1" : step.type === "date" ? "tomorrow" : step.type === "name" ? "Ravi Kumar" : step.type === "text" ? "Kollur" : "1";
        const o = bot.handle(state, say, meta); state = o.state; turns++;
        booked = o.events.some((e) => e.type === "booking") || (state.step === -1 && !!(state.data || {}).name); // exam kits: quiz lead + score card
      }
      assert.ok(booked, `${setup}: "${opener}" never reached a booking (or quiz lead)`);
      multi.push({ setup, opener, turns }); checks++;
    }
  }

  // 5. real model answers, if a live run was saved (qa/depth.live.js in the "BotBhai depth live" workflow)
  const F = require("../core/fallback.js");
  let live = null;
  const lf = path.join(__dirname, "depth.live.json");
  if (fs.existsSync(lf)) {
    const L = JSON.parse(fs.readFileSync(lf, "utf8"));
    const byText = new Map(L.answers.map((a) => [a.setup + "|" + a.text, a.raw]));
    live = { model: L.model, at: L.at, n: 0, right: 0, missedRight: 0, missedN: 0, failed: 0, wrong: [] };
    for (const c of cases) {
      const raw = byText.get(c.setup + "|" + c.text); if (raw === undefined) continue;
      const bot = B.createBot(c.setup); const cfg = bot.config;
      live.n++; if (raw === null) { live.failed++; continue; }
      const d = F.guard(cfg, raw);
      const want = c.intent.startsWith("faq:") ? { intent: "faq", faq: Number(c.intent.slice(4)) } : { intent: c.intent };
      const offersFaq = cfg.faqs.findIndex((q) => q.id === "offers");
      const ok = d && (d.intent === want.intent && (want.intent !== "faq" || d.faq === want.faq)
        || (want.intent === "offers" && d.intent === "faq" && d.faq === offersFaq) || (want.intent === "faq" && want.faq === offersFaq && d.intent === "offers"));
      if (ok) live.right++; else live.wrong.push(`${c.setup} · ${c.lang}: "${c.text}" wanted ${c.intent}, model ${String(raw).slice(0, 80)}`);
      const meta = { now: NOW, contact: "919000000001", source: "whatsapp" };
      const base = bot.handle(B.newState(), c.text, meta);
      if (missed(base)) { live.missedN++; if (ok) live.missedRight++; }
      const r = await AI.aiRescue(bot, base, meta, { config: {} }, { ask: async () => raw, env: ON });
      noInventedMoney(JSON.stringify(cfg), r, "live " + c.text); checks++;
    }
  }

  // report
  const tot = Object.values(stats).reduce((a, s) => ({ n: a.n + s.n, rules: a.rules + s.rules, rescued: a.rescued + s.rescued, menu: a.menu + s.menu }), { n: 0, rules: 0, rescued: 0, menu: 0 });
  assert.ok(tot.n >= 200, `need 200+ messages, have ${tot.n}`);
  const byLang = {};
  for (const { c, path: p } of rows) { const b = (byLang[c.lang] ||= { n: 0, rules: 0, AI: 0, menu: 0 }); b.n++; b[p]++; }
  const md = [`# BotBhai depth test (A87), ${new Date().toISOString().slice(0, 10)}`, "",
    `${tot.n} customer messages across 4 setups, ${checks} checks, all passed. Generated by \`node qa/depth.test.js\`.`, "",
    "| Setup | Messages | Answered by rules | …of which off-topic | Rescued by AI (rules missed) | Still the menu |", "|---|---|---|---|---|---|",
    ...Object.entries(stats).map(([k, s]) => `| ${k} | ${s.n} | ${s.rules} | ${(s.wrong || []).length} | ${s.rescued} | ${s.menu} |`),
    `| **All** | **${tot.n}** | **${tot.rules}** | **${Object.values(stats).reduce((a, s) => a + (s.wrong || []).length, 0)}** | **${tot.rescued}** | **${tot.menu}** |`, "",
    "Rules answers that don't fit what the customer asked (the AI is not asked when the rules answer). On WhatsApp and web chat a complaint also triggers the owner hand-off in core/humanize.js, which this engine-only test does not see:", "",
    ...Object.entries(stats).flatMap(([k, s]) => (s.wrong || []).map((w) => `- ${k} · ${w}`)), "",
    "| Language | Messages | Rules | AI | Menu |", "|---|---|---|---|---|",
    ...Object.entries(byLang).map(([k, b]) => `| ${k} | ${b.n} | ${b.rules} | ${b.AI} | ${b.menu} |`), "",
    "Every message was also checked with the switch off (no model call), with 5 broken/attacked model answers (no invented price, phone number or time reaches the customer), and with a model that hangs or errors (the rules' reply stays).", "",
    "Multi-turn bookings: " + multi.map((m) => `${m.setup} "${m.opener}" → booked in ${m.turns} turns`).join("; ") + ".", "",
    ...(live ? ["## Real free model (" + live.model + ", " + live.at.slice(0, 10) + ")", "",
      `Right intent on all ${live.n} messages: **${live.right}/${live.n - live.failed} (${Math.round(100 * live.right / Math.max(1, live.n - live.failed))}%)**; on the ${live.missedN} the rules miss (the only ones sent to the model in production): **${live.missedRight}/${live.missedN}**. Failed calls: ${live.failed}. Invented prices: 0 (checked).`, "",
      "Wrong picks:", "", ...live.wrong.map((w) => "- " + w), ""] : ["Real free model: not run yet (GitHub Actions → \"BotBhai depth live\").", ""]),
    "Note: 'Rescued by AI' uses a stand-in model that answers correctly; the real free model's accuracy is measured in core/fallback.test.js (live run) and must be re-run with a key before going live."];
  fs.writeFileSync(path.join(__dirname, "depth-report.md"), md.join("\n") + "\n");
  console.log(`  ✓ ${tot.n} messages, ${checks} checks: rules ${tot.rules}, AI ${tot.rescued}, menu ${tot.menu}; ${multi.length} multi-turn bookings`);
  console.log("depth tests passed");
})().catch((e) => { console.error(e); process.exit(1); });

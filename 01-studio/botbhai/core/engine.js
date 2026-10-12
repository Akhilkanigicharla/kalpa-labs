/*
 * BotBhai conversation engine — Kalpa Labs
 * One engine; each industry setup (salon, real estate, gym, exam kits) plugs in its own config.
 * Pure JavaScript, no dependencies. Runs in the browser (demo, website widget, voice agent)
 * and in Node / Netlify Functions (real WhatsApp webhook).
 *
 *   const bot = Botforge.createBot("clinic", { business: "My Clinic" });
 *   let state = Botforge.newState();
 *   const out = bot.handle(state, "hi");      // { replies:[{text, options?}], state, lead, events }
 *   state = out.state;
 *
 * Deliberately rule-based: answers are predictable, cost ₹0 per message, and stay inside
 * WhatsApp's business-messaging policy (task-specific bot, not a general-purpose AI chat).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.BotBhai = root.Botforge = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // Industry setups register themselves (see setups/<industry>/bot.config.js). The engine holds no business data.
  const NICHES = {};
  function register(cfg) { if (!cfg || !cfg.id) throw new Error("config needs an id"); NICHES[cfg.id] = cfg; return cfg; }

  // ---------------------------------------------------------------- helpers
  const DAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const GREET = /^(hi+|hello+|hey+|hai|helo|namaste|namaskar|namaskaram|vanakkam|good (morning|afternoon|evening)|start|menu|main menu|options|హాయ్|నమస్కారం|नमस्ते|हाय)\b/i;

  function norm(s) { return String(s || "").toLowerCase().replace(/[^\p{L}\p{N}\s/:\-₹.]/gu, " ").replace(/\s+/g, " ").trim(); }
  function fill(t, v) { return String(t).replace(/\{(\w+)\}/g, (m, k) => (v[k] !== undefined && v[k] !== "" ? v[k] : m)); }
  function fmtDate(d) { return `${DAYS[d.getDay()].slice(0, 1).toUpperCase()}${DAYS[d.getDay()].slice(1, 3)}, ${d.getDate()} ${MONTHS[d.getMonth()]}`; }
  function hasWord(text, k) {
    if (k.includes(" ")) return text.includes(k);
    return new RegExp(`(^|\\s)${k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(\\s|$)`).test(text);
  }

  // Understands: today, tomorrow, day after tomorrow, weekday names, 15/10, 15-10-2026, "15 oct".
  function parseDate(input, now) {
    const t = norm(input); const base = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const plus = (n) => { const d = new Date(base); d.setDate(d.getDate() + n); return d; };
    if (/day after tomorrow|parso|ellundi/.test(t)) return plus(2);
    if (/\b(today|aaj|ivala|ee roju)\b/.test(t)) return plus(0);
    if (/\b(tomorrow|tmrw|tmr|kal|repu)\b/.test(t)) return plus(1);
    for (let i = 0; i < 7; i++) {
      if (t.includes(DAYS[i]) || new RegExp(`\\b${DAYS[i].slice(0, 3)}\\b`).test(t)) {
        let diff = (i - base.getDay() + 7) % 7; if (diff === 0) diff = 7; return plus(diff);
      }
    }
    let m = t.match(/\b(\d{1,2})\s*[\/\-.]\s*(\d{1,2})(?:\s*[\/\-.]\s*(\d{2,4}))?\b/);
    if (m) {
      const day = +m[1], mon = +m[2] - 1; let yr = m[3] ? +m[3] : base.getFullYear(); if (yr < 100) yr += 2000;
      const d = new Date(yr, mon, day);
      if (d.getMonth() !== mon) return null;
      if (!m[3] && d < base) d.setFullYear(d.getFullYear() + 1);
      return d;
    }
    m = t.match(/\b(\d{1,2})\s*(st|nd|rd|th)?\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b/);
    if (m) {
      const mon = MONTHS.findIndex((x) => x.toLowerCase() === m[3]);
      const d = new Date(base.getFullYear(), mon, +m[1]); if (d < base) d.setFullYear(d.getFullYear() + 1); return d;
    }
    return null;
  }

  // Match free text or a number against a list of choices.
  function pickChoice(input, choices) {
    const t = norm(input);
    const n = parseInt(t, 10);
    if (/^\d+$/.test(t) && n >= 1 && n <= choices.length) return choices[n - 1];
    const exact = choices.find((c) => norm(c) === t); if (exact) return exact;
    const contains = choices.find((c) => t.length >= 3 && norm(c).includes(t)); if (contains) return contains;
    let best = null, bestScore = 0;
    for (const c of choices) {
      const words = norm(c).split(" ").filter((w) => w.length >= 3);
      const score = words.filter((w) => t.includes(w)).length / Math.max(words.length, 1);
      if (score > bestScore) { bestScore = score; best = c; }
    }
    return bestScore >= 0.34 ? best : null;
  }

  function newState() { return { step: -1, data: {}, lead: { score: "cold", status: "new", intents: [] }, turns: 0, optedOut: false }; }

  // ---------------------------------------------------------------- bot
  function createBot(nicheOrConfig, overrides) {
    const base = typeof nicheOrConfig === "object" ? nicheOrConfig : NICHES[nicheOrConfig]; if (!base) throw new Error("Unknown setup: " + nicheOrConfig);
    const cfg = Object.assign({}, base, overrides || {});
    const vars = () => ({ business: cfg.business, address: cfg.address, hours: cfg.hours, phone: cfg.phone });
    const choiceList = (step) => (step.choices === "catalog" ? cfg.catalog.map((c) => c.name) : step.choices);

    function menuReply(prefix) {
      return { text: (prefix ? prefix + "\n\n" : "") + "How can I help? Reply with a number:\n" + cfg.menu.map((m, i) => `*${i + 1}.* ${m.label}`).join("\n"), options: cfg.menu.map((m) => m.label) };
    }
    function catalogReply() {
      return { text: `*${cfg.catalogTitle}* — ${cfg.business}\n` + cfg.catalog.map((c) => `• ${c.name} — *${c.price}*`).join("\n") + `\n\nReply *1* to book your ${cfg.bookWord}.` };
    }
    function hoursReply() {
      return { text: `🕘 ${cfg.hours}\n📍 ${cfg.address}\n📞 ${cfg.phone}\n🗺️ https://maps.google.com/?q=${encodeURIComponent(cfg.address)}` };
    }
    function askStep(state) {
      const step = cfg.steps[state.step];
      if (step.type === "quiz") {
        const bank = cfg.quizBank || {}; const qs = bank[state.data.service] || bank[Object.keys(bank)[0]]; const q = qs[step.n];
        return { text: `*Q${step.n + 1}/3.* ${q.q}\n` + q.o.map((o, i) => `${String.fromCharCode(65 + i)}) ${o}`).join("\n"), options: q.o.map((o, i) => String.fromCharCode(65 + i) + ") " + o) };
      }
      const ch = step.choices ? choiceList(step) : null;
      if (ch) return { text: step.ask + "\n" + ch.map((c, i) => `*${i + 1}.* ${c}`).join("\n"), options: ch };
      return { text: step.ask };
    }
    function bump(state, score, intent) {
      const rank = { cold: 0, warm: 1, hot: 2 };
      if (rank[score] > rank[state.lead.score]) state.lead.score = score;
      if (intent && !state.lead.intents.includes(intent)) state.lead.intents.push(intent);
    }
    function leadSnapshot(state, meta) {
      return Object.assign({ niche: cfg.id, business: cfg.business, contact: meta.contact || null, source: meta.source || "whatsapp" }, state.data, {
        name: state.data.name || meta.profileName || null,
        score: state.lead.score, status: state.lead.status, intents: state.lead.intents.slice(), turns: state.turns,
      });
    }
    function startFlow(state) {
      state.step = 0; state.data = {}; bump(state, "warm", "book");
      return [{ text: cfg.quiz ? "Let's go! 3 quick questions." : `Great, let's book your ${cfg.bookWord}. Type *cancel* any time to stop.` }, askStep(state)];
    }

    function handleStep(state, raw, events) {
      const step = cfg.steps[state.step];
      let value = null, error = null;
      if (step.type === "quiz") {
        const bank = cfg.quizBank || {}; const qs = bank[state.data.service] || bank[Object.keys(bank)[0]]; const q = qs[step.n];
        const t = norm(raw); let idx = -1;
        const letter = t.match(/^([abcd])\b/); if (letter) idx = letter[1].charCodeAt(0) - 97;
        else if (/^[1-4]$/.test(t)) idx = +t - 1;
        else idx = q.o.findIndex((o) => norm(o) === t || (t.length > 2 && norm(o).includes(t)));
        if (idx < 0) error = "Please reply A, B, C or D.";
        else {
          const ok = idx === q.a; state.data.correct = (state.data.correct || 0) + (ok ? 1 : 0);
          value = q.o[idx];
          state.step++;
          const fb = { text: (ok ? "✅ Correct! " : `❌ Not quite — answer: *${q.o[q.a]}*. `) + q.why };
          return [fb, nextOrFinish(state, events)].flat();
        }
      } else if (step.type === "date") {
        const d = parseDate(raw, state.now ? new Date(state.now) : new Date());
        if (!d) error = "Sorry, I couldn't read that date. Try *today*, *tomorrow*, a weekday, or *15/10*.";
        else { value = fmtDate(d); state.data.date_iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; }
      } else if (step.type === "name") {
        const n = String(raw).trim().replace(/^(my name is|i am|i'm|this is|name)\s*[:\-]?\s*/i, "");
        if (n.length < 2 || n.length > 60 || /^\d+$/.test(n)) error = "Please type the name (letters only).";
        else value = n.replace(/\b\w/g, (c) => c.toUpperCase());
      } else if (step.choices) {
        value = pickChoice(raw, choiceList(step));
        if (!value) error = "Please choose one of the options (reply with the number).";
      } else {
        const v = String(raw).trim(); if (v.length < 2) error = "Could you type that again?"; else value = v.slice(0, 80);
      }
      if (error) return [{ text: error }, askStep(state)];
      state.data[step.field] = value;
      state.step++;
      return nextOrFinish(state, events);
    }

    function nextOrFinish(state, events) {
      if (state.step < cfg.steps.length) return [askStep(state)];
      // finished
      const v = Object.assign(vars(), state.data);
      if (cfg.quiz) {
        const s = state.data.correct || 0; v.score = s; state.data.quiz_score = `${s}/3`;
        v.advice = s === 3 ? "Excellent — you're exam-ready on these topics. The full kit has 5 mock tests to keep you sharp." : s === 2 ? "Good — one gap to fix. The kit's 30-day plan targets exactly these weak areas." : "Let's build the basics. Start with the free daily question and the kit's chapter-wise practice.";
        delete state.data.correct; delete state.data.q1; delete state.data.q2; delete state.data.q3;
      }
      state.step = -1; state.lead.status = cfg.quiz ? "quiz_done" : "booked"; bump(state, "hot", cfg.quiz ? "quiz" : "booked");
      events.push({ type: "notify_owner", text: `🔔 New ${cfg.bookWord}: ${state.data.name}` + (state.data.service ? ` · ${state.data.service}` : "") + (state.data.date ? ` · ${state.data.date} ${state.data.slot || ""}` : "") + (state.data.quiz_score ? ` · score ${state.data.quiz_score}` : "") });
      return [{ text: fill(cfg.confirm, v) }];
    }

    function handle(stateIn, text, meta) {
      meta = meta || {};
      const state = JSON.parse(JSON.stringify(stateIn || newState()));
      if (meta.now) state.now = meta.now;
      state.turns++;
      const events = []; let replies = [];
      const raw = String(text || "").trim(); const t = norm(raw);

      if (/^(stop|unsubscribe|opt out)$/.test(t)) {
        state.optedOut = true; state.step = -1; state.lead.status = "opted_out";
        replies = [{ text: "You're unsubscribed and won't get any more messages from us. Reply *START* any time to come back." }];
      } else if (state.optedOut && !/^start$/.test(t)) {
        replies = [];
      } else if (state.step >= 0 && /^(cancel|exit|quit)$/.test(t)) {
        state.step = -1; replies = [menuReply("No problem, cancelled.")];
      } else if (state.step >= 0 && !GREET.test(t)) {
        replies = handleStep(state, raw, events);
      } else if (!t) {
        replies = [menuReply()];
      } else if (GREET.test(t) || /^start$/.test(t)) {
        state.optedOut = false; state.step = -1;
        const first = state.turns === 1 ? fill(cfg.greeting, vars()) : `Welcome back to *${cfg.business}* 😊`;
        replies = [menuReply(first)];
      } else {
        // Menu number or keyword intent
        let key = null;
        if (/^\d$/.test(t) && +t >= 1 && +t <= cfg.menu.length) key = cfg.menu[+t - 1].key;
        else {
          const m = cfg.menu.find((x) => norm(x.label) === t); if (m) key = m.key;
        }
        if (!key) {
          if (cfg.guardWords && cfg.guardWords.some((w) => t.includes(w))) key = "guard";
          else if (/\b(human|agent|person|call me|callback|call back|talk|speak|reception|advisor|owner|manager)\b/.test(t)) key = "human";
          else if (/\b(book|booking|appointment|appoint|slot|schedule|visit|trial|reserve|quiz|test me)\b/.test(t)) key = "book";
          else if (/\b(price|prices|cost|fee|fees|charge|charges|rate|rates|how much|plans?|membership|packages?|projects?|kits?)\b/.test(t)) key = "prices";
          else if (/\b(time|timing|timings|open|close|hours|where|location|address|directions|map)\b/.test(t)) key = "hours";
        }
        if (!key) {
          const f = cfg.faqs.find((q) => q.k.some((k) => hasWord(t, k)));
          if (f) { replies = [{ text: fill(f.a, vars()) + "\n\nReply *menu* for more options." }]; bump(state, "warm", "faq"); }
        }
        if (key === "book") replies = startFlow(state);
        else if (key === "prices") { replies = [catalogReply()]; bump(state, "warm", "prices"); }
        else if (key === "hours") { replies = [hoursReply()]; bump(state, "cold", "hours"); }
        else if (key === "guard") replies = [{ text: cfg.guard }];
        else if (key === "human") {
          state.lead.status = state.lead.status === "booked" ? "booked" : "callback"; bump(state, "warm", "human");
          events.push({ type: "handoff", text: `🙋 ${meta.profileName || "A customer"} (${meta.contact || "web chat"}) wants to talk to a person.` });
          replies = [{ text: `Sure 🙂 I've told the team — someone from *${cfg.business}* will message you shortly (within working hours: ${cfg.hours}). You can also call ${cfg.phone}.` }];
        } else if (key && key.startsWith("faq:")) {
          const f = cfg.faqs.find((q) => q.id === key.slice(4));
          replies = [{ text: fill(f.a, vars()) + "\n\nReply *menu* for more options." }]; bump(state, "warm", "faq");
        }
        if (!replies.length) {
          events.push({ type: "unanswered", text: raw });
          replies = [menuReply("Sorry, I didn't quite get that. I can help with these:")];
        }
      }
      return { replies, state, lead: leadSnapshot(state, meta), events };
    }

    return { config: cfg, handle };
  }

  return { NICHES, register, createBot, newState, parseDate, pickChoice, version: "2.0.0" };
});

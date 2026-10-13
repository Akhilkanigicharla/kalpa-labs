/*
 * BotBhai conversation engine — Kalpa Labs                                  v3.0
 * One engine; each industry setup (salon, real estate, gym, exam kits) plugs in its own config.
 * Pure JavaScript, no dependencies. Runs in the browser (demo, website widget) and in
 * Node / Netlify Functions (WhatsApp webhook, website chat).
 *
 *   const bot = BotBhai.createBot("salon", { business: "My Salon" });
 *   let state = BotBhai.newState();
 *   const out = bot.handle(state, "hi", { now, busy, known });  // { replies, state, lead, events }
 *
 * All calendar maths is in India time (IST, UTC+5:30) whatever the server's clock says.
 * Deliberately rule-based for bookings and money: predictable, ₹0 per message, and inside WhatsApp's
 * business-messaging policy (task-specific bot, not a general-purpose AI chat).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.BotBhai = root.Botforge = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // Slot engine (core/slots.js). In Node it is required; in the browser it is used if loaded first
  // (window.BotBhaiSlots); otherwise the built-in v3.0 fixed-slot logic below is used.
  let Slots = null;
  try { Slots = typeof require === "function" ? require("./slots.js") : (typeof self !== "undefined" && self.BotBhaiSlots) || null; } catch (e) { Slots = null; }

  const NICHES = {};
  function register(cfg) { if (!cfg || !cfg.id) throw new Error("config needs an id"); NICHES[cfg.id] = cfg; return cfg; }

  // ---------------------------------------------------------------- time (IST)
  const IST_MS = 330 * 60000;
  const DAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  // A "day" is a Date at UTC midnight of the IST calendar date; read it only with getUTC*.
  function istToday(now) { const z = new Date(now.getTime() + IST_MS); return new Date(Date.UTC(z.getUTCFullYear(), z.getUTCMonth(), z.getUTCDate())); }
  function istMinutes(now) { const z = new Date(now.getTime() + IST_MS); return z.getUTCHours() * 60 + z.getUTCMinutes(); }
  function addDays(d, n) { return new Date(d.getTime() + n * 864e5); }
  function isoOf(d) { return d.toISOString().slice(0, 10); }
  function fmtDate(d) { const w = DAYS[d.getUTCDay()]; return `${w[0].toUpperCase()}${w.slice(1, 3)}, ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`; }
  function slotMinutes(s) { const m = String(s).match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i); return m ? ((+m[1] % 12) + (/pm/i.test(m[3]) ? 12 : 0)) * 60 + +m[2] : null; }

  // ---------------------------------------------------------------- language helpers
  const GREET = /^(hi+|hello+|hey+|hai+|helo|hlo|namaste|namasthe|namastey|namaskar|namaskaram|namaskaaram|vanakkam|good (morning|afternoon|evening)|start|menu|main menu|options|హాయ్|హలో|నమస్కారం|నమస్కారాలు|నమస్తే|नमस्ते|नमस्कार|हाय|हेलो)(?=\s|$|[!.,?])/i;
  // Tenglish / Hinglish / Telugu / Hindi words people really type
  const INTENT = {
    human: /\b(human|agent|person|call me|callback|call back|talk to|speak to|reception|advisor|owner|manager|staff)\b/,
    book: /\b(bo+k(ing)?|bok|buk|appointment|apointment|appoint|slot|schedule|reserve|trial|quiz|test me|kavali|kaavali|chahiye|chaiye|cheyyali|cheyandi|book cheyyi|book karo|book kar do|fix cheyyi)\b|బుక్|బుకింగ్|అపాయింట్మెంట్|అపాయింట్|స్లాట్|కావాలి|बुक|बुकिंग|अपॉइंटमेंट|चाहिए/,
    haggle: /\b(too much|costly|expensive|discount|last price|less price|reduce|kam karo|kam kijiye|thagginchandi|taggincha|tagginchandi|chestara|best price|final price)\b/,
    prices: /\b(price|prices|cost|fee|fees|charge|charges|rate|rates|how much|plans?|membership|packages?|projects?|kits?|entha|enta|ఎంత|kitna|kitne|kitni|kya rate|rate kya|price list)\b|ధర|कितना|कीमत/,
    cancel: /\b(cancel|cancell?ed|cancellation|radhu|raddu)\b|రద్దు|క్యాన్సిల్|कैंसिल|रद्द/,
    hours: /\b(time|timing|timings|open|close|closed|hours|where|location|address|directions|map|eppudu|ekkada|kab|kahan|kidhar)\b|ఎక్కడ|ఎప్పుడు|कहाँ|कब/,
  };
  const W = (words) => new RegExp(`(^|\\s)(${words})(?=\\s|$)`); // word boundary that also works for Telugu/Hindi script
  const DAYPART = [
    { re: W("morning|udayam|poddunna|poddune|subah|ఉదయం|పొద్దున|सुबह"), from: 0, to: 720 },
    { re: W("afternoon|noon|madhyahnam|madhyanam|madhyaanam|dopahar|మధ్యాహ్నం|दोपहर"), from: 720, to: 1020 },
    { re: W("evening|night|sayantram|saayantram|sayantra|ratri|shaam|sham|raat|సాయంత్రం|రాత్రి|शाम|रात"), from: 1020, to: 1440 },
  ];
  // M1: replies to the reminder ("Confirm" button, 1, yes, sare, haan, సరే)
  const CONFIRM = /^(1|yes|y|yes confirm|ok|okay|ok confirm|confirm|confirmed|sure|will come|coming|i will come|vastanu|vasthanu|vastam|vasthamu|sare|sari|avunu|haa|haan|han|ha ji|haan ji|ji|aaunga|aaungi|aayenge|సరే|అవును|వస్తాను|हाँ|हां|हा|ठीक है|आऊंगा|आऊंगी)$/;
  function norm(s) { return String(s || "").replace(/[\u200b-\u200d\u2060\ufeff]/g, "").toLowerCase().replace(/[^\p{L}\p{N}\p{M}\s/:\-₹.]/gu, " ").replace(/\s+/g, " ").trim(); }
  function squash(s) { return norm(s).replace(/[\s\-]/g, ""); }
  function fill(t, v) { return String(t).replace(/\{(\w+)\}/g, (m, k) => (v[k] !== undefined && v[k] !== "" ? v[k] : m)); }
  function hasWord(text, k) {
    if (k.includes(" ")) return text.includes(k);
    return new RegExp(`(^|\\s)${k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(\\s|$)`).test(text);
  }

  // Understands: today, tomorrow, day after, weekdays, 15/10, 15-10-2026, "15 oct", Telugu/Hindi day words.
  // Returns an IST calendar day, or null. Past dates are rejected.
  function parseDate(input, now) {
    const t = norm(input); const base = istToday(now);
    if (/day after tomorrow|parso|ellundi|ఎల్లుండి|परसों/.test(t)) return addDays(base, 2);
    if (/\b(today|aaj|ivala|ee roju|eeroju|tonight)\b|ఈరోజు|ఇవాళ|आज/.test(t)) return base;
    if (/\b(tomorrow|tmrw|tmr|tmrw|kal|repu|reypu)\b|రేపు|कल/.test(t)) return addDays(base, 1);
    for (let i = 0; i < 7; i++) {
      if (t.includes(DAYS[i]) || new RegExp(`\\b${DAYS[i].slice(0, 3)}\\b`).test(t)) {
        let diff = (i - base.getUTCDay() + 7) % 7;
        if (diff === 0 && /\b(next|vachhe|agle)\b/.test(t)) diff = 7; // "saturday" on a Saturday = today; "next saturday" = in 7 days
        return addDays(base, diff);
      }
    }
    let m = t.match(/\b(\d{1,2})\s*[\/\-.]\s*(\d{1,2})(?:\s*[\/\-.]\s*(\d{2,4}))?\b/);
    if (m) {
      const day = +m[1], mon = +m[2] - 1; let yr = m[3] ? +m[3] : base.getUTCFullYear(); if (yr < 100) yr += 2000;
      let d = new Date(Date.UTC(yr, mon, day));
      if (d.getUTCMonth() !== mon) return null;
      if (d < base) { if (m[3]) return null; d = new Date(Date.UTC(yr + 1, mon, day)); }
      return d;
    }
    m = t.match(/\b(\d{1,2})\s*(st|nd|rd|th)?\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b/);
    if (m) {
      const mon = MONTHS.findIndex((x) => x.toLowerCase() === m[3]);
      let d = new Date(Date.UTC(base.getUTCFullYear(), mon, +m[1])); if (d.getUTCMonth() !== mon) return null;
      if (d < base) d = new Date(Date.UTC(base.getUTCFullYear() + 1, mon, +m[1]));
      return d;
    }
    return null;
  }

  // Match free text, a number, or a time ("4", "4pm", "4:30 pm", "evening") against choices.
  // "hair cut" -> "haircut" when the glued word is a word of one of the choices, so the
  // loose "hair" can't make "Hair spa" win (Deep Scan v2 finding, 13 Oct 2026)
  function joinSplitWords(t, choices) {
    const words = new Set([].concat(...choices.map((c) => norm(c).split(" "))).filter((w) => w.length >= 5));
    const tok = t.split(" "); const out = [];
    for (let i = 0; i < tok.length; i++) {
      if (i + 1 < tok.length && words.has(tok[i] + tok[i + 1]) && !words.has(tok[i])) { out.push(tok[i] + tok[i + 1]); i++; } else out.push(tok[i]);
    }
    return out.join(" ");
  }
  function pickChoice(input, choices) {
    const t = joinSplitWords(norm(input), choices); if (!t) return null;
    const timed = choices.filter((c) => slotMinutes(c) !== null);
    if (timed.length === choices.length) {
      const tm = t.match(/^(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|a m|p m)?$/);
      if (tm && (tm[3] || tm[2] || +tm[1] > choices.length)) {
        const ap = tm[3] ? tm[3].replace(" ", "") : null;
        const hit = choices.filter((c) => { const x = c.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i); return +x[1] === +tm[1] && (!tm[2] || x[2] === tm[2]) && (!ap || x[3].toLowerCase() === ap); });
        if (hit.length === 1) return hit[0];
        if (hit.length > 1 && !ap) return hit.find((c) => /pm/i.test(c)) || hit[0]; // "4" for a salon usually means 4 PM
      }
      const part = DAYPART.find((x) => x.re.test(t)); // "evening", "sayantram", "సాయంత్రం", "शाम"
      if (part) { const hit = choices.find((c) => slotMinutes(c) >= part.from && slotMinutes(c) < part.to); if (hit) return hit; }
    }
    const n = parseInt(t, 10);
    if (/^\d+$/.test(t) && n >= 1 && n <= choices.length) return choices[n - 1];
    const exact = choices.find((c) => norm(c) === t); if (exact) return exact;
    const sq = squash(t);
    const glued = choices.filter((c) => sq.length >= 4 && squash(c).startsWith(sq)); if (glued.length === 1) return glued[0]; if (glued.length > 1) return null; // "haircut": men or women? ask
    const contains = choices.filter((c) => t.length >= 3 && new RegExp(`(^|\\s)${t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(\\s|$)`).test(norm(c))); if (contains.length === 1) return contains[0];
    const gluedIn = choices.filter((c) => sq.length >= 5 && squash(c).includes(sq)); if (gluedIn.length === 1) return gluedIn[0]; if (gluedIn.length > 1) return null;
    // word overlap: the choice whose words the customer used most; if two choices share the same matched words, it's ambiguous
    const scored = choices.map((c) => { const words = norm(c).split(" ").filter((w) => w.length >= 3); const hit = words.filter((w) => hasWord(t, w)); return { c, hits: hit.length, ratio: hit.length / Math.max(words.length, 1) }; });
    const maxHits = Math.max(0, ...scored.map((x) => x.hits));
    const top = scored.filter((x) => x.hits === maxHits && maxHits > 0);
    if (top.length !== 1) return null;
    return top[0].ratio >= 0.34 ? top[0].c : null;
  }

  // M6: catalog aliases ("gents cut", "ladies cut"). An alias listed on two items ("cutting") means "ask which one".
  function aliasMatch(raw, catalog) {
    const t = " " + norm(raw) + " ";
    const hits = (catalog || []).filter((c) => (c.aliases || []).some((a) => t.includes(" " + norm(a) + " ")));
    if (!hits.length) return null;
    const best = Math.max(...hits.map((c) => Math.max(...c.aliases.filter((a) => t.includes(" " + norm(a) + " ")).map((a) => norm(a).length))));
    const top = hits.filter((c) => c.aliases.some((a) => t.includes(" " + norm(a) + " ") && norm(a).length === best)); // longest alias wins: "ladies cutting" beats "cutting"
    return top.length === 1 ? { hit: top[0].name } : { ambiguous: top.map((c) => c.name) };
  }

  function newState() { return { step: -1, data: {}, lead: { score: "cold", status: "new", intents: [] }, turns: 0, optedOut: false }; }

  // ---------------------------------------------------------------- bot
  function createBot(nicheOrConfig, overrides) {
    const base = typeof nicheOrConfig === "object" ? nicheOrConfig : NICHES[nicheOrConfig]; if (!base) throw new Error("Unknown setup: " + nicheOrConfig);
    const cfg = Object.assign({}, base, overrides || {});
    const vars = () => ({ business: cfg.business, address: cfg.address, hours: cfg.hours, phone: cfg.phone });
    const choiceList = (step) => (step.choices === "catalog" ? cfg.catalog.map((c) => c.name) : step.choices); // "auto" = slots from schedule.hours
    const dateStep = () => cfg.steps.findIndex((x) => x.type === "date");
    const slotStep = () => cfg.steps.findIndex((x) => x.field === "slot");
    const nowOf = (state) => (state.now ? new Date(state.now) : new Date());

    function menuReply(prefix) {
      return { text: (prefix ? prefix + "\n\n" : "") + "How can I help? Reply with a number:\n" + cfg.menu.map((m, i) => `*${i + 1}.* ${m.label}`).join("\n"), options: cfg.menu.map((m) => m.label) };
    }
    function catalogReply() {
      return { text: `*${cfg.catalogTitle}* — ${cfg.business}\n` + cfg.catalog.map((c) => `• ${c.name} — *${c.price}*`).join("\n") + `\n\nReply *1* to book your ${cfg.bookWord}.` };
    }
    function hoursReply() {
      return { text: `🕘 ${cfg.hours}\n📍 ${cfg.address}\n📞 ${cfg.phone}\n🗺️ https://maps.google.com/?q=${encodeURIComponent(cfg.address)}` };
    }
    // Closed weekdays (0 = Sunday) and holidays: [{ date: "2026-11-08", name: "Diwali" }]
    function closedReason(dayIso, d) {
      if (Slots) return Slots.closedReason(cfg, dayIso);
      const h = (cfg.holidays || []).find((x) => x.date === dayIso); if (h) return `we're closed for ${h.name}`;
      if ((cfg.closed_weekdays || []).includes(d.getUTCDay())) return `we're closed on ${DAYS[d.getUTCDay()][0].toUpperCase() + DAYS[d.getUTCDay()].slice(1)}s`;
      return null;
    }
    // Bookable start times for the chosen day. Fixed list from the setup, or (choices: "auto") generated
    // from schedule.hours; service length, staff and breaks come from cfg.schedule (see core/slots.js).
    function freeSlotInfo(state, slots) {
      return Slots.free({ cfg, date_iso: state.data.date_iso, now: nowOf(state), busy: state._busy || [], service: state.data.service, labels: slots === "auto" ? null : slots });
    }
    function freeSlots(state, slots) {
      if (Slots) return freeSlotInfo(state, slots).map((x) => x.label);
      if (!Array.isArray(slots)) return []; // "auto" needs core/slots.js
      const cap = cfg.capacity || Infinity; const busy = state._busy || [];
      const now = nowOf(state); const today = isoOf(istToday(now)); const mins = istMinutes(now) + (cfg.lead_minutes || 30);
      return slots.filter((sl) => (state.data.date_iso !== today || slotMinutes(sl) === null || slotMinutes(sl) >= mins)
        && busy.filter((b) => b.date_iso === state.data.date_iso && b.slot === sl).length < cap);
    }
    function askStep(state) {
      const step = cfg.steps[state.step];
      if (step.type === "quiz") {
        const bank = cfg.quizBank || {}; const qs = bank[state.data.service] || bank[Object.keys(bank)[0]]; const q = qs[step.n];
        return { text: `*Q${step.n + 1}/3.* ${q.q}\n` + q.o.map((o, i) => `${String.fromCharCode(65 + i)}) ${o}`).join("\n"), options: q.o.map((o, i) => String.fromCharCode(65 + i) + ") " + o) };
      }
      let ch = step.choices ? choiceList(step) : null;
      if (ch && step.field === "slot") {
        const all = ch; ch = freeSlots(state, ch);
        if (!ch.length) {
          const day = state.data.date; const today = state.data.date_iso === isoOf(istToday(nowOf(state)));
          const info = Slots ? Slots.day(cfg, state.data.date_iso) : {};
          const allPast = today && (all === "auto" || (Slots && cfg.schedule && cfg.schedule.hours)
            ? !Slots.free({ cfg, date_iso: state.data.date_iso, now: nowOf(state), busy: [], service: state.data.service, labels: all === "auto" ? null : all }).length
            : all.every((sl) => slotMinutes(sl) !== null && slotMinutes(sl) < istMinutes(nowOf(state)) + (cfg.lead_minutes || 30)));
          state.step = dateStep(); delete state.data.date; delete state.data.date_iso;
          const why = today && info.closingToday ? `Sorry, we're ${info.note || "closed today"} 🙏 How about tomorrow? (or pick any other day)` : allPast ? "Today's slots are over 🌙 How about tomorrow? (or pick any other day)" : `Sorry, ${day} is fully booked 😕 Which other day works for you?`;
          return { text: why, options: ["Tomorrow", "Day after tomorrow"] };
        }
      }
      if (ch) return { text: step.ask + "\n" + ch.map((c, i) => `*${i + 1}.* ${c}`).join("\n"), options: ch };
      return { text: step.ask };
    }
    function bump(state, score, intent) {
      const rank = { cold: 0, warm: 1, hot: 2 };
      if (rank[score] > rank[state.lead.score]) state.lead.score = score;
      if (intent && !state.lead.intents.includes(intent)) state.lead.intents.push(intent);
    }
    function leadSnapshot(state, meta) {
      const data = Object.assign({}, state.data); delete data.correct;
      return Object.assign({ niche: cfg.id, business: cfg.business, contact: meta.contact || null, source: meta.source || "whatsapp" }, data, {
        name: state.data.name || (meta.known && meta.known.name) || meta.profileName || null,
        score: state.lead.score, status: state.lead.status, intents: state.lead.intents.slice(), turns: state.turns,
        marketing_opt_in: !!state.lead.marketing, customer_name: state.data.name || undefined, // the name they typed (not the WhatsApp profile name)
      });
    }
    function startFlow(state, meta, raw) {
      state.prev = { data: JSON.parse(JSON.stringify(state.data)), status: state.lead.status };
      state.step = 0; state.data = {}; bump(state, "warm", "book");
      if (meta && meta.known && meta.known.name) state.data.name = meta.known.name; // returning customer: don't ask the name again
      const heard = [];
      if (raw && !cfg.quiz) { // "repu haircut kavali" → service + date already understood, like a person would
        const svc = cfg.steps.find((x) => x.choices === "catalog");
        if (svc) {
          const words = norm(raw).split(" ").filter((w) => /\p{L}{3,}/u.test(w) && !INTENT.book.test(w) && !INTENT.prices.test(w) && !parseDate(w, nowOf(state)) && !cfg.menu.some((m) => norm(m.label).split(" ").includes(w)));
          const al = aliasMatch(raw, cfg.catalog);
          let hit = al ? al.hit || null : words.length ? pickChoice(words.join(" "), choiceList(svc)) : null;
          if (!hit && !al && words.length > 1) { const each = [...new Set(words.map((w) => pickChoice(w, choiceList(svc))).filter(Boolean))]; if (each.length === 1) hit = each[0]; }
          const item = hit && cfg.catalog.find((c) => c.name === hit);
          if (item && !item.enquiry) { state.data[svc.field] = hit; heard.push(hit); }
        }
        const d = parseDate(raw, nowOf(state));
        if (d && !closedReason(isoOf(d), d) && dateStep() >= 0) { state.data.date = fmtDate(d); state.data.date_iso = isoOf(d); heard.push(state.data.date); }
      }
      const intro = cfg.quiz ? "Let's go! 3 quick questions." : heard.length ? `Sure! ${heard.join(", ")} 👍` : `Great, let's book your ${cfg.bookWord}. Type *cancel* any time to stop.`;
      return [{ text: intro }, ...nextOrFinish(state, [])];
    }
    function abandonFlow(state) { // restore what was there before an unfinished booking/reschedule
      if (state.prev) { state.data = state.prev.data; state.lead.status = state.prev.status; }
      delete state.prev; delete state.rescheduling; state.step = -1;
    }
    function handoff(state, meta, events, why) {
      const now = nowOf(state);
      state.humanUntil = new Date(now.getTime() + (cfg.handoff_hours || 2) * 3.6e6).toISOString();
      events.push({ type: "handoff", text: `🙋 ${meta.profileName || state.data.name || "A customer"} (${meta.contact || "web chat"}) ${why}. The bot is paused for ${cfg.handoff_hours || 2} h for this chat; reply to them from the WhatsApp Business app.` });
    }

    // A question in the middle of a booking ("address?", "price entha?") is answered, then the same step is asked again.
    function sideQuestion(state, raw, t) {
      const step = cfg.steps[state.step]; if (!step || step.type === "quiz") return null;
      if (step.type === "date" && parseDate(raw, nowOf(state))) return null;
      if (step.choices) {
        const list = step.field === "slot" ? freeSlots(state, choiceList(step)) : choiceList(step);
        if (/^\d{1,2}$/.test(t) || pickChoice(raw, list) || (step.choices === "catalog" && aliasMatch(raw, cfg.catalog))) return null;
      } else if (step.type !== "date" && !/\?/.test(raw)) return null; // a name like "Priya" is never a question
      const faq = cfg.faqs.find((q) => q.k.some((k) => k.includes(" ") && hasWord(t, k)));
      if (faq) return { text: fill(faq.a, vars()) };
      if (INTENT.prices.test(t)) return catalogReply();
      if (INTENT.hours.test(t)) return hoursReply();
      const one = cfg.faqs.find((q) => q.k.some((k) => k.length >= 4 && hasWord(t, k)));
      return one ? { text: fill(one.a, vars()) } : null;
    }
    function handleStep(state, raw, events, meta) {
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
          state.step++;
          const fb = { text: (ok ? "✅ Correct! " : `❌ Not quite — answer: *${q.o[q.a]}*. `) + q.why };
          return [fb, nextOrFinish(state, events)].flat();
        }
      } else if (step.type === "date") {
        const d = parseDate(raw, nowOf(state));
        if (!d) error = "Sorry, I couldn't read that date (or it's already gone). Try *today*, *tomorrow*, a weekday, or *15/10*.";
        else {
          const why = closedReason(isoOf(d), d);
          if (why) error = `Sorry, ${why} (${fmtDate(d)}) 🙏 Which other day works?`;
          else if ((cfg.max_days_ahead || 60) < Math.round((d - istToday(nowOf(state))) / 864e5)) error = `We take bookings up to ${cfg.max_days_ahead || 60} days ahead. Could you pick a closer date?`;
          else { value = fmtDate(d); state.data.date_iso = isoOf(d); }
        }
      } else if (step.type === "name") {
        let n = String(raw).trim().replace(/^(my name is|i am|i'm|this is|name|naa peru|na peru|mera naam|naam)\s*[:\-]?\s*/i, "").replace(/\s+(hai|ji|garu)$/i, "");
        const forOther = n.match(/^(?:it'?s\s+)?for\s+(?:my\s+)?(?:friend|sister|brother|wife|husband|mother|mom|father|dad|daughter|son|cousin|colleague)?\s*(.+)$/i);
        if (forOther) { n = forOther[1].trim(); state.data.booked_for_someone = true; }
        if (n.length < 2 || n.length > 60 || /^\d+$/.test(n)) error = "Please type the name (letters only).";
        else value = n.replace(/(^|\s)(\p{L})/gu, (m, s, c) => s + c.toUpperCase());
      } else if (step.choices) {
        const list = step.field === "slot" ? freeSlots(state, choiceList(step)) : choiceList(step);
        const num = norm(raw).match(/^(\d{1,2})$/);
        if (step.field === "slot" && num && +num[1] >= 3 && +num[1] <= list.length) { // 1–2 are row numbers; // "4": option 4, or 4 o'clock? ask, like a person would
          const byHour = list.filter((c) => +c.match(/^(\d{1,2})/)[1] === +num[1]);
          const byRow = list[+num[1] - 1];
          if (byHour.length && !byHour.includes(byRow)) return [{ text: `Just to check: ${byHour[0]} or ${byRow}?`, options: [byHour[0], byRow] }];
        }
        const al = step.choices === "catalog" ? aliasMatch(raw, cfg.catalog.filter((c) => list.includes(c.name))) : null;
        if (al && al.ambiguous) return [{ text: `Did you mean ${al.ambiguous.join(" or ")}?`, options: al.ambiguous }];
        value = (al && al.hit) || pickChoice(raw, list);
        if (!value) {
          const sqr = squash(raw); const words = norm(raw).split(" ").filter((w) => w.length >= 3);
          let close = list.filter((c) => sqr.length >= 4 && (squash(c).startsWith(sqr) || squash(c).includes(sqr)));
          if (close.length < 2) close = list.filter((c) => words.some((w) => squash(c).includes(w)));
          if (close.length >= 2 && close.length <= 3) return [{ text: `Did you mean ${close.join(" or ")}?`, options: close }];
          error = "Please choose one of the options (reply with the number).";
        }
        else if (step.choices === "catalog") {
          const item = cfg.catalog.find((c) => c.name === value);
          if (item && item.enquiry) { // e.g. bridal: needs a consultation, not a 1-hour slot
            state.data.service = value; bump(state, "hot", "enquiry"); state.lead.status = "callback"; state.step = -1; delete state.prev;
            handoff(state, meta, events, `asked about ${value}`);
            return [{ text: `${value} needs a quick chat with our ${cfg.enquiry_role || "team"} first, so we get every detail right 💛 I've passed your number on; they'll WhatsApp you shortly (${cfg.hours}).` }];
          }
        }
      } else {
        const v = String(raw).trim(); if (v.length < 2) error = "Could you type that again?"; else value = v.slice(0, 80);
      }
      if (error) return [{ text: error }, askStep(state)];
      state.data[step.field] = value;
      if (step.field === "slot" && Slots && cfg.schedule && cfg.schedule.staff) { // "any stylist": give it to the first one free
        const hit = freeSlotInfo(state, step.choices === "auto" ? "auto" : choiceList(step)).find((x) => x.label === value);
        if (hit && hit.staff.length) state.data.staff = hit.staff[0]; else delete state.data.staff;
      }
      state.step++;
      return nextOrFinish(state, events);
    }

    function nextOrFinish(state, events) {
      const reask = state.rescheduling ? ["date", "slot"] : [];
      while (state.step < cfg.steps.length && state.data[cfg.steps[state.step].field] && !reask.includes(cfg.steps[state.step].field) && cfg.steps[state.step].type !== "quiz") state.step++;
      if (state.step < cfg.steps.length) return [askStep(state)];
      const v = Object.assign(vars(), state.data);
      if (cfg.quiz) {
        const s = state.data.correct || 0; v.score = s; state.data.quiz_score = `${s}/3`;
        v.advice = s === 3 ? "Excellent — you're exam-ready on these topics. The full course has 5 mock tests to keep you sharp." : s === 2 ? "Good — one gap to fix. The 30-day plan targets exactly these weak areas." : "Let's build the basics. Start with the free daily question and chapter-wise practice.";
        delete state.data.correct;
      }
      delete state.prev;
      state.step = -1; state.lead.status = cfg.quiz ? "quiz_done" : "booked"; bump(state, "hot", cfg.quiz ? "quiz" : "booked");
      const optIn = !cfg.quiz && !state.lead.marketing ? "\n\nWant member-only offers (max 2 a month)? Reply *OFFERS*." : "";
      if (!cfg.quiz) {
        const booking = { service: state.data.service || state.data.goal || state.data.bhk || null, date_iso: state.data.date_iso, slot: state.data.slot, name: state.data.name };
        if (Slots && cfg.schedule) { booking.minutes = Slots.durationOf(Slots.schedule(cfg), state.data.service); if (state.data.staff) booking.staff = state.data.staff; }
        events.push({ type: "booking", booking, replaces: state.rescheduling || null });
      }
      if (state.rescheduling) {
        const old = state.rescheduling; delete state.rescheduling;
        events.push({ type: "notify_owner", text: `🔁 Rescheduled: ${state.data.name} · ${state.data.service || ""} · ${old.date} ${old.slot} → ${state.data.date} ${state.data.slot}` });
        return [{ text: "🔁 Done, I've moved it.\n\n" + fill(cfg.confirm, v) }];
      }
      events.push({ type: "notify_owner", text: `🔔 New ${cfg.bookWord}: ${state.data.name}` + (state.data.service ? ` · ${state.data.service}` : "") + (state.data.date ? ` · ${state.data.date} ${state.data.slot || ""}` : "") + (state.data.quiz_score ? ` · score ${state.data.quiz_score}` : "") });
      return [{ text: fill(cfg.confirm, v) + optIn }];
    }

    // Called by the server when the database says the slot was taken a moment ago (race between two customers).
    function slotTaken(stateIn, busy) {
      const state = JSON.parse(JSON.stringify(stateIn));
      state.lead.status = (state.prev && state.prev.status) || "new"; state.step = slotStep();
      const gone = state.data.slot; delete state.data.slot;
      state._busy = (busy || []).concat(Array.from({ length: Math.min(cfg.capacity || 1, 1000) }, () => ({ date_iso: state.data.date_iso, slot: gone, blocked: true })));
      const replies = [{ text: `Oops, someone grabbed ${gone} a second ago 😅 Here's what's still free:` }, askStep(state)];
      delete state._busy;
      return { replies, state };
    }

    function handle(stateIn, text, meta) {
      meta = meta || {};
      const state = JSON.parse(JSON.stringify(stateIn || newState()));
      if (meta.now) state.now = meta.now;
      state._busy = meta.busy || [];
      state.turns++;
      const events = []; let replies = [];
      const raw = String(text || "").trim(); let t = norm(raw);
      const ref = raw.match(/\bREF-[A-Z0-9]{4}\b/i);
      if (ref && !state.data.referred_by) {
        state.data.referred_by = ref[0].toUpperCase(); bump(state, "warm", "referral");
        events.push({ type: "notify_owner", text: `🤝 Referral: a friend of ${ref[0].toUpperCase()} just messaged.` });
        t = norm(raw.replace(ref[0], "")) || "hi";
      }
      const booked = state.lead.status === "booked" && state.step < 0;
      const paused = state.humanUntil && new Date(state.humanUntil) > nowOf(state);

      if (/^(stop|unsubscribe|opt out|stop messages)$/.test(t) && state.optedOut) {
        replies = []; // already unsubscribed: say nothing more
      } else if (/^(stop|unsubscribe|opt out|stop messages)$/.test(t)) {
        state.optedOut = true; state.step = -1; state.lead.status = "opted_out"; state.lead.marketing = false;
        events.push({ type: "opt_out" });
        replies = [{ text: "You're unsubscribed and won't get any more messages from us. Reply *START* any time to come back." }];
      } else if (state.optedOut && !/^start$/.test(t)) {
        replies = [];
      } else if (paused && !/^(bot|menu|start)$/.test(t)) {
        events.push({ type: "forward_to_owner", text: `💬 ${meta.profileName || state.data.name || meta.contact}: ${raw.slice(0, 300)}` });
        replies = []; // a person is handling this chat
      } else if (state.pending === "cancel") {
        delete state.pending;
        if (/^(1|yes|y|confirm|ok|okay|haa|haan|han|avunu|sare|cancel it|yes cancel)\b/.test(t)) {
          state.lead.status = "cancelled";
          events.push({ type: "cancel_booking", booking: { date_iso: state.data.date_iso, slot: state.data.slot, service: state.data.service || null } });
          events.push({ type: "notify_owner", text: `❌ Cancelled: ${state.data.name || "customer"} · ${state.data.service || ""} · ${state.data.date} ${state.data.slot}` });
          replies = [{ text: `Cancelled. No worries at all 🙂 Whenever you're ready, reply *book* and I'll find you a new slot.` }];
        } else replies = [{ text: `Okay, your booking stays as it is: ${state.data.date} at ${state.data.slot}. See you then! 👋` }];
      } else if (booked && CONFIRM.test(t) && !(state.data.date_iso < isoOf(istToday(nowOf(state))))) { // a past visit is not "confirmed"
        state.data.confirmed = true;
        events.push({ type: "confirmed", booking: { date_iso: state.data.date_iso, slot: state.data.slot } });
        replies = [{ text: `✅ Confirmed: ${state.data.service ? state.data.service + ", " : ""}${state.data.date} at ${state.data.slot}. See you! (Reply *menu* for anything else.)` }];
      } else if (booked && (/^2$/.test(t) || /\b(reschedule|postpone|prepone|change (the )?(date|time|day|slot)|another (day|time)|move (my|the) (booking|appointment)|(date|time|day|slot) (marchandi|marchali|marchu|change|badlo|badal do))\b/.test(t))) {
        state.prev = { data: JSON.parse(JSON.stringify(state.data)), status: state.lead.status };
        state.rescheduling = { date: state.data.date, slot: state.data.slot, date_iso: state.data.date_iso };
        state.step = dateStep();
        const head = { text: `No problem! Your current booking is ${state.data.date} at ${state.data.slot}.` };
        const d = parseDate(raw, nowOf(state));
        if (d && !closedReason(isoOf(d), d)) { state.data.date = fmtDate(d); state.data.date_iso = isoOf(d); state.step = slotStep(); }
        replies = [head, askStep(state)];
      } else if (booked && INTENT.cancel.test(t)) {
        state.pending = "cancel";
        replies = [{ text: `Do you want to cancel your ${state.data.service || cfg.bookWord} on ${state.data.date} at ${state.data.slot}? Reply *YES* to cancel, or anything else to keep it.`, options: ["Yes, cancel", "Keep it"] }];
      } else if (/^(offers|offer yes|yes offers)$/.test(t)) {
        state.lead.marketing = true; events.push({ type: "marketing_opt_in" });
        replies = [{ text: "Done 🎉 You'll get member-only offers, max 2 a month. Reply *STOP* any time to stop." }];
      } else if (state.step >= 0 && (/^(cancel|exit|quit|stop booking|vaddu|nahi chahiye)$/.test(t) || (INTENT.cancel.test(t) && t.split(" ").length <= 4 && !parseDate(raw, nowOf(state))))) {
        abandonFlow(state); replies = [menuReply("No problem, stopped. Nothing was changed.")];
      } else if (state.step < 0 && INTENT.cancel.test(t) && !/\b(policy|charges?|fee|rules?|membership|plan|subscription|order)\b/.test(t)) { // "booking cancel cheyyandi" with nothing booked
        replies = [menuReply("You don't have an upcoming booking with us, so there's nothing to cancel 🙂")];
      } else if (state.step >= 0 && !GREET.test(t) && sideQuestion(state, raw, t)) { // Rasa-style digression: answer, then re-ask
        replies = [sideQuestion(state, raw, t), askStep(state)];
      } else if (state.step >= 0 && !GREET.test(t)) {
        replies = handleStep(state, raw, events, meta);
      } else if (!t) {
        replies = [menuReply()];
      } else if (GREET.test(t) || /^(start|bot)$/.test(t)) {
        if (state.step >= 0) abandonFlow(state);
        state.optedOut = false; delete state.humanUntil;
        const known = meta.known || {};
        const first = known.name
          ? `Welcome back, ${known.name.split(" ")[0]}! 😊` + (known.lastService ? ` Same *${known.lastService}* as last time? Reply *1* and I'll find you a slot.` : "")
          : state.turns === 1 ? fill(cfg.greeting, vars()) : `Welcome back to *${cfg.business}* 😊`;
        replies = [menuReply(first)];
      } else {
        let key = null;
        if (/^\d$/.test(t) && +t >= 1 && +t <= cfg.menu.length) key = cfg.menu[+t - 1].key;
        else { const m = cfg.menu.find((x) => norm(x.label) === t); if (m) key = m.key; }
        let faq = null;
        if (!key) faq = cfg.faqs.find((q) => q.k.some((k) => k.includes(" ") && hasWord(t, k))); // multi-word FAQ phrases win ("home visit")
        if (!key && !faq) {
          if (cfg.guardWords && cfg.guardWords.some((w) => t.includes(w))) key = "guard";
          else if (INTENT.human.test(t)) key = "human";
          else if (INTENT.haggle.test(t)) key = "haggle";
          else if (INTENT.book.test(t) || /\b(visit)\b/.test(t)) key = "book";
          else if (INTENT.prices.test(t)) key = "prices";
          else if (INTENT.hours.test(t)) key = "hours";
        }
        if (!key && !faq) faq = cfg.faqs.find((q) => q.k.some((k) => hasWord(t, k)));
        if (faq && !key) { replies = [{ text: fill(faq.a, vars()) + "\n\nReply *menu* for more options." }]; bump(state, "warm", "faq"); }
        if (key === "book") replies = startFlow(state, meta, raw);
        else if (key === "prices") { replies = [catalogReply()]; bump(state, "warm", "prices"); }
        else if (key === "hours") { replies = [hoursReply()]; bump(state, "cold", "hours"); }
        else if (key === "guard") replies = [{ text: cfg.guard }];
        else if (key === "haggle") { // fixed prices, real offers only — never invent a discount
          const offer = cfg.faqs.find((q) => q.id === "offers" || q.k.includes("offer") || q.k.includes("offers"));
          replies = [{ text: `I understand 🙏 Our prices are fixed so every customer gets the same fair price.` + (offer ? `\n\nGood news though: ${fill(offer.a, vars())}` : "") + `\n\nShall I book you a slot? Reply *1*.` }];
          bump(state, "warm", "haggle");
        }
        else if (key === "human") {
          if (state.lead.status !== "booked") state.lead.status = "callback"; bump(state, "warm", "human");
          handoff(state, meta, events, "wants to talk to a person");
          replies = [{ text: `Sure 🙂 I've told the team — someone from *${cfg.business}* will message you here shortly (working hours: ${cfg.hours}). You can also call ${cfg.phone}. Type *bot* to come back to me.` }];
        } else if (key && key.startsWith("faq:")) {
          const f = cfg.faqs.find((q) => q.id === key.slice(4));
          replies = [{ text: fill(f.a, vars()) + "\n\nReply *menu* for more options." }]; bump(state, "warm", "faq");
        }
        if (!replies.length) {
          events.push({ type: "unanswered", text: raw });
          replies = [menuReply("Sorry, I didn't quite get that. I can help with these:")];
        }
      }
      delete state._busy;
      return { replies, state, lead: leadSnapshot(state, meta), events };
    }

    return { config: cfg, handle, slotTaken };
  }

  return { NICHES, register, createBot, newState, parseDate, pickChoice, istToday, isoOf, Slots, version: "3.1.0" };
});

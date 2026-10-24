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
    human: /\b(human|agent|person|call me|callback|call back|talk to|speak to|reception|advisor|owner|manager|staff|matladali|matladatanu|baat karni|baat karna)\b|మాట్లాడాలి|మాట్లాడతాను|బాత్ కరనీ|बात करनी|बात करना|बात करें/,
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

  // ---------------------------------------------------------------- bridal / high-value enquiries (A12, T15)
  // Wedding words that open the enquiry flow (only for setups whose catalog has an `enquiry: true` item).
  const BRIDAL = /\b(bridal|bride|wedding|marriage|pelli|pelliki|shaadi|shadi|engagement|nischitartham|haldi|mehendi|mehndi|sangeet|muhurtham|muhurat)\b|పెళ్లి|పెళ్ళి|शादी|दुल्हन/;
  const EVENT_TYPES = [
    ["wedding", /\b(wedding|marriage|pelli|pelliki|shaadi|shadi|muhurtham|muhurat)\b|పెళ్లి|పెళ్ళి|शादी/],
    ["haldi", /\b(haldi|pasupu|mangala ?snanam)\b|హల్దీ|हल्दी/],
    ["mehendi", /\b(mehendi|mehndi|henna)\b|మెహందీ|मेहंदी/],
    ["sangeet", /\bsangeet\b|संगीत/],
    ["engagement", /\b(engagement|nischitartham|ring ceremony)\b/],
    ["reception", /\breception\b/],
  ];
  const MON = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec";
  // "22 Jan", "Jan 22nd", "22/1", or "20th" (month taken from another date in the same message)
  function clauseDate(c, monthCtx, now) {
    let m = c.match(new RegExp(`\\b(\\d{1,2})(?:st|nd|rd|th)?\\s*(?:of\\s+)?(${MON})[a-z]*\\b`));
    if (m) return parseDate(`${m[1]} ${m[2]}`, now);
    m = c.match(new RegExp(`\\b(${MON})[a-z]*\\s+(\\d{1,2})(?:st|nd|rd|th)?\\b`));
    if (m) return parseDate(`${m[2]} ${m[1]}`, now);
    m = c.match(/\b\d{1,2}\s*[\/\-.]\s*\d{1,2}(?:\s*[\/\-.]\s*\d{2,4})?\b/);
    if (m) return parseDate(m[0], now);
    m = c.match(/\b(\d{1,2})(?:st|nd|rd|th)\b/);
    if (m && monthCtx) return parseDate(`${m[1]} ${monthCtx}`, now);
    return null;
  }
  // Returns [{ type, date_iso }] in the order the customer wrote them.
  function parseEvents(raw, now) {
    const low = String(raw || "").toLowerCase();
    const mc = low.match(new RegExp(`\\b(${MON})[a-z]*\\b`)); const monthCtx = mc ? mc[1] : null;
    const out = []; let orphan = null;
    for (const c of low.split(/[,;\n&]|\band\b|\balso\b|\bthen\b/)) {
      const types = EVENT_TYPES.filter(([, re]) => re.test(c)).map(([k]) => k);
      const d = clauseDate(c, monthCtx, now); const iso = d ? isoOf(d) : null;
      if (types.length) for (const k of types) { if (!out.some((e) => e.type === k)) out.push({ type: k, date_iso: iso }); }
      else if (iso) { const open = out.find((e) => !e.date_iso); if (open) open.date_iso = iso; else if (!orphan) orphan = iso; }
    }
    if (orphan && !out.some((e) => e.type === "wedding")) out.unshift({ type: "wedding", date_iso: orphan });
    return out;
  }
  // "50k", "₹40,000", "1.5 lakh", "75 thousand" → rupees; anything vaguer → null (never guessed)
  function parseBudget(raw) {
    const t = String(raw || "").toLowerCase().replace(/(\d),(?=\d)/g, "$1");
    for (const m of t.matchAll(/(\d+(?:\.\d+)?)\s*(k\b|thousand|lakhs?\b|lacs?\b|l\b)?/g)) {
      const v = parseFloat(m[1]); const unit = m[2] || "";
      if (/^k|thousand/.test(unit)) return Math.round(v * 1e3);
      if (/^(l|lakh|lac)/.test(unit)) return Math.round(v * 1e5);
      if (v >= 1000) return Math.round(v);
    }
    return null;
  }
  // Customer's name from "my name is priya", "Sravani garu" → "Priya" / "Sravani"
  function nameFrom(raw) {
    let n = String(raw).trim().replace(/^(my name is|i am|i'm|this is|name|naa peru|na peru|mera naam|naam)\s*[:\-]?\s*/i, "").replace(/\s+(hai|ji|garu)$/i, "");
    let forOther = false;
    const fo = n.match(/^(?:it'?s\s+)?for\s+(?:my\s+)?(?:friend|sister|brother|wife|husband|mother|mom|father|dad|daughter|son|cousin|colleague)?\s*(.+)$/i);
    if (fo) { n = fo[1].trim(); forOther = true; }
    if (n.length < 2 || n.length > 60 || /^\d+$/.test(n)) return { error: "Please type the name (letters only)." };
    return { value: n.replace(/(^|\s)(\p{L})/gu, (m, s, c) => s + c.toUpperCase()), forOther };
  }

  // ---------------------------------------------------------------- reply language (A73)
  // The customer gets replies in Telugu or Hindi when they write in that script, tap a language, or type
  // "telugu" / "hindi" / "english". Tenglish / Hinglish typed in English letters gets replies the same way
  // ("tg" / "hg", Roman script; service names, dates and times stay in English letters).
  // Owner alerts stay in English. Translations: Claude, 22 Oct 2026; a Telugu speaker reviews before go-live.
  const LANG_PICK = {
    te: /^(telugu|telugulo|telugu lo|telugu please|తెలుగు|తెలుగులో)$/,
    hi: /^(hindi|hindi me|hindi mein|hindi please|हिंदी|हिन्दी|हिंदी में)$/,
    en: /^(english|english please|english lo|english me|ఇంగ్లీష్|इंग्लिश)$/,
    tg: /^(tenglish|telugu in english)$/,
    hg: /^(hinglish|hindi in english)$/,
  };
  // Words that mark Tenglish / Hinglish in English letters (counted; the bigger count wins, a tie changes nothing)
  const ROMAN = {
    tg: /(^|\s)(kavali|kaavali|kavala|repu|reypu|ellundi|ivala|ivvala|cheyyandi|cheyyali|cheyyi|cheyandi|chestara|cheppandi|entha|enta|ekkada|eppudu|undi|unda|ledu|avunu|sare|vastanu|vasthanu|vastam|sayantram|saayantram|poddunna|madhyanam|garu|naaku|naku|meeru|meeku|ivvandi|kaadu|emaina|bagundi|baagundi|enti|pelli|intiki|matladali|chesko|teeskuntara|marchandi|raddu|thagginchandi)(?=\s|$)/g,
    hg: /(^|\s)(chahiye|chaiye|kitna|kitne|kitni|hai|hain|kya|karo|kijiye|karna|karni|karwana|mujhe|mera|meri|mere|aaj|kal|parso|shaam|sham|subah|haan|nahi|nahin|kab|kahan|kidhar|bhai|aap|aapka|aapke|batao|bataiye|shaadi|ghar|chahta|chahti|wala|wali|badlo|kam)(?=\s|$)/g,
  };
  const SCRIPT = { te: /[ఀ-౿]/, hi: /[ऀ-ॿ]/ };
  const DAY_L = { te: ["ఆది", "సోమ", "మంగళ", "బుధ", "గురు", "శుక్ర", "శని"], hi: ["रवि", "सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि"] };
  const MON_L = {
    te: ["జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్", "జులై", "ఆగస్టు", "సెప్టెంబర్", "అక్టోబర్", "నవంబర్", "డిసెంబర్"],
    hi: ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"],
  };
  const EVENT_L = {
    te: { wedding: "పెళ్లి", haldi: "హల్దీ", mehendi: "మెహందీ", sangeet: "సంగీత్", engagement: "నిశ్చితార్థం", reception: "రిసెప్షన్" },
    hi: { wedding: "शादी", haldi: "हल्दी", mehendi: "मेहंदी", sangeet: "संगीत", engagement: "सगाई", reception: "रिसेप्शन" },
    tg: { wedding: "Pelli", haldi: "Haldi", mehendi: "Mehendi", sangeet: "Sangeet", engagement: "Nischitartham", reception: "Reception" },
    hg: { wedding: "Shaadi", haldi: "Haldi", mehendi: "Mehendi", sangeet: "Sangeet", engagement: "Sagai", reception: "Reception" },
  };
  const STR = {
    en: {
      menuAsk: "How can I help? Reply with a number:", catalogFoot: "Reply *1* to book your {bookWord}.",
      closedToday: "Sorry, we're {note} 🙏 How about tomorrow? (or pick any other day)", pastSlots: "Today's slots are over 🌙 How about tomorrow? (or pick any other day)",
      fullyBooked: "Sorry, {day} is fully booked 😕 Which other day works for you?", optTomorrow: "Tomorrow", optDayAfter: "Day after tomorrow",
      quizIntro: "Let's go! 3 quick questions.", sureHeard: "Sure! {heard} 👍", letsBook: "Great, let's book your {bookWord}. Type *cancel* any time to stop.",
      missedTime: "{m} isn't free that day, so pick a time below.", missedShort: "{m} isn't free that day.", slotBooked: "Sorry, {m} is already booked that day 🙏 Closest free: {near}.", slotNotOffered: "We don't have a {m} slot 🙏 Closest free: {near}.", slotLate: "Sorry, {m} is too late for us. Our last booking is {last}{hours}. Closest free: {near}.", slotEarly: "Sorry, {m} is too early for us. Our first booking is {first}{hours}. Closest free: {near}.",
      replyABCD: "Please reply A, B, C or D.", correct: "✅ Correct! ", notQuite: "❌ Not quite — answer: *{ans}*. ",
      dateErr: "Sorry, I couldn't read that date (or it's already gone). Try *today*, *tomorrow*, a weekday, or *15/10*.",
      closedDay: "Sorry, {why} ({date}) 🙏 Which other day works?", tooFar: "We take bookings up to {n} days ahead. Could you pick a closer date?",
      justCheck: "Just to check: {a} or {b}?", didYouMean: "Did you mean {list}?", or: " or ", chooseOption: "Please choose one of the options (reply with the number).",
      typeAgain: "Could you type that again?", gotIt: "Got it: {got} 👍", nameErr: "Please type the name (letters only).",
      moved: "🔁 Done, I've moved it.\n\n", grabbed: "Oops, someone grabbed {gone} a second ago 😅 Here's what's still free:",
      unsub: "You're unsubscribed and won't get any more messages from us. Reply *START* any time to come back.",
      cancelled: "Cancelled. No worries at all 🙂 Whenever you're ready, reply *book* and I'll find you a new slot.",
      keep: "Okay, your booking stays as it is: {date} at {slot}. See you then! 👋",
      confirmed: "✅ Confirmed: {svc}{date} at {slot}. See you! (Reply *menu* for anything else.)",
      reschedHead: "No problem! Your current booking is {date} at {slot}.",
      askCancel: "Do you want to cancel your {what} on {date} at {slot}? Reply *YES* to cancel, or anything else to keep it.", optYesCancel: "Yes, cancel", optKeep: "Keep it",
      offersDone: "Done 🎉 You'll get member-only offers, max 2 a month. Reply *STOP* any time to stop.",
      stopped: "No problem, stopped. Nothing was changed.", nothingToCancel: "You don't have an upcoming booking with us, so there's nothing to cancel 🙂",
      welcomeBack: "Welcome back, {name}! 😊", sameAgain: " Same *{svc}* as last time? Reply *1* and I'll find you a slot.", welcomeBiz: "Welcome back to *{business}* 😊",
      menuMore: "Reply *menu* for more options.", haggle: "I understand 🙏 Our prices are fixed so every customer gets the same fair price.",
      haggleOffer: "\n\nGood news though: {offer}", haggleBook: "\n\nShall I book you a slot? Reply *1*.",
      human: "Sure 🙂 I've told the team — someone from *{business}* will message you here shortly (working hours: {hours}). You can also call {phone}. Type *bot* to come back to me.",
      sorry: "Sorry, I didn't quite get that. I can help with these:", optIn: "\n\nWant member-only offers (max 2 a month)? Reply *OFFERS*.",
      congrats: "💍 Congratulations! Our *{item}* packages are *{price}*, and every package includes a trial.",
      askEvents: "Which events, and on which dates? (e.g. *wedding 22 Jan, haldi 20 Jan*)", askBudget: "What budget do you have in mind for the whole package? (e.g. *50k*, or *not decided*)",
      askName: "Lovely! And your name, please?", gotDates: "Got it 👍\n📅 {events}", noDates: "No problem, our artist will confirm dates with you 👍",
      cantCatch: "Sorry, I couldn't catch a date 🙏 {ask} Or just say *not fixed yet*.", toConfirm: "(date to confirm)",
      fullDate: "So sorry 🙏 our {role} is fully committed on {date}. I've asked the owner to call you; they may be able to suggest another artist or arrangement.",
      thanks: "Thank you, {name} 💛 Our {role} has your details and will WhatsApp you shortly ({hours}).\n\nWould you like to book your *bridal trial* now? It's included in the package.",
      optTrial: "Book a bridal trial", optArtist: "Talk to the artist", trialStart: "Lovely! Let's book your *{trial}* 💄 Type *cancel* any time to stop.", team: "team", artist: "artist",
      adv3: "Excellent — you're exam-ready on these topics. The full course has 5 mock tests to keep you sharp.",
      adv2: "Good — one gap to fix. The 30-day plan targets exactly these weak areas.", adv1: "Let's build the basics. Start with the free daily question and chapter-wise practice.",
    },
    te: {
      menuAsk: "మీకు ఎలా సహాయం చేయగలను? నంబర్‌తో రిప్లై ఇవ్వండి:", catalogFoot: "బుక్ చేయడానికి *1* అని పంపండి.",
      closedToday: "క్షమించండి, ఈరోజు మేము మూసి ఉన్నాం 🙏 రేపు ఎలా ఉంటుంది? (లేదా వేరే ఏ రోజైనా ఎంచుకోండి)", pastSlots: "ఈరోజు స్లాట్లు అయిపోయాయి 🌙 రేపు ఎలా ఉంటుంది? (లేదా వేరే ఏ రోజైనా ఎంచుకోండి)",
      fullyBooked: "క్షమించండి, {day} పూర్తిగా బుక్ అయిపోయింది 😕 మీకు వేరే ఏ రోజు వీలవుతుంది?", optTomorrow: "రేపు", optDayAfter: "ఎల్లుండి",
      quizIntro: "మొదలుపెడదాం! 3 చిన్న ప్రశ్నలు.", sureHeard: "సరే! {heard} 👍", letsBook: "సరే, మీ {bookWord} బుక్ చేద్దాం. ఆపాలంటే ఎప్పుడైనా *cancel* అని టైప్ చేయండి.",
      missedTime: "ఆ రోజు {m} ఖాళీ లేదు, కింద ఉన్న సమయాల్లో ఒకటి ఎంచుకోండి.", missedShort: "ఆ రోజు {m} ఖాళీ లేదు.", slotBooked: "క్షమించండి, ఆ రోజు {m} ఇప్పటికే బుక్ అయింది 🙏 దగ్గరలో ఖాళీ: {near}.", slotNotOffered: "మా దగ్గర {m} స్లాట్ లేదు 🙏 దగ్గరలో ఖాళీ: {near}.", slotLate: "క్షమించండి, {m} చాలా ఆలస్యం. మా చివరి బుకింగ్ {last}{hours}. దగ్గరలో ఖాళీ: {near}.", slotEarly: "క్షమించండి, {m} చాలా ముందు. మా మొదటి బుకింగ్ {first}{hours}. దగ్గరలో ఖాళీ: {near}.",
      replyABCD: "దయచేసి A, B, C లేదా D అని పంపండి.", correct: "✅ సరైన జవాబు! ", notQuite: "❌ కాదు — సరైన జవాబు: *{ans}*. ",
      dateErr: "క్షమించండి, ఆ తేదీ అర్థం కాలేదు (లేదా అది అయిపోయింది). *ఈరోజు*, *రేపు*, ఒక వారం రోజు, లేదా *15/10* లా టైప్ చేయండి.",
      closedDay: "క్షమించండి, {date} న మేము మూసి ఉన్నాం 🙏 వేరే ఏ రోజు వీలవుతుంది?", tooFar: "మేము {n} రోజుల ముందు వరకే బుకింగ్ తీసుకుంటాం. దగ్గరి తేదీ ఎంచుకుంటారా?",
      justCheck: "ఒక్కసారి చెప్పండి: {a} కావాలా, {b} కావాలా?", didYouMean: "మీకు కావాల్సింది {list}?", or: " లేదా ", chooseOption: "దయచేసి ఆప్షన్లలో ఒకటి ఎంచుకోండి (నంబర్‌తో రిప్లై ఇవ్వండి).",
      typeAgain: "మళ్లీ ఒకసారి టైప్ చేస్తారా?", gotIt: "అర్థమైంది: {got} 👍", nameErr: "దయచేసి పేరు టైప్ చేయండి (అక్షరాలు మాత్రమే).",
      moved: "🔁 అయిపోయింది, మీ బుకింగ్ మార్చాను.\n\n", grabbed: "అయ్యో, {gone} ఇప్పుడే వేరేవాళ్లు తీసుకున్నారు 😅 ఇంకా ఖాళీగా ఉన్నవి ఇవి:",
      unsub: "మీరు అన్‌సబ్‌స్క్రైబ్ అయ్యారు, ఇకపై మా నుంచి మెసేజ్‌లు రావు. మళ్లీ రావాలంటే ఎప్పుడైనా *START* అని పంపండి.",
      cancelled: "క్యాన్సిల్ అయింది. పర్వాలేదు 🙂 మళ్లీ కావాలంటే *book* అని పంపండి, కొత్త స్లాట్ చూస్తాను.",
      keep: "సరే, మీ బుకింగ్ అలాగే ఉంది: {date}, {slot}. కలుద్దాం! 👋",
      confirmed: "✅ కన్ఫర్మ్ అయింది: {svc}{date}, {slot}. కలుద్దాం! (ఇంకేమైనా కావాలంటే *menu* అని పంపండి.)",
      reschedHead: "సరే! మీ ప్రస్తుత బుకింగ్: {date}, {slot}.",
      askCancel: "{date}, {slot} కి ఉన్న మీ {what} క్యాన్సిల్ చేయాలా? క్యాన్సిల్ చేయాలంటే *YES* అని, ఉంచాలంటే ఇంకేదైనా పంపండి.", optYesCancel: "అవును, క్యాన్సిల్", optKeep: "ఉంచండి",
      offersDone: "అయిపోయింది 🎉 మెంబర్లకు మాత్రమే ఆఫర్లు, నెలకు గరిష్ఠంగా 2 వస్తాయి. ఆపాలంటే ఎప్పుడైనా *STOP* అని పంపండి.",
      stopped: "సరే, ఆపేశాను. ఏమీ మారలేదు.", nothingToCancel: "మీకు రాబోయే బుకింగ్ ఏదీ లేదు, కాబట్టి క్యాన్సిల్ చేయడానికి ఏమీ లేదు 🙂",
      welcomeBack: "మళ్లీ స్వాగతం, {name}! 😊", sameAgain: " గతసారిలాగే *{svc}* కావాలా? *1* అని పంపండి, స్లాట్ చూస్తాను.", welcomeBiz: "*{business}* కి మళ్లీ స్వాగతం 😊",
      menuMore: "ఇంకా ఆప్షన్ల కోసం *menu* అని పంపండి.", haggle: "అర్థమైంది 🙏 అందరికీ ఒకే న్యాయమైన ధర ఉండాలని మా ధరలు ఫిక్స్‌డ్‌గా ఉంటాయి.",
      haggleOffer: "\n\nఒక మంచి వార్త: {offer}", haggleBook: "\n\nస్లాట్ బుక్ చేయమంటారా? *1* అని పంపండి.",
      human: "సరే 🙂 టీమ్‌కి చెప్పాను, *{business}* నుంచి ఎవరైనా త్వరలో ఇక్కడే మెసేజ్ చేస్తారు (పని వేళలు: {hours}). {phone} కి కాల్ కూడా చేయవచ్చు. నా దగ్గరికి తిరిగి రావాలంటే *bot* అని టైప్ చేయండి.",
      sorry: "క్షమించండి, సరిగ్గా అర్థం కాలేదు. నేను వీటిలో సహాయం చేయగలను:", optIn: "\n\nమెంబర్లకు మాత్రమే ఆఫర్లు కావాలా (నెలకు గరిష్ఠంగా 2)? *OFFERS* అని పంపండి.",
      congrats: "💍 అభినందనలు! మా *{item}* ప్యాకేజీలు *{price}*, ప్రతి ప్యాకేజీలో ఒక ట్రయల్ ఉంటుంది.",
      askEvents: "ఏ ఫంక్షన్లు, ఏ తేదీల్లో? (ఉదా: *పెళ్లి 22 Jan, హల్దీ 20 Jan*)", askBudget: "మొత్తం ప్యాకేజీకి మీ బడ్జెట్ ఎంత? (ఉదా: *50k*, లేదా *ఇంకా అనుకోలేదు*)",
      askName: "బాగుంది! మీ పేరు చెప్తారా?", gotDates: "అర్థమైంది 👍\n📅 {events}", noDates: "పర్వాలేదు, మా ఆర్టిస్ట్ తేదీలు మీతో కన్ఫర్మ్ చేస్తారు 👍",
      cantCatch: "క్షమించండి, తేదీ అర్థం కాలేదు 🙏 {ask} లేదా *ఇంకా ఫిక్స్ కాలేదు* అని చెప్పండి.", toConfirm: "(తేదీ ఇంకా ఖరారు కాలేదు)",
      fullDate: "క్షమించండి 🙏 {date} న మా {role} ఖాళీగా లేరు. ఓనర్‌ని మీకు కాల్ చేయమని చెప్పాను; వేరే ఆర్టిస్ట్ లేదా ఏర్పాటు సూచించగలరు.",
      thanks: "ధన్యవాదాలు, {name} 💛 మా {role} దగ్గర మీ వివరాలు ఉన్నాయి, త్వరలో WhatsApp చేస్తారు ({hours}).\n\nఇప్పుడే మీ *బ్రైడల్ ట్రయల్* బుక్ చేయాలా? అది ప్యాకేజీలోనే ఉంది.",
      optTrial: "బ్రైడల్ ట్రయల్ బుక్ చేయండి", optArtist: "ఆర్టిస్ట్‌తో మాట్లాడాలి", trialStart: "బాగుంది! మీ *{trial}* బుక్ చేద్దాం 💄 ఆపాలంటే ఎప్పుడైనా *cancel* అని టైప్ చేయండి.", team: "టీమ్", artist: "ఆర్టిస్ట్",
      adv3: "అద్భుతం — ఈ టాపిక్‌లలో మీరు పరీక్షకు సిద్ధంగా ఉన్నారు. పూర్తి కోర్సులో 5 మాక్ టెస్టులు ఉన్నాయి.",
      adv2: "బాగుంది — ఒక లోటు సరిచేయాలి. 30 రోజుల ప్లాన్ సరిగ్గా ఈ బలహీన అంశాలపైనే పనిచేస్తుంది.", adv1: "బేసిక్స్ నుంచి మొదలుపెడదాం. ఉచిత రోజువారీ ప్రశ్న, చాప్టర్ వారీ ప్రాక్టీస్‌తో మొదలుపెట్టండి.",
    },
    hi: {
      menuAsk: "मैं कैसे मदद करूँ? नंबर से जवाब दें:", catalogFoot: "बुक करने के लिए *1* भेजें.",
      closedToday: "माफ़ कीजिए, आज हम बंद हैं 🙏 कल कैसा रहेगा? (या कोई और दिन चुनें)", pastSlots: "आज के स्लॉट ख़त्म हो गए 🌙 कल कैसा रहेगा? (या कोई और दिन चुनें)",
      fullyBooked: "माफ़ कीजिए, {day} पूरा बुक है 😕 आपके लिए और कौन सा दिन ठीक रहेगा?", optTomorrow: "कल", optDayAfter: "परसों",
      quizIntro: "चलिए शुरू करते हैं! 3 छोटे सवाल.", sureHeard: "ज़रूर! {heard} 👍", letsBook: "ठीक है, आपका {bookWord} बुक करते हैं. रोकने के लिए कभी भी *cancel* लिखें.",
      missedTime: "उस दिन {m} खाली नहीं है, नीचे से कोई समय चुनें.", missedShort: "उस दिन {m} खाली नहीं है.", slotBooked: "माफ़ कीजिए, उस दिन {m} पहले से बुक है 🙏 सबसे पास खाली: {near}.", slotNotOffered: "हमारे यहाँ {m} का स्लॉट नहीं है 🙏 सबसे पास खाली: {near}.", slotLate: "माफ़ कीजिए, {m} बहुत देर है. हमारी आख़िरी बुकिंग {last} है{hours}. सबसे पास खाली: {near}.", slotEarly: "माफ़ कीजिए, {m} बहुत जल्दी है. हमारी पहली बुकिंग {first} है{hours}. सबसे पास खाली: {near}.",
      replyABCD: "कृपया A, B, C या D भेजें.", correct: "✅ सही जवाब! ", notQuite: "❌ नहीं — सही जवाब: *{ans}*. ",
      dateErr: "माफ़ कीजिए, यह तारीख़ समझ नहीं आई (या निकल चुकी है). *आज*, *कल*, कोई दिन, या *15/10* लिखें.",
      closedDay: "माफ़ कीजिए, {date} को हम बंद हैं 🙏 और कौन सा दिन ठीक रहेगा?", tooFar: "हम {n} दिन आगे तक ही बुकिंग लेते हैं. कोई नज़दीक की तारीख़ चुनेंगे?",
      justCheck: "बस पक्का कर लूँ: {a} या {b}?", didYouMean: "क्या आपका मतलब {list} है?", or: " या ", chooseOption: "कृपया कोई एक विकल्प चुनें (नंबर से जवाब दें).",
      typeAgain: "क्या आप फिर से लिख सकते हैं?", gotIt: "समझ गया: {got} 👍", nameErr: "कृपया नाम लिखें (सिर्फ़ अक्षर).",
      moved: "🔁 हो गया, मैंने बुकिंग बदल दी है.\n\n", grabbed: "अरे, {gone} अभी-अभी किसी और ने ले लिया 😅 अभी ये खाली हैं:",
      unsub: "आपका सब्सक्रिप्शन बंद हो गया, अब हमसे कोई मैसेज नहीं आएगा. वापस आने के लिए कभी भी *START* भेजें.",
      cancelled: "कैंसिल हो गया. कोई बात नहीं 🙂 जब चाहें *book* भेजें, मैं नया स्लॉट ढूँढ दूँगा.",
      keep: "ठीक है, आपकी बुकिंग वैसी ही है: {date}, {slot}. मिलते हैं! 👋",
      confirmed: "✅ पक्का हो गया: {svc}{date}, {slot}. मिलते हैं! (कुछ और चाहिए तो *menu* भेजें.)",
      reschedHead: "कोई बात नहीं! आपकी अभी की बुकिंग: {date}, {slot}.",
      askCancel: "क्या आप {date}, {slot} वाला अपना {what} कैंसिल करना चाहते हैं? कैंसिल के लिए *YES* भेजें, रखने के लिए कुछ और.", optYesCancel: "हाँ, कैंसिल", optKeep: "रहने दें",
      offersDone: "हो गया 🎉 आपको सिर्फ़ मेंबर वाले ऑफ़र मिलेंगे, महीने में ज़्यादा से ज़्यादा 2. रोकने के लिए कभी भी *STOP* भेजें.",
      stopped: "ठीक है, रोक दिया. कुछ नहीं बदला.", nothingToCancel: "आपकी कोई आने वाली बुकिंग नहीं है, इसलिए कैंसिल करने को कुछ नहीं है 🙂",
      welcomeBack: "फिर से स्वागत है, {name}! 😊", sameAgain: " पिछली बार की तरह *{svc}*? *1* भेजें, मैं स्लॉट ढूँढ दूँगा.", welcomeBiz: "*{business}* में फिर से स्वागत है 😊",
      menuMore: "और विकल्पों के लिए *menu* भेजें.", haggle: "मैं समझता हूँ 🙏 हमारे दाम फ़िक्स हैं ताकि हर ग्राहक को एक जैसा सही दाम मिले.",
      haggleOffer: "\n\nएक अच्छी ख़बर: {offer}", haggleBook: "\n\nक्या मैं आपका स्लॉट बुक कर दूँ? *1* भेजें.",
      human: "ज़रूर 🙂 मैंने टीम को बता दिया है, *{business}* से कोई जल्द ही यहीं मैसेज करेगा (काम का समय: {hours}). आप {phone} पर कॉल भी कर सकते हैं. मेरे पास वापस आने के लिए *bot* लिखें.",
      sorry: "माफ़ कीजिए, मैं ठीक से समझ नहीं पाया. मैं इनमें मदद कर सकता हूँ:", optIn: "\n\nसिर्फ़ मेंबर वाले ऑफ़र चाहिए (महीने में ज़्यादा से ज़्यादा 2)? *OFFERS* भेजें.",
      congrats: "💍 बधाई हो! हमारे *{item}* पैकेज *{price}* के हैं, और हर पैकेज में एक ट्रायल शामिल है.",
      askEvents: "कौन से फ़ंक्शन, और किन तारीख़ों पर? (जैसे *शादी 22 Jan, हल्दी 20 Jan*)", askBudget: "पूरे पैकेज के लिए आपका बजट कितना है? (जैसे *50k*, या *अभी तय नहीं*)",
      askName: "बढ़िया! आपका नाम बताएँगे?", gotDates: "समझ गया 👍\n📅 {events}", noDates: "कोई बात नहीं, हमारी आर्टिस्ट आपसे तारीख़ें पक्की कर लेंगी 👍",
      cantCatch: "माफ़ कीजिए, तारीख़ समझ नहीं आई 🙏 {ask} या बस *अभी तय नहीं* लिखें.", toConfirm: "(तारीख़ पक्की होनी है)",
      fullDate: "माफ़ कीजिए 🙏 {date} को हमारी {role} खाली नहीं हैं. मैंने ओनर को आपको कॉल करने को कहा है; वे कोई और आर्टिस्ट या इंतज़ाम सुझा सकते हैं.",
      thanks: "धन्यवाद, {name} 💛 हमारी {role} के पास आपकी जानकारी है, वे जल्द ही WhatsApp करेंगी ({hours}).\n\nक्या अभी अपना *ब्राइडल ट्रायल* बुक करें? यह पैकेज में शामिल है.",
      optTrial: "ब्राइडल ट्रायल बुक करें", optArtist: "आर्टिस्ट से बात करनी है", trialStart: "बढ़िया! आपका *{trial}* बुक करते हैं 💄 रोकने के लिए कभी भी *cancel* लिखें.", team: "टीम", artist: "आर्टिस्ट",
      adv3: "शानदार — इन टॉपिक्स पर आप परीक्षा के लिए तैयार हैं. पूरे कोर्स में 5 मॉक टेस्ट हैं.",
      adv2: "अच्छा — एक कमी दूर करनी है. 30 दिन का प्लान इन्हीं कमज़ोर हिस्सों पर काम करता है.", adv1: "चलिए बेसिक्स से शुरू करते हैं. मुफ़्त रोज़ाना सवाल और चैप्टर के हिसाब से प्रैक्टिस से शुरू करें.",
    },
    tg: {
      menuAsk: "Meeku ela help cheyyali? Number tho reply ivvandi:", catalogFoot: "Book cheyyadaniki *1* ani pampandi.",
      closedToday: "Sorry andi, ee roju memu close 🙏 Repu ela untundi? (leda vere roju cheppandi)", pastSlots: "Ee roju slots aipoyayi 🌙 Repu ela untundi? (leda vere roju cheppandi)",
      fullyBooked: "Sorry andi, {day} full ga book aipoyindi 😕 Vere ye roju meeku kudurutundi?", optTomorrow: "Repu", optDayAfter: "Ellundi",
      quizIntro: "Start cheddam! 3 chinna questions.", sureHeard: "Sare! {heard} 👍", letsBook: "Sare, mee {bookWord} book cheddam. Aapalante eppudaina *cancel* ani type cheyyandi.",
      missedTime: "Aa roju {m} free ledu, kinda unna times lo okati choose cheyyandi.", missedShort: "Aa roju {m} free ledu.", slotBooked: "Sorry andi, aa roju {m} already book ayyindi 🙏 Daggaralo free: {near}.", slotNotOffered: "Maa daggara {m} slot ledu 🙏 Daggaralo free: {near}.", slotLate: "Sorry andi, {m} chala late. Maa last booking {last}{hours}. Daggaralo free: {near}.", slotEarly: "Sorry andi, {m} chala early. Maa first booking {first}{hours}. Daggaralo free: {near}.",
      replyABCD: "Please A, B, C leda D ani reply ivvandi.", correct: "✅ Correct! ", notQuite: "❌ Kaadu — answer: *{ans}*. ",
      dateErr: "Sorry, aa date ardham kaaledu (leda adi aipoyindi). *ivala*, *repu*, oka weekday, leda *15/10* la type cheyyandi.",
      closedDay: "Sorry andi, {date} roju memu close 🙏 Vere ye roju kudurutundi?", tooFar: "Memu {n} rojula mundu varake bookings teesukuntam. Daggara date choose chestara?",
      justCheck: "Okkasari cheppandi: {a} aa, {b} aa?", didYouMean: "Meeku kavalsindi {list}?", or: " leda ", chooseOption: "Please options lo okati choose cheyyandi (number tho reply ivvandi).",
      typeAgain: "Inkosari type chestara?", gotIt: "Ardhamaindi: {got} 👍", nameErr: "Please peru type cheyyandi (letters matrame).",
      moved: "🔁 Aipoyindi, mee booking marchanu.\n\n", grabbed: "Ayyo, {gone} ippude evaro teesukunnaru 😅 Inka free ga unnavi ivi:",
      unsub: "Meeru unsubscribe ayyaru, inka maa nunchi messages raavu. Malli ravalante eppudaina *START* ani pampandi.",
      cancelled: "Cancel aipoyindi. Parledu 🙂 Malli kavalante *book* ani pampandi, kotha slot chustanu.",
      keep: "Sare, mee booking alage undi: {date} at {slot}. Kaluddam! 👋",
      confirmed: "✅ Confirm aipoyindi: {svc}{date} at {slot}. Kaluddam! (Inka emaina kavalante *menu* ani pampandi.)",
      reschedHead: "Parledu! Mee current booking {date} at {slot}.",
      askCancel: "{date} at {slot} ki unna mee {what} cancel cheyyala? Cancel ki *YES* ani, unchadaniki inka edaina pampandi.", optYesCancel: "Yes, cancel", optKeep: "Unchandi",
      offersDone: "Aipoyindi 🎉 Members ki matrame offers, nelaku max 2 vastayi. Aapalante eppudaina *STOP* ani pampandi.",
      stopped: "Sare, aapesanu. Emi marchaledu.", nothingToCancel: "Meeku ye upcoming booking ledu, so cancel cheyyadaniki emi ledu 🙂",
      welcomeBack: "Welcome back, {name}! 😊", sameAgain: " Last time laage *{svc}* kavala? *1* ani pampandi, slot chustanu.", welcomeBiz: "*{business}* ki malli welcome 😊",
      menuMore: "Inka options kosam *menu* ani pampandi.", haggle: "Ardhamaindi andi 🙏 Andariki oke fair price undali ani maa prices fixed.",
      haggleOffer: "\n\nOka good news: {offer}", haggleBook: "\n\nSlot book cheyyamantara? *1* ani pampandi.",
      human: "Sare 🙂 Team ki cheppanu, *{business}* nunchi evaraina twaraga ikkade message chestaru (working hours: {hours}). {phone} ki call kuda cheyyochu. Naa daggariki ravalante *bot* ani type cheyyandi.",
      sorry: "Sorry andi, sariga ardham kaaledu. Nenu veetilo help cheyyagalanu:", optIn: "\n\nMembers ki matrame offers kavala (nelaku max 2)? *OFFERS* ani pampandi.",
      congrats: "💍 Congratulations! Maa *{item}* packages *{price}*, prati package lo oka trial untundi.",
      askEvents: "Ye functions, ye dates lo? (e.g. *pelli 22 Jan, haldi 20 Jan*)", askBudget: "Total package ki mee budget entha? (e.g. *50k*, leda *not decided*)",
      askName: "Super! Mee peru cheptara?", gotDates: "Ardhamaindi 👍\n📅 {events}", noDates: "Parledu, maa artist dates meeto confirm chestaru 👍",
      cantCatch: "Sorry, date ardham kaaledu 🙏 {ask} Leda *not fixed yet* ani cheppandi.", toConfirm: "(date inka fix kaaledu)",
      fullDate: "Sorry andi 🙏 {date} roju maa {role} full busy. Owner ni meeku call cheyyamani cheppanu; vere artist leda arrangement suggest cheyyagalaru.",
      thanks: "Thank you, {name} 💛 Maa {role} daggara mee details unnayi, twaraga WhatsApp chestaru ({hours}).\n\nIppude mee *bridal trial* book cheyyala? Adi package lone undi.",
      optTrial: "Bridal trial book cheyyandi", optArtist: "Artist tho matladali", trialStart: "Super! Mee *{trial}* book cheddam 💄 Aapalante eppudaina *cancel* ani type cheyyandi.", team: "team", artist: "artist",
      adv3: "Super — ee topics lo meeru exam ki ready. Full course lo 5 mock tests unnayi.",
      adv2: "Bagundi — oka gap fix cheyyali. 30-day plan exactly ee weak areas meeda work chestundi.", adv1: "Basics nunchi start cheddam. Free daily question, chapter-wise practice tho start cheyyandi.",
    },
    hg: {
      menuAsk: "Main kaise help karun? Number se reply kijiye:", catalogFoot: "Book karne ke liye *1* bhejiye.",
      closedToday: "Sorry, aaj hum band hain 🙏 Kal kaisa rahega? (ya koi aur din chuniye)", pastSlots: "Aaj ke slots khatam ho gaye 🌙 Kal kaisa rahega? (ya koi aur din chuniye)",
      fullyBooked: "Sorry, {day} pura book hai 😕 Aapke liye aur kaunsa din theek rahega?", optTomorrow: "Kal", optDayAfter: "Parso",
      quizIntro: "Chaliye shuru karte hain! 3 chhote sawaal.", sureHeard: "Zaroor! {heard} 👍", letsBook: "Theek hai, aapka {bookWord} book karte hain. Rokne ke liye kabhi bhi *cancel* likhiye.",
      missedTime: "Us din {m} free nahi hai, neeche se koi time chuniye.", missedShort: "Us din {m} free nahi hai.", slotBooked: "Sorry, us din {m} already book hai 🙏 Sabse paas free: {near}.", slotNotOffered: "Hamare yahan {m} ka slot nahi hai 🙏 Sabse paas free: {near}.", slotLate: "Sorry, {m} bahut late hai. Hamari last booking {last} hai{hours}. Sabse paas free: {near}.", slotEarly: "Sorry, {m} bahut early hai. Hamari pehli booking {first} hai{hours}. Sabse paas free: {near}.",
      replyABCD: "Please A, B, C ya D bhejiye.", correct: "✅ Sahi jawab! ", notQuite: "❌ Nahi — sahi jawab: *{ans}*. ",
      dateErr: "Sorry, yeh date samajh nahi aayi (ya nikal chuki hai). *aaj*, *kal*, koi din, ya *15/10* likhiye.",
      closedDay: "Sorry, {date} ko hum band hain 🙏 Aur kaunsa din theek rahega?", tooFar: "Hum {n} din aage tak hi booking lete hain. Koi nazdeek ki date chunenge?",
      justCheck: "Bas confirm kar loon: {a} ya {b}?", didYouMean: "Kya aapka matlab {list} hai?", or: " ya ", chooseOption: "Please koi ek option chuniye (number se reply kijiye).",
      typeAgain: "Kya aap phir se likh sakte hain?", gotIt: "Samajh gaya: {got} 👍", nameErr: "Please naam likhiye (sirf letters).",
      moved: "🔁 Ho gaya, maine booking badal di hai.\n\n", grabbed: "Arre, {gone} abhi-abhi kisi aur ne le liya 😅 Abhi yeh free hain:",
      unsub: "Aapka subscription band ho gaya, ab humse koi message nahi aayega. Wapas aane ke liye kabhi bhi *START* bhejiye.",
      cancelled: "Cancel ho gaya. Koi baat nahi 🙂 Jab chahein *book* bhejiye, main naya slot dhoondh dunga.",
      keep: "Theek hai, aapki booking waisi hi hai: {date} at {slot}. Milte hain! 👋",
      confirmed: "✅ Confirm ho gaya: {svc}{date} at {slot}. Milte hain! (Kuch aur chahiye toh *menu* bhejiye.)",
      reschedHead: "Koi baat nahi! Aapki abhi ki booking {date} at {slot} hai.",
      askCancel: "Kya aap {date} at {slot} wala apna {what} cancel karna chahte hain? Cancel ke liye *YES* bhejiye, rakhne ke liye kuch aur.", optYesCancel: "Yes, cancel", optKeep: "Rehne dijiye",
      offersDone: "Ho gaya 🎉 Aapko sirf members wale offers milenge, mahine mein max 2. Rokne ke liye kabhi bhi *STOP* bhejiye.",
      stopped: "Theek hai, rok diya. Kuch nahi badla.", nothingToCancel: "Aapki koi upcoming booking nahi hai, toh cancel karne ko kuch nahi hai 🙂",
      welcomeBack: "Welcome back, {name}! 😊", sameAgain: " Pichhli baar ki tarah *{svc}*? *1* bhejiye, main slot dhoondh dunga.", welcomeBiz: "*{business}* mein phir se swagat hai 😊",
      menuMore: "Aur options ke liye *menu* bhejiye.", haggle: "Main samajhta hoon 🙏 Hamare rates fixed hain taaki har customer ko ek jaisa sahi daam mile.",
      haggleOffer: "\n\nEk achhi khabar: {offer}", haggleBook: "\n\nKya main aapka slot book kar doon? *1* bhejiye.",
      human: "Zaroor 🙂 Maine team ko bata diya hai, *{business}* se koi jaldi hi yahin message karega (working hours: {hours}). Aap {phone} par call bhi kar sakte hain. Mere paas wapas aane ke liye *bot* likhiye.",
      sorry: "Sorry, main theek se samajh nahi paya. Main inmein help kar sakta hoon:", optIn: "\n\nSirf members wale offers chahiye (mahine mein max 2)? *OFFERS* bhejiye.",
      congrats: "💍 Badhai ho! Hamare *{item}* packages *{price}* ke hain, aur har package mein ek trial shamil hai.",
      askEvents: "Kaunse functions, aur kin dates par? (jaise *shaadi 22 Jan, haldi 20 Jan*)", askBudget: "Poore package ke liye aapka budget kitna hai? (jaise *50k*, ya *not decided*)",
      askName: "Badhiya! Aapka naam batayenge?", gotDates: "Samajh gaya 👍\n📅 {events}", noDates: "Koi baat nahi, hamari artist aapse dates pakki kar lengi 👍",
      cantCatch: "Sorry, date samajh nahi aayi 🙏 {ask} Ya bas *not fixed yet* likhiye.", toConfirm: "(date abhi fix nahi)",
      fullDate: "Sorry 🙏 {date} ko hamari {role} free nahi hain. Maine owner ko aapko call karne ko kaha hai; woh koi aur artist ya intezaam suggest kar sakte hain.",
      thanks: "Thank you, {name} 💛 Hamari {role} ke paas aapki details hain, woh jaldi hi WhatsApp karengi ({hours}).\n\nKya abhi apna *bridal trial* book karein? Yeh package mein shamil hai.",
      optTrial: "Bridal trial book karein", optArtist: "Artist se baat karni hai", trialStart: "Badhiya! Aapka *{trial}* book karte hain 💄 Rokne ke liye kabhi bhi *cancel* likhiye.", team: "team", artist: "artist",
      adv3: "Shandaar — in topics par aap exam ke liye ready hain. Full course mein 5 mock tests hain.",
      adv2: "Achha — ek kami theek karni hai. 30-day plan inhi weak areas par kaam karta hai.", adv1: "Chaliye basics se shuru karte hain. Free daily question aur chapter-wise practice se shuru kijiye.",
    },
  };

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
    // A73: the reply language for this turn (set in handle / slotTaken from state.lang)
    let LG = "en";
    const T = (k, v) => fill((STR[LG] && STR[LG][k]) || STR.en[k], v || {});
    const I = () => (LG !== "en" && cfg.i18n && cfg.i18n[LG]) || {};
    const cf = (k) => I()[k] || cfg[k];
    const lab = (x) => (x && (I().labels || {})[x]) || x;
    const askOf = (step) => (I().asks || {})[step.field] || step.ask;
    const faqA = (f) => { const i = cfg.faqs.indexOf(f); return ((I().faqs || [])[i]) || f.a; };
    const menuLabel = (m, i) => ((I().menu || [])[i]) || m.label;
    const dateL = (iso, fallback) => { if (!DAY_L[LG] || !iso) return fallback; const d = new Date(iso + "T00:00:00Z"); return `${DAY_L[LG][d.getUTCDay()]}, ${d.getUTCDate()} ${MON_L[LG][d.getUTCMonth()]}`; };
    const D = (state) => dateL(state.data.date_iso, state.data.date);
    function pickLocal(raw, list) { // a reply in the customer's script ("హెయిర్ స్పా") maps back to the canonical choice
      if (LG === "en" || !I().labels) return null;
      const loc = list.map(lab); const h = pickChoice(raw, loc); return h ? list[loc.indexOf(h)] : null;
    }

    function menuReply(prefix) {
      return { text: (prefix ? prefix + "\n\n" : "") + T("menuAsk") + "\n" + cfg.menu.map((m, i) => `*${i + 1}.* ${menuLabel(m, i)}`).join("\n"), options: cfg.menu.map(menuLabel) };
    }
    function catalogReply() {
      return { text: `*${cf("catalogTitle")}* — ${cfg.business}\n` + cfg.catalog.map((c) => `• ${lab(c.name)} — *${lab(c.price)}*`).join("\n") + "\n\n" + T("catalogFoot", { bookWord: cf("bookWord") }) };
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
          const day = state.data.date; const isoOfDay = state.data.date_iso; const today = state.data.date_iso === isoOf(istToday(nowOf(state)));
          const info = Slots ? Slots.day(cfg, state.data.date_iso) : {};
          const allPast = today && (all === "auto" || (Slots && cfg.schedule && cfg.schedule.hours)
            ? !Slots.free({ cfg, date_iso: state.data.date_iso, now: nowOf(state), busy: [], service: state.data.service, labels: all === "auto" ? null : all }).length
            : all.every((sl) => slotMinutes(sl) !== null && slotMinutes(sl) < istMinutes(nowOf(state)) + (cfg.lead_minutes || 30)));
          state.step = dateStep(); delete state.data.date; delete state.data.date_iso;
          const why = today && info.closingToday ? T("closedToday", { note: info.note || "closed today" }) : allPast ? T("pastSlots") : T("fullyBooked", { day: dateL(isoOfDay, day) });
          return { text: why, options: [T("optTomorrow"), T("optDayAfter")] };
        }
      }
      if (ch) return { text: askOf(step) + "\n" + ch.map((c, i) => `*${i + 1}.* ${lab(c)}`).join("\n"), options: ch.map(lab) };
      return { text: askOf(step) };
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
        bridal: state.bridal ? (({ asking, tries, ...rest }) => rest)(state.bridal) : undefined,
      });
    }
    // Smart fill (A69): a service named anywhere in the message ("repu haircut kavali")
    function catalogHit(raw, state) {
      const svc = cfg.steps.find((x) => x.choices === "catalog"); if (!svc) return null;
      const words = norm(raw).split(" ").filter((w) => /\p{L}{3,}/u.test(w) && !INTENT.book.test(w) && !INTENT.prices.test(w) && !parseDate(w, nowOf(state)) && !cfg.menu.some((m) => norm(m.label).split(" ").includes(w)));
      const al = aliasMatch(raw, cfg.catalog);
      let hit = al ? al.hit || null : words.length ? pickChoice(words.join(" "), choiceList(svc)) || pickLocal(words.join(" "), choiceList(svc)) : null;
      if (!hit && !al && words.length > 1) { const each = [...new Set(words.map((w) => pickChoice(w, choiceList(svc))).filter(Boolean))]; if (each.length === 1) hit = each[0]; }
      const item = hit && cfg.catalog.find((c) => c.name === hit);
      return item && !item.enquiry ? { field: svc.field, name: hit } : null;
    }
    const TIME_RE = /(^|\s)(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|a m|p m)(?=\s|$)/;
    function timeIn(raw) { const m = norm(raw).match(TIME_RE); return m ? `${m[2]}${m[3] ? ":" + m[3] : ""} ${m[4].replace(" ", "")}` : null; }
    function useTime(state) { // a time said earlier ("6pm") becomes the slot once the day is known, only if that slot is free
      const si = slotStep(); if (si < 0 || !state.pendingTime || !state.data.date_iso || state.data.slot) return null;
      const step = cfg.steps[si]; const hit = pickChoice(state.pendingTime, freeSlots(state, choiceList(step)));
      const asked = state.pendingTime; delete state.pendingTime;
      if (!hit) { state.missedTime = asked.toUpperCase(); state.missedNote = slotAdvice(state, asked) || undefined; return null; }
      state.data.slot = hit;
      if (Slots && cfg.schedule && cfg.schedule.staff) { const f = freeSlotInfo(state, step.choices === "auto" ? "auto" : choiceList(step)).find((x) => x.label === hit); if (f && f.staff.length) state.data.staff = f.staff[0]; }
      return hit;
    }
    function slotAdvice(state, asked) { // "6 PM" not free → say why, name the 2 nearest free times and the last/first booking
      const si = slotStep(); if (si < 0 || !asked) return null;
      const step = cfg.steps[si]; const all = Array.isArray(choiceList(step)) ? choiceList(step) : [];
      const free = freeSlots(state, choiceList(step));
      const t = String(asked).match(/(\d{1,2})(?::(\d{2}))?\s*(am|pm)/i); // "6 pm", "6:30pm"
      const am = t ? ((+t[1] % 12) + (/pm/i.test(t[3]) ? 12 : 0)) * 60 + +(t[2] || 0) : null;
      if (am === null || !free.length) return null;
      const fm = free.map((f) => [f, slotMinutes(f)]).filter((x) => x[1] !== null);
      if (!fm.length) return null;
      const near = fm.slice().sort((a, b) => Math.abs(a[1] - am) - Math.abs(b[1] - am)).slice(0, 2).sort((a, b) => a[1] - b[1]).map((x) => x[0]);
      const span = (all.length ? all : free).map(slotMinutes).filter((x) => x !== null);
      const v = { m: asked.toUpperCase(), near: near.join(T("or")), hours: cfg.hours ? ` (${cfg.hours})` : "",
        last: (all.length ? all : free)[span.indexOf(Math.max(...span))], first: (all.length ? all : free)[span.indexOf(Math.min(...span))] };
      if (all.some((a) => slotMinutes(a) === am)) return T("slotBooked", v);
      if (am > Math.max(...span)) return T("slotLate", v);
      if (am < Math.min(...span)) return T("slotEarly", v);
      return T("slotNotOffered", v);
    }
    function startFlow(state, meta, raw) {
      state.prev = { data: JSON.parse(JSON.stringify(state.data)), status: state.lead.status };
      state.step = 0; state.data = {}; bump(state, "warm", "book");
      if (meta && meta.known && meta.known.name) state.data.name = meta.known.name; // returning customer: don't ask the name again
      const heard = [];
      if (raw && !cfg.quiz) { // "repu haircut kavali" → service + date already understood, like a person would
        const c = catalogHit(raw, state); if (c) { state.data[c.field] = c.name; heard.push(lab(c.name)); }
        const d = parseDate(raw, nowOf(state));
        if (d && !closedReason(isoOf(d), d) && dateStep() >= 0) { state.data.date = fmtDate(d); state.data.date_iso = isoOf(d); heard.push(D(state)); }
        state.pendingTime = timeIn(raw) || undefined; const slot = useTime(state); if (slot) heard.push(slot);
      }
      const intro = cfg.quiz ? T("quizIntro") : heard.length ? T("sureHeard", { heard: heard.join(", ") }) : T("letsBook", { bookWord: cf("bookWord") });
      if (state.missedTime) { const m = state.missedTime, note = state.missedNote; delete state.missedTime; delete state.missedNote; return [{ text: `${intro}\n` + (note || T("missedTime", { m })) }, ...nextOrFinish(state, [])]; }
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

    // ---- Bridal enquiry (M8 / A12 / T15): package price from the catalog, events + dates, budget, name →
    // hot lead + owner alert; then offer a trial slot. The wedding day itself is never sold as a 1-hour slot.
    const enquiryItem = () => (cfg.catalog || []).find((c) => c.enquiry);
    const trialName = () => cfg.enquiry_trial || `${enquiryItem().name} trial`;
    const cap = (k) => k[0].toUpperCase() + k.slice(1);
    const eventsLine = (evs) => evs.map((e) => `${cap(e.type)} ${e.date_iso ? fmtDate(new Date(e.date_iso + "T00:00:00Z")) : "(date to confirm)"}`).join(" · "); // owner alerts: English
    const eventsLineL = (evs) => LG === "en" ? eventsLine(evs) : evs.map((e) => `${EVENT_L[LG][e.type] || e.type} ${e.date_iso ? dateL(e.date_iso, fmtDate(new Date(e.date_iso + "T00:00:00Z"))) : T("toConfirm")}`).join(" · ");
    const BUDGET_BANDS = () => cfg.bridal_budget_bands || [[0, "under 20k"], [20000, "20k–40k"], [40000, "40k–75k"], [75000, "75k+"]];
    const ASK = { get events() { return T("askEvents"); }, get budget() { return T("askBudget"); }, get name() { return T("askName"); } };
    function absorbBridal(state, raw) { // people / place can come in any message
      const b = state.bridal; const low = String(raw || "").toLowerCase();
      for (const e of parseEvents(raw, nowOf(state))) { const have = b.events.find((x) => x.type === e.type); if (!have) b.events.push(e); else if (e.date_iso) have.date_iso = e.date_iso; }
      const ppl = low.match(/\b(\d{1,2})\s*(people|persons|members|ladies|girls|faces|bridesmaids|mandi)\b/); if (ppl) b.people = +ppl[1];
      if (/\b(venue|function hall|kalyana mandapam|hotel|resort)\b/.test(low)) b.location = "venue";
      else if (/\b(at home|our home|my home|house|intiki|intlo)\b/.test(low)) b.location = "home";
      else if (/\b(at|in) (the )?(salon|parlour|parlor)\b/.test(low)) b.location = "salon";
    }
    function bridalFull(state, meta) {
      const evs = state.bridal.events; const w = evs.find((e) => e.type === "wedding" && e.date_iso) || evs.find((e) => e.date_iso); if (!w) return null;
      const holds = (meta.bridal_holds || []).filter((h) => h.date_iso === w.date_iso).length;
      return (cfg.bridal_full_dates || []).includes(w.date_iso) || (cfg.bridal_capacity && holds >= cfg.bridal_capacity) ? w : null;
    }
    function bridalNext(state, meta, events, head) {
      const b = state.bridal; const lead = head ? [head] : [];
      const full = bridalFull(state, meta);
      if (full) {
        b.asking = null; b.full_date = full.date_iso; state.lead.status = "callback";
        handoff(state, meta, events, `asked for bridal makeup on ${fmtDate(new Date(full.date_iso + "T00:00:00Z"))}, a date you marked full`);
        return [...lead, { text: T("fullDate", { role: cf("enquiry_role") || T("artist"), date: dateL(full.date_iso, fmtDate(new Date(full.date_iso + "T00:00:00Z"))) }) }];
      }
      if (!b.events.length && !b.note) { b.asking = "events"; return [...lead, { text: ASK.events }]; }
      if (!b.budget_band) { b.asking = "budget"; return [...lead, { text: ASK.budget }]; }
      if (!b.name) { b.asking = "name"; return [...lead, { text: ASK.name }]; }
      return bridalFinish(state, meta, events, lead);
    }
    function bridalStart(state, raw, meta, events, item) {
      state.step = -1; delete state.prev; delete state.rescheduling;
      state.bridal = { service: item.name, events: [], asking: "events", tries: 0 };
      if (meta.known && meta.known.name) state.bridal.name = meta.known.name;
      bump(state, "hot", "bridal"); state.lead.status = "callback";
      absorbBridal(state, raw);
      const intro = T("congrats", { item: lab(item.name), price: lab(item.price) }) + (state.bridal.events.length ? `\n📅 ${eventsLineL(state.bridal.events)}` : "");
      return bridalNext(state, meta, events, { text: intro });
    }
    function bridalAnswer(state, raw, t, meta, events) {
      const b = state.bridal;
      if (b.asking === "events") {
        const before = b.events.length; absorbBridal(state, raw);
        if (b.events.length > before) return bridalNext(state, meta, events, { text: T("gotDates", { events: eventsLineL(b.events) }) });
        b.tries++;
        if (b.tries >= 2 || /\b(not (fixed|decided|final)|don'?t know|dont know|tbd|later|no idea)\b|ఫిక్స్ కాలేదు|తెలియదు|అనుకోలేదు|तय नहीं|पता नहीं/.test(t)) { b.note = String(raw).trim().slice(0, 120); return bridalNext(state, meta, events, { text: T("noDates") }); }
        return [{ text: T("cantCatch", { ask: ASK.events }) }];
      }
      if (b.asking === "budget") {
        absorbBridal(state, raw);
        const inr = parseBudget(raw);
        if (inr) { b.budget_inr = inr; b.budget_band = BUDGET_BANDS().filter(([min]) => inr >= min).pop()[1]; }
        else { b.budget_band = "not decided"; if (!/\b(not|no|decide|deciding|flexible|any)\b/.test(t)) b.budget_note = String(raw).trim().slice(0, 80); }
        return bridalNext(state, meta, events, null);
      }
      if (b.asking === "name") {
        const nm = nameFrom(raw); if (nm.error) return [{ text: T("nameErr") }];
        b.name = nm.value; return bridalNext(state, meta, events, null);
      }
      b.asking = null; return [menuReply()];
    }
    function bridalFinish(state, meta, events, lead) {
      const b = state.bridal; b.asking = null; delete b.tries;
      state.data.name = b.name; state.data.service = b.service; state.lead.status = "callback"; bump(state, "hot", "bridal");
      const budget = b.budget_inr ? `budget about ${b.budget_inr.toLocaleString("en-IN")} (${b.budget_band})` : `budget ${b.budget_band}`;
      const bits = [eventsLine(b.events) || "dates to confirm", budget, b.people ? `${b.people} people` : "", b.location ? `at ${b.location}` : "", b.note ? `note: "${b.note}"` : ""].filter(Boolean);
      events.push({ type: "bridal_enquiry", enquiry: Object.assign({ contact: meta.contact || null }, b) });
      events.push({ type: "notify_owner", text: `💍 Bridal enquiry (hot lead): ${b.name} (${meta.contact || "web chat"}) · ${bits.join(" · ")}. Please call within 15 minutes; muhurtham dates fill fast.` });
      return [...lead, { text: T("thanks", { name: b.name.split(" ")[0], role: cf("enquiry_role") || T("team"), hours: cfg.hours }), options: [T("optTrial"), T("optArtist")] }];
    }
    function startTrial(state) {
      state.prev = { data: JSON.parse(JSON.stringify(state.data)), status: state.lead.status };
      state.step = 0; state.data = { service: trialName() }; if (state.bridal.name) state.data.name = state.bridal.name;
      bump(state, "hot", "trial");
      return [{ text: T("trialStart", { trial: lab(trialName()) }) }, ...nextOrFinish(state, [])];
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
      if (faq) return { text: fill(faqA(faq), vars()) };
      if (INTENT.prices.test(t)) return catalogReply();
      if (INTENT.hours.test(t)) return hoursReply();
      const one = cfg.faqs.find((q) => q.k.some((k) => k.length >= 4 && hasWord(t, k)));
      return one ? { text: fill(faqA(one), vars()) } : null;
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
        if (idx < 0) error = T("replyABCD");
        else {
          const ok = idx === q.a; state.data.correct = (state.data.correct || 0) + (ok ? 1 : 0);
          state.step++;
          const fb = { text: (ok ? T("correct") : T("notQuite", { ans: q.o[q.a] })) + q.why };
          return [fb, nextOrFinish(state, events)].flat();
        }
      } else if (step.type === "date") {
        const d = parseDate(raw, nowOf(state));
        if (!d) error = T("dateErr");
        else {
          const why = closedReason(isoOf(d), d);
          if (why) error = T("closedDay", { why, date: dateL(isoOf(d), fmtDate(d)) });
          else if ((cfg.max_days_ahead || 60) < Math.round((d - istToday(nowOf(state))) / 864e5)) error = T("tooFar", { n: cfg.max_days_ahead || 60 });
          else { value = fmtDate(d); state.data.date_iso = isoOf(d); }
        }
      } else if (step.type === "name") {
        const nm = nameFrom(raw); if (nm.forOther) state.data.booked_for_someone = true;
        if (nm.error) error = T("nameErr"); else value = nm.value;
      } else if (step.choices) {
        const list = step.field === "slot" ? freeSlots(state, choiceList(step)) : choiceList(step);
        const num = norm(raw).match(/^(\d{1,2})$/);
        if (step.field === "slot" && num && +num[1] >= 3 && +num[1] <= list.length) { // 1–2 are row numbers; // "4": option 4, or 4 o'clock? ask, like a person would
          const byHour = list.filter((c) => +c.match(/^(\d{1,2})/)[1] === +num[1]);
          const byRow = list[+num[1] - 1];
          if (byHour.length && !byHour.includes(byRow)) return [{ text: T("justCheck", { a: byHour[0], b: byRow }), options: [byHour[0], byRow] }];
        }
        const al = step.choices === "catalog" ? aliasMatch(raw, cfg.catalog.filter((c) => list.includes(c.name))) : null;
        if (al && al.ambiguous) return [{ text: T("didYouMean", { list: al.ambiguous.map(lab).join(T("or")) }), options: al.ambiguous.map(lab) }];
        value = (al && al.hit) || pickChoice(raw, list) || pickLocal(raw, list);
        if (!value) {
          const sqr = squash(raw); const words = norm(raw).split(" ").filter((w) => w.length >= 3);
          let close = list.filter((c) => sqr.length >= 4 && (squash(c).startsWith(sqr) || squash(c).includes(sqr)));
          if (close.length < 2) close = list.filter((c) => words.some((w) => squash(c).includes(w)));
          if (close.length >= 2 && close.length <= 3) return [{ text: T("didYouMean", { list: close.map(lab).join(T("or")) }), options: close.map(lab) }];
          error = (step.field === "slot" && timeIn(raw) && slotAdvice(state, timeIn(raw))) || T("chooseOption"); // "6pm" typed at the time step
        }
        else if (step.choices === "catalog") {
          const item = cfg.catalog.find((c) => c.name === value);
          if (item && item.enquiry) { // e.g. bridal: an enquiry with dates + budget, never a 1-hour slot (M8)
            if (state.prev) { state.data = state.prev.data; }
            return bridalStart(state, "", meta, events, item);
          }
        }
      } else {
        const v = String(raw).trim(); if (v.length < 2) error = T("typeAgain"); else value = v.slice(0, 80);
      }
      if (error && step.type !== "date" && !state.rescheduling) {
        const got = [];
        const d = dateStep() > state.step && !state.data.date_iso ? parseDate(raw, nowOf(state)) : null;
        if (d && !closedReason(isoOf(d), d)) { state.data.date = fmtDate(d); state.data.date_iso = isoOf(d); got.push(D(state)); }
        if (step.field !== "slot" && timeIn(raw)) { state.pendingTime = timeIn(raw); got.push(state.pendingTime.toUpperCase()); }
        if (got.length) return [{ text: T("gotIt", { got: got.join(", ") }) }, askStep(state)];
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
      useTime(state);
      while (state.step < cfg.steps.length && state.data[cfg.steps[state.step].field] && !reask.includes(cfg.steps[state.step].field) && cfg.steps[state.step].type !== "quiz") state.step++;
      if (state.step < cfg.steps.length) {
        if (state.missedTime) { const m = state.missedTime, note = state.missedNote; delete state.missedTime; delete state.missedNote; return [{ text: note || T("missedShort", { m }) }, askStep(state)]; }
        return [askStep(state)];
      }
      const v = Object.assign(vars(), state.data);
      if (cfg.quiz) {
        const s = state.data.correct || 0; v.score = s; state.data.quiz_score = `${s}/3`;
        v.advice = T(s === 3 ? "adv3" : s === 2 ? "adv2" : "adv1");
        delete state.data.correct;
      }
      delete state.prev;
      state.step = -1; state.lead.status = cfg.quiz ? "quiz_done" : "booked"; bump(state, "hot", cfg.quiz ? "quiz" : "booked");
      const optIn = !cfg.quiz && !state.lead.marketing ? T("optIn") : "";
      if (LG !== "en") { for (const k of Object.keys(v)) if (typeof v[k] === "string" && k !== "name") v[k] = lab(v[k]); v.date = D(state); } // shown in the customer's language
      if (!cfg.quiz) {
        const booking = { service: state.data.service || state.data.goal || state.data.bhk || null, date_iso: state.data.date_iso, slot: state.data.slot, name: state.data.name };
        if (Slots && cfg.schedule) { booking.minutes = Slots.durationOf(Slots.schedule(cfg), state.data.service); if (state.data.staff) booking.staff = state.data.staff; }
        events.push({ type: "booking", booking, replaces: state.rescheduling || null });
      }
      if (state.rescheduling) {
        const old = state.rescheduling; delete state.rescheduling;
        events.push({ type: "notify_owner", text: `🔁 Rescheduled: ${state.data.name} · ${state.data.service || ""} · ${old.date} ${old.slot} → ${state.data.date} ${state.data.slot}` });
        return [{ text: T("moved") + fill(cf("confirm"), v) }];
      }
      events.push({ type: "notify_owner", text: `🔔 New ${cfg.bookWord}: ${state.data.name}` + (state.data.service ? ` · ${state.data.service}` : "") + (state.data.date ? ` · ${state.data.date} ${state.data.slot || ""}` : "") + (state.data.quiz_score ? ` · score ${state.data.quiz_score}` : "") });
      return [{ text: fill(cf("confirm"), v) + optIn }];
    }

    // Called by the server when the database says the slot was taken a moment ago (race between two customers).
    function slotTaken(stateIn, busy) {
      const state = JSON.parse(JSON.stringify(stateIn)); LG = state.lang || "en";
      state.lead.status = (state.prev && state.prev.status) || "new"; state.step = slotStep();
      const gone = state.data.slot; delete state.data.slot;
      state._busy = (busy || []).concat(Array.from({ length: Math.min(cfg.capacity || 1, 1000) }, () => ({ date_iso: state.data.date_iso, slot: gone, blocked: true })));
      const replies = [{ text: T("grabbed", { gone }) }, askStep(state)];
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
      // A73: reply language. An explicit pick wins; Telugu or Hindi script switches; otherwise it stays as it was.
      const picked = Object.keys(LANG_PICK).find((k) => LANG_PICK[k].test(t));
      if (picked) { state.lang = picked; state.langPicked = true; }
      else if (SCRIPT.te.test(raw)) state.lang = "te";
      else if (SCRIPT.hi.test(raw)) state.lang = "hi";
      else {
        const tg = (t.match(ROMAN.tg) || []).length, hg = (t.match(ROMAN.hg) || []).length;
        if ((tg || hg) && tg !== hg && !state.langPicked && (!state.lang || ["en", "tg", "hg"].includes(state.lang))) state.lang = tg > hg ? "tg" : "hg";
        else if (!state.lang && meta.lang && STR[meta.lang]) state.lang = meta.lang;
      }
      LG = state.lang || "en";
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
        state.optedOut = true; state.step = -1; state.lead.status = "opted_out"; state.lead.marketing = false; if (state.bridal) state.bridal.asking = null;
        events.push({ type: "opt_out" });
        replies = [{ text: T("unsub") }];
      } else if (state.optedOut && !/^start$/.test(t)) {
        replies = [];
      } else if (paused && !/^(bot|menu|start)$/.test(t)) {
        events.push({ type: "forward_to_owner", text: `💬 ${meta.profileName || state.data.name || meta.contact}: ${raw.slice(0, 300)}` });
        replies = []; // a person is handling this chat
      } else if (state.pending === "cancel") {
        delete state.pending;
        if (/^(1|yes|y|confirm|ok|okay|haa|haan|han|avunu|sare|cancel it|yes cancel)\b|^(అవును|సరే|हाँ|हां|हा|ठीक है)/.test(t)) {
          state.lead.status = "cancelled";
          events.push({ type: "cancel_booking", booking: { date_iso: state.data.date_iso, slot: state.data.slot, service: state.data.service || null } });
          events.push({ type: "notify_owner", text: `❌ Cancelled: ${state.data.name || "customer"} · ${state.data.service || ""} · ${state.data.date} ${state.data.slot}` });
          replies = [{ text: T("cancelled") }];
        } else replies = [{ text: T("keep", { date: D(state), slot: state.data.slot }) }];
      } else if (state.bridal && state.bridal.asking && (/^(cancel|exit|quit|stop|vaddu|nahi chahiye)$/.test(t) || (INTENT.cancel.test(t) && t.split(" ").length <= 4))) {
        state.bridal.asking = null; replies = [menuReply(T("stopped"))];
      } else if (state.bridal && state.bridal.asking && !(GREET.test(t) && t.split(" ").length <= 2)) {
        replies = bridalAnswer(state, raw, t, meta, events);
      } else if (state.step < 0 && state.bridal && !state.bridal.asking && /\btrial\b|ట్రయల్|ट्रायल/.test(t) && enquiryItem()) {
        replies = startTrial(state);
      } else if (state.step < 0 && enquiryItem() && BRIDAL.test(t) && !INTENT.cancel.test(t) && !/\b(reschedule|postpone|prepone)\b/.test(t)) {
        replies = bridalStart(state, raw, meta, events, enquiryItem());
      } else if (booked && CONFIRM.test(t) && !(state.data.date_iso < isoOf(istToday(nowOf(state))))) { // a past visit is not "confirmed"
        state.data.confirmed = true;
        events.push({ type: "confirmed", booking: { date_iso: state.data.date_iso, slot: state.data.slot } });
        replies = [{ text: T("confirmed", { svc: state.data.service ? lab(state.data.service) + ", " : "", date: D(state), slot: state.data.slot }) }];
      } else if (booked && (/^2$/.test(t) || /\b(reschedule|postpone|prepone|change (the )?(date|time|day|slot)|another (day|time)|move (my|the) (booking|appointment)|(date|time|day|slot) (marchandi|marchali|marchu|change|badlo|badal do))\b/.test(t))) {
        state.prev = { data: JSON.parse(JSON.stringify(state.data)), status: state.lead.status };
        state.rescheduling = { date: state.data.date, slot: state.data.slot, date_iso: state.data.date_iso };
        state.step = dateStep();
        const head = { text: T("reschedHead", { date: D(state), slot: state.data.slot }) };
        const d = parseDate(raw, nowOf(state));
        if (d && !closedReason(isoOf(d), d)) { state.data.date = fmtDate(d); state.data.date_iso = isoOf(d); state.step = slotStep(); }
        replies = [head, askStep(state)];
      } else if (booked && INTENT.cancel.test(t)) {
        state.pending = "cancel";
        replies = [{ text: T("askCancel", { what: lab(state.data.service) || cf("bookWord"), date: D(state), slot: state.data.slot }), options: [T("optYesCancel"), T("optKeep")] }];
      } else if (/^(offers|offer yes|yes offers)$/.test(t)) {
        state.lead.marketing = true; events.push({ type: "marketing_opt_in" });
        replies = [{ text: T("offersDone") }];
      } else if (state.step >= 0 && (/^(cancel|exit|quit|stop booking|vaddu|nahi chahiye)$/.test(t) || (INTENT.cancel.test(t) && t.split(" ").length <= 4 && !parseDate(raw, nowOf(state))))) {
        abandonFlow(state); replies = [menuReply(T("stopped"))];
      } else if (state.step < 0 && INTENT.cancel.test(t) && !/\b(policy|charges?|fee|rules?|membership|plan|subscription|order)\b/.test(t)) { // "booking cancel cheyyandi" with nothing booked
        replies = [menuReply(T("nothingToCancel"))];
      } else if (picked && state.step >= 0) { // "telugu" in the middle of a booking: same question, new language
        replies = [askStep(state)];
      } else if (state.step >= 0 && !GREET.test(t) && sideQuestion(state, raw, t)) { // Rasa-style digression: answer, then re-ask
        replies = [sideQuestion(state, raw, t), askStep(state)];
      } else if (state.step >= 0 && !GREET.test(t)) {
        replies = handleStep(state, raw, events, meta);
      } else if (!t) {
        replies = [menuReply()];
      } else if (GREET.test(t) || /^(start|bot)$/.test(t) || picked) {
        if (state.step >= 0) abandonFlow(state);
        if (state.bridal) state.bridal.asking = null;
        state.optedOut = false; delete state.humanUntil;
        const known = meta.known || {};
        const first = known.name
          ? T("welcomeBack", { name: known.name.split(" ")[0] }) + (known.lastService ? T("sameAgain", { svc: lab(known.lastService) }) : "")
          : state.turns === 1 || picked ? fill(cf("greeting"), vars()) : T("welcomeBiz", { business: cfg.business });
        replies = [menuReply(first)];
      } else {
        let key = null;
        if (/^\d$/.test(t) && +t >= 1 && +t <= cfg.menu.length) key = cfg.menu[+t - 1].key;
        else { const m = cfg.menu.find((x, i) => norm(x.label) === t || norm(menuLabel(x, i)) === t); if (m) key = m.key; }
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
        if (faq && !key) { replies = [{ text: fill(faqA(faq), vars()) + "\n\n" + T("menuMore") }]; bump(state, "warm", "faq"); }
        if (key === "book") replies = startFlow(state, meta, raw);
        else if (key === "prices") { replies = [catalogReply()]; bump(state, "warm", "prices"); }
        else if (key === "hours") { replies = [hoursReply()]; bump(state, "cold", "hours"); }
        else if (key === "guard") replies = [{ text: cf("guard") }];
        else if (key === "haggle") { // fixed prices, real offers only — never invent a discount
          const offer = cfg.faqs.find((q) => q.id === "offers" || q.k.includes("offer") || q.k.includes("offers"));
          replies = [{ text: T("haggle") + (offer ? T("haggleOffer", { offer: fill(faqA(offer), vars()) }) : "") + T("haggleBook") }];
          bump(state, "warm", "haggle");
        }
        else if (key === "human") {
          if (state.lead.status !== "booked") state.lead.status = "callback"; bump(state, "warm", "human");
          handoff(state, meta, events, "wants to talk to a person");
          replies = [{ text: T("human", { business: cfg.business, hours: cfg.hours, phone: cfg.phone }) }];
        } else if (key && key.startsWith("faq:")) {
          const f = cfg.faqs.find((q) => q.id === key.slice(4));
          replies = [{ text: fill(faqA(f), vars()) + "\n\n" + T("menuMore") }]; bump(state, "warm", "faq");
        }
        if (!replies.length && !cfg.quiz && (catalogHit(raw, state) || (parseDate(raw, nowOf(state)) && dateStep() >= 0))) replies = startFlow(state, meta, raw);
        if (!replies.length) {
          events.push({ type: "unanswered", text: raw });
          replies = [menuReply(T("sorry"))];
        }
      }
      delete state._busy;
      return { replies, state, lead: leadSnapshot(state, meta), events };
    }

    return { config: cfg, handle, slotTaken };
  }

  return { NICHES, register, createBot, newState, parseDate, pickChoice, parseEvents, parseBudget, istToday, isoOf, Slots, version: "3.3.0" };
});

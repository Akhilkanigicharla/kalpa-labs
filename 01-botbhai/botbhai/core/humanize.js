/*
 * BotBhai "human touch" layer — runs on every reply the engine produces, before it is sent.
 *
 * What it does (rules first, AI only where rules can't):
 *  1. Persona + honest disclosure on first contact ("I'm Meera, Glow Studio's booking assistant").
 *  2. Time-of-day greeting in IST (Good morning / afternoon / evening).
 *  3. Varied phrasing, so regulars don't see the same robotic sentence every time.
 *  4. Empathy: frustration or urgency words → a warm acknowledgement + a real person offered.
 *  5. Language mirroring: Telugu / Hindi / Hinglish / Tenglish customers get replies in their language
 *     (Groq LLM, free tier), with a validator that refuses any translation that changes a price,
 *     date, time, number or link — then falls back to English.
 *  6. Pacing: a typing delay proportional to message length, like a person typing.
 */
"use strict";

const IST_MIN = 330;
const PERSONAS = { salon: "Meera", realestate: "Arjun", gym: "Vikram", examkits: "Lakshmi" };

// ---------- language detection (script + common romanized words)
const TE_LATN = /\b(ela|enti|undi|kavali|cheppandi|chesthara|ivvandi|repu|ivala|nenu|meeru|baagundi|ekkada|entha|chala|sare|avunu|ledu|kuda|vasthanu)\b/i;
const HI_LATN = /\b(kya|hain|chahiye|kitna|kitne|aaj|mujhe|aap|kaise|kab|kahan|nahi|haan|accha|achha|theek|karna|milega|karo|dijiye)\b/i; // not "hai"/"kal"/"bhai": Telugu speakers use them too
function detectLanguage(text) {
  const s = String(text || "");
  if (/[ఀ-౿]/.test(s)) return "te";
  if (/[ऀ-ॿ]/.test(s)) return "hi";
  const te = (s.match(new RegExp(TE_LATN.source, "gi")) || []).length, hi = (s.match(new RegExp(HI_LATN.source, "gi")) || []).length;
  if (te >= 1 && te >= hi) return "te-latn";
  if (hi >= 2) return "hi-latn";
  return "en";
}

// ---------- small deterministic randomness (same customer + turn → same pick; tests stay stable)
function pick(list, seed) { let h = 0; for (const c of String(seed)) h = (h * 31 + c.charCodeAt(0)) >>> 0; return list[h % list.length]; }

function timeGreeting(nowMs) {
  const h = new Date(nowMs + IST_MIN * 60000).getUTCHours();
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

const VARIANTS = [
  [/^Great, let's book your (.+?)\. Type \*cancel\* any time to stop\.$/, (m) => [
    `Lovely! Let's get your ${m[1]} booked 🙂 (type *cancel* anytime)`,
    `Super, let's lock in your ${m[1]}. Takes 30 seconds! (type *cancel* to stop)`,
    `Done deal, let's book your ${m[1]} ✨ (type *cancel* anytime)`]],
  [/^Sorry, I didn't quite get that\. I can help with these:/, () => [
    "Hmm, I didn't catch that one 😅 Here's what I can do:",
    "Oops, that one went over my head! I can help with:",
    "Sorry, I'm still learning that 🙈 Meanwhile, I can help with:"]],
  [/^No problem, cancelled\./, () => ["No worries, stopped it 👍", "Okay, cancelled. All good 🙂"]],
];

const FRUSTRATION = /\b(worst|angry|bad service|waiting since|still waiting|no response|no one picking|cheating|fraud|useless|bakwas|chetha|chettha|late again|disappointed|complaint|refund|pathetic|horrible|ghatiya)\b/i;
const URGENT = /\b(urgent|asap|right now|immediately|emergency|jaldi|twaraga)\b/i;

/**
 * Pure post-processing. ctx = { setup, business, persona?, firstContact, userText, contact, turn, nowMs }
 * Returns { replies, handoff } — handoff:true means "also alert the owner".
 */
function humanize(replies, ctx) {
  if (!replies || !replies.length) return { replies: [], handoff: false }; // bot is silent (opted out / human takeover): stay silent
  const persona = ctx.persona || PERSONAS[ctx.setup] || "Asha";
  const seed = `${ctx.contact || ""}:${ctx.turn || 0}`;
  let out = replies.map((r) => Object.assign({}, r));
  let handoff = false;

  for (const r of out) for (const [re, gen] of VARIANTS) {
    const head = r.text.split("\n")[0]; const m = head.match(re);
    if (m) r.text = r.text.replace(head, pick(gen(m), seed + r.text.length));
  }
  if (ctx.firstContact && out[0]) {
    out[0].text = out[0].text.replace(/^(Namaste 🙏|Hi ✨|Hello 👋|Hey 💪|Hi 📚|Hi|Hello|Hey)\s*/, `${timeGreeting(ctx.nowMs || Date.now())}! `);
    out[0].text = out[0].text.replace(/\n\nHow can I help\?/, `\n\nI'm ${persona}, ${ctx.business}'s booking assistant (an AI; type *human* any time to reach the team).\n\nHow can I help?`);
  }
  if (FRUSTRATION.test(ctx.userText || "")) {
    handoff = true;
    out = []; // no menus or "didn't get that" after a complaint: only a real apology, then a person takes over
    out.unshift({ text: pick([
      "I'm really sorry about this 🙏 I've alerted the team right now, and a person will reply to you personally.",
      "That's not the experience we want for you, I'm sorry 🙏 I've flagged it to the team; someone will reach out shortly."], seed) });
  } else if (URGENT.test(ctx.userText || "")) {
    out.unshift({ text: "On it right away ⚡" });
  }
  return { replies: out, handoff };
}

// Typing delay a person would need: ~25 characters per second, between 0.8 s and 4 s.
function typingDelayMs(text) { return Math.max(800, Math.min(4000, Math.round(String(text).length / 25 * 1000))); }

// ---------- language mirroring with a strict validator
const KEEP = /₹\s?[\d,]+(?:\.\d+)?|\d{1,2}:\d{2}\s?(?:AM|PM)|https?:\/\/\S+|\d[\d,./-]*/gi;
function protectedTokens(text) { return (String(text).match(KEEP) || []).map((x) => x.replace(/\s/g, "")).sort(); }
function translationIsSafe(src, out) {
  const a = protectedTokens(src), b = protectedTokens(out);
  return a.length === b.length && a.every((x, i) => x === b[i]);
}
const LANG_NAME = { te: "Telugu (Telugu script)", hi: "Hindi (Devanagari)", "te-latn": "Telugu written in English letters (Tenglish), casual", "hi-latn": "Hinglish (Hindi in English letters), casual" };

const MODELS = require("./models.json"); // A85: one place for model names; core/models.test.js fails on retired ones
async function chat(fetchImpl, url, key, model, messages) {
  const res = await fetchImpl(url, { method: "POST", headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, temperature: 0.3, ...(model.startsWith("auto") ? {} : { reasoning_effort: "low" }), messages }) });
  if (res.ok === false) throw new Error(`HTTP ${res.status}`);
  return (await res.json()).choices[0].message.content.trim();
}

/** Translate replies with Groq; if Groq fails and the Kalpa router (A120) is set, try it; else keep English. */
async function mirrorLanguage(replies, lang, { apiKey, fetchImpl = fetch, model = MODELS.groq_chat, router } = {}) {
  if (lang === "en" || (!apiKey && !(router && router.url && router.key))) return replies;
  const out = [];
  for (const r of replies) {
    const messages = [
      { role: "system", content: `Translate the WhatsApp message into ${LANG_NAME[lang]}. Sound like a friendly local receptionist, not a textbook. Keep every number, price (₹), time, date, URL, emoji and *bold* marker exactly as written. Keep business and service names in English. Output only the translated message.` },
      { role: "user", content: r.text }];
    let text = null;
    if (apiKey) { try { text = await chat(fetchImpl, "https://api.groq.com/openai/v1/chat/completions", apiKey, model, messages); } catch (e) { text = null; } }
    if (text === null && router && router.url && router.key) {
      try { text = await chat(fetchImpl, `${router.url.replace(/\/$/, "")}/v1/chat/completions`, router.key, "auto:reliable", messages); } catch (e) { text = null; }
    }
    out.push(text !== null && translationIsSafe(r.text, text) ? Object.assign({}, r, { text }) : r);
  }
  return out;
}

module.exports = { humanize, detectLanguage, typingDelayMs, mirrorLanguage, translationIsSafe, timeGreeting, PERSONAS };

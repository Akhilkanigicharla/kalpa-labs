/*
 * WhatsApp Cloud API webhook — one endpoint serves every BotBhai client.
 * URL after deploy: https://<your-site>.netlify.app/.netlify/functions/whatsapp
 *
 * Env vars (Netlify → Site configuration → Environment variables):
 *   WA_VERIFY_TOKEN     any word you also type into Meta's webhook settings
 *   WA_ACCESS_TOKEN     System User token from Meta Business settings (secret)
 *   WA_APP_SECRET       Meta app secret — REQUIRED in production (verifies X-Hub-Signature-256)
 *   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
 *   GROQ_API_KEY        free: voice-note transcription + Telugu/Hindi replies
 *   SITE_URL            public site URL (smile-card images)
 *   VOICE_SERVER_URL, VOICE_SERVER_KEY   optional: voice-note replies
 *
 * Per message: dedupe (Meta retries) → understand (text, button, list, voice note) → engine (with calendar
 * + memory) → atomic booking in the database (capacity lock) → human touch → reply with human pacing →
 * owner alerts → save lead without wiping other agents' data.
 */
const crypto = require("crypto");
const { BotBhai } = require("../../setups/index.js");
const L = require("./_lib.js");
const { parseDayClose } = require("../automations.js");
const { humanize, detectLanguage, typingDelayMs, mirrorLanguage } = require("../humanize.js");
const sleep = (ms) => new Promise((r) => setTimeout(r, process.env.NO_DELAY ? 0 : ms));
const IGNORE = new Set(["reaction", "system", "unsupported", "ephemeral", "request_welcome", "order"]);

function validSignature(event) {
  const secret = process.env.WA_APP_SECRET;
  if (!secret) return process.env.ALLOW_UNSIGNED === "1"; // only for the first local test; never in production
  const sig = event.headers["x-hub-signature-256"] || "";
  const raw = event.isBase64Encoded ? Buffer.from(event.body, "base64") : Buffer.from(event.body || "");
  const expected = "sha256=" + crypto.createHmac("sha256", secret).update(raw).digest("hex");
  return sig.length === expected.length && crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected));
}
async function typing(phoneNumberId, messageId) { // blue ticks + "typing…" bubble
  try { await L.graph(`${phoneNumberId}/messages`, { method: "POST", body: { messaging_product: "whatsapp", status: "read", message_id: messageId, typing_indicator: { type: "text" } } }); } catch (e) { /* cosmetic */ }
}
async function transcribe(mediaId) { // voice note → text (Groq Whisper, free tier)
  if (!process.env.GROQ_API_KEY) return null;
  try {
    const meta = await L.graph(mediaId);
    const audio = await (await fetch(meta.url, { headers: { Authorization: `Bearer ${process.env.WA_ACCESS_TOKEN}` } })).arrayBuffer();
    const form = new FormData();
    form.append("file", new Blob([audio], { type: meta.mime_type || "audio/ogg" }), "voice.ogg");
    form.append("model", "whisper-large-v3-turbo");
    const r = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", { method: "POST", headers: { Authorization: `Bearer ${process.env.GROQ_API_KEY}` }, body: form, signal: AbortSignal.timeout(8000) });
    return r.ok ? (await r.json()).text : null;
  } catch (e) { return null; }
}
function textOf(msg) {
  if (msg.type === "text") return msg.text.body;
  if (msg.type === "interactive") { const r = msg.interactive.button_reply || msg.interactive.list_reply || {}; const id = r.id || "";
    return id.startsWith("t:") ? id.slice(2) : id.startsWith("o") ? id.slice(1) : r.title || ""; }
  if (msg.type === "button") return msg.button.text || msg.button.payload || "";
  return "";
}

// M10: the owner answers the 9 PM list ("all done except 3"). Returns true when the message was that answer.
async function closeTheDay(client, state, text) {
  const dc = state.dayclose; const res = parseDayClose(text, dc.ids.length); if (!res) return false;
  const set = async (nums, status) => { for (const n of nums) await L.db(`bookings?id=eq.${L.enc(dc.ids[n - 1])}&client_id=eq.${client.id}`, { method: "PATCH", prefer: "return=minimal", body: { status } }); };
  await set(res.completed, "completed"); await set(res.no_show, "no_show");
  const left = dc.ids.length - res.completed.length - res.no_show.length;
  const msg = `✅ Day closed: ${res.completed.length} done, ${res.no_show.length} no-show` + (left ? `, ${left} not marked (no review ask for them)` : "") + ". Review requests go to the ones who came. Thank you!";
  await L.sendText(client.phone_number_id, client.owner_whatsapp, msg).catch((e) => console.error("dayclose reply", e.message));
  const next = Object.assign({}, state); delete next.dayclose;
  await L.db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates,return=minimal", body: { client_id: client.id, contact: client.owner_whatsapp, state: next, updated_at: new Date().toISOString() } });
  return true;
}

// With the shared inbox deployed (SITE_URL set), the owner replies from inbox.html instead of the WhatsApp Business app,
// which can't send from a Cloud-API number unless coexistence is set up.
function inboxHint(text) {
  if (!process.env.SITE_URL) return text;
  const link = `open the inbox to reply: ${process.env.SITE_URL}/inbox.html`;
  return /reply to them from the WhatsApp Business app/.test(text) ? text.replace("reply to them from the WhatsApp Business app", link) : `${text} ${link}`;
}

async function handleMessage(client, v, msg) {
  const phoneNumberId = client.phone_number_id; const contact = msg.from;
  const profileName = (v.contacts && v.contacts[0] && v.contacts[0].profile && v.contacts[0].profile.name) || null;
  const [[sess], [prev], busy] = await Promise.all([
    L.db(`sessions?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=state`),
    L.db(`leads?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=name,details,status,source,marketing_opt_in`),
    L.busySlots(client.id),
  ]);
  const state0 = sess ? sess.state : BotBhai.newState();
  let text = textOf(msg);
  if (msg.type === "audio") text = (await transcribe(msg.audio.id)) || "";
  if (contact === client.owner_whatsapp && state0.dayclose && (await closeTheDay(client, state0, text))) return;
  if (!text) {
    if (!state0.optedOut) await L.sendText(phoneNumberId, contact, "Sorry, I can read text and voice notes only 🙏 Reply *menu* to see options.").catch(() => {});
    return;
  }
  // "known" = a name the customer typed in an earlier booking (not just their WhatsApp profile name)
  const known = prev && prev.details && prev.details.customer_name ? { name: prev.details.customer_name, lastService: prev.details.service || prev.details.goal } : null;
  const bot = BotBhai.createBot(client.niche, client.config);
  let out = bot.handle(state0, text, { contact, profileName, source: "whatsapp", busy, known });

  // Calendar first: if someone grabbed the slot a millisecond ago, offer the rest instead of a false confirmation
  if (!(await L.applyCalendarEvents(client, contact, out.events, "whatsapp"))) {
    const back = bot.slotTaken(out.state, busy);
    out = Object.assign({}, out, { replies: back.replies, state: back.state, events: out.events.filter((e) => e.type !== "booking" && e.type !== "notify_owner") });
    out.lead = Object.assign({}, out.lead, { status: back.state.lead.status, slot: undefined });
  }

  // Human touch: persona, greeting, variety, empathy, then the customer's language
  const detected = detectLanguage(text);
  const lang = detected !== "en" ? detected : (state0.lang || "en");
  out.state.lang = lang;
  const cfg = client.config || {};
  const h = humanize(out.replies, { setup: client.niche, business: cfg.business || client.name, persona: cfg.persona, firstContact: !sess, userText: text, contact, turn: out.state.turns, nowMs: Date.now() });
  const replies = await mirrorLanguage(h.replies, lang, { apiKey: process.env.GROQ_API_KEY });
  if (h.handoff) { // complaint: a person takes over this chat for 2 hours
    out.state.humanUntil = new Date(Date.now() + ((cfg.handoff_hours || 2) * 3.6e6)).toISOString();
    out.events.push({ type: "handoff", text: `⚠️ Unhappy customer ${profileName || contact}: "${text.slice(0, 160)}" — bot paused for this chat; please reply personally.` });
  }

  if (replies.length) await typing(phoneNumberId, msg.id);
  let budget = 4000; // stay well inside Meta's webhook timeout
  for (const r of replies) { const d = Math.min(typingDelayMs(r.text), budget); budget -= d; await sleep(d); await L.sendReply(phoneNumberId, contact, r).catch((e) => console.error("send", e.message)); }
  if (out.events.some((e) => e.type === "booking")) { const card = L.cardUrl(client, `${client.niche}-booking_confirmed.png`); if (card) await L.sendImage(phoneNumberId, contact, card, "").catch(() => {}); }
  if (msg.type === "audio" && cfg.voice_replies && process.env.VOICE_SERVER_URL && process.env.VOICE_SERVER_KEY && replies.length)
    fetch(`${process.env.VOICE_SERVER_URL}/voicenote`, { method: "POST", headers: { "Content-Type": "application/json", "X-BotBhai-Key": process.env.VOICE_SERVER_KEY }, body: JSON.stringify({ phone_number_id: phoneNumberId, to: contact, text: replies.map((r) => r.text).join("\n"), lang, setup: client.niche }) }).catch(() => {});

  for (const e of out.events) {
    if (["notify_owner", "handoff", "forward_to_owner"].includes(e.type)) await L.alertOwner(client, e.type === "handoff" ? inboxHint(e.text) : e.text);
    if (e.type === "opt_out") await L.db(`members?client_id=eq.${client.id}&phone=eq.${L.enc(contact)}`, { method: "PATCH", prefer: "return=minimal", body: { opted_out: true } }).catch(() => {});
  }
  await Promise.all([
    // Inbox columns (A04): assigned_to and notes are left out on purpose, so a new message never wipes them.
    L.db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates,return=minimal", body: Object.assign(
      { client_id: client.id, contact, state: out.state, updated_at: new Date().toISOString(), last_inbound_at: new Date().toISOString() }, L.inboxStatus(out.state)) }),
    L.saveLead(client, contact, out.lead, prev),
    L.db("messages", { method: "POST", prefer: "return=minimal", body: [{ client_id: client.id, contact, direction: "in", author: "customer", body: text }, ...replies.map((r) => ({ client_id: client.id, contact, direction: "out", author: "bot", body: r.text }))] }),
  ]);
}

exports.handler = async (event) => {
  if (event.httpMethod === "GET") { // Meta verifies the webhook once
    const q = event.queryStringParameters || {};
    if (q["hub.mode"] === "subscribe" && q["hub.verify_token"] === process.env.WA_VERIFY_TOKEN) return { statusCode: 200, body: q["hub.challenge"] };
    return { statusCode: 403, body: "forbidden" };
  }
  if (event.httpMethod !== "POST") return L.json(405, { error: "method" });
  if (!validSignature(event)) return L.json(401, { error: "bad signature" });
  const body = JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, "base64").toString() : event.body || "{}");
  for (const entry of body.entry || []) for (const change of entry.changes || []) {
    const v = change.value || {}; const pnid = v.metadata && v.metadata.phone_number_id;
    for (const msg of v.messages || []) {
      try {
        if (IGNORE.has(msg.type)) continue;                       // 👍 reactions etc. never get a bot reply
        if (!(await L.firstTime(msg.id))) continue;               // Meta retry → already handled
        const [client] = await L.db(`clients?phone_number_id=eq.${L.enc(pnid)}&active=eq.true&select=*`);
        if (!client) { console.warn("no client for", pnid); continue; }
        await handleMessage(client, v, msg);
      } catch (err) { console.error(err); }
    }
  }
  return L.json(200, { ok: true }); // always 200 fast, or Meta retries
};
exports._textOf = textOf;
exports._inboxHint = inboxHint;

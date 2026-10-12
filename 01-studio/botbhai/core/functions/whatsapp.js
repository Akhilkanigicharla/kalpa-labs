/*
 * WhatsApp Cloud API webhook — one endpoint serves every client.
 * URL after deploy: https://<your-site>.netlify.app/.netlify/functions/whatsapp
 *
 * Env vars (Netlify → Site configuration → Environment variables):
 *   WA_VERIFY_TOKEN            any secret string you also type into Meta's webhook settings
 *   WA_ACCESS_TOKEN            permanent System User token from Meta Business settings
 *   WA_APP_SECRET              Meta app secret (used to verify the X-Hub-Signature-256 header)
 *   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
 *   GROQ_API_KEY (optional)    free key from console.groq.com — transcribes WhatsApp voice notes (Whisper)
 */
const crypto = require("crypto");
const { BotBhai: Botforge } = require("../../setups/index.js");
const { db, json, sendImage, cardUrl } = require("./_lib.js");
const { humanize, detectLanguage, typingDelayMs, mirrorLanguage } = require("../humanize.js");
const sleep = (ms) => new Promise((r) => setTimeout(r, process.env.NO_DELAY ? 0 : ms));
// Blue ticks + "typing…" bubble, like a person picking up the phone
async function typing(phoneNumberId, messageId) {
  try {
    await fetch(`${GRAPH}/${phoneNumberId}/messages`, { method: "POST", headers: { Authorization: `Bearer ${process.env.WA_ACCESS_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({ messaging_product: "whatsapp", status: "read", message_id: messageId, typing_indicator: { type: "text" } }) });
  } catch (e) { /* cosmetic only */ }
}
const GRAPH = "https://graph.facebook.com/v21.0";

function validSignature(event) {
  const secret = process.env.WA_APP_SECRET; if (!secret) return true; // allow during first setup only
  const sig = event.headers["x-hub-signature-256"] || "";
  const raw = event.isBase64Encoded ? Buffer.from(event.body, "base64") : Buffer.from(event.body || "");
  const expected = "sha256=" + crypto.createHmac("sha256", secret).update(raw).digest("hex");
  return sig.length === expected.length && crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected));
}

async function send(phoneNumberId, to, reply) {
  let payload;
  const opts = reply.options || [];
  if (opts.length >= 1 && opts.length <= 3) {
    payload = { type: "interactive", interactive: { type: "button", body: { text: reply.text.slice(0, 1024) },
      action: { buttons: opts.map((o, i) => ({ type: "reply", reply: { id: `o${i + 1}`, title: o.slice(0, 20) } })) } } };
  } else if (opts.length > 3 && opts.length <= 10) {
    payload = { type: "interactive", interactive: { type: "list", body: { text: reply.text.slice(0, 1024) },
      action: { button: "Choose", sections: [{ title: "Options", rows: opts.map((o, i) => ({ id: `o${i + 1}`, title: o.slice(0, 24), description: o.length > 24 ? o.slice(0, 72) : undefined })) }] } } };
  } else {
    payload = { type: "text", text: { body: reply.text.slice(0, 4096), preview_url: true } };
  }
  const res = await fetch(`${GRAPH}/${phoneNumberId}/messages`, {
    method: "POST",
    headers: { Authorization: `Bearer ${process.env.WA_ACCESS_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify(Object.assign({ messaging_product: "whatsapp", to }, payload)),
  });
  if (!res.ok) console.error("send failed", res.status, await res.text());
}

// Voice note → text with Groq's free Whisper endpoint (optional)
async function transcribe(mediaId) {
  if (!process.env.GROQ_API_KEY) return null;
  const meta = await (await fetch(`${GRAPH}/${mediaId}`, { headers: { Authorization: `Bearer ${process.env.WA_ACCESS_TOKEN}` } })).json();
  const audio = await (await fetch(meta.url, { headers: { Authorization: `Bearer ${process.env.WA_ACCESS_TOKEN}` } })).arrayBuffer();
  const form = new FormData();
  form.append("file", new Blob([audio], { type: meta.mime_type || "audio/ogg" }), "voice.ogg");
  form.append("model", "whisper-large-v3-turbo");
  const r = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", { method: "POST", headers: { Authorization: `Bearer ${process.env.GROQ_API_KEY}` }, body: form });
  return r.ok ? (await r.json()).text : null;
}

exports.handler = async (event) => {
  // 1) Meta verifies the webhook once with a GET
  if (event.httpMethod === "GET") {
    const q = event.queryStringParameters || {};
    if (q["hub.mode"] === "subscribe" && q["hub.verify_token"] === process.env.WA_VERIFY_TOKEN) return { statusCode: 200, body: q["hub.challenge"] };
    return { statusCode: 403, body: "forbidden" };
  }
  if (event.httpMethod !== "POST") return json(405, { error: "method" });
  if (!validSignature(event)) return json(401, { error: "bad signature" });

  const body = JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, "base64").toString() : event.body || "{}");
  for (const entry of body.entry || []) for (const change of entry.changes || []) {
    const v = change.value || {}; const phoneNumberId = v.metadata && v.metadata.phone_number_id;
    for (const msg of v.messages || []) {
      try {
        const [client] = await db(`clients?phone_number_id=eq.${phoneNumberId}&active=eq.true&select=*`);
        if (!client) { console.warn("no client for", phoneNumberId); continue; }
        const contact = msg.from; const profileName = (v.contacts && v.contacts[0] && v.contacts[0].profile.name) || null;

        let text = "";
        if (msg.type === "text") text = msg.text.body;
        else if (msg.type === "interactive") text = (msg.interactive.button_reply || msg.interactive.list_reply).id.replace(/^o/, ""); // "o2" → "2": the engine reads numbers in menus, choices and quizzes
        else if (msg.type === "button") text = msg.button.text;
        else if (msg.type === "audio") text = (await transcribe(msg.audio.id)) || "";
        if (!text) { await send(phoneNumberId, contact, { text: "Sorry, I can only read text and voice notes. Reply *menu* to see options." }); continue; }

        // Memory + calendar: who is this, and which slots are taken in the next 2 weeks?
        const today = new Date(Date.now() + 330 * 60000).toISOString().slice(0, 10);
        const [[sess], [prev], busy] = await Promise.all([
          db(`sessions?client_id=eq.${client.id}&contact=eq.${contact}&select=state`),
          db(`leads?client_id=eq.${client.id}&contact=eq.${contact}&select=name,details,status`),
          db(`bookings?client_id=eq.${client.id}&status=eq.confirmed&date_iso=gte.${today}&select=date_iso,slot&limit=2000`),
        ]);
        const known = prev && prev.name ? { name: prev.name, lastService: prev.details && (prev.details.service || prev.details.goal) } : null;
        const state0 = sess ? sess.state : Botforge.newState();
        const bot = Botforge.createBot(client.niche, client.config);
        const out = bot.handle(state0, text, { contact, profileName, source: "whatsapp", busy, known });

        // Human touch: persona, greeting, variety, empathy, then the customer's own language
        const lang = detectLanguage(text) !== "en" ? detectLanguage(text) : (state0.lang || "en");
        out.state.lang = lang;
        const cfg = client.config || {};
        const h = humanize(out.replies, { setup: client.niche, business: cfg.business || client.name, persona: cfg.persona, firstContact: !sess, userText: text, contact, turn: out.state.turns, nowMs: Date.now() });
        const replies = await mirrorLanguage(h.replies, lang, { apiKey: process.env.GROQ_API_KEY });
        if (h.handoff) out.events.push({ type: "handoff", text: `⚠️ Unhappy customer ${profileName || contact}: "${text.slice(0, 120)}"` });

        await typing(phoneNumberId, msg.id);
        let budget = 5000; // keep the webhook well inside Meta's timeout
        for (const r of replies) { const d = Math.min(typingDelayMs(r.text), budget); budget -= d; await sleep(d); await send(phoneNumberId, contact, r); }
        if (msg.type === "audio" && cfg.voice_replies && process.env.VOICE_SERVER_URL) // they spoke, so we answer with a voice note too
          fetch(`${process.env.VOICE_SERVER_URL}/voicenote`, { method: "POST", headers: { "Content-Type": "application/json", "X-BotBhai-Key": process.env.VOICE_SERVER_KEY || "" }, body: JSON.stringify({ phone_number_id: phoneNumberId, to: contact, text: replies.map((r) => r.text).join("\n"), lang, setup: client.niche }) }).catch(() => {});
        for (const e of out.events) if ((e.type === "notify_owner" || e.type === "handoff") && client.owner_whatsapp)
          await send(phoneNumberId, client.owner_whatsapp, { text: e.text }); // works when the owner has messaged the number in the last 24h; else use an approved template

        // Calendar writes: new booking, reschedule (old slot freed), cancel
        for (const e of out.events) {
          if (e.type === "booking") {
            const card = cardUrl(client, `${client.niche}-booking_confirmed.png`);
            if (card) await sendImage(phoneNumberId, contact, card, "").catch(() => {});
            if (e.replaces) await db(`bookings?client_id=eq.${client.id}&contact=eq.${contact}&date_iso=eq.${e.replaces.date_iso}&slot=eq.${encodeURIComponent(e.replaces.slot)}&status=eq.confirmed`, { method: "PATCH", prefer: "return=minimal", body: { status: "rescheduled" } });
            await db("bookings", { method: "POST", prefer: "return=minimal", body: Object.assign({ client_id: client.id, contact, status: "confirmed" }, e.booking) });
          }
          if (e.type === "cancel_booking") await db(`bookings?client_id=eq.${client.id}&contact=eq.${contact}&date_iso=eq.${e.booking.date_iso}&slot=eq.${encodeURIComponent(e.booking.slot)}&status=eq.confirmed`, { method: "PATCH", prefer: "return=minimal", body: { status: "cancelled" } });
        }

        const { niche, business, contact: _c, source, name, score, status, ...details } = out.lead;
        await Promise.all([
          db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates", body: { client_id: client.id, contact, state: out.state, updated_at: new Date().toISOString() } }),
          db("leads?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates", body: { client_id: client.id, contact, name, score, status, details, source, updated_at: new Date().toISOString() } }),
          db("messages", { method: "POST", prefer: "return=minimal", body: [{ client_id: client.id, contact, direction: "in", body: text }, ...replies.map((r) => ({ client_id: client.id, contact, direction: "out", body: r.text }))] }),
        ]);
      } catch (err) { console.error(err); }
    }
  }
  return json(200, { ok: true }); // always 200 fast, or Meta retries
};

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
const { db, json } = require("./_lib.js");
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

        const [sess] = await db(`sessions?client_id=eq.${client.id}&contact=eq.${contact}&select=state`);
        const bot = Botforge.createBot(client.niche, client.config);
        const out = bot.handle(sess ? sess.state : Botforge.newState(), text, { contact, profileName, source: "whatsapp" });

        for (const r of out.replies) await send(phoneNumberId, contact, r);
        for (const e of out.events) if ((e.type === "notify_owner" || e.type === "handoff") && client.owner_whatsapp)
          await send(phoneNumberId, client.owner_whatsapp, { text: e.text }); // works when the owner has messaged the number in the last 24h; else use an approved template

        const { niche, business, contact: _c, source, name, score, status, ...details } = out.lead;
        await Promise.all([
          db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates", body: { client_id: client.id, contact, state: out.state, updated_at: new Date().toISOString() } }),
          db("leads?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates", body: { client_id: client.id, contact, name, score, status, details, source, updated_at: new Date().toISOString() } }),
          db("messages", { method: "POST", prefer: "return=minimal", body: [{ client_id: client.id, contact, direction: "in", body: text }, ...out.replies.map((r) => ({ client_id: client.id, contact, direction: "out", body: r.text }))] }),
        ]);
      } catch (err) { console.error(err); }
    }
  }
  return json(200, { ok: true }); // always 200 fast, or Meta retries
};

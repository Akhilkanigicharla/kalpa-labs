// A130: BotBhai on Telegram (official Bot API, free). Akhil 30 Oct 2026: WhatsApp's test number is blocked, so the
// pilot runs on Telegram + the website chat. Same engine, calendar lock, leads, inbox and humanize layer as WhatsApp.
//
// POST /.netlify/functions/telegram?client=<client uuid>   (Telegram webhook, set once with setWebhook + secret_token)
// Env (set by Akhil in Netlify, never in code): TELEGRAM_BOT_TOKEN (from @BotFather), TELEGRAM_WEBHOOK_SECRET (any long random text).
// Owner alerts go to the owner's Telegram chat when client.config.owner_telegram_chat_id is set (the owner sends /owner <code> once).
const crypto = require("crypto");
const { BotBhai } = require("../../setups/index.js");
const L = require("./_lib.js");
const { humanize, detectLanguage, mirrorLanguage } = require("../humanize.js");

const API = () => `https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}`;

function validSecret(event) {
  const want = process.env.TELEGRAM_WEBHOOK_SECRET || "";
  const got = String((event.headers || {})["x-telegram-bot-api-secret-token"] || "");
  return want.length >= 16 && got.length === want.length && crypto.timingSafeEqual(Buffer.from(got), Buffer.from(want));
}

async function tg(method, body) {
  const r = await fetch(`${API()}/${method}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (r.ok === false) throw new Error(`telegram ${method} ${r.status}`);
  return r.json();
}

// Buttons carry the option TEXT (≤ 64 bytes, Telegram's callback limit), so a tap means exactly what the customer saw.
function keyboard(options) {
  const opts = (options || []).filter((o) => Buffer.byteLength(o) <= 62).slice(0, 10);
  if (!opts.length) return undefined;
  return { inline_keyboard: opts.map((o) => [{ text: o.slice(0, 64), callback_data: "t:" + o }]) };
}
// WhatsApp-style *bold* → Telegram HTML (safe: everything else is escaped, so stray * or _ never breaks a send).
const toHtml = (t) => String(t).slice(0, 3800).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\*([^*\n]+)\*/g, "<b>$1</b>");
const sendReply = (chatId, r) => tg("sendMessage", { chat_id: chatId, text: toHtml(r.text), parse_mode: "HTML", reply_markup: keyboard(r.options) });

async function alertOwner(client, text) {
  const ownerChat = client.config && client.config.owner_telegram_chat_id;
  if (ownerChat) return tg("sendMessage", { chat_id: ownerChat, text: String(text).slice(0, 4096) }).catch((e) => console.error("owner alert", e.message));
  return L.alertOwner(client, text); // falls back to WhatsApp when the client has it
}

// One update in, replies out. Returns the replies (tests read them).
async function handleUpdate(client, update) {
  const cb = update.callback_query;
  const msg = update.message || (cb && cb.message);
  if (!msg || !msg.chat || msg.chat.type !== "private") return []; // no groups: one customer per chat
  const chatId = msg.chat.id; const contact = "tg:" + chatId;
  const text = String(cb ? String(cb.data || "").replace(/^t:/, "") : msg.text || "").trim().slice(0, 500);
  if (cb) await tg("answerCallbackQuery", { callback_query_id: cb.id }).catch(() => {});
  const cfg = client.config || {};

  // Owner links their Telegram once: "/owner <dashboard token's first 8 characters>". Never shown to customers.
  const own = /^\/owner\s+(\S{8})$/.exec(text);
  if (own && client.dashboard_token && own[1] === client.dashboard_token.slice(0, 8)) {
    await L.db(`clients?id=eq.${client.id}`, { method: "PATCH", prefer: "return=minimal", body: { config: Object.assign({}, cfg, { owner_telegram_chat_id: chatId }) } });
    await tg("sendMessage", { chat_id: chatId, text: "Done ✅ Owner alerts for this business will now come to this chat." });
    return [];
  }
  if (!text) { await tg("sendMessage", { chat_id: chatId, text: "Sorry, I can read text messages only 🙏 Type *menu* to see options." }).catch(() => {}); return []; }
  const input = text === "/start" ? "hi" : text;

  const profileName = [msg.chat.first_name, msg.chat.last_name].filter(Boolean).join(" ") || null;
  const [[sess], [prev], busy] = await Promise.all([
    L.db(`sessions?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=state`),
    L.db(`leads?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=name,details,status,source,marketing_opt_in`),
    L.busySlots(client.id),
  ]);
  const state0 = sess ? sess.state : BotBhai.newState();
  const known = prev && prev.details && prev.details.customer_name ? { name: prev.details.customer_name, lastService: prev.details.service || prev.details.goal } : null;
  const bot = BotBhai.createBot(client.niche, cfg);
  let out = bot.handle(state0, input, { contact, profileName, source: "telegram", busy, known });
  if (!(await L.applyCalendarEvents(client, contact, out.events, "telegram"))) { // someone took the slot a moment ago
    const back = bot.slotTaken(out.state, busy);
    out = Object.assign({}, out, { replies: back.replies, state: back.state, events: out.events.filter((e) => e.type !== "booking" && e.type !== "notify_owner") });
    out.lead = Object.assign({}, out.lead, { status: back.state.lead.status, slot: undefined });
  }
  const detected = detectLanguage(input);
  const lang = detected !== "en" ? detected : (state0.lang || "en");
  out.state.lang = lang;
  const h = humanize(out.replies, { setup: client.niche, business: cfg.business || client.name, persona: cfg.persona, firstContact: !sess, userText: input, contact, turn: out.state.turns, nowMs: Date.now() });
  const replies = await mirrorLanguage(h.replies, lang, { apiKey: process.env.GROQ_API_KEY, router: { url: process.env.LLM_ROUTER_URL, key: process.env.LLM_ROUTER_KEY } });
  if (h.handoff) {
    out.state.humanUntil = new Date(Date.now() + ((cfg.handoff_hours || 2) * 3.6e6)).toISOString();
    out.events.push({ type: "handoff", text: `⚠️ Unhappy customer ${profileName || contact} on Telegram: "${input.slice(0, 160)}" — bot paused for this chat; please reply personally.` });
  }
  for (const r of replies) await sendReply(chatId, r).catch((e) => console.error("send", e.message));
  for (const e of out.events) if (["notify_owner", "handoff", "forward_to_owner"].includes(e.type)) await alertOwner(client, e.text + " (Telegram)");
  await Promise.all([
    L.db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates,return=minimal", body: Object.assign(
      { client_id: client.id, contact, state: out.state, updated_at: new Date().toISOString(), last_inbound_at: new Date().toISOString() }, L.inboxStatus(out.state)) }),
    L.saveLead(client, contact, out.lead, prev),
    L.db("messages", { method: "POST", prefer: "return=minimal", body: [{ client_id: client.id, contact, direction: "in", author: "customer", body: input }, ...replies.map((r) => ({ client_id: client.id, contact, direction: "out", author: "bot", body: r.text }))] }),
  ]);
  return replies;
}

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") return L.json(405, { error: "method" });
  if (!validSecret(event)) return L.json(401, { error: "bad secret" });
  const clientId = (event.queryStringParameters || {}).client || "";
  if (!/^[0-9a-f-]{36}$/.test(clientId)) return L.json(400, { error: "client" });
  let update; try { update = JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, "base64").toString() : event.body || "{}"); } catch (e) { return L.json(200, { ok: true }); }
  try {
    if (!(await L.firstTime("tg:" + update.update_id))) return L.json(200, { ok: true }); // Telegram retry → already handled
    const [client] = await L.db(`clients?id=eq.${clientId}&active=eq.true&select=*`);
    if (client) await handleUpdate(client, update);
  } catch (err) { console.error(err); }
  return L.json(200, { ok: true }); // always 200 fast, or Telegram retries
};
exports._keyboard = keyboard;
exports._toHtml = toHtml;

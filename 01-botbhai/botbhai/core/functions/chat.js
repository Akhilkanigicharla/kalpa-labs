// Website chat widget + browser voice agent backend: POST /.netlify/functions/chat
// body: { client: "<client uuid>", visitor: "<random id>", text: "hi", source?: "voice", turnstile?: "<token>" }
//   → { replies: [...] }, or { replies, check: { sitekey } } when a booking needs the Turnstile check first (A50).
// Same engine, same calendar (capacity lock) and same leads table as WhatsApp.
const { BotBhai } = require("../../setups/index.js");
const L = require("./_lib.js");
const { humanize } = require("../humanize.js");

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" } };
  if (event.httpMethod !== "POST") return L.json(405, { error: "method" });
  let input; try { input = JSON.parse(event.body || "{}"); } catch (e) { return L.json(400, { error: "bad json" }); }
  const { client: clientId, visitor, text, source } = input;
  const lang = ["en", "te", "hi"].includes(input.lang) ? input.lang : undefined; // A73: the page's language button
  if (!/^[0-9a-f-]{36}$/.test(clientId || "") || !/^[\w-]{6,64}$/.test(visitor || "") || typeof text !== "string" || !text.trim() || text.length > 500) return L.json(400, { error: "bad input" });

  // Anyone on the internet can call this, so cap traffic per visitor and per IP before touching the calendar.
  const ip = (event.headers && (event.headers["x-nf-client-connection-ip"] || String(event.headers["x-forwarded-for"] || "").split(",")[0].trim())) || "unknown";
  const [okVisitor, okIp] = await Promise.all([
    L.rateHit(`chat:v:${clientId}:${visitor}`, 600, 30),   // 30 messages per visitor per 10 minutes
    L.rateHit(`chat:ip:${clientId}:${ip}`, 600, 120),       // 120 per IP per 10 minutes (shared Wi-Fi friendly)
  ]);
  if (!okVisitor || !okIp) return L.json(429, { error: "slow down", replies: [{ text: "You're sending messages very fast. Please wait a few minutes, or message us on WhatsApp." }] });
  const [client] = await L.db(`clients?id=eq.${clientId}&active=eq.true&select=*`);
  if (!client) return L.json(404, { error: "unknown client" });
  const contact = "web:" + visitor; const src = source === "voice" ? "voice" : "web";
  const [[sess], [prev], busy] = await Promise.all([
    L.db(`sessions?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=state`),
    L.db(`leads?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=name,details,status,source,marketing_opt_in`),
    L.busySlots(client.id),
  ]);
  const bot = BotBhai.createBot(client.niche, client.config);
  let out = bot.handle(sess ? sess.state : BotBhai.newState(), text, { contact, source: src, busy, lang });
  // A booking is only saved after a Cloudflare Turnstile check (A50). Nothing is written otherwise, so when the page
  // resends the same message with a token, the engine replays the same booking from the same state.
  if (out.events.some((e) => e.type === "booking")) {
    const t = await L.turnstileOk(input.turnstile, ip, exports.siteverify); // tests inject a fake verifier
    if (!t.ok && t.setup === false) return L.json(200, { replies: [{ text: "Online booking is paused for a moment. Please message us on WhatsApp to book." }] });
    if (!t.ok) return L.json(200, { replies: [{ text: "One quick check so we know you're not a robot: tap the box below. Your slot is not booked yet." }], check: { sitekey: t.sitekey } });
  }
  // One open booking per website visitor: a second booking moves the first one instead of taking another slot.
  if (out.events.some((e) => e.type === "booking" && !e.replaces)) {
    const [mine] = await L.db(`bookings?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&status=eq.confirmed&date_iso=gte.${L.istTodayIso()}&select=date_iso,slot`);
    if (mine) out.events = out.events.map((e) => (e.type === "booking" && !e.replaces ? Object.assign({}, e, { replaces: mine }) : e));
  }
  if (!(await L.applyCalendarEvents(client, contact, out.events, src))) {
    const back = bot.slotTaken(out.state, busy);
    out = Object.assign({}, out, { replies: back.replies, state: back.state, events: [] });
    out.lead = Object.assign({}, out.lead, { status: back.state.lead.status });
  }
  const cfg = client.config || {};
  const h = humanize(out.replies, { setup: client.niche, business: cfg.business || client.name, persona: cfg.persona, firstContact: !sess, userText: text, contact, turn: out.state.turns, nowMs: Date.now() });
  for (const e of out.events) if (["notify_owner", "handoff", "forward_to_owner"].includes(e.type)) {
    if (await L.rateHit(`chat:alert:${client.id}:${visitor}`, 3600, 3)) await L.alertOwner(client, e.text + " (website)"); // max 3 owner alerts per visitor per hour
  }
  await Promise.all([
    L.db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates,return=minimal", body: { client_id: client.id, contact, state: out.state, updated_at: new Date().toISOString() } }),
    L.saveLead(client, contact, out.lead, prev),
  ]);
  return L.json(200, { replies: h.replies });
};

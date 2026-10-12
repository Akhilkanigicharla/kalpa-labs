// Website chat widget + browser voice agent backend: POST /.netlify/functions/chat
// body: { client: "<client uuid>", visitor: "<random id>", text: "hi", source?: "voice" }  → { replies: [...] }
// Same engine, same calendar (capacity lock) and same leads table as WhatsApp.
const { BotBhai } = require("../../setups/index.js");
const L = require("./_lib.js");
const { humanize } = require("../humanize.js");

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" } };
  if (event.httpMethod !== "POST") return L.json(405, { error: "method" });
  let input; try { input = JSON.parse(event.body || "{}"); } catch (e) { return L.json(400, { error: "bad json" }); }
  const { client: clientId, visitor, text, source } = input;
  if (!/^[0-9a-f-]{36}$/.test(clientId || "") || !/^[\w-]{6,64}$/.test(visitor || "") || typeof text !== "string" || !text.trim() || text.length > 500) return L.json(400, { error: "bad input" });

  const [client] = await L.db(`clients?id=eq.${clientId}&active=eq.true&select=*`);
  if (!client) return L.json(404, { error: "unknown client" });
  const contact = "web:" + visitor; const src = source === "voice" ? "voice" : "web";
  const [[sess], [prev], busy] = await Promise.all([
    L.db(`sessions?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=state`),
    L.db(`leads?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=name,details,status,source,marketing_opt_in`),
    L.busySlots(client.id),
  ]);
  const bot = BotBhai.createBot(client.niche, client.config);
  let out = bot.handle(sess ? sess.state : BotBhai.newState(), text, { contact, source: src, busy });
  if (!(await L.applyCalendarEvents(client, contact, out.events, src))) {
    const back = bot.slotTaken(out.state, busy);
    out = Object.assign({}, out, { replies: back.replies, state: back.state, events: [] });
    out.lead = Object.assign({}, out.lead, { status: back.state.lead.status });
  }
  const cfg = client.config || {};
  const h = humanize(out.replies, { setup: client.niche, business: cfg.business || client.name, persona: cfg.persona, firstContact: !sess, userText: text, contact, turn: out.state.turns, nowMs: Date.now() });
  for (const e of out.events) if (["notify_owner", "handoff", "forward_to_owner"].includes(e.type)) await L.alertOwner(client, e.text + " (website)");
  await Promise.all([
    L.db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates,return=minimal", body: { client_id: client.id, contact, state: out.state, updated_at: new Date().toISOString() } }),
    L.saveLead(client, contact, out.lead, prev),
  ]);
  return L.json(200, { replies: h.replies });
};

// Website chat widget + voice agent backend: POST /.netlify/functions/chat
// body: { client: "<client uuid>", visitor: "<random id>", text: "hi" }  → { replies: [...] }
// Same engine and same leads table as WhatsApp, so the owner sees web leads in the dashboard too.
const { BotBhai: Botforge } = require("../../setups/index.js");
const { db, json } = require("./_lib.js");

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" } };
  if (event.httpMethod !== "POST") return json(405, { error: "method" });
  const { client: clientId, visitor, text, source } = JSON.parse(event.body || "{}");
  if (!/^[0-9a-f-]{36}$/.test(clientId || "") || !/^[\w-]{6,64}$/.test(visitor || "") || typeof text !== "string" || text.length > 500) return json(400, { error: "bad input" });

  const [client] = await db(`clients?id=eq.${clientId}&active=eq.true&select=id,niche,config`);
  if (!client) return json(404, { error: "unknown client" });
  const contact = "web:" + visitor;
  const [sess] = await db(`sessions?client_id=eq.${client.id}&contact=eq.${encodeURIComponent(contact)}&select=state`);
  const out = Botforge.createBot(client.niche, client.config).handle(sess ? sess.state : Botforge.newState(), text, { contact, source: source === "voice" ? "voice" : "web" });

  const { niche, business, contact: _c, source: src, name, score, status, ...details } = out.lead;
  await Promise.all([
    db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates", body: { client_id: client.id, contact, state: out.state, updated_at: new Date().toISOString() } }),
    db("leads?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates", body: { client_id: client.id, contact, name, score, status, details, source: src, updated_at: new Date().toISOString() } }),
  ]);
  return json(200, { replies: out.replies });
};

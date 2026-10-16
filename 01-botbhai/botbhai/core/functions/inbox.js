// Shared inbox, phase 1 (A04 / P1-W2-02): the salon sees every chat, takes over from the bot, replies from the salon's
// own WhatsApp number, and hands the chat back to the bot. Pattern from ArnasDon/wacrm (MIT): explicit status
// (bot / human / resolved) next to the engine's humanUntil timer, assignment and private notes.
//
//   GET  /.netlify/functions/inbox                     → { client, conversations: [...] }
//   GET  /.netlify/functions/inbox?contact=9198…       → { conversation, messages: [...] } (oldest first)
//   POST /.netlify/functions/inbox  { action, contact, text?, assigned_to?, notes? }
//        action = take_over | reply | resume | resolve | assign | note
//
// Auth: header  Authorization: Bearer <dashboard_token>  (same key as the owner dashboard; never in the URL).
// Same-site only: no CORS header. WhatsApp rules enforced here, not just in the page:
//   · free-form replies only inside 24 h of the customer's last message (otherwise Meta needs a template)
//   · never message someone who replied STOP
//   · website-chat visitors have no WhatsApp number, so they can't be replied to from here
const L = require("./_lib.js");

const HOUR = 3.6e6;
const ACTIONS = new Set(["take_over", "reply", "resume", "resolve", "assign", "note"]);
const CONTACT = /^(\d{8,15}|web:[\w-]{6,64})$/;

function displayStatus(row, nowMs) {
  if (row.status === "resolved") return "resolved";
  return L.inboxStatus(row.state || {}, nowMs).status; // a "human" chat whose timer ran out is back with the bot
}
function windowOpen(row, nowMs) {
  return !!row.last_inbound_at && nowMs - new Date(row.last_inbound_at).getTime() < 24 * HOUR;
}
function view(row, names, last, nowMs) {
  const s = row.state || {}; const d = s.data || {};
  return {
    contact: row.contact, name: d.name || names[row.contact] || null, status: displayStatus(row, nowMs),
    human_until: row.status === "resolved" ? null : L.inboxStatus(s, nowMs).human_until,
    assigned_to: row.assigned_to || null, notes: row.notes || "", opted_out: !!s.optedOut,
    channel: row.contact.startsWith("web:") ? "web" : "whatsapp", window_open: windowOpen(row, nowMs),
    last_inbound_at: row.last_inbound_at || null, updated_at: row.updated_at || null,
    last: last ? { direction: last.direction, author: last.author || (last.direction === "in" ? "customer" : "bot"), body: String(last.body || "").slice(0, 140), created_at: last.created_at || null } : null,
  };
}
const rank = (c) => (c.status === "human" ? 0 : c.status === "bot" ? 1 : 2);

exports.handler = async (event) => {
  const method = event.httpMethod || "GET";
  if (method !== "GET" && method !== "POST") return L.json(405, { error: "method" }, false);
  const ip = (event.headers && (event.headers["x-nf-client-connection-ip"] || String(event.headers["x-forwarded-for"] || "").split(",")[0].trim())) || "unknown";
  if (!(await L.rateHit(`inbox:ip:${ip}`, 600, 600))) return L.json(429, { error: "slow down" }, false); // ~1 call/s; the page polls every 15 s
  const auth = (event.headers && (event.headers.authorization || event.headers.Authorization)) || "";
  const token = (auth.match(/^Bearer\s+([a-f0-9-]{36})$/i) || [])[1] || "";
  if (!token) return L.json(401, { error: "invalid token" }, false);
  const [client] = await L.db(`clients?dashboard_token=eq.${L.enc(token)}&active=eq.true&select=id,name,niche,phone_number_id,owner_whatsapp,config`);
  if (!client) return L.json(401, { error: "invalid token" }, false);
  const now = Date.now(); const cfg = client.config || {};
  const q = event.queryStringParameters || {};

  if (method === "GET" && !q.contact) {
    const [rows, leads, recent] = await Promise.all([
      L.db(`sessions?client_id=eq.${client.id}&select=contact,state,status,assigned_to,human_until,notes,last_inbound_at,updated_at&order=updated_at.desc&limit=200`),
      L.db(`leads?client_id=eq.${client.id}&select=contact,name&limit=1000`),
      L.db(`messages?client_id=eq.${client.id}&select=contact,direction,author,body,created_at&order=created_at.desc&limit=400`),
    ]);
    const names = {}; for (const l of leads || []) if (l.name) names[l.contact] = l.name;
    const last = {}; for (const m of recent || []) if (!(m.contact in last)) last[m.contact] = m; // newest first, so the first one wins
    const list = (rows || []).filter((r) => r.contact !== client.owner_whatsapp).map((r) => view(r, names, last[r.contact], now));
    list.sort((a, b) => rank(a) - rank(b) || String(b.updated_at || "").localeCompare(String(a.updated_at || "")));
    return L.json(200, { client: { name: cfg.business || client.name, niche: client.niche, hold_hours: cfg.inbox_hold_hours || 12 }, conversations: list }, false);
  }

  let input = q;
  if (method === "POST") { try { input = JSON.parse(event.body || "{}"); } catch (e) { return L.json(400, { error: "bad json" }, false); } }
  const contact = String(input.contact || "");
  if (!CONTACT.test(contact) || contact === client.owner_whatsapp) return L.json(400, { error: "bad contact" }, false);
  const [row] = await L.db(`sessions?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=contact,state,status,assigned_to,human_until,notes,last_inbound_at,updated_at`);
  if (!row) return L.json(404, { error: "no such conversation" }, false);

  if (method === "GET") {
    const msgs = await L.db(`messages?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=id,direction,author,body,created_at&order=created_at.desc&limit=150`);
    const [lead] = await L.db(`leads?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=name`);
    const messages = (msgs || []).slice() // latest 150, shown oldest first; id breaks ties inside one webhook insert
      .sort((a, b) => String(a.created_at || "").localeCompare(String(b.created_at || "")) || Number(a.id) - Number(b.id))
      .map((m) => ({ direction: m.direction, author: m.author || (m.direction === "in" ? "customer" : "bot"), body: m.body, created_at: m.created_at || null }));
    return L.json(200, { conversation: view(row, lead && lead.name ? { [contact]: lead.name } : {}, null, now), messages }, false);
  }

  const action = String(input.action || "");
  if (!ACTIONS.has(action)) return L.json(400, { error: "unknown action" }, false);
  const state = Object.assign({}, row.state || {});
  const hold = () => { // bot stays quiet for the hold time, never shorter than a pause already running
    const until = Math.max(now + (cfg.inbox_hold_hours || 12) * HOUR, state.humanUntil ? new Date(state.humanUntil).getTime() : 0);
    state.humanUntil = new Date(until).toISOString();
  };
  const patch = { updated_at: new Date(now).toISOString() };

  if (action === "reply") {
    const text = typeof input.text === "string" ? input.text.trim() : "";
    if (!text || text.length > 4096) return L.json(400, { error: "write a message (up to 4096 characters)" }, false);
    if (contact.startsWith("web:")) return L.json(400, { error: "web_visitor", message: "Website visitors have no WhatsApp number. Ask them to message you on WhatsApp." }, false);
    if (state.optedOut) return L.json(409, { error: "opted_out", message: "This customer replied STOP. WhatsApp rules: don't message them unless they write START." }, false);
    if (!windowOpen(row, now)) return L.json(409, { error: "outside_24h", message: "Their last message was over 24 hours ago, so WhatsApp only allows an approved template. Call them, or wait for them to write." }, false);
    try { await L.sendText(client.phone_number_id, contact, text); }
    catch (e) {
      if (/131047|Re-engagement/.test(e.message)) return L.json(409, { error: "outside_24h", message: "WhatsApp says the 24-hour window has closed." }, false);
      console.error("inbox send", e.message.slice(0, 120)); return L.json(502, { error: "send_failed", message: "WhatsApp didn't accept the message. Try again in a minute." }, false);
    }
    hold(); // a person is talking now: keep the bot out of the way
    await L.db("messages", { method: "POST", prefer: "return=minimal", body: { client_id: client.id, contact, direction: "out", author: "staff", body: text } });
  } else if (action === "take_over") hold();
  else if (action === "resume" || action === "resolve") delete state.humanUntil;
  else if (action === "assign") {
    const who = String(input.assigned_to || "").trim().slice(0, 40);
    patch.assigned_to = who || null;
  } else if (action === "note") patch.notes = String(input.notes || "").slice(0, 2000);

  if (["reply", "take_over", "resume", "resolve"].includes(action)) {
    Object.assign(patch, { state }, L.inboxStatus(state, now));
    if (action === "resolve") patch.status = "resolved";
  }
  await L.db(`sessions?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}`, { method: "PATCH", prefer: "return=minimal", body: patch });
  const after = Object.assign({}, row, patch);
  return L.json(200, { ok: true, conversation: view(after, {}, null, now) }, false);
};

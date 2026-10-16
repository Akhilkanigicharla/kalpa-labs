// Owner dashboard API: GET /.netlify/functions/leads  with header  Authorization: Bearer <dashboard_token>
// Returns that client's leads (newest first) and recent messages. The token is the only key, so it never goes in the
// URL (URLs end up in browser history and server logs), and the reply has no CORS header (dashboard is same-site).
const { db, json, istTodayIso } = require("./_lib.js");

exports.handler = async (event) => {
  const auth = (event.headers && (event.headers.authorization || event.headers.Authorization)) || "";
  const token = (auth.match(/^Bearer\s+([a-f0-9-]{36})$/i) || [])[1] || "";
  if (!token) return json(401, { error: "invalid token" }, false);
  const [client] = await db(`clients?dashboard_token=eq.${encodeURIComponent(token)}&select=id,name,niche`);
  if (!client) return json(401, { error: "invalid token" }, false);
  const leads = await db(`leads?client_id=eq.${client.id}&select=contact,name,score,status,details,source,created_at,updated_at&order=updated_at.desc&limit=1000`);
  const messages = await db(`messages?client_id=eq.${client.id}&select=contact,direction,body,created_at&order=created_at.desc&limit=500`);
  // A10 owner dashboard: the calendar from 30 days back to 14 days ahead (IST dates) and chats waiting for a person
  const today = istTodayIso(), day = 864e5, from = istTodayIso(Date.now() - 30 * day), to = istTodayIso(Date.now() + 14 * day);
  const [bookings, waiting] = await Promise.all([
    db(`bookings?client_id=eq.${client.id}&date_iso=gte.${from}&date_iso=lte.${to}&select=contact,name,service,date_iso,slot,status,confirmed_at&order=date_iso.asc&limit=2000`),
    db(`sessions?client_id=eq.${client.id}&status=eq.human&select=contact&limit=200`),
  ]);
  const keep = ["contact", "name", "service", "date_iso", "slot", "status", "confirmed_at"];
  return json(200, { client: { name: client.name, niche: client.niche }, today, leads, messages,
    bookings: (bookings || []).map((b) => Object.fromEntries(keep.map((k) => [k, b[k] == null ? null : b[k]]))), waiting: (waiting || []).length }, false);
};

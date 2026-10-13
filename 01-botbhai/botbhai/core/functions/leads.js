// Owner dashboard API: GET /.netlify/functions/leads?token=<dashboard_token>
// Returns that client's leads (newest first) and recent messages. The token is the only key.
const { db, json } = require("./_lib.js");

exports.handler = async (event) => {
  const token = (event.queryStringParameters || {}).token || "";
  if (!/^[a-f0-9]{36}$/.test(token)) return json(401, { error: "invalid token" });
  const [client] = await db(`clients?dashboard_token=eq.${token}&select=id,name,niche`);
  if (!client) return json(401, { error: "invalid token" });
  const leads = await db(`leads?client_id=eq.${client.id}&select=contact,name,score,status,details,source,created_at,updated_at&order=updated_at.desc&limit=1000`);
  const messages = await db(`messages?client_id=eq.${client.id}&select=contact,direction,body,created_at&order=created_at.desc&limit=500`);
  return json(200, { client: { name: client.name, niche: client.niche }, leads, messages });
};

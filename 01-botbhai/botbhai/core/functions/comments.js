/*
 * Comment → DM (A100). Webhook URL: https://<site>/.netlify/functions/comments
 * Meta app → Webhooks → Instagram field "comments" and Page field "feed". Official Meta webhooks only, no scraping.
 * A keyword comment on the owner's post → one private reply (listing + BotBhai link) → lead + chat land in the inbox.
 * DRY RUN BY DEFAULT: nothing is sent unless COMMENT_DM_LIVE=1 AND the client's config.comment_dm_live is true
 * AND a Page token (pages_messaging / instagram_manage_messages) is in Vault. Dry runs still save the lead.
 */
const L = require("./_lib.js");
const C = require("../comments.js");

const ID = /^[0-9_]{1,40}$/;

async function handleEvent(e, nowMs) {
  if (!ID.test(e.account_id) || !ID.test(e.comment_id) || !ID.test(e.from_id)) return "bad_ids";
  const col = e.platform === "instagram" ? "ig_user_id" : "meta_page_id";
  const [client] = await L.db(`clients?${col}=eq.${L.enc(e.account_id)}&active=eq.true&select=*`);
  if (!client) return "no_client";
  const cfg = client.config || {};
  const d = C.decide(e, cfg.comment_dm, nowMs);
  if (d.action !== "reply") return d.reason;
  if (!(await L.firstTime("comment:" + e.comment_id))) return "duplicate"; // Meta retries; one reply per comment
  const text = C.replyText(d.rule, e, cfg.business || client.name);
  const live = process.env.COMMENT_DM_LIVE === "1" && cfg.comment_dm_live === true;
  let sent = false;
  if (live) {
    const token = await L.clientToken(client.id, "meta_page");
    if (!token || !client.meta_page_id) console.warn("comment dm: no page token or page id for client", client.id);
    else { await L.graph(`${client.meta_page_id}/messages`, { method: "POST", token, body: C.sendBody(e.comment_id, text) }); sent = true; }
  }
  const contact = (e.platform === "instagram" ? "ig:" : "fb:") + e.from_id;
  const source = e.platform + "_comment";
  const [prev] = await L.db(`leads?client_id=eq.${client.id}&contact=eq.${L.enc(contact)}&select=id,details,status,name,source,marketing_opt_in`);
  const now = new Date(nowMs).toISOString();
  await Promise.all([
    L.saveLead(client, contact, { source, name: (prev && prev.name) || e.from_name, score: "warm", status: (prev && prev.status) || "new",
      comment: { id: e.comment_id, text: e.text.slice(0, 500), media_id: e.media_id, keyword: d.rule.keyword, at: new Date(e.created_ms).toISOString(), dm: sent ? "sent" : "dry_run" } }, prev),
    L.db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=ignore-duplicates,return=minimal", body: { client_id: client.id, contact, state: { channel: source }, updated_at: now } }),
    L.db("messages", { method: "POST", prefer: "return=minimal", body: [{ client_id: client.id, contact, direction: "in", author: "customer", body: `💬 comment: ${e.text.slice(0, 500)}` },
      { client_id: client.id, contact, direction: "out", author: "bot", body: (sent ? "" : "[dry run, not sent] ") + text }] }),
  ]);
  if (sent) await L.alertOwner(client, `💬 ${e.platform} comment from ${e.from_name || "someone"}: "${e.text.slice(0, 120)}" → DM sent (${d.rule.keyword})`);
  return sent ? "sent" : "dry_run";
}

exports.handler = async (event) => {
  if (event.httpMethod === "GET") return L.metaVerify(event); // Meta verifies the webhook once
  if (event.httpMethod !== "POST") return L.json(405, { error: "method" });
  if (!L.metaSignatureOk(event)) return L.json(401, { error: "bad signature" });
  let body;
  try { body = JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, "base64").toString() : event.body || "{}"); } catch { return L.json(400, { error: "json" }); }
  const results = [];
  for (const e of C.parseCommentEvents(body)) {
    try { results.push(await handleEvent(e, Date.now())); } catch (err) { console.error("comment dm failed", err.message); results.push("error"); }
  }
  return L.json(200, { ok: true, results });
};

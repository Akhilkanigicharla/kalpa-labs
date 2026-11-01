/*
 * Comment → DM (A100, replaces Manychat). Pure logic, no network.
 * Someone comments a keyword on the owner's Instagram/Facebook post → ONE private reply to that comment.
 * Meta rules (developers.facebook.com, Private replies for Instagram and for Pages, fetched 1 Nov 2026):
 * one message per comment, within 7 days of the comment; the chat continues only if the person writes back.
 * We never message anyone who did not comment first.
 */
const WINDOW_MS = 7 * 864e5;
const MAX_TEXT = 1000;

const toMs = (t) => (t == null ? NaN : typeof t === "number" ? (t < 1e12 ? t * 1000 : t) : Date.parse(t));

// Meta webhook body → [{ platform, account_id, comment_id, text, from_id, from_name, media_id, created_ms }]
function parseCommentEvents(body) {
  const out = [];
  if (!body || !Array.isArray(body.entry)) return out;
  for (const entry of body.entry) for (const ch of (entry && entry.changes) || []) {
    const v = (ch && ch.value) || {};
    if (body.object === "instagram" && ch.field === "comments" && v.id && v.text && v.from && v.from.id) {
      out.push({ platform: "instagram", account_id: String(entry.id), comment_id: String(v.id), text: String(v.text), from_id: String(v.from.id),
        from_name: v.from.username || "", media_id: v.media ? String(v.media.id) : "", created_ms: toMs(v.timestamp || entry.time) });
    } else if (body.object === "page" && ch.field === "feed" && v.item === "comment" && v.verb === "add" && v.comment_id && v.message && v.from && v.from.id) {
      out.push({ platform: "facebook", account_id: String(entry.id), comment_id: String(v.comment_id), text: String(v.message), from_id: String(v.from.id),
        from_name: v.from.name || "", media_id: v.post_id ? String(v.post_id) : "", created_ms: toMs(v.created_time || entry.time) });
    }
  }
  return out;
}

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// rules: [{ keyword, reply, link?, media_id? }] from client.config.comment_dm. Whole-word, case-insensitive.
function matchRule(text, rules, mediaId) {
  for (const r of rules || []) {
    if (!r || !r.keyword || !r.reply) continue;
    if (r.media_id && r.media_id !== mediaId) continue;
    if (new RegExp(`(^|[^\\p{L}\\p{N}])${esc(String(r.keyword))}($|[^\\p{L}\\p{N}])`, "iu").test(text)) return r;
  }
  return null;
}

function decide(e, rules, nowMs = Date.now()) {
  if (e.from_id === e.account_id) return { action: "skip", reason: "own_comment" }; // our own reply comments: no loops
  if (!(nowMs - e.created_ms <= WINDOW_MS)) return { action: "skip", reason: "too_old" }; // also catches a missing time
  const rule = matchRule(e.text, rules, e.media_id);
  return rule ? { action: "reply", rule } : { action: "skip", reason: "no_keyword" };
}

function replyText(rule, e, business) {
  let t = String(rule.reply).replace(/\{name\}/g, (e && e.from_name) || "there").replace(/\{business\}/g, business || "").replace(/\{[^}]*\}/g, "");
  if (rule.link && !t.includes(rule.link)) t += "\n" + rule.link;
  return t.length > MAX_TEXT ? t.slice(0, MAX_TEXT - 1) + "…" : t;
}

const sendBody = (commentId, text) => ({ recipient: { comment_id: commentId }, message: { text } });

module.exports = { parseCommentEvents, matchRule, decide, replyText, sendBody, WINDOW_MS };

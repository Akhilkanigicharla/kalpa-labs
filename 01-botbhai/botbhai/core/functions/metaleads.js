/*
 * Lead generation bot, part 1 — Meta (Facebook/Instagram) Lead Ads → WhatsApp in under 60 seconds.
 * Webhook URL: https://<site>/.netlify/functions/metaleads   (Meta app → Webhooks → Page → field "leadgen")
 * For each new lead: fetch the form answers, save the lead (source "meta_ads"), send the WhatsApp
 * welcome template with "Book now / Call me" buttons, alert the owner, and queue a voice call if enabled.
 */
const crypto = require("crypto");
const { db, json, graph, sendTemplate, templatesFor, alertOwner, firstTime, enc, clientToken } = require("./_lib.js");
const { parseMetaLead } = require("../automations.js");

function validSignature(event) {
  const secret = process.env.WA_APP_SECRET;
  if (!secret) return process.env.ALLOW_UNSIGNED === "1"; // fail closed, same as whatsapp.js: only for a first local test
  const sig = event.headers["x-hub-signature-256"] || "";
  const raw = event.isBase64Encoded ? Buffer.from(event.body, "base64") : Buffer.from(event.body || "");
  const expected = "sha256=" + crypto.createHmac("sha256", secret).update(raw).digest("hex");
  return sig.length === expected.length && crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected));
}

exports.handler = async (event) => {
  if (event.httpMethod === "GET") {
    const q = event.queryStringParameters || {};
    return q["hub.mode"] === "subscribe" && q["hub.verify_token"] === process.env.WA_VERIFY_TOKEN ? { statusCode: 200, body: q["hub.challenge"] } : { statusCode: 403, body: "forbidden" };
  }
  if (event.httpMethod !== "POST") return json(405, { error: "method" });
  if (!validSignature(event)) return json(401, { error: "bad signature" });
  const body = JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, "base64").toString() : event.body || "{}");
  for (const entry of body.entry || []) for (const ch of entry.changes || []) {
    if (ch.field !== "leadgen") continue;
    try {
      const v = ch.value;
      if (!/^\d{1,20}$/.test(String(v.page_id || "")) || !/^\d{1,25}$/.test(String(v.leadgen_id || ""))) { console.warn("bad lead ids"); continue; }
      const [client] = await db(`clients?meta_page_id=eq.${enc(v.page_id)}&active=eq.true&select=*`);
      if (!client) { console.warn("no client for page", v.page_id); continue; }
      const pageToken = await clientToken(client.id, "meta_page");
      if (!pageToken) { console.warn("no page token in Vault for client", client.id); continue; } // never fall back to the WhatsApp token
      const raw = await graph(`${v.leadgen_id}?fields=field_data,created_time,ad_id,form_id`, { token: pageToken });
      const lead = parseMetaLead(raw);
      const contact = lead.phone || `meta:${v.leadgen_id}`;
      if (!(await firstTime("lead:" + v.leadgen_id))) continue; // Meta retried this lead
      const answers = Object.assign({ email: lead.email, ad_id: lead.ad_id, form_id: lead.form_id, consent: "meta_lead_form", consent_at: lead.created_time }, lead.answers);
      const [existing] = await db(`leads?client_id=eq.${client.id}&contact=eq.${enc(contact)}&select=id,details,status,name`);
      if (existing) { // a known customer filled a form again: add the answers, keep their booking and history
        await db(`leads?id=eq.${existing.id}`, { method: "PATCH", prefer: "return=minimal", body: { details: Object.assign({}, existing.details, { meta_form: answers }), name: existing.name || lead.name, updated_at: new Date().toISOString() } });
      } else {
        await db("leads", { method: "POST", prefer: "return=minimal", body: { client_id: client.id, contact, name: lead.name, score: "warm", status: "new", source: "meta_ads", details: answers, updated_at: new Date().toISOString() } });
      }
      const tpl = templatesFor(client.niche);
      const cfg = client.config || {};
      if (lead.phone && client.phone_number_id) await sendTemplate(client.phone_number_id, lead.phone, tpl.lead_welcome, { name: lead.name || "there", business: cfg.business || client.name });
      await alertOwner(client, `🆕 Meta lead: ${lead.name || "?"} (${lead.phone || "no phone"}) ` + Object.entries(lead.answers).map(([k, a]) => `${k.replace(/_/g, " ")}: ${a}`).join("; "));
      if (cfg.voice_followup && lead.phone) await db("jobs", { method: "POST", prefer: "return=minimal", body: { client_id: client.id, type: "voice_call", payload: { to: lead.phone, name: lead.name, reason: "new_meta_lead" }, run_at: new Date(Date.now() + 120000).toISOString() } });
    } catch (e) { console.error("lead failed", e.message); }
  }
  return json(200, { ok: true });
};

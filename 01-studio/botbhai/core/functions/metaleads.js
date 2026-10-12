/*
 * Lead generation bot, part 1 — Meta (Facebook/Instagram) Lead Ads → WhatsApp in under 60 seconds.
 * Webhook URL: https://<site>/.netlify/functions/metaleads   (Meta app → Webhooks → Page → field "leadgen")
 * For each new lead: fetch the form answers, save the lead (source "meta_ads"), send the WhatsApp
 * welcome template with "Book now / Call me" buttons, alert the owner, and queue a voice call if enabled.
 */
const crypto = require("crypto");
const { db, json, graph, sendTemplate, sendText, templatesFor } = require("./_lib.js");
const { parseMetaLead } = require("../automations.js");

function validSignature(event) {
  const secret = process.env.WA_APP_SECRET; if (!secret) return true;
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
  if (!validSignature(event)) return json(401, { error: "bad signature" });
  const body = JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, "base64").toString() : event.body || "{}");
  for (const entry of body.entry || []) for (const ch of entry.changes || []) {
    if (ch.field !== "leadgen") continue;
    try {
      const v = ch.value;
      const [client] = await db(`clients?meta_page_id=eq.${v.page_id}&active=eq.true&select=*`);
      if (!client) { console.warn("no client for page", v.page_id); continue; }
      const [secret] = await db(`client_secrets?client_id=eq.${client.id}&select=meta_page_token`);
      const raw = await graph(`${v.leadgen_id}?fields=field_data,created_time,ad_id,form_id`, { token: secret && secret.meta_page_token });
      const lead = parseMetaLead(raw);
      const contact = lead.phone || `meta:${v.leadgen_id}`;
      await db("leads?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates", body: {
        client_id: client.id, contact, name: lead.name, score: "warm", status: "new", source: "meta_ads",
        details: Object.assign({ email: lead.email, ad_id: lead.ad_id, form_id: lead.form_id, consent: "meta_lead_form", consent_at: lead.created_time }, lead.answers), updated_at: new Date().toISOString() } });
      const tpl = templatesFor(client.niche);
      const cfg = client.config || {};
      if (lead.phone && client.phone_number_id) await sendTemplate(client.phone_number_id, lead.phone, tpl.lead_welcome, { name: lead.name || "there", business: cfg.business || client.name });
      if (client.owner_whatsapp) await sendText(client.phone_number_id, client.owner_whatsapp, `🆕 Meta lead: ${lead.name || "?"} (${lead.phone || "no phone"})\n` + Object.entries(lead.answers).map(([k, a]) => `• ${k.replace(/_/g, " ")}: ${a}`).join("\n")).catch(() => {});
      if (cfg.voice_followup && lead.phone) await db("jobs", { method: "POST", prefer: "return=minimal", body: { client_id: client.id, type: "voice_call", payload: { to: lead.phone, name: lead.name, reason: "new_meta_lead" }, run_at: new Date(Date.now() + 120000).toISOString() } });
    } catch (e) { console.error("lead failed", e.message); }
  }
  return json(200, { ok: true });
};

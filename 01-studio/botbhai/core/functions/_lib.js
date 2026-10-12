// Shared helpers for the Netlify Functions. No npm packages needed (Node 18+ has fetch).
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY; // server-only secret, never put in a web page

async function db(path, opts = {}) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    method: opts.method || "GET",
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${SUPABASE_KEY}`,
      "Content-Type": "application/json",
      Prefer: opts.prefer || "return=representation",
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) throw new Error(`Supabase ${res.status}: ${await res.text()}`);
  const txt = await res.text();
  return txt ? JSON.parse(txt) : null;
}

const json = (status, body) => ({ statusCode: status, headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }, body: JSON.stringify(body) });

module.exports = { db, json };

// ---------- WhatsApp senders (shared by every BotBhai function)
const GRAPH = "https://graph.facebook.com/v21.0";
async function graph(path, { method = "GET", token, body } = {}) {
  const res = await fetch(`${GRAPH}/${path}`, { method, headers: { Authorization: `Bearer ${token || process.env.WA_ACCESS_TOKEN}`, "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Graph ${res.status}: ${JSON.stringify(data.error || data)}`);
  return data;
}
// Approved template message (needed outside the 24-hour window: lead follow-ups, reminders, renewals, owner reports)
function sendTemplate(phoneNumberId, to, tpl, values) {
  const params = (tpl.params || []).map((k) => ({ type: "text", text: String(values[k] == null || values[k] === "" ? "-" : values[k]).slice(0, 60) }));
  const components = params.length ? [{ type: "body", parameters: params }] : [];
  if (tpl.card && values.card_url) components.unshift({ type: "header", parameters: [{ type: "image", image: { link: values.card_url } }] });
  return graph(`${phoneNumberId}/messages`, { method: "POST", body: { messaging_product: "whatsapp", to, type: "template",
    template: { name: tpl.name, language: { code: tpl.language || "en" }, components } } });
}
// Public URL of a smile card for this client (cards are generated at onboarding into web/dist/cards/<card_dir>/)
function cardUrl(client, file) {
  if (!process.env.SITE_URL || !file) return "";
  return `${process.env.SITE_URL}/cards/${(client.config && client.config.card_dir) || "demo"}/${file}`;
}
function sendImage(phoneNumberId, to, link, caption) {
  return graph(`${phoneNumberId}/messages`, { method: "POST", body: { messaging_product: "whatsapp", to, type: "image", image: { link, caption: (caption || "").slice(0, 1024) } } });
}
function sendText(phoneNumberId, to, text) {
  return graph(`${phoneNumberId}/messages`, { method: "POST", body: { messaging_product: "whatsapp", to, type: "text", text: { body: text.slice(0, 4096) } } });
}
function templatesFor(setupId) {
  const dir = { salon: "salon", realestate: "realestate", gym: "gym", examkits: "examkits" }[setupId];
  return require(`../../setups/${dir}/templates.json`);
}
module.exports = Object.assign(module.exports, { graph, sendTemplate, sendText, sendImage, cardUrl, templatesFor, GRAPH });

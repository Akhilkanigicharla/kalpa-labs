// Shared helpers for the Netlify Functions. No npm packages needed (Node 18+ has fetch).
const SUPABASE_URL = () => process.env.SUPABASE_URL;
const SUPABASE_KEY = () => process.env.SUPABASE_SERVICE_ROLE_KEY; // server-only secret, never put in a web page
const enc = encodeURIComponent;

async function db(path, opts = {}) {
  const res = await fetch(`${SUPABASE_URL()}/rest/v1/${path}`, {
    method: opts.method || "GET",
    headers: { apikey: SUPABASE_KEY(), Authorization: `Bearer ${SUPABASE_KEY()}`, "Content-Type": "application/json", Prefer: opts.prefer || "return=representation" },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) { // the body can echo customer text, so only the status and error code go to the logs
    let code = ""; try { code = (JSON.parse(await res.text()) || {}).code || ""; } catch (e) { /* not json */ }
    throw new Error(`Supabase ${res.status}${code ? " " + code : ""} on ${path.split("?")[0]}`);
  }
  const txt = await res.text();
  return txt ? JSON.parse(txt) : null;
}
// Public endpoints (website chat) allow any origin; private ones (owner dashboard) pass cors=false: same-site only.
const json = (status, body, cors = true) => ({ statusCode: status, headers: Object.assign({ "Content-Type": "application/json" }, cors ? { "Access-Control-Allow-Origin": "*" } : {}), body: JSON.stringify(body) });
// Sliding-window limit kept in the database (works across function instances). true = allowed.
async function rateHit(key, windowS, max) {
  return (await db("rpc/rate_hit", { method: "POST", body: { p_key: key, p_window_s: windowS, p_max: max } })) !== false;
}
// ---------- Cloudflare Turnstile (free bot check) before a website booking is saved (A50).
// Fails closed: no secret, no token, a used/forged token, a token for another action or Cloudflare unreachable → not ok.
async function turnstileOk(token, ip) {
  const secret = process.env.TURNSTILE_SECRET_KEY;
  if (!secret) { console.error("TURNSTILE_SECRET_KEY missing: website bookings are paused"); return { ok: false, setup: false }; }
  const sitekey = process.env.TURNSTILE_SITE_KEY || "";
  if (typeof token !== "string" || !token || token.length > 2048) return { ok: false, sitekey };
  try {
    const body = new URLSearchParams({ secret, response: token });
    if (ip && ip !== "unknown") body.set("remoteip", ip);
    const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: body.toString() });
    const data = await res.json();
    return { ok: !!(data && data.success === true && data.action === "booking"), sitekey };
  } catch (e) { console.error("turnstile verify failed", e.message); return { ok: false, sitekey }; }
}
const istTodayIso = (ms = Date.now()) => new Date(ms + 330 * 60000).toISOString().slice(0, 10);

// ---------- idempotency: Meta retries webhooks; each message id is handled once
async function firstTime(key) {
  const rows = await db("processed?on_conflict=wamid", { method: "POST", prefer: "resolution=ignore-duplicates,return=representation", body: { wamid: key } });
  return Array.isArray(rows) && rows.length === 1;
}

// ---------- calendar (shared by WhatsApp, website chat and the voice agent)
async function busySlots(clientId) {
  return db(`bookings?client_id=eq.${clientId}&status=eq.confirmed&date_iso=gte.${istTodayIso()}&select=date_iso,slot&limit=5000`);
}
// Atomic: the database checks capacity under a lock, so two customers can never take the last chair.
async function bookSlot(client, contact, b, replaces, source) {
  return db("rpc/book_slot", { method: "POST", body: {
    p_client: client.id, p_contact: contact, p_name: b.name || null, p_service: b.service || null, p_date: b.date_iso, p_slot: b.slot,
    p_capacity: (client.config && client.config.capacity) || 1, p_source: source || "whatsapp",
    p_replaces_date: replaces ? replaces.date_iso : null, p_replaces_slot: replaces ? replaces.slot : null } });
}
async function setBookingStatus(clientId, contact, b, status) {
  return db(`bookings?client_id=eq.${clientId}&contact=eq.${enc(contact)}&date_iso=eq.${b.date_iso}&slot=eq.${enc(b.slot)}&status=eq.confirmed`, { method: "PATCH", prefer: "return=minimal", body: status === "confirmed_by_customer" ? { confirmed_at: new Date().toISOString() } : { status } });
}
// Runs the calendar side of engine events. Returns false if a booking lost the race for the slot.
async function applyCalendarEvents(client, contact, events, source) {
  let ok = true;
  for (const e of events) {
    if (e.type === "booking") ok = (await bookSlot(client, contact, e.booking, e.replaces, source)) !== false && ok;
    if (e.type === "cancel_booking") await setBookingStatus(client.id, contact, e.booking, "cancelled");
    if (e.type === "confirmed") await setBookingStatus(client.id, contact, e.booking, "confirmed_by_customer");
  }
  return ok;
}

// Save lead without wiping what other agents wrote (reminder flags, consent, ad answers).
async function saveLead(client, contact, lead, prev) {
  const { niche, business, contact: _c, source, name, score, status, marketing_opt_in, ...details } = lead;
  const keep = (prev && prev.details) || {};
  const merged = Object.assign({}, keep, details, { reminders: keep.reminders || details.reminders || {} });
  return db("leads?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates,return=minimal", body: {
    client_id: client.id, contact, name, score, status, details: merged, source: (prev && prev.source) || source,
    marketing_opt_in: !!marketing_opt_in || !!(prev && prev.marketing_opt_in && status !== "opted_out"), updated_at: new Date().toISOString() } });
}

// ---------- shared inbox (A04): the sessions.status/human_until columns mirror the engine's humanUntil timer
function inboxStatus(state, nowMs = Date.now()) {
  const until = state && state.humanUntil ? new Date(state.humanUntil) : null;
  return until && until.getTime() > nowMs ? { status: "human", human_until: until.toISOString() } : { status: "bot", human_until: null };
}

// ---------- WhatsApp senders
const GRAPH = "https://graph.facebook.com/v21.0";
async function graph(path, { method = "GET", token, body } = {}) {
  const res = await fetch(`${GRAPH}/${path}`, { method, headers: { Authorization: `Bearer ${token || process.env.WA_ACCESS_TOKEN}`, "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Graph ${res.status}: ${JSON.stringify(data.error || data)}`);
  return data;
}
// WhatsApp template rules: no newlines/tabs and no more than 4 spaces in a row inside a parameter. URLs are never cut.
function tplParam(v) {
  const s = String(v == null || v === "" ? "-" : v);
  if (/^https?:\/\//.test(s)) return s;
  const t = s.replace(/[\n\t]+/g, " ").replace(/ {4,}/g, "   ");
  if (t.length <= 200) return t;
  const m = t.match(/\s(https?:\/\/\S+)$/); // an alert that ends in a link (inbox, invoice): shorten the words, never the link
  if (m && m[1].length < 150) return t.slice(0, 200 - m[1].length - 2).trimEnd() + "… " + m[1];
  return t.slice(0, 200);
}
function sendTemplate(phoneNumberId, to, tpl, values) {
  const params = (tpl.params || []).map((k) => ({ type: "text", text: tplParam(values[k]) }));
  const components = params.length ? [{ type: "body", parameters: params }] : [];
  if (tpl.card && values.card_url) components.unshift({ type: "header", parameters: [{ type: "image", image: { link: values.card_url } }] });
  return graph(`${phoneNumberId}/messages`, { method: "POST", body: { messaging_product: "whatsapp", to, type: "template",
    template: { name: tpl.name, language: { code: tpl.language || "en" }, components } } });
}
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
// Interactive message. Option ids carry the option TEXT, so a tap always means exactly what the customer saw.
function sendReply(phoneNumberId, to, reply) {
  const opts = reply.options || [];
  let payload;
  if (opts.length >= 1 && opts.length <= 3 && opts.every((o) => o.length <= 20)) {
    payload = { type: "interactive", interactive: { type: "button", body: { text: reply.text.slice(0, 1024) },
      action: { buttons: opts.map((o) => ({ type: "reply", reply: { id: "t:" + o.slice(0, 250), title: o } })) } } };
  } else if (opts.length >= 1 && opts.length <= 10) {
    payload = { type: "interactive", interactive: { type: "list", body: { text: reply.text.slice(0, 1024) },
      action: { button: "Choose", sections: [{ title: "Options", rows: opts.map((o) => ({ id: "t:" + o.slice(0, 198), title: o.slice(0, 24), description: o.length > 24 ? o.slice(0, 72) : undefined })) }] } } };
  } else payload = { type: "text", text: { body: reply.text.slice(0, 4096), preview_url: true } };
  return graph(`${phoneNumberId}/messages`, { method: "POST", body: Object.assign({ messaging_product: "whatsapp", to }, payload) });
}
// Owner alerts: plain text works only inside 24 h of the owner's last message; otherwise the approved utility template.
async function alertOwner(client, text) {
  if (!client.owner_whatsapp || !client.phone_number_id) return;
  try { await sendText(client.phone_number_id, client.owner_whatsapp, text); }
  catch (e) {
    const tpl = templatesFor(client.niche).owner_alert;
    if (tpl) await sendTemplate(client.phone_number_id, client.owner_whatsapp, tpl, { business: (client.config && client.config.business) || client.name, summary: text }).catch((err) => console.error("owner alert failed", err.message));
  }
}
function templatesFor(setupId) {
  const dir = { salon: "salon", realestate: "realestate", gym: "gym", examkits: "examkits" }[setupId];
  return require(`../../setups/${dir}/templates.json`);
}
module.exports = { db, json, enc, rateHit, turnstileOk, istTodayIso, firstTime, inboxStatus, busySlots, bookSlot, setBookingStatus, applyCalendarEvents, saveLead,
  graph, sendTemplate, sendText, sendImage, sendReply, cardUrl, alertOwner, templatesFor, tplParam, GRAPH };

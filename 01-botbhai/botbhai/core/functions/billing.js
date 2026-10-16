// Billing (A05 / P1-W2-06): Kalpa Labs bills each salon. Manual on purpose: Akhil creates, sends and marks paid.
//
//   GET  /.netlify/functions/billing?v=<view key>       the salon's invoice page (no login; the key is 128 random bits)
//   Admin (header  Authorization: Bearer <BILLING_ADMIN_KEY>):
//   GET  /.netlify/functions/billing                     → { seller, clients, invoices }
//   POST { action: "create", client_id, items: [{ desc, amount (₹), qty? }], period?, due_days? (default 7) }
//   POST { action: "send" | "remind" | "void", number }   send/remind = WhatsApp to the salon owner with the link
//   POST { action: "paid", number, ref? (UPI ref / UTR), paid_on? }
//
// Env (Akhil sets these himself in Netlify; nothing secret is ever typed into a chat):
//   BILLING_ADMIN_KEY   32+ random characters; admin is switched off without it
//   BILLING_UPI_ID      Kalpa Labs' business UPI ID (shown on invoices; not a secret)
//   BILLING_NAME, BILLING_ADDRESS, BILLING_PHONE, BILLING_EMAIL, BILLING_UDYAM   optional seller details
// Rules + sources: 01-botbhai/research/billing-scan.md
const crypto = require("crypto");
const L = require("./_lib.js");
const B = require("../billing.js");

const ACTIONS = new Set(["create", "send", "remind", "paid", "void"]);
const NUMBER = /^KL\/\d{2}-\d{2}\/\d{3,6}$/;
const UTR = /^[A-Za-z0-9]{6,35}$/;

function seller() {
  const e = process.env;
  return { name: e.BILLING_NAME || "Kalpa Labs", address: e.BILLING_ADDRESS || "Hyderabad, Telangana", phone: e.BILLING_PHONE || "",
    email: e.BILLING_EMAIL || "", udyam: e.BILLING_UDYAM || "UDYAM-TS-02-0382711", vpa: B.VPA.test(e.BILLING_UPI_ID || "") ? e.BILLING_UPI_ID : "" };
}
function isAdmin(event) {
  const want = process.env.BILLING_ADMIN_KEY || "";
  if (want.length < 32) return null; // switched off: refuse rather than accept a guessable key
  const auth = (event.headers && (event.headers.authorization || event.headers.Authorization)) || "";
  const got = (auth.match(/^Bearer\s+(\S{32,200})$/) || [])[1] || "";
  const h = (s) => crypto.createHash("sha256").update(s).digest();
  return !!got && crypto.timingSafeEqual(h(got), h(want));
}
const ipOf = (event) => (event.headers && (event.headers["x-nf-client-connection-ip"] || String(event.headers["x-forwarded-for"] || "").split(",")[0].trim())) || "unknown";
const istToday = (plusDays = 0) => new Date(Date.now() + 330 * 60000 + plusDays * 864e5).toISOString().slice(0, 10);
const linkFor = (inv) => `${process.env.SITE_URL || ""}/.netlify/functions/billing?v=${inv.view_key}`;
const view = (inv, now = new Date()) => Object.assign({}, inv, { link: linkFor(inv), overdue_days: B.overdueDays(inv, now) });

function html(status, body) {
  return { statusCode: status, headers: {
    "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow", "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src data:; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  }, body };
}
const notFound = () => html(404, '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Invoice not found</title><body style="font:16px system-ui;padding:24px;color:#191C33;background:#EEEDF3">This invoice link is not valid. Please ask Kalpa Labs for a new one.</body>');

// Plain text inside 24 h of the owner's last message; otherwise the approved utility template. Template parameters are
// cut at 200 characters (_lib.tplParam), so the template gets a short summary with the link last and never cut.
async function message(client, text, short) {
  try { await L.sendText(client.phone_number_id, client.owner_whatsapp, text); return true; }
  catch (e) {
    const tpl = L.templatesFor(client.niche).owner_alert; if (!tpl) return false;
    const link = short.link; const head = short.head.slice(0, Math.max(0, 196 - link.length));
    try { await L.sendTemplate(client.phone_number_id, client.owner_whatsapp, tpl, { business: (client.config && client.config.business) || client.name, summary: `${head} ${link}` }); return true; }
    catch (err) { console.error("billing send failed", err.message.slice(0, 120)); return false; }
  }
}

exports.handler = async (event) => {
  const method = event.httpMethod || "GET";
  const q = event.queryStringParameters || {};

  // ---- the salon's invoice page (public, key-protected, rate-limited)
  if (method === "GET" && q.v !== undefined) {
    if (!(await L.rateHit(`bill:ip:${ipOf(event)}`, 600, 60))) return html(429, '<!doctype html><meta charset="utf-8"><title>Slow down</title>Too many requests. Try again in a few minutes.');
    if (!/^[0-9a-f]{32}$/.test(String(q.v))) return notFound();
    const [inv] = await L.db(`invoices?view_key=eq.${q.v}&select=*`);
    return inv ? html(200, B.invoiceHTML(inv, seller())) : notFound();
  }

  if (method !== "GET" && method !== "POST") return L.json(405, { error: "method" }, false);
  if (!(await L.rateHit(`bill:admin:${ipOf(event)}`, 600, 300))) return L.json(429, { error: "slow down" }, false);
  const admin = isAdmin(event);
  if (admin === null) return L.json(503, { error: "billing admin is off: set BILLING_ADMIN_KEY (32+ characters) in Netlify" }, false);
  if (!admin) return L.json(401, { error: "invalid key" }, false);
  const s = seller();

  if (method === "GET") {
    const [clients, invoices] = await Promise.all([
      L.db("clients?select=id,name,niche,owner_whatsapp,active,config&order=name.asc&limit=500"),
      L.db("invoices?select=*&order=created_at.desc&limit=500"),
    ]);
    const now = new Date();
    return L.json(200, {
      seller: { name: s.name, udyam: s.udyam, upi_id: s.vpa, upi_ready: !!s.vpa },
      clients: (clients || []).map((c) => ({ id: c.id, name: (c.config && c.config.business) || c.name, active: c.active !== false, has_whatsapp: !!c.owner_whatsapp })),
      invoices: (invoices || []).map((i) => view(i, now)).sort((a, b) => String(b.created_at || "").localeCompare(String(a.created_at || ""))),
    }, false);
  }

  let input; try { input = JSON.parse(event.body || "{}"); } catch (e) { return L.json(400, { error: "bad json" }, false); }
  const action = String(input.action || "");
  if (!ACTIONS.has(action)) return L.json(400, { error: "unknown action" }, false);

  if (action === "create") {
    if (!/^[\w-]{1,64}$/.test(String(input.client_id || ""))) return L.json(400, { error: "pick a client" }, false);
    const [client] = await L.db(`clients?id=eq.${L.enc(input.client_id)}&select=id,name,niche,owner_whatsapp,config`);
    if (!client) return L.json(404, { error: "no such client" }, false);
    let bill;
    try { bill = B.computeBill((Array.isArray(input.items) ? input.items : []).map((it) => ({ desc: it && it.desc, qty: it && it.qty, rate: it && it.amount }))); }
    catch (e) { return L.json(400, { error: e.message }, false); }
    const dueDays = input.due_days == null ? 7 : Number(input.due_days);
    if (!Number.isInteger(dueDays) || dueDays < 0 || dueDays > 90) return L.json(400, { error: "due in 0–90 days" }, false);
    const cfg = client.config || {};
    const billTo = { name: cfg.business || client.name, address: cfg.address || "", phone: client.owner_whatsapp || "" };
    const inv = await L.db("rpc/create_invoice", { method: "POST", body: {
      p_client: client.id, p_issued: istToday(), p_due: istToday(dueDays), p_period: String(input.period || "").slice(0, 40) || null,
      p_bill_to: billTo, p_lines: bill.rows.map((r) => ({ desc: r.desc, qty: r.qty, rate_paise: r.rate })), p_total: bill.total } });
    return L.json(200, { ok: true, invoice: view(Array.isArray(inv) ? inv[0] : inv) }, false);
  }

  const number = String(input.number || "");
  if (!NUMBER.test(number)) return L.json(400, { error: "bad invoice number" }, false);
  const [inv] = await L.db(`invoices?number=eq.${L.enc(number)}&select=*`);
  if (!inv) return L.json(404, { error: "no such invoice" }, false);
  const patch = (body) => L.db(`invoices?number=eq.${L.enc(number)}`, { method: "PATCH", prefer: "return=minimal", body });

  if (action === "send" || action === "remind") {
    if (inv.status !== "due") return L.json(409, { error: `this invoice is ${inv.status}` }, false);
    const [client] = await L.db(`clients?id=eq.${L.enc(inv.client_id)}&select=id,name,niche,phone_number_id,owner_whatsapp,config`);
    if (!client || !client.owner_whatsapp || !client.phone_number_id) return L.json(409, { error: "this client has no WhatsApp number set up" }, false);
    const late = B.overdueDays(inv);
    const text = action === "remind"
      ? `🙏 Gentle reminder: Invoice ${number} for ${B.money(inv.total_paise)}${inv.period ? ` (${inv.period})` : ""} is ${late ? `overdue by ${late} day${late === 1 ? "" : "s"}` : "due"}. View and pay by UPI: ${linkFor(inv)} . Already paid? Please ignore this; thank you!`
      : `🧾 Invoice ${number} from ${s.name}: ${B.money(inv.total_paise)}${inv.period ? ` for ${inv.period}` : ""}${inv.due_on ? `, due ${B.nice(inv.due_on)}` : ""}. View and pay by UPI: ${linkFor(inv)}`;
    const short = { head: `${action === "remind" ? "Reminder: " : ""}Invoice ${number}, ${B.money(inv.total_paise)}${inv.due_on ? `, due ${B.nice(inv.due_on)}` : ""}. Pay:`, link: linkFor(inv) };
    if (!(await message(client, text, short))) return L.json(502, { error: "WhatsApp didn't accept the message; try again later" }, false);
    await patch({ sent_at: new Date().toISOString() });
    return L.json(200, { ok: true }, false);
  }
  if (action === "paid") {
    if (inv.status === "void") return L.json(409, { error: "this invoice is void" }, false);
    const ref = input.ref == null || input.ref === "" ? null : String(input.ref).trim();
    if (ref !== null && !UTR.test(ref)) return L.json(400, { error: "the UPI reference is 6–35 letters or digits (no spaces)" }, false);
    const paidOn = input.paid_on ? String(input.paid_on) : istToday();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(paidOn) || paidOn > istToday()) return L.json(400, { error: "paid date must be today or earlier" }, false);
    await patch({ status: "paid", paid_on: paidOn, paid_ref: ref });
    return L.json(200, { ok: true }, false);
  }
  // void
  if (inv.status === "paid") return L.json(409, { error: "this invoice is paid; it can't be voided" }, false);
  await patch({ status: "void" });
  return L.json(200, { ok: true }, false);
};

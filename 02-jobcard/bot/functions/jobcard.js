/*
 * JobCard WhatsApp webhook (b2.q09). Modelled on 01-botbhai/botbhai/core/functions/whatsapp.js.
 * URL after deploy: https://<jobcard-site>.netlify.app/.netlify/functions/jobcard
 *
 * The technician sends a voice note (or types) after a job. The bot:
 *   signature check → dedupe (Meta retries) → find the technician by his WhatsApp number →
 *   voice note → Supabase Edge Function `transcribe-extract` (Sarvam STT, key stays there) →
 *   parseTranscript() → reply with the card and "✅ Correct / ✏️ Edit" buttons →
 *   on ✅: save customer + job card + invoice (FY number) → English PDF → sent to the technician as a document.
 * Only the technician is messaged; he forwards the bill himself (WhatsApp Business policy: no unsolicited customer messages).
 *
 * Env vars (Netlify → Site configuration → Environment variables; Akhil sets them, never Claude):
 *   WA_VERIFY_TOKEN       any word, also typed into Meta's webhook settings
 *   WA_ACCESS_TOKEN       Meta System User token (secret)
 *   WA_APP_SECRET         Meta app secret, REQUIRED in production (X-Hub-Signature-256)
 *   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY   JobCard Supabase project (secret key)
 */
import crypto from "node:crypto";
import { parseTranscript } from "../../lib/parse.mjs";
import { computeInvoice, invoicePDF, upiLink, SAC } from "../../lib/invoice.mjs";

const GRAPH = "https://graph.facebook.com/v21.0";
const IGNORE = new Set(["reaction", "system", "unsupported", "ephemeral", "request_welcome", "order"]);
const MAX_VOICE_S = 120; // research a4: cap notes at about 2 min

// ---------------------------------------------------------------- small I/O helpers
const env = (k) => process.env[k] || "";
export async function db(path, { method = "GET", body, prefer } = {}) {
  const r = await fetch(`${env("SUPABASE_URL")}/rest/v1/${path}`, { method, body: body === undefined ? undefined : JSON.stringify(body),
    headers: { apikey: env("SUPABASE_SERVICE_ROLE_KEY"), Authorization: `Bearer ${env("SUPABASE_SERVICE_ROLE_KEY")}`, "Content-Type": "application/json", ...(prefer ? { Prefer: prefer } : {}) } });
  if (!r.ok) throw new Error(`db ${method} ${path.split("?")[0]} ${r.status}`);
  const t = await r.text(); return t ? JSON.parse(t) : null;
}
const rpc = (fn, args) => db(`rpc/${fn}`, { method: "POST", body: args });
async function graph(path, { method = "GET", body, form } = {}) {
  const r = await fetch(`${GRAPH}/${path}`, { method, body: form || (body && JSON.stringify(body)),
    headers: { Authorization: `Bearer ${env("WA_ACCESS_TOKEN")}`, ...(form ? {} : { "Content-Type": "application/json" }) } });
  if (!r.ok) throw new Error(`graph ${path} ${r.status}`);
  return r.json();
}
const send = (pnid, to, msg) => graph(`${pnid}/messages`, { method: "POST", body: { messaging_product: "whatsapp", to, ...msg } });
const sendText = (pnid, to, text) => send(pnid, to, { type: "text", text: { body: text.slice(0, 4096) } });
const json = (statusCode, o) => ({ statusCode, headers: { "Content-Type": "application/json" }, body: JSON.stringify(o) });

export function validSignature(event) {
  const secret = env("WA_APP_SECRET");
  if (!secret) return env("ALLOW_UNSIGNED") === "1"; // first local test only; never in production
  const sig = (event.headers || {})["x-hub-signature-256"] || "";
  const raw = event.isBase64Encoded ? Buffer.from(event.body, "base64") : Buffer.from(event.body || "");
  const expected = "sha256=" + crypto.createHmac("sha256", secret).update(raw).digest("hex");
  return sig.length === expected.length && crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected));
}
async function firstTime(id) { // insert-or-ignore; an empty result means we saw this message already
  const rows = await db("wa_processed?on_conflict=id", { method: "POST", body: { id }, prefer: "resolution=ignore-duplicates,return=representation" });
  return Array.isArray(rows) && rows.length > 0;
}

// ---------------------------------------------------------------- words the technician sees (te / hi / en)
const S = {
  en: { unknown: "This number isn't registered with JobCard yet. Sign up in the JobCard app, then send your job as a voice note.",
        deaf: "Sorry, I couldn't hear that note. Please type the job, e.g. \"Split AC gas refill 2500, customer Sita 9000033333\".",
        long: "That note is longer than 2 minutes. Please send a shorter one (just the work and the amounts).",
        check: "Please check this job card:", ok: "✅ Correct", edit: "✏️ Edit",
        editAsk: "Send the change as a voice note or text, e.g. \"capacitor 450\" or \"customer Sita 9000033333\".",
        needRates: "I still need the amount for:", needParts: "I didn't hear any work or amounts. Please say what you did and the price.",
        saved: "Saved. Bill {no} for {amt} is below — forward it to the customer.", none: "No job card is waiting. Send a voice note after the job.",
        noPdf: "Saved bill {no} for {amt}. Open the JobCard app to share the Telugu bill." },
  te: { unknown: "ఈ నంబర్ JobCard లో లేదు. ముందు JobCard యాప్‌లో చేరండి, తర్వాత పని వివరాలు వాయిస్ నోట్‌గా పంపండి.",
        deaf: "క్షమించండి, వాయిస్ నోట్ వినిపించలేదు. పని టైప్ చేయండి, ఉదా. \"Split AC gas refill 2500, customer Sita 9000033333\".",
        long: "నోట్ 2 నిమిషాల కంటే ఎక్కువ ఉంది. పని, ధరలు మాత్రమే చెప్పి చిన్న నోట్ పంపండి.",
        check: "ఈ జాబ్ కార్డ్ సరిచూడండి:", ok: "✅ సరైనది", edit: "✏️ మార్చు",
        editAsk: "మార్పు వాయిస్ లేదా టెక్స్ట్‌గా పంపండి, ఉదా. \"capacitor 450\".",
        needRates: "వీటి ధర ఇంకా కావాలి:", needParts: "పని లేదా ధరలు వినిపించలేదు. ఏం చేశారో, ధర ఎంతో చెప్పండి.",
        saved: "సేవ్ అయింది. బిల్ {no}, మొత్తం {amt} కింద ఉంది — కస్టమర్‌కి ఫార్వర్డ్ చేయండి.", none: "ఏ జాబ్ కార్డ్ పెండింగ్‌లో లేదు. పని అయ్యాక వాయిస్ నోట్ పంపండి.",
        noPdf: "బిల్ {no} ({amt}) సేవ్ అయింది. తెలుగు బిల్ కోసం JobCard యాప్ ఓపెన్ చేయండి." },
  hi: { unknown: "यह नंबर JobCard में नहीं है। पहले JobCard ऐप में जुड़ें, फिर काम का वॉइस नोट भेजें।",
        deaf: "माफ़ कीजिए, वॉइस नोट सुनाई नहीं दिया। काम टाइप करें, जैसे \"Split AC gas refill 2500, customer Sita 9000033333\"।",
        long: "नोट 2 मिनट से लंबा है। सिर्फ़ काम और दाम बताकर छोटा नोट भेजें।",
        check: "यह जॉब कार्ड जाँच लें:", ok: "✅ सही है", edit: "✏️ बदलें",
        editAsk: "बदलाव वॉइस या टेक्स्ट में भेजें, जैसे \"capacitor 450\"।",
        needRates: "इनका दाम अभी चाहिए:", needParts: "काम या दाम सुनाई नहीं दिया। क्या किया और कितने का, बताइए।",
        saved: "सेव हो गया। बिल {no}, कुल {amt} नीचे है — ग्राहक को फ़ॉरवर्ड करें।", none: "कोई जॉब कार्ड बाकी नहीं है। काम के बाद वॉइस नोट भेजें।",
        noPdf: "बिल {no} ({amt}) सेव हो गया। हिंदी/तेलुगु बिल के लिए JobCard ऐप खोलें।" },
};
const say = (lang, key, vars = {}) => (S[lang] || S.en)[key].replace(/\{(\w+)\}/g, (_, k) => vars[k]);
const rs = (rupees) => "₹" + Number(rupees).toLocaleString("en-IN");
const LABEL = { split_ac: "Split AC", window_ac: "Window AC", cassette_ac: "Cassette AC", ac: "AC", fridge: "Fridge", washing_machine: "Washing machine" };

/** The card as the technician reads it. The total is always the sum of the parts, never the spoken number. */
export function cardText(card, lang = "en") {
  const c = card.customer || {}; const lines = [say(lang, "check")];
  lines.push(`👤 ${c.name || "—"}${c.phone ? " · " + c.phone : ""}${c.area ? " · " + c.area : ""}`);
  lines.push(`🔧 ${[LABEL[card.appliance] || card.appliance, card.brand, card.capacity_tons && card.capacity_tons + " ton"].filter(Boolean).join(" · ") || "—"}`);
  for (const p of card.parts) lines.push(`• ${p.desc}${p.qty > 1 ? " × " + p.qty : ""}: ${p.rate == null ? "?" : rs(p.rate)}`);
  lines.push(`*Total: ${rs(partsTotal(card))}*`);
  if (card.total != null && card.total !== partsTotal(card)) lines.push(`⚠️ You said ${rs(card.total)}; the items add up to ${rs(partsTotal(card))}.`);
  if (card.next_service) lines.push(`📅 Next service: ${card.next_service}`);
  return lines.join("\n");
}
const partsTotal = (card) => card.parts.reduce((s, p) => s + (p.rate || 0) * (p.qty || 1), 0);

/** An edit note changes only what it mentions: new parts are added, a part said again gets its new amount. */
export function mergeCard(prev, next) {
  const out = { ...prev, customer: { ...prev.customer } };
  for (const [k, v] of Object.entries(next.customer || {})) if (v) out.customer[k] = v;
  for (const k of ["appliance", "brand", "capacity_tons", "next_service"]) if (next[k] != null) out[k] = next[k];
  out.issues = [...new Set([...(prev.issues || []), ...(next.issues || [])])];
  out.parts = prev.parts.map((p) => ({ ...p }));
  for (const p of next.parts) { const same = out.parts.find((q) => q.desc === p.desc); if (same) { if (p.rate != null) same.rate = p.rate; } else out.parts.push(p); }
  out.total = next.total ?? null; // a spoken total belongs to the note it was spoken in
  out.notes = [prev.notes, next.notes].filter(Boolean).join(" | ");
  return out;
}

// ---------------------------------------------------------------- voice → text
async function transcribe(mediaId, lang) { // returns { text, seconds } or null
  try {
    const meta = await graph(mediaId);
    const audio = Buffer.from(await (await fetch(meta.url, { headers: { Authorization: `Bearer ${env("WA_ACCESS_TOKEN")}` } })).arrayBuffer());
    const r = await fetch(`${env("SUPABASE_URL")}/functions/v1/transcribe-extract`, { method: "POST", signal: AbortSignal.timeout(20000),
      headers: { Authorization: `Bearer ${env("SUPABASE_SERVICE_ROLE_KEY")}`, "Content-Type": "application/json" },
      body: JSON.stringify({ audio_base64: audio.toString("base64"), mime: meta.mime_type || "audio/ogg", lang: `${lang}-IN` }) });
    if (!r.ok) return null;
    const out = await r.json(); return out && typeof out.text === "string" ? { text: out.text, seconds: Math.ceil(Number(out.seconds) || 0) } : null;
  } catch { return null; }
}

// ---------------------------------------------------------------- confirm → save → PDF
async function saveJob(tech, card) {
  const c = card.customer || {}; let customer = null;
  if (c.phone || c.name) {
    const row = { technician_id: tech.id, name: c.name || "Customer", phone: c.phone || null, area: c.area || null };
    [customer] = await db(c.phone ? "customers?on_conflict=technician_id,phone" : "customers",
      { method: "POST", body: row, prefer: (c.phone ? "resolution=merge-duplicates," : "") + "return=representation" });
  }
  const [job] = await db("job_cards", { method: "POST", prefer: "return=representation", body: {
    technician_id: tech.id, customer_id: customer ? customer.id : null, status: "invoiced", appliance: card.appliance || null, brand: card.brand || null,
    capacity_tons: card.capacity_tons || null, issues: card.issues || [], parts: card.parts, transcript: card.notes || null, next_service: card.next_service || null } });
  const sac = (card.issues || []).includes("installation") ? SAC.install : SAC.home;
  const t = computeInvoice({ kind: tech.gst_kind || "unregistered", lines: card.parts.map((p) => ({ desc: p.desc, sac, qty: p.qty || 1, rate: p.rate })),
    supplierState: tech.state || "Telangana", placeOfSupply: tech.state || "Telangana" });
  const today = new Date(Date.now() + 330 * 60000).toISOString().slice(0, 10); // IST date
  const number = await rpc("next_invoice_no_for", { p_tech: tech.id, p_date: today });
  await db("invoices", { method: "POST", prefer: "return=minimal", body: { technician_id: tech.id, job_card_id: job.id, customer_id: customer ? customer.id : null,
    number, fy: number.split("/")[1], kind: t.kind, issued_on: today, lines: card.parts, taxable_paise: t.taxable, cgst_paise: t.cgst, sgst_paise: t.sgst,
    igst_paise: t.igst, payable_paise: t.payable, place_of_supply: t.placeOfSupply } });
  return { number, t, customer: { name: c.name || "Customer", phone: c.phone || "", address: c.area || "" }, date: today };
}

async function billPdf(tech, saved) {
  const inv = { number: saved.number, date: saved.date, customer: saved.customer,
    supplier: { name: tech.business_name || tech.name, address: tech.address || "", phone: "+91 " + tech.phone, gstin: tech.gstin || "", udyam: tech.udyam || "" } };
  let qrPng;
  if (tech.upi_vpa) try { const QR = (await import("qrcode")).default; qrPng = await QR.toBuffer(upiLink({ vpa: tech.upi_vpa, name: inv.supplier.name, amountPaise: saved.t.payable, invoice: saved.number })); } catch { /* no QR is fine */ }
  try { return await invoicePDF(inv, saved.t, { qrPng }); } catch { return null; } // Telugu names: the app prints the bilingual bill instead
}

async function sendPdf(pnid, to, bytes, filename, caption) {
  const form = new FormData();
  form.append("messaging_product", "whatsapp"); form.append("type", "application/pdf");
  form.append("file", new Blob([bytes], { type: "application/pdf" }), filename);
  const { id } = await graph(`${pnid}/media`, { method: "POST", form });
  return send(pnid, to, { type: "document", document: { id, filename, caption } });
}

// ---------------------------------------------------------------- one message
function intentOf(msg) {
  if (msg.type === "interactive") { const r = msg.interactive.button_reply || {}; return r.id === "jc:ok" ? "ok" : r.id === "jc:edit" ? "edit" : null; }
  if (msg.type === "button") return /✅|correct|ok/i.test(msg.button.text || "") ? "ok" : null;
  if (msg.type === "text" && /^\s*(✅|ok|okay|yes|correct|sari|సరే|సరైనది|haan|हाँ|ठीक)\s*[.!]*\s*$/i.test(msg.text.body)) return "ok";
  return null;
}

async function handleMessage(pnid, msg) {
  const from = msg.from; const phone10 = String(from).replace(/^91/, "");
  const [tech] = await db(`technicians?phone=eq.${encodeURIComponent(phone10)}&select=*`);
  if (!tech) return sendText(pnid, from, S.en.unknown + "\n\n" + S.te.unknown);
  const lang = tech.language || "te";
  const [sess] = await db(`bot_sessions?technician_id=eq.${tech.id}&select=pending`);
  const pending = sess && sess.pending;
  const keep = (card) => db("bot_sessions?on_conflict=technician_id", { method: "POST", prefer: "resolution=merge-duplicates,return=minimal",
    body: { technician_id: tech.id, pending: card, updated_at: new Date().toISOString() } });

  const intent = intentOf(msg);
  if (intent === "edit") return sendText(pnid, from, say(lang, "editAsk"));
  if (intent === "ok") {
    if (!pending) return sendText(pnid, from, say(lang, "none"));
    const unpriced = pending.parts.filter((p) => p.rate == null);
    if (!pending.parts.length) return sendText(pnid, from, say(lang, "needParts"));
    if (unpriced.length) return sendText(pnid, from, `${say(lang, "needRates")} ${unpriced.map((p) => p.desc).join(", ")}`);
    const saved = await saveJob(tech, pending);
    await keep(null);
    const amt = rs(saved.t.payable / 100); const bytes = await billPdf(tech, saved);
    if (!bytes) return sendText(pnid, from, say(lang, "noPdf", { no: saved.number, amt }));
    await sendText(pnid, from, say(lang, "saved", { no: saved.number, amt }));
    return sendPdf(pnid, from, bytes, `${saved.number.replace(/\//g, "-")}.pdf`, `${saved.customer.name} · ${amt}`);
  }

  let text = msg.type === "text" ? msg.text.body : "";
  if (msg.type === "audio") {
    const heard = await transcribe(msg.audio.id, lang);
    if (heard && heard.seconds) await rpc("add_usage", { p_tech: tech.id, p_seconds: heard.seconds }).catch(() => {});
    if (heard && heard.seconds > MAX_VOICE_S) return sendText(pnid, from, say(lang, "long"));
    text = heard ? heard.text : "";
    if (!text.trim()) return sendText(pnid, from, say(lang, "deaf"));
  }
  if (!text.trim()) return sendText(pnid, from, say(lang, "deaf"));

  const parsed = parseTranscript(text);
  const card = pending ? mergeCard(pending, parsed) : parsed;
  await keep(card);
  if (!card.parts.length) return sendText(pnid, from, say(lang, "needParts"));
  return send(pnid, from, { type: "interactive", interactive: { type: "button", body: { text: cardText(card, lang).slice(0, 1024) },
    action: { buttons: [{ type: "reply", reply: { id: "jc:ok", title: say(lang, "ok") } }, { type: "reply", reply: { id: "jc:edit", title: say(lang, "edit") } }] } } });
}

export async function handler(event) {
  if (event.httpMethod === "GET") { // Meta verifies the webhook once
    const q = event.queryStringParameters || {};
    if (q["hub.mode"] === "subscribe" && env("WA_VERIFY_TOKEN") && q["hub.verify_token"] === env("WA_VERIFY_TOKEN")) return { statusCode: 200, body: q["hub.challenge"] };
    return { statusCode: 403, body: "forbidden" };
  }
  if (event.httpMethod !== "POST") return json(405, { error: "method" });
  if (!validSignature(event)) return json(401, { error: "bad signature" });
  let body; try { body = JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, "base64").toString() : event.body || "{}"); } catch { return json(400, { error: "bad json" }); }
  for (const entry of body.entry || []) for (const change of entry.changes || []) {
    const v = change.value || {}; const pnid = v.metadata && v.metadata.phone_number_id;
    for (const msg of v.messages || []) {
      try {
        if (IGNORE.has(msg.type)) continue;
        if (!(await firstTime(msg.id))) continue; // Meta retry: already handled
        await handleMessage(pnid, msg);
      } catch (err) { console.error("jobcard", err.message); }
    }
  }
  return json(200, { ok: true }); // always 200 fast, or Meta retries
}

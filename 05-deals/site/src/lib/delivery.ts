// A21 / K-06: deliver a kit after a Razorpay payment. Runtime-agnostic (Web Crypto + a tiny key-value store), wired to
// Cloudflare Pages Functions in /functions/api/. Rules from Razorpay's webhook docs (checked 16 Oct 2026):
//   · X-Razorpay-Signature = HMAC-SHA256(raw body, webhook secret): verify the RAW body, never a re-serialised one
//   · the same event can arrive more than once → x-razorpay-event-id makes it idempotent
//   · events can arrive out of order → only payment.captured (or order.paid) delivers
// Secrets live only in the host's environment: RAZORPAY_WEBHOOK_SECRET, KIT_COPY_URLS (JSON {"kit:tier": "…/copy"}).
import { PDFDocument, StandardFonts, rgb } from "pdf-lib";
import { KITS } from "./kits";

export interface Store { get(k: string): Promise<string | null>; put(k: string, v: string): Promise<void> }
export interface Env { RAZORPAY_WEBHOOK_SECRET?: string; KIT_COPY_URLS?: string; store: Store }
export const memoryStore = (): Store => { const m = new Map<string, string>(); return { get: async (k) => m.get(k) ?? null, put: async (k, v) => { m.set(k, v); } }; };

// slug → { name, prices by tier (₹) } straight from the landing-page data, so a price can't differ between page and delivery
export const PRODUCTS: Record<string, { name: string; prices: Record<string, number> }> = Object.fromEntries(
  KITS.map((k) => [k.slug, { name: k.name, prices: Object.fromEntries(k.tiers.filter((t) => t.price > 0).map((t) => [t.id, t.price])) }]));

const hex = (b: ArrayBuffer) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
async function hmac(secret: string, body: string) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body)));
}
function sameString(a: string, b: string) { // constant-time for equal lengths
  if (a.length !== b.length) return false;
  let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

/** Which kit and tier a payment is for: notes {kit, tier} first, else the Payment Page title in the description. */
export function resolveProduct(p: { notes?: Record<string, string> | unknown[]; description?: string | null }) {
  const notes = (p.notes && !Array.isArray(p.notes) ? p.notes : {}) as Record<string, string>;
  if (notes.kit && PRODUCTS[notes.kit]) return { kit: notes.kit, tier: notes.tier === "pro" ? "pro" : "kit" };
  const d = (p.description || "").toLowerCase();
  const k = KITS.find((x) => d.includes(x.name.toLowerCase()) || d.includes(x.slug));
  return k ? { kit: k.slug, tier: /\bpro\b/.test(d) ? "pro" : "kit" } : null;
}

export async function handleWebhook(raw: string, signature: string, eventId: string, env: Env) {
  const secret = env.RAZORPAY_WEBHOOK_SECRET || "";
  if (secret.length < 8 || !signature || !sameString(await hmac(secret, raw), signature.trim().toLowerCase())) return { status: 401, result: "bad signature" };
  if (eventId && (await env.store.get(`evt:${eventId}`))) return { status: 200, result: "duplicate" };
  let ev: any; try { ev = JSON.parse(raw); } catch { return { status: 400, result: "bad json" }; }
  if (!["payment.captured", "order.paid"].includes(ev.event)) { if (eventId) await env.store.put(`evt:${eventId}`, "1"); return { status: 200, result: "ignored" }; }
  const p = ev.payload?.payment?.entity || {};
  if (!/^pay_[A-Za-z0-9]{6,40}$/.test(p.id || "")) return { status: 400, result: "no payment id" };
  if (await env.store.get(`pay:${p.id}`)) { if (eventId) await env.store.put(`evt:${eventId}`, "1"); return { status: 200, result: "duplicate" }; }
  const prod = resolveProduct(p);
  const price = prod ? PRODUCTS[prod.kit].prices[prod.tier] : undefined;
  const ok = !!prod && price !== undefined && p.currency === "INR" && p.amount === price * 100;
  const order = { paymentId: p.id, kit: prod?.kit ?? null, tier: prod?.tier ?? null, amount: p.amount, email: p.email || "", status: ok ? "paid" : "review",
    reason: ok ? "" : !prod ? "unknown product" : "amount does not match the price", at: new Date().toISOString() };
  await env.store.put(`pay:${p.id}`, JSON.stringify(order));
  if (eventId) await env.store.put(`evt:${eventId}`, "1");
  return { status: 200, result: ok ? "delivered" : "review" };
}

/** What the success page may show. Only a paid order gets the copy link. */
export async function deliveryStatus(paymentId: string, env: Env) {
  if (!/^pay_[A-Za-z0-9]{6,40}$/.test(paymentId || "")) return { state: "invalid" as const };
  const raw = await env.store.get(`pay:${paymentId}`);
  if (!raw) return { state: "pending" as const };                     // webhook not here yet: the page retries
  const o = JSON.parse(raw);
  if (o.status !== "paid") return { state: "review" as const };       // a human checks it (email on the page)
  const urls = JSON.parse(env.KIT_COPY_URLS || "{}");
  return { state: "paid" as const, kit: o.kit, tier: o.tier, copyUrl: urls[`${o.kit}:${o.tier}`] || null, name: PRODUCTS[o.kit].name };
}

const GUIDE: Record<string, string[]> = {
  "gate-2027": ["1. Open the copy link and tap Make a copy. The sheet is now yours, in your Google Drive.",
    "2. Plan tab: choose your exam date (on your admit card). The countdown updates every day.",
    "3. Syllabus tab: mark topics Not started / Learning / Done. When Done, type the date: revisions come back after 1, 3, 7 and 21 days.",
    "4. Daily log: type your study hours. The streak counts itself. Week tab: hours against your target.",
    "5. Pro: after each mock, count careless and concept mistakes per subject in the Mocks tab. Fix the biggest leak first.",
    "Dates: 6, 7, 13, 14, 20, 21 Feb 2027 (IIT Madras). Always check gate2027.iitm.ac.in. Not an official GATE product."],
  "upsc-2027": ["1. Open the copy link and tap Make a copy.", "2. Plan tab: Prelims is on 23 May 2027 (UPSC calendar).",
    "3. Mark topics as you go; revisions come back after 1, 3, 7 and 21 days.", "Not an official UPSC product. Check upsc.gov.in."],
  "tax-sip-2026-27": ["1. Open the copy link and tap Make a copy.", "2. Tax tab: type your yearly gross salary and age band, then the old-regime deductions you really have.",
    "3. HRA tab only if you pay rent and get HRA. The SIP goal tab uses the return YOU assume: it promises nothing.",
    "4. Self-check tab: every row must say PASS. Tax year 2026-27 rules; above Rs 50 lakh, surcharge is not included.",
    "A calculator, not tax or investment advice."],
};

/** A short guide PDF stamped with the buyer's email and payment ID on every page (discourages forwarding). */
export async function stampedGuide(o: { kit: string; tier: string; email: string; paymentId: string }) {
  const doc = await PDFDocument.create(); const font = await doc.embedFont(StandardFonts.Helvetica); const bold = await doc.embedFont(StandardFonts.HelveticaBold);
  doc.setTitle(`${PRODUCTS[o.kit].name}: guide`); doc.setAuthor("Kalpa Labs"); doc.setSubject(`Licensed to ${o.email} (${o.paymentId})`);
  const ink = rgb(0.098, 0.11, 0.2), hero = rgb(0.11, 0.14, 0.39), muted = rgb(0.36, 0.38, 0.47);
  const latin = (s: string) => s.replace(/[–—]/g, "-").replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/₹/g, "Rs ").replace(/[^\x20-\x7E]/g, "");
  const pages = [[`${PRODUCTS[o.kit].name} (${o.tier === "pro" ? "Kit Pro" : "Kit"})`, "Thank you for buying from Kalpa Labs.", "", "How to start"],
                 ["Help", `Write to aakhiil51458@gmail.com with your payment ID (${o.paymentId}).`, "Refunds within 7 days if the kit isn't as described.", "",
                  "Personal licence: please don't share the copy link or this guide. Institutes can buy a 50-student licence."]];
  pages[0].push(...(GUIDE[o.kit] || []));
  for (const lines of pages) {
    const page = doc.addPage([595.28, 841.89]); let y = 780;
    page.drawRectangle({ x: 0, y: 812, width: 595.28, height: 30, color: hero });
    page.drawText("Kalpa Labs · Kit guide".replace("·", "-"), { x: 40, y: 822, size: 11, font: bold, color: rgb(0.96, 0.95, 0.91) });
    lines.forEach((t, i) => {
      const f = i === 0 ? bold : font, size = i === 0 ? 16 : 11;
      for (const part of wrap(latin(t), 86)) { page.drawText(part, { x: 40, y, size, font: f, color: ink }); y -= size + 7; }
      if (!t) y -= 4;
    });
    page.drawText(latin(`Licensed to ${o.email} - payment ${o.paymentId} - personal use only`), { x: 40, y: 30, size: 9, font, color: muted });
  }
  return doc.save();
}
function wrap(s: string, n: number) { const out: string[] = []; let line = ""; for (const w of s.split(" ")) { if ((line + " " + w).trim().length > n) { out.push(line); line = w; } else line = (line + " " + w).trim(); } if (line || !out.length) out.push(line); return out; }

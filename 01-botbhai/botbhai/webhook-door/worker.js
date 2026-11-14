// BotBhai webhook door (A245, DESIGN §3 in 00-hq/agent-engine/DESIGN.md).
// A private Hugging Face Space can't receive webhooks, so this Cloudflare Worker is the only public door:
//   GET  /meta      Meta's subscribe handshake (hub.verify_token must match)
//   POST /meta      WhatsApp Cloud API events, checked with X-Hub-Signature-256 (HMAC-SHA256 of the raw body)
//   POST /telegram  Telegram updates, checked with X-Telegram-Bot-Api-Secret-Token
// Good requests are rate-limited per IP, then forwarded to the private Space with the HF token.
// Closed until Akhil says "go": DOOR_OPEN must be "true" or every request gets 503.
// Secrets (Akhil sets them in Cloudflare, never in git): META_APP_SECRET, META_VERIFY_TOKEN,
// TELEGRAM_SECRET, HF_TOKEN. Vars: FORWARD_URL (https Space URL), DOOR_OPEN, RATE_PER_MIN.
// Optional binding LIMITER (Workers rate-limit binding) is used when present; else a per-isolate window.

export const MAX_BODY = 256 * 1024;        // WhatsApp/Telegram events are a few KB
export const FORWARD_TIMEOUT_MS = 10000;
const HEADERS = { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
const reply = (status, text = "") => new Response(text, { status, headers: HEADERS });
const enc = new TextEncoder();

export function safeEqual(a, b) {           // constant time for equal lengths
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function hmacHex(secret, bytes) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", key, bytes));
  return [...sig].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function metaSignatureOk(secret, bytes, header) {
  if (!header || !header.startsWith("sha256=")) return false;
  const given = header.slice(7).toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(given)) return false;
  return safeEqual(await hmacHex(secret, bytes), given);
}

// Fixed one-minute window per key, per isolate. Good enough to stop one IP flooding; the
// LIMITER binding (when bound) shares the count across Cloudflare's machines.
export function makeLimiter(perMin, now = () => Date.now()) {
  const hits = new Map();
  return (key) => {
    const win = Math.floor(now() / 60000);
    const h = hits.get(key);
    if (!h || h.win !== win) { hits.set(key, { win, n: 1 }); if (hits.size > 5000) hits.clear(); return true; }
    h.n += 1;
    return h.n <= perMin;
  };
}

async function readBody(request) {
  const len = Number(request.headers.get("content-length") || 0);
  if (len > MAX_BODY) return null;
  const buf = new Uint8Array(await request.arrayBuffer());
  return buf.byteLength > MAX_BODY ? null : buf;
}

function log(event, extra = {}) {             // never logs bodies, tokens or phone numbers
  console.log(JSON.stringify({ at: new Date().toISOString(), door: event, ...extra }));
}

export async function handle(request, env, deps = {}) {
  const fetchFn = deps.fetch || fetch;
  const allow = deps.limit || defaultLimit(env);
  const url = new URL(request.url);
  const route = url.pathname === "/meta" ? "meta" : url.pathname === "/telegram" ? "telegram" : null;

  if (env.DOOR_OPEN !== "true") return reply(503, "closed");
  if (!route) return reply(404, "not found");
  if (!(route === "meta" && request.method === "GET") && request.method !== "POST") return reply(405, "method not allowed");

  const ip = request.headers.get("cf-connecting-ip") || "unknown";
  if (!(await allow(`${route}:${ip}`))) { log("rate_limited", { route }); return reply(429, "slow down"); }

  if (route === "meta" && request.method === "GET") {     // subscribe handshake
    const p = url.searchParams;
    const challenge = p.get("hub.challenge") || "";
    if (!env.META_VERIFY_TOKEN) return reply(500, "not configured");
    if (p.get("hub.mode") === "subscribe" && safeEqual(p.get("hub.verify_token") || "", env.META_VERIFY_TOKEN) && /^[0-9A-Za-z_-]{1,128}$/.test(challenge)) {
      log("meta_verified");
      return reply(200, challenge);
    }
    log("meta_verify_refused");
    return reply(403, "forbidden");
  }

  const secret = route === "meta" ? env.META_APP_SECRET : env.TELEGRAM_SECRET;
  if (!secret || !env.HF_TOKEN || !/^https:\/\//.test(env.FORWARD_URL || "")) return reply(500, "not configured");

  const body = await readBody(request);
  if (!body) { log("too_large", { route }); return reply(413, "too large"); }

  const ok = route === "meta"
    ? await metaSignatureOk(secret, body, request.headers.get("x-hub-signature-256"))
    : safeEqual(request.headers.get("x-telegram-bot-api-secret-token") || "", secret);
  if (!ok) { log("bad_signature", { route }); return reply(401, "unauthorized"); }

  try {
    const r = await fetchFn(`${env.FORWARD_URL.replace(/\/+$/, "")}/${route}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${env.HF_TOKEN}`, "Content-Type": request.headers.get("content-type") || "application/json", "X-Kalpa-Source": route },
      body,
      signal: AbortSignal.timeout(FORWARD_TIMEOUT_MS),
    });
    if (!r.ok) { log("forward_failed", { route, status: r.status }); return reply(502, "upstream error"); }
    log("forwarded", { route });
    return reply(200, "ok");
  } catch (e) {
    log("forward_error", { route, error: e.name });   // 502 makes Meta/Telegram retry later
    return reply(502, "upstream error");
  }
}

let isolateLimit;
function defaultLimit(env) {
  if (env.LIMITER && typeof env.LIMITER.limit === "function") return async (key) => (await env.LIMITER.limit({ key })).success;
  isolateLimit ||= makeLimiter(Number(env.RATE_PER_MIN) || 120);
  return isolateLimit;
}

export default { fetch: (request, env) => handle(request, env) };

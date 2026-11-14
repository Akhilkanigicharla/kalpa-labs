// node 01-botbhai/botbhai/webhook-door/test.mjs : forged signatures, floods, closed door, big bodies, forwarding (no network).
import assert from "node:assert/strict";
import { handle, hmacHex, makeLimiter, safeEqual, MAX_BODY } from "./worker.js";

const env = { DOOR_OPEN: "true", META_APP_SECRET: "app-secret", META_VERIFY_TOKEN: "verify-me", TELEGRAM_SECRET: "tg-secret_1", HF_TOKEN: "hf_x", FORWARD_URL: "https://kalpa-flows.hf.space/" };
const sent = [];
const fwd = async (url, opt) => { sent.push({ url, opt }); return { ok: true, status: 200 }; };
const yes = async () => true;
const deps = { fetch: fwd, limit: yes };
const B = "https://door.example.workers.dev";
const body = JSON.stringify({ object: "whatsapp_business_account", entry: [{ changes: [{ value: { messages: [{ text: { body: "నమస్తే 🙏 slot kavali" } }] } }] }] });
const sig = "sha256=" + (await hmacHex("app-secret", new TextEncoder().encode(body)));
const meta = (h = {}, b = body) => new Request(`${B}/meta`, { method: "POST", headers: { "content-type": "application/json", "cf-connecting-ip": "1.2.3.4", ...h }, body: b });
let n = 0; const check = async (label, req, status, d = deps, e = env) => { const r = await handle(req, e, d); assert.equal(r.status, status, label); n++; return r; };

// valid Meta event is forwarded with the HF token, raw body untouched
await check("valid meta", meta({ "x-hub-signature-256": sig }), 200);
assert.equal(sent.length, 1); assert.equal(sent[0].url, "https://kalpa-flows.hf.space/meta");
assert.equal(sent[0].opt.headers.Authorization, "Bearer hf_x");
assert.equal(new TextDecoder().decode(sent[0].opt.body), body); n++;
// forged / missing / malformed / uppercase-valid signatures
await check("forged sig", meta({ "x-hub-signature-256": "sha256=" + "0".repeat(64) }), 401);
await check("missing sig", meta(), 401);
await check("sha1 sig", meta({ "x-hub-signature-256": "sha1=abc" }), 401);
await check("tampered body", meta({ "x-hub-signature-256": sig }, body.replace("slot", "free")), 401);
await check("upper-case hex ok", meta({ "x-hub-signature-256": sig.toUpperCase().replace("SHA256=", "sha256=") }), 200);
await check("other secret", meta({ "x-hub-signature-256": "sha256=" + (await hmacHex("wrong", new TextEncoder().encode(body))) }), 401);
assert.equal(sent.length, 2, "only the 2 valid requests forwarded"); n++;
// Meta handshake
await check("handshake ok", new Request(`${B}/meta?hub.mode=subscribe&hub.verify_token=verify-me&hub.challenge=1158201444`), 200)
  .then(async (r) => assert.equal(await r.text(), "1158201444"));
await check("handshake bad token", new Request(`${B}/meta?hub.mode=subscribe&hub.verify_token=nope&hub.challenge=1`), 403);
await check("handshake script challenge", new Request(`${B}/meta?hub.mode=subscribe&hub.verify_token=verify-me&hub.challenge=<script>`), 403);
// Telegram secret token
const tg = (h = {}) => new Request(`${B}/telegram`, { method: "POST", headers: { "content-type": "application/json", ...h }, body: '{"update_id":1}' });
await check("telegram ok", tg({ "x-telegram-bot-api-secret-token": "tg-secret_1" }), 200);
assert.equal(sent.at(-1).url, "https://kalpa-flows.hf.space/telegram"); n++;
await check("telegram forged", tg({ "x-telegram-bot-api-secret-token": "tg-secret_2" }), 401);
await check("telegram missing", tg(), 401);
// rate limit: 3 per minute per IP, 4th refused, other IP fine, next minute fine
let t = 0; const lim = makeLimiter(3, () => t);
const ld = { fetch: fwd, limit: lim };
for (let i = 0; i < 3; i++) await check(`within limit ${i}`, meta({ "x-hub-signature-256": sig }), 200, ld);
await check("over limit", meta({ "x-hub-signature-256": sig }), 429, ld);
await check("other ip", meta({ "x-hub-signature-256": sig, "cf-connecting-ip": "5.6.7.8" }), 200, ld);
t = 61000; await check("next minute", meta({ "x-hub-signature-256": sig }), 200, ld);
// over-limit forged call never reaches the signature check or the Space
const before = sent.length; await check("flood of forged", meta({ "x-hub-signature-256": "sha256=" + "f".repeat(64) }), 401, ld);
assert.equal(sent.length, before); n++;
// LIMITER binding path
await check("binding refuses", meta({ "x-hub-signature-256": sig }), 429, { fetch: fwd }, { ...env, LIMITER: { limit: async () => ({ success: false }) } });
// closed door, wrong path/method, missing config, size cap, upstream failures
await check("closed", meta({ "x-hub-signature-256": sig }), 503, deps, { ...env, DOOR_OPEN: "false" });
await check("closed unset", meta({ "x-hub-signature-256": sig }), 503, deps, { ...env, DOOR_OPEN: undefined });
await check("404", new Request(`${B}/admin`, { method: "POST", body: "x" }), 404);
await check("405", new Request(`${B}/telegram`), 405);
await check("no secret", meta({ "x-hub-signature-256": sig }), 500, deps, { ...env, META_APP_SECRET: "" });
await check("http forward refused", meta({ "x-hub-signature-256": sig }), 500, deps, { ...env, FORWARD_URL: "http://evil" });
await check("too large", meta({ "x-hub-signature-256": sig }, "x".repeat(MAX_BODY + 1)), 413);
await check("upstream 500", meta({ "x-hub-signature-256": sig }), 502, { fetch: async () => ({ ok: false, status: 500 }), limit: yes });
await check("upstream timeout", meta({ "x-hub-signature-256": sig }), 502, { fetch: async () => { throw Object.assign(new Error("t"), { name: "TimeoutError" }); }, limit: yes });
const r = await check("headers", tg({ "x-telegram-bot-api-secret-token": "tg-secret_1" }), 200);
assert.equal(r.headers.get("x-content-type-options"), "nosniff"); assert.equal(r.headers.get("cache-control"), "no-store"); n++;
assert.equal(safeEqual("abc", "abd"), false); assert.equal(safeEqual("abc", "abc"), true); assert.equal(safeEqual("a", undefined), false); n++;
console.log(`PASS webhook-door: ${n} checks`);

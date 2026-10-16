// The Cloudflare Pages adapters, driven with real Request objects and an in-memory KV.
import { expect, test } from "vitest";
import { onRequestPost } from "./razorpay-webhook";
import { onRequestGet as kit } from "./kit";
import { onRequestGet as guide } from "./kit-guide";

const kv = () => { const m = new Map<string, string>(); return { get: async (k: string) => m.get(k) ?? null, put: async (k: string, v: string) => { m.set(k, v); } }; };
async function sign(body: string, secret: string) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return [...new Uint8Array(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(body)))].map((b) => b.toString(16).padStart(2, "0")).join("");
}

test("webhook → status → stamped guide, end to end through the Pages handlers", async () => {
  const env = { KITS_KV: kv(), RAZORPAY_WEBHOOK_SECRET: "fake_secret_123", KIT_COPY_URLS: JSON.stringify({ "gate-2027:kit": "https://docs.google.com/spreadsheets/d/FAKE/copy" }) };
  const body = JSON.stringify({ event: "payment.captured", payload: { payment: { entity: { id: "pay_TESTe2e0000001", amount: 19900, currency: "INR", email: "ravi@example.com", notes: { kit: "gate-2027", tier: "kit" } } } } });
  const before = await (await kit({ request: new Request("https://x/api/kit?p=pay_TESTe2e0000001"), env })).json();
  expect(before.state).toBe("pending");
  const res = await onRequestPost({ request: new Request("https://x/api/razorpay-webhook", { method: "POST", body, headers: { "x-razorpay-signature": await sign(body, "fake_secret_123"), "x-razorpay-event-id": "evt_e2e" } }), env });
  expect(res.status).toBe(200); expect(res.headers.get("cache-control")).toBe("no-store");
  const after = await (await kit({ request: new Request("https://x/api/kit?p=pay_TESTe2e0000001"), env })).json();
  expect(after).toMatchObject({ state: "paid", copyUrl: "https://docs.google.com/spreadsheets/d/FAKE/copy" });
  const g = await guide({ request: new Request("https://x/api/kit-guide?p=pay_TESTe2e0000001"), env });
  expect(g.headers.get("content-type")).toBe("application/pdf");
  expect(new TextDecoder().decode(new Uint8Array(await g.arrayBuffer()).slice(0, 5))).toBe("%PDF-");
  expect((await guide({ request: new Request("https://x/api/kit-guide?p=pay_TESTnotpaid0001"), env })).status).toBe(404);
  const forged = await onRequestPost({ request: new Request("https://x/api/razorpay-webhook", { method: "POST", body, headers: { "x-razorpay-signature": "00" } }), env });
  expect(forged.status).toBe(401);
});

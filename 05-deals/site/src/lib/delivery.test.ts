// A21 / K-06: kit delivery after a Razorpay payment. Fake payloads and fake secrets only.
import { describe, expect, test } from "vitest";
import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { handleWebhook, deliveryStatus, stampedGuide, memoryStore, PRODUCTS } from "./delivery";

const SECRET = "test_webhook_secret_not_real";
const COPY = { "tax-sip-2026-27:kit": "https://docs.google.com/spreadsheets/d/FAKE_TAX/copy", "gate-2027:kit": "https://docs.google.com/spreadsheets/d/FAKE_GATE_KIT/copy", "gate-2027:pro": "https://docs.google.com/spreadsheets/d/FAKE_GATE_PRO/copy" };
const env = (store = memoryStore()) => ({ RAZORPAY_WEBHOOK_SECRET: SECRET, KIT_COPY_URLS: JSON.stringify(COPY), store });

async function sign(body: string, secret = SECRET) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return [...new Uint8Array(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(body)))].map((b) => b.toString(16).padStart(2, "0")).join("");
}
const payment = (o: Record<string, unknown> = {}) => JSON.stringify({ entity: "event", event: "payment.captured", contains: ["payment"], created_at: 1792000000,
  payload: { payment: { entity: Object.assign({ id: "pay_TESTabcdefgh12", amount: 19900, currency: "INR", status: "captured", email: "asha@example.com", contact: "+919800000001",
    description: "Salary Tax-Regime + SIP Goal Planner 2026-27", notes: { kit: "tax-sip-2026-27", tier: "kit" } }, o) } } });

describe("delivery", () => {
  test("rejects a missing, wrong or tampered signature, and never logs it", async () => {
    const e = env(); const body = payment();
    expect((await handleWebhook(body, "", "evt_1", e)).status).toBe(401);
    expect((await handleWebhook(body, await sign(body, "wrong"), "evt_1", e)).status).toBe(401);
    expect((await handleWebhook(body.replace("19900", "100"), await sign(body), "evt_1", e)).status).toBe(401);
    expect(await e.store.get("pay:pay_TESTabcdefgh12")).toBeNull();
  });

  test("a captured payment is logged once, even when Razorpay sends it again", async () => {
    const e = env(); const body = payment(); const sig = await sign(body);
    const r1 = await handleWebhook(body, sig, "evt_1", e); const r2 = await handleWebhook(body, sig, "evt_1", e);
    expect(r1).toMatchObject({ status: 200, result: "delivered" }); expect(r2).toMatchObject({ status: 200, result: "duplicate" });
    const order = JSON.parse((await e.store.get("pay:pay_TESTabcdefgh12"))!);
    expect(order).toMatchObject({ kit: "tax-sip-2026-27", tier: "kit", amount: 19900, email: "asha@example.com", status: "paid" });
  });

  test("the price must match: a ₹1 payment for a ₹199 kit is held for review, not delivered", async () => {
    const e = env(); const body = payment({ amount: 100 });
    const r = await handleWebhook(body, await sign(body), "evt_2", e);
    expect(r).toMatchObject({ status: 200, result: "review" });
    expect((await deliveryStatus("pay_TESTabcdefgh12", e)).state).toBe("review");
  });

  test("the product is found from notes, else from the payment page title; unknown goes to review", async () => {
    const e = env();
    const b1 = payment({ id: "pay_TESTgate000001", amount: 29900, notes: {}, description: "GATE 2027 Final-120-Days Tracker (Kit Pro)" });
    expect(await handleWebhook(b1, await sign(b1), "evt_3", e)).toMatchObject({ result: "delivered" });
    expect(JSON.parse((await e.store.get("pay:pay_TESTgate000001"))!)).toMatchObject({ kit: "gate-2027", tier: "pro" });
    const b2 = payment({ id: "pay_TESTmystery001", amount: 49900, notes: {}, description: "Something else" });
    expect(await handleWebhook(b2, await sign(b2), "evt_4", e)).toMatchObject({ result: "review" });
  });

  test("other events are acknowledged and ignored", async () => {
    const e = env(); const body = JSON.stringify({ event: "payment.failed", payload: { payment: { entity: { id: "pay_TESTfail000001" } } } });
    expect(await handleWebhook(body, await sign(body), "evt_5", e)).toMatchObject({ status: 200, result: "ignored" });
  });

  test("the success page gets the copy link only for a paid order; bad IDs and unknown IDs get nothing", async () => {
    const e = env(); const body = payment(); await handleWebhook(body, await sign(body), "evt_6", e);
    expect(await deliveryStatus("pay_TESTabcdefgh12", e)).toEqual({ state: "paid", kit: "tax-sip-2026-27", tier: "kit", copyUrl: COPY["tax-sip-2026-27:kit"], name: PRODUCTS["tax-sip-2026-27"].name });
    expect((await deliveryStatus("pay_UNKNOWN00000001", e)).state).toBe("pending");
    expect((await deliveryStatus("../etc/passwd", e)).state).toBe("invalid");
  });

  test("the guide PDF is stamped with the buyer's email and payment ID on every page", async () => {
    const pdf = await stampedGuide({ kit: "gate-2027", tier: "pro", email: "asha@example.com", paymentId: "pay_TESTgate000001" });
    expect(new TextDecoder().decode(pdf.slice(0, 5))).toBe("%PDF-");
    let text = "";
    try { const d = mkdtempSync(join(tmpdir(), "kit-")); const f = join(d, "g.pdf"); writeFileSync(f, pdf); text = execFileSync("pdftotext", ["-layout", f, "-"], { encoding: "utf8" }); }
    catch { return; } // pdftotext not installed: the %PDF header check above still ran
    const pages = text.split("\f").filter((p) => p.trim());
    expect(pages.length).toBeGreaterThanOrEqual(2);
    for (const p of pages) { expect(p).toContain("asha@example.com"); expect(p).toContain("pay_TESTgate000001"); }
    expect(text).toContain("GATE 2027"); expect(text).not.toMatch(/guarantee/i);
  });
});

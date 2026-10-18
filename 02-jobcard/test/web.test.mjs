// A37 (b2.q15): "my customers" PWA logic. The 390 px / offline / installability checks are in web/check.py.
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";

execFileSync(process.execPath, [new URL("../web/build.mjs", import.meta.url).pathname], { env: { ...process.env, SUPABASE_URL: "", SUPABASE_ANON_KEY: "" } });
const { createApi, demoData, filterCustomers, normPhone, views } = await import("../web/logic.mjs");
const { STR } = await import("../web/i18n.mjs");

test("phone numbers", () => {
  for (const s of ["9000033333", "+91 90000 33333", "090000-33333", "91-9000033333"]) assert.equal(normPhone(s), "9000033333", s);
  for (const s of ["12345", "5000033333", "", null]) assert.equal(normPhone(s), null);
});

test("phone OTP sign-in, token refresh, RLS reads with the user's token, sign-out on 401", async () => {
  const calls = []; let clock = 1_000_000; let status = 200;
  const mem = new Map(); const store = { getItem: (k) => mem.get(k) ?? null, setItem: (k, v) => mem.set(k, v), removeItem: (k) => mem.delete(k) };
  const fetchFn = async (url, init = {}) => {
    calls.push({ url, init }); const body = init.body ? JSON.parse(init.body) : null;
    const res = (s, j) => ({ ok: s < 300, status: s, json: async () => j, text: async () => JSON.stringify(j) });
    if (url.endsWith("/auth/v1/otp")) return res(200, {});
    if (url.endsWith("/auth/v1/verify")) return body.token === "123456" ? res(200, { access_token: "A1", refresh_token: "R1", expires_in: 3600, user: { id: "t1" } }) : res(400, { msg: "Token has expired or is invalid" });
    if (url.includes("grant_type=refresh_token")) return res(200, { access_token: "A2", refresh_token: "R2", expires_in: 3600 });
    return res(status, [{ id: "c1" }]);
  };
  const api = createApi({ url: "https://p.supabase.co", anonKey: "anon", fetchFn, store, now: () => clock });
  assert.equal(api.signedIn(), false);
  await api.sendOtp("9000022222"); assert.equal(JSON.parse(calls[0].init.body).phone, "+919000022222");
  await assert.rejects(api.verifyOtp("9000022222", "000000"), /invalid/);
  await api.verifyOtp("9000022222", " 123456 "); assert.equal(api.signedIn(), true);
  assert.deepEqual(await api.rest("customers?select=id"), [{ id: "c1" }]); assert.equal(calls.at(-1).init.headers.Authorization, "Bearer A1");
  assert.ok(createApi({ url: "https://p.supabase.co", anonKey: "anon", fetchFn, store }).signedIn(), "session survives a reload");
  clock += 3_600_000; await api.rest("customers?select=id");
  assert.ok(calls.some((c) => c.url.includes("refresh_token"))); assert.equal(calls.at(-1).init.headers.Authorization, "Bearer A2");
  status = 401; await assert.rejects(api.rest("customers"), (e) => e.signedOut === true); assert.equal(api.signedIn(), false);
});

test("tabs: due list with wa.me reminders, opt-in respected, AMC, customers, bills", () => {
  const today = "2026-10-18"; const d = demoData(today); const v = views(d, today, "te");
  assert.deepEqual(v.due.map((x) => x.name), ["Ravi Teja", "Sita Devi", "Anjali", "Padma"]); // Lakshmi not opted in; Imran just visited
  assert.equal(v.notOpted, 1); assert.equal(v.due[0].overdue, true);
  assert.ok(v.due[1].wa.startsWith("https://wa.me/919000033333?text=")); assert.match(v.due[1].text, /^నమస్తే Sita Devi గారు/);
  assert.match(views(d, today, "hi").due[1].text, /^नमस्ते/);
  assert.equal(v.amc.length, 1); assert.equal(v.amc[0].customer.name, "Anjali");
  assert.equal(v.customers.find((c) => c.id === "c3").spentPaise, 295000); assert.equal(v.unpaidPaise, 345000);
  assert.equal(v.quota.limitSeconds, 9000); assert.equal(v.quota.blocked, false);
  assert.deepEqual(filterCustomers(v.customers, "ameer").map((c) => c.name), ["Sita Devi"]);
  assert.deepEqual(filterCustomers(v.customers, "77777").map((c) => c.name), ["Imran Khan"]);
});

test("te / hi / en have the same keys; built files are in place", () => {
  const keys = (o) => Object.keys(o).sort();
  assert.deepEqual(keys(STR.te), keys(STR.en)); assert.deepEqual(keys(STR.hi), keys(STR.en));
  const sw = fs.readFileSync(new URL("../web/sw.js", import.meta.url), "utf8");
  assert.match(sw, /const CACHE = "jobcard-[0-9a-f]{12}"/); assert.match(sw, /"\/vendor\/parse\.mjs"/);
  const m = JSON.parse(fs.readFileSync(new URL("../web/manifest.webmanifest", import.meta.url)));
  assert.equal(m.display, "standalone"); assert.ok(m.icons.some((i) => i.sizes === "512x512" && i.purpose === "maskable"));
  assert.match(fs.readFileSync(new URL("../web/config.js", import.meta.url), "utf8"), /"demo":true/);
});

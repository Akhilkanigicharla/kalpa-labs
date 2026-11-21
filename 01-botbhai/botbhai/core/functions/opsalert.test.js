// A312: error alerts to Akhil's private Telegram. Run: node core/functions/opsalert.test.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { alertOps, scrub, kindOf, _reset } = require("./_opsalert.js");

const sent = [];
const fakeFetch = async (url, opts) => { sent.push({ url, body: JSON.parse(opts.body) }); return { ok: true, status: 200 }; };
const env = { OPS_ALERT_BOT_TOKEN: "t0k", OPS_ALERT_CHAT_ID: "42" };
const t = (name, fn) => fn().then(() => console.log("ok -", name)).catch((e) => { console.error("FAIL -", name, e.message); process.exitCode = 1; });

(async () => {
  await t("two errors of one kind in an hour -> one alert", async () => {
    _reset(); sent.length = 0;
    const now = Date.parse("2026-11-21T14:00:00Z");
    const a = await alertOps({ app: "BotBhai", fn: "whatsapp", err: new Error("Supabase down for +91 98765 43210") }, { fetch: fakeFetch, env, now });
    const b = await alertOps({ app: "BotBhai", fn: "whatsapp", err: new Error("again 9876543210") }, { fetch: fakeFetch, env, now: now + 60000 });
    assert.strictEqual(a.sent, true); assert.strictEqual(b.sent, false); assert.strictEqual(b.reason, "throttled");
    assert.strictEqual(sent.length, 1);
    assert.match(sent[0].url, /api\.telegram\.org\/bott0k\/sendMessage$/);
    assert.strictEqual(sent[0].body.chat_id, "42");
  });

  await t("alert text holds no phone number, email or customer text", async () => {
    const text = sent[0].body.text;
    assert.ok(!/\d{5,}/.test(text.replace(/[\s+().-]/g, "")), text);
    assert.ok(!/98765|43210|Supabase down/.test(text), text);
    assert.match(text, /BotBhai · whatsapp · error · \d\d:\d\d IST/);
    assert.ok(text.length <= 200);
  });

  await t("after an hour the same kind alerts again and says how many were held back", async () => {
    const now = Date.parse("2026-11-21T15:00:01Z");
    const c = await alertOps({ app: "BotBhai", fn: "whatsapp", err: new Error("x") }, { fetch: fakeFetch, env, now });
    assert.strictEqual(c.sent, true); assert.match(sent[1].body.text, /\+1 more in the last hour/);
  });

  await t("another kind is not throttled by the first", async () => {
    const e = new Error("slow"); e.name = "TimeoutError";
    const d = await alertOps({ app: "JobCard", fn: "reminders", err: e }, { fetch: fakeFetch, env, now: Date.parse("2026-11-21T15:00:02Z") });
    assert.strictEqual(d.sent, true); assert.match(sent[2].body.text, /JobCard · reminders · timeout/);
  });

  await t("shared limiter (other function copies) can say no; a broken one falls back to memory", async () => {
    _reset(); sent.length = 0;
    const no = await alertOps({ app: "BotBhai", fn: "chat" }, { fetch: fakeFetch, env, allow: async () => false });
    assert.strictEqual(no.sent, false); assert.strictEqual(sent.length, 0);
    _reset();
    const yes = await alertOps({ app: "BotBhai", fn: "chat" }, { fetch: fakeFetch, env, allow: async () => { throw new Error("db down"); } });
    assert.strictEqual(yes.sent, true);
  });

  await t("no token -> off, never throws; Telegram down -> never throws", async () => {
    _reset();
    const off = await alertOps({ app: "BotBhai", fn: "x" }, { fetch: fakeFetch, env: {} });
    assert.deepStrictEqual(off, { sent: false, reason: "off" });
    _reset();
    const down = await alertOps({ app: "BotBhai", fn: "x" }, { fetch: async () => { throw new Error("offline"); }, env });
    assert.strictEqual(down.sent, false); assert.strictEqual(down.reason, "send_failed");
    _reset();
    const r429 = await alertOps({ app: "BotBhai", fn: "y" }, { fetch: async () => ({ ok: false, status: 429 }), env });
    assert.strictEqual(r429.reason, "http_429");
  });

  await t("hostile names are cleaned (no markup, no digits runs, short)", async () => {
    assert.strictEqual(kindOf({ name: "AbortError" }), "timeout");
    assert.strictEqual(kindOf({ status: 401 }), "http_401");
    assert.strictEqual(kindOf(undefined), "error");
    const s = scrub("<b>Ravi 😀</b> +91-98765-43210 ravi@x.in " + "a".repeat(200));
    assert.ok(!/[<>@]/.test(s) && !/\d{5}/.test(s) && s.length <= 30, s);
  });

  await t("JobCard copy is identical to the BotBhai copy (one source, no drift)", async () => {
    const a = fs.readFileSync(path.join(__dirname, "_opsalert.js"), "utf8");
    const b = fs.readFileSync(path.join(__dirname, "../../../../02-jobcard/lib/opsalert.cjs"), "utf8");
    assert.strictEqual(a, b);
  });
})();

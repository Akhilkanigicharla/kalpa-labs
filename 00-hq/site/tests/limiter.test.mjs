// A303 tests: node 00-hq/site/tests/limiter.test.mjs (fake Netlify Blobs store, no network)
// The live limiter failed because every Netlify function copy kept its own count. These prove the shared count holds
// across copies, never stores a raw IP, cleans old days, and falls back to the local count when the store is slow or down.
import assert from "node:assert";
import handler, { limitedShared, reply, BUSY, BUSY_TEXT, LIMIT } from "../netlify/functions/chat.mjs";

function fakeStore({ delay = 0, fail = false } = {}) {
  const data = new Map();
  const wait = () => new Promise((r, j) => (fail ? j(new Error("store down")) : delay === Infinity ? null : setTimeout(r, delay)));
  return {
    data,
    async get(k) { await wait(); return data.has(k) ? JSON.parse(data.get(k)) : null; },
    async setJSON(k, v) { await wait(); data.set(k, JSON.stringify(v)); },
    async delete(k) { await wait(); data.delete(k); },
    async list({ prefix = "" } = {}) { await wait(); return { blobs: [...data.keys()].filter((k) => k.startsWith(prefix)).map((key) => ({ key })) }; },
  };
}
const now = Date.UTC(2026, 10, 27, 10, 0, 0);
const keepAlive = setInterval(() => {}, 1000); // AbortSignal.timeout timers do not keep Node alive on their own

// 1. two function copies (separate local memory) sharing one store: request 13 in a minute is refused
{
  const store = fakeStore(), memA = new Map(), memB = new Map(); const out = [];
  for (let k = 0; k < LIMIT + 1; k++) out.push(await limitedShared("203.0.113.7", { store, mem: k % 2 ? memA : memB, now: now + k * 100 }));
  assert.deepStrictEqual(out.slice(0, LIMIT), Array(LIMIT).fill(false));
  assert.strictEqual(out[LIMIT], true, "13th message in a minute across two copies is limited");
  // a new minute starts a new count
  assert.strictEqual(await limitedShared("203.0.113.7", { store, mem: new Map(), now: now + 61_000 }), false);
  // another visitor is not affected
  assert.strictEqual(await limitedShared("198.51.100.1", { store, mem: new Map(), now: now + 500 }), false);
  // DPDP: no raw IP in keys or values; keys are day/<hash>
  for (const [k, v] of store.data) { assert.ok(!k.includes("203.0.113") && !v.includes("203.0.113"), k); assert.match(k, /^2026-11-27\/[0-9a-f]{32}$/); }
}
// 2. old days are deleted (cleanup runs when asked), today's keys stay
{
  const store = fakeStore();
  store.data.set("2026-11-25/" + "a".repeat(32), '{"t":1,"n":1}');
  store.data.set("2026-11-26/" + "b".repeat(32), '{"t":1,"n":1}');
  await limitedShared("203.0.113.7", { store, mem: new Map(), now, sweep: true });
  assert.deepStrictEqual([...store.data.keys()].map((k) => k.slice(0, 10)), ["2026-11-27"]);
}
// 3. store slow or down: answers within the time box and falls back to this copy's own count
for (const store of [fakeStore({ delay: Infinity }), fakeStore({ fail: true })]) {
  const mem = new Map(); const t = Date.now(); const out = [];
  for (let k = 0; k < LIMIT + 1; k++) out.push(await limitedShared("203.0.113.9", { store, mem, now: now + k, timeoutMs: 50 }));
  assert.ok(Date.now() - t < 50 * (LIMIT + 1) + 500, "never waits long for the store");
  assert.strictEqual(out[LIMIT], true, "local count still limits when the store is unavailable");
}
// 4. every free model slow: reply gives BUSY inside the deadline instead of hanging
{
  const slow = (url, opts) => new Promise((_, j) => opts.signal.addEventListener("abort", () => j(new Error("aborted"))));
  const t = Date.now();
  const out = await reply({ chatInput: "hi" }, { fetchImpl: slow, env: { GROQ_API_KEY: "g", OPENROUTER_API_KEY: "o" }, deadlineMs: 300 });
  assert.strictEqual(out, BUSY);
  assert.ok(Date.now() - t < 1000, "busy answer comes fast: " + (Date.now() - t) + " ms");
  // all models fail fast (no keys): still null -> 503, not "busy"
  assert.strictEqual(await reply({ chatInput: "hi" }, { fetchImpl: slow, env: {}, deadlineMs: 300 }), null);
}
// 5. handler: busy is a polite 429 with Retry-After (the page shows it and does not retry)
{
  process.env.GROQ_API_KEY = "g"; process.env.CHAT_DEADLINE_MS = "200";
  const real = globalThis.fetch;
  globalThis.fetch = (url, opts) => new Promise((_, j) => opts?.signal?.addEventListener("abort", () => j(new Error("aborted"))));
  const quiet = console.log; console.log = () => {};
  try {
    const r = await handler(new Request("http://x/api/chat", { method: "POST", body: JSON.stringify({ chatInput: "hi" }) }), { ip: "192.0.2.50" });
    assert.strictEqual(r.status, 429); assert.strictEqual(r.headers.get("Retry-After"), "60");
    const d = await r.json(); assert.ok(d.busy && /busy/i.test(d.output), d.output);
    const te = await handler(new Request("http://x/api/chat", { method: "POST", body: JSON.stringify({ chatInput: "రేపు స్లాట్ ఉందా?" }) }), { ip: "192.0.2.51" });
    assert.strictEqual((await te.json()).output, BUSY_TEXT.te, "busy reply in the visitor's script");
  } finally { globalThis.fetch = real; console.log = quiet; delete process.env.GROQ_API_KEY; delete process.env.CHAT_DEADLINE_MS; }
}
clearInterval(keepAlive);
console.log("limiter + busy tests: PASS");

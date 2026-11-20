// Row 64 Load Testing for /api/chat. No dependencies (plain Node 20+).
//   node 00-hq/site/tests/load_chat.mjs                 # local: 50 visitors x 4 msgs + 1 fast clicker, model stubbed (300-1500 ms)
//   node 00-hq/site/tests/load_chat.mjs --url https://kalpalabs.dpdns.org/api/chat [--users 50] [--msgs 1]
// Live mode comes from one IP, so the 12-per-minute limit answers most calls with 429: that is the point
// (it proves the limiter holds under 50 parallel users) and keeps real model calls to about a dozen.
// Pass: p95 < 5 s, no 5xx except 503 "models unavailable" in live mode, 429s counted, the fast clicker gets 429s.
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const URL_ = arg("--url"), USERS = +arg("--users", 50), MSGS = +arg("--msgs", URL_ ? 1 : 4);
let send;
if (URL_) {
  send = async (_u, body) => {
    const r = await fetch(URL_, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: AbortSignal.timeout(30000) });
    return r.status;
  };
} else {
  process.env.GROQ_API_KEY = "stub"; process.env.OPENROUTER_API_KEY = "";
  const real = globalThis.fetch;
  globalThis.fetch = async (url, opts) => { // stand-in model: 300-1500 ms, like a free Groq model on a good day
    if (!String(url).includes("api.groq.com")) return real(url, opts);
    await new Promise((r) => setTimeout(r, 300 + Math.random() * 1200));
    return new Response(JSON.stringify({ choices: [{ message: { content: "Namaste! (load test)" } }] }), { status: 200 });
  };
  const { default: handler } = await import("../netlify/functions/chat.mjs");
  const quiet = console.log; console.log = () => {};
  send = async (u, body) => (await handler(new Request("http://local/api/chat", { method: "POST", body: JSON.stringify(body) }), { ip: u })).status;
  process.on("exit", () => { console.log = quiet; });
}
const ms = [], codes = {};
const one = async (u, i) => {
  const t = performance.now(); let s;
  try { s = await send(u, { sessionId: u, chatInput: `load test message ${i}`, history: [] }); } catch { s = "timeout"; }
  ms.push(performance.now() - t); codes[s] = (codes[s] || 0) + 1; return s;
};
const user = async (u) => { for (let i = 0; i < MSGS; i++) await one(u, i); };
const clicker = async () => { const out = []; for (let i = 0; i < 20; i++) out.push(await one("fast-clicker", i)); return out; };
const t0 = performance.now();
const [, clicks] = await Promise.all([Promise.all(Array.from({ length: USERS }, (_, k) => user(`visitor-${k}`))), clicker()]);
ms.sort((a, b) => a - b);
const p95 = ms[Math.ceil(ms.length * 0.95) - 1], p50 = ms[Math.ceil(ms.length * 0.5) - 1];
const bad5xx = Object.entries(codes).filter(([c]) => (c >= 500 && !(URL_ && c == 503)) || c === "timeout").reduce((n, [, v]) => n + v, 0);
const result = { mode: URL_ ? "live" : "local (model stubbed)", users: USERS, requests: ms.length, seconds: +((performance.now() - t0) / 1000).toFixed(1),
  p50_ms: Math.round(p50), p95_ms: Math.round(p95), codes, clicker_429: clicks.filter((s) => s === 429).length };
const ok = p95 < 5000 && bad5xx === 0 && result.clicker_429 > 0;
console.info(JSON.stringify(result));
console.info(ok ? "PASS load test" : "FAIL load test");
process.exitCode = ok ? 0 : 1;

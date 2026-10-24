// A85: every AI model name comes from core/models.json, and no file anywhere uses a model Groq has shut down.
// Run: node core/models.test.js
const assert = require("assert"); const fs = require("fs"); const path = require("path");
const M = require("./models.json");
const ROOT = path.resolve(__dirname, "../../.."); // the whole Kalpa repo
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };
console.log("Model name tests (A85)");
const SKIP = /(^|\/)(node_modules|\.git|dist|_dist|archive|vendor|log|__pycache__|out)(\/|$)/;
function files(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name), rel = path.relative(ROOT, p);
    if (SKIP.test(rel)) continue;
    if (e.isDirectory()) files(p, acc); else if (/\.(js|mjs|ts|tsx|py|json|ya?ml|toml|sh)$/.test(e.name)) acc.push(p);
  }
  return acc;
}
ok("models.json names the chat and speech models and is not itself retired", () => {
  assert.ok(M.groq_chat && M.groq_speech_to_text && Array.isArray(M.retired) && M.retired.length);
  assert.ok(!M.retired.includes(M.groq_chat) && !M.retired.includes(M.groq_speech_to_text));
});
ok("no code or config in the repo uses a retired Groq model", () => {
  const bad = [];
  for (const f of files(ROOT)) {
    if (f === path.join(__dirname, "models.json")) continue;
    const t = fs.readFileSync(f, "utf8");
    for (const m of M.retired) if (new RegExp(`["'\`]${m.replace(/[./-]/g, "\\$&")}["'\`]`).test(t)) bad.push(`${path.relative(ROOT, f)}: ${m}`);
  }
  assert.deepStrictEqual(bad, [], "retired model still used:\n" + bad.join("\n"));
});
ok("both call sites read the name from models.json (no hard-coded chat model)", () => {
  assert.match(fs.readFileSync(path.join(__dirname, "humanize.js"), "utf8"), /model = MODELS\.groq_chat/);
  assert.match(fs.readFileSync(path.join(__dirname, "../voice/agent.py"), "utf8"), /Settings\(model=GROQ_CHAT_MODEL\)/);
  assert.match(fs.readFileSync(path.join(__dirname, "../voice/Dockerfile"), "utf8"), /COPY core\/models\.json/);
});
(async () => {
  const H = require("./humanize.js"); const sent = [];
  const fake = async (url, o) => { sent.push(JSON.parse(o.body)); return { json: async () => ({ choices: [{ message: { content: "సరే, మీ బుకింగ్ 4:00 PM కి ఉంది." } }] }) }; };
  const out = await H.mirrorLanguage([{ text: "Okay, your booking is at 4:00 PM." }], "te", { apiKey: "test", fetchImpl: fake });
  assert.strictEqual(sent[0].model, M.groq_chat); assert.match(out[0].text, /సరే/);
  const down = await H.mirrorLanguage([{ text: "Hi" }], "te", { apiKey: "test", fetchImpl: async () => { throw new Error("400 model_decommissioned"); } });
  assert.strictEqual(down[0].text, "Hi");
  console.log("  ✓ translator uses " + M.groq_chat + "; an API error keeps the English reply");
  console.log(`model tests passed (${n + 1})`);
})().catch((e) => { console.error(e); process.exit(1); });

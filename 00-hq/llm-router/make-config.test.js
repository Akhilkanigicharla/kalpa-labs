const assert = require("assert");
const { build } = require("./make-config.js");
const allowed = require("./allowed.json").providers.map((p) => p.platform);
let c = build({ GROQ_API_KEY: "gsk_x", OPENROUTER_API_KEY: " ", AIRFORCE_API_KEY: "nope" });
assert.deepStrictEqual(c.keys.map((k) => k.platform), ["groq"], "only allowed providers with a value");
assert.ok(!("admin" in c), "no admin without both secrets");
c = build({ ROUTER_ADMIN_EMAIL: "a@b.c", ROUTER_ADMIN_PASSWORD: "longenough" });
assert.strictEqual(c.admin.email, "a@b.c");
assert.throws(() => build({ ROUTER_ADMIN_EMAIL: "a@b.c", ROUTER_ADMIN_PASSWORD: "short" }));
assert.ok(!allowed.some((p) => ["airforce", "pollinations", "electronhub", "llm7"].includes(p)), "unofficial proxies never allowed");
const A = require("./allowed.json");
for (const bad of ["huggingface", "cohere", "cerebras", "nvidia"]) {
  assert.ok(!allowed.includes(bad), `${bad} is trial/eval only, never production`);
  assert.ok(A.excluded.some((e) => e.platform === bad && e.reason && e.source), `${bad} exclusion has a reason + source`);
}
assert.deepStrictEqual(build({ HF_TOKEN: "hf_x", COHERE_API_KEY: "c", CEREBRAS_API_KEY: "c", NVIDIA_API_KEY: "n" }).keys, [], "excluded keys are ignored even if set");
const readme = require("fs").readFileSync(__dirname + "/README.md", "utf8");
for (const p of A.providers) {
  assert.ok(/^https:\/\//.test(p.terms) && /^\d{4}-\d{2}-\d{2}$/.test(p.checked), `${p.platform} has a terms link + date`);
  assert.ok(readme.includes(p.terms), `README links ${p.platform}'s terms page`);
}
// A244: PII-safe by default: only no-training providers, each with a dated official source
const both = { GROQ_API_KEY: "gsk_x", OPENROUTER_API_KEY: "sk-or-x" };
c = build(both);
assert.strictEqual(c.pii_safe, true);
assert.deepStrictEqual(c.keys.map((k) => k.platform), ["groq"], "OpenRouter free may train: no customer PII");
assert.deepStrictEqual(build({ ...both, ROUTER_ALLOW_TRAINING_PROVIDERS: "yes" }).keys.map((k) => k.platform), ["groq"], "only exact 1 opts out");
c = build({ ...both, ROUTER_ALLOW_TRAINING_PROVIDERS: "1" });
assert.strictEqual(c.pii_safe, false); assert.deepStrictEqual(c.keys.map((k) => k.platform), ["groq", "openrouter"]);
for (const p of A.providers) {
  assert.strictEqual(typeof p.pii, "boolean", `${p.platform} has a pii verdict`);
  assert.match(p.pii_source, /^https:\/\/.*\(checked \d{4}-\d{2}-\d{2}\)/, `${p.platform} pii verdict has a dated source`);
}
assert.ok(A.excluded.some((e) => e.platform === "google" && /human reviewers/.test(e.reason)), "free Gemini excluded for training");
console.log("llm-router config tests passed");
// CLI: rejects a short key; prints JSON (stdout) with a 64-hex key
const { spawnSync } = require("child_process");
let r = spawnSync(process.execPath, [__dirname + "/make-config.js"], { env: { ENCRYPTION_KEY: "a".repeat(32), GROQ_API_KEY: "gsk_x" } });
assert.notStrictEqual(r.status, 0); assert.match(String(r.stderr), /64 hex characters \(got 32\)/);
r = spawnSync(process.execPath, [__dirname + "/make-config.js"], { env: { ENCRYPTION_KEY: "ab".repeat(32), GROQ_API_KEY: "gsk_x" } });
assert.strictEqual(r.status, 0); assert.deepStrictEqual(JSON.parse(String(r.stdout)).keys.map((k) => k.platform), ["groq"]);
assert.ok(!String(r.stderr).includes("gsk_x"), "key never printed");
console.log("llm-router CLI tests passed");

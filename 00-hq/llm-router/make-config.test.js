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
console.log("llm-router config tests passed");

// Kalpa LLM router (A120): builds FreeLLMAPI's startup config from secrets at boot.
// Only providers with an official free tier whose terms we checked are allowed (allowed.json);
// the many unofficial "free" proxies FreeLLMAPI also supports are never enabled here.
const fs = require("fs");
const path = require("path");
const ALLOWED = require("./allowed.json");

function build(env) {
  const keys = [];
  for (const p of ALLOWED.providers) {
    const v = (env[p.env] || "").trim();
    if (v) keys.push({ platform: p.platform, key: v, label: "kalpa", enabled: true });
  }
  const cfg = { keys, routing: { strategy: "balanced" } };
  if (env.ROUTER_ADMIN_EMAIL && env.ROUTER_ADMIN_PASSWORD) {
    if (env.ROUTER_ADMIN_PASSWORD.length < 8) throw new Error("ROUTER_ADMIN_PASSWORD must be 8+ characters");
    cfg.admin = { email: env.ROUTER_ADMIN_EMAIL, password: env.ROUTER_ADMIN_PASSWORD };
  }
  return cfg;
}

if (require.main === module) {
  const out = process.env.FREEAPI_CONFIG_PATH || "/tmp/kalpa-router.json";
  if (!process.env.ENCRYPTION_KEY) { console.error("ENCRYPTION_KEY secret missing: provider keys can't be stored safely"); process.exit(1); }
  const cfg = build(process.env);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(cfg), { mode: 0o600 });
  console.log(`router config: ${cfg.keys.length} provider key(s): ${cfg.keys.map((k) => k.platform).join(", ") || "none yet"}`); // names only, never keys
}
module.exports = { build };

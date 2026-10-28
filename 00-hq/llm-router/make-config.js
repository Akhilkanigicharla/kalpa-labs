// Kalpa LLM router (A120): builds FreeLLMAPI's startup config from secrets at boot.
// Only providers with an official free tier whose terms we checked are allowed (allowed.json);
// the many unofficial "free" proxies FreeLLMAPI also supports are never enabled here.
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
  // Prints the config JSON on stdout for FREEAPI_CONFIG_JSON (no file on disk: works as any user, after restarts,
  // and keeps keys off the filesystem). Messages go to stderr; they name providers, never keys.
  const k = process.env.ENCRYPTION_KEY || "";
  if (!/^[0-9a-fA-F]{64}$/.test(k)) {
    console.error(`ENCRYPTION_KEY must be exactly 64 hex characters (got ${k.length}). Make a new one and paste all of it.`);
    process.exit(1);
  }
  const cfg = build(process.env);
  console.error(`router config: ${cfg.keys.length} provider key(s): ${cfg.keys.map((x) => x.platform).join(", ") || "none yet"}`);
  process.stdout.write(JSON.stringify(cfg));
}
module.exports = { build };

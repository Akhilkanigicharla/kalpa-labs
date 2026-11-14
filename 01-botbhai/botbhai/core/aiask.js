// A87 · AI fallback wiring for web chat and WhatsApp (server side only).
// Off switch, two levels:
//   · whole platform: Netlify env BOTBHAI_AI_FALLBACK=off
//   · one client:     clients.config.ai_fallback = false  (owner asks us; set in Supabase)
// It also stays off when no free model is configured (no GROQ_API_KEY and no LLM_ROUTER_URL/KEY).
// The model only picks an intent (core/fallback.js guards it); prices and slots always come from the setup.
const F = require("./fallback.js");
const { chat, MODELS } = require("./humanize.js");

function aiOn(client, env = process.env) {
  if (String(env.BOTBHAI_AI_FALLBACK || "").trim().toLowerCase() === "off") return false;
  if (((client && client.config) || {}).ai_fallback === false) return false;
  return !!(env.GROQ_API_KEY || (env.LLM_ROUTER_URL && env.LLM_ROUTER_KEY));
}

// ask(system, user) → model text. Groq free tier first, then the Kalpa router (A120). Throws if both fail.
function makeAsk(env = process.env, fetchImpl = fetch) {
  return async (system, user) => {
    const messages = [{ role: "system", content: system }, { role: "user", content: user }];
    if (env.GROQ_API_KEY) {
      try { return await chat(fetchImpl, "https://api.groq.com/openai/v1/chat/completions", env.GROQ_API_KEY, MODELS.groq_chat, messages); } catch (e) { /* try the router */ }
    }
    if (env.LLM_ROUTER_URL && env.LLM_ROUTER_KEY) return chat(fetchImpl, `${env.LLM_ROUTER_URL.replace(/\/$/, "")}/v1/chat/completions`, env.LLM_ROUTER_KEY, "auto:reliable", messages);
    throw new Error("no model");
  };
}

// Runs only when the rules logged "unanswered" and the switch is on. Never throws; on any problem the
// customer gets the rules' normal menu reply. `ask` can be injected (tests).
async function aiRescue(bot, out, meta, client, { ask, ms = 5000, env = process.env } = {}) {
  if (!out.events.some((e) => e.type === "unanswered") || !aiOn(client, env)) return out;
  try { return await F.rescue(bot, out, meta, ask || makeAsk(env), ms); } catch (e) { return out; }
}

// Inbox author for this turn's bot replies: "ai" when the free model chose the answer, so the owner sees it.
const authorOf = (out) => (out.events.some((e) => e.type === "ai_fallback") ? "ai" : "bot");

module.exports = { aiOn, makeAsk, aiRescue, authorOf };

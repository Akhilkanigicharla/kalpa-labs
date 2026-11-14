// A283 · Real free-model run of the 224-message corpus. Runs in GitHub Actions with the GROQ_API_KEY secret
// (workflow "BotBhai depth live"); saves the raw model answers to qa/depth.live.json, which qa/depth.test.js
// then checks offline (right intent, no invented price). Only the message and the setup's own service names
// and FAQ keywords are sent (core/fallback.js request()), never customer names, numbers or prices.
const fs = require("fs");
const path = require("path");
const { BotBhai: B } = require("../setups/index.js");
const F = require("../core/fallback.js");
const AI = require("../core/aiask.js");

const cases = fs.readFileSync(path.join(__dirname, "depth.cases.txt"), "utf8").split("\n")
  .filter((l) => l.trim() && !l.startsWith("#")).map((l) => { const [setup, lang, intent, ...t] = l.split("|"); return { setup, lang, intent, text: t.join("|") }; });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  if (!process.env.GROQ_API_KEY && !process.env.LLM_ROUTER_KEY) { console.error("no model key"); process.exit(1); }
  const ask = AI.makeAsk(process.env);
  const out = [];
  for (const [i, c] of cases.entries()) {
    const req = F.request(B.createBot(c.setup).config, c.text);
    let raw = null;
    for (let a = 0; a < 3 && raw === null; a++) {
      try { raw = await ask(req.system, req.user); } catch (e) { await sleep(5000 * (a + 1)); }
    }
    out.push({ setup: c.setup, text: c.text, raw });
    if (i % 20 === 0) console.log(`${i + 1}/${cases.length}`);
    await sleep(Number(process.env.GAP_MS || 2500)); // stay under the free tier's requests per minute
  }
  fs.writeFileSync(path.join(__dirname, "depth.live.json"), JSON.stringify({ model: require("../core/models.json").groq_chat, at: new Date().toISOString(), answers: out }, null, 1));
  console.log(`saved ${out.length} answers, ${out.filter((x) => x.raw === null).length} failed`);
})();

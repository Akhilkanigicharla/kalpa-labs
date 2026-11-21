// A312: one short line to Akhil's private Telegram when a function fails. Same file in BotBhai
// (core/functions/_opsalert.js) and JobCard (lib/opsalert.cjs); a test keeps them identical.
// Privacy: the line holds only app, function, error kind, time (IST) and a count. Never the error
// message, customer name, phone number or chat text (DPDP; A221 rows 17/50/53).
// At most one alert per kind per hour: memory in this function copy, plus an optional shared
// `allow(key)` (BotBhai: Supabase rate_hit) so many copies don't each send one. Never throws.
// Env (Akhil sets them in Netlify, never in code): OPS_ALERT_BOT_TOKEN, OPS_ALERT_CHAT_ID. Missing → off.
const HOUR = 3600 * 1000;
let seen = new Map(); // kind -> { at, held }

const scrub = (s, max = 30) => String(s == null ? "" : s).replace(/[^A-Za-z0-9_ .-]/g, "").replace(/\d{3,}/g, "#").trim().slice(0, max) || "unknown";

function kindOf(err) {
  if (!err) return "error";
  if (err.name === "AbortError" || err.name === "TimeoutError") return "timeout";
  const st = Number(err.status || err.statusCode);
  if (st >= 100 && st < 600) return `http_${st}`;
  return "error";
}

const istTime = (ms) => new Date(ms + 330 * 60000).toISOString().slice(11, 16);

async function alertOps({ app, fn, kind, err } = {}, deps = {}) {
  try {
    const env = deps.env || process.env, now = deps.now || Date.now(), doFetch = deps.fetch || fetch;
    const token = env.OPS_ALERT_BOT_TOKEN, chat = env.OPS_ALERT_CHAT_ID;
    if (!token || !chat) return { sent: false, reason: "off" };
    const k = [scrub(app), scrub(fn), scrub(kind || kindOf(err))];
    const key = k.join("|"), last = seen.get(key);
    if (last && now - last.at < HOUR) { last.held++; return { sent: false, reason: "throttled" }; }
    if (deps.allow) {
      let ok = true;
      try { ok = (await deps.allow(`opsalert:${key}`)) !== false; } catch (e) { ok = true; } // shared limiter down: memory still caps it
      if (!ok) { seen.set(key, { at: now, held: 0 }); return { sent: false, reason: "throttled" }; }
    }
    const held = last ? last.held : 0;
    seen.set(key, { at: now, held: 0 });
    const text = `⚠️ ${k.join(" · ")} · ${istTime(now)} IST${held ? ` · +${held} more in the last hour` : ""}`;
    const res = await doFetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chat, text, disable_web_page_preview: true }),
      signal: AbortSignal.timeout(5000),
    });
    return res.ok ? { sent: true } : { sent: false, reason: `http_${res.status}` };
  } catch (e) {
    return { sent: false, reason: "send_failed" };
  }
}

module.exports = { alertOps, scrub, kindOf, _reset: () => { seen = new Map(); } };

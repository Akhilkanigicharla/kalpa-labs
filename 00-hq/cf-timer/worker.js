// Kalpa precise timer (Cloudflare Workers free plan): GitHub's own cron is "best effort" (only 8 of ~400
// keep-awake runs landed 4–6 Nov 2026). Cloudflare Cron Triggers fire on time (down to every minute).
// Free plan: 5 cron triggers per account, 10 ms CPU per run (waiting on fetch doesn't count), 100k requests/day.
// This worker does two light jobs and nothing else:
//   1. ping n8n /healthz every 5 min from 05:30 to 00:30 IST, so Render never puts it to sleep;
//   2. start chosen GitHub Actions workflows at their exact time (workflow_dispatch).
// Secrets (Akhil sets them in Cloudflare, never in code): GH_TOKEN (fine-grained, Actions: write on kalpa-labs only).

export const N8N_URL = "https://kalpa-n8n.onrender.com/healthz";
export const REPO = "Akhilkanigicharla/kalpa-labs";
// UTC cron → workflows to start. Keep in sync with wrangler.toml [triggers].
export const DISPATCH = {
  "30 15 * * *": ["daily-brief.yml"],   // 21:00 IST daily brief
  "20,50 * * * *": ["agents.yml"],       // A237: free agents every 30 min, on time
};

export function inN8nWindow(date) {          // 05:30–00:29 IST = 00:00–18:59 UTC
  return date.getUTCHours() <= 18;
}

export async function run(cron, now, env, fetchFn = fetch) {
  const done = [];
  if (cron === "*/5 * * * *" && inN8nWindow(now)) {
    const r = await fetchFn(N8N_URL, { method: "GET" });
    done.push(`n8n ${r.status}`);
  }
  for (const wf of DISPATCH[cron] || []) {
    if (!env.GH_TOKEN) { done.push(`skip ${wf} (no GH_TOKEN)`); continue; }
    const r = await fetchFn(`https://api.github.com/repos/${REPO}/actions/workflows/${wf}/dispatches`, {
      method: "POST",
      headers: { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "kalpa-cf-timer" },
      body: JSON.stringify({ ref: "main" }),
    });
    done.push(`${wf} ${r.status}`);
  }
  return done;
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(run(event.cron, new Date(event.scheduledTime), env).then((d) => console.log(event.cron, d.join("; "))));
  },
};

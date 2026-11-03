// F-11 check: 1M synthetic events through the handler (validation + hashing) with an in-memory store.
// Measures our CPU only; network and database time are not included.
import { handle, sha256Hex } from './ingest.js';
const N = Number(process.argv[2] || 1_000_000), B = 1000, KEY = 'lp_bench_' + 'x'.repeat(32);
const h = await sha256Hex(KEY); let stored = 0;
const store = { tenantForKeyHash: async (x) => (x === h ? 't' : null), insertEvents: async (r) => { stored += r.length; } };
const now = Date.now();
const batch = Array.from({ length: B }, (_, i) => ({ ts: new Date(now - i * 1000).toISOString(), provider: 'openai',
  model: i % 2 ? 'gpt-4.1-mini' : 'claude-sonnet-4-5', input_tokens: 1000 + i, output_tokens: 200,
  customer: 'c_' + (i % 97).toString(16).padStart(16, '0'), feature: 'f' + (i % 5) }));
const body = JSON.stringify({ events: batch });
const t0 = performance.now();
for (let i = 0; i < N / B; i++) {
  const r = await handle(new Request('https://x/v1/events', { method: 'POST', headers: { authorization: 'Bearer ' + KEY }, body }), store, now);
  if (r.status !== 202) throw new Error('status ' + r.status);
}
const s = (performance.now() - t0) / 1000;
console.log(JSON.stringify({ events: stored, seconds: +s.toFixed(1), per_batch_ms: +(s * 1000 / (N / B)).toFixed(2), under_10_min: s < 600 }));
if (stored !== N || s >= 600) process.exit(1);

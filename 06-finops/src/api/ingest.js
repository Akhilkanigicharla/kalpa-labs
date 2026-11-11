// Ledger Peaks ingest API (F-11): POST /v1/events, batched, one key per tenant.
// Web-standard fetch handler, so the same file runs as a Supabase Edge Function (Deno),
// a Cloudflare Worker or under Node 18+. No dependencies.
//
// Metadata only: token counts, model, provider, feature tag and an already-hashed
// customer id (c_ + 16 hex, made with the client's own salt). Prompt or completion
// text and raw customer ids are refused, never stored.
// Cost is NOT trusted from the client: rows land with cost_paise = null and the
// price pass (price_pass.py, genai-prices + FBIL rate) fills it in.

export const MAX_BATCH = 1000;
export const MAX_BODY_BYTES = 1_000_000;
const HASH_RE = /^c_[0-9a-f]{16}$/;
const KEY_RE = /^lp_[A-Za-z0-9_-]{24,64}$/;
const EVENT_ID_RE = /^[A-Za-z0-9._:-]{8,80}$/;   // optional; makes a retried batch safe (db: unique per tenant)
const TEXT_KEYS = ['prompt', 'completion', 'messages', 'input', 'output', 'content', 'response',
  'gen_ai.prompt', 'gen_ai.completion', 'gen_ai.input.messages', 'gen_ai.output.messages'];

// our field <- accepted names (snake_case first, then OTel gen_ai.* / ledger.* attributes)
const FIELDS = {
  ts: ['ts', 'ledger.ts', 'timestamp'],
  provider: ['provider', 'gen_ai.provider.name', 'gen_ai.system'],
  model: ['model', 'gen_ai.request.model', 'gen_ai.response.model'],
  input_tokens: ['input_tokens', 'gen_ai.usage.input_tokens', 'gen_ai.usage.prompt_tokens'],
  output_tokens: ['output_tokens', 'gen_ai.usage.output_tokens', 'gen_ai.usage.completion_tokens'],
  cache_read_tokens: ['cache_read_tokens', 'gen_ai.usage.cache_read.input_tokens'],
  cache_write_tokens: ['cache_write_tokens', 'gen_ai.usage.cache_creation.input_tokens'],
  reasoning_tokens: ['reasoning_tokens', 'gen_ai.usage.reasoning.output_tokens'],
  requests: ['requests', 'ledger.requests'],
  customer_id_hash: ['customer_id_hash', 'customer', 'ledger.customer_id_hash'],
  feature: ['feature', 'ledger.feature'],
  batch: ['batch', 'ledger.batch'],
  served_from_cache: ['served_from_cache', 'ledger.served_from_cache'],
  event_id: ['event_id', 'ledger.event_id'],
};
const INTS = ['input_tokens', 'output_tokens', 'cache_read_tokens', 'cache_write_tokens', 'reasoning_tokens'];

function pick(e, names) {
  for (const n of names) if (e[n] !== undefined && e[n] !== null) return e[n];
  return undefined;
}

function str(v, field, min, max) {
  if (typeof v !== 'string') throw new Error(`${field} must be text`);
  const s = v.trim();
  if (s.length < min || s.length > max) throw new Error(`${field} must be ${min}-${max} characters`);
  return s;
}

/** One client event -> one usage_event row (without tenant_id). Throws Error with a plain reason. */
export function normalizeEvent(e, now = Date.now()) {
  if (!e || typeof e !== 'object' || Array.isArray(e)) throw new Error('event must be an object');
  for (const k of TEXT_KEYS) if (k in e) throw new Error(`"${k}" looks like prompt/response text; send counts only`);
  const row = {};
  const tsRaw = pick(e, FIELDS.ts);
  const t = typeof tsRaw === 'number' ? tsRaw * (tsRaw < 1e12 ? 1000 : 1) : Date.parse(tsRaw);
  if (!Number.isFinite(t)) throw new Error('ts must be an ISO time or epoch seconds');
  if (t > now + 10 * 60_000) throw new Error('ts is in the future');
  if (t < now - 400 * 86_400_000) throw new Error('ts is older than 400 days');
  row.ts = new Date(t).toISOString();
  row.provider = str(pick(e, FIELDS.provider), 'provider', 1, 40).toLowerCase();
  row.model = str(pick(e, FIELDS.model), 'model', 1, 120);
  for (const f of INTS) {
    const v = pick(e, FIELDS[f]) ?? 0;
    if (!Number.isSafeInteger(v) || v < 0) throw new Error(`${f} must be a whole number >= 0`);
    row[f] = v;
  }
  if (row.reasoning_tokens > row.output_tokens) throw new Error('reasoning_tokens cannot exceed output_tokens');
  if (row.cache_read_tokens + row.cache_write_tokens > row.input_tokens)
    throw new Error('input_tokens must include cache read + write tokens');
  const req = pick(e, FIELDS.requests) ?? 1;
  if (!Number.isSafeInteger(req) || req < 1 || req > 2_147_483_647) throw new Error('requests must be a whole number >= 1');
  row.requests = req;
  const cust = pick(e, FIELDS.customer_id_hash);
  if (cust !== undefined && !HASH_RE.test(cust)) throw new Error('customer must be hashed (c_ + 16 hex); never send raw ids');
  row.customer_id_hash = cust ?? null;
  const feat = pick(e, FIELDS.feature);
  row.feature = feat === undefined || feat === '' ? null : str(feat, 'feature', 1, 80);
  for (const f of ['batch', 'served_from_cache']) {
    const v = pick(e, FIELDS[f]) ?? false;
    if (typeof v !== 'boolean') throw new Error(`${f} must be true or false`);
    row[f] = v;
  }
  const eid = pick(e, FIELDS.event_id);
  if (eid !== undefined && (typeof eid !== 'string' || !EVENT_ID_RE.test(eid))) throw new Error('event_id must be 8-80 letters, digits or . _ : -');
  row.event_id = eid ?? null;
  row.cost_paise = null;
  row.source = 'api';
  return row;
}

export async function sha256Hex(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

const json = (status, body) => new Response(JSON.stringify(body), {
  status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });

/**
 * store = { tenantForKeyHash(hex) -> tenant_id | null, insertEvents(rows) -> void }
 * Response: 202 {accepted, rejected:[{index, error}]}. A batch with any bad event is stored
 * without the bad ones; the caller sees exactly which were dropped and why.
 */
export async function handle(request, store, now = Date.now()) {
  const url = new URL(request.url);
  if (url.pathname !== '/v1/events') return json(404, { error: 'not found' });
  if (request.method !== 'POST') return json(405, { error: 'use POST' });
  const auth = request.headers.get('authorization') || '';
  const key = auth.startsWith('Bearer ') ? auth.slice(7).trim() : '';
  if (!KEY_RE.test(key)) return json(401, { error: 'missing or malformed API key' });
  let tenant;
  try { tenant = await store.tenantForKeyHash(await sha256Hex(key)); }
  catch { return json(503, { error: 'storage unavailable, retry later' }); }   // never leak the internal error
  if (!tenant) return json(401, { error: 'unknown or revoked API key' });
  const len = Number(request.headers.get('content-length') || 0);
  if (len > MAX_BODY_BYTES) return json(413, { error: `body over ${MAX_BODY_BYTES} bytes` });
  const text = await request.text();
  if (text.length > MAX_BODY_BYTES) return json(413, { error: `body over ${MAX_BODY_BYTES} bytes` });
  let body;
  try { body = JSON.parse(text); } catch { return json(400, { error: 'body is not JSON' }); }
  const events = Array.isArray(body) ? body : body?.events;
  if (!Array.isArray(events) || events.length === 0) return json(400, { error: 'send {"events": [...]}' });
  if (events.length > MAX_BATCH) return json(413, { error: `at most ${MAX_BATCH} events per request` });
  const rows = [], rejected = [];
  const ids = new Set();
  events.forEach((e, index) => {
    try {
      const row = normalizeEvent(e, now);
      if (row.event_id && ids.has(row.event_id)) throw new Error('duplicate event_id in this batch');
      if (row.event_id) ids.add(row.event_id);
      rows.push({ tenant_id: tenant, ...row });
    } catch (err) { rejected.push({ index, error: err.message }); }
  });
  if (rows.length) {
    try { await store.insertEvents(rows); }
    catch { return json(503, { error: 'storage unavailable, retry later' }); }
  }
  return json(202, { accepted: rows.length, rejected });
}

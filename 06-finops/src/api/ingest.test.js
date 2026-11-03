import { test } from 'node:test';
import assert from 'node:assert/strict';
import { handle, normalizeEvent, sha256Hex, MAX_BATCH } from './ingest.js';
import { supabaseStore } from './supabase-store.js';

const NOW = Date.parse('2026-11-03T06:00:00Z');
const KEY = 'lp_test_' + 'a'.repeat(32);
const T = '10000000-0000-0000-0000-00000000000a';
const ok = { ts: '2026-11-03T05:00:00Z', provider: 'OpenAI', model: 'gpt-4.1-mini', input_tokens: 1200,
  output_tokens: 300, cache_read_tokens: 200, customer: 'c_0123456789abcdef', feature: 'summary' };

async function fakeStore() {
  const h = await sha256Hex(KEY); const rows = [];
  return { rows, tenantForKeyHash: async (x) => (x === h ? T : null), insertEvents: async (r) => { rows.push(...r); } };
}
const req = (body, key = KEY, method = 'POST', path = '/v1/events') => new Request('https://x.test' + path, {
  method, headers: { authorization: `Bearer ${key}`, 'content-type': 'application/json' },
  body: method === 'POST' ? JSON.stringify(body) : undefined });

test('accepts a batch and tags tenant, source api, unpriced', async () => {
  const s = await fakeStore();
  const r = await handle(req({ events: [ok, ok] }), s, NOW);
  assert.equal(r.status, 202);
  assert.deepEqual(await r.json(), { accepted: 2, rejected: [] });
  assert.equal(s.rows[0].tenant_id, T); assert.equal(s.rows[0].provider, 'openai');
  assert.equal(s.rows[0].cost_paise, null); assert.equal(s.rows[0].source, 'api');
});
test('OTel gen_ai attribute names map to the same row', () => {
  const o = normalizeEvent({ 'ledger.ts': ok.ts, 'gen_ai.provider.name': 'openai', 'gen_ai.request.model': ok.model,
    'gen_ai.usage.input_tokens': 1200, 'gen_ai.usage.output_tokens': 300,
    'gen_ai.usage.cache_read.input_tokens': 200, 'ledger.customer_id_hash': ok.customer, 'ledger.feature': 'summary' }, NOW);
  assert.deepEqual(o, normalizeEvent(ok, NOW));
});
test('wrong, missing and revoked keys get 401; unknown path 404; GET 405', async () => {
  const s = await fakeStore();
  assert.equal((await handle(req({ events: [ok] }, 'lp_' + 'b'.repeat(30)), s, NOW)).status, 401);
  assert.equal((await handle(req({ events: [ok] }, 'nope'), s, NOW)).status, 401);
  assert.equal((await handle(req({}, KEY, 'POST', '/v1/other'), s, NOW)).status, 404);
  assert.equal((await handle(req(null, KEY, 'GET'), s, NOW)).status, 405);
  assert.equal(s.rows.length, 0);
});
test('bad events are dropped with reasons, good ones kept', async () => {
  const s = await fakeStore();
  const bad = [
    { ...ok, customer: '9848012345' },             // raw phone number
    { ...ok, prompt: 'hello' },                    // text
    { ...ok, input_tokens: -1 },
    { ...ok, output_tokens: 10, reasoning_tokens: 11 },
    { ...ok, cache_read_tokens: 5000 },
    { ...ok, ts: '2027-01-01T00:00:00Z' },
    { ...ok, model: '' },
    { ...ok, batch: 'yes' },
  ];
  const r = await (await handle(req({ events: [ok, ...bad] }), s, NOW)).json();
  assert.equal(r.accepted, 1); assert.equal(r.rejected.length, bad.length);
  assert.match(r.rejected[0].error, /hashed/); assert.match(r.rejected[1].error, /text/);
  assert.ok(!JSON.stringify(s.rows).includes('9848012345'));
});
test('limits: empty, not JSON, too many events, too big', async () => {
  const s = await fakeStore();
  assert.equal((await handle(req({ events: [] }), s, NOW)).status, 400);
  const raw = new Request('https://x.test/v1/events', { method: 'POST', headers: { authorization: `Bearer ${KEY}` }, body: '{' });
  assert.equal((await handle(raw, s, NOW)).status, 400);
  assert.equal((await handle(req({ events: Array(MAX_BATCH + 1).fill(ok) }), s, NOW)).status, 413);
  assert.equal((await handle(req({ events: [{ ...ok, feature: 'x'.repeat(1_100_000) }] }), s, NOW)).status, 413);
});
test('storage failure is a 503 so clients retry', async () => {
  const s = await fakeStore(); s.insertEvents = async () => { throw new Error('down'); };
  assert.equal((await handle(req({ events: [ok] }), s, NOW)).status, 503);
});
test('epoch seconds accepted', () => {
  assert.equal(normalizeEvent({ ...ok, ts: NOW / 1000 }, NOW).ts, '2026-11-03T06:00:00.000Z');
});
test('supabase store: looks up active keys, caches, inserts with service key', async () => {
  const calls = [];
  const fetchFn = async (u, o) => { calls.push([u, o]); return new Response(u.includes('api_key') ? JSON.stringify([{ tenant_id: T }]) : '', { status: u.includes('api_key') ? 200 : 201 }); };
  const st = supabaseStore({ url: 'https://p.supabase.co/', serviceKey: 'svc', fetchFn });
  const h = await sha256Hex(KEY);
  assert.equal(await st.tenantForKeyHash(h), T); await st.tenantForKeyHash(h);
  assert.equal(calls.length, 1); assert.match(calls[0][0], /revoked_at=is\.null/);
  assert.equal(await st.tenantForKeyHash('not-hex'), null);
  await st.insertEvents([{ a: 1 }]);
  assert.equal(calls[1][0], 'https://p.supabase.co/rest/v1/usage_event');
  assert.equal(calls[1][1].headers.authorization, 'Bearer svc');
  assert.throws(() => supabaseStore({ url: '', serviceKey: '' }));
});

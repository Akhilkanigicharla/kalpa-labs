// A203: free X-ray intake handler. Run: cd 06-finops/src/api && node --test
import test from 'node:test';
import assert from 'node:assert/strict';
import { handleIntake, checkFields, scanExport, makeLimiter, MAX_BYTES, KEEP_DAYS } from './intake.js';

const NOW = Date.parse('2026-11-13T00:00:00Z');
const CSV = 'timestamp,model,input_tokens,output_tokens,feature,customer_id_hash\n2026-10-12T05:00:00Z,gpt-4o,100,20,support,c_d63f6363743af20e\n';

function form(over = {}) {
  const f = new FormData();
  const v = { company: 'Chaiwala AI', email: 'ops@chaiwala.ai', consent: 'yes', website: '', ...over };
  for (const [k, x] of Object.entries(v)) if (x !== null) f.set(k, x);
  if (over.file !== null) f.set('file', over.file || new File([CSV], 'usage.csv', { type: 'text/csv' }));
  return f;
}
const req = (body, init = {}) => new Request('https://x.test/api/xray-intake', { method: 'POST', body, ...init,
  headers: { 'x-forwarded-for': '1.2.3.4', ...(init.headers || {}) } });
const memStore = () => { const rows = []; return { rows, save: async (r) => { rows.push(r); return 'xr_' + rows.length; } }; };

test('valid upload is saved with a 14-day delete date and only counts in the reply', async () => {
  const s = memStore();
  const r = await handleIntake(req(form()), s, { now: NOW, limiter: makeLimiter() });
  assert.equal(r.status, 202);
  const body = await r.json();
  assert.deepEqual(body, { ok: true, id: 'xr_1' });
  assert.equal(s.rows[0].email, 'ops@chaiwala.ai');
  assert.equal(s.rows[0].delete_after, new Date(NOW + KEEP_DAYS * 864e5).toISOString());
  assert.equal(s.rows[0].consent_at, new Date(NOW).toISOString());
  assert.match(s.rows[0].sha256, /^[0-9a-f]{64}$/);
  assert.equal(r.headers.get('cache-control'), 'no-store');
});

test('each field gets its own plain error', () => {
  const e = checkFields({ company: ' ', email: 'not-an-email', consent: '' }, null);
  assert.deepEqual(Object.keys(e).sort(), ['company', 'consent', 'email', 'file']);
  assert.match(checkFields({ company: 'A', email: 'a@gmail.com', consent: 'yes' }, null).email, /work email/);
  const long = checkFields({ company: 'x'.repeat(121), email: 'a@b.co', consent: 'yes' }, null);
  assert.ok(long.company);
  assert.ok(checkFields({ company: 'Acme\u0000', email: 'a@b.co', consent: 'yes' }, null).company, 'control chars refused');
  assert.equal(checkFields({ company: 'చాయ్‌వాలా AI 🍵', email: 'a@acme.in', consent: 'yes' },
    new File([CSV], 'u.json')).company, undefined, 'Telugu and emoji names are fine');
});

test('file rules: type, empty, too big', () => {
  const ok = { company: 'Acme', email: 'a@acme.in', consent: 'yes' };
  assert.match(checkFields(ok, new File([CSV], 'usage.xlsx')).file, /CSV or JSON/);
  assert.match(checkFields(ok, new File([], 'usage.csv')).file, /empty/);
  assert.match(checkFields(ok, new File([new Uint8Array(MAX_BYTES + 1)], 'usage.csv')).file, /5 MB/);
});

test('exports with prompts, replies or raw customer emails/phones are refused', () => {
  assert.match(scanExport('timestamp,model,prompt,input_tokens\n1,2,hi,3\n'), /prompt/);
  assert.match(scanExport('[{"model":"gpt-4o","messages":[{"role":"user"}]}]'), /messages/);
  assert.match(scanExport('model,customer\ngpt-4o,ravi@shop.in\n'), /email/);
  assert.match(scanExport('model,customer\ngpt-4o,+91 98480 22338\n'), /phone/);
  assert.equal(scanExport(CSV), null);
  assert.equal(scanExport('model,input_tokens\ngpt-4o,1234567890123\n'), null, 'big token counts are not phones');
});

test('bad export comes back as a file error, nothing stored', async () => {
  const s = memStore();
  const r = await handleIntake(req(form({ file: new File(['model,completion\na,b\n'], 'u.csv') })), s, { now: NOW, limiter: makeLimiter() });
  assert.equal(r.status, 422);
  assert.match((await r.json()).errors.file, /completion/);
  assert.equal(s.rows.length, 0);
});

test('honeypot, wrong method, wrong type, oversized body', async () => {
  const s = memStore(), o = { now: NOW, limiter: makeLimiter() };
  assert.equal((await handleIntake(req(form({ website: 'spam.biz' })), s, o)).status, 400);
  assert.equal((await handleIntake(new Request('https://x.test/', { method: 'GET' }), s, o)).status, 405);
  assert.equal((await handleIntake(req('{}', { headers: { 'content-type': 'application/json' } }), s, o)).status, 415);
  assert.equal((await handleIntake(req(form(), { headers: { 'content-length': String(MAX_BYTES * 2) } }), s, o)).status, 413);
  assert.equal(s.rows.length, 0);
});

test('rate limit: 5 an hour per address, then 429 with Retry-After', async () => {
  const s = memStore(), o = { now: NOW, limiter: makeLimiter() };
  for (let i = 0; i < 5; i++) assert.equal((await handleIntake(req(form()), s, o)).status, 202);
  const r = await handleIntake(req(form()), s, o);
  assert.equal(r.status, 429);
  assert.ok(Number(r.headers.get('retry-after')) > 0);
  assert.equal((await handleIntake(req(form()), s, { ...o, now: NOW + 3601e3 })).status, 202, 'window resets');
});

test('store down or slow → 503, never a fake success', async () => {
  const o = { now: NOW, limiter: makeLimiter(), timeoutMs: 20 };
  const down = { save: async () => { throw new Error('db down'); } };
  const slow = { save: () => new Promise(() => {}) };
  const a = await handleIntake(req(form()), down, o);
  const b = await handleIntake(req(form()), slow, o);
  assert.equal(a.status, 503); assert.equal(b.status, 503);
  assert.doesNotMatch(JSON.stringify(await a.json()), /db down/, 'internal error text never leaks');
});

test('Supabase store writes export_text and returns the id', async () => {
  const { supabaseStore } = await import('./supabase-store.js');
  let sent;
  const fetchFn = async (url, init) => { sent = { url, init }; return new Response('[{"id":"u-1"}]', { status: 201 }); };
  const s = supabaseStore({ url: 'https://p.supabase.co/', serviceKey: 'k', fetchFn });
  assert.equal(await s.save({ company: 'Acme', text: 'a,b' }), 'u-1');
  assert.match(sent.url, /\/rest\/v1\/xray_intake\?select=id$/);
  assert.deepEqual(JSON.parse(sent.init.body), { company: 'Acme', export_text: 'a,b' });
  const bad = supabaseStore({ url: 'https://p', serviceKey: 'k', fetchFn: async () => new Response('', { status: 500 }) });
  await assert.rejects(bad.save({ text: '' }), /intake 500/);
});

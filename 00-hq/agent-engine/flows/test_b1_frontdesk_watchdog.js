// A242 b1 flow test: runs the Code nodes of b1-frontdesk-watchdog.json with fake n8n inputs. node test_b1_frontdesk_watchdog.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const raw = fs.readFileSync(path.join(__dirname, 'b1-frontdesk-watchdog.json'), 'utf8');
const wf = JSON.parse(raw);
const node = (n) => wf.nodes.find((x) => x.name === n);
let store = {};
const settings = new Function(node('Settings').parameters.jsCode)()[0].json;
const run = (data, cfg = { supabase: 'https://abcd.supabase.co', waitMin: 20 }) => new Function('$', '$getWorkflowStaticData', node('Find waiting chats').parameters.jsCode)(
  (n) => ({ first: () => ({ json: cfg }), all: () => { if (!(n in data)) throw new Error('no node'); return data[n].map((json) => ({ json })); } }),
  () => store).map((i) => i.json.text);
const ago = (min) => new Date(Date.now() - min * 60000).toISOString();
const later = (min) => new Date(Date.now() + min * 60000).toISOString();
const A = 'c-aaa', B = 'c-bbb';
const clients = [{ id: A, name: 'Glow Salon' }, { id: B, name: '<b>Evil</b>‮ Spa' }];
const ses = (client_id, contact, inMin, extra = {}) => ({ client_id, contact, status: 'human', human_until: later(60), last_inbound_at: ago(inMin), ...extra });

// wiring: schedule only, inactive, no webhook, read-only GETs, once per run, retries + timeouts, secrets only in credentials
assert.strictEqual(wf.active, false);
assert(!wf.nodes.some((n) => /webhook|formTrigger|chatTrigger/i.test(n.type)), 'no public URL');
const https = wf.nodes.filter((n) => n.type.endsWith('httpRequest'));
assert.strictEqual(https.length, 3);
assert(https.every((n) => !n.parameters.method && n.executeOnce && n.retryOnFail && n.parameters.options.timeout === 10000 && n.onError === 'continueRegularOutput'));
assert(https.every((n) => !/body|text|state/.test(n.parameters.url.split('select=')[1])), 'never reads message text or bot state');
assert(!/eyJ|sk-|service_role|apikey/i.test(raw), 'no keys in the file');
assert.deepStrictEqual(settings, { supabase: 'https://YOUR-PROJECT.supabase.co', waitMin: 20 });
const chain = Object.entries(wf.connections).map(([a, c]) => a + '>' + c.main[0][0].node).join(',');
assert.strictEqual(chain, 'Every 15 min>Settings,Settings>Read handed-over chats,Read handed-over chats>Read staff replies,Read staff replies>Read businesses,Read businesses>Find waiting chats,Find waiting chats>Tell Akhil (private)');

// placeholder URL: one setup nudge per 6 h, never a request to a fake host
assert.match(run({}, settings)[0], /set the Supabase project URL/);
assert.strictEqual(run({}, settings).length, 0);
store = {};
assert.match(run({}, { supabase: 'https://evil.example.com/x' })[0], /set the Supabase project URL/, 'only *.supabase.co hosts');
store = {};

// normal: 4 handed-over chats; one answered by staff, one too fresh, one late, one web chat late
const data = {
  'Read handed-over chats': [ses(A, '919876543210', 45), ses(A, '919800000001', 50), ses(A, '919800000002', 5), ses(B, 'web_x1y2', 30),
    ses(A, '919800000003', 90, { human_until: ago(1) }), ses(A, '919800000004', 30, { status: 'bot' })],
  'Read staff replies': [{ client_id: A, contact: '919800000001', created_at: ago(10) }, { client_id: A, contact: '919876543210', created_at: ago(60) }],
  'Read businesses': clients,
};
let t = run(data);
assert.strictEqual(t.length, 1);
assert.match(t[0], /2 customers waiting/);
assert(t[0].includes('Glow Salon · ••••3210 · waited 45 min') && t[0].indexOf('3210') < t[0].indexOf('web chat'), t[0]);
assert(t[0].includes('&lt;b&gt;Evil&lt;/b&gt; Spa · ••••x1y2 (web chat)') && !t[0].includes('‮'), 'business name escaped, bidi stripped');
assert(!/9876543210|0001|0002|0003|0004/.test(t[0]), 'answered, fresh, expired and bot chats left out; phones masked');

// dedupe: same state 15 min later = silence; a new customer message = a new alert
assert.strictEqual(run(data).length, 0);
data['Read handed-over chats'][0].last_inbound_at = ago(21);
assert.match(run(data)[0], /1 customer waiting.*\n.*••••3210 · waited 21 min/);

// WhatsApp 24 h window: closing (< 2 h left) and closed (template only); escalation to "closing" alerts again
store = {};
t = run({ ...data, 'Read handed-over chats': [ses(A, '919811111111', 23 * 60), ses(A, '919822222222', 25 * 60, { human_until: later(600) })] })[0];
assert(t.includes('🔴') && t.includes('only an approved template') && t.includes('🟠') && /next 60 min/.test(t), t);
assert(t.indexOf('🔴') < t.indexOf('🟠'), 'longest wait first');

// hostile and broken rows are skipped, no crash
store = {};
const bad = [null, 'x', 5, { client_id: A, contact: '../../etc', status: 'human', last_inbound_at: ago(90) }, { client_id: A, contact: '9198', status: 'human', last_inbound_at: 'not a date' },
  { client_id: A, contact: '919833333333', status: 'human', last_inbound_at: later(90) }, { client_id: 7, contact: '919844444444', status: 'human', last_inbound_at: ago(90) }];
assert.strictEqual(run({ ...data, 'Read handed-over chats': bad, 'Read staff replies': [null, { contact: 1 }] }).length, 0);

// cap: 25 waiting → 10 lines + "15 more"
store = {};
const many = Array.from({ length: 25 }, (_, i) => ses(A, '91990000' + String(1000 + i), 30 + i));
t = run({ ...data, 'Read handed-over chats': many, 'Read staff replies': [] })[0];
assert.strictEqual((t.match(/🟡/g) || []).length, 10);
assert(t.includes('25 customers') && t.includes('15 more'));

// Supabase down or key wrong: one warning per 6 h, not every 15 min
store = {};
const down = { ...data, 'Read handed-over chats': [{ error: { message: '401' } }] };
assert.match(run(down)[0], /could not read Supabase/);
assert.strictEqual(run(down).length, 0);
assert.match((store = {}, run({ 'Read businesses': clients }))[0], /could not read/);

// old dedupe keys are pruned after 3 days
store = { seen: { old: Date.now() - 4 * 864e5, fresh: Date.now() } };
run({ ...data, 'Read handed-over chats': [] });
assert.deepStrictEqual(Object.keys(store.seen), ['fresh']);

console.log('b1 front-desk watchdog flow: PASS (wiring, setup nudge, late/closing/closed, masking, escaping, dedupe, hostile rows, cap, outage, pruning)');

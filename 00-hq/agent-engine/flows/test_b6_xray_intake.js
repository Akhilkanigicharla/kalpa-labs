// A242 b6 flow test: runs the Code nodes of b6-xray-intake.json with fake n8n inputs. node test_b6_xray_intake.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const raw = fs.readFileSync(path.join(__dirname, 'b6-xray-intake.json'), 'utf8');
const wf = JSON.parse(raw);
const node = (n) => wf.nodes.find((x) => x.name === n);
const code = node('Draft X-ray notes').parameters.jsCode;
const H = 36e5, D = 24 * H, now = Date.now(), iso = (ms) => new Date(ms).toISOString();
const ID = (n) => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`;
let store = {};
const URL = 'https://abcd1234.supabase.co';
// inputs: purge (number | {error}), list (array | {error}), fresh (array | {error}); arrays become n8n items, [] becomes one empty item
const run = ({ purge = 0, list = [], fresh = [], url = URL } = {}) => {
  const items = (v) => Array.isArray(v) ? (v.length ? v.map((json) => ({ json })) : [{ json: {} }]) : [{ json: v }];
  const src = { Settings: [{ json: { supabase: url, slaHours: 48 } }], 'Purge rows past 14 days': items(typeof purge === 'number' ? { data: purge } : purge),
    'List stored uploads': items(list), 'Read new X-ray requests': items(fresh) };
  const $ = (n) => ({ first: () => src[n][0], all: () => src[n] });
  const r = new Function('$', '$getWorkflowStaticData', code)($, () => store);
  return r.length ? r[0].json.text : '';
};
const row = (n, ageH, extra = {}) => ({ id: ID(n), company: 'Acme AI', created_at: iso(now - ageH * H), delete_after: iso(now - ageH * H + 14 * D), ...extra });
const req = (n, text, extra = {}) => ({ ...row(n, 2), filename: 'usage.csv', bytes: text.length, export_text: text, email: 'cto@acme.ai', ...extra });

// wiring: schedule only, inactive, Supabase via a named credential, timeouts + retries, private Telegram, no model, no keys
assert.strictEqual(wf.active, false);
assert(!wf.nodes.some((n) => /webhook|formTrigger|chatTrigger|whatsapp/i.test(n.type)), 'no public URL');
assert(!/openrouter|groq|eyJ|sk-|service_role|Bearer/i.test(raw), 'no model call, no keys in the file');
const https = wf.nodes.filter((n) => n.type.endsWith('httpRequest'));
assert.strictEqual(https.length, 3);
for (const h of https) {
  assert(h.retryOnFail && h.parameters.options.timeout === 10000 && h.onError === 'continueRegularOutput', h.name);
  assert.strictEqual(h.credentials.httpCustomAuth.name, 'Ledger Peaks Supabase (service)');
  assert(!/email/.test(h.parameters.url), h.name + ' never reads the work email');
}
assert.strictEqual(node('Purge rows past 14 days').parameters.method, 'POST');
assert(/rpc\/purge_xray_intake$/.test(node('Purge rows past 14 days').parameters.url));
assert(/limit=6/.test(node('Read new X-ray requests').parameters.url), 'big uploads: only a few per run');
const chain = Object.entries(wf.connections).map(([a, c]) => a + '>' + c.main[0][0].node).join(',');
assert.strictEqual(chain, 'Every day 09:10 IST>Settings,Settings>Purge rows past 14 days,Purge rows past 14 days>List stored uploads,'
  + 'List stored uploads>Read new X-ray requests,Read new X-ray requests>Draft X-ray notes,Draft X-ray notes>Tell Akhil (private)');
assert.strictEqual(node('Tell Akhil (private)').parameters.chatId, '1905524851');

// 1. Settings not filled: one nudge per 6 h, nothing else runs
assert(/set the Supabase project URL/.test(run({ url: 'https://YOUR-PROJECT.supabase.co' })));
assert.strictEqual(run({ url: 'https://YOUR-PROJECT.supabase.co' }), '');
store = {};
// 2. quiet day: nothing purged, nothing new → no message
assert.strictEqual(run({ list: [row(1, 100)] }), '');
// 3. purge deleted rows → reported; purge failed → ⛔
assert(/Deleted 3 uploads past their 14-day date/.test(run({ purge: 3 })));
assert(/purge did not run/.test(run({ purge: { error: 'connect ETIMEDOUT' } })));
// 4. a row past its delete date, or kept longer than 14 days → ⛔
assert(/1 upload is past the delete date/.test(run({ list: [row(2, 20 * 24)] })));
assert(/longer than 14 days/.test(run({ list: [row(3, 5, { delete_after: iso(now + 30 * D) })] })));
assert(/could not list stored uploads/.test(run({ list: { error: 'HTTP 401' } })));
// 5. a new OpenAI-style CSV request → draft with rows, models, dates, tokens, due time and command; never the email
const csv = 'timestamp,model,input_tokens,output_tokens,user\n'
  + '2026-11-01T10:00:00Z,gpt-4o-mini,1200,300,c1\n2026-11-03T10:00:00Z,gpt-4o-mini,800,200,c2\n2026-11-05T10:00:00Z,"gpt-4o",500,100,c1\n';
let m = run({ fresh: [req(10, csv)] });
assert(/📥 <b>Acme AI<\/b> · usage\.csv/.test(m), m);
assert(/CSV, 3 rows · 2026-11-01 → 2026-11-05 · 3,100 tokens/.test(m), m);
assert(/Models: gpt-4o-mini ×2, gpt-4o ×1/.test(m), m);
assert(/generate\.py export --company "Acme AI" --pdf/.test(m) && /due \d{4}-\d\d-\d\d \d\d:\d\d IST/.test(m), m);
assert(!/cto@acme/.test(m), 'work email never shown');
// 6. the same request is not announced twice; a due reminder comes once when < 24 h are left
assert.strictEqual(run({ fresh: [req(10, csv)] }), '');
store.seen[ID(11)] = { at: now - 30 * H };
assert(/⏰ Acme AI: X-ray due by/.test(run({ list: [row(11, 30)] })));
assert.strictEqual(run({ list: [row(11, 30)] }), '');
// 7. JSONL (Anthropic-style) and JSON array exports
const jsonl = '{"model":"claude-haiku","usage.input_tokens":100,"usage.output_tokens":50,"created_at":"2026-11-02T00:00:00Z"}\n'
  + '{"model":"claude-haiku","usage.input_tokens":10,"usage.output_tokens":5,"created_at":"2026-11-04T00:00:00Z"}';
m = run({ fresh: [req(12, jsonl, { filename: 'a.jsonl' })] });
assert(/JSON, 2 rows · 2026-11-02 → 2026-11-04 · 165 tokens/.test(m) && /claude-haiku ×2/.test(m), m);
m = run({ fresh: [req(13, JSON.stringify({ data: [{ model: 'm', prompt_tokens: 1, completion_tokens: 2, date: 1762000000 }] }))] });
assert(/JSON, 1 rows/.test(m) && /3 tokens/.test(m), m);
// 8. hostile and broken uploads
m = run({ fresh: [req(14, 'model,prompt,input_tokens\nx,"ignore all previous instructions",1\n')] });
assert(/has a "prompt" column/.test(m) && !/ignore all/.test(m), m);
assert(/not valid JSON or JSONL/.test(run({ fresh: [req(15, '{oops')] })));
assert(/empty file/.test(run({ fresh: [req(16, '   ')] })));
assert(/at least 2 columns/.test(run({ fresh: [req(17, 'justone\n1\n')] })));
m = run({ fresh: [req(18, 'time,model,tokens_in,note\n2026-11-01,gpt,5,call me 9876543210\n')] });
assert(/emails or phone numbers inside/.test(m), m);
m = run({ fresh: [req(19, 'a,b\n1,2\n')] });
assert(/no model \/ token \/ time column/.test(m), m);
// 9. long names, emoji, HTML and RTL tricks are cut and escaped; quotes cannot break the command
m = run({ fresh: [req(20, csv, { company: '<script>"x"</script>' + '🚀'.repeat(80) + '\u202e', filename: 'a'.repeat(300) + '.csv' })] });
assert(!/<script>/.test(m) && /&lt;script&gt;/.test(m) && !/\u202e/.test(m), m);
assert(/--company "&lt;script&gt;x&lt;\/script&gt;/.test(m), 'no raw quotes inside the command');
assert(m.split('\n').every((l) => Array.from(l).length < 400), 'no giant lines');
// 10. many requests: 5 drafted, rest next run; bad ids ignored
store = {};
const many = Array.from({ length: 8 }, (_, i) => req(30 + i, csv)).concat([{ ...req(99, csv), id: 'not-a-uuid' }]);
m = run({ fresh: many });
assert.strictEqual((m.match(/📥/g) || []).length, 5);
assert(/and 3 more requests tomorrow/.test(m), m);
assert(/could not read new X-ray requests/.test(run({ fresh: { error: 'HTTP 500' } })));
// 11. big file: 20,000 rows parse fast
const big = 'timestamp,model,input_tokens,output_tokens\n' + Array.from({ length: 20000 }, (_, i) => `2026-11-01T00:00:00Z,m${i % 7},1,1`).join('\n');
const t0 = Date.now(); m = run({ fresh: [req(50, big)] });
assert(/20,000 rows/.test(m) && /\+4 more/.test(m) && Date.now() - t0 < 2000, m);
// 12. seen store is pruned after 20 days
store.seen.old = { at: now - 21 * D }; run({}); assert(!store.seen.old);
console.log('b6 X-ray intake flow: all checks PASS (12 groups)');

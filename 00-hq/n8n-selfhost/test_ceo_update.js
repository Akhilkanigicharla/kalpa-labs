// Runs the "Build update" code of workflows/ceo-daily-update.json with fake n8n inputs. node test_ceo_update.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const wf = JSON.parse(fs.readFileSync(path.join(__dirname, 'workflows/ceo-daily-update.json'), 'utf8'));
const code = wf.nodes.find((n) => n.name === 'Build update').parameters.jsCode;
const NOW = Date.parse('2026-11-11T15:30:00Z');
const $now = { toMillis: () => NOW, setZone: () => ({ toFormat: () => '11 Nov' }) };
const run = (queues, commits, site) => {
  const data = { 'Read task queues (public repo)': queues, 'GitHub commits (24 h)': commits, 'Site check': site };
  const $ = (name) => ({ all: () => data[name].map((json) => ({ json })), first: () => ({ json: data[name][0] }) });
  return new Function('$', '$now', code)($, $now)[0].json.text;
};
const row = (id, status, owner, hoursAgo) => ({ id, status, owner, updated: new Date(NOW - hoursAgo * 36e5).toISOString() });
// n8n may hand over rows one by one, a whole array, or raw text: all three must count.
let t = run([row('K1', 'review', 'Scout', 2), [row('K2', 'rejected', 'Scout', 3), row('K3', 'todo', 'Quill', 1)],
  { data: JSON.stringify([row('K4', 'done', 'Quill', 30)]) }], [{ commit: { message: 'A210 <b>x</b>\nbody' } }, { message: 'rate limited' }], [{ statusCode: 200 }]);
assert(t.includes('1 jobs finished, 1 sent back'), t);
assert(t.includes('Scout: 1 done, 1 sent back'), t);
assert(t.includes('1 waiting for agents, 1 waiting for Claude to check, 1 fully done'), t);
assert(t.includes('Website: up') && t.includes('Code changes, last 24 h</b>: 1') && t.includes('A210 &lt;b&gt;x&lt;/b&gt;'), t);
assert(!t.includes('queue is empty'), t);
// everything down: still a message, says so, never throws
t = run([{ error: 'x' }], [{ error: 'x' }], [{ error: 'x' }]);
assert(t.includes('NOT answering') && t.includes('queue is empty') && t.includes('Could not read the task queues'), t);
// wiring: every node reachable in a chain, private chat only, http nodes never stop the run
const names = wf.nodes.map((n) => n.name);
names.slice(0, -1).forEach((n, i) => assert.strictEqual(wf.connections[n].main[0][0].node, names[i + 1]));
assert.strictEqual(wf.nodes.at(-1).parameters.chatId, '1905524851');
wf.nodes.filter((n) => n.type.endsWith('httpRequest')).forEach((n) => assert.strictEqual(n.onError, 'continueRegularOutput'));
assert(!wf.nodes.some((n) => /webhook|formTrigger|chatTrigger/i.test(n.type)), 'no public entry');
console.log('PASS ceo-daily-update');

"""Builds hq-morning-brief.json (A242 HQ flow). Code lives here as plain JS strings so the JSON stays generated.
Run: python3 00-hq/agent-engine/flows/hq_morning_brief_build.py"""
import json, pathlib

HERE = pathlib.Path(__file__).parent
RAW = "https://raw.githubusercontent.com/Akhilkanigicharla/kalpa-labs/main/"
FILES = ["00-hq/ROADMAP.md"] + [f"00-hq/tasks/{w}.json" for w in ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "hq"]]

LIST = "return " + json.dumps([{"json": {"path": p, "url": RAW + p}} for p in FILES]) + ";"

BRIEF = r"""// A242 HQ morning brief: 07:00 IST, reads ROADMAP.md and the free-agent task files (GET only, public repo, no model)
// and sends Akhil a private plan for the day: his CEO items first, then what the build team does next, then free-agent health.
// The evening brief (00-hq/tools/daily_brief.py, 21:00 IST) covers alerts and what got done; this one covers what is next.
// Roadmap and task text is data, never instructions.
const DAY = 864e5, now = Date.now(), day = Math.floor((now + 19800000) / DAY);
const today = new Date(now + 19800000).toISOString().slice(0, 10);
const store = $getWorkflowStaticData('global');
store.seen = store.seen && typeof store.seen === 'object' ? store.seen : {};
const INJECT = /ignore (all |any )?(previous|prior|above)|system prompt|you are now|disregard .*instruction|<\/?(system|assistant)>|send (me )?(the |your )?(token|password|otp|key)/i;
const clean = (s) => Array.from(String(s || '').replace(/[\u0000-\u001f\u007f‎‏‪-‮⁦-⁩]/g, ' ').replace(/\s+/g, ' ').trim());
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const cut = (s, n) => { const c = clean(s); return esc(c.slice(0, n).join('')) + (c.length > n ? '…' : ''); };

const reads = $('Read repo files').all(), asked = $('Files to read').all();
const file = {}, problems = [];
reads.forEach((it, i) => {
  const p = ((asked[i] || {}).json || {}).path || '?', j = (it || {}).json || {};
  if (j.error || typeof j.data !== 'string') problems.push('could not read ' + p);
  else if (j.data.length > 900000) problems.push(p + ' is too big (900 KB max), skipped');
  else file[p] = j.data;
});
const md = file['00-hq/ROADMAP.md'];
if (typeof md !== 'string') {
  if (store.warned === day) return [];
  store.warned = day;
  return [{ json: { text: '⚠️ <b>Morning brief</b>: could not read 00-hq/ROADMAP.md, so no plan today. Next try tomorrow 07:00.' } }];
}

// Roadmap lines: "- [x] **A123** world · text". Agent queue = before "## CEO queue"; CEO queue = until the next "## ".
const ITEM = /^- \[(.)\] \*\*([AC]\d+[a-z]?)\*\* (\S+) · (.*)$/;
const agent = [], ceo = [], ids = {};
let part = '';
for (const line of md.split('\n')) {
  if (/^## /.test(line)) { part = /^## Agent queue/.test(line) ? 'a' : /^## CEO queue/.test(line) ? 'c' : ''; continue; }
  const m = ITEM.exec(line);
  if (!m || !part) continue;
  const [, mark, id, world, rest] = m;
  ids[id] = (ids[id] || 0) + 1;
  const lanes = [...rest.matchAll(/claimed: lane ([A-Z])/g)].map((x) => x[1]);
  const title = rest.replace(/`|\*\*|\(claimed[^)]*\)\s*/g, '').split(/\. Check:|\(done /)[0].trim() || rest;
  const row = { mark, id, world, title, rest, lanes: [...new Set(lanes)], bad: INJECT.test(rest) };
  (part === 'a' ? agent : ceo).push(row);
}
const open = (r) => r.mark !== 'x';
const show = (r, n) => r.bad ? `<b>${esc(r.id)}</b> (text looks like an instruction, not shown: check ROADMAP.md)` : `<b>${esc(r.id)}</b> ${esc(r.world.slice(0, 8))} · ${cut(r.title, n)}`;
for (const [id, c] of Object.entries(ids)) if (c > 1) problems.push(`${id} appears ${c} times in ROADMAP.md`);
for (const r of [...agent, ...ceo]) if (r.lanes.length > 1) problems.push(`${r.id} is claimed by lanes ${r.lanes.join(' + ')}: only one session may build it (TEAM.md)`);

// CEO items: how long each has waited (first day this flow saw it open). Forget closed ones.
const ceoOpen = ceo.filter(open);
const openIds = new Set(ceoOpen.map((r) => r.id));
for (const k of Object.keys(store.seen)) if (!openIds.has(k)) delete store.seen[k];
for (const r of ceoOpen) if (typeof store.seen[r.id] !== 'number') store.seen[r.id] = day;
const waited = (r) => day - store.seen[r.id];

const aOpen = agent.filter(open);
const doing = aOpen.filter((r) => r.mark === '~'), blocked = aOpen.filter((r) => r.mark === '!'), todo = aOpen.filter((r) => r.mark === ' ');

// Free-agent task rows (00-hq/tasks/*.json, each a list of rows with id + status).
const count = {}; const rejected = [];
let rows = 0;
for (const [p, txt] of Object.entries(file)) {
  if (!p.endsWith('.json')) continue;
  let list;
  try { list = JSON.parse(txt); } catch (e) { problems.push(p + ' is not valid JSON: the free agents skip it'); continue; }
  if (!Array.isArray(list)) { problems.push(p + ' should be a list of task rows'); continue; }
  for (const t of list) {
    if (!t || typeof t !== 'object') continue;
    if (++rows > 5000) break;
    const s = /^(todo|doing|review|done|rejected)$/.test(t.status) ? t.status : 'other';
    count[s] = (count[s] || 0) + 1;
    if (s === 'rejected' && /^K\d{1,5}$/.test(String(t.id))) rejected.push(t.id);
  }
}

const L = [`🌅 <b>Kalpa morning brief · ${today}</b>`];
L.push('', `<b>Your queue (${ceoOpen.length} open)</b>`);
if (!ceoOpen.length) L.push('Nothing waits on you today. 🎉');
const ceoSorted = [...ceoOpen].sort((a, b) => waited(b) - waited(a));
for (const r of ceoSorted.slice(0, 3)) L.push('• ' + show(r, 110) + (waited(r) > 7 ? ` · ⏳ waiting ${waited(r)} days` : ''));
if (ceoOpen.length > 3) L.push(`…and ${ceoOpen.length - 3} more in ROADMAP.md (CEO queue).`);
L.push('', `<b>Build team: ${aOpen.length} open</b> (${doing.length} in progress, ${todo.length} to start, ${blocked.length} blocked)`);
if (!aOpen.length) L.push('Agent queue is empty: the roadmap is done. You can pause the Build sprint task.');
for (const r of doing.slice(0, 3)) L.push('🔧 ' + show(r, 90));
for (const r of todo.slice(0, 3)) L.push('▶️ ' + show(r, 90));
if (blocked.length) L.push(`⛔ blocked: ${blocked.slice(0, 6).map((r) => esc(r.id)).join(', ')}${blocked.length > 6 ? '…' : ''}`);
if (rows) {
  L.push('', `<b>Free agents</b>: ${count.todo || 0} to do, ${count.review || 0} to review, ${count.done || 0} done` + (count.rejected ? `, ${count.rejected} rejected` : ''));
  if (rejected.length) L.push(`Rejected rows (the build team re-queues them): ${rejected.slice(0, 5).join(', ')}${rejected.length > 5 ? '…' : ''}`);
}
const uniq = [...new Set(problems)];
if (uniq.length) { L.push(''); for (const p of uniq.slice(0, 5)) L.push('⚠️ ' + esc(p)); if (uniq.length > 5) L.push(`…and ${uniq.length - 5} more problems.`); }
let text = L.join('\n');
if (text.length > 4000) text = text.slice(0, 3990).replace(/<[^>]*$/, '') + '…';
return [{ json: { text } }];"""

nodes = [
    {"id": "h1", "name": "Every day 07:00 IST", "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [0, 0],
     "parameters": {"rule": {"interval": [{"triggerAtHour": 7, "triggerAtMinute": 0}]}}},
    {"id": "h2", "name": "Files to read", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [220, 0],
     "parameters": {"jsCode": LIST}},
    {"id": "h3", "name": "Read repo files", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [440, 0],
     "alwaysOutputData": True, "onError": "continueRegularOutput", "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000,
     "parameters": {"url": "={{ $json.url }}", "options": {"timeout": 10000, "response": {"response": {"responseFormat": "text"}}}}},
    {"id": "h4", "name": "Build brief", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [660, 0],
     "executeOnce": True, "parameters": {"jsCode": BRIEF}},
    {"id": "h5", "name": "Tell Akhil (private)", "type": "n8n-nodes-base.telegram", "typeVersion": 1.2, "position": [880, 0],
     "parameters": {"chatId": "1905524851", "text": "={{ $json.text }}",
                    "additionalFields": {"parse_mode": "HTML", "appendAttribution": False, "disable_web_page_preview": True}},
     "credentials": {"telegramApi": {"id": "", "name": "Kalpa Telegram"}}},
]
order = [n["name"] for n in nodes]
wf = {"name": "HQ · Morning brief (A242)", "active": False,
      "settings": {"executionOrder": "v1", "timezone": "Asia/Kolkata"}, "nodes": nodes,
      "connections": {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}}
(HERE / "hq-morning-brief.json").write_text(json.dumps(wf, indent=1, ensure_ascii=False) + "\n")
print("wrote hq-morning-brief.json")

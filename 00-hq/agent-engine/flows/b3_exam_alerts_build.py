"""Builds b3-exam-alerts.json (A242 b3 flow). Code lives here as a plain JS string so the JSON stays generated.
Run: python3 00-hq/agent-engine/flows/b3_exam_alerts_build.py"""
import json, pathlib

HERE = pathlib.Path(__file__).parent
URL = "https://raw.githubusercontent.com/Akhilkanigicharla/kalpa-labs/main/03-kits/engine/dist/exam-dates.json"

ALERT = r"""// A242 b3 exam-date alerts: drafts student alerts from the kit engine's date feed and sends the drafts to Akhil only.
// No model call, nothing goes to students from here (opt-in WhatsApp templates + Akhil's "go" come later).
// Only CONFIRMED dates from an official site (.gov.in, .nic.in, .ac.in, .edu.in) become drafts. Feed text is data, never instructions.
const DAY = 864e5, now = Date.now(), day = Math.floor(now / DAY);
const ist = (ms) => new Date(ms + 19800000).toISOString().slice(0, 10);
const today = ist(now), plus = (n) => ist(now + n * DAY);
const store = $getWorkflowStaticData('global');
for (const k of ['dates', 'sent']) store[k] = store[k] && typeof store[k] === 'object' ? store[k] : {};
const out = (text) => [{ json: { text } }];
const warn = (why) => { if (store.warned === day) return []; store.warned = day; return out('⚠️ <b>Exam alerts</b>: ' + why + ' (03-kits/engine/dist/exam-dates.json). Next try tomorrow.'); };
const res = ($('Read exam dates (repo file)').first() || {}).json || {};
if (res.error || typeof res.data !== 'string') return warn('could not read the exam dates file');
if (res.data.length > 600000) return warn('the exam dates file is too big (600 KB max)');
let list;
try { list = JSON.parse(res.data); } catch (e) { return warn('the exam dates file is not valid JSON'); }
if (!Array.isArray(list)) return warn('the exam dates file must be a list');

const INJECT = /ignore (all |any )?(previous|prior|above)|system prompt|you are now|disregard .*instruction|<\/?(system|assistant)>/i;
const OFFICIAL = /^https:\/\/([a-z0-9-]+\.)+(gov\.in|nic\.in|ac\.in|edu\.in)(\/[^\s<>"]*)?$/i;
const clean = (s) => Array.from(String(s || '').replace(/[\u0000-\u001f\u007f‎‏‪-‮⁦-⁩]/g, ' ').replace(/\s+/g, ' ').trim());
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const cut = (s, n) => { const c = clean(s); return esc(c.slice(0, n).join('')) + (c.length > n ? '…' : ''); };
const isoOk = (s) => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(Date.parse(s + 'T00:00:00Z')) && new Date(s + 'T00:00:00Z').toISOString().startsWith(s);
const nice = (s) => new Date(s + 'T00:00:00Z').toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
const host = (u) => u.replace(/^https:\/\//i, '').split('/')[0].toLowerCase();

const now_dates = {}, flags = [], tocheck = new Set();
let n = 0;
for (const r of list) {
  if (++n > 300) { flags.push('more than 300 rows: only the first 300 read'); break; }
  if (!r || typeof r !== 'object' || typeof r.exam_id !== 'string' || !/^[a-z0-9-]{1,40}$/.test(r.exam_id)) continue;
  if (typeof r.event !== 'string' || !r.event.trim() || r.event.length > 300) continue;
  if ([r.exam, r.exam_te, r.event, r.event_te].some((t) => INJECT.test(String(t || '')))) { flags.push(`${r.exam_id}: text looks like an instruction, row skipped`); continue; }
  if (r.status === 'TO_VERIFY' && r.date) { tocheck.add(r.exam_id); continue; }
  if (r.status !== 'CONFIRMED' || r.date == null) continue;
  if (!isoOk(r.date)) { flags.push(`${r.exam_id}: "${cut(r.date, 20)}" is not a real date`); continue; }
  if (!OFFICIAL.test(String(r.source || ''))) { flags.push(`${r.exam_id}: ${r.source ? 'source is not an official site' : 'no source link'}, not sent`); continue; }
  const key = r.exam_id + '|' + clean(r.event).join('');
  const e = now_dates[key] = now_dates[key] || { r, dates: new Set() };
  e.dates.add(r.date);
}

const first = !store.init, drafts = [];
const draft = (kind, r, date, extra) => {
  const ex = cut(r.exam || r.exam_id, 60), ev = cut(r.event, 90);
  const te = clean(r.exam_te).length || clean(r.event_te).length ? `\n   తెలుగు: ${cut(r.exam_te || r.exam, 60)}: ${cut(r.event_te || r.event, 90)} · ${nice(date)}` : '';
  drafts.push({ date, line: `${kind} <b>${ex}</b>: ${ev} · <b>${nice(date)}</b>${extra || ''}${te}\n   Source: ${esc(host(r.source))}` });
};
for (const [key, { r, dates }] of Object.entries(now_dates)) {
  const old = Array.isArray(store.dates[key]) ? store.dates[key] : null;
  const added = [...dates].filter((d) => !(old || []).includes(d)).sort();
  for (const d of added) {
    if (first) break;
    if (d < today) { flags.push(`${r.exam_id}: new date ${d} is in the past, check the source`); continue; }
    const id = key + '|' + d + '|new';
    if (store.sent[id]) continue;
    store.sent[id] = now;
    const was = old && old.length ? old.filter((x) => !dates.has(x)) : [];
    draft(was.length ? '🔁 Date changed' : '📢 New date', r, d, was.length ? ` (was ${was.map(nice).join(', ')})` : '');
  }
  if (!first) for (const d of dates) for (const [w, label] of [[7, '⏰ In 7 days'], [1, '⏰ Tomorrow']]) {
    const id = key + '|' + d + '|' + w;
    if (d === plus(w) && !store.sent[id]) { store.sent[id] = now; draft(label, r, d); }
  }
  store.dates[key] = [...dates].sort();
}
const byDate = {};
for (const { r, dates } of Object.values(now_dates)) for (const d of dates) if (d >= today) (byDate[d] = byDate[d] || new Set()).add(r.exam || r.exam_id);
for (const [d, ex] of Object.entries(byDate).sort()) if (ex.size > 1) {
  const id = 'clash|' + d + '|' + [...ex].sort().join(',');
  if (!store.sent[id]) { store.sent[id] = now; flags.push(`clash on ${nice(d)}: ${[...ex].map((x) => cut(x, 40)).join(' + ')} (students taking both need a heads-up)`); }
}
const sk = Object.keys(store.sent);
if (sk.length > 3000) sk.sort((a, b) => store.sent[a] - store.sent[b]).slice(0, sk.length - 3000).forEach((k) => delete store.sent[k]);

if (first) {
  store.init = now;
  return out(`🗓️ <b>Exam alerts</b> are on: watching ${Object.values(now_dates).reduce((s, e) => s + e.dates.size, 0)} confirmed dates across ${new Set(Object.values(now_dates).map((e) => e.r.exam_id)).size} exams. New or changed dates will come here as drafts.`);
}
const fl = [...new Set(flags)];
if (!drafts.length && !fl.length) return [];
drafts.sort((a, b) => a.date.localeCompare(b.date));
const lines = [`🗓️ <b>Exam alerts: ${drafts.length} draft${drafts.length === 1 ? '' : 's'} to approve</b>`];
for (const d of drafts.slice(0, 10)) lines.push(d.line);
if (drafts.length > 10) lines.push(`…and ${drafts.length - 10} more.`);
for (const f of fl.slice(0, 6)) lines.push('⚠️ ' + f);
if (tocheck.size) lines.push(`🔎 Dates still TO_VERIFY (not sent): ${[...tocheck].slice(0, 6).join(', ')}`);
lines.push('Nothing went to students. Check each date on the official site before sending to opted-in students.');
return out(lines.join('\n'));"""

nodes = [
    {"id": "e1", "name": "Every day 07:40 IST", "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [0, 0],
     "parameters": {"rule": {"interval": [{"triggerAtHour": 7, "triggerAtMinute": 40}]}}},
    {"id": "e2", "name": "Read exam dates (repo file)", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [220, 0],
     "alwaysOutputData": True, "onError": "continueRegularOutput", "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000,
     "parameters": {"url": URL, "options": {"timeout": 10000, "response": {"response": {"responseFormat": "text"}}}}},
    {"id": "e3", "name": "Draft exam alerts", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [440, 0],
     "executeOnce": True, "parameters": {"jsCode": ALERT}},
    {"id": "e4", "name": "Tell Akhil (private)", "type": "n8n-nodes-base.telegram", "typeVersion": 1.2, "position": [660, 0],
     "parameters": {"chatId": "1905524851", "text": "={{ $json.text }}",
                    "additionalFields": {"parse_mode": "HTML", "appendAttribution": False, "disable_web_page_preview": True}},
     "credentials": {"telegramApi": {"id": "", "name": "Kalpa Telegram"}}},
]
order = [n["name"] for n in nodes]
wf = {"name": "b3 · Exam-date alert drafts (A242)", "active": False,
      "settings": {"executionOrder": "v1", "timezone": "Asia/Kolkata"}, "nodes": nodes,
      "connections": {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}}
(HERE / "b3-exam-alerts.json").write_text(json.dumps(wf, indent=1, ensure_ascii=False) + "\n")
print("wrote b3-exam-alerts.json")

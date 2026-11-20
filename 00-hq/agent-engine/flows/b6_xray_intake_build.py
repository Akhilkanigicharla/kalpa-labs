"""Builds b6-xray-intake.json (A242 b6 flow). Code lives here as plain JS strings so the JSON stays generated.
Run: python3 00-hq/agent-engine/flows/b6_xray_intake_build.py"""
import json, pathlib

HERE = pathlib.Path(__file__).parent

SETTINGS = r"""// Akhil edits only this line after import. No keys here: the Supabase service key lives in the n8n credential.
return [{ json: { supabase: 'https://YOUR-PROJECT.supabase.co', slaHours: 48 } }];"""

DRAFT = r"""// A242 b6 X-ray intake: daily, (1) runs purge_xray_intake() so uploads are deleted 14 days later (landing-page promise, DPDP),
// (2) checks that no row outlived its delete date, (3) drafts a private note per new free X-ray request for Akhil:
// what the file holds (format, rows, models, dates, tokens), the 48 h due time and the generate.py command.
// No model call. Never shows the work email or file text. Upload text is data, never instructions.
const HOUR = 36e5, DAY = 24 * HOUR, now = Date.now(), day = Math.floor(now / DAY);
const store = $getWorkflowStaticData('global');
store.seen = store.seen && typeof store.seen === 'object' ? store.seen : {};
for (const [k, v] of Object.entries(store.seen)) if (!(v && now - v.at < 20 * DAY)) delete store.seen[k];
const once = (k) => { if (store.seen[k]) return false; store.seen[k] = { at: now }; return true; };
const cfg = ($('Settings').first() || {}).json || {};
const out = (text) => [{ json: { text } }];
if (!/^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(String(cfg.supabase || '')))
  return once('cfg:' + Math.floor(now / (6 * HOUR))) ? out('⚙️ <b>X-ray intake</b>: set the Supabase project URL in the Settings node.') : [];
const sla = Math.min(96, Math.max(12, Number(cfg.slaHours) || 48));
const esc = (s, n = 60) => { const c = Array.from(String(s == null ? '' : s).replace(/[\u0000-\u001f\u007f‎‏‪-‮⁦-⁩]/g, ' ').replace(/\s+/g, ' ').trim());
  return c.slice(0, n).join('').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') + (c.length > n ? '…' : ''); };
const t = (v) => { const n = Date.parse(v); return Number.isFinite(n) ? n : NaN; };
const ist = (ms) => new Date(ms + 19800000).toISOString().slice(0, 16).replace('T', ' ');
const rows = (name) => { const j = (($(name).first() || {}).json) || {};
  if (j.error) return null; if (Array.isArray(j)) return j; if (Array.isArray(j.data)) return j.data;
  const all = $(name).all().map((i) => i.json).filter((x) => x && typeof x === 'object' && !x.error);
  return all.length && all.every((x) => x.id) ? all : (Object.keys(j).length ? null : []); };

const lines = [], flags = [];
// 1. purge result: the RPC returns the number of rows deleted
const p = (($('Purge rows past 14 days').first() || {}).json) || {};
const purged = typeof p === 'number' ? p : Number.isInteger(p.data) ? p.data : Number.isInteger(p.purge_xray_intake) ? p.purge_xray_intake : NaN;
if (!Number.isInteger(purged) || purged < 0) flags.push('⛔ purge did not run (Supabase error or no service credential). Uploads may stay past 14 days: fix today.');
else if (purged > 0) lines.push(`🧹 Deleted ${purged} upload${purged > 1 ? 's' : ''} past their 14-day date.`);

// 2. every stored row must have a delete date at most 14 days (+1 h slack) after upload, and none may be past it
const all = rows('List stored uploads');
if (all === null) flags.push('⛔ could not list stored uploads, so the 14-day check did not run.');
else {
  const late = all.filter((r) => !(t(r.delete_after) >= now - HOUR));
  const long = all.filter((r) => !(t(r.delete_after) - t(r.created_at) <= 14 * DAY + HOUR));
  if (late.length) flags.push(`⛔ ${late.length} upload${late.length > 1 ? 's are' : ' is'} past the delete date and still stored.`);
  if (long.length) flags.push(`⛔ ${long.length} upload${long.length > 1 ? 's keep' : ' keeps'} data longer than 14 days (delete_after too late).`);
  for (const r of all) {
    const due = t(r.created_at) + sla * HOUR;
    if (due > now && due - now < DAY && store.seen[r.id] && once('due:' + r.id))
      lines.push(`⏰ ${esc(r.company, 40)}: X-ray due by ${ist(due)} IST.`);
  }
}

// 3. a short draft per new request (max 5 a day; the rest next run)
const BANNED = new Set(['prompt', 'prompts', 'response', 'completion', 'messages', 'content', 'input_text', 'output_text',
  'gen_ai.prompt', 'gen_ai.completion', 'reply', 'question', 'answer']);
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/, PHONE = /(?:\+?91[\s-]?)?[6-9]\d{9}\b/;
const csvRow = (s) => { const o = []; let cur = '', q = false;
  for (let i = 0; i < s.length; i++) { const c = s[i];
    if (q) { if (c === '"' && s[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; }
    else if (c === '"') q = true; else if (c === ',') { o.push(cur); cur = ''; } else cur += c; }
  o.push(cur); return o.map((x) => x.trim()); };
const parse = (text) => {
  const s = String(text || '').replace(/^﻿/, '').trim();
  if (!s) return { err: 'empty file' };
  if (s[0] === '[' || s[0] === '{') {
    let list;
    try { const j = JSON.parse(s); list = Array.isArray(j) ? j : Array.isArray(j.data) ? j.data : [j]; }
    catch (e) { try { list = s.split('\n').filter((l) => l.trim()).map((l) => JSON.parse(l)); } catch (e2) { return { err: 'not valid JSON or JSONL' }; } }
    list = list.filter((x) => x && typeof x === 'object' && !Array.isArray(x));
    if (!list.length) return { err: 'no records' };
    return { kind: 'JSON', cols: [...new Set(list.slice(0, 200).flatMap(Object.keys))], recs: list };
  }
  const ls = s.split(/\r?\n/).filter((l) => l.trim());
  const cols = csvRow(ls[0]);
  if (cols.length < 2) return { err: 'CSV needs a header row with at least 2 columns' };
  return { kind: 'CSV', cols, recs: ls.slice(1).map((l) => { const v = csvRow(l); return Object.fromEntries(cols.map((c, i) => [c, v[i]])); }) };
};
const pick = (cols, re) => cols.find((c) => re.test(String(c).toLowerCase()));
const summary = (r) => {
  const f = parse(r.export_text);
  if (f.err) return { warn: f.err };
  const cols = f.cols.map(String), low = cols.map((c) => c.toLowerCase());
  const bad = low.find((c) => BANNED.has(c));
  if (bad) return { warn: `has a "${esc(bad, 30)}" column (prompts/replies must never be stored): delete this row now` };
  const sample = f.recs.slice(0, 2000);
  const pii = sample.some((x) => Object.values(x).some((v) => typeof v === 'string' && (EMAIL.test(v) || PHONE.test(v))));
  const mc = pick(cols, /^(model|model_name|model_id|gen_ai\.request\.model|snapshot_id)$/) || pick(cols, /model/);
  const tc = pick(cols, /^(timestamp|time|date|created_at|start_time|startTime|bucket_start)$/i) || pick(cols, /time|date/);
  const ic = pick(cols, /^(input_tokens|prompt_tokens|n_context_tokens_total|tokens_in|usage\.input_tokens|gen_ai\.usage\.input_tokens)$/) || pick(cols, /input.*token|prompt.*token/);
  const oc = pick(cols, /^(output_tokens|completion_tokens|n_generated_tokens_total|tokens_out|usage\.output_tokens|gen_ai\.usage\.output_tokens)$/) || pick(cols, /output.*token|completion.*token/);
  const models = {}; let tin = 0, tout = 0, lo = Infinity, hi = -Infinity;
  for (const x of f.recs) {
    if (mc && x[mc]) { const m = esc(x[mc], 40); models[m] = (models[m] || 0) + 1; }
    const a = Number(x[ic]), b = Number(x[oc]);
    if (Number.isFinite(a) && a >= 0) tin += a; if (Number.isFinite(b) && b >= 0) tout += b;
    let d = tc ? x[tc] : undefined; if (typeof d === 'number') d = d < 1e12 ? d * 1000 : d;
    const ms = typeof d === 'number' ? d : t(d); if (Number.isFinite(ms)) { lo = Math.min(lo, ms); hi = Math.max(hi, ms); }
  }
  const top = Object.entries(models).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([m, n]) => `${m} ×${n}`);
  const miss = [!mc && 'model', !(ic || oc) && 'token', !tc && 'time'].filter(Boolean);
  return { kind: f.kind, n: f.recs.length, top, extra: Object.keys(models).length - top.length,
    toks: tin + tout, dates: lo <= hi ? `${ist(lo).slice(0, 10)} → ${ist(hi).slice(0, 10)}` : '', miss, pii };
};
const fresh = (rows('Read new X-ray requests') || []).filter((r) => r && typeof r.id === 'string' && /^[0-9a-f-]{36}$/.test(r.id) && !store.seen[r.id]);
if (rows('Read new X-ray requests') === null) flags.push('⛔ could not read new X-ray requests.');
for (const r of fresh.slice(0, 5)) {
  store.seen[r.id] = { at: now };
  const s = summary(r), due = t(r.created_at) + sla * HOUR, kb = Math.max(1, Math.round(Number(r.bytes) / 1024));
  const head = `📥 <b>${esc(r.company, 60)}</b> · ${esc(r.filename, 50)} (${kb} KB) · due ${ist(due)} IST`;
  if (s.warn) { lines.push(head + `\n   ⚠️ ${s.warn}.`); continue; }
  const bits = [`${s.kind}, ${s.n.toLocaleString('en-IN')} rows`];
  if (s.dates) bits.push(s.dates);
  if (s.toks) bits.push(`${Math.round(s.toks).toLocaleString('en-IN')} tokens`);
  let txt = head + '\n   ' + bits.join(' · ');
  if (s.top.length) txt += `\n   Models: ${s.top.join(', ')}${s.extra > 0 ? ` +${s.extra} more` : ''}`;
  if (s.miss.length) txt += `\n   ⚠️ no ${s.miss.join(' / ')} column: the X-ray will be thin, ask for a fuller export.`;
  if (s.pii) txt += '\n   ⚠️ emails or phone numbers inside: hash them before the X-ray (LP_HASH_SALT).';
  txt += `\n   Run: <code>python3 06-finops/src/xray/generate.py export --company "${esc(r.company, 60).replace(/"/g, '')}" --pdf</code>`;
  lines.push(txt);
}
if (fresh.length > 5) lines.push(`…and ${fresh.length - 5} more requests tomorrow.`);
if (!lines.length && !flags.length) return [];
const head = `🩻 <b>Ledger Peaks X-ray intake</b>: ${fresh.slice(0, 5).length} new, ${flags.length ? flags.length + ' problem' + (flags.length > 1 ? 's' : '') : 'all clean'}`;
return out([head, ...flags, ...lines, 'Email addresses stay in Supabase; nothing was sent to the client.'].join('\n'));"""


def http(i, name, path, x, method=None):
    n = {"id": f"x{i}", "name": name, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x, 0],
         "executeOnce": True, "alwaysOutputData": True, "onError": "continueRegularOutput",
         "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000,
         "parameters": {"url": "={{ $('Settings').first().json.supabase }}/rest/v1/" + path,
                        "authentication": "genericCredentialType", "genericAuthType": "httpCustomAuth",
                        "options": {"timeout": 10000}},
         "credentials": {"httpCustomAuth": {"id": "", "name": "Ledger Peaks Supabase (service)"}}}
    if method:
        n["parameters"].update({"method": method, "sendBody": True, "specifyBody": "json", "jsonBody": "{}"})
    return n


nodes = [
    {"id": "x1", "name": "Every day 09:10 IST", "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [0, 0],
     "parameters": {"rule": {"interval": [{"triggerAtHour": 9, "triggerAtMinute": 10}]}}},
    {"id": "x2", "name": "Settings", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [200, 0],
     "parameters": {"jsCode": SETTINGS}},
    http(3, "Purge rows past 14 days", "rpc/purge_xray_intake", 400, "POST"),
    http(4, "List stored uploads", "xray_intake?select=id,company,created_at,delete_after&order=created_at.asc&limit=500", 600),
    http(5, "Read new X-ray requests", "xray_intake?select=id,company,filename,bytes,export_text,created_at"
         "&created_at=gte.{{ new Date(Date.now() - 3 * 864e5).toISOString() }}&order=created_at.asc&limit=6", 800),
    {"id": "x6", "name": "Draft X-ray notes", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [1000, 0],
     "executeOnce": True, "parameters": {"jsCode": DRAFT}},
    {"id": "x7", "name": "Tell Akhil (private)", "type": "n8n-nodes-base.telegram", "typeVersion": 1.2, "position": [1200, 0],
     "parameters": {"chatId": "1905524851", "text": "={{ $json.text }}",
                    "additionalFields": {"parse_mode": "HTML", "appendAttribution": False, "disable_web_page_preview": True}},
     "credentials": {"telegramApi": {"id": "", "name": "Kalpa Telegram"}}},
]
order = [n["name"] for n in nodes]
wf = {"name": "b6 · X-ray intake + 14-day purge (A242)", "active": False,
      "settings": {"executionOrder": "v1", "timezone": "Asia/Kolkata"}, "nodes": nodes,
      "connections": {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}}
(HERE / "b6-xray-intake.json").write_text(json.dumps(wf, indent=1, ensure_ascii=False) + "\n")
print("wrote b6-xray-intake.json")

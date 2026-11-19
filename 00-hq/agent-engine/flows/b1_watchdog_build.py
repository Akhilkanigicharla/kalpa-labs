"""Builds b1-frontdesk-watchdog.json (A242 b1 flow). Code lives here as plain JS strings so the JSON stays generated.
Run: python3 00-hq/agent-engine/flows/b1_watchdog_build.py"""
import json, pathlib

HERE = pathlib.Path(__file__).parent

SETTINGS = r"""// Akhil edits only these two lines after import. No keys here: the Supabase service key lives in the n8n credential.
return [{ json: { supabase: 'https://YOUR-PROJECT.supabase.co', waitMin: 20 } }];"""

FIND = r"""// A242 b1 front-desk watchdog: a chat was handed to a person (status=human) but nobody has answered the customer.
// Reads only ids, timestamps and the business name. Never reads or sends customer message text; phone numbers are masked.
const MIN = 60000, HOUR = 60 * MIN, DAY = 24 * HOUR, now = Date.now();
const store = $getWorkflowStaticData('global');
store.seen = store.seen && typeof store.seen === 'object' ? store.seen : {};
for (const [k, t] of Object.entries(store.seen)) if (!(now - t < 3 * DAY)) delete store.seen[k];
const cfg = ($('Settings').first() || {}).json || {};
const waitMin = Math.min(240, Math.max(5, Number(cfg.waitMin) || 20));
const esc = (s) => String(s == null ? '' : s).replace(/[\u0000-\u001f\u007f‎‏‪-‮⁦-⁩]/g, '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').slice(0, 60);
const t = (v) => { const n = Date.parse(v); return Number.isFinite(n) ? n : NaN; };
const rows = (name) => { try { return $(name).all().map((i) => i.json); } catch (e) { return [{ error: 'missing' }]; } };
const once = (key) => { if (store.seen[key]) return false; store.seen[key] = now; return true; };
const out = (text) => [{ json: { text } }];

if (!/^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(String(cfg.supabase || '')))
  return once('cfg:' + Math.floor(now / (6 * HOUR))) ? out('⚙️ <b>Front-desk watchdog</b>: set the Supabase project URL in the Settings node.') : [];
const sessions = rows('Read handed-over chats'), replies = rows('Read staff replies'), clients = rows('Read businesses');
const broken = [sessions, replies, clients].some((r) => r.some((x) => x && x.error));
if (broken) return once('err:' + Math.floor(now / (6 * HOUR))) ? out('⚠️ <b>Front-desk watchdog</b> could not read Supabase (key, URL or network). Will try again in 15 min; next warning in 6 h.') : [];

const names = {};
for (const c of clients) if (c && typeof c.id === 'string') names[c.id] = c.name;
const lastStaff = {};
for (const r of replies) {
  if (!r || typeof r.contact !== 'string' || typeof r.client_id !== 'string') continue;
  const k = r.client_id + '|' + r.contact, at = t(r.created_at);
  if (at > (lastStaff[k] || 0)) lastStaff[k] = at;
}
const late = [];
for (const s of sessions) {
  if (!s || s.status !== 'human' || typeof s.client_id !== 'string' || typeof s.contact !== 'string') continue;
  if (!/^[A-Za-z0-9_:-]{3,64}$/.test(s.contact)) continue;
  const inbound = t(s.last_inbound_at), until = t(s.human_until);
  if (!(inbound <= now)) continue;                       // no customer message yet, or a clock from the future
  if (until < now) continue;                             // pause is over: the bot answers again
  if ((lastStaff[s.client_id + '|' + s.contact] || 0) >= inbound) continue; // a person already replied
  const waited = now - inbound;
  if (waited < waitMin * MIN) continue;
  const wa = /^\d{8,15}$/.test(s.contact), left = DAY - waited;
  const level = wa && left <= 0 ? 'closed' : wa && left < 2 * HOUR ? 'closing' : 'late';
  if (!once([s.client_id, s.contact, s.last_inbound_at, level].join('|'))) continue;
  late.push({ waited, left, level, wa, who: '••••' + s.contact.slice(-4), biz: esc(names[s.client_id] || 'a client') });
}
if (!late.length) return [];
late.sort((a, b) => b.waited - a.waited);
const ago = (ms) => ms < 90 * MIN ? Math.round(ms / MIN) + ' min' : (ms / HOUR).toFixed(1) + ' h';
const line = (x) => x.level === 'closed'
  ? `🔴 ${x.biz} · ${x.who} · waited ${ago(x.waited)}. WhatsApp 24 h window is closed: only an approved template can reach them now.`
  : x.level === 'closing'
    ? `🟠 ${x.biz} · ${x.who} · waited ${ago(x.waited)}. Reply in the next ${ago(x.left)} or the WhatsApp window closes.`
    : `🟡 ${x.biz} · ${x.who}${x.wa ? '' : ' (web chat)'} · waited ${ago(x.waited)} after the bot handed over.`;
const shown = late.slice(0, 10);
const more = late.length > shown.length ? `\n…and ${late.length - shown.length} more in the BotBhai inbox.` : '';
return out(`🛎️ <b>Front desk: ${late.length} customer${late.length > 1 ? 's' : ''} waiting for a person</b>\n` +
  shown.map(line).join('\n') + more + '\nOpen the BotBhai inbox to reply.');"""

def http(i, name, path, x):
    return {"id": f"w{i}", "name": name, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x, 0],
            "executeOnce": True, "alwaysOutputData": True, "onError": "continueRegularOutput",
            "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000,
            "parameters": {"url": "={{ $('Settings').first().json.supabase }}/rest/v1/" + path,
                           "authentication": "genericCredentialType", "genericAuthType": "httpCustomAuth",
                           "options": {"timeout": 10000}},
            "credentials": {"httpCustomAuth": {"id": "", "name": "BotBhai Supabase (read only)"}}}

nodes = [
    {"id": "w1", "name": "Every 15 min", "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [0, 0],
     "parameters": {"rule": {"interval": [{"field": "minutes", "minutesInterval": 15}]}}},
    {"id": "w2", "name": "Settings", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [200, 0],
     "parameters": {"jsCode": SETTINGS}},
    http(3, "Read handed-over chats", "sessions?status=eq.human&select=client_id,contact,status,human_until,last_inbound_at&limit=500", 400),
    http(4, "Read staff replies", "messages?direction=eq.out&author=eq.staff&created_at=gte.{{ new Date(Date.now() - 26 * 3600e3).toISOString() }}&select=client_id,contact,created_at&limit=2000", 600),
    http(5, "Read businesses", "clients?active=eq.true&select=id,name&limit=500", 800),
    {"id": "w6", "name": "Find waiting chats", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [1000, 0],
     "executeOnce": True, "parameters": {"jsCode": FIND}},
    {"id": "w7", "name": "Tell Akhil (private)", "type": "n8n-nodes-base.telegram", "typeVersion": 1.2, "position": [1200, 0],
     "parameters": {"chatId": "1905524851", "text": "={{ $json.text }}",
                    "additionalFields": {"parse_mode": "HTML", "appendAttribution": False, "disable_web_page_preview": True}},
     "credentials": {"telegramApi": {"id": "", "name": "Kalpa Telegram"}}},
]
order = [n["name"] for n in nodes]
wf = {"name": "b1 · BotBhai front-desk watchdog (A242)", "active": False,
      "settings": {"executionOrder": "v1", "timezone": "Asia/Kolkata"}, "nodes": nodes,
      "connections": {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}}
(HERE / "b1-frontdesk-watchdog.json").write_text(json.dumps(wf, indent=1, ensure_ascii=False) + "\n")
print("wrote b1-frontdesk-watchdog.json")

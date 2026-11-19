"""Builds b2-review-watcher.json (A242 b2 flow). Code lives here as a plain JS string so the JSON stays generated.
Run: python3 00-hq/agent-engine/flows/b2_review_watcher_build.py"""
import json, pathlib

HERE = pathlib.Path(__file__).parent
URL = "https://raw.githubusercontent.com/Akhilkanigicharla/kalpa-labs/main/02-jobcard/store/reviews.json"

WATCH = r"""// A242 b2 store-review watcher: daily digest of NEW app-store reviews for the b2 apps, to Akhil only.
// No model call: keyword topics in English, Telugu, Hindi, Tenglish and Hinglish. Review text is data, never instructions.
const DAY = 864e5, now = Date.now(), day = Math.floor(now / DAY);
const APPS = ['bhasha-kids', 'jyotish', 'photo-studio'];
const store = $getWorkflowStaticData('global');
store.seen = store.seen && typeof store.seen === 'object' ? store.seen : {};
const out = (text) => [{ json: { text } }];
const warn = (why) => { if (store.warned === day) return []; store.warned = day; return out('⚠️ <b>App review watcher</b>: ' + why + ' (02-jobcard/store/reviews.json). Next try tomorrow.'); };
const res = ($('Read reviews (repo file)').first() || {}).json || {};
if (res.error || typeof res.data !== 'string') return warn('could not read the reviews file');
if (res.data.length > 600000) return warn('the reviews file is too big (600 KB max)');
let list;
try { list = JSON.parse(res.data); } catch (e) { return warn('the reviews file is not valid JSON'); }
if (!Array.isArray(list)) return warn('the reviews file must be a list');

const TOPICS = [
  ['crash', /crash|force.?close|hang|not open|band ho|बंद हो|क्रैश|క్రాష్|ఆగిపోతుంది|ఓపెన్ అవ్వ/i],
  ['login', /log.?in|sign.?in|otp|लॉगिन|లాగిన్/i],
  ['notifications', /notif|alert|reminder|सूचना|నోటిఫికేషన్/i],
  ['data', /\bdata\b|save|lost|delete|डेटा|सेव|డేటా|సేవ్/i],
  ['slow', /slow|lag(?!s)|loading|धीमा|स्लो|స్లో/i],
  ['payment', /pay|refund|upi|money|पैसे|డబ్బు/i],
];
const INJECT = /ignore (all |any )?(previous|prior|above)|system prompt|you are now|disregard .*instruction|<\/?(system|assistant)>/i;
const clean = (s) => Array.from(String(s).replace(/[\u0000-\u001f\u007f‎‏‪-‮⁦-⁩]/g, ' ').replace(/\s+/g, ' ').trim());
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const snip = (s) => { const c = clean(s); return esc(c.slice(0, 80).join('')) + (c.length > 80 ? '…' : ''); };

const fresh = [], inFile = new Set();
for (const r of list) {
  if (fresh.length >= 200) break;
  if (!r || typeof r !== 'object' || !APPS.includes(r.app)) continue;
  const id = typeof r.id === 'number' && Number.isInteger(r.id) && r.id > 0 ? String(r.id)
    : typeof r.id === 'string' && /^[A-Za-z0-9_.:-]{1,64}$/.test(r.id) ? r.id : '';
  if (!id || !Number.isInteger(r.rating) || r.rating < 1 || r.rating > 5) continue;
  if (typeof r.text !== 'string' || !r.text.trim() || r.text.length > 5000) continue;
  const key = r.app + ':' + id;
  if (inFile.has(key) || store.seen[key]) continue;
  inFile.add(key);
  const inject = INJECT.test(r.text);
  const topics = inject ? [] : TOPICS.filter(([, re]) => re.test(r.text)).map(([n]) => n);
  fresh.push({ key, app: r.app, rating: r.rating, text: r.text, inject, topics });
}
for (const f of fresh) store.seen[f.key] = now;
const keys = Object.keys(store.seen);
if (keys.length > 5000) keys.sort((a, b) => store.seen[a] - store.seen[b]).slice(0, keys.length - 5000).forEach((k) => delete store.seen[k]);
if (!fresh.length) return [];

const per = {}, clusters = {};
for (const f of fresh) {
  const p = per[f.app] = per[f.app] || { n: 0, sum: 0 };
  p.n++; p.sum += f.rating;
  if (f.rating <= 3) for (const t of f.topics) clusters[f.app + ' · ' + t] = (clusters[f.app + ' · ' + t] || 0) + 1;
}
const low = fresh.filter((f) => f.rating <= 2).sort((a, b) => a.rating - b.rating || a.app.localeCompare(b.app));
const lines = [`📱 <b>App reviews: ${fresh.length} new review${fresh.length > 1 ? 's' : ''}</b>`];
for (const a of APPS) if (per[a]) lines.push(`${a}: ${per[a].n} new, avg ${(Math.round(per[a].sum / per[a].n * 10) / 10).toFixed(1)}★`);
const rep = Object.entries(clusters).filter(([, n]) => n >= 2).sort((a, b) => b[1] - a[1]).slice(0, 3);
for (const [k, n] of rep) lines.push(`🔁 ${k} ×${n}: same problem more than once, worth a fix`);
for (const f of low.slice(0, 8)) lines.push(f.inject
  ? `🔴 ${f.app} · ★${f.rating} · ⚠️ looks like an instruction, not a review (text not shown)`
  : `${f.rating === 1 ? '🔴' : '🟠'} ${f.app} · ★${f.rating} · ${f.topics.join(', ') || 'other'}: "${snip(f.text)}"`);
if (low.length > 8) lines.push(`…and ${low.length - 8} more ★1–2 reviews in the file.`);
if (!low.length) lines.push('No ★1–2 reviews. 👍');
lines.push('Reply in the Play Console; bugs go to the b2 roadmap.');
return out(lines.join('\n'));"""

nodes = [
    {"id": "r1", "name": "Every day 09:40 IST", "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [0, 0],
     "parameters": {"rule": {"interval": [{"triggerAtHour": 9, "triggerAtMinute": 40}]}}},
    {"id": "r2", "name": "Read reviews (repo file)", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [220, 0],
     "alwaysOutputData": True, "onError": "continueRegularOutput", "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000,
     "parameters": {"url": URL, "options": {"timeout": 10000, "response": {"response": {"responseFormat": "text"}}}}},
    {"id": "r3", "name": "Watch reviews", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [440, 0],
     "executeOnce": True, "parameters": {"jsCode": WATCH}},
    {"id": "r4", "name": "Tell Akhil (private)", "type": "n8n-nodes-base.telegram", "typeVersion": 1.2, "position": [660, 0],
     "parameters": {"chatId": "1905524851", "text": "={{ $json.text }}",
                    "additionalFields": {"parse_mode": "HTML", "appendAttribution": False, "disable_web_page_preview": True}},
     "credentials": {"telegramApi": {"id": "", "name": "Kalpa Telegram"}}},
]
order = [n["name"] for n in nodes]
wf = {"name": "b2 · App store-review watcher (A242)", "active": False,
      "settings": {"executionOrder": "v1", "timezone": "Asia/Kolkata"}, "nodes": nodes,
      "connections": {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}}
(HERE / "b2-review-watcher.json").write_text(json.dumps(wf, indent=1, ensure_ascii=False) + "\n")
print("wrote b2-review-watcher.json")
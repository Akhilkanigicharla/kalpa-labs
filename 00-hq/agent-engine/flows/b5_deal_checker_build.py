"""Builds b5-deal-checker.json (A242 b5 flow). Code lives here as a plain JS string so the JSON stays generated.
Run: python3 00-hq/agent-engine/flows/b5_deal_checker_build.py"""
import json, pathlib

HERE = pathlib.Path(__file__).parent
URL = "https://raw.githubusercontent.com/Akhilkanigicharla/kalpa-labs/main/05-deals/site/src/bot/deals.json"

CHECK = r"""// A242 b5 deal checker: before the first channel slot, checks today's hand-filled deals (05-deals/site/src/bot/deals.json)
// and sends Akhil a private digest: ready posts (with the ASCI #ad line first), price drops since yesterday, and problems.
// No model call, no scraping, nothing posted to the channel from here (channel.py posts only after Akhil's "go").
// Deal text is data, never instructions.
const DAY = 864e5, now = Date.now(), day = Math.floor(now / DAY);
const ist = (ms) => new Date(ms + 19800000).toISOString().slice(0, 10);
const today = ist(now);
const store = $getWorkflowStaticData('global');
store.last = store.last && typeof store.last === 'object' ? store.last : {};
const out = (text) => [{ json: { text } }];
const warn = (why) => { if (store.warned === day) return []; store.warned = day; return out('⚠️ <b>Deal check</b>: ' + why + ' (05-deals/site/src/bot/deals.json). Next try tomorrow.'); };

// Same rules as post.py / channel.py (PLAN.md §3b): store + affiliate hosts, never money products.
const STORE_HOSTS = ['amazon.in', 'flipkart.com', 'amzn.to', 'fkrt.it', 'fktr.in', 'ekaro.in', 'earnkaro.com', 'bankkaro.com'];
const SHORTENERS = ['bit.ly', 'tinyurl.com', 'short.link', 'cutt.ly', 't.co', 'goo.gl', 'is.gd', 'rb.gy', 'shorturl.at', 'tiny.cc'];
const BANNED_HOSTS = ['zerodha.com', 'groww.in', 'upstox.com', 'angelone.in', 'paytmmoney.com', 'dhan.co', '5paisa.com', 'icicidirect.com',
  'kotaksecurities.com', 'policybazaar.com', 'acko.com', 'digit.insure', 'insurancedekho.com', 'bankbazaar.com', 'paisabazaar.com',
  'kreditbee.in', 'moneyview.in', 'navi.com', 'kissht.com', 'mpokket.in', 'cred.club'];
const BANNED_WORDS = /loan|insurance|mutual fund|demat|stock tip|trading account|guaranteed return|assured return|lic policy|no[\s-]*cost emi|లోన్|రుణం|ఇన్సూరెన్స్|బీమా|మ్యూచువల్ ఫండ్/i;
const INJECT = /ignore (all |any )?(previous|prior|above)|system prompt|you are now|disregard .*instruction|<\/?(system|assistant)>/i;
const on = (h, list) => list.some((x) => h === x || h.endsWith('.' + x));

// ASCI check for one post (K127 cases): #ad as its own tag, in the first 2 lines, before any other hashtag; one link on an allowed host.
const adCheck = (text, hosts) => {
  const t = String(text || ''), top = t.split('\n').slice(0, 2).join('\n');
  const tags = [...t.matchAll(/(^|[\s(])#([\p{L}\p{N}_]+)/gu)].map((m) => m[2].toLowerCase());
  if (!tags.includes('ad')) return { ok: false, why: tags.some((x) => /^(sponsored|paid|collab|partner)/.test(x)) ? '#sponsored-style tag, ASCI needs "#ad"' : 'no #ad disclosure' };
  if (tags[0] !== 'ad' || !/(^|[\s(])#ad(?![\p{L}\p{N}_])/iu.test(top)) return { ok: false, why: '#ad is buried: put it first, before other hashtags, in the first 2 lines' };
  const links = [...t.matchAll(/(?:https?:\/\/)?((?:[a-z0-9-]+\.)+[a-z]{2,})(?:\/[^\s<>"]*)?/gi)].map((m) => m[1].toLowerCase());
  if (!links.length) return { ok: false, why: 'no link to the deal' };
  for (const h of links) {
    if (on(h, BANNED_HOSTS)) return { ok: false, why: 'money-product link (' + h + ') is never promoted' };
    if (!on(h, hosts)) return { ok: false, why: (on(h, SHORTENERS) ? 'unknown short link (' : 'link not on a known store (') + h + ')' };
  }
  if (BANNED_WORDS.test(t)) return { ok: false, why: 'loan / insurance / investment / no-cost EMI words are not allowed' };
  return { ok: true, why: '' };
};
if (typeof module === 'object' && module && module.k127) { module.adCheck = adCheck; return []; }

const res = ($('Read deals (repo file)').first() || {}).json || {};
if (res.error || typeof res.data !== 'string') return warn('could not read the deals file');
if (res.data.length > 600000) return warn('the deals file is too big (600 KB max)');
let doc;
try { doc = JSON.parse(res.data); } catch (e) { return warn('the deals file is not valid JSON'); }
const list = doc && Array.isArray(doc.deals) ? doc.deals : null;
if (!list) return warn('the deals file needs a "deals" list');

const clean = (s) => Array.from(String(s || '').replace(/[\u0000-\u001f\u007f‎‏‪-‮⁦-⁩]/g, ' ').replace(/\s+/g, ' ').trim());
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const cut = (s, n) => { const c = clean(s); return esc(c.slice(0, n).join('')) + (c.length > n ? '…' : ''); };
const rs = (n) => '₹' + Math.round(n).toLocaleString('en-IN');
const asOfMs = (s) => /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(String(s || '')) ? Date.parse(s.replace(' ', 'T') + ':00+05:30') : NaN;

const ready = [], drops = [], flags = [];
let n = 0, seen = 0;
for (const d of list) {
  if (++n > 200) { flags.push('more than 200 deals: only the first 200 read'); break; }
  if (!d || typeof d !== 'object' || typeof d.id !== 'string' || !/^[a-z0-9-]{1,60}$/.test(d.id)) continue;
  if (d.kind !== 'product') continue; // card offers have their own RBI gate in channel.py
  if (d.date && d.date !== today) continue;
  if (d.valid_until && String(d.valid_until) < today) continue;
  seen++;
  const tag = d.sample ? ' (sample)' : '', id = esc(d.id) + tag;
  if ([d.title_te, d.note_te, d.coupon, d.store].some((x) => INJECT.test(String(x || '')))) { flags.push(id + ': text looks like an instruction, skipped'); continue; }
  const price = Number(d.price);
  if (!Number.isFinite(price) || price <= 0 || price > 1e7) { flags.push(id + ': price missing or not a number'); continue; }
  const at = asOfMs(d.price_as_of);
  if (isNaN(at)) { flags.push(id + ': price_as_of must be "YYYY-MM-DD HH:MM" (IST)'); continue; }
  if (now - at > DAY) { flags.push(id + ': price is older than 24 h, re-check it on the store page'); continue; }
  if (!/^https:\/\//i.test(String(d.link || ''))) { flags.push(id + ': link must start with https://'); continue; }
  const post = ['#ad · affiliate link / అనుబంధ లింక్', cut(d.title_te || d.id, 90), `${rs(price)} (as of ${esc(d.price_as_of)}, may change / ధర మారవచ్చు)`, String(d.link)].join('\n');
  const c = adCheck(post + ' ' + clean(d.note_te).join(''), STORE_HOSTS);
  if (!c.ok) { flags.push(id + ': ' + c.why); continue; }
  // price vs our own log (own-log or an https page, last 90 days): a "deal" above the 90-day low is called out, never hidden.
  const hist = (Array.isArray(d.history) ? d.history : []).filter((h) => h && /^\d{4}-\d{2}-\d{2}$/.test(String(h.date)) && Number(h.price) > 0
    && Date.parse(h.date) >= now - 90 * DAY && h.date <= today).map((h) => Number(h.price));
  let note = 'no price history yet';
  if (hist.length >= 3) { const low = Math.min(...hist); note = price < low ? `lowest in 90 days (was ${rs(low)})` : price === low ? 'same as the 90-day low' : `⚠️ ${rs(price - low)} above the 90-day low ${rs(low)}`; }
  const prev = store.last[d.id];
  if (prev && prev.price > price && prev.day < day) drops.push(`📉 <b>${cut(d.title_te || d.id, 60)}</b>${tag}: ${rs(prev.price)} → <b>${rs(price)}</b>`);
  store.last[d.id] = { price, day };
  ready.push(`✅ <b>${cut(d.title_te || d.id, 60)}</b>${tag} · ${rs(price)} · ${note}`);
}
const ks = Object.keys(store.last);
if (ks.length > 2000) ks.sort((a, b) => store.last[a].day - store.last[b].day).slice(0, ks.length - 2000).forEach((k) => delete store.last[k]);

if (!seen) return [];
const lines = [`🛍️ <b>Deal check ${today}: ${ready.length} ready, ${flags.length} need a fix</b>`];
for (const x of drops.slice(0, 5)) lines.push(x);
for (const x of ready.slice(0, 8)) lines.push(x);
if (ready.length > 8) lines.push(`…and ${ready.length - 8} more ready.`);
for (const f of [...new Set(flags)].slice(0, 8)) lines.push('⚠️ ' + f);
lines.push('Nothing was posted. Every post starts with "#ad · affiliate link"; the channel poster sends only after your go.');
return out(lines.join('\n'));"""

nodes = [
    {"id": "f1", "name": "Every day 08:20 IST", "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [0, 0],
     "parameters": {"rule": {"interval": [{"triggerAtHour": 8, "triggerAtMinute": 20}]}}},
    {"id": "f2", "name": "Read deals (repo file)", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [220, 0],
     "alwaysOutputData": True, "onError": "continueRegularOutput", "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000,
     "parameters": {"url": URL, "options": {"timeout": 10000, "response": {"response": {"responseFormat": "text"}}}}},
    {"id": "f3", "name": "Check deals + #ad", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [440, 0],
     "executeOnce": True, "parameters": {"jsCode": CHECK}},
    {"id": "f4", "name": "Tell Akhil (private)", "type": "n8n-nodes-base.telegram", "typeVersion": 1.2, "position": [660, 0],
     "parameters": {"chatId": "1905524851", "text": "={{ $json.text }}",
                    "additionalFields": {"parse_mode": "HTML", "appendAttribution": False, "disable_web_page_preview": True}},
     "credentials": {"telegramApi": {"id": "", "name": "Kalpa Telegram"}}},
]
order = [n["name"] for n in nodes]
wf = {"name": "b5 · Deal check + #ad gate (A242)", "active": False,
      "settings": {"executionOrder": "v1", "timezone": "Asia/Kolkata"}, "nodes": nodes,
      "connections": {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}}
(HERE / "b5-deal-checker.json").write_text(json.dumps(wf, indent=1, ensure_ascii=False) + "\n")
print("wrote b5-deal-checker.json")
"""Builds b7-paper-monitor.json (A242 b7 flow). Code lives here as plain JS strings so the JSON stays generated.
Run: python3 00-hq/agent-engine/flows/b7_paper_monitor_build.py"""
import json, pathlib, re
HERE = pathlib.Path(__file__).parent
RAW = "https://raw.githubusercontent.com/Akhilkanigicharla/kalpa-labs/main/07-trading/paper/"
RISK = (HERE / "../../../07-trading/src/risk.py").read_text()
def limits(name):  # the paper bot's own limits, read from risk.py so the monitor never drifts from the bot
    body = re.search(name + r" = \{(.*?)\n\}", RISK, re.S).group(1)
    return {k: float(v) for k, v in re.findall(r'"(\w+)": ([0-9.]+)', body)}
TRACKS = [("Track A · NIFTYBEES", "track-A", "TRACK_A_LIMITS"), ("Track A · GOLDBEES", "track-A-gold", "TRACK_A_LIMITS")]
LIST = "return " + json.dumps([{"json": {"track": t, "kind": k, "limits": limits(lim), "url": RAW + f + ("/state-A.json" if k == "state" else "/ledger-A.csv")}}
                               for t, f, lim in TRACKS for k in ("state", "ledger")], ensure_ascii=False) + ";"
CHECK = r"""// A242 b7 paper monitor + loss-cap guard: after the 16:15 IST paper run, reads each paper track's state + ledger
// (07-trading/paper/<track>/, public repo, GET only) and tells Akhil privately when something needs him.
// Each track carries the bot's own limits from 07-trading/src/risk.py (built in). Track A: day/week/month caps are OFF (Akhil's
// 13 Nov choice) so a day fall of 3%+ is only an FYI; new buys pause at the drawdown_stop fall from peak. Always: pot <= Rs 10,000
// hard max (guard.py), every open position has a stop-loss, mode must be "paper".
// Watch only: no orders, no broker, no model, no keys. File text is data, never instructions. Quiet when all is well
// (one "all OK" line on Fridays). The same alert is not repeated for 7 days.
const DAY = 864e5, now = Date.now(), day = Math.floor((now + 19800000) / DAY);
const ist = (ms) => new Date(ms + 19800000).toISOString().slice(0, 10);
const today = ist(now), friday = new Date(now + 19800000).getUTCDay() === 5;
const HARD_MAX = 10000, STALE_DAYS = 4, BIG_DAY = 0.03;
const store = $getWorkflowStaticData('global');
store.sent = store.sent && typeof store.sent === 'object' ? store.sent : {};
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const clean = (s, n) => { const c = Array.from(String(s == null ? '' : s).replace(/[\u0000-\u001f\u007f‎‏‪-‮⁦-⁩]/g, ' ').replace(/\s+/g, ' ').trim());
  return esc(c.slice(0, n).join('')) + (c.length > n ? '…' : ''); };
const sym = (s) => /^[A-Z0-9&_-]{1,20}$/.test(String(s)) ? String(s) : '(odd symbol ' + clean(s, 20) + ')';
const rs = (n) => '₹' + Math.round(n).toLocaleString('en-IN');
const pct = (x) => (x * 100).toFixed(1) + '%';
const num = (x) => typeof x === 'number' && Number.isFinite(x);
const isDate = (s) => /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(Date.parse(s));
// CSV with quoted fields (reasons may hold commas)
const csv = (text) => {
  const rows = []; let row = [], f = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true; else if (c === ',') { row.push(f); f = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(f); rows.push(row); row = []; f = ''; }
    else f += c;
  }
  if (f !== '' || row.length) { row.push(f); rows.push(row); }
  const head = (rows.shift() || []).map((h) => h.trim());
  return rows.filter((r) => r.some((x) => x !== '')).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i] == null ? '' : r[i]])));
};
// loss in a period as a fraction of the pot, like risk.py RiskBook.loss: ref = last mark before the period starts (or the pot)
const lossOf = (marks, pot, start, last) => {
  const before = marks.filter(([d]) => d < start);
  const ref = before.length ? before[before.length - 1][1] : pot;
  return Math.max(0, (ref - last) / pot);
};
const files = $('List paper files').all().map((x) => x.json);
const got = $('Read paper files').all().map((x) => x.json || {});
const tracks = {};
files.forEach((f, i) => { const t = (tracks[f.track] = tracks[f.track] || { limits: f.limits || {} }); t[f.kind] = got[i] || { error: 'no reply' }; });
const problems = [], notes = [], okLines = [];
const add = (list, key, text) => { if (store.sent[key] != null && day - store.sent[key] < 7) return; store.sent[key] = day; list.push(text); };
for (const [name, t] of Object.entries(tracks)) {
  const tn = esc(name), s = t.state || {}, l = t.ledger || {};
  const lim = (k, d) => num(t.limits[k]) && t.limits[k] > 0 ? t.limits[k] : d;
  const CAPS = { day: lim('daily_loss', 0.01), week: lim('weekly_loss', 0.02), month: lim('monthly_loss', 0.04) }, PAUSE = lim('drawdown_stop', 0.10), WARN_DD = PAUSE * 0.75;
  if (s.error || typeof s.data !== 'string') { add(problems, name + ':nostate:' + today, `⛔ <b>${tn}</b>: could not read state-A.json (file missing or GitHub down). Check the "paper-trade" GitHub Action.`); continue; }
  if (s.data.length > 2e6) { add(problems, name + ':big', `⛔ <b>${tn}</b>: state-A.json is over 2 MB, not read.`); continue; }
  let st;
  try { st = JSON.parse(s.data); } catch (e) { add(problems, name + ':badjson:' + today, `⛔ <b>${tn}</b>: state-A.json is not valid JSON. The next paper run may fail.`); continue; }
  if (!st || typeof st !== 'object' || !st.broker || typeof st.broker !== 'object') { add(problems, name + ':shape', `⛔ <b>${tn}</b>: state-A.json has no "broker" section.`); continue; }
  const pot = st.capital;
  if (!num(pot) || pot <= 0 || pot > HARD_MAX) add(problems, name + ':pot:' + pot, `⛔ <b>${tn}</b>: pot ${esc(pot)} is outside ₹1–${rs(HARD_MAX)} (hard max in guard.py).`);
  const P = num(pot) && pot > 0 ? pot : 5000;
  const cash = st.broker.cash;
  if (!num(cash) || cash < -1) add(problems, name + ':cash', `⛔ <b>${tn}</b>: cash is ${num(cash) ? rs(cash) : 'not a number'}; the paper broker should never go below ₹0.`);
  const pos = st.broker.positions && typeof st.broker.positions === 'object' ? st.broker.positions : {};
  const cost = st.broker.avg_cost && typeof st.broker.avg_cost === 'object' ? st.broker.avg_cost : {};
  const stops = st.stops && typeof st.stops === 'object' ? st.stops : {};
  let held = 0, open = 0;
  for (const [k, q] of Object.entries(pos).slice(0, 50)) {
    const sy = sym(k);
    if (!num(q) || q < 0 || Math.floor(q) !== q) { add(problems, name + ':qty:' + k, `⛔ <b>${tn}</b>: ${sy} quantity ${clean(q, 12)} is not a whole number.`); continue; }
    if (!q) continue;
    open++;
    const c = cost[k];
    if (!num(c) || c <= 0) add(problems, name + ':cost:' + k, `⛔ <b>${tn}</b>: ${sy} has no buy price.`); else held += q * c;
    const sl = stops[k];
    if (!num(sl) || sl <= 0) add(problems, name + ':nostop:' + k, `⛔ <b>${tn}</b>: ${sy} is open with no stop-loss. The bot must set one before the next run.`);
  }
  if (held > P + 1) add(problems, name + ':overpot:' + Math.round(held), `⛔ <b>${tn}</b>: positions cost ${rs(held)}, more than the ${rs(P)} pot.`);
  const marks = Object.entries(st.marks && typeof st.marks === 'object' ? st.marks : {}).filter(([d, v]) => isDate(d) && num(v) && v >= 0).sort((a, b) => a[0] < b[0] ? -1 : 1);
  if (!marks.length) { add(notes, name + ':nomarks', `ℹ️ <b>${tn}</b>: no daily values yet.`); continue; }
  const [lastDay, last] = marks[marks.length - 1];
  const age = Math.floor((Date.parse(today) - Date.parse(lastDay)) / DAY);
  if (age > STALE_DAYS) add(problems, name + ':stale:' + lastDay, `⛔ <b>${tn}</b>: no paper run since ${lastDay} (${age} days). Check the "paper-trade" GitHub Action.`);
  if (lastDay > today) add(problems, name + ':future:' + lastDay, `⛔ <b>${tn}</b>: a daily value is dated in the future (${lastDay}).`);
  const d = new Date(lastDay + 'T00:00:00Z'), dow = (d.getUTCDay() + 6) % 7;
  const weekStart = new Date(d - dow * DAY).toISOString().slice(0, 10), monthStart = lastDay.slice(0, 8) + '01';
  const L = { day: lossOf(marks, P, lastDay, last), week: lossOf(marks, P, weekStart, last), month: lossOf(marks, P, monthStart, last) };
  const what = { day: 'today', week: 'this week', month: 'the rest of this month' };
  const key = { day: lastDay, week: weekStart, month: monthStart };
  if (CAPS.day >= 1 && L.day >= BIG_DAY) add(notes, name + ':bigday:' + lastDay, `ℹ️ <b>${tn}</b>: fell ${pct(L.day)} today (${rs(L.day * P)}). Day/week/month caps are off for this track (your 13 Nov choice); the stop-loss and the ${pct(PAUSE)} pause still guard it.`);
  for (const p of ['month', 'week', 'day']) if (CAPS[p] < 1 && L[p] >= CAPS[p] - 1e-9) {
    add(notes, name + ':cap:' + p + ':' + key[p], `🛑 <b>${tn}</b>: ${p} loss ${pct(L[p])} reached the ${pct(CAPS[p])} cap (${rs(L[p] * P)} of ${rs(P)}). The bot makes no new buys ${what[p]}; holdings keep their stop-losses.`);
    break;
  }
  const peak = Math.max(P, ...marks.map((m) => m[1])), dd = Math.max(0, (peak - last) / peak);
  if (dd >= PAUSE - 1e-9) add(problems, name + ':pause:' + lastDay.slice(0, 7), `⛔ <b>${tn}</b>: down ${pct(dd)} from the ${rs(peak)} peak. New buys are paused (${pct(PAUSE)} rule) until you review it.`);
  else if (dd >= WARN_DD) add(notes, name + ':dd:' + lastDay.slice(0, 7), `⚠️ <b>${tn}</b>: down ${pct(dd)} from the peak; new buys pause at ${pct(PAUSE)}.`);
  // ledger: paper mode only, failed/rejected orders, the same order twice
  if (l.error || typeof l.data !== 'string') add(problems, name + ':noledger:' + today, `⛔ <b>${tn}</b>: could not read ledger-A.csv.`);
  else if (l.data.length > 5e6) add(problems, name + ':bigledger', `⛔ <b>${tn}</b>: ledger-A.csv is over 5 MB, not read.`);
  else {
    const rows = csv(l.data), recent = rows.filter((r) => isDate(r.asof) && Date.parse(today) - Date.parse(r.asof) <= 7 * DAY);
    const live = rows.filter((r) => r.mode && r.mode !== 'paper');
    if (live.length) add(problems, name + ':live:' + live.length, `🚨 <b>${tn}</b>: ${live.length} ledger row(s) not in paper mode ("${clean(live[0].mode, 20)}"). Live money needs your "go"; check now.`);
    const seen = {};
    for (const r of recent) {
      const ok = ['filled', 'no_change'].includes(r.status);
      if (!ok) add(problems, name + ':status:' + r.asof + ':' + r.symbol + ':' + r.side, `⛔ <b>${tn}</b>: ${r.asof} ${sym(r.symbol)} ${clean(r.side, 10)} → ${clean(r.status || 'no status', 20)}${r.reasons ? ' (' + clean(r.reasons, 80) + ')' : ''}.`);
      if (r.side && r.side !== 'hold') {
        const k = r.asof + '|' + r.symbol + '|' + r.side;
        if (seen[k]) add(problems, name + ':dup:' + k, `⛔ <b>${tn}</b>: the same ${clean(r.side, 10)} of ${sym(r.symbol)} for ${r.asof} is in the ledger twice. Do not resend; check the runner.`);
        seen[k] = 1;
      }
    }
  }
  const days = Array.isArray(st.paper_days) ? st.paper_days.length : 0;
  okLines.push(`${tn}: ${rs(last)} (${last >= P ? '+' : ''}${pct((last - P) / P)}), ${open} open, ${days}/90 paper days`);
}
for (const k of Object.keys(store.sent)) if (day - store.sent[k] > 40) delete store.sent[k];
if (!problems.length && !notes.length) {
  if (!friday || !okLines.length || store.okWeek === today) return [];
  store.okWeek = today;
  return [{ json: { text: ['✅ <b>b7 paper week</b>: all checks OK', ...okLines, 'Paper only. Own money only. Not advice.'].join('\n') } }];
}
const lines = [`📈 <b>b7 paper check ${today}</b>: ${problems.length} need you, ${notes.length} FYI`, ...problems.slice(0, 10), ...notes.slice(0, 6)];
if (problems.length > 10) lines.push(`…and ${problems.length - 10} more.`);
lines.push(...okLines, 'Watch only: this flow never places orders. Paper only. Not advice.');
return [{ json: { text: lines.join('\n') } }];"""
nodes = [
    {"id": "g1", "name": "Weekdays 16:45 IST", "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [0, 0],
     "parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "45 16 * * 1-5"}]}}},
    {"id": "g2", "name": "List paper files", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [220, 0],
     "parameters": {"jsCode": LIST}},
    {"id": "g3", "name": "Read paper files", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [440, 0],
     "alwaysOutputData": True, "onError": "continueRegularOutput", "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000,
     "parameters": {"url": "={{ $json.url }}", "options": {"timeout": 10000, "response": {"response": {"responseFormat": "text"}}}}},
    {"id": "g4", "name": "Check tracks + loss caps", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [660, 0],
     "executeOnce": True, "parameters": {"jsCode": CHECK}},
    {"id": "g5", "name": "Tell Akhil (private)", "type": "n8n-nodes-base.telegram", "typeVersion": 1.2, "position": [880, 0],
     "parameters": {"chatId": "1905524851", "text": "={{ $json.text }}",
                    "additionalFields": {"parse_mode": "HTML", "appendAttribution": False, "disable_web_page_preview": True}},
     "credentials": {"telegramApi": {"id": "", "name": "Kalpa Telegram"}}},
]
order = [n["name"] for n in nodes]
wf = {"name": "b7 · Paper-trade monitor + loss-cap guard (A242)", "active": False,
      "settings": {"executionOrder": "v1", "timezone": "Asia/Kolkata"}, "nodes": nodes,
      "connections": {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}}
(HERE / "b7-paper-monitor.json").write_text(json.dumps(wf, indent=1, ensure_ascii=False) + "\n")
print("wrote b7-paper-monitor.json")

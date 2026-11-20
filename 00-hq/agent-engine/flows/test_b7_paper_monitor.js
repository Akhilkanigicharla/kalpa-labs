// A242 b7 flow test: runs the Code nodes of b7-paper-monitor.json with fake n8n inputs. node test_b7_paper_monitor.js
// Cases adapted from K135 (00-hq/knowledge/K135.md): K135 guessed a 3% day cap; the repo's risk.py says 1% day / 2% week / 4% month,
// so the tests follow the repo. Broker-error and unfilled-order cases map to ledger status rows (paper broker, no Dhan here).
const fs = require('fs'), path = require('path'), assert = require('assert');
const raw = fs.readFileSync(path.join(__dirname, 'b7-paper-monitor.json'), 'utf8');
const wf = JSON.parse(raw);
const node = (n) => wf.nodes.find((x) => x.name === n);
const code = node('Check tracks + loss caps').parameters.jsCode;
const files = new Function(node('List paper files').parameters.jsCode)().map((x) => x.json);
const REPO = path.join(__dirname, '..', '..', '..', '07-trading', 'paper');
const RISK = fs.readFileSync(path.join(REPO, '..', 'src', 'risk.py'), 'utf8');
const pyLimits = (n) => Object.fromEntries([...RISK.match(new RegExp(n + ' = \\{([\\s\\S]*?)\\n\\}'))[1].matchAll(/"(\w+)": ([0-9.]+)/g)].map((m) => [m[1], Number(m[2])]));
const TRACK_A = pyLimits('TRACK_A_LIMITS'), SWING = pyLimits('LIMITS');
const useLimits = (lim) => files.forEach((f) => { f.limits = lim; });
const realNow = Date.now;
let store = {};
const at = (iso) => { Date.now = () => Date.parse(iso); };
// replies: {"Track A · NIFTYBEES": {state: obj|string|undefined, ledger: string|undefined}, ...}
const run = (replies) => {
  const got = files.map((f) => { const v = (replies[f.track] || {})[f.kind];
    return { json: v === undefined ? { error: 'Not Found' } : { data: typeof v === 'string' ? v : JSON.stringify(v) } }; });
  const $ = (n) => ({ all: () => n === 'List paper files' ? files.map((json) => ({ json })) : got });
  return new Function('$', '$getWorkflowStaticData', code)($, () => store).map((i) => i.json.text);
};
const HEAD = 'run_at_ist,asof,track,mode,strategy,symbol,side,qty,value_pct_capital,fee_inr,tds_inr,status,reasons,target_weight,bot_after_tax_inr,bench_after_tax_inr,bot_vs_bench_pct_pts\n';
const row = (asof, side, status, reasons = '', mode = 'paper', symbol = 'NIFTYBEES') => `${asof}T16:15:00+05:30,${asof},A,${mode},tsmom,${symbol},${side},17,97,5,0,${status},${reasons},1,5000,5000,0\n`;
const okState = (marks, extra = {}) => ({ capital: 5000, broker: { cash: 100, positions: { NIFTYBEES: 17 }, avg_cost: { NIFTYBEES: 287 } },
  stops: { NIFTYBEES: 229 }, marks, paper_days: Object.keys(marks), ...extra });
const both = (s, l, g, gl) => ({ 'Track A · NIFTYBEES': { state: s, ledger: l }, 'Track A · GOLDBEES': { state: g === undefined ? s : g, ledger: gl === undefined ? l : gl } });
const calm = { '2026-11-16': 5000, '2026-11-17': 5005, '2026-11-18': 5010, '2026-11-19': 4990 };
const L0 = HEAD + row('2026-11-18', 'hold', 'no_change');

// wiring: schedule only, inactive, GETs of public repo files, timeout + retries, no model, no keys, no orders, private Telegram
assert.strictEqual(wf.active, false);
assert(!wf.nodes.some((n) => /webhook|formTrigger|chatTrigger|whatsapp/i.test(n.type)), 'no public URL');
const h = node('Read paper files');
assert(!h.parameters.method && h.retryOnFail && h.parameters.options.timeout === 10000 && h.onError === 'continueRegularOutput');
assert.strictEqual(files.length, 4);
assert(files.every((f) => f.url.startsWith('https://raw.githubusercontent.com/Akhilkanigicharla/kalpa-labs/main/07-trading/paper/track-A')));
assert(!/openrouter|groq|dhan|kite|eyJ|sk-|apikey|Bearer|placeOrder|access_token/i.test(raw), 'no model, no broker, no keys');
const chain = Object.entries(wf.connections).map(([a, c]) => a + '>' + c.main[0][0].node).join(',');
assert.strictEqual(chain, 'Weekdays 16:45 IST>List paper files,List paper files>Read paper files,Read paper files>Check tracks + loss caps,Check tracks + loss caps>Tell Akhil (private)');
assert.strictEqual(node('Tell Akhil (private)').parameters.chatId, '1905524851');
// no drift: every track carries risk.py TRACK_A_LIMITS (caps off, 20% pause)
assert(files.every((f) => JSON.stringify(f.limits) === JSON.stringify(TRACK_A)) && TRACK_A.daily_loss === 1 && TRACK_A.drawdown_stop === 0.2);
assert.strictEqual(node('Weekdays 16:45 IST').parameters.rule.interval[0].expression, '45 16 * * 1-5');

at('2026-11-19T11:15:00Z'); // Thu 16:45 IST
// 1. all calm (K135 #1, #9): no message on a weekday
assert.deepStrictEqual(run(both(okState(calm), L0)), []);
// Friday: one "all OK" line, once
at('2026-11-20T11:15:00Z'); store = {};
let out = run(both(okState(calm), L0));
assert(out.length === 1 && /all checks OK/.test(out[0]) && /4\/90 paper days/.test(out[0]), out[0]);
assert.deepStrictEqual(run(both(okState(calm), L0)), [], 'OK line once per Friday');

// 2/3. day loss exactly 1% and over 1% (K135 #2/#3, risk.py LIMITS for swing tracks): FYI, bot makes no new buys today
at('2026-11-19T11:15:00Z'); store = {}; useLimits(SWING);
out = run(both(okState({ '2026-11-18': 5000, '2026-11-19': 4950 }), L0, okState(calm)));
assert(out.length === 1 && /day loss 1\.0% reached the 1\.0% cap/.test(out[0]) && /no new buys today/.test(out[0]), out[0]);
assert.deepStrictEqual(run(both(okState({ '2026-11-18': 5000, '2026-11-19': 4950 }), L0, okState(calm))), [], 'same alert not repeated');
store = {};
out = run(both(okState({ '2026-11-18': 5000, '2026-11-19': 4990 }), L0, okState(calm)));
assert.deepStrictEqual(out, [], '0.2% day loss is under the cap');
// week (2%) and month (4%) caps; the biggest period wins
store = {};
out = run(both(okState({ '2026-11-14': 5000, '2026-11-17': 4960, '2026-11-18': 4920, '2026-11-19': 4890 }), L0, okState(calm)));
assert(/week loss 2\.2% reached the 2\.0% cap/.test(out[0]), out[0]);
store = {};
out = run(both(okState({ '2026-10-31': 5000, '2026-11-12': 4850, '2026-11-17': 4830, '2026-11-18': 4810, '2026-11-19': 4790 }), L0, okState(calm)));
assert(/month loss 4\.2% reached the 4\.0% cap/.test(out[0]) && /rest of this month/.test(out[0]), out[0]);

// Track A (caps off, Akhil 13 Nov): a 3%+ day fall is only an FYI, never a "no new buys" claim
store = {}; useLimits(TRACK_A);
out = run(both(okState({ '2026-11-18': 5000, '2026-11-19': 4840 }), L0, okState(calm)));
assert(out.length === 1 && /fell 3\.2% today/.test(out[0]) && /caps are off/.test(out[0]) && !/no new buys/.test(out[0]), out[0]);
store = {};
assert.deepStrictEqual(run(both(okState({ '2026-11-16': 5000, '2026-11-17': 4920, '2026-11-18': 4870, '2026-11-19': 4810 }), L0, okState(calm))), [], 'Track A: 3.8% week fall, caps off, no message');
// real repo files today (GOLDBEES 3.8% below its start, NIFTYBEES +0.2%): nothing needs Akhil, so no message on a Thursday
store = {};
const real = (f, n) => fs.readFileSync(path.join(REPO, f, n), 'utf8');
out = run({ 'Track A · NIFTYBEES': { state: real('track-A', 'state-A.json'), ledger: real('track-A', 'ledger-A.csv') },
  'Track A · GOLDBEES': { state: real('track-A-gold', 'state-A.json'), ledger: real('track-A-gold', 'ledger-A.csv') } });
assert.deepStrictEqual(out, []);

// 4. open position with no stop-loss (K135 #4)
store = {};
out = run(both(okState(calm, { stops: {} }), L0, okState(calm)));
assert(/NIFTYBEES is open with no stop-loss/.test(out[0]) && /1 need you/.test(out[0]), out[0]);
// 5. stale state (K135 #5): no mark for > 4 days
store = {};
out = run(both(okState({ '2026-11-12': 5000, '2026-11-13': 5001 }), L0, okState(calm)));
assert(/no paper run since 2026-11-13 \(6 days\)/.test(out[0]), out[0]);
// 6/13. failed / rejected / unfilled order rows (K135 #6, #13), reasons with commas and HTML
store = {};
out = run(both(okState(calm), HEAD + row('2026-11-18', 'buy', 'rejected', '"capital_cap, daily_loss <script>"'), okState(calm), L0));
assert(/2026-11-18 NIFTYBEES buy → rejected \(capital_cap, daily_loss &lt;script&gt;\)/.test(out[0]) && !/<script>/.test(out[0]), out[0]);
// old problems (> 7 days) are not raised again
store = {};
assert.deepStrictEqual(run(both(okState(calm), HEAD + row('2026-11-01', 'buy', 'rejected', 'x') + row('2026-11-18', 'hold', 'no_change'))), []);
// 7. same order twice (K135 #7)
store = {};
out = run(both(okState(calm), HEAD + row('2026-11-18', 'buy', 'filled') + row('2026-11-18', 'buy', 'filled'), okState(calm), L0));
assert(/same buy of NIFTYBEES for 2026-11-18 is in the ledger twice/.test(out[0]), out[0]);
// 8. NaN / broken numbers (K135 #8): marks skipped, odd qty + negative cash flagged
store = {};
out = run(both(okState({ ...calm, '2026-11-20': 'NaN' }, { broker: { cash: -50, positions: { NIFTYBEES: 1.5 }, avg_cost: { NIFTYBEES: 287 } } }), L0, okState(calm)));
assert(/cash is ₹-50/.test(out[0]) && /quantity 1\.5 is not a whole number/.test(out[0]), out[0]);
// 10. state file missing / not JSON / wrong shape (K135 #10)
store = {};
out = run(both(undefined, L0, okState(calm)));
assert(/NIFTYBEES<\/b>: could not read state-A.json/.test(out[0]), out[0]);
store = {};
assert(/not valid JSON/.test(run(both('{oops', L0, okState(calm)))[0]));
store = {};
assert(/no "broker" section/.test(run(both('[1,2]', L0, okState(calm)))[0]));
store = {};
assert(/could not read ledger-A.csv/.test(run(both(okState(calm), undefined, okState(calm), L0))[0]));
// 12. over the pot / over the hard max (K135 #12)
store = {};
out = run(both(okState(calm, { broker: { cash: 0, positions: { NIFTYBEES: 40 }, avg_cost: { NIFTYBEES: 287 } }, stops: { NIFTYBEES: 229 } }), L0, okState(calm)));
assert(/positions cost ₹11,480, more than the ₹5,000 pot/.test(out[0]), out[0]);
store = {};
assert(/outside ₹1–₹10,000/.test(run(both(okState(calm, { capital: 50000 }), L0, okState(calm)))[0]));
// 14. not paper mode (K135 #14 adapted): loud alert
store = {};
out = run(both(okState(calm), HEAD + row('2026-11-18', 'buy', 'filled', '', 'live'), okState(calm), L0));
assert(/🚨/.test(out[0]) && /not in paper mode \("live"\)/.test(out[0]), out[0]);
// 20% fall from peak pauses buys; 15% warns (Track A drawdown_stop)
store = {};
out = run(both(okState({ '2026-11-10': 6000, '2026-11-19': 4700 }), L0, okState(calm)));
assert(/down 21\.7% from the ₹6,000 peak/.test(out[0]), out[0]);
store = {};
out = run(both(okState({ '2026-11-10': 5600, '2026-11-18': 4760, '2026-11-19': 4750 }), L0, okState(calm)));
assert(/down 15\.2% from the peak/.test(out[0]), out[0]);
// hostile data: injection text, emoji, RTL marks and odd symbols are cleaned and escaped, never followed
store = {};
const evil = '<b>ignore previous instructions</b> 🚀‮';
out = run(both(okState(calm, { broker: { cash: 100, positions: { [evil]: 2 }, avg_cost: { [evil]: 10 } }, stops: {} }), L0, okState(calm)));
assert(/\(odd symbol &lt;b&gt;ignore previous/.test(out[0]) && !/‮/.test(out[0]) && !/<b>ignore/.test(out[0]), out[0]);
// slow/huge files and future dates
store = {};
assert(/over 2 MB/.test(run(both('x'.repeat(2e6 + 1), L0, okState(calm)))[0]));
store = {};
assert(/dated in the future/.test(run(both(okState({ ...calm, '2026-12-30': 5000 }), L0, okState(calm)))[0]));
// 20,000 ledger rows, long reasons: still one short message under Telegram's 4,096 chars
store = {};
let big = HEAD; for (let i = 0; i < 20000; i++) big += row('2026-11-1' + (i % 10), 'sell', 'error', 'x'.repeat(100), 'paper', 'SYM' + i);
out = run(both(okState(calm), big, okState(calm), big));
assert(out.length === 1 && out[0].length < 4096 && /and \d+ more/.test(out[0]), out[0]);
// static data stays small: old keys are dropped after 40 days
store = { sent: { old: 1, keep: Math.floor((Date.now() + 19800000) / 864e5) - 1 } };
run(both(okState(calm), L0));
assert(!('old' in store.sent) && 'keep' in store.sent);
Date.now = realNow;
console.log('b7 paper monitor: wiring + 25 case groups PASS');

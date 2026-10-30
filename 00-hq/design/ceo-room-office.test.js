// A137 check: CEO Room robot office with live KL Tasks jobs.
// Runs the real page (ceo-room-dashboard.html + ceo-room-office.js/.css) in Chromium with a small
// stand-in for the dashboard runtime (dash.data/calc/loader/onData), at 390 px light + dark and reduced motion.
// Usage: D3=/path/to/d3.min.js node 00-hq/design/ceo-room-office.test.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const { chromium } = require('playwright');
const dir = __dirname;
const d3 = fs.readFileSync(process.env.D3 || require.resolve('d3/dist/d3.min.js'), 'utf8');
const css = fs.readFileSync(path.join(dir, 'ceo-room-office.css'), 'utf8');
const js = fs.readFileSync(path.join(dir, 'ceo-room-office.js'), 'utf8');
const page0 = fs.readFileSync(path.join(dir, 'ceo-room-dashboard.html'), 'utf8')
  .replace('<link rel="stylesheet" href="office.css">', () => `<style>${css}</style>`)
  .replace('<script src="office.js"></script>', () => `<script>${js}</script>`);

// ---- fixtures shaped like the real n8n answers (30 Oct 2026) ----
const NOW = Date.now(), ago = m => new Date(NOW - m * 60000).toISOString();
const istDay = t => new Date(new Date(t).getTime() + 19800000).toISOString().slice(0, 10);
const AG = [['Kalpa','HQ','NVIDIA','nvidia/nemotron-3-nano-omni'],['Vigil','HQ','Groq','openai/gpt-oss-120b'],['Probe','HQ','Groq','openai/gpt-oss-20b'],
  ['Scout','b1','NVIDIA','nvidia/nemotron-3-nano-omni'],['Chitti','b1','Groq','qwen/qwen3.8-27b'],['Forge','HQ','Groq','openai/gpt-oss-20b'],
  ['Echo','HQ','NVIDIA','nvidia/nemotron-3-nano-omni'],['Adi','Marketing','NVIDIA','nvidia/nemotron-3-nano-omni'],['Quant','b7','Groq','openai/gpt-oss-120b'],
  ['Deal','b5','NVIDIA','nvidia/nemotron-3-nano-omni'],['Plug','b4','Groq','qwen/qwen3.8-27b'],['Ledger','b6','Groq','openai/gpt-oss-20b']];
const roster = AG.map(([agent, world, host, model]) => ({ agent, world, host, model, role: agent + ' role', job: 'Does ' + agent + ' work' }));
const agents = AG.map(([n], i) => ({ id: 'id' + i, name: n + ' — agent', published: i % 2 === 0, updatedAt: ago(600) }));
const owners = ['Scout','Chitti','Forge','Echo','Adi','Deal','Plug','Customer','Council','Competitor Watch','Offer'];
const ST = ['review','rejected','todo','review','todo'];
const tasks = Array.from({ length: 100 }, (_, i) => ({ id: 300 - i, owner_agent: owners[i % owners.length], stream: 'b1', status: ST[i % ST.length], priority: 'P0',
  title: `(Max 350 words) Job ${300 - i}: a long real-looking ask for ${owners[i % owners.length]} about salons in Hyderabad and their pricing pages`,
  output_summary: i % 5 === 2 || i % 5 === 4 ? null : `VIGIL: ${ST[i % ST.length] === 'rejected' ? 'FAIL' : 'PASS'}: reason ${i}.\nDELIVERABLE: <img src=x onerror=window.__xss=1> text`,
  needs_ceo: false, created_by: 'Claude', createdAt: ago(i * 25 + 5), updatedAt: ago(i * 25 + 5) }));
// variant: the real KL Tasks answer saved from n8n (REAL=/path/to/answer.json)
if (process.env.REAL) { const real = JSON.parse(fs.readFileSync(process.env.REAL, 'utf8')).rows; tasks.splice(0, tasks.length, ...real); }
// variant: a council seat filed 10 minutes ago -> table must light up
if (process.env.LIT_CASE) { tasks[1].owner_agent = 'Council'; }
const known = new Set(AG.map(a => a[0])), seatTimes = tasks.filter(t => !known.has(t.owner_agent)).map(t => +new Date(t.updatedAt));
const LIT = new Date(NOW + 19800000).getUTCHours() === 6 || NOW - Math.max(...seatTimes) < 36e5;
const fx = { kl_tasks: { rows: tasks, count: 201 }, kl_queue: { rows: [tasks[2]], count: 112 }, roster, agents,
  roadmap: [{ id: 'A137', queue: 'Agents', status: 'to do', world: 'HQ', title: 'Robot office' }], workers: [],
  n8n_workflows: [], n8n_runs: [], or_usage: [], game_stats: [], game_worlds: [] };
// expected numbers, computed independently of the page
const today = istDay(process.env.REAL ? tasks[0].updatedAt : NOW), todays = tasks.filter(t => istDay(t.updatedAt) === today);
const expect = { queue: '112', passed: String(todays.filter(t => t.status === 'review').length), redo: String(todays.filter(t => t.status === 'rejected').length), models: '4' };

const runtime = `window.__fx=${JSON.stringify(fx)};(function(){const calcs={},loaders={},subs=[];
window.dash={data(id){if(calcs[id]){const c=calcs[id];const ins=c.inputs.map(i=>dash.data(i));if(ins.some(x=>x.status!=='ok'))return{status:'loading',data:[]};return{status:'ok',data:c.fn(...ins.map(x=>x.data))};}
let a=__fx[id];if(a===undefined)return{status:'missing',data:[]};if(loaders[id])a=loaders[id].fn({answer:a});else if(a&&a.rows)a=a.rows;return{status:'ok',data:a};},
onData(fn){subs.push(fn);fn();},calc(id,o){if(calcs[id])throw new Error('calc twice '+id);calcs[id]=o;},loader(id,o){loaders[id]=o;},setLink(){},params(){return{}},setParams(){},refresh(){},colors:[]};})();`;
const shell = scheme => `<!doctype html><html><head><meta name=viewport content="width=device-width"><style>
:root{color-scheme:${scheme};--color-fg:light-dark(#1f1e1b,#ece9e1);--color-fg-muted:light-dark(#6b675e,#a8a397);--color-bg:light-dark(#faf8f3,#191815);--color-panel:light-dark(#fff,#23221e);
--color-border-line:light-dark(#e6e1d6,#3a3833);--color-ok:light-dark(#2f7d3a,#6fd08f);--color-warn:light-dark(#9c700e,#e8b64a);--color-bad:light-dark(#b3261e,#ff8a80);
--font-anthropic-sans:system-ui;--font-anthropic-serif:Georgia;--cds-gap-sm:8px;--cds-gap-md:12px;--cds-gap-lg:18px;--cds-pad-sm:8px;--cds-pad-md:12px;--cds-pad-lg:16px;
--cds-font-size-caption:12px;--cds-font-size-body:14px;--cds-font-size-heading:17px;--cds-font-weight-medium:550;--cds-chart-grid:#8883;--cds-chart-axis:#8886;--cds-ease-out:ease-out;--cds-dur-slow:.3s}
body{margin:0;background:var(--color-bg)}</style><script>${d3}</script><script>${runtime}</script></head><body><div id="dash-root">${page0}</div></body></html>`;

(async () => {
  const browser = await chromium.launch(); let fails = 0;
  for (const [scheme, motion] of [['light', 'no-preference'], ['dark', 'no-preference'], ['light', 'reduce']]) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: scheme, reducedMotion: motion });
    const p = await ctx.newPage(), errors = [];
    p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); }); p.on('pageerror', e => errors.push(String(e)));
    await p.setContent(shell(scheme)); await p.waitForTimeout(400);
    const name = `${scheme}/${motion}`;
    try {
      const got = await p.evaluate(() => ({
        queue: document.querySelector('[data-where="metric=queue"]').textContent, passed: document.getElementById('oc-passed').textContent,
        redo: document.getElementById('oc-redo').textContent, models: document.querySelector('[data-where="metric=models"]').textContent,
        bubbles: [...document.querySelectorAll('#scene g.bubble[data-agent]')].map(b => [b.dataset.agent, b.querySelector('text').textContent, getComputedStyle(b).opacity]),
        badges: document.querySelectorAll('#scene [data-kx] circle').length, couriers: document.querySelectorAll('#scene animateMotion').length,
        council: !!document.getElementById('council-table'), lit: document.getElementById('council-table')?.classList.contains('lit'),
        seats: document.querySelectorAll('#council-table g.bot').length, overflowX: document.documentElement.scrollWidth > innerWidth + 1 }));
      for (const k of ['queue', 'passed', 'redo', 'models']) assert.strictEqual(got[k], expect[k], `${k}: ${got[k]} != ${expect[k]}`);
      const latest = {}; tasks.forEach(t => { if (!latest[t.owner_agent] || t.updatedAt > latest[t.owner_agent].updatedAt) latest[t.owner_agent] = t; });
      for (const [a, text] of got.bubbles) if (latest[a]) assert.ok(text.includes(latest[a].title.replace(/^\([^)]*\)\s*/, '').slice(0, 20)), `bubble ${a}: ${text}`);
      assert.ok(got.bubbles.length > 0 && got.badges > 0, 'bubbles + verdict badges drawn');
      assert.ok(got.council && got.seats >= 3, 'council table with seats'); assert.strictEqual(got.lit, LIT, 'council light matches 06:00 IST rule / last-hour filing');
      assert.strictEqual(got.couriers > 4, motion !== 'reduce', 'couriers walk to Vigil only when motion is allowed');
      if (motion === 'reduce') assert.ok(got.bubbles.filter(b => b[2] === '1').length <= 4 && got.bubbles.some(b => b[2] === '1'), 'reduced motion: up to 4 static live bubbles');
      assert.ok(!got.overflowX, 'no sideways page scroll at 390 px');
      // the labels this file adds (council sign + seat names) must not sit on top of each other
      const clash = await p.evaluate(() => { const r = [...document.querySelectorAll('#scene text[data-kx]')].map(t => [t.textContent, t.getBBox()]);
        const hit = (a, b) => a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;
        const out = []; r.forEach((a, i) => r.slice(i + 1).forEach(b => { if (hit(a[1], b[1])) out.push(a[0] + ' / ' + b[0]); })); return out; });
      assert.deepStrictEqual(clash, [], 'new labels overlap');
      // tap a robot -> its last 5 jobs, newest first, summaries as text (not HTML)
      await p.evaluate(() => document.querySelector('#scene g.bot[data-agent="Scout"]').dispatchEvent(new MouseEvent('click', { bubbles: true })));
      const jobs = await p.evaluate(() => ({ hidden: document.getElementById('office-jobs').hidden, head: document.getElementById('oj-name').textContent,
        ids: [...document.querySelectorAll('#oj-list > li')].map(l => +l.dataset.key), xss: !!window.__xss }));
      const want = tasks.filter(t => t.owner_agent === 'Scout').slice(0, 5).map(t => t.id);
      assert.ok(!jobs.hidden && jobs.head.startsWith('Scout'), 'jobs panel opens'); assert.deepStrictEqual(jobs.ids, want); assert.ok(!jobs.xss, 'summary text not run as HTML');
      // a council seat opens too; "Meet on the team page" hidden for non-roster owners
      await p.evaluate(() => document.querySelector('#council-table g.bot').dispatchEvent(new MouseEvent('click', { bubbles: true })));
      assert.ok(await p.evaluate(() => document.getElementById('oj-team').hidden), 'team button hidden for a council seat');
      // team page detail shows the same last 5 jobs
      await p.evaluate(() => window.kxShowTeam('Forge')); await p.waitForTimeout(100);
      const bd = await p.evaluate(() => [...document.querySelectorAll('#bd-jobs > li')].map(l => +l.dataset.key));
      assert.deepStrictEqual(bd, tasks.filter(t => t.owner_agent === 'Forge').slice(0, 5).map(t => t.id));
      assert.deepStrictEqual(errors, [], 'no console errors');
      await p.evaluate(() => window.kxShowTeam && document.querySelector('#tab-home').click());
      await p.evaluate(() => { const s = document.querySelector('.kx-scroll'); s.scrollLeft = 0; });
      await p.locator('#office').screenshot({ path: `/tmp/a137-${scheme}-${motion}.png` });
      console.log('PASS', name, JSON.stringify({ q: got.queue, passed: got.passed, redo: got.redo, models: got.models, couriers: got.couriers, seats: got.seats }));
    } catch (e) { fails++; console.log('FAIL', name, e.message, errors.slice(0, 3)); }
    await ctx.close();
  }
  await browser.close(); process.exit(fails ? 1 : 0);
})();

// A198 part 6: 390 px screenshots of the CEO Room (light + dark) with a stand-in dashboard runtime.
// Usage: D3=/path/to/d3.min.js node 00-hq/design/ceo-room-shots.js <before|after>  -> unslop/ceoroom/<tab>-<tag>-<scheme>.jpg
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const tag = process.argv[2] || 'after', out = path.join(__dirname, 'unslop', 'ceoroom');
const d3 = fs.readFileSync(process.env.D3 || require.resolve('d3/dist/d3.min.js'), 'utf8');
const page0 = fs.readFileSync(path.join(__dirname, 'ceo-room-dashboard.html'), 'utf8')
  .replace('<link rel="stylesheet" href="office.css">', '').replace('<script src="office.js"></script>', '').replace('<script src="rooms.js"></script>', '');
const roadmap = [
  { id: 'A198', queue: 'Agents', status: 'doing', world: 'HQ', title: 'Unslop every Kalpa UI' },
  { id: 'A203', queue: 'Agents', status: 'to do', world: 'b6', title: 'Ledger Peaks free X-ray intake form' },
  { id: 'A199', queue: 'Agents', status: 'done', world: 'HQ', title: 'Website glow-up', done: '2026-11-12' },
  { id: 'C73', queue: 'Akhil (CEO)', status: 'to do', world: 'HQ', title: 'Say go for the unslopped site' }];
const workers = [{ name: 'Build sprint', schedule: '0 */2 * * *', enabled: true, next_run_at: '2026-11-12T20:00:00Z', last_status: 'SUCCEEDED', last_fired_at: '2026-11-12T18:00:00Z', last_finished_at: '2026-11-12T18:40:00Z', last_session: '', failure: '' }];
const fx = { roadmap, workers, roster: [], agents: [], n8n_workflows: [], n8n_runs: [], or_usage: [], game_stats: [], game_worlds: [], kl_tasks: [], kl_queue: [] };
const runtime = `window.__fx=${JSON.stringify(fx)};(function(){const calcs={};
window.dash={data(id){if(calcs[id]){const c=calcs[id];const ins=c.inputs.map(i=>dash.data(i));if(ins.some(x=>x.status!=='ok'))return{status:'loading',data:[]};return{status:'ok',data:c.fn(...ins.map(x=>x.data))};}
const a=__fx[id];return a===undefined?{status:'missing',data:[]}:{status:'ok',data:a};},
onData(fn){fn();},calc(id,o){calcs[id]=o;},loader(){},setLink(){},params(){return{}},setParams(){},refresh(){},colors:[]};})();`;
const shell = s => `<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width"><style>
:root{color-scheme:${s};--color-fg:light-dark(#1f1e1b,#ece9e1);--color-fg-muted:light-dark(#6b675e,#a8a397);--color-bg:light-dark(#faf8f3,#191815);--color-panel:light-dark(#fff,#23221e);
--color-border-line:light-dark(#e6e1d6,#3a3833);--color-ok:#2f7d3a;--color-warn:#9c700e;--color-bad:#b3261e;--font-anthropic-sans:system-ui;--cds-font-size-caption:12px;--cds-font-size-body:14px;
--cds-chart-grid:#8883;--cds-chart-axis:#8886;--cds-dur-slow:.3s}body{margin:0;background:var(--color-bg)}</style>
<script>${d3}</script><script>${runtime}</script></head><body><div id="dash-root">${page0}</div></body></html>`;
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); let bad = 0;
  for (const s of ['light', 'dark']) {
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, colorScheme: s, hasTouch: true, reducedMotion: 'reduce' });
    await ctx.route('http://kalpa.test/**', r => r.fulfill({ contentType: 'text/html', body: shell(s) }));
    const p = await ctx.newPage(); p.on('pageerror', e => { bad++; console.error(String(e)); });
    await p.goto('http://kalpa.test/'); await p.waitForTimeout(300);
    for (const tab of ['home', 'work']) {
      await p.locator('#tab-' + tab).tap(); await p.waitForTimeout(200);
      const wide = await p.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (wide) { bad++; console.error(s, tab, 'sideways scroll'); }
      await p.screenshot({ path: path.join(out, `${tab}-${tag}-${s}.jpg`), quality: 60, fullPage: true });
    }
    await ctx.close();
  }
  await b.close(); console.log(bad ? 'FAIL' : 'PASS', tag); process.exit(bad ? 1 : 0);
})();

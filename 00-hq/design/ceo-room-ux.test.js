// A189 check: CEO Room UX patterns 5 (empty), 7 (debounce), 8 (throttle, in rooms test), 12 (kept + clearable filters),
// 13 ('/' shortcut), 20 (Retry). Runs the real page in Chromium at 390 px, light + dark, with a stand-in dashboard runtime.
// Usage: D3=/path/to/d3.min.js node 00-hq/design/ceo-room-ux.test.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const { chromium } = require('playwright');
const dir = __dirname;
const d3 = fs.readFileSync(process.env.D3 || require.resolve('d3/dist/d3.min.js'), 'utf8');
const page0 = fs.readFileSync(path.join(dir, 'ceo-room-dashboard.html'), 'utf8')
  .replace('<link rel="stylesheet" href="office.css">', '').replace('<script src="office.js"></script>', '').replace('<script src="rooms.js"></script>', '');

// every CEO task is done -> "needs you" is empty; no workers yet; game_worlds fails to load
const roadmap = [{ id: 'A1', queue: 'Agents', status: 'to do', world: 'HQ', title: 'Robot office' },
  { id: 'A2', queue: 'Agents', status: 'done', world: 'b1', title: 'BotBhai voice', done: '2026-11-08' },
  { id: 'C1', queue: 'Akhil (CEO)', status: 'done', world: 'HQ', title: 'Open GitHub' }];
const fx = { roadmap, workers: [], roster: [], agents: [], n8n_workflows: [], n8n_runs: [], or_usage: [], game_stats: [], kl_tasks: [], kl_queue: [] };
const runtime = `window.__fx=${JSON.stringify(fx)};window.__refreshed=[];(function(){const calcs={},subs=[];const ERR=new Set(['game_worlds']);
window.dash={data(id){if(calcs[id]){const c=calcs[id];const ins=c.inputs.map(i=>dash.data(i));if(ins.some(x=>x.status!=='ok'))return{status:ins.some(x=>x.status==='error')?'error':'loading',data:[]};return{status:'ok',data:c.fn(...ins.map(x=>x.data))};}
if(ERR.has(id))return{status:'error',data:[]};const a=__fx[id];return a===undefined?{status:'missing',data:[]}:{status:'ok',data:a};},
onData(fn){subs.push(fn);fn();},calc(id,o){calcs[id]=o;},loader(){},setLink(){},params(){return{}},setParams(){},refresh(id){__refreshed.push(id);},colors:[]};})();`;
const shell = scheme => `<!doctype html><html><head><meta name=viewport content="width=device-width"><style>
:root{color-scheme:${scheme};--color-fg:light-dark(#1f1e1b,#ece9e1);--color-fg-muted:light-dark(#6b675e,#a8a397);--color-bg:light-dark(#faf8f3,#191815);--color-panel:light-dark(#fff,#23221e);
--color-border-line:light-dark(#e6e1d6,#3a3833);--color-ok:#2f7d3a;--color-warn:#9c700e;--color-bad:#b3261e;--font-anthropic-sans:system-ui;--cds-font-size-caption:12px;--cds-font-size-body:14px;
--cds-chart-grid:#8883;--cds-chart-axis:#8886;--cds-dur-slow:.3s}body{margin:0;background:var(--color-bg)}</style>
<script>${d3}</script><script>${runtime}</script></head><body><div id="dash-root">${page0}</div></body></html>`;

(async () => {
  const browser = await chromium.launch(); let fails = 0;
  for (const scheme of ['light', 'dark']) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: scheme, hasTouch: true });
    await ctx.route('http://kalpa.test/**', r => r.fulfill({ contentType: 'text/html', body: shell(scheme) }));
    const p = await ctx.newPage(), errors = [];
    p.on('pageerror', e => errors.push(String(e))); p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    try {
      await p.goto('http://kalpa.test/'); await p.waitForTimeout(200);
      // 5: empty "needs you" says so
      assert.match(await p.locator('#needlist .kx-empty').textContent(), /Nothing is waiting/, 'needs-you empty state');
      // 20: a failed box offers Retry (44 px) that re-asks its dataset
      await p.locator('#tab-game').tap();
      const retry = p.locator('#gmap .kx-fail button');
      assert.ok((await retry.boundingBox()).height >= 44, 'Retry tap target ≥ 44 px');
      await retry.tap();
      assert.deepStrictEqual(await p.evaluate(() => __refreshed), ['game_worlds'], 'Retry refreshes game_worlds');
      assert.ok(await retry.isDisabled(), 'Retry rests while loading');
      // 5: no workers yet
      await p.locator('#tab-workers').tap();
      assert.match(await p.locator('#workerlist .kx-empty').textContent(), /No cloud workers/, 'workers empty state');
      // 13: '/' jumps to search on the Work tab
      await p.locator('#tab-home').tap(); await p.keyboard.press('/');
      assert.strictEqual(await p.evaluate(() => document.activeElement.id), 'q', "'/' focuses search");
      assert.ok(await p.locator('#tab-work').getAttribute('aria-selected') === 'true', "'/' opens Work");
      // 7: search waits for typing to stop
      const rows = () => p.locator('#roadtable tbody tr').count();
      assert.strictEqual(await rows(), 3, 'all rows first');
      await p.keyboard.type('zzz', { delay: 30 });
      assert.strictEqual(await rows(), 3, 'no redraw while typing');
      await p.waitForTimeout(300);
      assert.match(await p.locator('#roadtable tbody').textContent(), /No tasks match/, 'no-match empty row');
      // 12: filters survive a reload, then clear with one tap
      await p.locator('#qfilters button', { hasText: 'done' }).tap();
      await p.reload(); await p.waitForTimeout(200); await p.locator('#tab-work').tap();
      assert.strictEqual(await p.locator('#q').inputValue(), 'zzz', 'search kept after reload');
      assert.strictEqual(await p.locator('#qfilters button', { hasText: 'done' }).getAttribute('aria-pressed'), 'true', 'stage filter kept');
      const clear = p.locator('#qclear'); assert.ok((await clear.boundingBox()).height >= 44, 'Clear ≥ 44 px');
      await clear.tap();
      assert.strictEqual(await rows(), 3, 'Clear filters shows everything again');
      assert.strictEqual(await p.locator('#qclear').count(), 0, 'Clear button goes away when nothing is filtered');
      // Esc clears a typed search
      await p.locator('#q').fill('A2'); await p.waitForTimeout(300); assert.strictEqual(await rows(), 1, 'search finds A2');
      await p.locator('#q').press('Escape'); assert.strictEqual(await rows(), 3, 'Esc clears search');
      // phone fit: no sideways scroll; every visible button on Work is ≥ 44 px tall and on screen
      const bad = await p.evaluate(() => [...document.querySelectorAll('#work button, #work input')].filter(b => b.offsetParent).map(b => [b.textContent || b.id, b.getBoundingClientRect()])
        .filter(([, r]) => r.height < 44 || r.left < 0 || r.right > innerWidth + 1).map(([t]) => t));
      assert.deepStrictEqual(bad, [], 'small or off-screen controls');
      assert.ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'no sideways scroll');
      assert.deepStrictEqual(errors, [], 'no console errors');
      console.log('PASS', scheme);
    } catch (e) { fails++; console.log('FAIL', scheme, e.message, errors.slice(0, 3)); }
    await ctx.close();
  }
  await browser.close(); process.exit(fails ? 1 : 0);
})();

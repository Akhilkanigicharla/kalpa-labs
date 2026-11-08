// Live robot rooms check: runs ceo-room-rooms.js in Chromium with a stand-in dashboard runtime and
// answers shaped like the real Cloudflare D1 reply, at 390 px light + dark, plus reduced motion.
// Usage: node 00-hq/design/ceo-room-rooms.test.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const { chromium } = require('playwright');
const js = fs.readFileSync(path.join(__dirname, 'ceo-room-rooms.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, 'ceo-room-dashboard.html'), 'utf8');
const markup = html.slice(html.indexOf('<div class="kx-card" id="rooms"'), html.indexOf('<div class="lr-card" id="lr-card" hidden></div>') + 48);
assert(markup.includes('id="lr-grid"'), 'rooms markup found in the page');

const now = Date.now(), ago = m => new Date(now - m * 60000).toISOString();
const d1 = rows => [{ results: rows, success: true, meta: {} }];
const AGENTS = [
  { id: 'hq:kalpa', name: 'Kalpa', room: 'hq', team: 'free-model agent', runs_as: 'free models', state: 'working', task: 'Marketing team plan', detail: 'K034', updated_at: ago(3) },
  { id: 'hq:claude', name: 'Claude (builder)', room: 'hq', team: 'build', runs_as: 'Claude', state: 'idle', task: 'Live rooms', detail: '', updated_at: ago(90) },
  { id: 'b1:chitti', name: 'Chitti', room: 'b1', team: 'free-model agent', runs_as: 'free models', state: 'needs review', task: '<img src=x onerror="window.pwned=1">5-language test', detail: 'K025', updated_at: ago(600) },
  { id: 'b2:forge', name: 'Forge', room: 'b2', team: 'free-model agent', runs_as: 'free models', state: 'redo', task: 'Voice phrases', detail: 'K026', updated_at: ago(1500) },
  { id: 'b3:kavi', name: 'Kavi', room: 'b3', team: 'free-model agent', runs_as: 'free models', state: 'queued', task: 'Kit blurb', detail: 'K045', updated_at: ago(30) }];
const RUNS = [{ id: '1', workflow: 'agents', room: 'hq', status: 'in_progress', conclusion: '', started_at: ago(2), url: '' },
  { id: '2', workflow: 'Trading Lab backtest', room: 'b7', status: 'completed', conclusion: 'failure', started_at: ago(200), url: '' }];
const META = [{ k: 'refreshed_at', v: ago(4) }, { k: 'roles_b1', v: '182' }];
const ANSWERS = { live_agents: d1(AGENTS), live_runs: d1(RUNS), live_meta: JSON.stringify(d1(META)) };

const stub = `window.dash=(()=>{const L={},F=[],A=${JSON.stringify(ANSWERS)};const out={};
 const get=id=>{if(!(id in out)){try{out[id]={status:'ok',data:L[id]?L[id].fn({answer:A[id]}):A[id]}}catch(e){out[id]={status:'error',message:String(e),data:[]}}}return out[id]};
 return {loader:(id,o)=>{L[id]=o},data:get,onData:f=>{F.push(f);f()},refresh:id=>{delete out[id];window.refreshed=(window.refreshed||0)+1;F.forEach(f=>f())},calc:()=>{}}})();`;
const page = `<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"><style>
 :root{--color-fg:#1b1b1b;--color-fg-muted:#666;--color-bg:#fff;--color-panel:#f6f3ea;--color-border-line:#ddd;--color-ok:#2e7d4f;--color-warn:#b7791f;--color-bad:#c0392b}
 @media (prefers-color-scheme:dark){:root{--color-fg:#eee;--color-fg-muted:#aaa;--color-bg:#111;--color-panel:#1c231d;--color-border-line:#333}}
 body{margin:0;padding:12px;background:var(--color-bg);color:var(--color-fg);font-family:sans-serif}</style></head>
 <body><div id="dash-root">${markup}</div><script>${stub}</script><script>${js}</script></body></html>`;

(async () => {
  const b = await chromium.launch();
  for (const [scheme, motion] of [['light', 'no-preference'], ['dark', 'no-preference'], ['light', 'reduce']]) {
    const pg = await b.newPage({ viewport: { width: 390, height: 844 }, colorScheme: scheme, reducedMotion: motion, hasTouch: true, isMobile: true });
    const errs = []; pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => m.type() === 'error' && errs.push(m.text()));
    await pg.setContent(page);
    const tag = `[${scheme}/${motion}]`;
    assert.strictEqual(await pg.locator('.lr-room').count(), 8, tag + ' 8 rooms');
    assert.strictEqual(await pg.locator('.lr-bot').count(), AGENTS.length, tag + ' one robot per agent');
    assert.match(await pg.textContent('#lr-updated'), /Updated 4 min ago/, tag + ' freshness shown');
    assert.match(await pg.textContent('#lr-sum'), /1 working now/, tag + ' summary counts');
    assert.match(await pg.textContent('#lr-room-b1'), /182 job roles planned/, tag + ' roles on paper');
    assert.match(await pg.textContent('#lr-room-b7'), /No agent working here yet/, tag + ' empty room says so');
    assert.strictEqual(await pg.locator('.lr-bot.lr-working').count(), 1, tag + ' working robot styled');
    // no horizontal overflow at 390 px
    assert(await pg.evaluate(() => document.documentElement.scrollWidth <= 390), tag + ' fits 390 px');
    // tap targets
    for (const bb of await pg.locator('.lr-bot, #lr-refresh').evaluateAll(es => es.map(e => e.getBoundingClientRect())))
      assert(bb.height >= 44 && bb.width >= 44, tag + ' tap target >= 44 px');
    // tap a robot -> its job card; text stays text (no HTML injection)
    await pg.locator('.lr-bot', { hasText: 'Chitti' }).tap();
    await pg.waitForSelector('#lr-card:not([hidden])');
    const card = await pg.textContent('#lr-card');
    assert.match(card, /Chitti · BotBhai/, tag + ' card names robot and room');
    assert.match(card, /<img src=x/, tag + ' task shown as plain text');
    assert.strictEqual(await pg.evaluate(() => window.pwned), undefined, tag + ' no script ran from data');
    assert.strictEqual(await pg.locator('.lr-bot[aria-pressed=true]').count(), 1, tag + ' tapped robot marked');
    // the card is not covered and its close button works
    await pg.locator('#lr-card .kx-btn').tap();
    assert(await pg.locator('#lr-card').isHidden(), tag + ' close hides card');
    await pg.locator('#lr-refresh').tap();
    assert.strictEqual(await pg.evaluate(() => window.refreshed), 3, tag + ' refresh asks for all 3 sources');
    if (motion === 'reduce') {
      const anim = await pg.locator('.lr-working .lr-body').evaluate(e => getComputedStyle(e).animationName);
      assert.strictEqual(anim, 'none', tag + ' no motion when reduced');
    }
    assert.deepStrictEqual(errs, [], tag + ' no console errors');
    await pg.screenshot({ path: `/tmp/rooms-${scheme}-${motion}.png`, fullPage: true });
    await pg.close();
  }
  await b.close();
  console.log('PASS live robot rooms (390 px, light + dark, reduced motion)');
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });

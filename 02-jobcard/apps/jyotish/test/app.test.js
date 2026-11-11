// Static checks on the shipped page: offline, private, labelled in 3 languages, Kalpa design rules.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const I = require('../src/i18n.js');

const ROOT = path.join(__dirname, '..');
const read = (f) => fs.readFileSync(path.join(ROOT, f), 'utf8');
const OWN = ['index.html', 'styles.css', 'src/app.js', 'src/core.js', 'src/data.js', 'src/names.js', 'src/i18n.js'];

test('no network: no remote URLs, fetch, XHR, sockets, beacons or service workers in our files', () => {
  for (const f of OWN) {
    const s = read(f).replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
    assert.ok(!/https?:\/\//.test(s.replace('http://www.w3.org/2000/svg', '')), `${f} has a URL`);
    assert.ok(!/\b(fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon|serviceWorker|importScripts)\b/.test(s), `${f} has a network API`);
  }
  const vendor = read('vendor/astronomy.browser.min.js');
  assert.ok(!/\b(fetch\(|XMLHttpRequest|WebSocket|sendBeacon)\b/.test(vendor), 'vendor lib makes network calls');
  assert.match(read('index.html'), /connect-src 'none'/);
});

test('vendored library keeps its MIT licence header', () => {
  const head = read('vendor/astronomy.browser.min.js').slice(0, 1500);
  assert.match(head, /MIT License/);
  assert.match(head, /Don Cross/);
  assert.ok(fs.existsSync(path.join(ROOT, 'fonts/OFL-anek.txt')) && fs.existsSync(path.join(ROOT, 'fonts/OFL-rozha-one.txt')));
  // The browser copy must be the same build the Node tests ran against.
  const pkg = JSON.parse(read('node_modules/astronomy-engine/package.json'));
  assert.equal(pkg.license, 'MIT');
  assert.equal(pkg.version, JSON.parse(read('package.json')).dependencies['astronomy-engine']);
  assert.equal(read('vendor/astronomy.browser.min.js'), read('node_modules/astronomy-engine/astronomy.browser.min.js'));
});

test('manifest is valid and points to local files', () => {
  const m = JSON.parse(read('manifest.webmanifest'));
  assert.equal(m.display, 'standalone');
  for (const ic of m.icons) assert.ok(fs.existsSync(path.join(ROOT, ic.src)));
  assert.ok(fs.existsSync(path.join(ROOT, 'index.html')));
});

test('every label exists in English, Telugu and Hindi, and every data-t key is defined', () => {
  for (const [k, row] of Object.entries(I.T)) {
    assert.equal(row.length, 3, k);
    assert.ok(/[ఀ-౿]/.test(row[1]), `${k} te`);
    assert.ok(/[ऀ-ॿ]/.test(row[2]), `${k} hi`);
    // Same {placeholders} in all three.
    const ph = (s) => (s.match(/\{\w+\}/g) || []).sort().join();
    assert.equal(ph(row[1]), ph(row[0]), k);
    assert.equal(ph(row[2]), ph(row[0]), k);
  }
  const html = read('index.html') + read('src/app.js');
  for (const m of html.matchAll(/data-t="(\w+)"|\bt\('(\w+)'/g)) assert.ok(I.T[m[1] || m[2]], `missing label ${m[1] || m[2]}`);
});

test('disclaimer and priest note are present', () => {
  assert.equal(I.t('en', 'disclaimer'), 'For guidance and tradition. No health, legal or money predictions.');
  assert.match(I.t('en', 'priest'), /check with your family priest/);
  assert.match(read('index.html'), /data-t="disclaimer"/);
});

test('Kalpa vibe check passes on the page, styles and UI script', async () => {
  const vibe = await import(path.join(ROOT, '../../../00-hq/design/vibecheck.mjs'));
  const text = ['index.html', 'styles.css', 'src/app.js', 'src/i18n.js'].map(read).join('\n');
  const hits = vibe.scan(text);
  const fails = Object.entries(hits).filter(([id, h]) => vibe.verdict(id, h) === 'FAIL');
  assert.deepEqual(fails, []);
  assert.ok(!/—/.test(text), 'no em dashes');
});

test('no new palettes: every colour in styles.css comes from tokens (two dark-text literals allowed)', () => {
  const css = read('styles.css');
  const hex = [...css.matchAll(/#[0-9a-fA-F]{3,8}\b/g)].map((m) => m[0].toUpperCase());
  const tokens = read('tokens.css').toUpperCase();
  for (const h of hex) assert.ok(tokens.includes(h), `${h} not a Kalpa token`);
  assert.equal(read('tokens.css'), fs.readFileSync(path.join(ROOT, '../../../00-hq/design/tokens.css'), 'utf8'), 'tokens.css drifted from HQ');
});

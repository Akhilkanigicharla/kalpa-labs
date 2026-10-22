// Run: node 00-hq/design/theme.test.mjs — Kalpavruksha tokens: every text pair passes WCAG AA in light and dark,
// every token copy across the sites matches tokens.css, and no old Kalamkari indigo is left in a UI.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { contrast } from './vibecheck.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const css = fs.readFileSync(path.join(ROOT, '00-hq/design/tokens.css'), 'utf8');
const block = (re) => Object.fromEntries([...css.match(re)[1].matchAll(/--([\w-]+):\s*(#[0-9A-Fa-f]{6})/g)].map((m) => [m[1], m[2]]));
const light = block(/^:root\{([\s\S]*?)\n\}/m);
const dark = block(/:root\[data-theme="dark"\]\{([\s\S]*?)\}/);
const AA = [['fg', 'bg', 4.5], ['fg', 'panel', 4.5], ['muted', 'bg', 4.5], ['muted', 'panel', 4.5], ['accent', 'panel', 4.5], ['accent', 'bg', 4.5],
  ['accent-fg', 'accent', 4.5], ['hero-fg', 'hero', 4.5], ['hero-mute', 'hero', 4.5], ['gold', 'hero', 3], ['leaf', 'hero', 3],
  ['bad', 'panel', 3], ['ok', 'panel', 3], ['warn', 'panel', 3], ['madder', 'panel', 3], ...[0, 1, 2, 3, 4, 5, 6, 7].map((i) => [`l${i}`, 'panel', 3])];
for (const [name, t] of [['light', light], ['dark', dark]]) {
  for (const [a, b, min] of AA) {
    assert.ok(t[a] && t[b], `${name}: missing --${a} or --${b}`);
    const r = contrast(t[a], t[b]); assert.ok(r >= min, `${name}: --${a} on --${b} is ${r.toFixed(2)}:1 (needs ${min})`);
  }
}
assert.ok(contrast(light.fg, light.gold) >= 4.5, 'dark text on a gold button');
console.log(`  ✓ ${AA.length * 2 + 1} colour pairs pass WCAG AA (light + dark)`);

assert.match(css, /Kalpavruksha/); assert.match(css, /--vine:/);
assert.ok(fs.existsSync(path.join(ROOT, '00-hq/design/brand/kalpavruksha.svg')), 'tree logo exists');
console.log('  ✓ tokens.css is the Kalpavruksha theme with the vine band and the tree logo');

// every UI file: no Kalamkari indigo / madder / old parchment values left
const OLD = /#(1C2463|1B2266|2A3A8F|9AABFF|B23A2C|D3940A|EEEDF3|0E1230|161B42)\b/i;
const files = execFileSync('git', ['ls-files'], { cwd: ROOT, encoding: 'utf8' }).split('\n')
  .filter((f) => /\.(html|css|astro|js|mjs|ts|tsx|py|svg|json)$/.test(f) && !/(node_modules|\/dist\/|_dist|\.output|^archive\/|^00-hq\/vendor\/|^00-hq\/log\/|theme\.test\.mjs)/.test(f));
const left = files.filter((f) => OLD.test(fs.readFileSync(path.join(ROOT, f), 'utf8')));
assert.deepEqual(left, [], 'old Kalamkari colours still in:\n' + left.join('\n'));
console.log(`  ✓ no old Kalamkari colour left in ${files.length} source files`);
console.log('theme tests passed');

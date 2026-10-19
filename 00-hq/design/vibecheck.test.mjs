// Run: node 00-hq/design/vibecheck.test.mjs — each of the 20 detectors catches its tell and passes clean Kalpa markup.
import assert from 'node:assert/strict';
import { scan, verdict, CHECKS, contrast, run } from './vibecheck.mjs';

const BAD = {
  'purple-blue-gradient': '.h{background:linear-gradient(90deg,#7c3aed,#2563eb)}',
  'gradient-text': '.t{background:linear-gradient(#000,#fff);-webkit-background-clip:text;background-clip:text}',
  'emoji-headings': '<h2>🚀 Launch fast</h2>',
  'inter-font': 'body{font-family:"Inter",sans-serif}',
  'left-border-cards': '.card{border-left:4px solid #f00}',
  'glassmorphism': '.g{backdrop-filter:blur(12px)}',
  'low-contrast-dark': '@media (prefers-color-scheme: dark){:root{--bg:#111111;--muted:#444444}}',
  'three-icon-boxes': '.features{display:grid;grid-template-columns:repeat(3,1fr)}',
  'badge-above-h1': '<span class="badge">New</span><h1>Hi</h1>',
  'lucide': '<script src="https://unpkg.com/lucide"></script>',
  'shadcn': '<button class="inline-flex items-center justify-center rounded-md text-sm font-medium">Go</button>',
  'fade-on-scroll': '<section data-aos="fade-up">x</section>',
  'cursor-beam': 'addEventListener("mousemove",e=>{el.style.setProperty("--x",e.clientX)})',
  'hover-fade': '.btn:hover{opacity:.8}',
  'spacing-chaos': '.a{padding:13px 17px;margin:22px}',
  'em-dashes': '<p>Fast — and simple.</p>',
  'buzzwords': '<p>Supercharge your workflow with seamless AI.</p>',
  'serif-italic-accent': '<h1>Build <em>faster</em></h1><style>em{font-style:italic}</style>',
  'grotesk-instrument': '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk">',
  'grain-texture': '<svg><filter><feTurbulence baseFrequency=".8"/></filter></svg>',
};
assert.equal(Object.keys(BAD).length, 20); assert.equal(CHECKS.length, 20);
for (const [id] of CHECKS) {
  const hits = scan(BAD[id])[id];
  assert.equal(verdict(id, hits), 'FAIL', `${id} should catch: ${BAD[id]}`);
}
console.log('  ✓ all 20 tells are caught on a bad example');

const GOOD = `<style>.kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.card{border:1px solid var(--rule);padding:16px 24px;margin:0 0 12px}
.btn:hover{background:var(--accent)}
@media (prefers-color-scheme: dark){:root{--bg:#0E1230;--panel:#161B42;--fg:#ECEBF7;--muted:#A3A7CC}}</style>
<h1>Your customers get a reply in Telugu</h1><p class="eyebrow">Hyderabad</p>
<table><tr><td>—</td></tr></table><p>Free 14-day pilot: no payment until you say yes.</p>`;
const g = scan(GOOD);
for (const [id] of CHECKS) assert.equal(verdict(id, g[id]), 'ok', `${id} false alarm: ${g[id]}`);
console.log('  ✓ clean Kalpa markup passes (number tiles, empty-cell dash, label under the headline)');

assert.ok(contrast('#A3A7CC', '#0E1230') >= 4.5 && contrast('#444444', '#111111') < 4.5);
console.log('  ✓ dark-mode contrast maths (Kalpa --muted on --bg passes 4.5:1)');

const rep = run(); const bad = Object.entries(rep).flatMap(([s, r]) => Object.values(r).filter(v => v.verdict === 'FAIL').map(v => `${s}: ${v.label}`));
assert.deepEqual(bad, [], 'every Kalpa site must be clean:\n' + bad.join('\n'));
console.log(`  ✓ all ${Object.keys(rep).length} Kalpa sites pass 20/20`);
console.log('vibecheck tests passed');

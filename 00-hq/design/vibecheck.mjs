#!/usr/bin/env node
// Vibe check: scans every Kalpa site for the 20 "vibecoded" tells (millee.md list, 19 Oct 2026).
// Usage: node 00-hq/design/vibecheck.mjs            -> report, exit 1 if any FAIL
//        node 00-hq/design/vibecheck.mjs --json     -> machine output
// Heuristics on source files (HTML/CSS/Astro/JS); a hit is a prompt to look, explained in `why`.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const SITES = {
  'Kalpa Labs (HQ site)': ['00-hq/site'],
  'BotBhai web + sales': ['01-botbhai/botbhai/web/index.src.html', '01-botbhai/botbhai/web/dashboard.html', '01-botbhai/botbhai/web/inbox.html', '01-botbhai/botbhai/web/billing.html', '01-botbhai/botbhai/web/widget.js', '01-botbhai/docs/sales/visit-cluster1.html'],
  'JobCard app': ['02-jobcard/web'],
  'Tab Lifeboat site + popup': ['04-extensions/site', '04-extensions/src/entrypoints'],
  'Deals & Tools site': ['05-deals/site/src'],
  'Ledger Peaks pages': ['06-finops/design'],
};
const EXT = /\.(html|css|astro|mjs|js|jsx|tsx|vue)$/;
const SKIP = /(node_modules|dist|\.test\.|sw\.template|build\.mjs|check\.py)/;

function files(rel) {
  const p = path.join(ROOT, rel);
  if (!fs.existsSync(p)) return [];
  if (fs.statSync(p).isFile()) return [p];
  return fs.readdirSync(p, { recursive: true }).map(f => path.join(p, f))
    .filter(f => EXT.test(f) && !SKIP.test(f) && fs.statSync(f).isFile());
}

// ---------- colour helpers ----------
export function hexToRgb(h) {
  h = h.replace('#', ''); if (h.length === 3) h = [...h].map(c => c + c).join('');
  const n = parseInt(h.slice(0, 6), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255];
}
export function hue([r, g, b]) {
  r /= 255; g /= 255; b /= 255; const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if (!d) return -1; let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return (h * 60 + 360) % 360;
}
function lum(rgb) { return rgb.map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }).reduce((a, v, i) => a + v * [.2126, .7152, .0722][i], 0); }
export function contrast(a, b) { const [x, y] = [lum(hexToRgb(a)), lum(hexToRgb(b))].sort((p, q) => q - p); return (x + .05) / (y + .05); }
const isPurple = h => h >= 255 && h <= 300, isBlue = h => h >= 200 && h < 255;

// ---------- the 20 checks: (text, ctx) -> list of hits ----------
const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F000}-\u{1F2FF}]/u;
const BUZZ = /\b(revolutioni[sz]e|seamless(ly)?|cutting[- ]edge|supercharge|game[- ]chang\w*|next[- ]gen\w*|unlock (the|your)|empower\w*|leverag\w+|effortless(ly)?|elevate your|streamlin\w+|world[- ]class|synerg\w+|harness the power|in today's fast-paced)\b/gi;
const grads = t => [...t.matchAll(/(?:linear|radial|conic)-gradient\(([^;{}]+)\)/g)].map(m => m[1]);
export const CHECKS = [
  ['purple-blue-gradient', 'Purple-to-blue gradient', t => grads(t).filter(g => { const hs = [...g.matchAll(/#[0-9a-f]{3,8}\b/gi)].map(m => hue(hexToRgb(m[0]))); return hs.some(isPurple) && hs.some(isBlue); })],
  ['gradient-text', 'Gradient hero text', t => /background-clip\s*:\s*text/i.test(t) ? ['background-clip:text'] : []],
  ['emoji-headings', 'Emojis in headings', t => [...t.matchAll(/<h[1-6][^>]*>([\s\S]*?)<\/h[1-6]>/gi)].map(m => m[1]).filter(h => EMOJI.test(h.replace(/<[^>]+>/g, ''))).map(h => h.replace(/<[^>]+>/g, '').trim().slice(0, 50))],
  ['inter-font', 'Inter font everywhere', t => /(font-family[^;]*["']?\bInter\b|family=Inter\b)/i.test(t) ? ['Inter'] : []],
  ['left-border-cards', 'Coloured left-border cards', t => [...t.matchAll(/border-left\s*:\s*([3-9]|\d\d)px\s+solid/gi)].map(m => m[0])],
  ['glassmorphism', 'Glassmorphism cards', t => [...t.matchAll(/backdrop-filter\s*:\s*[^;]*blur/gi)].map(m => m[0])],
  ['low-contrast-dark', 'Low-contrast dark mode', (t, c) => c.darkPairs(t)],
  // number tiles (.kpis/.stats) on app screens are data, not the marketing "3 feature boxes"
  ['three-icon-boxes', 'Three icon boxes in a row', t => [...t.matchAll(/([.#][\w-]+)\s*\{[^}]*grid-template-columns\s*:\s*repeat\(\s*3\s*,/gi)].filter(m => !/kpi|stat/i.test(m[1])).map(m => m[1])],
  ['badge-above-h1', 'Badge above the headline', t => [...t.matchAll(/<(span|div|p)[^>]*class="[^"]*\b(badge|pill|eyebrow|chip|tag)\b[^"]*"[^>]*>[^<]{0,60}<\/\1>\s*<h[12]\b/gi)].map(m => m[0].slice(0, 60))],
  ['lucide', 'Lucide icons everywhere', t => /lucide/i.test(t) ? ['lucide'] : []],
  ['shadcn', 'Untouched shadcn components', t => /(shadcn|inline-flex items-center justify-center (whitespace-nowrap )?rounded-md text-sm font-medium)/.test(t) ? ['shadcn signature'] : []],
  ['fade-on-scroll', 'Sections fading in on scroll', t => /(data-aos|\bfade-?in\b|\breveal\b[^;]*IntersectionObserver|IntersectionObserver[\s\S]{0,400}opacity)/i.test(t) ? ['scroll fade'] : []],
  ['cursor-beam', 'Beam that follows the cursor', t => /(mousemove|pointermove)[\s\S]{0,300}(--x|--mouse|radial-gradient|style\.(left|top|transform))/i.test(t) ? ['cursor follower'] : []],
  ['hover-fade', 'Hover effects that make buttons fade', t => [...t.matchAll(/:hover[^{]*\{[^}]*opacity\s*:\s*0?\.\d/gi)].map(m => m[0].slice(0, 60))],
  ['spacing-chaos', 'Inconsistent spacing', (t, c) => c.spacing(t)],
  ['em-dashes', 'Em dashes everywhere', (t, c) => c.copy(t).match(/[\p{L}\p{N}] — [\p{L}\p{N}]/gu) || []], // "x — y" in prose; a lone "—" in an empty table cell is fine
  ['buzzwords', 'Generic buzzword copy', (t, c) => c.copy(t).match(BUZZ) || []],
  ['serif-italic-accent', 'Serif italics for accent words', t => /<h[12][^>]*>[^<]*<(em|i)\b/i.test(t) && /(em|i)\s*\{[^}]*font-style\s*:\s*italic/i.test(t) ? ['italic accent in heading'] : []],
  ['grotesk-instrument', 'Space Grotesk + Instrument Serif', t => /(Space Grotesk|Space\+Grotesk|Instrument Serif|Instrument\+Serif)/i.test(t) ? ['font pair'] : []],
  ['grain-texture', 'Grain texture over a gradient', t => /(feTurbulence|\bgrain\b|noise\.(png|svg))/i.test(t) ? ['grain'] : []],
];
// per-site limits: em dashes / buzzwords / spacing are counted, the rest fail on any hit
const LIMITS = {};

export const SCALE = new Set([0, 1, 2, 4, 6, 8, 10, 12, 16, 20, 24, 28, 32, 40, 48, 56, 64, 72, 80, 96, 112, 128]);
const ctx = {
  copy: t => t.replace(/<(script|style)[\s\S]*?<\/\1>/gi, ' ').replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/^\s*(\/\/|\*|\/\*).*$/gm, ' ').replace(/<[^>]+>/g, ' '),
  spacing: t => { // every margin/padding/gap px value must sit on the 4-point scale (2/6/10 allowed for hairlines)
    const off = new Set([...t.matchAll(/\b(?:margin|padding|gap)[a-z-]*\s*:\s*([^;}"]+)/gi)]
      .flatMap(m => (m[1].match(/\b\d+(?:\.\d+)?px\b/g) || []).map(parseFloat))
      .filter(v => v < 200 && !SCALE.has(v)));
    return off.size ? [`off-scale spacing: ${[...off].sort((a, b) => a - b).map(v => v + 'px').join(' ')}`] : [];
  },
  darkPairs: t => { // text vs background tokens inside dark-mode blocks must reach 4.5:1
    const out = [];
    for (const m of t.matchAll(/(?:prefers-color-scheme:\s*dark|data-theme="?dark"?\])[^{]*\{([\s\S]*?)\}\s*\}?/gi)) {
      const v = Object.fromEntries([...m[1].matchAll(/--([\w-]+)\s*:\s*(#[0-9a-f]{6})\b/gi)].map(x => [x[1], x[2]]));
      for (const fg of ['fg', 'muted', 'ink', 'text', 'mute']) for (const bg of ['bg', 'panel', 'paper', 'surface']) {
        if (v[fg] && v[bg]) { const r = contrast(v[fg], v[bg]); if (r < 4.5) out.push(`--${fg} on --${bg} ${r.toFixed(2)}:1`); }
      }
    }
    return out;
  },
};

export function scan(text) {
  const res = {};
  for (const [id, , fn] of CHECKS) res[id] = fn(text, ctx);
  return res;
}
export function verdict(id, hits) { return hits.length > (LIMITS[id] ?? 0) ? 'FAIL' : 'ok'; }

export function run() {
  const report = {};
  for (const [site, paths] of Object.entries(SITES)) {
    const fl = paths.flatMap(files);
    const perFile = fl.map(f => [path.relative(ROOT, f), scan(fs.readFileSync(f, 'utf8'))]);
    report[site] = {};
    for (const [id, label] of CHECKS) {
      const hits = perFile.flatMap(([f, r]) => r[id].map(h => `${f}: ${h}`));
      report[site][id] = { label, verdict: verdict(id, hits), hits };
    }
  }
  return report;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const rep = run(); let fails = 0;
  if (process.argv.includes('--json')) { console.log(JSON.stringify(rep, null, 1)); }
  for (const [site, r] of Object.entries(rep)) {
    const bad = Object.entries(r).filter(([, v]) => v.verdict === 'FAIL'); fails += bad.length;
    if (process.argv.includes('--json')) continue;
    console.log(`\n${bad.length ? '✗' : '✓'} ${site}: ${20 - bad.length}/20 clean`);
    for (const [, v] of bad) console.log(`   ✗ ${v.label} (${v.hits.length}): ${v.hits.slice(0, 3).join(' | ')}`);
  }
  process.exit(fails ? 1 : 0);
}

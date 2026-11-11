import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import {
  mmToPx, faceToHead, headRangeMm, computeCrop, outputSize, sheetLayout, validate, replaceBackground, SHEETS,
} from '../core.mjs';

const dir = path.dirname(fileURLToPath(import.meta.url));
const { specs } = JSON.parse(fs.readFileSync(path.join(dir, '../specs.json'), 'utf8'));
const byId = Object.fromEntries(specs.map(s => [s.id, s]));
const close = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) <= eps, `${a} != ${b}`);

test('specs.json: 8 entries, required fields, all unverified with an official-looking https url', () => {
  const ids = ['in-passport', 'in-visa', 'us-passport-visa', 'uk-passport', 'schengen-visa', 'ca-passport', 'au-passport', 'ae-visa'];
  assert.deepEqual(specs.map(s => s.id).sort(), [...ids].sort());
  for (const s of specs) {
    assert.equal(s.verified, false, `${s.id} must stay unverified until a person checks it`);
    assert.match(s.verify_url, /^https:\/\//);
    assert.ok(s.print_mm.w > 0 && s.print_mm.h > 0, s.id);
    assert.match(s.fill_hex, /^#[0-9A-F]{6}$/i);
    if (s.head_mm) assert.ok(s.head_mm.min < s.head_mm.max && s.head_mm.max < s.print_mm.h, s.id);
    if (s.digital) assert.ok(s.digital.min_px.w > 0 && s.digital.min_px.h > 0, s.id);
  }
});

test('mmToPx: 2 inch at 300 and 600 dpi, 35 x 45 mm at 300 dpi', () => {
  assert.equal(mmToPx(50.8, 300), 600);
  assert.equal(mmToPx(50.8, 600), 1200);
  assert.equal(mmToPx(35, 300), 413);
  assert.equal(mmToPx(45, 300), 531);
  assert.throws(() => mmToPx(0, 300), RangeError);
});

test('faceToHead grows the box up to the crown and keeps it centred', () => {
  const head = faceToHead({ x: 100, y: 200, w: 100, h: 100 });
  close(head.y, 155); close(head.h, 150);
  close(head.x + head.w / 2, 150);
});

test('headRangeMm: mm rule, percent rule, fallback', () => {
  assert.deepEqual(headRangeMm(byId['uk-passport']), { min: 29, max: 34, target: 31.5, source: 'rule' });
  const ind = headRangeMm(byId['in-passport']);
  close(ind.min, 35.7); close(ind.max, 40.8); assert.equal(ind.source, 'rule');
  assert.equal(headRangeMm(byId['ae-visa']).source, 'fallback');
});

test('computeCrop UK: head scaled to 31.5 mm, centred, 35:45 shape, inside image', () => {
  const spec = byId['uk-passport'];
  const box = { x: 900, y: 600, w: 500, h: 630 };
  const c = computeCrop(spec, { w: 2400, h: 3200 }, box);
  close(c.pxPerMm, 20);
  close(c.w, 700); close(c.h, 900);
  close(c.x + c.w / 2, 1150); // head centre
  // spare height 13.5 mm, 40% above the head = 5.4 mm = 108 px
  close(c.y, 600 - 108);
  assert.equal(c.inside, true);
  const v = validate(spec, { image: { w: 2400, h: 3200 }, crop: c, out: outputSize(spec, 300) });
  assert.equal(v.pass, true, JSON.stringify(v.reasons));
  assert.ok(v.reasons.some(r => r.code === 'spec-unchecked' && r.level === 'warn'));
});

test('computeCrop US: eye line lands inside 28 to 35 mm from the bottom', () => {
  const spec = byId['us-passport-visa'];
  const c = computeCrop(spec, { w: 3000, h: 4000 }, { x: 1200, y: 1000, w: 480, h: 600 });
  const v = validate(spec, { image: { w: 3000, h: 4000 }, crop: c });
  const eye = v.reasons.find(r => r.code === 'eye-line');
  assert.equal(eye.level, 'pass', eye.msg);
  close(c.w, c.h); // square
});

test('computeCrop from a detector face box gives the same result as the grown head box', () => {
  const spec = byId['au-passport'];
  const face = { x: 1000, y: 1200, w: 400, h: 400 };
  const a = computeCrop(spec, { w: 3000, h: 4000 }, face, { boxIs: 'face' });
  const b = computeCrop(spec, { w: 3000, h: 4000 }, faceToHead(face));
  close(a.x, b.x); close(a.y, b.y); close(a.w, b.w);
});

test('computeCrop near the top edge reports overflow; validation warns or fails', () => {
  const spec = byId['ca-passport'];
  const near = computeCrop(spec, { w: 1000, h: 1400 }, { x: 350, y: 20, w: 300, h: 400 });
  assert.equal(near.inside, false);
  assert.ok(near.overflow.top > 0);
  const tooClose = computeCrop(spec, { w: 1000, h: 1000 }, { x: 100, y: 50, w: 800, h: 900 });
  const v = validate(spec, { image: { w: 1000, h: 1000 }, crop: tooClose });
  assert.equal(v.pass, false);
  assert.ok(v.reasons.some(r => r.code === 'too-tight'));
});

test('validate fails a head that is too small, off centre, and a low-resolution source', () => {
  const spec = byId['uk-passport'];
  const crop = computeCrop(spec, { w: 2400, h: 3200 }, { x: 900, y: 600, w: 500, h: 630 });
  const small = { ...crop, head: { ...crop.head, h: crop.head.h * 0.8 } };
  assert.ok(validate(spec, { crop: small }).reasons.some(r => r.code === 'head-small'));
  const shifted = { ...crop, head: { ...crop.head, x: crop.head.x + crop.w * 0.1 } };
  assert.ok(validate(spec, { crop: shifted }).reasons.some(r => r.code === 'off-centre'));
  const tiny = computeCrop(spec, { w: 300, h: 400 }, { x: 100, y: 80, w: 100, h: 126 });
  const v = validate(spec, { image: { w: 300, h: 400 }, crop: tiny, out: outputSize(spec, 600) });
  assert.ok(v.reasons.some(r => r.code === 'low-res' && r.level === 'fail'));
});

test('outputSize: print sizes and digital rules', () => {
  assert.deepEqual(outputSize(byId['us-passport-visa'], 300), { w: 602, h: 602, dpi: 300 });
  assert.deepEqual(outputSize(byId['uk-passport'], 600), { w: 827, h: 1063, dpi: 600 });
  assert.deepEqual(outputSize(byId['us-passport-visa'], 'digital'), { w: 600, h: 600, dpi: null });
  assert.deepEqual(outputSize(byId['in-visa'], 'digital'), { w: 350, h: 350, dpi: null });
  const uk = outputSize(byId['uk-passport'], 'digital');
  assert.ok(uk.w >= 600 && uk.h >= 750, JSON.stringify(uk));
  assert.match(outputSize(byId['au-passport'], 'digital').note, /No upload rule/);
  assert.throws(() => outputSize(byId['au-passport'], 72), RangeError);
});

test('validate digital pixel and file-size rules', () => {
  const spec = byId['us-passport-visa'];
  const ok = validate(spec, { out: { w: 600, h: 600, dpi: null }, fileBytes: 200 * 1024 });
  assert.equal(ok.pass, true);
  const big = validate(spec, { out: { w: 600, h: 600, dpi: null }, fileBytes: 300 * 1024 });
  assert.ok(big.reasons.some(r => r.code === 'file-big'));
  const small = validate(spec, { out: { w: 500, h: 500, dpi: null } });
  assert.ok(small.reasons.some(r => r.code === 'px-small'));
  const notSq = validate(spec, { out: { w: 700, h: 600, dpi: null } });
  assert.ok(notSq.reasons.some(r => r.code === 'not-square'));
  const evisa = validate(byId['in-visa'], { out: { w: 350, h: 350, dpi: null }, fileBytes: 5 * 1024 });
  assert.ok(evisa.reasons.some(r => r.code === 'file-small'));
});

test('sheetLayout 35 x 45 mm on 4x6: 6 photos, all inside the margins, no overlap', () => {
  const L = sheetLayout({ w: 35, h: 45 }, '4x6');
  assert.equal(L.count, 6);
  assert.equal(L.positions.length, 6);
  for (const p of L.positions) {
    assert.ok(p.x >= L.margin - 1e-9 && p.y >= L.margin - 1e-9);
    assert.ok(p.x + p.w <= L.sheet.w - L.margin + 1e-9 && p.y + p.h <= L.sheet.h - L.margin + 1e-9);
  }
  for (let i = 0; i < L.positions.length; i++) for (let j = i + 1; j < L.positions.length; j++) {
    const a = L.positions[i], b = L.positions[j];
    const overlap = a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
    assert.ok(!overlap, `photos ${i} and ${j} overlap`);
  }
});

test('sheetLayout: 2 inch on 4x6 and A4, 50 x 70 on 4x6, landscape chosen when better', () => {
  assert.equal(sheetLayout({ w: 51, h: 51 }, '4x6').count, 2);
  // A4 usable 200 x 287: 3 cols x 5 rows
  const a4 = sheetLayout({ w: 51, h: 51 }, 'A4');
  assert.equal(a4.cols * a4.rows, a4.count);
  assert.equal(a4.count, 15);
  assert.equal(sheetLayout({ w: 50, h: 70 }, '4x6').count, 2);
  assert.equal(sheetLayout({ w: 35, h: 45 }, 'A4').count, 30);
  // A wide photo fits better with the sheet turned
  const wide = sheetLayout({ w: 140, h: 40 }, '4x6');
  assert.equal(wide.orient, 'landscape');
  assert.equal(wide.count, 2);
  assert.ok(SHEETS['4x6'].w === 101.6);
  assert.throws(() => sheetLayout({ w: 35, h: 45 }, 'letterx'), RangeError);
});

test('replaceBackground fills the plain wall, keeps the person and the cut-off bottom', () => {
  const w = 10, h = 10;
  const data = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = (y * w + x) * 4;
    const person = x >= 3 && x <= 6 && y >= 3; // a block touching the bottom
    const v = person ? [90, 60, 40] : [200, 205, 210]; // dark subject on a grey-blue wall
    data[i] = v[0]; data[i + 1] = v[1]; data[i + 2] = v[2]; data[i + 3] = 255;
  }
  const n = replaceBackground(data, w, h, { fill: '#FFFFFF', threshold: 30 });
  assert.equal(n, 100 - 4 * 7);
  const px = (x, y) => Array.from(data.slice((y * w + x) * 4, (y * w + x) * 4 + 3));
  assert.deepEqual(px(0, 0), [255, 255, 255]);
  assert.deepEqual(px(0, 9), [255, 255, 255]); // reached through the wall from above
  assert.deepEqual(px(4, 5), [90, 60, 40]);
  assert.throws(() => replaceBackground(new Uint8ClampedArray(3), 1, 1), RangeError);
});

test('tokens.css copy matches the Kalpa design system source', () => {
  const src = path.join(dir, '../../../../00-hq/design/tokens.css');
  if (!fs.existsSync(src)) return; // app folder used on its own
  assert.equal(fs.readFileSync(path.join(dir, '../tokens.css'), 'utf8'), fs.readFileSync(src, 'utf8'));
});

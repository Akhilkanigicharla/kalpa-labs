// Kalpa Photo Studio UI. Everything runs on the device: no uploads, no outside requests (see the CSP in index.html).
import { computeCrop, outputSize, sheetLayout, validate, replaceBackground, faceToHead, mmToPx, SHEETS } from './core.mjs';

const $ = id => document.getElementById(id);
const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const state = { specs: [], spec: null, src: null, img: { w: 0, h: 0 }, box: null, drag: null, scale: 1 };

// ---------- photo rules ----------
async function loadSpecs() {
  const res = await fetch('specs.json');
  const { specs } = await res.json();
  state.specs = specs;
  $('spec').innerHTML = specs.map(s => `<option value="${esc(s.id)}">${esc(s.country)} · ${esc(s.document)}</option>`).join('');
  pickSpec(specs[0].id);
}
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const range = r => (r ? `${r.min} to ${r.max}` : null);

function pickSpec(id) {
  const s = state.specs.find(x => x.id === id);
  state.spec = s;
  const head = s.head_mm ? `${range(s.head_mm)} mm, chin to top of head`
    : s.head_pct ? `${range(s.head_pct)}% of photo height` : 'No number stored (general size used)';
  const dig = s.digital
    ? `${s.digital.min_px.w} x ${s.digital.min_px.h} px minimum${s.digital.max_px ? `, ${s.digital.max_px.w} x ${s.digital.max_px.h} max` : ''}${s.digital.file_kb ? `, ${s.digital.file_kb.min ?? 0} to ${s.digital.file_kb.max} KB` : ''}, ${s.digital.format}`
    : 'No upload rule stored';
  $('specInfo').innerHTML = `
    <p>${s.verified ? '' : '<span class="badge unchecked">spec to be checked</span>'}</p>
    <dl>
      <dt class="k">Size</dt><dd>${esc(s.print_mm.w)} x ${esc(s.print_mm.h)} mm</dd>
      <dt class="k">Head</dt><dd>${esc(head)}</dd>
      ${s.eye_from_bottom_mm ? `<dt class="k">Eyes</dt><dd>${range(s.eye_from_bottom_mm)} mm from bottom</dd>` : ''}
      <dt class="k">Background</dt><dd>${esc(s.background)}</dd>
      <dt class="k">Upload</dt><dd>${esc(dig)}</dd>
    </dl>
    ${s.notes ? `<p class="hint">${esc(s.notes)}</p>` : ''}
    <p class="hint">${s.verified ? 'Checked' : 'Not yet checked'} against <a href="${esc(s.verify_url)}" rel="noreferrer noopener" target="_blank">the official page</a>.</p>`;
  if (state.src) refresh();
}

// ---------- choosing a photo ----------
async function loadFile(file) {
  $('fileErr').hidden = true;
  if (!file || !file.type.startsWith('image/')) return showErr('Please choose a photo file.');
  try {
    const bmp = await createImageBitmap(file, { imageOrientation: 'from-image' });
    state.src = bmp;
    state.img = { w: bmp.width, h: bmp.height };
  } catch {
    return showErr('This photo could not be opened. Try a JPG or PNG.');
  }
  const w = state.img.w * 0.35;
  state.box = { x: (state.img.w - w) / 2, y: state.img.h * 0.18, w, h: w * 1.3 };
  $('adjustCard').hidden = false;
  $('resultCard').hidden = false;
  $('detect').hidden = !('FaceDetector' in window);
  sizeEditor();
  refresh();
  $('adjustCard').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
}
function showErr(msg) { $('fileErr').textContent = msg; $('fileErr').hidden = false; }

// ---------- editor (head box drag) ----------
function sizeEditor() {
  const c = $('editor');
  const maxW = c.parentElement.clientWidth;
  const maxH = Math.max(320, window.innerHeight * 0.62);
  const s = Math.min(maxW / state.img.w, maxH / state.img.h);
  const dpr = window.devicePixelRatio || 1;
  state.scale = s;
  c.style.width = `${Math.round(state.img.w * s)}px`;
  c.style.height = `${Math.round(state.img.h * s)}px`;
  c.width = Math.round(state.img.w * s * dpr);
  c.height = Math.round(state.img.h * s * dpr);
}

function crop() { return computeCrop(state.spec, state.img, state.box); }

function drawEditor(cr) {
  const c = $('editor'), ctx = c.getContext('2d');
  const k = c.width / state.img.w;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.drawImage(state.src, 0, 0, c.width, c.height);
  ctx.setTransform(k, 0, 0, k, 0, 0);
  // dim what will be cut away
  ctx.fillStyle = 'rgba(0,0,0,0.45)';
  ctx.beginPath();
  ctx.rect(0, 0, state.img.w, state.img.h);
  ctx.rect(cr.x + cr.w, cr.y, -cr.w, cr.h); // reverse winding = hole
  ctx.fill('evenodd');
  const lw = 2 / k * (window.devicePixelRatio || 1);
  ctx.lineWidth = lw;
  ctx.strokeStyle = css('--hero-fg') || '#F4EEDC';
  ctx.strokeRect(cr.x, cr.y, cr.w, cr.h);
  const b = state.box;
  ctx.strokeStyle = css('--gold') || '#C38E12';
  ctx.lineWidth = lw * 1.5;
  ctx.beginPath();
  ctx.ellipse(b.x + b.w / 2, b.y + b.h / 2, b.w / 2, b.h / 2, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([lw * 4, lw * 3]);
  ctx.strokeRect(b.x, b.y, b.w, b.h);
  ctx.setLineDash([]);
  const r = 14 / state.scale;
  ctx.fillStyle = css('--gold') || '#C38E12';
  ctx.beginPath(); ctx.arc(b.x + b.w, b.y + b.h, r, 0, Math.PI * 2); ctx.fill();
}

function toImg(e) {
  const rect = $('editor').getBoundingClientRect();
  return { x: (e.clientX - rect.left) / rect.width * state.img.w, y: (e.clientY - rect.top) / rect.height * state.img.h };
}
function onDown(e) {
  if (!state.box) return;
  const p = toImg(e), b = state.box, hit = 26 / state.scale;
  const onHandle = Math.hypot(p.x - (b.x + b.w), p.y - (b.y + b.h)) < hit;
  const inside = p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h;
  if (!onHandle && !inside) return;
  state.drag = { mode: onHandle ? 'resize' : 'move', start: p, box: { ...b } };
  $('editor').setPointerCapture(e.pointerId);
  e.preventDefault();
}
function onMove(e) {
  const d = state.drag; if (!d) return;
  const p = toImg(e), dx = p.x - d.start.x, dy = p.y - d.start.y, min = 20;
  if (d.mode === 'move') state.box = { ...d.box, x: d.box.x + dx, y: d.box.y + dy };
  else state.box = { ...d.box, w: Math.max(min, d.box.w + dx), h: Math.max(min, d.box.h + dy) };
  scheduleRefresh();
}
function onUp() { state.drag = null; }
function resizeBy(f) {
  const b = state.box; if (!b) return;
  const w = b.w * f, h = b.h * f;
  state.box = { x: b.x - (w - b.w) / 2, y: b.y - (h - b.h) / 2, w, h };
  refresh();
}

async function detectFace() {
  const msg = $('detectMsg');
  try {
    const fd = new window.FaceDetector({ fastMode: false, maxDetectedFaces: 3 });
    const faces = await fd.detect(state.src);
    if (!faces.length) { msg.textContent = 'No face found. Fit the box by hand.'; return; }
    const f = faces.map(x => x.boundingBox).sort((a, b) => b.width * b.height - a.width * a.height)[0];
    state.box = faceToHead({ x: f.x, y: f.y, w: f.width, h: f.height });
    msg.textContent = 'Face found. Check the box reaches the top of your hair and your chin.';
    refresh();
  } catch {
    msg.textContent = 'Face finder is not available on this browser. Fit the box by hand.';
  }
}

// ---------- rendering the photo ----------
// Draw the crop into a w x h canvas, padding anything past the photo edge with the rule's background colour.
function renderPhoto(cr, w, h, withBg) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d', { willReadFrequently: withBg });
  ctx.fillStyle = state.spec.fill_hex;
  ctx.fillRect(0, 0, w, h);
  const sx = Math.max(0, cr.x), sy = Math.max(0, cr.y);
  const ex = Math.min(state.img.w, cr.x + cr.w), ey = Math.min(state.img.h, cr.y + cr.h);
  if (ex > sx && ey > sy) {
    const k = w / cr.w;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(state.src, sx, sy, ex - sx, ey - sy, (sx - cr.x) * k, (sy - cr.y) * k, (ex - sx) * k, (ey - sy) * k);
  }
  if (withBg) {
    const data = ctx.getImageData(0, 0, w, h);
    replaceBackground(data.data, w, h, { fill: state.spec.fill_hex, threshold: Number($('bgThr').value) });
    ctx.putImageData(data, 0, 0);
  }
  return c;
}

function outMode() { const v = $('outMode').value; return v === 'digital' ? 'digital' : Number(v); }

function drawChecks(result) {
  const ic = { pass: '✓', warn: '!', fail: '✗' };
  $('checks').innerHTML = result.reasons.map(r =>
    `<li class="${esc(r.level)}"><span class="ic" aria-label="${esc(r.level)}">${esc(ic[r.level])}</span><span>${esc(r.msg)}</span></li>`).join('');
}

function refresh() {
  if (!state.src) return;
  const cr = crop();
  drawEditor(cr);
  const pw = 300, ph = Math.round(pw * cr.h / cr.w);
  const prev = renderPhoto(cr, pw, ph, $('bgOn').checked);
  const pc = $('preview');
  pc.width = pw; pc.height = ph;
  pc.getContext('2d').drawImage(prev, 0, 0);
  drawChecks(validate(state.spec, { image: state.img, crop: cr, out: outputSize(state.spec, outMode()) }));
  const L = sheetLayout(state.spec.print_mm, $('sheet').value);
  $('sheetInfo').textContent = `${L.count} photos fit on ${SHEETS[$('sheet').value].label} (${L.cols} x ${L.rows}, ${L.orient}).`;
}
let raf = 0;
function scheduleRefresh() { if (!raf) raf = requestAnimationFrame(() => { raf = 0; refresh(); }); }

// ---------- saving ----------
const toBlob = (c, q) => new Promise(r => c.toBlob(r, 'image/jpeg', q));
function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: name });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

async function savePhoto() {
  const cr = crop(), mode = outMode();
  const out = outputSize(state.spec, mode);
  const c = renderPhoto(cr, out.w, out.h, $('bgOn').checked);
  const kb = mode === 'digital' ? state.spec.digital?.file_kb : null;
  let q = 0.92, blob = await toBlob(c, q);
  // Fit the upload file-size rule: lower quality if too big, raise it if too small.
  while (kb?.max && blob.size > kb.max * 1024 && q > 0.4) { q -= 0.08; blob = await toBlob(c, q); }
  if (kb?.min && blob.size < kb.min * 1024) blob = await toBlob(c, 1);
  drawChecks(validate(state.spec, { image: state.img, crop: cr, out, fileBytes: blob.size }));
  download(blob, `kalpa-${state.spec.id}-${out.w}x${out.h}.jpg`);
}

async function saveSheet() {
  const cr = crop(), dpi = 300;
  const L = sheetLayout(state.spec.print_mm, $('sheet').value);
  if (!L.count) return;
  const c = document.createElement('canvas');
  c.width = mmToPx(L.sheet.w, dpi); c.height = mmToPx(L.sheet.h, dpi);
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#FFFFFF'; ctx.fillRect(0, 0, c.width, c.height);
  const pw = mmToPx(state.spec.print_mm.w, dpi), ph = mmToPx(state.spec.print_mm.h, dpi);
  const photo = renderPhoto(cr, pw, ph, $('bgOn').checked);
  const px = mm => Math.round(mm / 25.4 * dpi);
  ctx.strokeStyle = '#BBBBBB'; ctx.lineWidth = 1;
  for (const p of L.positions) {
    ctx.drawImage(photo, px(p.x), px(p.y), pw, ph);
    ctx.strokeRect(px(p.x) - 0.5, px(p.y) - 0.5, pw + 1, ph + 1);
  }
  download(await toBlob(c, 0.95), `kalpa-${state.spec.id}-sheet-${$('sheet').value}.jpg`);
}

// ---------- wire up ----------
$('spec').addEventListener('change', e => pickSpec(e.target.value));
$('file').addEventListener('change', e => loadFile(e.target.files[0]));
const ed = $('editor');
ed.addEventListener('pointerdown', onDown);
ed.addEventListener('pointermove', onMove);
ed.addEventListener('pointerup', onUp);
ed.addEventListener('pointercancel', onUp);
$('smaller').addEventListener('click', () => resizeBy(0.95));
$('bigger').addEventListener('click', () => resizeBy(1.05));
$('detect').addEventListener('click', detectFace);
$('bgOn').addEventListener('change', () => { $('bgTune').hidden = $('bgNote').hidden = !$('bgOn').checked; refresh(); });
$('bgThr').addEventListener('input', scheduleRefresh);
$('outMode').addEventListener('change', refresh);
$('sheet').addEventListener('change', refresh);
$('savePhoto').addEventListener('click', savePhoto);
$('saveSheet').addEventListener('click', saveSheet);
window.addEventListener('resize', () => { if (state.src) { sizeEditor(); refresh(); } });

loadSpecs();
if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
  navigator.serviceWorker.register('sw.js');
}

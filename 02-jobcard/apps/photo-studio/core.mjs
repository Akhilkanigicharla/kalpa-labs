// Kalpa Photo Studio core: pure maths for passport/visa photos.
// No DOM, no network. Runs in the browser (ES module) and in `node --test`.
// Units: source image in pixels, photo rules in millimetres, sheets in millimetres.

export const MM_PER_INCH = 25.4;

// Head-box rules used when the photo rule has no number of its own (shown to the user as a fallback).
export const FALLBACK_HEAD_PCT = { min: 50, max: 70 };
// Where the eyes sit inside the head box, measured down from the crown (fraction of head height).
export const EYE_FROM_CROWN = 0.48;
// With no eye-line rule, this share of the spare height goes above the head (the rest below the chin).
export const TOP_GAP_SHARE = 0.4;

export const SHEETS = {
  '4x6': { label: '4 x 6 inch photo paper', w: 101.6, h: 152.4 },
  A4: { label: 'A4 paper', w: 210, h: 297 },
};

export function mmToPx(mm, dpi) {
  if (!(mm > 0) || !(dpi > 0)) throw new RangeError('mm and dpi must be positive');
  return Math.round((mm / MM_PER_INCH) * dpi);
}

// A face detector box usually runs from the eyebrows/forehead to the chin.
// Passport rules measure chin to crown (top of hair), so grow the box upwards.
export function faceToHead(face, { crownExtra = 0.45, chinExtra = 0.05, widthExtra = 0.1 } = {}) {
  const { x, y, w, h } = face;
  const nw = w * (1 + widthExtra);
  return { x: x - (nw - w) / 2, y: y - h * crownExtra, w: nw, h: h * (1 + crownExtra + chinExtra) };
}

// Target head height in mm for a spec: {min, max, target, source}.
export function headRangeMm(spec) {
  const H = spec.print_mm.h;
  if (spec.head_mm) {
    const { min, max } = spec.head_mm;
    return { min, max, target: (min + max) / 2, source: 'rule' };
  }
  const pct = spec.head_pct || FALLBACK_HEAD_PCT;
  const min = (H * pct.min) / 100;
  const max = (H * pct.max) / 100;
  return { min, max, target: (min + max) / 2, source: spec.head_pct ? 'rule' : 'fallback' };
}

// Crop rectangle in source pixels that puts the head at the target size and centres it.
// box = head box (crown to chin) unless boxIs === 'face', then it is grown with faceToHead.
// The rectangle may run past the image edges; `overflow` says by how much (the export pads it).
export function computeCrop(spec, image, box, { boxIs = 'head', faceOpts } = {}) {
  if (!(image.w > 0 && image.h > 0)) throw new RangeError('image size must be positive');
  if (!(box.w > 0 && box.h > 0)) throw new RangeError('box size must be positive');
  const head = boxIs === 'face' ? faceToHead(box, faceOpts) : { ...box };
  const { w: W, h: H } = spec.print_mm;
  const range = headRangeMm(spec);
  const pxPerMm = head.h / range.target;
  const cw = W * pxPerMm;
  const ch = H * pxPerMm;

  let topGapMm;
  if (spec.eye_from_bottom_mm) {
    const eye = (spec.eye_from_bottom_mm.min + spec.eye_from_bottom_mm.max) / 2;
    topGapMm = H - eye - EYE_FROM_CROWN * range.target;
  } else {
    topGapMm = (H - range.target) * TOP_GAP_SHARE;
  }
  topGapMm = Math.max(0, Math.min(topGapMm, H - range.target));

  const x = head.x + head.w / 2 - cw / 2;
  const y = head.y - topGapMm * pxPerMm;
  const overflow = {
    left: Math.max(0, -x),
    top: Math.max(0, -y),
    right: Math.max(0, x + cw - image.w),
    bottom: Math.max(0, y + ch - image.h),
  };
  const inside = Object.values(overflow).every(v => v < 0.5);
  return { x, y, w: cw, h: ch, pxPerMm, head, headMm: range.target, headRange: range, overflow, inside };
}

// Output pixel size: mode 300 or 600 (dpi print size) or 'digital' (online upload rule).
export function outputSize(spec, mode = 300) {
  const { w, h } = spec.print_mm;
  if (mode === 'digital') {
    const d = spec.digital;
    if (!d) return { ...outputSize(spec, 300), note: 'No upload rule stored; using 300 dpi print size' };
    // Smallest size that meets the minimum, shaped like the print photo (or square).
    const ratio = d.square ? 1 : h / w;
    let ow = d.min_px.w;
    let oh = Math.round(ow * ratio);
    if (oh < d.min_px.h) { oh = d.min_px.h; ow = Math.round(oh / ratio); }
    if (d.max_px && (ow > d.max_px.w || oh > d.max_px.h)) {
      const k = Math.min(d.max_px.w / ow, d.max_px.h / oh);
      ow = Math.floor(ow * k); oh = Math.floor(oh * k);
    }
    return { w: ow, h: oh, dpi: null };
  }
  if (mode !== 300 && mode !== 600) throw new RangeError('mode must be 300, 600 or "digital"');
  return { w: mmToPx(w, mode), h: mmToPx(h, mode), dpi: mode };
}

function grid(photo, area, gap) {
  const cols = Math.floor((area.w + gap) / (photo.w + gap));
  const rows = Math.floor((area.h + gap) / (photo.h + gap));
  return { cols: Math.max(0, cols), rows: Math.max(0, rows) };
}

// How many photos fit on a sheet, and where (mm from the sheet's top-left).
// Tries the sheet both ways round and keeps the better one; the block is centred.
export function sheetLayout(photoMm, sheet = '4x6', { margin = 5, gap = 2 } = {}) {
  const base = typeof sheet === 'string' ? SHEETS[sheet] : sheet;
  if (!base) throw new RangeError(`unknown sheet ${sheet}`);
  let best = null;
  for (const orient of ['portrait', 'landscape']) {
    const S = orient === 'portrait' ? { w: base.w, h: base.h } : { w: base.h, h: base.w };
    const area = { w: S.w - 2 * margin, h: S.h - 2 * margin };
    const { cols, rows } = grid(photoMm, area, gap);
    const count = cols * rows;
    if (!best || count > best.count) best = { orient, sheet: S, cols, rows, count };
  }
  const { cols, rows, sheet: S } = best;
  const blockW = cols * photoMm.w + Math.max(0, cols - 1) * gap;
  const blockH = rows * photoMm.h + Math.max(0, rows - 1) * gap;
  const ox = (S.w - blockW) / 2;
  const oy = (S.h - blockH) / 2;
  const positions = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    positions.push({ x: ox + c * (photoMm.w + gap), y: oy + r * (photoMm.h + gap), w: photoMm.w, h: photoMm.h });
  }
  return { ...best, margin, gap, positions };
}

// Check a crop against a spec. Returns { pass, reasons: [{ level, code, msg }] }.
// level: 'pass' | 'warn' | 'fail'. pass is false when any reason is 'fail'.
export function validate(spec, { image, crop, out, fileBytes } = {}) {
  const reasons = [];
  const add = (level, code, msg) => reasons.push({ level, code, msg });
  const H = spec.print_mm.h;

  if (!spec.verified) add('warn', 'spec-unchecked', 'This photo rule is not checked against the official page yet');

  if (crop) {
    const k = crop.pxPerMm;
    const head = crop.head;
    const headMm = head.h / k;
    const range = headRangeMm(spec);
    const t = 0.05; // rounding slack, mm
    if (headMm < range.min - t) add('fail', 'head-small', `Head is ${headMm.toFixed(1)} mm; needs at least ${range.min.toFixed(1)} mm`);
    else if (headMm > range.max + t) add('fail', 'head-big', `Head is ${headMm.toFixed(1)} mm; needs at most ${range.max.toFixed(1)} mm`);
    else add('pass', 'head-size', `Head is ${headMm.toFixed(1)} mm (${range.min.toFixed(1)} to ${range.max.toFixed(1)} mm)`);
    if (range.source === 'fallback') add('warn', 'head-fallback', 'No head-size number in this rule; a general size was used');

    const off = Math.abs(head.x + head.w / 2 - (crop.x + crop.w / 2)) / crop.w;
    if (off > 0.03) add('fail', 'off-centre', `Head is ${(off * 100).toFixed(1)}% off centre`);
    else add('pass', 'centred', 'Head is centred');

    const crownMm = (head.y - crop.y) / k;
    if (crownMm < 0) add('fail', 'crown-cut', 'Top of the head is cut off');
    const chinFromBottom = H - (head.y + head.h - crop.y) / k;
    if (chinFromBottom < 0) add('fail', 'chin-cut', 'Chin is cut off');

    if (spec.eye_from_bottom_mm) {
      const eye = H - (head.y + EYE_FROM_CROWN * head.h - crop.y) / k;
      const { min, max } = spec.eye_from_bottom_mm;
      if (eye < min - t || eye > max + t) add('fail', 'eye-line', `Eyes are ${eye.toFixed(1)} mm from the bottom; needs ${min} to ${max} mm`);
      else add('pass', 'eye-line', `Eyes are ${eye.toFixed(1)} mm from the bottom`);
    }

    if (image) {
      const o = crop.overflow;
      const worst = Math.max(o.left / crop.w, o.right / crop.w, o.top / crop.h, o.bottom / crop.h);
      if (worst > 0.15) add('fail', 'too-tight', 'Photo is too close up; the frame runs far past the edge. Stand further back');
      else if (worst > 0.005) add('warn', 'padded', 'Frame runs past the photo edge; it will be filled with the background colour');
    }

    if (out) {
      const scale = out.h / crop.h;
      if (scale > 2) add('fail', 'low-res', 'Photo is too small for this size; it would look blurry');
      else if (scale > 1.01) add('warn', 'upscaled', `Photo is stretched ${scale.toFixed(2)}x; a sharper photo is better`);
      else add('pass', 'resolution', 'Enough detail for this size');
    }
  }

  const d = spec.digital;
  if (d && out && out.dpi === null) {
    if (out.w < d.min_px.w || out.h < d.min_px.h) add('fail', 'px-small', `File is ${out.w} x ${out.h} px; needs at least ${d.min_px.w} x ${d.min_px.h}`);
    else if (d.max_px && (out.w > d.max_px.w || out.h > d.max_px.h)) add('fail', 'px-big', `File is ${out.w} x ${out.h} px; needs at most ${d.max_px.w} x ${d.max_px.h}`);
    else add('pass', 'px', `File is ${out.w} x ${out.h} px`);
    if (d.square && out.w !== out.h) add('fail', 'not-square', 'Upload must be square');
  }
  if (d && d.file_kb && fileBytes != null) {
    const kb = fileBytes / 1024;
    if (d.file_kb.min != null && kb < d.file_kb.min) add('fail', 'file-small', `File is ${kb.toFixed(0)} KB; needs at least ${d.file_kb.min} KB`);
    else if (d.file_kb.max != null && kb > d.file_kb.max) add('fail', 'file-big', `File is ${kb.toFixed(0)} KB; needs at most ${d.file_kb.max} KB`);
    else add('pass', 'file-size', `File is ${kb.toFixed(0)} KB`);
  }

  return { pass: !reasons.some(r => r.level === 'fail'), reasons };
}

export function hexToRgb(hex) {
  const n = parseInt(hex.replace('#', ''), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

// BETA background swap: flood fill from the top edge and the upper part of the side edges,
// replacing pixels close in colour to the average top-edge colour. Mutates RGBA `data`.
// Works only on a plain, evenly lit wall behind the person. Returns the number of pixels changed.
export function replaceBackground(data, w, h, { fill = '#FFFFFF', threshold = 40, sideSeedShare = 0.6 } = {}) {
  if (data.length !== w * h * 4) throw new RangeError('data length must be w*h*4');
  let r0 = 0, g0 = 0, b0 = 0;
  for (let x = 0; x < w; x++) { const i = x * 4; r0 += data[i]; g0 += data[i + 1]; b0 += data[i + 2]; }
  r0 /= w; g0 /= w; b0 /= w;
  const t2 = threshold * threshold;
  const near = p => { const i = p * 4, dr = data[i] - r0, dg = data[i + 1] - g0, db = data[i + 2] - b0; return dr * dr + dg * dg + db * db <= t2; };
  const seen = new Uint8Array(w * h);
  const stack = [];
  const push = p => { if (!seen[p] && near(p)) { seen[p] = 1; stack.push(p); } };
  for (let x = 0; x < w; x++) push(x);
  const sideRows = Math.floor(h * sideSeedShare);
  for (let y = 0; y < sideRows; y++) { push(y * w); push(y * w + w - 1); }
  const [fr, fg, fb] = hexToRgb(fill);
  let n = 0;
  while (stack.length) {
    const p = stack.pop();
    const i = p * 4; data[i] = fr; data[i + 1] = fg; data[i + 2] = fb; n++;
    const x = p % w, y = (p - x) / w;
    if (x > 0) push(p - 1);
    if (x < w - 1) push(p + 1);
    if (y > 0) push(p - w);
    if (y < h - 1) push(p + w);
  }
  return n;
}

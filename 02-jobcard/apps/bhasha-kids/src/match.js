// Say-it check: compare what the browser heard with the target word.
// Works on Unicode code points after NFC, so Telugu/Devanagari vowel signs count.

export function normalize(s) {
  return String(s || '')
    .normalize('NFC')
    .toLowerCase()
    .replace(/_{2,}/g, ' ')
    .replace(/[\s.,!?;:'"()।॥‌‍-]+/g, ' ')
    .trim();
}

export function levenshtein(a, b) {
  const x = [...a], y = [...b];
  if (!x.length) return y.length;
  if (!y.length) return x.length;
  let prev = Array.from({ length: y.length + 1 }, (_, i) => i);
  for (let i = 1; i <= x.length; i++) {
    const cur = [i];
    for (let j = 1; j <= y.length; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x[i - 1] === y[j - 1] ? 0 : 1));
    }
    prev = cur;
  }
  return prev[y.length];
}

export function similarity(a, b) {
  const x = normalize(a), y = normalize(b);
  if (!x && !y) return 1;
  const n = Math.max([...x].length, [...y].length);
  return 1 - levenshtein(x, y) / n;
}

// heard: array of alternatives from SpeechRecognition. Accepts the item's
// script or its transliteration (some recognisers answer in Latin letters).
export function judge(heard, item, threshold = 0.7) {
  const targets = [item.script, item.translit].map(normalize).filter(Boolean);
  let best = 0, bestText = '';
  for (const h of heard || []) {
    const nh = normalize(h);
    if (!nh) continue;
    for (const t of targets) {
      const sc = nh === t || nh.split(' ').includes(t) ? 1 : similarity(nh, t);
      if (sc > best) { best = sc; bestText = h; }
    }
  }
  return { ok: best >= threshold, score: Math.round(best * 100) / 100, heard: bestText };
}

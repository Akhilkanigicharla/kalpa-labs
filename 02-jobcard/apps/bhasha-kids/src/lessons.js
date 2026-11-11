// Turns a language file (data/te.json, data/hi.json) into lessons, checks the
// file's shape, and builds match-game rounds.

export function lessonsFor(data) {
  const out = [
    { id: 'vowels', title: 'Vowels', kind: 'letters', items: data.letters.vowels },
    { id: 'consonants', title: 'Consonants', kind: 'letters', items: data.letters.consonants },
  ];
  for (const t of data.themes) out.push({ id: t.id, title: t.title, kind: 'words', items: t.words });
  out.push({ id: 'phrases', title: 'Phrases', kind: 'phrases', items: data.phrases });
  return out;
}

const SCRIPT_RANGES = { te: /[ఀ-౿]/, hi: /[ऀ-ॿ]/ };

// Returns a list of problems; empty means the file is usable.
export function validateLang(data) {
  const errs = [];
  if (!data || typeof data !== 'object') return ['not an object'];
  if (data.native_speaker_checked !== false && data.native_speaker_checked !== true) errs.push('native_speaker_checked missing');
  const re = SCRIPT_RANGES[data.lang];
  if (!re) errs.push(`unknown lang ${data.lang}`);
  if (!/^[a-z]{2}-IN$/.test(data.speech_lang || '')) errs.push('speech_lang must look like te-IN');
  const ids = new Set();
  const check = (it, where) => {
    for (const f of ['id', 'script', 'translit', 'en']) {
      if (typeof it[f] !== 'string' || !it[f].trim()) errs.push(`${where}: ${f} missing`);
    }
    if (ids.has(it.id)) errs.push(`${where}: duplicate id ${it.id}`);
    ids.add(it.id);
    if (re && !re.test(it.script || '')) errs.push(`${where}: script is not ${data.lang} script`);
    if (/[^\x20-\x7E]/.test(it.translit || '')) errs.push(`${where}: transliteration must be plain ASCII`);
    if (it.id && !it.id.startsWith(`${data.lang}-`)) errs.push(`${where}: id must start with ${data.lang}-`);
  };
  if (!data.letters || !Array.isArray(data.letters.vowels) || !Array.isArray(data.letters.consonants)) errs.push('letters missing');
  else {
    data.letters.vowels.forEach((it, i) => check(it, `vowel ${i}`));
    data.letters.consonants.forEach((it, i) => check(it, `consonant ${i}`));
  }
  if (!Array.isArray(data.themes)) errs.push('themes missing');
  else data.themes.forEach(t => {
    if (!Array.isArray(t.words) || t.words.length < 8) errs.push(`theme ${t.id}: needs 8+ words`);
    else t.words.forEach((w, i) => check(w, `${t.id} ${i}`));
  });
  if (!Array.isArray(data.phrases)) errs.push('phrases missing');
  else data.phrases.forEach((p, i) => check(p, `phrase ${i}`));
  return errs;
}

// Fisher-Yates with an injectable random source (tests pass a seeded one).
export function shuffle(arr, rand = Math.random) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// A match round: n pairs, left = script, right = English, both shuffled.
export function matchRound(items, n = 4, rand = Math.random) {
  const pick = shuffle(items, rand).slice(0, Math.min(n, items.length));
  return {
    pairs: pick.map(it => it.id),
    left: shuffle(pick.map(it => ({ id: it.id, text: it.script })), rand),
    right: shuffle(pick.map(it => ({ id: it.id, text: it.en })), rand),
  };
}

export function seeded(seed = 1) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

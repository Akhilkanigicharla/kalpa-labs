// Browser speech, feature-detected. Nothing here calls our servers or any API we chose.
// Listen: speechSynthesis with a te-IN / hi-IN voice when the device has one.
// Say it: SpeechRecognition ON-DEVICE only (processLocally = true). Browsers that
// cannot promise on-device recognition send audio to their maker's servers
// (MDN, "Using the Web Speech API"), so that path stays off unless a parent turns
// on "browser speech service" in the parent screen.

export function pickVoice(voices, lang) {
  const list = Array.from(voices || []);
  const want = lang.toLowerCase(), base = want.split('-')[0];
  return list.find(v => (v.lang || '').toLowerCase().replace('_', '-') === want)
    || list.find(v => (v.lang || '').toLowerCase().startsWith(base))
    || null;
}

export function ttsSupport(win) {
  return !!(win && win.speechSynthesis && typeof win.SpeechSynthesisUtterance === 'function');
}

// Resolves to the voice list; some browsers fill it only after 'voiceschanged'.
export function loadVoices(win, timeoutMs = 1200) {
  if (!ttsSupport(win)) return Promise.resolve([]);
  const now = win.speechSynthesis.getVoices();
  if (now && now.length) return Promise.resolve(now);
  return new Promise(res => {
    const done = () => res(win.speechSynthesis.getVoices() || []);
    try { win.speechSynthesis.addEventListener('voiceschanged', done, { once: true }); } catch { /* old Safari */ }
    setTimeout(done, timeoutMs);
  });
}

export function speak(win, text, lang, voice, rate = 0.8) {
  if (!ttsSupport(win) || !voice) return false;
  try {
    win.speechSynthesis.cancel();
    const u = new win.SpeechSynthesisUtterance(text.replace(/_{2,}/g, ' '));
    u.lang = voice.lang || lang; u.voice = voice; u.rate = rate;
    win.speechSynthesis.speak(u);
    return true;
  } catch { return false; }
}

export function recognitionCtor(win) {
  return (win && (win.SpeechRecognition || win.webkitSpeechRecognition)) || null;
}

// mode: 'local' (on-device, ready), 'local-download' (needs a one-time language pack),
// 'cloud' (only the browser's server service; needs parent opt-in), 'none'.
export async function recognitionMode(win, lang) {
  const R = recognitionCtor(win);
  if (!R) return 'none';
  if (typeof R.available === 'function') {
    try {
      const local = await R.available({ langs: [lang], processLocally: true });
      if (local === 'available') return 'local';
      if (local === 'downloadable' || local === 'downloading') return 'local-download';
      const any = await R.available({ langs: [lang], processLocally: false });
      return any === 'available' ? 'cloud' : 'none';
    } catch { return 'none'; }
  }
  return 'cloud'; // old API: cannot promise on-device, assume server-based
}

export function sayItAllowed(mode, cloudOptIn) {
  return mode === 'local' || (mode === 'cloud' && cloudOptIn === true);
}

// One listen attempt. Resolves to an array of heard alternatives ([] on silence/error).
export function listenOnce(win, lang, { local = true, timeoutMs = 7000 } = {}) {
  const R = recognitionCtor(win);
  if (!R) return Promise.resolve({ heard: [], error: 'unsupported' });
  return new Promise(resolve => {
    let settled = false;
    const finish = (heard, error) => { if (!settled) { settled = true; resolve({ heard, error }); } };
    let rec;
    try {
      rec = new R();
      rec.lang = lang; rec.interimResults = false; rec.maxAlternatives = 5; rec.continuous = false;
      if (local) rec.processLocally = true;
      rec.onresult = e => {
        const alts = [];
        const r = e.results && e.results[0];
        if (r) for (let i = 0; i < r.length; i++) alts.push(r[i].transcript);
        finish(alts, null);
      };
      rec.onerror = e => finish([], e.error || 'error');
      rec.onend = () => finish([], 'no-speech');
      rec.start();
    } catch (e) { finish([], 'start-failed'); }
    setTimeout(() => { try { rec && rec.stop(); } catch { /* ignore */ } finish([], 'timeout'); }, timeoutMs);
  });
}

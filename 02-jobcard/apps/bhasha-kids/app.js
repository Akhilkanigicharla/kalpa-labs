// Kalpa Bhasha Kids: UI. No network calls except loading our own files from this
// folder; no accounts; progress lives in localStorage on this device only.
import { GRADES, dayKey, dueQueue, isDue } from './src/srs.js';
import { normalizeState, recordReview, recordLesson, lessonStars, liveStreak, parentSummary, summaryLine, newState } from './src/progress.js';
import { lessonsFor, matchRound, shuffle } from './src/lessons.js';
import { makeChallenge, checkAnswer } from './src/gate.js';
import { judge } from './src/match.js';
import { makeStore, browserBackend } from './src/storage.js';
import { loadVoices, pickVoice, speak, ttsSupport, recognitionMode, recognitionCtor, sayItAllowed, listenOnce } from './src/speech.js';

const LANGS = ['te', 'hi'];
const app = document.getElementById('app');
const live = document.getElementById('live');
const store = makeStore(browserBackend());
let state = normalizeState(store.load());
const data = {}, lessons = {}, voice = {}, rec = {};
let view = { name: 'home' };

const today = () => dayKey(new Date());
const lang = () => (LANGS.includes(state.settings.lang) ? state.settings.lang : 'te');
const save = () => store.save(state);
const say = msg => { live.textContent = ''; setTimeout(() => { live.textContent = msg; }, 30); };
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const STAR = on => `<svg viewBox="0 0 24 24" aria-hidden="true"><path class="${on ? 'star-on' : 'star-off'}" d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>`;
const stars = (n, cls = 'stars') => `<span class="${cls}" role="img" aria-label="${n} of 3 stars">${[0, 1, 2].map(i => STAR(i < n)).join('')}</span>`;
const SPEAKER = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4zm12.5 3a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4zM14 3.2v2.1a7 7 0 0 1 0 13.4v2.1a9 9 0 0 0 0-17.6z"/></svg>';
const MIC = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.9V21h2v-3.1A7 7 0 0 0 19 11h-2z"/></svg>';

async function boot() {
  try {
    await Promise.all(LANGS.map(async l => {
      const r = await fetch(`data/${l}.json`);
      if (!r.ok) throw new Error(`data/${l}.json ${r.status}`);
      data[l] = await r.json();
      lessons[l] = lessonsFor(data[l]);
    }));
  } catch (e) {
    app.innerHTML = `<p class="note">Lessons could not load (${esc(e.message)}). Open this app from a local web server, see README.</p>`;
    return;
  }
  render();
  const voices = await loadVoices(window);
  for (const l of LANGS) {
    voice[l] = pickVoice(voices, data[l].speech_lang);
    rec[l] = await recognitionMode(window, data[l].speech_lang);
  }
  render();
  if ('serviceWorker' in navigator && location.protocol !== 'file:') navigator.serviceWorker.register('sw.js').catch(() => {});
}

function scriptClass(l) { return l === 'hi' ? 'hi' : 'te'; }
function setStreak() {
  const n = liveStreak(state.streak, today());
  const el = document.getElementById('streak');
  el.textContent = n ? `Streak ${n}` : '';
  el.setAttribute('aria-label', n ? `${n} day streak` : '');
}
function lessonById(l, id) {
  if (id === 'review') {
    const cards = state.langs[l]?.cards || {};
    const all = lessons[l].flatMap(x => x.items);
    const due = all.filter(it => cards[it.id]?.seen && isDue(cards[it.id], today()));
    return { id: 'review', title: 'Practice today', kind: 'words', items: due };
  }
  return lessons[l].find(x => x.id === id);
}
function kindOf(item, les) {
  if (les.kind !== 'words') return les.kind;
  return item.id.includes('-v-') || item.id.includes('-c-') ? 'letters' : item.script.length > 14 ? 'phrases' : 'words';
}

function render() {
  setStreak();
  const fn = { home: renderHome, lesson: renderLesson, gate: renderGate, parent: renderParent }[view.name] || renderHome;
  app.innerHTML = `<div class="view">${fn()}</div>`;
  app.querySelectorAll('[data-w]').forEach(el => { el.style.width = `${el.dataset.w}%`; });
  app.querySelectorAll('[data-h]').forEach(el => { el.style.height = `${el.dataset.h}%`; });
  if (view.focus) { app.querySelector(view.focus)?.focus(); view.focus = null; }
}
function go(v) { view = v; render(); window.scrollTo(0, 0); app.focus({ preventScroll: true }); }

// ---------- home ----------
function renderHome() {
  const l = lang(), d = data[l];
  const due = lessonById(l, 'review').items.length;
  const tiles = lessons[l].map(les => `
    <li><button class="tile" data-act="open" data-id="${les.id}">
      <span class="big ${scriptClass(l)}" lang="${l}">${esc(les.items[0].script.replace(/_{2,}.*/, '').trim())}</span>
      <span class="name">${esc(les.title)}</span>
      ${stars(lessonStars(state, l, les.id))}
    </button></li>`).join('');
  return `
    <div class="pills" role="group" aria-label="Language">
      ${LANGS.map(x => `<button class="pill ${scriptClass(x)}" data-act="lang" data-lang="${x}" aria-pressed="${x === l}">${esc(data[x].native_name)} · ${esc(data[x].name)}</button>`).join('')}
    </div>
    <section class="today">
      <div><h1>Practice today</h1><p>${due ? `${due} word${due === 1 ? '' : 's'} ready to review` : 'Pick any lesson below to start'}</p></div>
      ${due ? '<button class="btn gold" data-act="open" data-id="review">Start</button>' : ''}
    </section>
    <ul class="grid" aria-label="${esc(d.name)} lessons">${tiles}</ul>`;
}

// ---------- lesson ----------
function startLesson(id, mode = 'cards') {
  const l = lang(), les = lessonById(l, id);
  if (!les || !les.items.length) return go({ name: 'home' });
  const s = { name: 'lesson', id, mode, i: 0, right: 0, total: 0, flipped: false, done: false, msg: '' };
  if (mode === 'cards') {
    const ids = les.items.map(x => x.id);
    let q = id === 'review' ? ids.slice(0, 12) : dueQueue(ids, state.langs[l]?.cards || {}, today(), 10);
    if (!q.length) q = shuffle(ids).slice(0, 10);
    s.queue = q;
  } else if (mode === 'match') {
    s.round = matchRound(les.items, 4);
    s.matched = []; s.missed = []; s.pick = null;
  } else {
    s.queue = shuffle(les.items.map(x => x.id)).slice(0, 5);
    s.tries = 0;
  }
  go(s);
}

function modeTabs(les) {
  const l = lang();
  const canSay = sayItAllowed(rec[l], state.settings.cloudSpeech);
  const tab = (m, label, dis) => `<button class="pill" data-act="mode" data-mode="${m}" aria-pressed="${view.mode === m}"${dis ? ' disabled' : ''}>${label}</button>`;
  return `<div class="pills" role="group" aria-label="Game">
    ${tab('cards', 'Cards')}${les.items.length >= 2 ? tab('match', 'Match') : ''}${tab('say', 'Say it', !canSay)}
  </div>${canSay ? '' : `<p class="small">Say it is off: ${esc(sayItReason(l))}</p>`}`;
}
function sayItReason(l) {
  return {
    none: 'it does not work in this browser.',
    'local-download': 'a grown-up needs to download a speech pack first.',
    cloud: 'a grown-up needs to turn it on first.',
  }[rec[l]] || 'checking this device.';
}

function itemFor(id) { return lessons[lang()].flatMap(x => x.items).find(x => x.id === id); }

function renderLesson() {
  const l = lang(), les = lessonById(l, view.id);
  if (!les) return renderHome();
  const head = `<div class="bar"><button class="back" data-act="home" aria-label="Back to lessons">&lt;</button><h1>${esc(les.title)}</h1>${stars(lessonStars(state, l, les.id))}</div>`;
  if (view.done) return head + modeTabs(les) + doneCard();
  const body = view.mode === 'match' ? matchBody(les) : view.mode === 'say' ? sayBody(les) : cardBody(les);
  return head + modeTabs(les) + body;
}

function listenBtn(item) {
  const l = lang();
  const fb = view.fallback === item.id ? `<p class="fallback" role="status">No ${esc(data[l].name)} voice on this device. Ask a grown-up to read it out: <b>${esc(item.translit)}</b></p>` : '';
  return `<button class="btn ghost listen" data-act="listen" data-id="${item.id}">${SPEAKER}Listen</button>${fb}`;
}

function cardBody(les) {
  const l = lang(), id = view.queue[view.i], item = itemFor(id), k = kindOf(item, les);
  const pct = Math.round((view.i / view.queue.length) * 100);
  const ex = item.example ? `<p class="ex">as in <span class="${scriptClass(l)}" lang="${l}">${esc(item.example.script)}</span></p>` : '';
  const ans = view.flipped ? `<div class="answer">
      <p class="translit">${esc(item.translit)}</p>
      <p class="en">${esc(item.en)}</p>
      ${item.example ? `<p class="small">${esc(item.example.translit)}: ${esc(item.example.en)}</p>` : ''}
      ${item.note ? `<p class="small">${esc(item.note)}</p>` : ''}
    </div>` : '';
  const actions = view.flipped
    ? `<div class="grades" role="group" aria-label="How did you do?">
        <button class="btn again" data-act="grade" data-g="again">Again</button>
        <button class="btn" data-act="grade" data-g="good">I knew it</button>
        <button class="btn gold" data-act="grade" data-g="easy">Easy</button></div>`
    : `<button class="btn wide" data-act="flip" id="flip">Show me</button>`;
  return `<p class="count">${view.i + 1} / ${view.queue.length}</p>
    <div class="progress"><i data-w="${pct}"></i></div>
    <div class="card">
      <p class="script ${k} ${scriptClass(l)}" lang="${l}">${esc(item.script)}</p>${ex}
      ${listenBtn(item)}${ans}
    </div>${actions}`;
}

function matchBody(les) {
  const l = lang(), r = view.round, letters = les.kind === 'letters';
  const rightText = it => (letters ? itemFor(it.id).translit : it.text);
  const btn = (side, it, txt) => {
    const done = view.matched.includes(it.id);
    const pressed = view.pick && view.pick.side === side && view.pick.id === it.id;
    return `<button class="m ${side === 'L' ? `script-side ${scriptClass(l)}` : ''} ${done ? 'done' : ''} ${view.miss === side + it.id ? 'miss' : ''}"
      data-act="m" data-side="${side}" data-id="${it.id}" aria-pressed="${!!pressed}" ${done ? 'disabled' : ''} ${side === 'L' ? `lang="${l}"` : ''}>${esc(txt)}</button>`;
  };
  return `<p class="small">Tap a ${esc(data[l].name)} word, then its ${letters ? 'sound' : 'meaning'}.</p>
    <div class="match">
      <div class="col">${r.left.map(it => btn('L', it, it.text)).join('')}</div>
      <div class="col">${r.right.map(it => btn('R', it, rightText(it))).join('')}</div>
    </div>`;
}

function sayBody(les) {
  const l = lang(), item = itemFor(view.queue[view.i]), k = kindOf(item, les);
  const pct = Math.round((view.i / view.queue.length) * 100);
  return `<p class="count">${view.i + 1} / ${view.queue.length}</p>
    <div class="progress"><i data-w="${pct}"></i></div>
    <div class="card">
      <p class="script ${k} ${scriptClass(l)}" lang="${l}">${esc(item.script)}</p>
      <p class="translit">${esc(item.translit)}</p><p class="small">${esc(item.en)}</p>
      ${listenBtn(item)}
      <button class="btn mic ${view.listening ? 'on' : ''}" data-act="mic" ${view.listening ? 'disabled' : ''}>${MIC}${view.listening ? 'Listening' : 'Say it'}</button>
      <p class="verdict ${view.ok === true ? 'ok' : view.ok === false ? 'no' : ''}" role="status">${esc(view.msg)}</p>
    </div>
    ${view.ok === false && view.tries >= 2 ? '<button class="btn ghost wide" data-act="saynext">Next word</button>' : ''}`;
}

function doneCard() {
  const n = view.earned;
  const line = n === 3 ? 'Super star!' : n === 2 ? 'Great work!' : n === 1 ? 'Good try!' : 'Keep practising!';
  return `<div class="card done-card">
      <h1>${line}</h1>
      <p class="small">${view.right} of ${view.total} right</p>
      <div class="pop">${stars(n, 'stars bigstars')}</div>
    </div>
    <div class="stack">
      <button class="btn wide" data-act="mode" data-mode="${view.mode}" id="again">Play again</button>
      <button class="btn ghost wide" data-act="home">All lessons</button>
    </div>`;
}

function finish() {
  const l = lang();
  view.earned = recordLesson(state, l, view.id, view.right, view.total, today());
  save();
  view.done = true; view.focus = '#again';
  say(`${view.earned} stars`);
  render();
}

function grade(g) {
  const l = lang(), id = view.queue[view.i];
  recordReview(state, l, id, GRADES[g], today());
  view.total++; if (g !== 'again') view.right++;
  if (g === 'again' && view.queue.filter(x => x === id).length < 2) view.queue.push(id); // one more go later
  save();
  view.i++; view.flipped = false; view.fallback = null;
  if (view.i >= view.queue.length) return finish();
  view.focus = '#flip';
  render();
}

function matchTap(side, id) {
  const l = lang();
  view.miss = null;
  if (!view.pick || view.pick.side === side) { view.pick = { side, id }; return render(); }
  const leftId = side === 'L' ? id : view.pick.id;
  const rightId = side === 'R' ? id : view.pick.id;
  if (leftId === rightId) {
    view.matched.push(leftId);
    const first = !view.missed.includes(leftId);
    recordReview(state, l, leftId, first ? GRADES.good : GRADES.again, today());
    view.total++; if (first) view.right++;
    save(); say('Match!');
    view.pick = null;
    if (view.matched.length === view.round.pairs.length) return finish();
  } else {
    if (!view.missed.includes(leftId)) view.missed.push(leftId);
    view.miss = side + id; view.pick = null; say('Try again');
  }
  render();
}

async function mic() {
  const l = lang(), item = itemFor(view.queue[view.i]);
  if (!sayItAllowed(rec[l], state.settings.cloudSpeech)) return;
  view.listening = true; view.msg = ''; view.ok = null; render();
  const res = await listenOnce(window, data[l].speech_lang, { local: rec[l] === 'local' });
  view.listening = false; view.tries++;
  if (res.error && !res.heard.length) {
    view.ok = false;
    view.msg = res.error === 'not-allowed' ? 'Microphone is blocked. A grown-up can allow it in the browser.' : "I didn't hear that. Try again!";
    if (res.error === 'not-allowed') view.tries = 2;
    return render();
  }
  const j = judge(res.heard, item);
  if (j.ok) {
    recordReview(state, l, item.id, GRADES.good, today());
    view.total++; view.right++; save();
    view.ok = true; view.msg = 'Well said!'; render();
    setTimeout(sayNext, 1100);
  } else {
    view.ok = false; view.msg = view.tries >= 2 ? `Good try! It sounds like: ${item.translit}` : 'Nearly! Listen and try again.';
    if (view.tries >= 2) { recordReview(state, l, item.id, GRADES.again, today()); view.total++; save(); }
    render();
  }
}
function sayNext() {
  if (view.name !== 'lesson' || view.mode !== 'say' || view.done) return;
  view.i++; view.tries = 0; view.ok = null; view.msg = '';
  if (view.i >= view.queue.length) return finish();
  render();
}

function listen(id) {
  const l = lang(), item = itemFor(id);
  if (!speak(window, item.script, data[l].speech_lang, voice[l])) { view.fallback = id; render(); }
}

// ---------- parent gate ----------
function renderGate() {
  return `<div class="panel gate">
    <h1>Grown-ups only</h1>
    <p class="small">Answer to open progress and settings.</p>
    <p class="q" aria-label="What is ${esc(view.ch.spoken)}?">${esc(view.ch.question)} = ?</p>
    <form data-form="gate" autocomplete="off">
      <label class="sr" for="ans">Answer</label>
      <input id="ans" inputmode="numeric" pattern="[0-9]*" maxlength="4" required>
      ${view.wrong ? '<p class="warn" role="alert">Not quite. Here is a new one.</p>' : ''}
      <div class="row"><button class="btn ghost" type="button" data-act="home">Cancel</button><button class="btn" type="submit">Open</button></div>
    </form></div>`;
}

// ---------- parent ----------
function renderParent() {
  const l = view.lang || lang(), d = data[l], s = parentSummary(state, l, lessons[l], today());
  const maxDay = Math.max(1, ...s.week.map(x => x.reviews));
  const week = s.week.map(x => `<div><i data-h="${Math.round((x.reviews / maxDay) * 100)}"></i><small>${x.day.slice(8)}</small></div>`).join('');
  const rows = s.perLesson.map(p => `<tr><td>${esc(p.title)}</td><td class="n">${p.seen}/${p.size}</td><td class="n">${p.known}</td><td>${stars(p.stars)}</td></tr>`).join('');
  const tricky = s.tricky.length ? `<ul class="tricky">${s.tricky.map(t => `<li><span class="${scriptClass(l)}" lang="${l}">${esc(t.script)}</span> ${esc(t.translit)}: ${esc(t.en)} <span class="small">(missed ${t.lapses})</span></li>`).join('')}</ul>` : '<p class="small">None yet.</p>';
  return `<div class="bar"><button class="back" data-act="home" aria-label="Close grown-ups screen">&lt;</button><h1>Progress</h1></div>
  <div class="pills" role="group" aria-label="Language">${LANGS.map(x => `<button class="pill" data-act="plang" data-lang="${x}" aria-pressed="${x === l}">${esc(data[x].name)}</button>`).join('')}</div>
  <section class="panel">
    <p>${esc(summaryLine(s, d.name))}</p>
    <div class="kpis">
      <div class="kpi"><b>${s.streak}</b><span>day streak</span></div>
      <div class="kpi"><b>${s.known}</b><span>known</span></div>
      <div class="kpi"><b>${s.stars}</b><span>of ${s.maxStars} stars</span></div>
    </div>
    <h2>Last 7 days</h2>
    <div class="week" aria-label="Practice per day, last 7 days">${week}</div>
    <p class="small">${s.activeDays7} active day${s.activeDays7 === 1 ? '' : 's'}, ${s.weekReviews} answers${s.weekAccuracy === null ? '' : `, ${s.weekAccuracy}% right`}.</p>
  </section>
  <section class="panel"><h2>Words to practise together</h2>${tricky}</section>
  <section class="panel"><h2>Lessons</h2>
    <table><thead><tr><th>Lesson</th><th>Seen</th><th>Known</th><th>Stars</th></tr></thead><tbody>${rows}</tbody></table>
  </section>
  ${settingsPanel(l)}
  <section class="panel"><h2>About the words</h2>
    <p class="small">${d.native_speaker_checked ? 'Checked by a native speaker.' : 'Prototype: these words have not yet been checked by a native speaker. Tell us if you spot a mistake.'} ${esc(d.transliteration_note)}</p>
  </section>`;
}

function settingsPanel(l) {
  const name = data[l].name, mode = rec[l];
  const v = voice[l] ? `Found: ${esc(voice[l].name || voice[l].lang)}.` : ttsSupport(window) ? `No ${name} voice on this device. On Android, add it in Settings, Text-to-speech; on iPhone, Settings, Accessibility, Spoken Content, Voices.` : 'This browser cannot read aloud.';
  const sayTxt = {
    local: 'Ready, and it listens on this device only.',
    'local-download': `This browser can listen on the device after a one-time ${name} speech pack download from the browser maker.`,
    cloud: `This browser can only listen by sending the child's voice to its maker's speech service. Off unless you allow it.`,
    none: 'This browser cannot listen to speech. Cards and Match still work.',
  }[mode] || 'Checking...';
  const dl = mode === 'local-download' ? `<button class="btn ghost wide" data-act="install">Download ${esc(name)} speech pack</button>` : '';
  const cloud = mode === 'cloud' ? `<label class="switch"><input type="checkbox" data-act="cloud" ${state.settings.cloudSpeech ? 'checked' : ''}>
      <span>Allow the browser's speech service for Say it. Your child's voice goes to the browser maker (for example Google or Apple), not to Kalpa Labs.</span></label>` : '';
  return `<section class="panel stack"><h2>Sound and privacy</h2>
    <p class="small"><b>Listen:</b> ${v}</p>
    <p class="small"><b>Say it:</b> ${sayTxt}</p>${dl}${cloud}
    <p class="small"><b>Your data:</b> no accounts, no ads, no chat. Progress is kept only in this browser${store.persistent ? '' : ' (not saved: this browser blocks storage, so progress ends when the tab closes)'}. Nothing is sent to Kalpa Labs.</p>
    <div class="row"><button class="btn ghost" data-act="export">Save a copy</button><button class="btn ghost danger" data-act="reset">Reset progress</button></div>
  </section>`;
}

// ---------- events ----------
app.addEventListener('submit', e => {
  const f = e.target.closest('[data-form="gate"]');
  if (!f) return;
  e.preventDefault();
  if (checkAnswer(view.ch, f.querySelector('#ans').value)) go({ name: 'parent', lang: lang() });
  else { view.ch = makeChallenge(); view.wrong = true; view.focus = '#ans'; render(); }
});
app.addEventListener('change', e => {
  if (e.target.dataset.act === 'cloud') { state.settings.cloudSpeech = e.target.checked; save(); render(); }
});
document.addEventListener('click', async e => {
  const b = e.target.closest('[data-act]');
  if (!b || b.dataset.act === 'cloud') return;
  const a = b.dataset.act;
  if (a === 'home') return go({ name: 'home' });
  if (a === 'gate') return go({ name: 'gate', ch: makeChallenge(), wrong: false, focus: '#ans' });
  if (a === 'lang') { state.settings.lang = b.dataset.lang; save(); return render(); }
  if (a === 'plang') { view.lang = b.dataset.lang; return render(); }
  if (a === 'open') return startLesson(b.dataset.id);
  if (a === 'mode') return startLesson(view.id, b.dataset.mode);
  if (a === 'flip') { view.flipped = true; view.focus = '[data-g="good"]'; return render(); }
  if (a === 'grade') return grade(b.dataset.g);
  if (a === 'listen') return listen(b.dataset.id);
  if (a === 'm') return matchTap(b.dataset.side, b.dataset.id);
  if (a === 'mic') return mic();
  if (a === 'saynext') return sayNext();
  if (a === 'install') {
    const l = view.lang || lang(), R = recognitionCtor(window);
    try { if (R && R.install) await R.install({ langs: [data[l].speech_lang], processLocally: true }); } catch { /* user declined or offline */ }
    rec[l] = await recognitionMode(window, data[l].speech_lang);
    return render();
  }
  if (a === 'export') {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = `bhasha-kids-progress-${today()}.json`;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    return;
  }
  if (a === 'reset') {
    if (!confirm('Delete all progress on this device? This cannot be undone.')) return;
    const keepLang = state.settings.lang;
    state = newState(); state.settings.lang = keepLang; store.clear(); save();
    return render();
  }
});

boot();

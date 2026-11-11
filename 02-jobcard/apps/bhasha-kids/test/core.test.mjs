import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { review, newCard, isDue, isKnown, dueQueue, addDays, daysBetween, GRADES, MIN_EF } from '../src/srs.js';
import { newState, normalizeState, touchStreak, liveStreak, starsFor, recordReview, recordLesson, parentSummary, summaryLine, lessonStars } from '../src/progress.js';
import { lessonsFor, validateLang, matchRound, seeded, shuffle } from '../src/lessons.js';
import { makeChallenge, checkAnswer } from '../src/gate.js';
import { judge, normalize, levenshtein, similarity } from '../src/match.js';
import { makeStore } from '../src/storage.js';
import { pickVoice, recognitionMode, sayItAllowed, speak, ttsSupport } from '../src/speech.js';

const load = f => JSON.parse(readFileSync(new URL(`../data/${f}`, import.meta.url), 'utf8'));
const te = load('te.json'), hi = load('hi.json');
const T = '2026-11-07';

test('date helpers cross month and leap year', () => {
  assert.equal(addDays('2026-11-30', 1), '2026-12-01');
  assert.equal(addDays('2028-02-28', 1), '2028-02-29');
  assert.equal(daysBetween('2026-12-31', '2027-01-01'), 1);
  assert.throws(() => addDays('7/11/2026', 1));
});

test('SM-2: first good review = 1 day, second = 6, third = 6 x EF', () => {
  let c = review(newCard(), GRADES.good, T);
  assert.deepEqual([c.reps, c.interval, c.due], [1, 1, '2026-11-08']);
  c = review(c, GRADES.good, '2026-11-08');
  assert.equal(c.interval, 6);
  const ef = c.ef;
  c = review(c, GRADES.good, '2026-11-14');
  assert.equal(c.interval, Math.round(6 * ef));
  assert.equal(c.reps, 3);
});

test('SM-2: EF formula; easy raises, again lowers and floors at 1.3', () => {
  assert.equal(review(newCard(), 5, T).ef, 2.6);
  assert.equal(review(newCard(), 4, T).ef, 2.5);
  assert.equal(review(newCard(), 3, T).ef, 2.36);
  let c = newCard();
  for (let i = 0; i < 10; i++) c = review(c, GRADES.again, T);
  assert.equal(c.ef, MIN_EF);
  assert.equal(c.lapses, 10);
});

test('SM-2: a lapse resets reps and comes back today', () => {
  let c = review(review(newCard(), 4, T), 4, '2026-11-08');
  c = review(c, GRADES.again, '2026-11-14');
  assert.deepEqual([c.reps, c.interval, c.due], [0, 0, '2026-11-14']);
  assert.ok(isDue(c, '2026-11-14'));
  assert.throws(() => review(newCard(), 6, T));
  assert.throws(() => review(newCard(), 2.5, T));
});

test('review never mutates input; isKnown after two good reviews', () => {
  const c0 = newCard();
  const c1 = review(c0, 4, T);
  assert.equal(c0.reps, 0);
  assert.equal(isKnown(c1), false);
  assert.equal(isKnown(review(c1, 4, '2026-11-08')), true);
});

test('dueQueue: overdue first, then new, limited', () => {
  const cards = {
    a: { ...newCard(), due: '2026-11-05', seen: 1, ef: 2.5 },
    b: { ...newCard(), due: '2026-11-01', seen: 1, ef: 2.5 },
    c: { ...newCard(), due: '2026-11-20', seen: 1, ef: 2.5 },
  };
  assert.deepEqual(dueQueue(['a', 'b', 'c', 'd', 'e'], cards, T, 3), ['b', 'a', 'd']);
});

test('streak: same day no change, next day +1, gap resets, longest kept', () => {
  let s = { current: 0, longest: 0, last: null };
  s = touchStreak(s, '2026-11-01'); assert.equal(s.current, 1);
  s = touchStreak(s, '2026-11-01'); assert.equal(s.current, 1);
  s = touchStreak(s, '2026-11-02'); s = touchStreak(s, '2026-11-03');
  assert.deepEqual([s.current, s.longest], [3, 3]);
  s = touchStreak(s, '2026-11-06');
  assert.deepEqual([s.current, s.longest], [1, 3]);
  assert.deepEqual(touchStreak(s, '2026-11-01'), s, 'clock going back changes nothing');
  assert.equal(liveStreak(s, '2026-11-07'), 1);
  assert.equal(liveStreak(s, '2026-11-08'), 0);
});

test('stars per lesson: thresholds and best-ever kept', () => {
  assert.deepEqual([starsFor(0, 8), starsFor(1, 8), starsFor(6, 8), starsFor(8, 8), starsFor(0, 0)], [0, 1, 2, 3, 0]);
  const st = newState();
  assert.equal(recordLesson(st, 'te', 'family', 8, 8, T), 3);
  assert.equal(recordLesson(st, 'te', 'family', 2, 8, T), 1);
  assert.equal(lessonStars(st, 'te', 'family'), 3);
  assert.equal(st.langs.te.lessons.family.plays, 2);
});

test('parent summary counts seen, known, due, tricky and week', () => {
  const st = newState();
  const lessons = lessonsFor(te);
  const fam = lessons.find(l => l.id === 'family').items;
  recordReview(st, 'te', fam[0].id, 4, '2026-11-05');
  recordReview(st, 'te', fam[0].id, 4, '2026-11-06');
  recordReview(st, 'te', fam[1].id, 1, '2026-11-06');
  recordReview(st, 'te', fam[1].id, 1, T);
  recordLesson(st, 'te', 'family', 6, 8, T);
  const s = parentSummary(st, 'te', lessons, T);
  assert.equal(s.seen, 2);
  assert.equal(s.known, 1);
  assert.equal(s.due, 1);
  assert.equal(s.stars, 2);
  assert.equal(s.streak, 3);
  assert.equal(s.tricky[0].id, fam[1].id);
  assert.equal(s.week.length, 7);
  assert.equal(s.weekReviews, 4);
  assert.equal(s.weekAccuracy, 50);
  assert.equal(s.activeDays7, 3);
  assert.match(summaryLine(s, 'Telugu'), /1 of \d+ Telugu items known/);
  assert.match(summaryLine(parentSummary(newState(), 'hi', lessonsFor(hi), T), 'Hindi'), /No Hindi practice yet/);
});

test('same-day right answer on a not-due card does not advance the schedule', () => {
  const st = newState();
  recordReview(st, 'te', 'te-family-amma', 4, T);
  const before = { ...st.langs.te.cards['te-family-amma'] };
  recordReview(st, 'te', 'te-family-amma', 5, T);
  const after = st.langs.te.cards['te-family-amma'];
  assert.deepEqual([after.reps, after.interval, after.due, after.ef], [before.reps, before.interval, before.due, before.ef]);
  assert.equal(after.seen, 2);
  assert.equal(st.days[T].reviews, 2);
  recordReview(st, 'te', 'te-family-amma', 1, T);
  assert.equal(st.langs.te.cards['te-family-amma'].reps, 0, 'a miss still counts');
});

test('normalizeState survives junk and keeps cloudSpeech off unless true', () => {
  assert.deepEqual(normalizeState(null), newState());
  assert.deepEqual(normalizeState('x'), newState());
  assert.deepEqual(normalizeState({ version: 99 }), newState());
  const s = normalizeState({ version: 1, settings: { lang: 'hi', cloudSpeech: 'yes' }, streak: { current: 'a' } });
  assert.equal(s.settings.lang, 'hi');
  assert.equal(s.settings.cloudSpeech, false);
  assert.equal(s.streak.current, 0);
});

test('lesson data: valid, flagged unchecked, required sizes', () => {
  for (const d of [te, hi]) {
    assert.deepEqual(validateLang(d), [], d.lang);
    assert.equal(d.native_speaker_checked, false, `${d.lang} must stay unchecked until a native speaker signs off`);
  }
  assert.equal(te.themes.length, 10);
  for (const t of te.themes) assert.ok(t.words.length >= 8, t.id);
  assert.equal(te.themes.find(t => t.id === 'numbers').words.length, 10);
  assert.equal(te.phrases.length, 20);
  assert.ok(te.letters.vowels.length >= 13 && te.letters.consonants.length >= 20);
  assert.ok(hi.themes.length >= 5);
  assert.equal(hi.phrases.length, 20);
  const themes = te.themes.map(t => t.id).sort();
  assert.deepEqual(themes, ['actions', 'animals', 'body', 'colours', 'family', 'festivals', 'food', 'greetings', 'home', 'numbers']);
  assert.equal(lessonsFor(te).length, 13);
});

test('validateLang catches bad items', () => {
  const bad = structuredClone(te);
  bad.themes[0].words[0].script = 'amma';
  bad.themes[0].words[1].id = bad.themes[0].words[2].id;
  bad.phrases[0].translit = 'నా';
  delete bad.native_speaker_checked;
  const errs = validateLang(bad).join('\n');
  assert.match(errs, /not te script/);
  assert.match(errs, /duplicate id/);
  assert.match(errs, /plain ASCII/);
  assert.match(errs, /native_speaker_checked/);
});

test('match round: n pairs, same ids both sides, deterministic with a seed', () => {
  const items = te.themes[0].words;
  const r = matchRound(items, 4, seeded(7));
  assert.equal(r.pairs.length, 4);
  assert.deepEqual(r.left.map(x => x.id).sort(), r.pairs.slice().sort());
  assert.deepEqual(r.right.map(x => x.id).sort(), r.pairs.slice().sort());
  assert.deepEqual(matchRound(items, 4, seeded(7)), r);
  assert.equal(shuffle([1, 2, 3], seeded(1)).length, 3);
});

test('parent gate: answer checks, rejects junk', () => {
  const ch = makeChallenge(seeded(3));
  assert.ok(ch.answer >= 36 && ch.answer <= 261);
  assert.equal(checkAnswer(ch, String(ch.answer)), true);
  assert.equal(checkAnswer(ch, ` ${ch.answer} `), true);
  assert.equal(checkAnswer(ch, String(ch.answer + 1)), false);
  assert.equal(checkAnswer(ch, `${ch.answer}e0`), false);
  assert.equal(checkAnswer(ch, ''), false);
});

test('say-it judge: script, transliteration, near miss, wrong word', () => {
  const amma = te.themes[0].words[0];
  assert.equal(judge(['అమ్మ'], amma).ok, true);
  assert.equal(judge(['Amma'], amma).ok, true);
  assert.equal(judge(['మా అమ్మ'], amma).ok, true);
  assert.equal(judge(['నాన్న'], amma).ok, false);
  assert.equal(judge([], amma).ok, false);
  assert.equal(levenshtein('kitten', 'sitting'), 3);
  assert.equal(normalize('  నా పేరు ___. '), 'నా పేరు');
  assert.ok(similarity('नमस्ते', 'नमस्ते') === 1);
  assert.equal(judge(['नमस्ते!'], hi.themes.find(t => t.id === 'greetings').words[0]).ok, true);
});

test('storage: survives throwing localStorage and bad JSON', () => {
  const throwing = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('quota'); }, removeItem() { throw new Error('x'); } };
  const s = makeStore(throwing);
  assert.equal(s.load(), null);
  assert.equal(s.save({ a: 1 }), false);
  assert.deepEqual(s.load(), { a: 1 }, 'falls back to memory');
  assert.equal(s.persistent, false);
  s.clear();
  const m = new Map();
  const good = makeStore({ getItem: k => m.get(k) ?? null, setItem: (k, v) => m.set(k, v), removeItem: k => m.delete(k) });
  assert.equal(good.save({ b: 2 }), true);
  assert.deepEqual(makeStore({ getItem: k => m.get(k) ?? null }).load(), { b: 2 });
  m.set('kalpa-bhasha-kids-v1', '{not json');
  assert.equal(makeStore({ getItem: k => m.get(k) }).load(), null);
  assert.equal(makeStore(null).save({}), true);
});

test('voice picking prefers exact lang, then base lang, else null', () => {
  const v = [{ lang: 'en-US' }, { lang: 'hi_IN', name: 'x' }, { lang: 'te-IN', name: 'te' }];
  assert.equal(pickVoice(v, 'te-IN').name, 'te');
  assert.equal(pickVoice(v, 'hi-IN').name, 'x');
  assert.equal(pickVoice([{ lang: 'en-GB' }], 'te-IN'), null);
  assert.equal(ttsSupport({}), false);
  assert.equal(speak({}, 'x', 'te-IN', null), false);
});

test('recognition mode: local only when on-device; cloud needs parent opt-in', async () => {
  assert.equal(await recognitionMode({}, 'te-IN'), 'none');
  const mk = (local, any) => { const R = function () {}; R.available = async o => (o.processLocally ? local : any); return { SpeechRecognition: R }; };
  assert.equal(await recognitionMode(mk('available', 'available'), 'te-IN'), 'local');
  assert.equal(await recognitionMode(mk('downloadable', 'available'), 'te-IN'), 'local-download');
  assert.equal(await recognitionMode(mk('unavailable', 'available'), 'te-IN'), 'cloud');
  assert.equal(await recognitionMode(mk('unavailable', 'unavailable'), 'te-IN'), 'none');
  assert.equal(await recognitionMode({ webkitSpeechRecognition: function () {} }, 'hi-IN'), 'cloud');
  assert.equal(sayItAllowed('local', false), true);
  assert.equal(sayItAllowed('cloud', false), false);
  assert.equal(sayItAllowed('cloud', true), true);
  assert.equal(sayItAllowed('none', true), false);
});

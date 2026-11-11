// Progress: streaks, stars per lesson, and the parent summary. Pure functions on
// a plain state object so the same code runs in the browser and in node --test.
import { review, isKnown, isDue, daysBetween, addDays } from './srs.js';

export const STATE_VERSION = 1;

export function newState() {
  return {
    version: STATE_VERSION,
    settings: { lang: 'te', cloudSpeech: false },
    streak: { current: 0, longest: 0, last: null },
    days: {},   // "YYYY-MM-DD" -> { reviews, correct }
    langs: {},  // lang -> { cards: {id: card}, lessons: {lessonId: {stars, plays, last}} }
  };
}

// Accepts anything (corrupt storage, older versions) and returns a valid state.
export function normalizeState(raw) {
  const s = newState();
  if (!raw || typeof raw !== 'object' || raw.version !== STATE_VERSION) return s;
  if (raw.settings && typeof raw.settings === 'object') {
    if (typeof raw.settings.lang === 'string') s.settings.lang = raw.settings.lang;
    s.settings.cloudSpeech = raw.settings.cloudSpeech === true;
  }
  if (raw.streak && typeof raw.streak === 'object') {
    s.streak.current = Number.isInteger(raw.streak.current) ? raw.streak.current : 0;
    s.streak.longest = Number.isInteger(raw.streak.longest) ? raw.streak.longest : 0;
    s.streak.last = typeof raw.streak.last === 'string' ? raw.streak.last : null;
  }
  if (raw.days && typeof raw.days === 'object') s.days = raw.days;
  if (raw.langs && typeof raw.langs === 'object') s.langs = raw.langs;
  return s;
}

function langState(state, lang) {
  if (!state.langs[lang]) state.langs[lang] = { cards: {}, lessons: {} };
  return state.langs[lang];
}

// Streak rule: practice on consecutive calendar days. Same day: no change.
// Yesterday: +1. Any gap: back to 1. A clock that went backwards changes nothing.
export function touchStreak(streak, today) {
  const s = { ...streak };
  if (!s.last) s.current = 1;
  else {
    const gap = daysBetween(s.last, today);
    if (gap < 0) return s;
    if (gap === 0) return s;
    s.current = gap === 1 ? s.current + 1 : 1;
  }
  s.last = today;
  if (s.current > s.longest) s.longest = s.current;
  return s;
}

// The streak shown on the home screen: 0 if the child missed yesterday and today.
export function liveStreak(streak, today) {
  if (!streak.last) return 0;
  const gap = daysBetween(streak.last, today);
  return gap <= 1 && gap >= 0 ? streak.current : 0;
}

// Stars for one lesson play: 3 = 90%+, 2 = 70%+, 1 = finished at all with 1+ right.
export function starsFor(correct, total) {
  if (!total || correct <= 0) return 0;
  const p = correct / total;
  if (p >= 0.9) return 3;
  if (p >= 0.7) return 2;
  return 1;
}

// Grade one card (flashcard, match or say-it) and log the day's practice.
export function recordReview(state, lang, cardId, grade, today) {
  const L = langState(state, lang);
  const prev = L.cards[cardId];
  // A right answer on a card that is not due yet (e.g. Match right after Cards)
  // counts as practice but must not push the schedule forward again today.
  if (prev && prev.due && !isDue(prev, today) && grade >= 3) L.cards[cardId] = { ...prev, seen: prev.seen + 1 };
  else L.cards[cardId] = review(prev, grade, today);
  const d = state.days[today] || (state.days[today] = { reviews: 0, correct: 0 });
  d.reviews += 1;
  if (grade >= 3) d.correct += 1;
  state.streak = touchStreak(state.streak, today);
  return L.cards[cardId];
}

// Keeps the best stars ever earned for the lesson; returns this play's stars.
export function recordLesson(state, lang, lessonId, correct, total, today) {
  const L = langState(state, lang);
  const stars = starsFor(correct, total);
  const prev = L.lessons[lessonId] || { stars: 0, plays: 0, last: null };
  L.lessons[lessonId] = { stars: Math.max(prev.stars, stars), plays: prev.plays + 1, last: today };
  state.streak = touchStreak(state.streak, today);
  return stars;
}

export function lessonStars(state, lang, lessonId) {
  return state.langs[lang]?.lessons?.[lessonId]?.stars || 0;
}

// lessons: [{id, title, items:[{id, script, translit, en}]}] from lessons.js
export function parentSummary(state, lang, lessons, today) {
  const L = state.langs[lang] || { cards: {}, lessons: {} };
  let total = 0, seen = 0, known = 0, due = 0, stars = 0;
  const perLesson = [], tricky = [];
  for (const les of lessons) {
    let lSeen = 0, lKnown = 0;
    for (const it of les.items) {
      total++;
      const c = L.cards[it.id];
      if (c && c.seen) {
        seen++; lSeen++;
        if (isKnown(c)) { known++; lKnown++; }
        if (isDue(c, today)) due++;
        if (c.lapses > 0) tricky.push({ ...it, lapses: c.lapses, ef: c.ef });
      }
    }
    const st = L.lessons[les.id]?.stars || 0;
    stars += st;
    perLesson.push({ id: les.id, title: les.title, size: les.items.length, seen: lSeen, known: lKnown, stars: st, plays: L.lessons[les.id]?.plays || 0 });
  }
  tricky.sort((a, b) => b.lapses - a.lapses || a.ef - b.ef);
  const week = [];
  for (let i = 6; i >= 0; i--) {
    const k = addDays(today, -i);
    week.push({ day: k, reviews: state.days[k]?.reviews || 0, correct: state.days[k]?.correct || 0 });
  }
  const weekReviews = week.reduce((n, d) => n + d.reviews, 0);
  const weekCorrect = week.reduce((n, d) => n + d.correct, 0);
  return {
    lang, total, seen, known, due, stars, maxStars: lessons.length * 3,
    streak: liveStreak(state.streak, today), longest: state.streak.longest,
    lastPractice: state.streak.last,
    activeDays7: week.filter(d => d.reviews > 0).length,
    weekReviews, weekAccuracy: weekReviews ? Math.round((weekCorrect / weekReviews) * 100) : null,
    week, perLesson, tricky: tricky.slice(0, 5),
  };
}

// One plain-English line a parent can read at a glance.
export function summaryLine(s, langName) {
  if (!s.seen) return `No ${langName} practice yet. Start with Family or Greetings together.`;
  const acc = s.weekAccuracy === null ? '' : `, ${s.weekAccuracy}% right this week`;
  return `${s.known} of ${s.total} ${langName} items known, ${s.seen} seen. ` +
    `Streak ${s.streak} day${s.streak === 1 ? '' : 's'} (best ${s.longest})${acc}. ${s.due} to review today.`;
}

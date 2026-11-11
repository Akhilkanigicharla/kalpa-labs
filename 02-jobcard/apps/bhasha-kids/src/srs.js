// Spaced repetition: SM-2, the SuperMemo-2 algorithm (P. A. Wozniak, 1990,
// "Optimization of learning", described at super-memory.com/english/ol/sm2.htm).
// Written from the published description; no code copied.
// Kid tweak: three buttons map to SM-2 grades (again=1, good=4, easy=5) and a
// lapse comes back the same day (interval 0) so the child sees it again soon.

export const GRADES = Object.freeze({ again: 1, good: 4, easy: 5 });
export const MIN_EF = 1.3;

// Day keys are local calendar dates "YYYY-MM-DD"; maths runs in UTC to avoid DST drift.
export function dayKey(date = new Date()) {
  const y = date.getFullYear(), m = date.getMonth() + 1, d = date.getDate();
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
}
function toUTC(key) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(key)) throw new Error(`bad day key: ${key}`);
  const [y, m, d] = key.split('-').map(Number);
  return Date.UTC(y, m - 1, d);
}
export function addDays(key, n) {
  const t = new Date(toUTC(key) + n * 86400000);
  return `${t.getUTCFullYear()}-${String(t.getUTCMonth() + 1).padStart(2, '0')}-${String(t.getUTCDate()).padStart(2, '0')}`;
}
export function daysBetween(a, b) { return Math.round((toUTC(b) - toUTC(a)) / 86400000); }

export function newCard() {
  return { reps: 0, interval: 0, ef: 2.5, due: null, lapses: 0, seen: 0, last: null };
}

// q is the SM-2 quality 0..5. Returns a new card object; never mutates the input.
export function review(card, q, today) {
  if (!Number.isInteger(q) || q < 0 || q > 5) throw new Error(`grade must be 0..5, got ${q}`);
  const c = { ...newCard(), ...card };
  let { reps, interval, ef, lapses } = c;
  if (q < 3) {
    reps = 0;
    interval = 0; // kid tweak: see it again today (SM-2 proper uses 1 day)
    lapses += 1;
  } else {
    if (reps === 0) interval = 1;
    else if (reps === 1) interval = 6;
    else interval = Math.round(interval * ef);
    reps += 1;
  }
  ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02));
  if (ef < MIN_EF) ef = MIN_EF;
  ef = Math.round(ef * 100) / 100;
  return { reps, interval, ef, lapses, seen: c.seen + 1, last: today, due: addDays(today, interval) };
}

export function isDue(card, today) {
  return !card || !card.due || daysBetween(card.due, today) >= 0;
}

// A word is "known" once it has survived two good reviews in a row (interval >= 6 days).
export function isKnown(card) { return !!card && card.reps >= 2 && card.interval >= 6; }

// Order for a session: due-and-seen first (most overdue first), then new ones.
export function dueQueue(ids, cards, today, limit = 10) {
  const seen = [], fresh = [];
  for (const id of ids) {
    const c = cards[id];
    if (!c || !c.due) fresh.push(id);
    else if (isDue(c, today)) seen.push(id);
  }
  seen.sort((a, b) => daysBetween(cards[b].due, cards[a].due) || (cards[a].ef - cards[b].ef));
  return seen.concat(fresh).slice(0, limit);
}

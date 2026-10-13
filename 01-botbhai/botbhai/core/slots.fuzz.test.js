// Run: node core/slots.fuzz.test.js
// Property test: the slot engine must agree with a dumb minute-by-minute reference on
// thousands of random salon days (hours, breaks, closing early, durations, capacity, bookings).
const assert = require("assert");
const S = require("./slots.js");

let seed = 20261013;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const pick = (a) => a[Math.floor(rnd() * a.length)];
const hhmm = (m) => `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;

function reference(day, cfg, busy, dur, interval, capacity, earliest) {
  // open[m] = business open at minute m
  const open = new Array(24 * 60).fill(false);
  for (const [a, b] of day.hours) for (let m = a; m < b; m++) open[m] = true;
  for (const [a, b] of day.breaks) for (let m = a; m < b; m++) open[m] = false;
  if (day.closeAt !== null) for (let m = day.closeAt; m < 24 * 60; m++) open[m] = false;
  const load = new Array(24 * 60).fill(0);
  for (const b of busy) for (let m = b.start; m < b.start + b.minutes && m < 24 * 60; m++) load[m]++;
  const out = [];
  for (let s = 0; s + dur <= 24 * 60; s += interval) {
    if (s < earliest) continue;
    let fine = true;
    for (let m = s; m < s + dur; m++) if (!open[m] || load[m] >= capacity) { fine = false; break; }
    if (fine) out.push(S.label(s));
  }
  return out;
}

let cases = 0, nonEmpty = 0;
for (let i = 0; i < 3000; i++) {
  const interval = pick([15, 30, 60]);
  const openAt = pick([540, 600, 630, 660]), closeAt = pick([1080, 1140, 1200, 1260]);
  const hours = rnd() < 0.3 ? [[openAt, 780], [840, closeAt]] : [[openAt, closeAt]];
  const breaks = rnd() < 0.5 ? [[pick([780, 810, 840]), pick([870, 900])]] : [];
  const early = rnd() < 0.2 ? pick([900, 960, 1020]) : null;
  const dur = pick([15, 30, 45, 60, 90, 120]);
  const capacity = pick([1, 2, 3]);
  const busy = [];
  for (let k = Math.floor(rnd() * 8); k > 0; k--) {
    const st = openAt + interval * Math.floor(rnd() * ((closeAt - openAt) / interval));
    busy.push({ date_iso: "2026-10-14", slot: S.label(st), minutes: pick([30, 60, 90]), start: st });
  }
  const cfg = {
    capacity, lead_minutes: 30,
    schedule: { hours: { default: hours.map(([a, b]) => [hhmm(a), hhmm(b)]) }, breaks: breaks.map(([a, b]) => [hhmm(a), hhmm(b)]), interval },
  };
  if (early !== null) cfg.schedule.closing_today = { date: "2026-10-14", at: hhmm(early) };
  const nowMin = rnd() < 0.5 ? openAt + Math.floor(rnd() * 400) : null;
  const now = nowMin === null ? null : new Date(`2026-10-14T${hhmm(nowMin)}:00+05:30`).getTime();
  const got = S.free({ cfg, date_iso: "2026-10-14", now, minutes: dur,
                       busy: busy.map(({ date_iso, slot, minutes }) => ({ date_iso, slot, minutes })) }).map((x) => x.label);
  const want = reference({ hours, breaks, closeAt: early }, cfg, busy, dur, interval, capacity,
                         nowMin === null ? -Infinity : nowMin + 30);
  assert.deepStrictEqual(got, want, `case ${i}: ${JSON.stringify({ cfg, dur, nowMin, busy })}`);
  cases++; if (got.length) nonEmpty++;
}
console.log(`  ✓ slot engine == minute-by-minute reference on ${cases} random days (${nonEmpty} with free slots)`);

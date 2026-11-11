// node --test: core calculations. Reference values marked (drik) were read from drikpanchang.com
// on 7 Nov 2026; the rest are checked by reasoning (definitions, symmetry, known weekdays).
const test = require('node:test');
const assert = require('node:assert/strict');
const A = require('astronomy-engine');
const J = require('../src/core.js');
const D = require('../src/data.js');

const HYD = [17.385, 78.4867, 'Asia/Kolkata'];
const IST = (iso) => new Date(iso + '+05:30');
const minutesApart = (a, b) => Math.abs(a.getTime() - b.getTime()) / 60000;

test('Lahiri ayanamsa: 23.857 deg at J2000 and about 50.3"/year drift', () => {
  const j2000 = new Date(Date.UTC(2000, 0, 1, 12));
  assert.ok(Math.abs(J.ayanamsaMean(j2000) - 23.857) < 0.001);
  // 1956-03-21 anchor reproduces itself.
  assert.ok(Math.abs(J.ayanamsaMean(new Date(Date.UTC(1956, 2, 21))) - 23.245525) < 1e-6);
  const perYear = (J.ayanamsaMean(new Date(Date.UTC(2050, 0, 1, 12))) - J.ayanamsaMean(j2000)) * 3600 / 50;
  assert.ok(perYear > 50.2 && perYear < 50.4, `drift ${perYear}`);
  // Nutation stays within its known swing (17.2" main term plus about 1.8" of smaller terms).
  for (let y = 1950; y < 2050; y += 3) assert.ok(Math.abs(J.nutationLon(new Date(Date.UTC(y, 5, 1)))) < 19.5 / 3600);
});

test('sidereal = tropical - ayanamsa, always 0..360', () => {
  const t = new Date('2024-01-01T00:00Z');
  const diff = ((J.moonTropical(t) - J.moonSidereal(t)) % 360 + 360) % 360;
  assert.ok(Math.abs(diff - J.ayanamsa(t)) < 1e-9);
  for (let i = 0; i < 50; i++) {
    const v = J.moonSidereal(new Date(Date.UTC(2024, 0, 1 + i * 7)));
    assert.ok(v >= 0 && v < 360);
  }
});

test('tithi just before a full moon is Purnima, just before a new moon is Amavasya', () => {
  let t = new Date('2024-01-01T00:00Z');
  for (let i = 0; i < 12; i++) {
    const full = A.SearchMoonPhase(180, t, 40).date;
    const neu = A.SearchMoonPhase(0, t, 40).date;
    const before = (d) => new Date(d.getTime() - 3600000);
    const after = (d) => new Date(d.getTime() + 3600000);
    assert.equal(J.tithiAt(before(full)).name.en, 'Purnima');
    assert.equal(J.tithiAt(after(full)).name.en, 'Pratipada');
    assert.equal(J.tithiAt(after(full)).paksha, 1);
    assert.equal(J.tithiAt(before(neu)).name.en, 'Amavasya');
    assert.equal(J.tithiAt(after(neu)).paksha, 0);
    // End time of Purnima is the full moon instant itself.
    assert.ok(minutesApart(J.tithiAt(before(full)).endsAt, full) < 1);
    t = after(full.getTime() > neu.getTime() ? full : neu);
  }
});

test('Diwali 2024, Hyderabad: Amavasya at sunrise on 1 Nov, ends near 18:16 IST (drik)', () => {
  const p = J.dayPanchang('2024-11-01', ...HYD);
  assert.equal(p.tithi.name.en, 'Amavasya');
  assert.deepEqual(p.flags, ['amavasya']);
  assert.equal(p.vara.name.en.split(' ')[0], 'Friday');
  assert.ok(minutesApart(p.tithi.endsAt, IST('2024-11-01T18:16:00')) < 4);
});

test('Onam 2024, Kochi: Shravana (Thiruvonam) at sunrise on 15 Sep, ends near 18:49 IST (drik)', () => {
  const p = J.dayPanchang('2024-09-15', 9.9312, 76.2673, 'Asia/Kolkata');
  assert.equal(p.nakshatra.name.en, 'Shravana');
  assert.ok(minutesApart(p.nakshatra.endsAt, IST('2024-09-15T18:49:00')) < 4);
});

test('Guru Purnima 21 Jul 2024 and Sri Rama Navami 17 Apr 2024 at Hyderabad sunrise', () => {
  assert.equal(J.dayPanchang('2024-07-21', ...HYD).tithi.name.en, 'Purnima');
  const rn = J.dayPanchang('2024-04-17', ...HYD);
  assert.equal(rn.tithi.name.en, 'Navami');
  assert.equal(rn.tithi.paksha, 0);
  assert.deepEqual(rn.flags, ['rikta']);
});

test('weekday: known dates', () => {
  assert.equal(J.weekday('1947-08-15').index, 5); // Friday
  assert.equal(J.weekday('2000-01-01').index, 6); // Saturday
  assert.equal(J.weekday('2026-11-07').index, 6); // Saturday
});

test('nakshatra, pada and rasi stay consistent with the Moon longitude', () => {
  for (let i = 0; i < 200; i++) {
    const t = new Date(Date.UTC(2020, 0, 1) + i * 37 * 3600000);
    const lon = J.moonSidereal(t);
    const n = J.nakshatraAt(t);
    const r = J.rasiAt(t);
    assert.equal(n.index, Math.floor(lon / (360 / 27)));
    assert.equal(r.index, Math.floor(lon / 30));
    // 9 padas per rasi: the pada counted from Ashwini fixes the rasi.
    assert.equal(Math.floor((n.index * 4 + n.pada - 1) / 9), r.index);
    assert.ok(n.endsAt > t && n.endsAt - t < 30 * 3600000);
    assert.equal(J.nakshatraAt(new Date(n.endsAt.getTime() + 120000)).index, (n.index + 1) % 27);
  }
});

test('time zones: IST, DST in New York, fixed offsets, bad input', () => {
  assert.equal(J.localToUtc(2024, 11, 1, 5, 30, 'Asia/Kolkata').toISOString(), '2024-11-01T00:00:00.000Z');
  assert.equal(J.localToUtc(2024, 7, 1, 8, 0, 'America/New_York').toISOString(), '2024-07-01T12:00:00.000Z');
  assert.equal(J.localToUtc(2024, 1, 1, 8, 0, 'America/New_York').toISOString(), '2024-01-01T13:00:00.000Z');
  assert.equal(J.localToUtc(2024, 1, 1, 5, 30, '+05:30').toISOString(), '2024-01-01T00:00:00.000Z');
  assert.throws(() => J.birthChart({ date: '2024-02-30', time: '10:00', lat: 17, lon: 78, tz: 'Asia/Kolkata' }));
  assert.throws(() => J.birthChart({ date: '2024-02-10', time: '25:00', lat: 17, lon: 78, tz: 'Asia/Kolkata' }));
  assert.throws(() => J.birthChart({ date: '2024-02-10', time: '10:00', lat: 95, lon: 78, tz: 'Asia/Kolkata' }));
  assert.throws(() => J.birthChart({ date: '2024-02-10', time: '10:00', lat: 17, lon: 78, tz: 'Mars/Olympus' }));
});

test('birth chart: shape, sunrise rule for vara, and the naming syllable', () => {
  const c = J.birthChart({ date: '2024-11-01', time: '04:00', lat: HYD[0], lon: HYD[1], tz: HYD[2] });
  assert.equal(c.vara.index, 4); // before sunrise on a Friday = still Thursday (Guruvara)
  assert.equal(c.vara.beforeSunrise, true);
  const n = c.nakshatra;
  assert.equal(n.akshara.dev, D.NAKSHATRAS[n.index].ak[n.pada - 1]);
  assert.ok(/^[ఀ-౿]+$/.test(n.akshara.te));
  assert.ok(c.minutesFromPadaEdge >= 0 && c.minutesFromPadaEdge < 200);
});

test('muhurat list: length cap, consecutive dates, flags only for Amavasya and Rikta tithis', () => {
  const days = J.muhuratDays('2024-10-25', 20, ...HYD);
  assert.equal(days.length, 20);
  assert.equal(days[19].date, '2024-11-13');
  for (const d of days) {
    const rikta = [4, 9, 14].includes(d.tithi.number);
    assert.equal(d.flags.includes('rikta'), rikta);
    assert.equal(d.flags.includes('amavasya'), d.tithi.nameIndex === 15);
  }
  assert.ok(days.some((d) => d.flags.includes('amavasya')));
  assert.equal(J.muhuratDays('2024-01-01', 500, ...HYD).length, 92);
});

test('polar night falls back to an estimated 06:00 sunrise', () => {
  const s = J.sunrise('2024-12-21', 78.22, 15.65, 'Europe/Oslo'); // Svalbard
  assert.equal(s.estimated, true);
});

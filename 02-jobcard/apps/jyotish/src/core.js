/* Kalpa Jyotish core: AI-free Vedic calculations on top of astronomy-engine (MIT, Don Cross).
   Classic script (UMD). Browser: load vendor/astronomy.browser.min.js and src/data.js first.
   Node: require('./core.js'). Nothing here touches the network or storage. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('astronomy-engine'), require('./data.js'));
  else root.Jyotish = factory(root.Astronomy, root.JyotishData);
})(typeof self !== 'undefined' ? self : this, function (A, D) {
  'use strict';

  const DEG = Math.PI / 180;
  const NAK = 360 / 27; // 13 deg 20 min
  const PADA = NAK / 4; // 3 deg 20 min
  const norm360 = (x) => ((x % 360) + 360) % 360;
  const centuries = (date) => (date.getTime() / 86400000 + 2440587.5 - 2451545.0) / 36525;

  /* ---------- Lahiri ayanamsa ----------
     Anchor: Lahiri (Indian Calendar Reform Committee) value at JD 2435553.5 (21 Mar 1956 0h),
     23.245524743 deg as a mean value (the constant Swiss Ephemeris uses for SE_SIDM_LAHIRI),
     carried to any date with the IAU 2006 general precession in longitude
     p = 5028.796195" T + 1.1054348" T^2 (T = Julian centuries from J2000).
     Gives 23.8571 deg at J2000 (published Lahiri J2000 value: 23.857 deg). */
  const T0 = (2435553.5 - 2451545.0) / 36525;
  const precArcsec = (T) => 5028.796195 * T + 1.1054348 * T * T;
  function ayanamsaMean(date) {
    return 23.245524743 + (precArcsec(centuries(date)) - precArcsec(T0)) / 3600;
  }
  /* Nutation in longitude, Meeus "Astronomical Algorithms" ch. 22 short series (about 0.5"). */
  function nutationLon(date) {
    const T = centuries(date);
    const om = (125.04452 - 1934.136261 * T) * DEG;
    const L = (280.4665 + 36000.7698 * T) * DEG;
    const Lm = (218.3165 + 481267.8813 * T) * DEG;
    return (-17.2 * Math.sin(om) - 1.32 * Math.sin(2 * L) - 0.23 * Math.sin(2 * Lm) + 0.21 * Math.sin(2 * om)) / 3600;
  }
  /* "True" ayanamsa (mean + nutation), to subtract from true-of-date longitudes. */
  function ayanamsa(date) { return ayanamsaMean(date) + nutationLon(date); }

  /* Tropical Moon longitude, true ecliptic and equinox of date (astronomy-engine, about 1'). */
  function moonTropical(date) { return norm360(A.EclipticGeoMoon(date).lon); }
  function moonSidereal(date) { return norm360(moonTropical(date) - ayanamsa(date)); }
  function sunSidereal(date) { return norm360(A.SunPosition(date).elon - ayanamsa(date)); }

  /* ---------- time zones ---------- */
  const OFFSET_RE = /^(?:UTC|GMT)?\s*([+-])(\d{1,2})(?::?(\d{2}))?$/i;
  /* Minutes east of UTC for an IANA zone or "+05:30" at a UTC instant. */
  function zoneOffsetMinutes(tz, utcDate) {
    const m = OFFSET_RE.exec(String(tz).trim());
    if (m) return (m[1] === '-' ? -1 : 1) * (Number(m[2]) * 60 + Number(m[3] || 0));
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
    }).formatToParts(utcDate);
    const g = (t) => Number(parts.find((p) => p.type === t).value);
    const asUtc = Date.UTC(g('year'), g('month') - 1, g('day'), g('hour'), g('minute'), g('second'));
    return Math.round((asUtc - Math.floor(utcDate.getTime() / 1000) * 1000) / 60000);
  }
  function validTimeZone(tz) {
    if (OFFSET_RE.test(String(tz).trim())) return true;
    try { new Intl.DateTimeFormat('en-US', { timeZone: tz }); return true; } catch { return false; }
  }
  /* Local wall-clock time in a zone -> UTC Date. Two passes handle DST edges. */
  function localToUtc(y, mo, d, h, mi, tz) {
    const guess = Date.UTC(y, mo - 1, d, h, mi);
    let off = zoneOffsetMinutes(tz, new Date(guess));
    let utc = guess - off * 60000;
    const off2 = zoneOffsetMinutes(tz, new Date(utc));
    if (off2 !== off) utc = guess - off2 * 60000;
    return new Date(utc);
  }
  function parseDate(s) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s));
    if (!m) throw new Error('Date must be YYYY-MM-DD');
    const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
    const t = new Date(Date.UTC(y, mo - 1, d));
    if (t.getUTCMonth() !== mo - 1 || t.getUTCDate() !== d) throw new Error('No such date');
    if (y < 1700 || y > 2200) throw new Error('Year must be between 1700 and 2200');
    return { y, mo, d };
  }
  function parseTime(s) {
    const m = /^(\d{1,2}):(\d{2})$/.exec(String(s));
    if (!m || Number(m[1]) > 23 || Number(m[2]) > 59) throw new Error('Time must be HH:MM (24 hour)');
    return { h: Number(m[1]), mi: Number(m[2]) };
  }
  function checkPlace(lat, lon, tz) {
    if (!Number.isFinite(lat) || lat < -90 || lat > 90) throw new Error('Latitude must be -90 to 90');
    if (!Number.isFinite(lon) || lon < -180 || lon > 180) throw new Error('Longitude must be -180 to 180');
    if (!validTimeZone(tz)) throw new Error('Unknown time zone');
  }

  /* ---------- searches ---------- */
  /* First time after `start` when f(t) (an angle that only increases, mod 360) reaches `target`.
     Steps forward then bisects to `tolMin` minutes. Returns null if not found within maxHours. */
  function searchAngle(f, target, start, maxHours, stepHours, tolMin) {
    const ahead = (t) => norm360(target - f(t));
    let a = start.getTime();
    let prev = ahead(start);
    for (let h = stepHours; h <= maxHours + 1e-9; h += stepHours) {
      const b = start.getTime() + h * 3600000;
      const cur = ahead(new Date(b));
      if (cur > prev + 180) { // wrapped past the target
        let lo = a, hi = b;
        while (hi - lo > tolMin * 60000) {
          const mid = (lo + hi) / 2;
          if (ahead(new Date(mid)) > 180) hi = mid; else lo = mid;
        }
        return new Date(Math.round((lo + hi) / 2));
      }
      a = b; prev = cur;
    }
    return null;
  }

  /* ---------- panchang pieces ---------- */
  function tithiAt(date) {
    const elong = norm360(A.MoonPhase(date)); // Moon minus Sun ecliptic longitude
    const index = Math.floor(elong / 12); // 0..29
    const paksha = index < 15 ? 0 : 1;
    const nameIndex = index === 14 ? 14 : index === 29 ? 15 : index % 15;
    const endT = A.SearchMoonPhase(((index + 1) * 12) % 360, date, 3);
    return { index, number: (index % 15) + 1, paksha, nameIndex, name: D.TITHIS[nameIndex], pakshaName: D.PAKSHAS[paksha], elongation: elong, endsAt: endT ? endT.date : null };
  }
  function nakshatraAt(date) {
    const lon = moonSidereal(date);
    const index = Math.min(26, Math.floor(lon / NAK));
    const pada = Math.min(4, Math.floor((lon - index * NAK) / PADA) + 1);
    const n = D.NAKSHATRAS[index];
    const endsAt = searchAngle(moonSidereal, ((index + 1) * NAK) % 360, date, 36, 2, 0.5);
    return { index, pada, name: n, akshara: { dev: n.ak[pada - 1], te: devToTelugu(n.ak[pada - 1]), ro: n.ro[pada - 1] }, endsAt };
  }
  function rasiAt(date) {
    const lon = moonSidereal(date);
    const index = Math.floor(lon / 30);
    return { index, name: D.RASIS[index], degreeInSign: lon - index * 30 };
  }

  /* Sunrise for a local calendar date at a place. Falls back to local 06:00 (flag) in polar day/night. */
  function sunrise(dateStr, lat, lon, tz) {
    const { y, mo, d } = parseDate(dateStr);
    checkPlace(lat, lon, tz);
    const midnight = localToUtc(y, mo, d, 0, 0, tz);
    const t = A.SearchRiseSet(A.Body.Sun, new A.Observer(lat, lon, 0), +1, midnight, 1);
    if (t && t.date.getTime() - midnight.getTime() < 86400000) return { at: t.date, estimated: false };
    return { at: localToUtc(y, mo, d, 6, 0, tz), estimated: true };
  }

  /* Weekday of a local calendar date (vara runs sunrise to sunrise; at sunrise it equals the civil weekday). */
  function weekday(dateStr) {
    const { y, mo, d } = parseDate(dateStr);
    const i = new Date(Date.UTC(y, mo - 1, d)).getUTCDay();
    return { index: i, name: D.VARAS[i] };
  }

  /* Birth details -> moon sign, nakshatra, pada, naming syllable, tithi, weekday. */
  function birthChart({ date, time, lat, lon, tz }) {
    const { y, mo, d } = parseDate(date);
    const { h, mi } = parseTime(time);
    checkPlace(lat, lon, tz);
    const utc = localToUtc(y, mo, d, h, mi, tz);
    const sr = sunrise(date, lat, lon, tz);
    // Vedic day starts at sunrise: a birth before sunrise belongs to the previous vara.
    let wd = weekday(date);
    if (utc < sr.at) wd = { index: (wd.index + 6) % 7, name: D.VARAS[(wd.index + 6) % 7], beforeSunrise: true };
    const moon = moonSidereal(utc);
    const nak = nakshatraAt(utc);
    return {
      utc, ayanamsa: ayanamsa(utc), moonSidereal: moon, sunSidereal: sunSidereal(utc),
      rasi: rasiAt(utc), nakshatra: nak, tithi: tithiAt(utc), vara: wd, sunrise: sr,
      // How close the Moon is to a pada edge, in minutes of time (Moon moves about 0.55 deg/hour).
      minutesFromPadaEdge: Math.round((Math.min(moon % PADA, PADA - (moon % PADA)) / 0.55) * 60),
    };
  }

  /* Panchang for one local date at sunrise. */
  function dayPanchang(dateStr, lat, lon, tz) {
    const sr = sunrise(dateStr, lat, lon, tz);
    const t = tithiAt(sr.at);
    const nak = nakshatraAt(sr.at);
    const wd = weekday(dateStr);
    const flags = [];
    if (t.nameIndex === 15) flags.push('amavasya');
    if (t.number === 4 || t.number === 9 || t.number === 14) flags.push('rikta');
    return { date: dateStr, sunrise: sr, tithi: t, nakshatra: nak, vara: wd, flags };
  }

  /* Muhurat helper: list days from `from` for `days` days (max 92). Traditional guidance only. */
  function muhuratDays(from, days, lat, lon, tz) {
    const { y, mo, d } = parseDate(from);
    const n = Math.max(1, Math.min(92, Math.floor(Number(days) || 1)));
    const out = [];
    for (let i = 0; i < n; i++) {
      const dt = new Date(Date.UTC(y, mo - 1, d + i));
      out.push(dayPanchang(dt.toISOString().slice(0, 10), lat, lon, tz));
    }
    return out;
  }

  /* ---------- scripts and names ---------- */
  /* Devanagari -> Telugu: the two Unicode blocks are laid out in parallel (offset 0x300) for every
     letter we use. Word-final bare consonants get a virama, the way Telugu writes Hindi names. */
  function devToTelugu(s, finalVirama) {
    let out = '';
    for (const ch of s) {
      const c = ch.codePointAt(0);
      out += c >= 0x0900 && c <= 0x0963 && c !== 0x093c ? String.fromCodePoint(c + 0x300) : ch;
    }
    if (finalVirama) {
      const last = out.codePointAt(out.length - 1);
      if (last >= 0x0c15 && last <= 0x0c39) out += '్';
    }
    return out;
  }
  const VOWEL_INDEP = { 'अ': 'a', 'आ': 'a', 'इ': 'i', 'ई': 'i', 'उ': 'u', 'ऊ': 'u', 'ए': 'e', 'ऐ': 'e', 'ओ': 'o', 'औ': 'o' };
  const VOWEL_SIGN = { 'ा': 'a', 'ि': 'i', 'ी': 'i', 'ु': 'u', 'ू': 'u', 'े': 'e', 'ै': 'e', 'ो': 'o', 'ौ': 'o', 'ृ': 'i' };
  const isCons = (ch) => ch >= 'क' && ch <= 'ह';
  /* First-syllable key of a Devanagari word: consonant + vowel class, ignoring vowel length.
     श and ष count as one sound (most families treat them so). Clusters take their first consonant. */
  function syllableKey(word) {
    const chars = [...String(word).trim()];
    const c0 = chars[0];
    if (!c0) return '';
    if (c0 === 'ऋ') return 'र|i';
    if (VOWEL_INDEP[c0]) return '|' + VOWEL_INDEP[c0];
    if (!isCons(c0)) return '';
    const cons = c0 === 'श' ? 'ष' : c0;
    let i = 1;
    while (chars[i] === '़') i++;
    while (chars[i] === '्' && isCons(chars[i + 1] || '')) { i += 2; while (chars[i] === '़') i++; }
    return cons + '|' + (VOWEL_SIGN[chars[i]] || 'a');
  }

  /* Chaldean numerology on the English spelling: letters only. */
  const CHALDEAN = { a: 1, i: 1, j: 1, q: 1, y: 1, b: 2, k: 2, r: 2, c: 3, g: 3, l: 3, s: 3, d: 4, m: 4, t: 4, e: 5, h: 5, n: 5, x: 5, u: 6, v: 6, w: 6, o: 7, z: 7, f: 8, p: 8 };
  function chaldean(name) {
    const total = [...String(name).toLowerCase()].reduce((s, ch) => s + (CHALDEAN[ch] || 0), 0);
    let single = total;
    while (single > 9) single = [...String(single)].reduce((s, x) => s + Number(x), 0);
    return { total, single };
  }

  /* Names list -> rows matching the syllable (Devanagari akshara) and filters.
     opts: { gender: 'm'|'f'|'' (unisex names always included), letter: 'A'..'Z'|'', number: 1..9|0 } */
  function teluguName(row) {
    return row.te || devToTelugu(row.hi, !/[aeiouy]$/i.test(row.en));
  }
  function suggestNames(names, akshara, opts) {
    const o = opts || {};
    const key = akshara ? syllableKey(akshara) : '';
    const letter = String(o.letter || '').trim().toLowerCase();
    const num = Number(o.number) || 0;
    return names
      .filter((r) => !key || syllableKey(r.hi) === key)
      .filter((r) => !o.gender || r.g === o.gender || r.g === 'u')
      .filter((r) => !letter || r.en.toLowerCase().startsWith(letter))
      .map((r) => ({ ...r, te: teluguName(r), numerology: chaldean(r.en) }))
      .filter((r) => !num || r.numerology.single === num)
      .sort((a, b) => a.en.localeCompare(b.en));
  }

  return {
    suggestNames, teluguName,
    ayanamsa, ayanamsaMean, nutationLon, moonTropical, moonSidereal, sunSidereal,
    zoneOffsetMinutes, validTimeZone, localToUtc, parseDate, parseTime,
    tithiAt, nakshatraAt, rasiAt, sunrise, weekday, birthChart, dayPanchang, muhuratDays,
    devToTelugu, syllableKey, chaldean, NAK, PADA,
  };
});

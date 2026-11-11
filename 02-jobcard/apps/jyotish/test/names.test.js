const test = require('node:test');
const assert = require('node:assert/strict');
const J = require('../src/core.js');
const D = require('../src/data.js');
const N = require('../src/names.js');

test('akshara table: 27 nakshatras x 4 padas, Devanagari only, Telugu conversion stays in the Telugu block', () => {
  assert.equal(D.NAKSHATRAS.length, 27);
  for (const n of D.NAKSHATRAS) {
    assert.equal(n.ak.length, 4);
    assert.equal(n.ro.length, 4);
    for (const a of n.ak) {
      assert.ok(/^[ऀ-ॿ]+$/.test(a), a);
      assert.ok(/^[ఀ-౿]+$/.test(J.devToTelugu(a)), a);
      assert.ok(J.syllableKey(a), a);
    }
    assert.ok(n.te && n.hi && n.en);
  }
  // Spot checks against two published tables (see data.js).
  assert.deepEqual(D.NAKSHATRAS[0].ro, ['Chu', 'Che', 'Cho', 'La']);
  assert.deepEqual(D.NAKSHATRAS[21].ro, ['Ju', 'Je', 'Jo', 'Gha']);
  assert.deepEqual(D.NAKSHATRAS[26].ro, ['De', 'Do', 'Cha', 'Chi']);
});

test('label tables complete in all three languages', () => {
  for (const [name, list, len] of [['RASIS', D.RASIS, 12], ['TITHIS', D.TITHIS, 16], ['VARAS', D.VARAS, 7], ['PAKSHAS', D.PAKSHAS, 2]]) {
    assert.equal(list.length, len, name);
    for (const x of list) assert.ok(x.en && /[ఀ-౿]/.test(x.te) && /[ऀ-ॿ]/.test(x.hi), name);
  }
  assert.ok(D.CITIES.length >= 30);
  for (const c of D.CITIES) assert.ok(J.validTimeZone(c.tz), c.name);
});

test('syllable keys ignore vowel length and follow clusters', () => {
  assert.equal(J.syllableKey('कार्तिक'), J.syllableKey('का'));
  assert.equal(J.syllableKey('कमला'), 'क|a');
  assert.equal(J.syllableKey('प्रिया'), 'प|i');
  assert.equal(J.syllableKey('ज्योति'), 'ज|o');
  assert.equal(J.syllableKey('ऐश्वर्या'), '|e');
  assert.equal(J.syllableKey('शंकर'), 'ष|a');
  assert.equal(J.syllableKey('ऋषि'), 'र|i');
  assert.notEqual(J.syllableKey('डा'), J.syllableKey('दा')); // retroflex and dental stay apart
});

test('names: at least 150, unique, valid fields', () => {
  assert.ok(N.length >= 150, `${N.length}`);
  assert.equal(new Set(N.map((r) => r.en)).size, N.length);
  for (const r of N) {
    assert.ok(['m', 'f', 'u'].includes(r.g), r.en);
    assert.ok(/^[A-Z][a-z]+$/.test(r.en), r.en);
    assert.ok(/^[ऀ-ॿ]+$/.test(r.hi), r.en);
    assert.ok(r.meaning.length > 2, r.en);
    assert.ok(/^[ఀ-౿]+$/.test(J.teluguName(r)), r.en);
  }
});

test('suggestNames: syllable, gender, letter and number filters', () => {
  const ju = J.suggestNames(N, 'जू').map((r) => r.en);
  assert.ok(ju.includes('Juhi'));
  const ka = J.suggestNames(N, 'का', { gender: 'f' });
  assert.ok(ka.length > 0 && ka.every((r) => r.g !== 'm'));
  assert.ok(ka.some((r) => r.en === 'Kavya'));
  assert.ok(!ka.some((r) => r.en === 'Karthik'));
  const k = J.suggestNames(N, '', { letter: 'k' });
  assert.ok(k.length > 5 && k.every((r) => r.en.startsWith('K')));
  const six = J.suggestNames(N, '', { number: 6 });
  assert.ok(six.length > 0 && six.every((r) => r.numerology.single === 6));
  assert.equal(J.suggestNames(N, 'डी').length, 0);
});

test('Chaldean numerology', () => {
  assert.deepEqual(J.chaldean('Akhil'), { total: 12, single: 3 }); // 1+2+5+1+3
  assert.deepEqual(J.chaldean('Om'), { total: 11, single: 2 }); // 7+4
  assert.deepEqual(J.chaldean('Sai Teja'), { total: 16, single: 7 }); // S3 A1 I1 + T4 E5 J1 A1, space ignored
  assert.deepEqual(J.chaldean(''), { total: 0, single: 0 });
});

test('Telugu conversion: final virama only when the English spelling ends in a consonant', () => {
  const t = (en) => J.teluguName(N.find((r) => r.en === en));
  assert.equal(t('Akhil'), 'అఖిల్');
  assert.equal(t('Krishna'), 'కృష్ణ');
  assert.equal(t('Ram'), 'రామ్');
  assert.equal(t('Vennela'), 'వెన్నెల');
});

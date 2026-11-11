# Kalpa Jyotish (prototype)

Idea A from `02-jobcard/research/a152-app-ideas.md` §4. A phone-first web app (PWA) that works out, with no AI and no network:

- **Birth star:** Moon sign (rasi), nakshatra and pada, the naming syllable (akshara) in Telugu, Hindi and English letters, plus tithi and weekday.
- **Names:** 239 names written by us (English, Telugu, Hindi, meaning), filtered by syllable, boy or girl, English first letter, and Chaldean name number. There is also a number check for any name.
- **Good days:** a list of up to 92 days with tithi, nakshatra and weekday at local sunrise, plus end times. Amavasya and Rikta tithis (Chaturthi, Navami, Chaturdashi) are flagged. Labelled "Traditional guidance, check with your family priest."
- English, Telugu and Hindi labels; light and dark; 390 px first. Disclaimer: "For guidance and tradition. No health, legal or money predictions."

**Status: private prototype. Not published** (rule 9; it needs Akhil's "go").

## Run it
```bash
cd 02-jobcard/apps/jyotish
npm install          # only needed for the tests
npm test             # node --test test/*.test.js
npx serve .          # then open the printed URL on a phone or at 390 px
```
You can also open `index.html` straight from disk; it works offline. The manifest makes it installable when served over https or localhost. There is **no service worker** on purpose.

## Privacy
- Every calculation runs in the page. The Content-Security-Policy sets `connect-src 'none'`, so the page cannot make network calls. A test checks for `fetch`, XHR, sockets, beacons and service workers.
- Birth details are kept in `localStorage` only when the user ticks "Remember on this phone". The About tab has "Delete saved details". Language and theme choices are stored too, and they are not personal data.
- A DPDP privacy notice is still needed before any public launch that adds accounts or payments.

## Licences
| Part | Licence | Checked |
|---|---|---|
| [astronomy-engine](https://github.com/cosinekitty/astronomy) 2.1.19 by Don Cross (Moon, Sun, sunrise) | **MIT** | `node_modules/astronomy-engine/package.json` says `"license": "MIT"`; the header of the shipped file carries the full MIT text; the GitHub repo is marked MIT (7 Nov 2026). Vendored unmodified as `vendor/astronomy.browser.min.js` (a test checks it matches npm). |
| Swiss Ephemeris | AGPL or paid | **Not used.** |
| Rozha One, Anek Latin, Telugu and Devanagari fonts | SIL OFL 1.1 | Copied from `00-hq/design/fonts` with their OFL texts. |
| Kalpavruksha icon, tokens.css | Kalpa Labs | Copied from `00-hq/design`. A test fails if `tokens.css` drifts from HQ. |
| Name list, syllable table, labels | Kalpa Labs | Written for this app. |

## How the maths works and how accurate it is
- **Moon and Sun:** astronomy-engine gives the true ecliptic longitude of date. The project states an accuracy of about ±1 arcminute against NOVAS. The Moon moves about 0.5′ per minute, so its times are good to roughly 2 minutes.
- **Lahiri ayanamsa:** the 21 Mar 1956 anchor (JD 2435553.5) is 23.245524743°, the mean value Swiss Ephemeris uses for Lahiri. We carry it forward with the IAU 2006 general precession, p = 5028.796195″T + 1.1054348″T² (T in Julian centuries from J2000). Nutation in longitude (Meeus ch. 22 short series, about 0.5″) is added to get the true ayanamsa. Result: **23.8571° at J2000**, against the published Lahiri J2000 value of 23.857°. Over 1900–2100 we expect it to stay within about 0.01° of Swiss Ephemeris Lahiri. That is by construction and has not been compared point by point.
- **Rasi** = floor(sidereal Moon / 30°). **Nakshatra** = floor(sidereal Moon / 13°20′). **Pada** = quarter of the nakshatra (3°20′).
- **Tithi** = floor((Moon − Sun) / 12°). This does not depend on the ayanamsa. The end time comes from astronomy-engine's `SearchMoonPhase`.
- **Weekday:** the Vedic day runs from sunrise to sunrise, so a birth before local sunrise gets the previous weekday. In Good days, tithi and nakshatra are the ones at local sunrise (astronomy-engine sunrise: upper limb, 34′ refraction).
- **Time zones:** IANA zones go through the browser's `Intl`, which includes historical offsets and DST. Fixed offsets such as `+05:30` also work.
- **Naming syllables:** the 27×4 Hoda/Avakahada table was checked against two published lists (himalayanacademy.com and dekhopanchang.com, 7 Nov 2026). Variants differ by region, for example Shravana Ju/Je/Jo/Gha against Khi/Khu/Khe/Kho. Known variants are noted in `src/data.js`. Name matching compares the first consonant and vowel, ignoring vowel length (श and ष count as the same). Retroflex and dental stay separate. 33 rare padas (Nga, retroflex Da/Ta and others) have no names in the list, so the app offers the other padas of the same nakshatra.
- **Telugu name spellings** are converted from the Hindi spelling (the Unicode blocks are parallel), with a virama added on a final consonant. Two names have hand-written Telugu (Venkatesh, Vennela).

## Tests (26, all passing)
- `test/core.test.js`
  - The ayanamsa value and its drift, and that sidereal equals tropical minus ayanamsa.
  - Twelve real full and new moons, where the tithi just before is Purnima or Amavasya.
  - Pada, nakshatra and rasi stay consistent over 200 instants, along with end times.
  - Time zones, including New York daylight saving.
  - Input errors, the before-sunrise weekday rule, muhurat flags and the polar-night fallback.
- Published dates:
  - Diwali, 1 Nov 2024, Hyderabad: Amavasya at sunrise, ending 18:17 IST. drikpanchang via zeebiz says 18:16.
  - Onam, 15 Sep 2024, Kochi: Shravana at sunrise, ending 18:49 IST. drikpanchang says 18:49.
  - Guru Purnima, 21 Jul 2024: Purnima at sunrise.
  - Sri Rama Navami, 17 Apr 2024: Shukla Navami, flagged Rikta.
- `test/names.test.js`: the syllable table, three-language labels, all 35 cities' time zones, the syllable matcher, the 239 names, filters, Chaldean sums, and Telugu conversion.
- `test/app.test.js`: no network code, the MIT header and vendored copy, the manifest, every label in three languages with matching placeholders, the disclaimer, the repo's `vibecheck.mjs` scan, no em dashes, and only Kalpa token colours.
- A manual browser check (headless Chrome, 390 px, light and dark, served locally and from file://) found no sideways scroll, no console errors and zero off-site requests.

## Check against a real panchang before real use
1. **Nakshatra and pada near a boundary.** The app warns when birth is within 20 minutes of a pada change. Compare a sample of 10 births with a trusted panchang (for example Drik Panchang with Lahiri) or a family priest.
2. **Tithi and nakshatra end times.** We matched two published times within 1 to 2 minutes. Spot-check a few months in other cities, especially the US and Australia across DST changes.
3. **The akshara table and Telugu spellings.** Regional lists differ, and the Telugu names are auto-converted. A Telugu speaker should review the 239 names and their meanings.
4. **Muhurat flags.** Only Amavasya and Rikta tithis are flagged. Real muhurat practice also weighs nakshatra, yoga, karana, rahu kalam and the event type, so keep the "check with your family priest" label.
5. **Sunrise convention.** Some panchangs use the Sun's centre or no refraction, which moves sunrise by 1 to 3 minutes. That only matters on days when a tithi changes right at sunrise.

## Files
`index.html`, `styles.css`, `tokens.css`, `manifest.webmanifest`, `icon.svg`, `src/core.js` (calculations), `src/data.js` (tables and cities), `src/names.js` (names), `src/i18n.js` (labels), `src/app.js` (UI), `vendor/` (astronomy-engine, MIT), `fonts/` (OFL), `test/`.

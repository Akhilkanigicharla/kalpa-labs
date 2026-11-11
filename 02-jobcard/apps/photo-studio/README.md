# Kalpa Photo Studio (prototype PWA)

Passport and visa photos made on the phone. Idea B in `02-jobcard/research/a152-app-ideas.md`. Status: **private prototype, not published.**

Photos never leave the device: there is no upload code, and the page's Content-Security-Policy blocks every outside request (no CDN, no fonts from Google, no analytics).

## Run it
```bash
cd 02-jobcard/apps/photo-studio
npm test                     # node --test test/*.test.mjs (no installs needed)
python3 -m http.server 8080  # then open http://localhost:8080 at 390 px wide
```
The service worker (offline use) only registers on https or localhost. It caches the app shell cache-first: bump `CACHE` in `sw.js` whenever a file changes.

## Files
| File | What it is |
|---|---|
| `specs.json` | Photo rules for 8 documents (India passport, India e-Visa, US, UK, Schengen, Canada, Australia, UAE). Every entry has `verify_url` and `verified: false` |
| `core.mjs` | Pure functions: `computeCrop`, `faceToHead`, `outputSize` (300/600 dpi or upload size), `sheetLayout` (4x6 inch / A4), `validate` (pass/warn/fail reasons), `replaceBackground` (beta) |
| `index.html`, `app.js`, `styles.css` | One mobile-first page: pick rule, choose photo, drag the head box, check, save JPG and print sheet |
| `tokens.css`, `fonts/`, `icons/icon.svg` | Copies of the Kalpa design system (a test keeps `tokens.css` identical to `00-hq/design/tokens.css`) |

## How the crop works
1. The user drags a box from the top of the hair to the chin (manual is the default). "Find my face" appears only when the browser has the built-in `FaceDetector`; its face box is grown upwards to the crown by `faceToHead` (an estimate, so the user still checks it).
2. Scale = head box pixels / target head height (middle of the rule's range).
3. The crop is centred on the head. If the rule has an eye line (US), the eyes go to the middle of that range; otherwise 40% of the spare height goes above the head.
4. Parts of the frame past the photo edge are filled with the rule's background colour, with a warning (fail if more than 15%).

## Before launch (a person must do these)
1. Open each `verify_url`, compare every number, then set `verified: true` and `verified_on`. Until then the app shows **spec to be checked**. Least sure: UAE (size only from third-party sites), India e-Visa pixel/KB limits, India passport "70-80%" meaning, Schengen background colour per country.
2. Test on real phones (Android Chrome, iPhone Safari) with real selfies: EXIF rotation, big 12 MP photos, print a 4x6 sheet at "actual size" and measure with a ruler.
3. Self-host Anek Latin 400 (OFL) for body text; only 600/700 are in `fonts/` now.

## Later: real models (to evaluate, not chosen)
Run in the browser with ONNX Runtime Web or Transformers.js so photos still stay on the device. Check each model card's licence (MIT/Apache only) and size before use.
Licence tags below were read from the Hugging Face Hub on 7 Nov 2026; "to confirm" means not checked yet.
- Face and landmarks (crown/chin/eyes instead of a guess): **MediaPipe Face Landmarker** (Apache-2.0, to confirm), **opencv/face_detection_yunet** (no licence tag on the Hub repo; confirm on OpenCV Zoo GitHub).
- Background removal (to replace the beta threshold tool): **Xenova/modnet** (apache-2.0, ONNX, made for Transformers.js, small), **ZhengPeng7/BiRefNet** (mit, but 220M params: heavy for phones), **MediaPipe Selfie Segmenter** (Apache-2.0, to confirm). Skip **briaai/RMBG-1.4**: licence "other" (Bria's own licence, not MIT/Apache).
- Checks a model could add: eyes open, neutral expression, no glare, even lighting, head tilt.

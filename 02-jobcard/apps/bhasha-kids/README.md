# Kalpa Bhasha Kids (prototype)

Mother-tongue practice for NRI kids aged 4 to 10. Telugu first, Hindi second. Idea C in `02-jobcard/research/a152-app-ideas.md` §4.
**Status: private prototype. Not published. The words have NOT been checked by a native speaker yet.**

## Run it (2 minutes)
```bash
cd 02-jobcard/apps/bhasha-kids
node --test test/*.test.mjs      # 19 tests (also: npm test)
python3 -m http.server 8080      # then open http://localhost:8080 (phone width 390 px)
```
It needs a web server (opening the file directly blocks loading the lesson files). No install, no build, no dependencies.

## What a child can do
- **Cards:** big letter or word, tap "Show me" for the sound and meaning, then Again / I knew it / Easy.
- **Listen:** reads the word aloud with the device's own te-IN / hi-IN voice. No voice on the device? It says so and shows the spelling for a grown-up to read.
- **Match:** tap a Telugu/Hindi word, then its meaning (letters match to their sound).
- **Say it:** the child says the word; the browser checks it. On only when the browser can listen **on the device** (see privacy below).
- **Stars** (0 to 3, best kept) per lesson, a **daily streak**, and **Practice today** for words due for review.
- **Grown-ups** button, behind a parent gate (two-digit × one-digit sum): progress for each language, last 7 days, words to practise together, per-lesson table, sound and privacy settings, save a copy, reset.

## Lessons (`data/te.json`, `data/hi.json`)
| | Telugu | Hindi |
|---|---|---|
| Vowels / consonants | 15 achulu, 26 hallulu | 13 svar, 31 vyanjan |
| Themes | 10 (family, colours, numbers 1 to 10, food, animals, body, home, greetings, festivals, actions); 8 words each, numbers 10 | same 10 themes |
| Phrases | 20 everyday | 20 everyday |

Every item has script, plain-ASCII transliteration and English. Both files carry `"native_speaker_checked": false`; a test keeps it that way until a native speaker signs off (then set it `true` and `checked_by`, and update the test).

**What a native speaker must check first:** every word and phrase, then especially: the transliteration style (simple learner spelling, capitals = retroflex: `tammuDu`, `ghoDaa`); Telugu `గులాబీ` for pink, `శుభోదయం` (formal) for good morning, `కాదు` as the kid word for "no", `దోసె` vs `దోశ` spelling; Telugu family words (only `అమ్మమ్మ`, maternal grandmother, is in; `నానమ్మ` could be added); Hindi gendered phrases (`रहा/रही`, marked in a note); letter example words (`ఈగ`, `ఊయల`, `ఒకటి` for ఒ; Hindi `ऐनक`-style examples were left out on purpose). Regional variants (Telangana vs Andhra; Hindi vs Hindustani) are the main open question.

## Code
| File | What |
|---|---|
| `src/srs.js` | Spaced repetition: **SM-2** (Wozniak 1990, SuperMemo-2, written from the published description). Kid tweaks: 3 buttons (again=1, good=4, easy=5), a miss comes back the same day. |
| `src/progress.js` | Streak (consecutive days, clock-back safe), stars (90%+ = 3, 70%+ = 2, any right = 1), parent summary + one-line text. A same-day right answer on a not-due card does not push the schedule. |
| `src/lessons.js` | Lessons from the JSON, data validator (script range, ASCII transliteration, unique ids), match rounds. |
| `src/match.js` | Say-it check: Unicode edit distance on script or transliteration, 70% threshold. |
| `src/speech.js` | Feature detection for speechSynthesis and SpeechRecognition (`available()`, `processLocally`). |
| `src/storage.js`, `src/gate.js` | localStorage in try/catch with memory fallback; parent gate sum. |
| `app.js`, `app.css`, `index.html` | Single-page UI on the Kalpa tokens (`vendor/tokens.css` copied unchanged, world colour `--l2`, self-hosted OFL fonts in `fonts/`). Light + dark checked at 390 px; `vibecheck` heuristics pass. |
| `sw.js`, `manifest.webmanifest` | Installable PWA, offline after first load, caches our own files only. |

Checked in headless Chrome (7 Nov 2026, 390 px, light and dark): cards, match, say-it (with a fake on-device recogniser), Hindi, parent gate wrong + right, no horizontal scroll, no console errors, **zero requests outside the app's own origin**.

## Privacy by design (what is already true)
- No accounts, no ads, no analytics, no chat, no links out, no other users. CSP blocks every outside connection (`default-src 'self'`).
- Progress stays in this browser's localStorage. Nothing is sent to Kalpa Labs. Parents can save a copy or reset.
- **Say it:** browser speech recognition is server-based by default and sends audio to the browser maker (MDN, "Using the Web Speech API"). The app only uses `processLocally = true` (on-device). If the browser can only do server recognition, Say it stays **off** unless a parent ticks the clearly worded switch behind the gate. A parent can trigger the one-time on-device speech-pack download where offered.

## Rules to follow before any real launch (Akhil's "go" needed)
1. **COPPA (US, under-13s):** if the app ever collects personal information from a child (voice recordings, names, accounts, persistent IDs, analytics), get **verifiable parental consent** first, post a clear privacy notice, give parents review/delete rights, keep only what is needed, and bind every vendor by contract. The 2025 FTC rule update (written security programme, separate consent for sharing with third parties) applies; check the current rule text on ftc.gov before launch.
2. **DPDP Act 2023 + Rules (India, under-18s):** **verifiable parental consent** before processing a child's data; no tracking, behavioural monitoring or targeted ads at children; privacy notice in plain language; a grievance contact. Check the notified Rules' dates and consent methods before launch.
3. Also: GDPR-K / UK Children's Code if marketed in the UK/EU (NRI families there); app-store kids-category rules if it goes to a store.
4. A native speaker signs off each language file (and the test flips to `true`).
5. If an AI tutor is added: no free-form chat with strangers ever; AI replies filtered and limited to the lesson; nothing a child says stored off-device without consent.

## Next step: AI voice tutor (named, not integrated)
Goal: short spoken back-and-forth ("ఏం తిన్నావు?" → child answers → gentle correction). Free/open options to evaluate later. Licences below are from each Hugging Face model card's licence tag, read 7 Nov 2026; a second check is still needed (rule 8).
| Job | Option | Licence tag | Note |
|---|---|---|---|
| Speech to text, in the browser | `onnx-community/whisper-base` via Transformers.js (WebGPU) | apache-2.0 | Fully on-device: best fit for kids' privacy. Telugu accuracy of small Whisper models is weak: test first |
| Speech to text, better Indic | `ai4bharat/indic-conformer-600m-multilingual` | MIT (gated) | Strong for Telugu/Hindi; needs a server, so parental consent first |
| Speech to text | `openai/whisper-small` | apache-2.0 | Middle ground |
| Text to speech | `ai4bharat/indic-parler-tts` | apache-2.0 (gated) | Natural Telugu/Hindi voices; server-side, could pre-record all lesson audio once and ship it as files |
| Text to speech | `facebook/mms-tts-tel` / `mms-tts-hin` | **cc-by-nc-4.0** | Non-commercial only: do not use in a paid product |
| Tutor brain | `sarvamai/sarvam-m` | apache-2.0 | Indic-tuned LLM; or free OpenRouter / Groq models through n8n (rule 11) with a strict kid-safe prompt |

Cheapest safe first move: pre-generate lesson audio with Indic Parler-TTS (so Listen works on every device), keep recognition on-device.

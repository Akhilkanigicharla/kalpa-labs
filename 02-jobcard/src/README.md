# JobCard app (Expo, Android first)

Scaffolded from the [Obytes template](https://github.com/obytes/react-native-template-obytes) v9 (MIT, commit fd9b358, licence in `LICENSE-obytes`), Expo SDK 54.
Removed: the demo feed, the style demo, Arabic/RTL, husky/commitlint/maestro. Added (A36, b2.q19 + q20):

| Piece | File |
|---|---|
| Telugu-first strings (te / hi / en) | `src/translations/*.json` |
| Kalpavruksha tokens (copied from `00-hq/design/tokens.css`, a test keeps them equal) and fonts | `src/lib/theme/` |
| Live dictation, offline on-device, audio kept for later server STT | `src/lib/jobcard/voice.ts` (`expo-speech-recognition` 3.1.3) |
| Local SQLite + ordered outbox with backoff | `src/lib/jobcard/db.ts`, `outbox.ts` |
| Offline bill numbering (FY series) and saving | `src/lib/jobcard/jobs.ts` |
| Bill → PDF → share sheet (WhatsApp) | `src/lib/jobcard/share.ts` (`expo-print` + `expo-sharing`) |
| Sync to Supabase as the signed-in technician (RLS) | `src/lib/jobcard/sync.ts` |
| Record screen | `src/features/jobcard/record-screen.tsx` |

The parser and invoice maths are **shared** with the WhatsApp bot: they live in `02-jobcard/lib/` and are imported as `@core/…`.

Checks (run in the `Kalpa quality` workflow, nothing installs on Akhil's PC):
```
corepack enable && pnpm install && pnpm type-check && CI=1 pnpm test
```

Not done yet: phone-OTP sign-in wired to Supabase, technician profile screen (the bill button needs one), local reminder notifications, the Expo SDK 57 upgrade, a device build (needs Akhil's free Expo account, CEO queue).

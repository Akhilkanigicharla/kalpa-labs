# UX check: JobCard "my customers" app (02-jobcard/web) · 9 Nov 2026

Against `00-hq/design/UX-PATTERNS.md`. The free-model draft (K050) saw only the old Expo files and marked 12 rows UNVERIFIED, so Claude audited the live PWA (`web/app.mjs`, the app technicians actually open) row by row.
Tests: `web/check.py` (manifest, offline, 390 px light + dark, 44 px, 16 px inputs) and new `web/ux.py` (the fixes below, live mode faked in the browser); tap sweep `00-hq/site/tests/test_tap_sweep.py` on all 4 tabs at 390 px light + dark; `npm test` in 02-jobcard (36 pass). All PASS, all in CI (`quality.yml`).

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | ✅ WhatsApp opt-in tick changes at once; fixed 9 Nov: if saving fails it un-ticks and says "Couldn't save". |
| 2 | Skeleton loaders | ✅ Fixed 9 Nov: shimmer cards in `#main` until data arrives (stop for reduced motion). |
| 3 | Command palette | ➖ 4 tabs on a phone; a technician with wet hands needs big tabs, not a search-everything box. |
| 4 | Persistent navigation | ✅ Bottom tab bar (Due, Customers, Bills, Record), current tab marked. |
| 5 | Loading and empty states | ✅ "Nobody this month."; fixed 9 Nov: a search with no match and an empty Bills tab now say so. |
| 6 | Autosave | ➖ No long forms: one phone field, one code field, voice notes saved by the server. |
| 7 | Debouncing | ✅ Fixed 9 Nov: customer search waits 250 ms after the last letter and keeps the cursor in place. |
| 8 | Throttling | ✅ Sign-in buttons disable while waiting; recording has a 2-minute cap; one recorder at a time. |
| 9 | Smart form validation | ✅ Fixed 9 Nov: the phone number is checked when you leave the field (`aria-invalid` + message) and clears as soon as it is right. |
| 10 | Bulk actions | ➖ On purpose: reminders go one customer at a time (WhatsApp opt-in rules; the design brief forbids bulk sends). |
| 11 | Reusable data table | ➖ Cards on a phone; no tables. |
| 12 | Advanced filtering | ✅ Search by name, area or phone; Due list split into overdue / due / AMC ending. |
| 13 | Keyboard shortcuts | ➖ Phone-only app; keyboard `enterkeyhint` set on every field instead. |
| 14 | Tier-based UI indicators | ✅ Voice minutes used vs plan limit shown on Record ("Voice this month: 3/60 min"). |
| 15 | Onboarding data capture | ✅ Phone + SMS code only; business name and language come from the technician's profile. |
| 16 | Referral pages | ➖ Not in the pilot; add with paid plans. |
| 17 | Custom 404 | ✅ Fixed 9 Nov: any unknown path opens the app (Netlify rewrite to `/index.html`, real files win; offline the service worker does the same). The app is behind a login, so it is `noindex` (SEO rule 6). |
| 18 | Mobile-optimised layout | ✅ 390 px, light + dark, 16 px inputs (no iOS zoom), safe-area bottom bar; fixed 9 Nov: Sign out raised from 36 px to 44 px. |
| 19 | Destructive action protection | ✅ Fixed 9 Nov: Sign out needs a second tap within 4 s (signing back in costs an SMS code). Un-ticking WhatsApp consent stays one tap: withdrawing consent must be easy (DPDP). |
| 20 | Graceful error recovery | ✅ Offline banner; fixed 9 Nov: a failed load shows the reason and a working "Try again" button; recording errors say "No internet" or "Something went wrong". |

No ❌ left. Telugu and Hindi for the 5 new messages were written by Claude: a Telugu speaker checks them before go-live (DELEGATE.md rule).

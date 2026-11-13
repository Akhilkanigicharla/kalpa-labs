# Kalpa UX patterns: the 20 every Kalpa UI must have

Akhil, 8 Nov 2026: "update this with every page and UI in Kalpa Labs going forward." Source: the list in Sohail Jafri's reel
"20 UX Patterns Every SaaS Needs" (8 Nov). The checks under each pattern are ours, written for our users (salon owners,
technicians, students, founders), mostly on a phone in Telugu, Hindi or English.

**How to use it.** Before any UI is ticked, fill the table at the bottom for that UI in its world's `design/` folder
(`ux-check.md`): each pattern is ✅ done, ➖ not relevant (say why) or ❌ missing (add a roadmap item). This sits next to
the design system (`DESIGN-SYSTEM.md`) and the phone tap test (CLAUDE.md rule 5). "Not relevant" is fine; "forgot" is not.

Kinds of UI: **P** public page (site, landing, store page) · **A** app screen (dashboard, JobCard, CEO Room, extension
popup) · **C** chat (BotBhai web chat, WhatsApp flows) · **F** form (sign-up, pilot form, settings).

## Speed and feedback
| # | Pattern | Applies to | Kalpa check |
|---|---|---|---|
| 1 | Optimistic UI updates | A C | A tap shows the result at once (message bubble, ticked job); if the save fails, roll back and say so. |
| 2 | Skeleton loaders | A P C | Grey shapes where content will appear, never a blank page or a lone spinner; respect reduced motion. |
| 5 | Loading and empty states | all | Every list has a loading view and a helpful empty view with the one next action ("No jobs yet. Add your first job"). |
| 6 | Autosave | A F | Long forms and drafts save as you type (local first), with "Saved" shown; nothing lost if the phone sleeps. |
| 7 | Debouncing | A F C | Search and live validation wait ~300 ms after typing stops; no request per keystroke. |
| 8 | Throttling | A C | Send / submit / refresh buttons can't fire twice; scroll and resize handlers are throttled. |

## Finding and moving
| # | Pattern | Applies to | Kalpa check |
|---|---|---|---|
| 3 | Command palette | A (desktop) | Ctrl/⌘+K to jump to any page or action. Not for phone-first screens: mark ➖ there. |
| 4 | Persistent navigation | A | Same nav on every screen: sidebar on desktop, bottom bar on phone (thumb reach, 44 px targets). |
| 13 | Keyboard shortcuts | A (desktop) | Common actions have shortcuts, listed on "?"; never the only way to do something. |
| 18 | Mobile-optimised layout | all | Works at 390 px light + dark: no sideways scroll, nothing covered, 16 px inputs (no zoom), safe areas. Tested by `test_tap_sweep.py`. |

## Data
| # | Pattern | Applies to | Kalpa check |
|---|---|---|---|
| 11 | Reusable data table | A | One table component per product: sort, paginate, sticky header, stacks into cards on a phone. |
| 12 | Advanced filtering | A | Filters by the fields people actually use (date, status, customer), shown as removable chips; remembered per user. |
| 10 | Bulk actions | A | Select many → one action (mark done, export, delete) with a count ("3 selected"). |

## Forms and onboarding
| # | Pattern | Applies to | Kalpa check |
|---|---|---|---|
| 9 | Smart form validation | F | Check on blur, plain-language messages next to the field, in the user's language; Indian phone, PIN and GST formats. |
| 15 | Onboarding data capture | A F | Ask only what the first value needs (2–3 fields), the rest later; show progress; DPDP consent in plain words. |

## Money and growth
| # | Pattern | Applies to | Kalpa check |
|---|---|---|---|
| 14 | Tier-based UI indicators | A | Free / paid features are labelled; a locked feature says what unlocks it, no dark patterns. Only once we charge. |
| 16 | Referral and affiliate pages | P A | Share link + what both sides get; affiliate links marked #ad (ASCI). Only once a product is live. |

## Safety and errors
| # | Pattern | Applies to | Kalpa check |
|---|---|---|---|
| 17 | Custom 404 page | P | Branded 404 with a way home and to chat; same for the extension's error page. |
| 19 | Destructive action protection | A F | Delete / cancel / send-to-all asks to confirm with the item named, or offers Undo for 10 s; never a browser `confirm()`. |
| 20 | Graceful error recovery | all | Errors say what happened, that their work is safe, and a Retry button ("Couldn't save. Your work is safe. Retry"); offline is detected; nothing crashes to a blank page. |

## Per-UI check (copy into `<world>/design/ux-check.md`)
| # | Pattern | Status (✅ / ➖ why / ❌ + roadmap id) |
|---|---|---|
| 1 | Optimistic UI | |
| 2 | Skeleton loaders | |
| 3 | Command palette | |
| 4 | Persistent navigation | |
| 5 | Loading and empty states | |
| 6 | Autosave | |
| 7 | Debouncing | |
| 8 | Throttling | |
| 9 | Smart form validation | |
| 10 | Bulk actions | |
| 11 | Reusable data table | |
| 12 | Advanced filtering | |
| 13 | Keyboard shortcuts | |
| 14 | Tier indicators | |
| 15 | Onboarding capture | |
| 16 | Referral / affiliate | |
| 17 | Custom 404 | |
| 18 | Mobile layout | |
| 19 | Destructive action protection | |
| 20 | Graceful error recovery | |

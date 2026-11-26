# Kalpa UX patterns: the 20 every Kalpa UI must have (+ 20 Laws of UX)

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

## The 20 Laws of UX (second check)

Akhil, 26 Nov 2026 (Charles Liu's reel, A342): every page and UI also passes these 20 laws. Same rule as above: ✅ done,
➖ not relevant (say why) or ❌ missing (add a roadmap item). Sources: lawsofux.com (Jon Yablonski) for 17 laws, Nielsen
Norman Group for 3 (links checked live 27 Nov 2026, all HTTP 200). The checks are ours, for a 390 px phone.

| # | Law | What it means | Kalpa check (390 px phone) | Source |
|---|---|---|---|---|
| L1 | Aesthetic-usability effect | Good-looking UI is forgiven more and feels easier. | Kalpa tokens only (no new colours or fonts), even spacing, no broken or stretched images in light and dark. | [lawsofux](https://lawsofux.com/aesthetic-usability-effect/) |
| L2 | Law of proximity | Things placed close together read as one group. | Each label sits right above its field; space between groups is clearly bigger than inside a group. | [lawsofux](https://lawsofux.com/law-of-proximity/) |
| L3 | Von Restorff effect | The one thing that looks different gets remembered. | Exactly one filled primary button per screen; warnings use the error colour and an icon, never colour alone. | [lawsofux](https://lawsofux.com/von-restorff-effect/) |
| L4 | Zeigarnik effect | Unfinished tasks stay on people's minds. | Multi-step flows show "step 2 of 3" and keep a half-filled form so the user can come back and finish. | [lawsofux](https://lawsofux.com/zeigarnik-effect/) |
| L5 | Tesler's law | Some complexity can't be removed, only moved. | We carry it, not the user: auto-fill city, date, price and language; never ask for what we already know. | [lawsofux](https://lawsofux.com/teslers-law/) |
| L6 | Law of Prägnanz | People see the simplest shape they can. | Plain icons and simple layouts; no busy backgrounds behind text; one idea per card. | [lawsofux](https://lawsofux.com/law-of-pr%C3%A4gnanz/) |
| L7 | Serial position effect | First and last items are remembered best. | The most important option is first in lists and menus, and the main action is last (bottom of screen). | [lawsofux](https://lawsofux.com/serial-position-effect/) |
| L8 | Progressive disclosure | Show the basics first, details on request. | Advanced settings, fine print and long FAQs sit behind "More" or an expander; the first screen fits one task. | [NN/g](https://www.nngroup.com/articles/progressive-disclosure/) |
| L9 | Law of common region | Things inside one border or box read as a group. | Related info and its button share one card; no button floats between two cards. | [lawsofux](https://lawsofux.com/law-of-common-region/) |
| L10 | Goal-gradient effect | People speed up as they near a goal. | Long tasks show progress (bar or "2 of 3 done"); the last step says how close they are. | [lawsofux](https://lawsofux.com/goal-gradient-effect/) |
| L11 | Law of similarity | Things that look alike read as doing the same thing. | Every link looks like a link, every secondary button has the same style; nothing tappable looks like plain text. | [lawsofux](https://lawsofux.com/law-of-similarity/) |
| L12 | Recognition over recall | Seeing options beats remembering them. | Show recent items, choices and examples (chips, pickers) instead of making the user type from memory. | [NN/g](https://www.nngroup.com/articles/recognition-and-recall/) |
| L13 | Pareto principle | About 80% of use comes from 20% of features. | The 1–2 most used actions are on the first screen; rarely used ones move one tap deeper. | [lawsofux](https://lawsofux.com/pareto-principle/) |
| L14 | Occam's razor | The simplest design that works is best. | Remove any field, step or element that changes nothing; each form asks only what it needs (DPDP minimum data too). | [lawsofux](https://lawsofux.com/occams-razor/) |
| L15 | Parkinson's law | A task fills the time it is given. | Forms are short enough to finish in about a minute; autofill and saved details cut the time further. | [lawsofux](https://lawsofux.com/parkinsons-law/) |
| L16 | Law of uniform connectedness | Visually connected things read as related. | Steps, timelines and tabs use a line, shared colour or container to show they belong together. | [lawsofux](https://lawsofux.com/law-of-uniform-connectedness/) |
| L17 | Paradox of the active user | People start using things without reading help. | Help sits inside the flow (hints, placeholders, empty states), never only in a manual or video. | [lawsofux](https://lawsofux.com/paradox-of-the-active-user/) |
| L18 | Cognitive load | Each extra thing to process costs mental effort. | One main task per screen, at most 5 choices at a time, plain words in the user's language and script. | [lawsofux](https://lawsofux.com/cognitive-load/) |
| L19 | Default effect | Most people keep the default they are given. | Defaults are the safe, honest choice: marketing opt-ins off, cheapest fitting plan pre-selected, language from the browser. | [NN/g](https://www.nngroup.com/articles/the-power-of-defaults/) |
| L20 | Peak-end rule | People judge an experience by its best moment and its end. | The success screen is warm and clear (what happened, what's next); errors end with a way forward, never a dead end. | [lawsofux](https://lawsofux.com/peak-end-rule/) |

### Per-UI law check (copy into `<world>/design/ux-check.md` below the pattern table)
| # | Law | Status (✅ / ➖ why / ❌ + roadmap id) |
|---|---|---|
| L1 | Aesthetic-usability effect | |
| L2 | Law of proximity | |
| L3 | Von Restorff effect | |
| L4 | Zeigarnik effect | |
| L5 | Tesler's law | |
| L6 | Law of Prägnanz | |
| L7 | Serial position effect | |
| L8 | Progressive disclosure | |
| L9 | Law of common region | |
| L10 | Goal-gradient effect | |
| L11 | Law of similarity | |
| L12 | Recognition over recall | |
| L13 | Pareto principle | |
| L14 | Occam's razor | |
| L15 | Parkinson's law | |
| L16 | Law of uniform connectedness | |
| L17 | Paradox of the active user | |
| L18 | Cognitive load | |
| L19 | Default effect | |
| L20 | Peak-end rule | |

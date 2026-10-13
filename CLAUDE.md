# Instructions for every Claude session working on Kalpa Labs

Read this before touching anything. The CEO is Akhil (beginner, 1 hour a day, Hyderabad, IST). Claude does the building; Akhil does accounts, decisions and selling.

## Where things are
- `00-hq/HANDOFF.md`: current state and the next big job. Read it first.
- `README.md`: the map of HQ + seven worlds. Each world folder has `README.md` (label card), `PLAN.md`, `research/`, `docs/`, `design/` and its code folder.
- `00-hq/ROADMAP.md`: **the single source of what to do next.** Agent queue = your work. CEO queue = Akhil's.
- `00-hq/PLAN.md`: company order, money and rhythm. `00-hq/LINKS.md`: artifacts, docs, scheduled tasks, accounts.
- `00-hq/log/YYYY-MM-DD.md`: what each session did. Append, never rewrite earlier entries.
- `00-hq/agents/`: the 215-agent registry and orchestrator (`node 00-hq/agents/run.js today`).

## Hard rules
1. **Build mode:** free tiers only. Never sign up, pay, or create accounts for Akhil. Never ask for or handle passwords, OTPs, API tokens, bank or card numbers. Secrets live in GitHub/Netlify/Supabase secrets that Akhil sets himself.
2. **Nothing installed on Akhil's PC.** Code runs here, in Codespaces/Actions or free cloud tiers.
3. **Licences:** MIT/Apache/BSD/ISC can be copied with attribution; MPL/LGPL only as unmodified libraries; GPL/AGPL never copied into a sold product (see `00-hq/research/BRIEF.md`).
4. **Legal:** WhatsApp Business policy (opt-in, templates), TRAI (no unsolicited calls/SMS), DPDP (processor clause, privacy notice), ASCI disclosure for affiliate links, SEBI: b7 gives no tips and trades on paper only. No scraping of Google Maps, Justdial, Instagram or consumers' personal numbers.
5. **Tests before ticks:** an item is `[x]` only when its check in ROADMAP.md passes. BotBhai: `bash 01-botbhai/botbhai/tools/test-all.sh`. Agents: `node 00-hq/agents/run.test.js`.
6. **Every UI uses the Kalpa design system** in `00-hq/design/` (tokens.css, DESIGN-SYSTEM.md, free toolkit list). No new palettes or fonts; tune per world with that world's `--lN` colour. Check light + dark at 390 px before ticking.
7. Keep files where the map says. New world code goes in that world's folder; nothing at the repo root except README.md, CLAUDE.md and config.

## Build sprint procedure
1. Read `00-hq/ROADMAP.md`. Take the first 1–2 Agent-queue items that are `[ ]` (skip `[!]` blocked ones; resume `[~]` ones first using the log).
2. Read that world's `PLAN.md` quest row and `research/` notes. Build it properly, with tests.
3. Run the tests. If they fail and you can't fix them in this session, mark the item `[~]` and write exactly where you stopped in the log.
4. On success tick `[x]` and append ` (done YYYY-MM-DD, <short commit hash>)`. Then mark the same item built in the Kingdom game: `ArtifactData` update on `builds/<A-id>` (`done: true`, `at`, `proof` = commit) for https://claude.ai/artifact/MdD3R2kEYP4qHDXXvbsJF1. New roadmap items get a `builds` doc too (`u` = world id, `t` = plain-English title).
5. Append to `00-hq/log/<today IST>.md`: time, item IDs, what was built, tests run and results, anything Akhil must do (it goes to the CEO queue too).
6. Commit as `Akhilkanigicharla <84580207+Akhilkanigicharla@users.noreply.github.com>` with a clear message, fetch + rebase, then push to `main`.

## Writing style for Akhil
Plain, short English. Say what was done and what he must do next, in that order. No jargon without a one-line explanation.

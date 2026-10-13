# Kingdom control room · gamification research (13 Oct 2026)

Why: Akhil asked to make the game UI reflect the real work, and to research GitHub, papers and the web before building. This note is the evidence; the changes it drove are listed at the end.

## What the research says

| Source | Finding | What we take from it |
|---|---|---|
| Sailer & Homner (2020), *The gamification of learning: a meta-analysis*, Educational Psychology Review ([OPUS Augsburg](https://opus.bibliothek.uni-augsburg.de/opus4/frontdoor/index/index/docId/109056)) | Small positive effects: cognitive g = .49, motivational g = .36, behavioural g = .25. **Game fiction** and **social interaction** moderate behavioural effects; **competition combined with collaboration** works best. | Keep the story (worlds, NPCs). Add collaboration: the agents are your co-op team, and their work should be visible next to your quests. |
| Nunes & Drèze (2006), *The Endowed Progress Effect*, J. Consumer Research ([summary](https://en.wikipedia.org/wiki/Goal_pursuit)) | A 10-stamp car-wash card with 2 free stamps was completed by **34%** vs **19%** for a plain 8-stamp card, and faster. | Show each world's head start: the builds agents already finished count as visible progress toward that world's goal. |
| Kivetz, Urminsky & Zheng (2006), *The Goal-Gradient Hypothesis Resurrected*, J. Marketing Research | Effort speeds up as people near a goal; the illusion of progress increases retention. | Show "N builds to go" per world, so the end is always visible. |
| Amabile & Kramer (2011), *The Progress Principle* (12,000 diary entries from 238 knowledge workers) ([AMA interview](https://www.amanet.org/articles/the-worth-of-small-wins-teresa-amabile-and-steven-kramer-on-the-progress-principle/)) | Making progress in meaningful work is the strongest daily booster of motivation; small wins count. | A "Forge" feed of small wins on the Today screen: what the agents finished, with proof (commit). |
| Duolingo streak research ([Duolingo blog](https://blog.duolingo.com/duolingo-streak-research/)) | Up to 2 streak freezes raised daily active learners **+0.38%** without more skipped lessons; a 7-day streak goes with **3.6×** course completion (correlational). Some slack in goals motivates more than strict rules (UPenn/UCLA). | One **rest day per week** keeps the streak alive (Akhil has 1 hour a day; a missed day should not reset weeks of progress). |
| Hamari, Koivisto & Sarsa (2014), *Does Gamification Work?* (HICSS) | Mostly positive but context-dependent; effects fade when points are disconnected from real outcomes. | XP only for real CEO actions; agent work is shown but never gives you XP, so the score stays honest. |

## What open source does (GitHub, topic `gamification`, sorted by stars, 13 Oct 2026)

| Repo | Stars | Licence | What we learn |
|---|---|---|---|
| [HabitRPG/habitica](https://github.com/HabitRPG/habitica) | 14.2k | GPL-3.0 (ideas only, no code) | HP loss for missed dailies punishes; we use a gentle rest day instead. Party quests = co-op framing. |
| [dohsimpson/HabitTrove](https://github.com/dohsimpson/HabitTrove) | 677 | (not checked) | Self-hosted habit tracker: coins + wishlist rewards. |
| [cjmellor/level-up](https://github.com/cjmellor/level-up) | 673 | MIT | XP, levels, achievements, streaks with **streak freeze** as a first-class feature. |
| [trophyso/ui](https://github.com/trophyso/ui) | 137 | (not checked) | Gamification UI components: streak calendars, achievement cards. |
| [FMCorz/moodle-block_xp](https://github.com/FMCorz/moodle-block_xp) | 161 | GPL-3.0 | Level-up block: XP rules must reward meaningful actions only. |

No code was copied: the Kingdom page is our own, single-file HTML.

## Changes made to the Kingdom (A42)

1. **Quests match the real roadmap.** Outdated quests were rewritten (the Trading world no longer asks for a Colab backtester; the agents built the lab). New quests for the CEO queue: C01, C06–C08 (HQ), C10 + C17 (Calculators), C11 (Ledger Peaks), C12 (trading gate) and the capital rules. IDs of quests already done or started were kept, so saved progress is untouched.
2. **The Forge (co-op + small wins):** every world shows what agents built (from ROADMAP A-items, each with its commit), a gold "agents' head start" bar next to your quest bar (endowed progress), and "N builds to go" (goal gradient). The Today screen opens with the latest builds.
3. **Live from the database:** builds live in the page's `builds` collection, so any session can add a build without republishing (`ArtifactData` update on `builds/<A-id>`).
4. **Rest day:** one missed day per 7 keeps the streak (Duolingo-style freeze), shown as 🧊.
5. **Honest scoring:** XP still comes only from your own quests.

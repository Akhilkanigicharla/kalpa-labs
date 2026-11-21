> **PARKED (Akhil, 6 Nov 2026):** JobCard was picked by Claude's planning on 12 Oct as the "mobile app" stream; it was never Akhil's idea and he dropped it. Code stays here for reference; no more work or tasks. World b2 waits for Akhil's own mobile-app idea.

# 🛠️ JobCard · world b2 (Workshop Valley)

**What it is:** Voice note → job card + invoice PDF + 6-month service reminder for AC/appliance technicians.
**Status (21 Nov 2026):** JobCard parked (see top). World b2 now holds the three apps Akhil chose in C80, all private prototypes, not live: Kalpa Jyotish, Kalpa Photo Studio, Kalpa Bhasha Kids (table below).
**Price:** Free tier, ₹149/month, ₹299/month Pro.

## What's in this folder

| Label | File or folder | What it holds |
|---|---|---|
| 📋 Plan | [PLAN.md](PLAN.md) | Verdict, customer, unit economics, go-to-market, quests, kill rules, what's needed from Akhil |
| 🔎 Research | [research/](research/) | GitHub repos checked, cloned and run: adopt / learn / avoid |
| 📝 Docs | [docs/](docs/) | Decisions, requirements, sales material |
| 🎨 Design | [design/](design/) | UI design brief and mockups (filled by the build sprints) |
| 💻 Code | src/, web/, bot/ | JobCard app, my-customers PWA, WhatsApp bot (parked) |
| 🔮 App | [apps/jyotish/](apps/jyotish/) | Birth star, naming syllable, names, good days; offline PWA. Checks: [ux](apps/jyotish/design/ux-check.md) · [eng](apps/jyotish/design/eng-check.md) |
| 📷 App | [apps/photo-studio/](apps/photo-studio/) | Passport/visa photos on the phone, photos never uploaded. Checks: [ux](apps/photo-studio/design/ux-check.md) · [eng](apps/photo-studio/design/eng-check.md) |
| 🗣️ App | [apps/bhasha-kids/](apps/bhasha-kids/) | Telugu + Hindi practice for kids 4–10; words await a native-speaker check. Checks: [ux](apps/bhasha-kids/design/ux-check.md) · [eng](apps/bhasha-kids/design/eng-check.md) |

Kalpa standard for all of b2: `python3 00-hq/tools/eng_check.py b2 --md` (0 FAIL, 21 Nov 2026); each app: `npm test` (in CI).

## Research reports
- [research/a4-jobcard.md](research/a4-jobcard.md)

## Next steps
See this world's lines in [../00-hq/ROADMAP.md](../00-hq/ROADMAP.md): agent tasks run automatically in the build sprints, CEO tasks show up in the morning brief.

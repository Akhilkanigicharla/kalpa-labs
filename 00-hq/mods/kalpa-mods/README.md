# kalpa-mods (untested draft)

Our own versions of the three mods from Nate Herk's short (8 Nov 2026). Code is ours; no third-party mod is installed.

| Mod | What it does |
|---|---|
| Cache Keeper | When you reply after the prompt cache went cold, a toast says so and roughly how many tokens get re-read. Default 5 min (UNVERIFIED for Akhil's plan; change `cacheTtlSeconds`). |
| Goal Meter | After a `/goal …` prompt, the spinner shows a 10-block bar, tasks done/total and minutes. |
| Collision Guard | If another Claude session on the same computer edited a file in the last 15 min, Claude is stopped and told to ask you first. |

Safety: uses no network, no model calls, no shell, no environment variables (check with `claude plugin validate 00-hq/mods/kalpa-mods`).

**Status: written in a cloud session where mods can't load, so NOT tested.** Laptop session (roadmap A195):
1. Claude Desktop → Code tab → open kalpa-labs.
2. `claude plugin validate 00-hq/mods/kalpa-mods` (Claude runs it), fix anything it reports, add `.test.ts` tests and run `claude plugin test 00-hq/mods/kalpa-mods`.
3. Try it for one session: `claude --plugin-dir 00-hq/mods/kalpa-mods`; then keep it: `/plugin marketplace add ./00-hq/mods` and `/plugin install kalpa-mods@kalpa`.

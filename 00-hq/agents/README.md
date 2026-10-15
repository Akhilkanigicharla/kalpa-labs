# Kalpa Labs agent org

`registry.js` lists every agent in the company (228 today, each with its own validator): BotBhai's four setup teams
(sales, delivery, client success), the shared platform (developers, test agents, QA swarm, reviewers, policy, release,
ops, PM, business analysts), HQ, the Kingdom game/UI team, and lean teams for the other six worlds.

Every agent says honestly how it runs: **code** (a program in this repo), **claude** (Claude follows the spec in chats
and scheduled tasks), **human** (needs Akhil), or **planned**.

```
node 00-hq/agents/run.js check     # validate: unique ids, validators, KPIs, code files exist, full setup teams
node 00-hq/agents/run.js summary   # counts by status, world, team
node 00-hq/agents/run.js today     # today's plan: which agents run, within each world's token budget
node 00-hq/agents/run.js proposal  # current vs proposed world token split (PLAN.md §5b)
node 00-hq/agents/run.js export    # compact rows for the Kingdom's Agents tab
```

`state.json` controls spend: only launched setups get sales agents; delivery agents switch on when a setup has clients.
`world_share_approved` stays `false` until Akhil approves the PLAN.md §5b split (CEO queue C01); `today` shows a ⚑ line until then,
and once it is `true` the budgets use `PROPOSED_WORLD_SHARE`.

Since A42 (2026-10-15) the registry also lists what the build sprints made: the Build Sprint team, the roadmap task engine,
the CI quality gate, the Kalpa marketing team, a Social Team per BotBhai setup, and one engine per built world
(b2 invoice, b4 Tab Lifeboat, b5 calculators, b6 ingest + PII guard, b7 paper-trading gate). Trading Lab marketing stays off.

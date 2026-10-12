# Kalpa Labs agent org

`registry.js` lists every agent in the company (215 today, each with its own validator): BotBhai's four setup teams
(sales, delivery, client success), the shared platform (developers, test agents, QA swarm, reviewers, policy, release,
ops, PM, business analysts), HQ, the Kingdom game/UI team, and lean teams for the other six worlds.

Every agent says honestly how it runs: **code** (a program in this repo), **claude** (Claude follows the spec in chats
and scheduled tasks), **human** (needs Akhil), or **planned**.

```
node 00-hq/agents/run.js check     # validate: unique ids, validators, KPIs, code files exist, full setup teams
node 00-hq/agents/run.js summary   # counts by status, world, team
node 00-hq/agents/run.js today     # today's plan: which agents run, within each world's token budget
node 00-hq/agents/run.js export    # compact rows for the Kingdom's Agents tab
```

`state.json` controls spend: only launched setups get sales agents; delivery agents switch on when a setup has clients.

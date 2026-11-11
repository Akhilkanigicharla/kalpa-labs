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

## Autoresearch: agents that improve their own playbooks (OFF)

`autoresearch.py` follows the method of chrisworsey55/atlas-gic (MIT): the playbook is the "weights", Vigil's pass rate is the
loss. Each cycle it scores every task owner on its last 10 Vigil attempts (read from `00-hq/tasks/*.json`), moves Darwinian
weights once a day (start 1.0, range 0.3–2.5, top quarter ×1.05, bottom quarter ×0.95), judges pending experiments after 5 new
attempts (keep if the pass rate beat the baseline, else revert; no attempts in 14 days = revert), then picks the worst agent and
records **one** added playbook line as a PENDING experiment in `autoresearch-ledger.json`.
Safety: a change can only add one line on top of the playbook; the vendored playbooks and the KALPA RULES in `runner.py` are never
edited; lines that weaken rules or game Vigil (ignore/skip/override, "PASS", links, keys) are refused; one pending change per agent,
5-day cooldown; every step goes to the ledger's append-only `log`. No LLM calls, no network.

```
python3 00-hq/agents/autoresearch.py --dry-run              # what it would do (saves nothing)
python3 00-hq/agents/autoresearch.py --write                # run one cycle and save the ledger
python3 -m pytest -q 00-hq/agents/test_autoresearch.py      # 19 tests
```

**Today it is switched off:** nothing calls it, and `runner.py` does not read the ledger. To switch it on (needs Akhil's yes):
1. In `runner.py` `work()`, after building `sys_msg`, add `sys_msg = autoresearch.compose(sys_msg, task.get("owner", ""), autoresearch.load_ledger())`
   so kept and pending lines reach the agent (compose refuses output that lost any KALPA RULES line).
2. In the hourly workflow, after the runner jobs, run `python3 00-hq/agents/autoresearch.py --write` once and commit the ledger.
3. Watch `log` for a week; to undo, delete step 2 and the line from step 1 (the ledger keeps the history).

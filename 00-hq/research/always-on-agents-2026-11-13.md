# Always-on agents and workflows without n8n Cloud (13 Nov 2026)

Akhil, 13 Nov 2026: "Use alternative of n8n … open source … free tools … I need agents and workflow run all the time."

## What is broken today (checked live 13 Nov)
- The n8n connector in Claude points at the old **n8n Cloud trial** (ended 9 Nov) → every session gets "404". Our **self-hosted n8n on Render is up** (`/healthz` 200 in 0.6 s) but has 512 MB, sleeps after 15 min and its Code nodes fail (log 11 Nov 02:35).
- The **GitHub agent queue** (`agents.yml`) was red on its last 2 runs: 3 new task rows (K098–K100) had no `priority`/`owner`, so `test_runner.py` failed and the run stopped. Fixed 13 Nov (test green).
- GitHub's own cron drops most slots: last scheduled `agents` run 02:10 UTC, none in the next 5 hours.

## Options checked (provider page fetched 13 Nov + second source)
| Option | Licence | Free limit (no card) | Always on? | Verdict |
|---|---|---|---|---|
| **Cloudflare Workers cron + Workflows + Agents SDK** | Agents SDK MIT (github.com/cloudflare/agents) | Workers 100k req/day, 5 crons; Workflows on Free: 1,024 steps, 100 concurrent, 10 ms CPU/step, sleep up to 365 days (developers.cloudflare.com/workflows/reference/limits); Durable Objects (SQLite) 100k req/day, 5 GB (…/durable-objects/platform/pricing) | **Yes, never sleeps**, cron to the minute | **Best brain/timer.** Our account is linked (D1 `kalpa-live` exists, 0 Workers). Deploy needs C65 token |
| **n8n moved to Hugging Face Spaces** + Supabase Postgres | n8n Sustainable Use (internal use OK) | CPU Basic 2 vCPU, 16 GB RAM free (huggingface.co/docs/hub/spaces-overview); sleeps after 48 h idle (…/spaces-gpus); disk not persistent → DB in Supabase | Yes with a ping (cf-timer) | **Best home for our 18 n8n flows** (32× Render's RAM). Pattern used widely (tenfyzhong/n8n-free is GPL-3.0 → write our own few-line Dockerfile, don't copy) |
| **Activepieces Cloud** | MIT core (`packages/ee` commercial) | 1,000 credits/month, unlimited flows, "Free forever, no card" (activepieces.com/pricing; reset period inconsistent on the page) | Yes (their cloud) | Good visual backup; the only one safe inside products we sell |
| Windmill | own terms | Self-host CE unlimited; **cloud free limits not published** | needs a host | UNVERIFIED, skip |
| GitHub Actions 24/7 loop | – | – | – | **No.** GitHub terms forbid using Actions "as part of a serverless application" / unrelated burden (docs.github.com …additional-products). Keep Actions for batch jobs only |

## Plan (smallest steps first)
1. Done now: agent queue fixed; cf-timer also starts `agents.yml` at :20/:50 on time (A237, tested; goes live with C65).
2. A238 (needs Akhil's yes): n8n → Hugging Face Space (private repo code in `00-hq/n8n-hf/`), data in Supabase, cf-timer pings it; then Akhil reconnects the n8n connector to the new URL.
3. A239: an always-on Cloudflare agent (Workflows + Agents SDK) that reads the task queue and calls free models, so agents run even when GitHub and n8n are down.

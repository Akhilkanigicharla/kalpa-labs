# Self-hosted n8n (A146), free

Why: our n8n Cloud trial ended on 31 Oct 2026 21:45 IST and n8n Cloud has no free plan. Akhil, 3 Nov: run n8n self-hosted **and** GitHub Actions.

## The setup (all free, checked 4 Nov 2026)
| Piece | Service | Free limits that matter |
|---|---|---|
| n8n app | **Render** free web service, Docker image `n8nio/n8n:2.46.4` (pinned; = `stable` on 4 Nov) | 512 MB RAM, 0.1 CPU, 750 instance hours per month per workspace, sleeps after 15 min with no traffic (about 1 min to wake), disk is wiped on restart |
| n8n data (workflows, credentials, runs) | **Supabase** free Postgres, its own project `kalpa-n8n` | 500 MB, 2 free projects per org, paused after 1 week with no activity (n8n keeps it busy) |
| Keep-awake | GitHub Actions `n8n-keepalive.yml`, every 10 min, 06:00 to 00:30 IST | public repo, so Actions minutes are free |
| Alerts | `daily-brief.yml` checks `N8N_SELF_URL/healthz` | shows ⚠️ when n8n is down |

Why not Hugging Face Spaces: since 2026 a new Docker Space needs a paid HF plan (HF docs, Spaces hardware page and huggingface_hub guide). Oracle / Google Cloud free VMs need a card.

**Hours budget:** awake 18.5 h a day is about 575 h a month. Our LLM router on Render uses the same 750 h pool but only when called, so keep it light. If Render says hours are running out, shorten the keep-awake window in `n8n-keepalive.yml`.

**Licence:** n8n Community Edition (Sustainable Use License) is free for our own business automation. Not allowed: letting clients build workflows in it, white-labelling it, or selling it as a service. BotBhai customers never log into this n8n.

## Akhil's steps (about 25 min, once)
1. **Supabase** (supabase.com → New project): name `kalpa-n8n`, region Mumbai (ap-south-1), make a strong database password and keep it in your password manager. Then **Connect** → **Session pooler** and note the host (looks like `aws-0-ap-south-1.pooler.supabase.com`) and the user (looks like `postgres.<project-ref>`). Use the pooler, not the direct host: the direct host is IPv6 only and Render needs IPv4.
2. **Render** (dashboard.render.com → New → Web Service → **Existing image**): image `docker.io/n8nio/n8n:2.46.4`, name `kalpa-n8n`, region Singapore, instance type **Free**.
3. In that service → **Environment**, add the variables in the table below (values marked 🔒 are secrets: type them yourself, never paste them into chat).
4. Deploy. When it is live, open `https://kalpa-n8n.onrender.com`, create the n8n owner login (your email + a strong password), then **Settings → n8n API → Create API key**.
5. GitHub → kalpa-labs → Settings → Secrets and variables → Actions: secret `N8N_SELF_API_KEY` 🔒 = that API key; **variable** `N8N_SELF_URL` = `https://kalpa-n8n.onrender.com`. Then reply "n8n self-host done".

### Render environment variables
| Name | Value |
|---|---|
| `DB_TYPE` | `postgresdb` |
| `DB_POSTGRESDB_HOST` | the Session pooler host from step 1 |
| `DB_POSTGRESDB_PORT` | `5432` |
| `DB_POSTGRESDB_DATABASE` | `postgres` |
| `DB_POSTGRESDB_USER` | the pooler user `postgres.<project-ref>` |
| `DB_POSTGRESDB_PASSWORD` 🔒 | your Supabase database password |
| `DB_POSTGRESDB_SCHEMA` | `n8n` |
| `DB_POSTGRESDB_SSL_ENABLED` | `true` |
| `DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED` | `false` |
| `N8N_ENCRYPTION_KEY` 🔒 | a long random text (keep a copy: losing it makes saved credentials unreadable) |
| `N8N_PORT` | `5678` |
| `N8N_PROTOCOL` | `https` |
| `N8N_HOST` | `kalpa-n8n.onrender.com` |
| `WEBHOOK_URL` | `https://kalpa-n8n.onrender.com/` |
| `N8N_PROXY_HOPS` | `1` |
| `GENERIC_TIMEZONE` / `TZ` | `Asia/Kolkata` |
| `N8N_DIAGNOSTICS_ENABLED` | `false` |
| `N8N_PERSONALIZATION_ENABLED` | `false` |
| `EXECUTIONS_DATA_SAVE_ON_SUCCESS` | `none` |
| `EXECUTIONS_DATA_PRUNE` / `EXECUTIONS_DATA_MAX_AGE` | `true` / `72` (was 168; changed 6 Nov) |
| `NODE_OPTIONS` | `--max-old-space-size=300` (was 400; see memory fix below) |
| `N8N_RUNNERS_MAX_OLD_SPACE_SIZE` / `N8N_RUNNERS_MAX_CONCURRENCY` / `N8N_RUNNERS_AUTO_SHUTDOWN_TIMEOUT` | `96` / `2` / `15` |
| `N8N_VERSION_NOTIFICATIONS_ENABLED` / `N8N_TEMPLATES_ENABLED` | `false` / `false` |

## Memory fix (6 Nov 2026, read from the Render connector)
- Render events: `server_failed` with `oomKilled` (512Mi limit) on 5 Nov 06:54 UTC.
- Render metrics: memory sat at 430–440 MB of 512 MB all day; 6 Nov 05:00 UTC hit 512.6 MB, then no data until 12:00 UTC (down most of the IST working day).
- Cause: n8n 2.x main heap (400 MB cap) plus the built-in task runner process plus Node overhead filled the 512 MB box.
- Fix applied through the Render API: main heap 300 MB, runner heap 96 MB, runner stops after 15 s idle, fewer extras. Deploy dep-dbn09kh5efls738oijrg live 16:50 UTC; /healthz 200.
- Sleeping after 15 min idle is separate and handled by the keep-awake ping (A165/A167).

## After that (Claude, via the n8n API)
1. Re-create the 4 workflows (Task Runner, CEO update replaced by `daily-brief.yml`, World Keeper, Read Repo File) on free models (OpenRouter, Groq, NVIDIA, Hugging Face).
2. Akhil re-enters the model keys once inside n8n → Credentials (OpenRouter, Groq, NVIDIA, Hugging Face, GitHub, Telegram). n8n locks keys to the instance that saved them, so cloud keys cannot be copied over.
3. Web search: the cloud trial's built-in Brave credit is gone; pick a free search API after checking it live.

Risks: 512 MB is tight for n8n; heavy AI agent runs may restart it. GitHub Actions (A144) stays the primary runner; this n8n is the editor and backup.

## Gotchas found (4 Nov 2026)
- Render's firewall blocks API requests whose JSON has a key containing the word `prompts` (HTTP 403 "Blocked" page). Never name an n8n node "...prompts".
- Credentials are created from GitHub secrets by `n8n-sync.yml` (input create_credentials=yes). Two runs at once on 4 Nov made duplicates of "Kalpa Telegram" and "Kalpa Groq header"; the newest is used, the older copy can be deleted in n8n → Credentials.

## What happened to each old n8n Cloud workflow (5 Nov 2026)
The cloud instance is locked since the trial ended (its API and our connector both fail), and n8n never exports saved key values, so nothing could be copied directly. Every active workflow already has a working replacement:

| Old n8n Cloud workflow | Now |
|---|---|
| Kalpa Task Runner (agents do KL Tasks) | GitHub `agents.yml` + `00-hq/agents/runner.py`, 8 worlds in parallel, hourly |
| Kalpa CEO Daily Update (Telegram) | GitHub `daily-brief.yml`, 9 PM IST, alerts first |
| Kalpa Site Chat (Kalpa Bhai) + Save Site Lead | Netlify function `00-hq/site/netlify/functions/chat.mjs` + Netlify Forms |
| World Keeper (daily company health) | `daily-brief.yml` checks (site, chat, n8n, failing Actions) |
| Read Kalpa Repo File (agent tool) | runner reads repo files directly |
| Councils (daily) | self-hosted n8n "Kalpa Morning Councils (all worlds)" 07:30 IST |
| Revenue Workforce, HQ Revenue Rollup, Smart Router | were switched off; not rebuilt |

Keys in the self-hosted n8n come from GitHub secrets via `n8n-sync.yml`: Kalpa Groq, Kalpa OpenRouter, Kalpa Telegram, and header versions for HTTP nodes. Older duplicates are deleted automatically.
If Akhil can still open app.n8n.cloud, he can download any workflow (⋯ → Download) and send the JSON; it goes into `workflows/` and syncs.

## Why it keeps going down (checked 6 Nov 2026)
- **The keep-awake job barely ran:** set for every 10 min, but only **8 runs landed in 3 days** (4–6 Nov, `gh run list`). GitHub runs scheduled jobs "best effort" and delays or drops them at busy times (GitHub docs, quoted in community threads; crontap and runhooks guides). So Render put n8n to sleep after 15 min idle most of the day.
- **Waking often failed:** 4 of those 8 pings got **no answer within 90 s (HTTP 000)**. n8n on 0.1 CPU / 512 MB boots slowly and sometimes not at all. A live check at 18:55 IST got HTTP 200 in 1.3 s, so it works while it is awake.
- Fix in repo (6 Nov): keepalive moved to odd minutes (7, 23, 41, 53), two tries of 150 s each. This is only a backup.

## Options (free, checked 6 Nov 2026)
| Option | Verdict | Why |
|---|---|---|
| **External pinger** on `/healthz` every 5 min: cron-job.org (free, down to every 1 min) or UptimeRobot free (50 monitors, 5 min; its help page says commercial use is allowed) | **Do now, 5 min for Akhil** | Reliable timer, so Render never sleeps inside the window. Keep the 06:00–00:30 window: 24/7 = 744 h and would eat the 750 h pool the LLM router also uses |
| **GitHub Actions as the engine** (A144), n8n as editor/backup only | **Keep**, main path | Jobs run at their time on Actions; nothing depends on Render being awake. Optional to test: export a workflow and run it headless with the n8n CLI (`n8n execute --file`) inside Actions |
| Hugging Face Docker Space | **No** for new Spaces | HF docs now: "Gradio and Docker Spaces run on compute and require a paid plan to create" (PRO); forum threads Jul 2026 agree |
| Koyeb free | No | Same 0.1 vCPU / 512 MB, sleeps after 1 h, and since Feb 2026 a card hold is required (Koyeb FAQ; snapdeploy comparison) |
| Oracle Cloud Always Free VM | Best power, **Akhil's call** | Needs a card for sign-up verification (breaks our "no card" rule unless Akhil chooses it). Specs not rechecked today |
| **Activepieces** (MIT core, n8n alternative) | Later, if we sell automation inside products | MIT licence is cleaner than n8n's Sustainable Use licence for embedding; but it needs Postgres + Redis, so it would not fit Render free either |
| Node-RED (Apache-2.0) | Only for tiny flows | Very light, but far fewer AI/agent nodes |
| **Google Opal** (Google Labs) | Use for small AI mini-apps, not as our n8n | Free experimental no-code builder for Gemini mini-apps; no self-hosting and no code export (ppc.land; technource.com). Not a replacement for scheduled backend jobs |
| **Google Workspace Studio** (ex-Workspace Flows) | No, for now | Included only with paid Google Workspace business plans; free Gmail accounts don't get it. Only Workspace events can start a flow; limits of about 25 flows per person (aurora tools page; superdupr.com, citing Google's help page) |

## Keep-awake now running (6 Nov 2026, 21:30 IST)
- n8n workflow **"Kalpa Keep Awake"** (`workflows/keep-awake.json`, synced and activated by `n8n-sync.yml`, runs 42248286845 + 42248289945) pings its own public URL every 5 min from 06:00 to 00:30 IST. Requests go through Render's front door, so they count as traffic and n8n should not fall asleep while it is awake. Successful runs are not saved (no DB growth).
- It cannot wake n8n after the night sleep: the GitHub keepalive (odd minutes) does the morning wake-up, even if it lands late.
- Not used: Supabase pg_cron (the connected Supabase login shows no projects), Netlify scheduled functions (using up the free credits would pause every live Kalpa site), a looping GitHub Actions job (GitHub's terms don't allow Actions as an always-on service).
- Proof to check on 7 Nov: `n8n-keepalive` runs should show HTTP 200 in about a second, and no `000`.

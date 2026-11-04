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
| `EXECUTIONS_DATA_PRUNE` / `EXECUTIONS_DATA_MAX_AGE` | `true` / `168` (keeps 500 MB free tier small) |
| `NODE_OPTIONS` | `--max-old-space-size=400` (stays under 512 MB) |

## After that (Claude, via the n8n API)
1. Re-create the 4 workflows (Task Runner, CEO update replaced by `daily-brief.yml`, World Keeper, Read Repo File) on free models (OpenRouter, Groq, NVIDIA, Hugging Face).
2. Akhil re-enters the model keys once inside n8n → Credentials (OpenRouter, Groq, NVIDIA, Hugging Face, GitHub, Telegram). n8n locks keys to the instance that saved them, so cloud keys cannot be copied over.
3. Web search: the cloud trial's built-in Brave credit is gone; pick a free search API after checking it live.

Risks: 512 MB is tight for n8n; heavy AI agent runs may restart it. GitHub Actions (A144) stays the primary runner; this n8n is the editor and backup.

## Gotchas found (4 Nov 2026)
- Render's firewall blocks API requests whose JSON has a key containing the word `prompts` (HTTP 403 "Blocked" page). Never name an n8n node "...prompts".
- Credentials are created from GitHub secrets by `n8n-sync.yml` (input create_credentials=yes). Two runs at once on 4 Nov made duplicates of "Kalpa Telegram" and "Kalpa Groq header"; the newest is used, the older copy can be deleted in n8n → Credentials.

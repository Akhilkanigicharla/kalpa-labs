# Kalpa engineering checklist (107 practices)

Akhil shared a reel of ~100 practices "vibe coders don't know" and said: apply it to all of Kalpa Labs (12 Nov 2026). This is that list, sized for a one-person company on free tiers. Every practice from the reel is here; none dropped.

**How to use it**
- Building or changing anything in a world: read the rows for your group, follow the **Kalpa rule**.
- **Check** says how we know it holds:
  - **AUTO `RULE-ID`**: `python3 00-hq/quality/eng_audit.py` finds it (see `report.md`). In CI, CRITICAL fails the build; the rest is the fix list.
  - **CI `job`**: an existing job in `.github/workflows/quality.yml` (or the named workflow) tests it.
  - **MANUAL (when)**: a person or Claude checks it at that moment (a new endpoint, before a world goes live, monthly).
- A rule can be waived only on the line, with a reason: `# eng-audit: ok <reason>`.
- **Worlds:** HQ = 00-hq (+ `.github`), b1 = 01-botbhai, b2 = 02-jobcard (incl. `apps/`), b3 = 03-kits, b4 = 04-extensions, b5 = 05-deals, b6 = 06-finops, b7 = 07-trading. "Server worlds" = the ones with server code: b1, b2, b5, b6, HQ (site chat, LLM router).
- Status on 12 Nov 2026 is in `report.md`; facts below come from the repo as it is today.

## Hosting map (today vs the Cloudflare free option)

Kalpa does **not** migrate anything because of this table. It lists the Cloudflare free stack as an option next to what we use today. Before choosing any of it, check Cloudflare's own pricing page today plus a second source (CLAUDE.md rule 8); free limits change.

| Need | Kalpa today (seen in the repo) | Cloudflare free option |
|---|---|---|
| Static sites + CDN | Netlify (`01-botbhai/botbhai`, `02-jobcard`, `00-hq/site` each have `netlify.toml`); GitHub Pages for the b4 policy site (`extension-site.yml`); b5 is an Astro site with a `public/_headers` file | Cloudflare Pages (global CDN built in) |
| Serverless functions / cron | Netlify Functions (`core/functions`, `bot/functions`, `netlify/functions`) incl. scheduled ones (`reminders` hourly, `dayclose`, `adsbot`); b5 `functions/api` (Pages-style handlers); GitHub Actions cron workflows | Cloudflare Workers (+ Cron Triggers), Pages Functions |
| Database | Supabase Postgres (b1, b2, b6 schemas with RLS) | D1 (SQLite). Not a drop-in for Postgres + RLS |
| File storage | Supabase / repo artifacts / Actions artifacts | R2 (object storage) |
| Backups | None automated yet (b1 `PLAN.md`: Supabase free has no backups; nightly dump via Actions planned as P1-M2-07) | R2 as a backup target for an Actions `pg_dump` |
| DNS + HTTPS | Host-managed TLS on Netlify / GitHub Pages / Render; no custom domain config in the repo | Cloudflare DNS + Universal SSL |
| Containers / long-running apps | Render free (LLM router, `00-hq/llm-router/Dockerfile`, per `00-hq/LINKS.md`); `01-botbhai/botbhai/voice/Dockerfile` | Workers (no Docker); keep Render/HF Spaces for containers |
| AI models | Free OpenRouter / Groq / Gemini via n8n and the LLM router | Workers AI (free daily allowance; verify) |
| Bot check | Cloudflare Turnstile already used by b1 bookings (`_lib.js` `turnstileOk`) | same |

## 1. Security (attacks and secrets)

| # | Practice | What it means | Kalpa rule | Worlds | Check |
|---|---|---|---|---|---|
| 1 | Rate Limiting | Cap how often one person or IP can call something. | Every public endpoint that costs money or writes data has a limit. b1 uses a database sliding window (`rate_hit` RPC, works across instances); the HQ site chat has a per-instance memory limit (fine for a demo, not for paid traffic). | b1 b2 b5 b6 HQ | MANUAL (each new public endpoint) |
| 2 | Environment Variables | Settings and keys live outside the code. | Read config from env; every world that reads env vars keeps a `.env.example` with dummy values and where to set the real one. | all | AUTO `ENV-EXAMPLE`, `ENV-UNDOCUMENTED` |
| 3 | Secrets Management | Keys are stored in a vault, never in the repo. | Secrets only in GitHub / Netlify / Supabase / Render secrets that Akhil sets (CLAUDE.md rule 1). Nothing secret in code, logs or chat. | all | CI `hygiene` (gitleaks, whole history) + AUTO `SECRET-*` |
| 4 | Secret Rotation | Change keys on a schedule and after any leak. | Rotate at once if a key leaks; otherwise yearly or when someone loses access. Akhil rotates (accounts are his); Claude lists which keys, where. | all | MANUAL (on leak; yearly) |
| 5 | Input Validation | Reject bad input at the edge (type, length, format). | Every handler checks types, lengths and allowed values before use; phone numbers normalised (b2 `normPhone`). | server worlds | MANUAL (new endpoint) + tests |
| 6 | Data Validation on the Server | The server re-checks everything; the browser check is only for comfort. | Never trust the page or app: prices, totals, quotas and roles are computed or checked on the server or in SQL (b2 invoice totals, b1 billing). | b1 b2 b5 b6 | MANUAL (new endpoint) + tests |
| 7 | SQL Injection | User text changes the SQL. | No SQL built from strings; use parameters, PostgREST filters with `encodeURIComponent` (`enc`), or SQL functions. | b1 b2 b6 | AUTO `SQL-STRING` |
| 8 | XSS | User text runs as script in a page. | Put data in with `textContent`, or wrap every value in `esc(...)` before `innerHTML`. No `eval`/`new Function` outside tests. | all with UI | AUTO `XSS-HTML-SINK`, `CODE-EVAL`; CI `design` (vibecheck) |
| 9 | CSRF | Another site makes the user's browser send a request. | We use bearer tokens and signed webhooks, not cookie logins, so classic CSRF does not apply today. If a cookie login is ever added: `SameSite=Lax` + a CSRF token on writes. | b1 b2 b5 | AUTO `COOKIE-FLAGS`; MANUAL (if cookie login added) |
| 10 | Dependency Vulnerabilities | Libraries with known holes. | Lockfiles committed (`package-lock.json`, `pnpm-lock.yaml`); pip versions pinned in CI; check advisories monthly; add Dependabot (free). | b2 b4 b5 HQ | AUTO `DEPS-BOT`; MANUAL (monthly `npm audit` / `pip-audit`) |
| 11 | Content Security Policy | A header that tells the browser which scripts may run. | Every site sends a CSP; start strict (`default-src 'self'`) and allow only named hosts. | b1 b2 b5 HQ (b4 site on GitHub Pages: use a `<meta>` CSP) | AUTO `HDR-CSP` |
| 12 | Security Headers | Extra browser safety switches. | Every site sends HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`. | b1 b2 b5 HQ | AUTO `HDR-HSTS`, `HDR-NOSNIFF`, `HDR-REFERRER` |
| 13 | Clickjacking | Our page hidden inside another site's frame. | `frame-ancestors 'none'` in CSP or `X-Frame-Options: DENY` (unless a page is meant to be embedded, like the b1 chat widget, then list the allowed sites). | b1 b2 b5 HQ | AUTO `HDR-FRAME` |
| 14 | SSRF | The server is tricked into calling an internal URL. | Server code calls only fixed hosts (Supabase, Meta Graph, Groq, Telegram). Never fetch a URL taken from user input; if needed, allow-list hosts. b1 already fetches Meta media URLs only after signature checks. | b1 b2 b6 HQ | MANUAL (any code that fetches a URL from input) |
| 15 | Open Redirects | `?next=evil.com` sends users to a scam site. | Redirect only to our own paths or an allow-list. | b1 b2 b5 | AUTO `OPEN-REDIRECT` |
| 16 | Path Traversal | `../../etc/passwd` reads files it should not. | Never build a file path from request input; allow-list file names. | server worlds | AUTO `PATH-TRAVERSAL` |
| 17 | Command Injection | User text runs as a shell command. | `subprocess.run([...])` / `execFile` with an argument list; never `shell=True` with built strings. Today all subprocess calls use lists. | all | AUTO `CMD-INJECTION` (CRITICAL if built string + shell) |
| 18 | Mass Assignment | A user sends `"role":"admin"` and the server saves it. | Copy only named fields from a request into a row; RLS `with check` blocks role/owner columns. | b1 b2 b6 | MANUAL (new write endpoint) |
| 19 | File Upload Security | Uploads that are huge, executable or fake images. | Check size and type on the server, store outside the web root with random names, never run uploads. Today uploads are WhatsApp voice notes (fetched from Meta) and on-device photos (b2 photo-studio stays on the phone). | b1 b2 | MANUAL (any new upload) |
| 20 | HTTPS/TLS | Encrypted connection. | HTTPS only; hosts give free certificates (see Hosting map). Never switch off certificate checks. | all | AUTO `TLS-OFF`, `PLAIN-HTTP`, `HDR-HSTS` |
| 21 | Encryption in Transit | Data encrypted while moving. | Same as #20, plus Postgres connections over TLS (Supabase default). | all | AUTO `PLAIN-HTTP`, `TLS-OFF` |
| 22 | Encryption at Rest | Data encrypted on disk. | Supabase/Netlify/GitHub encrypt disks (provider feature; check their page before telling a customer). Extra-sensitive fields (tokens) encrypted with `pgcrypto` (enabled in b1 and b2 schemas). | b1 b2 b6 | MANUAL (new sensitive column) |
| 23 | Hashing vs Encryption | Hash = one way (passwords); encryption = two way (things you must read back). | Passwords and API keys are hashed, never encrypted or stored plain; tokens we must reuse (e.g. a client's WhatsApp token) are encrypted. | b1 b2 b6 | MANUAL (new credential field) |
| 24 | Salting | Random extra data per password before hashing. | Use bcrypt/argon2 or Supabase Auth (salts for us); never plain SHA/MD5 for passwords. | b1 b2 b6 | MANUAL (new credential field) |
| 25 | Penetration Testing | Someone attacks your app on purpose to find holes. | Before each world goes live: run the eng audit, OWASP ZAP baseline (free) against the preview URL, and the b6 prompt-injection test list for chatbots. Yearly after. | b1 b2 b5 b6 | MANUAL (before go-live, yearly) |

## 2. Login & access

| # | Practice | What it means | Kalpa rule | Worlds | Check |
|---|---|---|---|---|---|
| 26 | Authentication | Proving who someone is. | Use Supabase Auth (b2 PWA: phone OTP) or signed per-client tokens (b1 `client_token` RPC). Never roll our own password system. | b1 b2 b6 | MANUAL (new login) |
| 27 | Authorization | Deciding what they may do. | Every read/write is checked on the server or by RLS, never only by hiding a button. | b1 b2 b6 | CI `jobcard`/`botbhai` (schema + RLS tests) |
| 28 | Session Management | Keeping a user logged in safely. | Short-lived access tokens with refresh (Supabase default); sign-out clears local storage. | b2 b6 | MANUAL (new login) |
| 29 | Two-Factor Authentication | A second proof (OTP app). | Akhil turns on 2FA for GitHub, Netlify, Supabase, Render, Meta, Google, broker (his accounts). Customer 2FA: not needed until we hold money or health data. | HQ, b7 (broker) | MANUAL (Akhil, once; recheck quarterly) |
| 30 | Brute Force Protection | Stop endless guessing of codes/passwords. | Rate-limit OTP and login tries (Supabase Auth limits OTP; b1 `rate_hit`); add Turnstile on public forms (b1 bookings use it). | b1 b2 b6 | MANUAL (new login/form) |
| 31 | Account Lockout | Pause an account after many failed tries. | Prefer slow-down (rate limit + cooldown) over hard lockout, so attackers cannot lock real users out. | b1 b2 b6 | MANUAL (new login) |
| 32 | Password Reset Flows | Safe "forgot password". | We avoid passwords (OTP / magic link). If ever added: one-time, 15-60 min expiry, same reply whether the email exists or not. | b2 b6 | MANUAL (if passwords added) |
| 33 | Magic Links | Login by a one-time link sent by email. | Supabase Auth magic links / OTP with short expiry; links single-use. | b2 b6 | MANUAL (new login) |
| 34 | Passkeys | Login with the phone's fingerprint/face. | Not needed until a paid dashboard has many users; Supabase/WebAuthn when it does. | b2 b6 | MANUAL (when a dashboard passes ~100 users) |
| 35 | SSO | One login across many apps (Google, company login). | Not needed until b6 sells to companies that ask for it; "Sign in with Google" via Supabase is the free first step. | b6 | MANUAL (when a customer asks) |
| 36 | Role-Based Access Control | Roles (owner, staff) decide rights. | Roles live in tables (b1 `members`, b6 `tenant_member`) and RLS policies read them. | b1 b2 b6 | CI (schema + RLS tests) |
| 37 | Row-Level Security | The database itself hides rows that are not yours. | Every table in an exposed Supabase schema has `enable row level security` plus policies; `SECURITY DEFINER` functions fix `search_path`; views use `security_invoker`. All 3 schemas pass today. | b1 b2 b6 | AUTO `RLS-MISSING` (CRITICAL), `DEFINER-SEARCH-PATH`, `VIEW-DEFINER`; CI schema tests |
| 38 | IDOR | Changing `?id=123` to `124` shows someone else's data. | Never trust an id from the request alone: RLS or a server check ties every row to the caller (b2 finds the technician by his own WhatsApp number). | b1 b2 b6 | MANUAL (new endpoint) + RLS tests |
| 39 | Principle of Least Privilege | Each key/job gets only the rights it needs. | Browser gets the anon key only; `service_role` stays in server functions. Workflows declare `permissions:` (quality.yml: `contents: read`). | all | AUTO `CI-PERMISSIONS`, `SECRET-supabase-service-role` |
| 40 | API Keys | Keys that let programs call our API. | Show once, store only a hash (b6 `api_key` table), allow revoke, never put in URLs or logs. | b6 HQ (LLM router) | AUTO `LOG-SECRET`; MANUAL (new key type) |
| 41 | Token Expiration and Refresh | Tokens die after a while and are renewed. | Access tokens short (Supabase ~1 h default), refresh tokens rotate; per-client tokens can be revoked. | b1 b2 b6 | MANUAL (new token type) |
| 42 | Cookie Flags (HttpOnly, Secure, SameSite) | Settings that stop scripts and other sites from stealing cookies. | Any cookie we set: `HttpOnly; Secure; SameSite=Lax`. No login tokens in `document.cookie`. None are set today. | b1 b2 b5 | AUTO `COOKIE-FLAGS`, `COOKIE-JS` |
| 43 | Audit Logs | A record of who did what, when. | Money, refunds, role changes and data exports write an audit row (append-only). b7 already logs risk breaches to a file. | b1 b2 b6 b7 | MANUAL (new money/admin action) |

## 3. Data

| # | Practice | What it means | Kalpa rule | Worlds | Check |
|---|---|---|---|---|---|
| 44 | Database Indexing | Indexes make lookups fast. | Index every column used in `where`/`join` by hot paths (client id, phone, date). Check with `explain` when a query passes ~100 ms. | b1 b2 b6 | MANUAL (new query; Supabase advisor monthly) |
| 45 | Database Migrations | Schema changes as versioned files. | Change schema only by files in git (b6 `migrations/0001_…`, b1/b2 `schema.sql` written idempotently with `if not exists`), tested in CI on Postgres 16. | b1 b2 b6 | CI `botbhai`, `jobcard` (schema tests) |
| 46 | Backups | Copies you can restore. | Supabase free has no backups (b1 `PLAN.md`). Before the first paying customer: nightly encrypted `pg_dump` from Actions (P1-M2-07) to a private store (option: R2, see Hosting map). | b1 b2 b6 | MANUAL (before first paid customer; restore drill monthly) |
| 47 | Disaster Recovery | The plan to get back after a big failure. | One page per server world: where backups are, how to restore, who does what, target "back in 1 day". Code is safe in GitHub. | b1 b2 b6 b7 | MANUAL (before go-live; drill twice a year) |
| 48 | Database Normalization | Store each fact once. | Normal tables for core data; copy values only on purpose (an invoice keeps its own prices so old bills never change). | b1 b2 b6 | MANUAL (schema review) |
| 49 | Soft Deletes | Mark deleted instead of erasing. | Use `deleted_at` for customer-facing records people may want back; hard delete when the law requires (DPDP erasure). No `deleted_at` columns exist yet. | b1 b2 b6 | MANUAL (new delete feature) |
| 50 | Connection Pooling | Reuse database connections. | Serverless functions talk to Supabase over HTTP (PostgREST), so no pool is needed. Direct Postgres from a server: use Supabase's pooler port. | b1 b2 b6 | MANUAL (any direct Postgres client) |
| 51 | Read Replicas | Copies of the DB just for reading. | Not needed until the database is the slow part at real load (paid Supabase feature). | b1 b2 b6 | MANUAL (when p95 query time hurts) |
| 52 | Race Conditions | Two requests at once corrupt data (double booking). | Do check-then-write inside one SQL function with a lock or unique constraint (b1 uses `pg_advisory_xact_lock` for slot booking and rate hits; invoice numbers come from a counter table). | b1 b2 b6 b7 | MANUAL (new shared-resource write) + tests |
| 53 | Time Zones | Same moment, different clocks. | Store UTC (`timestamptz`); show IST (`Asia/Kolkata`); Python uses aware datetimes; schedules state their UTC time (b1 `dayclose` = `30 15 * * *` = 9 PM IST). | all | AUTO `NAIVE-DATETIME` |
| 54 | Character Encoding | Bytes to letters (UTF-8). | UTF-8 everywhere; Python always passes `encoding="utf-8"` (Telugu/Hindi text breaks on Windows otherwise). | all | AUTO `TEXT-ENCODING` |

## 4. Reliability

| # | Practice | What it means | Kalpa rule | Worlds | Check |
|---|---|---|---|---|---|
| 55 | Timeouts | Give up on a slow call instead of hanging. | Every outgoing call in server code has a timeout shorter than the host's function limit: `AbortSignal.timeout(ms)` in JS, `timeout=` in Python. | all | AUTO `NET-TIMEOUT-JS`, `NET-TIMEOUT-PY` |
| 56 | Exponential Backoff | Retry after 1 s, 2 s, 4 s… not in a tight loop. | Retry only safe/idempotent calls, max 3 tries with backoff + jitter; respect `Retry-After` from APIs (Groq, Meta). | b1 b2 b5 b6 HQ | MANUAL (new external call) |
| 57 | Idempotency | Doing it twice has the same effect as once. | Webhooks and payments are de-duplicated by their id (b1 `processed`, b2 `wa_processed`); payment handlers ignore repeats. | b1 b2 b5 | MANUAL (new webhook) + tests |
| 58 | Circuit Breakers | Stop calling a service that keeps failing. | Use model fallback instead: b1 `fallback.js` and the LLM router switch to the next free model. Full circuit breakers not needed at our volume. | b1 HQ | CI `botbhai` (fallback tests) |
| 59 | Error Handling | Expect failures and handle them. | Catch at the edge, show the user a plain message (in their language), log the status/code only, never customer text (b1 `_lib.js` does this). | all | MANUAL (code review) + tests |
| 60 | HTTP Status Codes | 200 ok, 400 bad input, 401 not logged in, 403 not allowed, 404, 429 too many, 500 our fault. | Return the right code; webhooks return 2xx fast after the signature check, 401 on a bad signature (b1, b2 do). | server worlds | MANUAL (new endpoint) + tests |
| 61 | Webhooks | Another service calls us when something happens. | Verify the signature over the raw body with a constant-time compare (b1/b2 Meta `X-Hub-Signature-256`, b5 Razorpay), fail closed without the secret, de-duplicate, reply fast. | b1 b2 b5 | MANUAL (new webhook) + tests (`webhook.test.js`, `api.test.ts`) |
| 62 | Background Jobs | Slow work done outside the request. | Use scheduled functions or GitHub Actions; the user never waits for AI or video work in a request. | b1 b2 HQ | MANUAL (new slow task) |
| 63 | Cron Jobs | Jobs that run on a timetable. | Netlify scheduled functions (`reminders`, `dayclose`, `adsbot`) and Actions `schedule:` workflows; each job has a timeout and is safe to run twice. | b1 b2 b5 HQ | AUTO `CI-TIMEOUT` |
| 64 | Message Queues | A waiting line between producer and worker. | Not needed now; the "KL Tasks" table in n8n is our queue (CLAUDE.md rule 11). Add a real queue only when jobs are lost or pile up. | HQ | MANUAL (when jobs pile up) |
| 65 | Health Checks | An URL that says "I'm alive". | Every long-running server exposes a health route (b1 voice agent has `/health`; check the LLM router on Render); n8n keepalive/sync workflows already ping n8n. | b1 HQ | MANUAL (new server) |
| 66 | Graceful Shutdown | Finish current work before stopping. | Long-running servers (FastAPI voice agent, router) finish open calls on SIGTERM; serverless needs nothing extra. | b1 HQ | MANUAL (new server) |
| 67 | Concurrency | Many things at once. | Protect shared data with database locks or unique keys, not in-memory flags (serverless instances do not share memory). | b1 b2 b6 b7 | MANUAL (code review) |
| 68 | Async/Await | Waiting for slow work without blocking. | Always `await` promises (no fire-and-forget unless commented why); in Python async code use async clients (b1 voice uses `aiohttp`). | all | MANUAL (code review); TypeScript lint in b4 |
| 69 | Memory Leaks | Memory that grows until a crash. | No unbounded module-level caches in servers (the HQ chat `hits` map is capped: cleared above 5,000 IPs); restart-safe design. | b1 HQ | MANUAL (new long-running server) |

## 5. Watching & alerts

| # | Practice | What it means | Kalpa rule | Worlds | Check |
|---|---|---|---|---|---|
| 70 | Logging | Writing down what happened. | Log events and error codes, never secrets or customer messages/phone numbers (DPDP). | all | AUTO `LOG-SECRET`; MANUAL (code review) |
| 71 | Structured Logging | Logs as key=value / JSON, easy to search. | One line per event with `event`, `world`, `status`, `ms`. Use when a world has paying customers. | b1 b2 b6 | MANUAL (before go-live) |
| 72 | Monitoring | Watching numbers over time. | Host dashboards (Netlify, Supabase, Render) plus the World Keeper daily check (`SERVICE-DESK.md`: CI for every world, site uptime, leads). | all | MANUAL (daily, World Keeper) |
| 73 | Alerting | Being told when something breaks. | Failures reach a person: b1 `alertOwner` messages the salon owner, b6 `alerts.py` posts spend spikes to the customer's Slack webhook, the HQ daily brief reaches Akhil; one alert per problem, not spam. | b1 b6 HQ | MANUAL (new failure path) |
| 74 | Distributed Tracing | Following one request across many services. | Not needed until one request crosses 3+ of our own services; pass a request id in logs meanwhile. | HQ | MANUAL (when needed) |
| 75 | Error Tracking | Collect crashes in one place. | Free tier error tracker only if host logs are not enough; until then Netlify/Render logs + Telegram alert. | b1 b2 b5 b6 | MANUAL (before go-live) |
| 76 | Uptime Monitoring | Ping the site every few minutes from outside. | Every live public URL is in the World Keeper uptime list; a free external pinger is an option. | all live sites | MANUAL (each go-live) |
| 77 | Cost Monitoring | Watching spend. | Free tiers only; watch usage pages monthly; b6 Ledger Peaks prices AI usage; never add a card (CLAUDE.md rule 1). | all | MANUAL (monthly) |
| 78 | Debugging | Finding the cause of a bug. | Reproduce with a failing test first (Superpowers `systematic-debugging`), then fix. | all | MANUAL (each bug) |
| 79 | Profiling | Measuring where time/memory goes. | Profile only when something is slow (`node --prof`, `cProfile`, Lighthouse for pages). | all | MANUAL (when slow) |
| 80 | Reading Error Messages | Read the whole error and stack before guessing. | Quote the exact error in the log and fix the first real cause. | all | MANUAL (each bug) |

## 6. Shipping

| # | Practice | What it means | Kalpa rule | Worlds | Check |
|---|---|---|---|---|---|
| 81 | Automated Testing | Code that checks code. | Every world has tests and every test runs in CI (CLAUDE.md rule 5, "tests before ticks"). | all | AUTO `TESTS-MISSING`, `TESTS-NOT-IN-CI`; CI all jobs |
| 82 | Unit vs Integration vs E2E Tests | Small piece / pieces together / whole app like a user. | Money paths get all three: unit (b1 `core/*.test.js`), integration (schema + RLS on Postgres), E2E (Playwright at 390 px: b1, b2, b4). | all | CI `botbhai`, `jobcard`, `tab-lifeboat`, `python-worlds`, `kits` |
| 83 | CI/CD | Robots test (and later deploy) every push. | `quality.yml` gates every push/PR; deploys only after Akhil's "go" (CLAUDE.md rule 9). Every job has `timeout-minutes`; actions are first-party or pinned to a SHA. | all | CI + AUTO `CI-TIMEOUT`, `CI-UNPINNED-ACTION`, `CI-SCRIPT-INJECTION`, `CI-ECHO-SECRET`, `CI-PR-TARGET`; CI `hygiene` (actionlint) |
| 84 | Code Review | Another pair of eyes before merge. | Claude reviews every diff with `ponytail-review` before ticking; the CI gate is the second reviewer. | all | MANUAL (every item) |
| 85 | Branching Strategies | How branches are used. | Small commits straight to `main` after rebase, two sessions claim items first (`00-hq/TEAM.md`); feature branches only for risky changes. | all | MANUAL |
| 86 | Semantic Versioning | MAJOR.MINOR.PATCH version numbers. | Versions for things customers install: b4 extension, b2 app builds, b3 kits. Breaking change = new MAJOR. | b2 b3 b4 | MANUAL (each release) |
| 87 | API Versioning | Old clients keep working when the API changes. | Not needed until outsiders call our API; then `/v1/` (the LLM router already serves `/v1`) and b6 ingest API. | b6 HQ | MANUAL (first external API customer) |
| 88 | API Documentation | How to call our API. | A README per API (b6 `src/api/README.md` exists); OpenAPI file when a customer integrates. | b6 HQ | MANUAL (first external API customer) |
| 89 | Feature Flags | Switch a feature on/off without new code. | Env switches are our flags (e.g. b1 `BOTBHAI_DEMO`, b5 `DEALS_LIVE`); default off for risky things. | b1 b5 | AUTO `ENV-EXAMPLE` (flags must be listed) |
| 90 | Staging Environments | A copy of production to test on. | Netlify deploy previews + local Postgres in CI are our staging; never test on a customer's live data. | b1 b2 b5 HQ | MANUAL (before go-live) |
| 91 | Infrastructure as Code | Servers and settings described in files. | Host settings live in git (`netlify.toml`, workflows, Dockerfiles, `schema.sql`); click-only settings get written down in the world README. | all | MANUAL (each new host setting) |
| 92 | Docker | Package an app with everything it needs. | Only for long-running servers (voice agent, LLM router); serverless and static sites need none. | b1 HQ | MANUAL |
| 93 | Technical Debt | Shortcuts that cost later. | Track in `ROADMAP.md` as items, not TODOs scattered in code; fix the audit's HIGH list first. | all | MANUAL (monthly) + AUTO report |
| 94 | Reading Documentation | Check the official docs before guessing. | Provider's own page fetched today + a second source (CLAUDE.md rule 8, `00-hq/audit/README.md`). | all | MANUAL (each claim) |

## 7. Speed & scale

| # | Practice | What it means | Kalpa rule | Worlds | Check |
|---|---|---|---|---|---|
| 95 | Load Balancing | Spread traffic across many servers. | Not needed: Netlify/Pages/Workers spread traffic for us. Revisit only if a self-run server (Render) is the bottleneck. | all | MANUAL (when a server maxes out) |
| 96 | Horizontal vs Vertical Scaling | More machines vs a bigger machine. | Serverless scales out by itself; for Supabase, a bigger plan (vertical) comes first, at the MRR set in the world's `PLAN.md`. | b1 b2 b6 | MANUAL (at the PLAN.md MRR trigger) |
| 97 | Stateless Services | Servers keep no memory between requests. | Functions keep state in Supabase, not in memory (in-memory maps are best-effort only, like the HQ chat limiter). | server worlds | MANUAL (code review) |
| 98 | Caching | Keep answers to reuse. | Cache static files long (`immutable` fonts on the HQ site), HTML short; cache AI answers only when the same question repeats. | all sites | MANUAL (new page type) |
| 99 | CDNs | Copies of files near the user. | Built into Netlify / GitHub Pages; Cloudflare Pages is the free option (Hosting map). | all sites | MANUAL |
| 100 | Cache Invalidation | Making caches drop old copies. | Fingerprinted file names for assets; service workers marked `no-cache` (b2 `sw.js` header) and versioned. | b2 b5 HQ | MANUAL (new service worker) |
| 101 | Reverse Proxies | A server in front that forwards traffic. | The host is our proxy (Netlify redirects, Render); Cloudflare in front is an option, not needed now. | all | MANUAL |
| 102 | API Gateways | One front door for many APIs (keys, limits). | The LLM router is our gateway for AI models; no other gateway needed. | HQ | MANUAL |
| 103 | Load Testing | Simulate many users. | Before a launch that expects traffic, run a small k6/autocannon test against a preview (never production, never third-party APIs). | b1 b2 b5 | MANUAL (before a big launch) |
| 104 | Performance Budgets | Limits like "page under 200 KB, LCP under 2.5 s". | Lighthouse runs in Actions (`lighthouse.yml`); every page passes at 390 px on mobile. | all sites | CI `lighthouse.yml` |

## 8. People & law

| # | Practice | What it means | Kalpa rule | Worlds | Check |
|---|---|---|---|---|---|
| 105 | Data Privacy (GDPR; India DPDP Act 2023) | Collect little, say why, let people delete it. | Privacy notice + consent on every form, processor clause for client data, delete on request, no scraping of banned sources, minimal logs (CLAUDE.md rule 4). b6 sells DPDP checklists; we follow them ourselves. | all | MANUAL (before go-live; Akhil signs legal) |
| 106 | Accessibility | Usable with screen readers, keyboard, large text. | Kalpa design system, real labels, contrast, focus rings; 20 SaaS UX patterns. | all with UI | CI `design` (vibecheck + theme), `lighthouse.yml`; MANUAL (keyboard pass before go-live) |
| 107 | Mobile Responsiveness | Works on a phone. | Every UI checked at 390 px, light + dark (CLAUDE.md rule 6), tested like a real customer on a phone. | all with UI | CI 390 px screen tests (b1, b2, b4) |

## What the scanner cannot see

Logic bugs (IDOR, mass assignment, missing checks), whether backups restore, whether alerts reach Akhil, and legal sign-off. Those stay MANUAL above, and every MANUAL "before go-live" row is part of a world's Depth item (A87–A94) before it goes live.

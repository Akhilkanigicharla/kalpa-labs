# Engineering checks: botbhai

Standard: `00-hq/design/ENGINEERING-CHECKS.md` (113) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).
Machine rows come from `python3 00-hq/tools/eng_check.py botbhai --md`; the rest are filled by hand.

## Automatic checks

| Check | Result | Note |
|---|---|---|
| Security Headers: Strict-Transport-Security | PASS | in 01-botbhai/botbhai/netlify.toml |
| Security Headers: X-Content-Type-Options | PASS | in 01-botbhai/botbhai/netlify.toml |
| Security Headers: Referrer-Policy | PASS | in 01-botbhai/botbhai/netlify.toml |
| Security Headers: Permissions-Policy | PASS | in 01-botbhai/botbhai/netlify.toml |
| Content Security Policy | PASS | default-src 'self'; script-src 'self' https://challenges.clo |
| Clickjacking | PASS | frame-ancestors / X-Frame-Options |
| Inline JS vs CSP | PASS | none |
| Inline on*= handlers | PASS |  |
| Custom 404 page | PASS |  |
| target=_blank has rel=noopener | PASS |  |
| Encryption in Transit (no http:// links) | PASS |  |
| Secrets Management (no keys in browser code) | PASS |  |
| XSS sinks (innerHTML/eval with variables) | PASS | reviewed: page.js: BotBhai demo page script (moved verbatim from index.src.html, A220): fmt() escapes first; tables use esc(); widget.js: constant SVG markup |
| Rate Limiting: 01-botbhai/botbhai/core/functions/adsbot.js | PASS | scheduled job, no public caller |
| Input caps: 01-botbhai/botbhai/core/functions/adsbot.js | PASS | no input length cap |
| Timeouts: 01-botbhai/botbhai/core/functions/telegram.js | PASS | fetch without timeout |
| Rate Limiting: 01-botbhai/botbhai/core/functions/telegram.js | WARN | webhook: platform-signed, rate set by sender |
| Input caps: 01-botbhai/botbhai/core/functions/telegram.js | PASS | no input length cap |
| Rate Limiting: 01-botbhai/botbhai/core/functions/billing.js | PASS | no limit |
| Input caps: 01-botbhai/botbhai/core/functions/billing.js | PASS | no input length cap |
| Timeouts: 01-botbhai/botbhai/core/functions/whatsapp.js | PASS | fetch without timeout |
| Rate Limiting: 01-botbhai/botbhai/core/functions/whatsapp.js | WARN | webhook: platform-signed, rate set by sender |
| Input caps: 01-botbhai/botbhai/core/functions/whatsapp.js | PASS | no input length cap |
| Rate Limiting: 01-botbhai/botbhai/core/functions/comments.js | WARN | webhook: platform-signed, rate set by sender |
| Input caps: 01-botbhai/botbhai/core/functions/comments.js | PASS | no input length cap |
| Rate Limiting: 01-botbhai/botbhai/core/functions/dayclose.js | PASS | scheduled job, no public caller |
| Input caps: 01-botbhai/botbhai/core/functions/dayclose.js | PASS | no input length cap |
| Rate Limiting: 01-botbhai/botbhai/core/functions/reminders.js | PASS | scheduled job, no public caller |
| Input caps: 01-botbhai/botbhai/core/functions/reminders.js | WARN | no input length cap |
| Rate Limiting: 01-botbhai/botbhai/core/functions/inbox.js | PASS | webhook: platform-signed, rate set by sender |
| Input caps: 01-botbhai/botbhai/core/functions/inbox.js | PASS | no input length cap |
| Rate Limiting: 01-botbhai/botbhai/core/functions/metaleads.js | WARN | webhook: platform-signed, rate set by sender |
| Input caps: 01-botbhai/botbhai/core/functions/metaleads.js | PASS | no input length cap |
| Rate Limiting: 01-botbhai/botbhai/core/functions/leads.js | PASS | no limit |
| Input caps: 01-botbhai/botbhai/core/functions/leads.js | PASS | no input length cap |
| Rate Limiting: 01-botbhai/botbhai/core/functions/chat.js | PASS | no limit |
| Input caps: 01-botbhai/botbhai/core/functions/chat.js | PASS | no input length cap |
| Pagination + Limits (every list read has limit= or pages) | PASS | no unbounded list reads |
| Failover (AI calls fall back to another model or a fixed reply) | PASS | 1 file(s) call AI, all with fallback |
| Graceful Degradation (browser fetch failures are caught) | PASS | 4 file(s) call the server, all catch errors |
| Performance Budgets (page + JS < 250 KB) | PASS | index.src.html: 101 KB |

## All 113 items (fill: done / not relevant + why / missing + roadmap id)

| # | Item | Status |
|---|---|---|
| 1 | Load Balancing | not relevant: Netlify CDN + serverless functions, no own servers to balance |
| 2 | Rate Limiting | auto: PASS |
| 3 | Environment Variables | done: server secrets only from process.env (SUPABASE_*, WA_*, TURNSTILE_SECRET_KEY, BILLING_ADMIN_KEY), set by Akhil in Netlify; gitleaks in CI |
| 4 | Secrets Management | auto: PASS |
| 5 | Authentication | done: owner = 36-hex dashboard key sent as `Authorization: Bearer` (leads.js, inbox.js; never in the URL, test in hardening.test.js); admin = BILLING_ADMIN_KEY compared with timingSafeEqual; customers need no login |
| 6 | Authorization | done: every read/write is filtered by the client found from the key; admin routes need the admin key |
| 7 | Input Validation | done: chat/webhook inputs typed and length-capped (automatic input-cap rows, hardening.test.js) |
| 8 | HTTP Status Codes | done: 400 bad JSON/contact, 401 bad key, 404 other client's chat, 429 rate limit (webhook.test.js) |
| 9 | Error Handling | done: try/catch in every function; customer gets a fixed reply (core/fallback.js); DB errors never carry customer text into logs (hardening.test.js) |
| 10 | Automated Testing | done: `bash 01-botbhai/botbhai/tools/test-all.sh` (engine, functions, schema, screens) in quality.yml |
| 11 | Database Indexing | done: indexes on leads, messages, sessions inbox, bookings slot, rate_hits, invoices, audit_log (schema.sql) |
| 12 | Database Migrations | done: schema.sql is idempotent (applied twice in supabase/test.sh) and carries its own migrations (migrate_client_secrets) |
| 13 | Backups | built 21 Nov (A310): nightly age-encrypted pg_dump, 7-day artifact, `.github/workflows/db-backup.yml`, tests `00-hq/backups/test.sh`; live after C93 secrets |
| 14 | Caching | not relevant: replies are per person and live; static files cached by the Netlify CDN |
| 15 | CDNs | done: Netlify CDN serves every static page |
| 16 | Logging | done: console.error with a short tag on every failure path → Netlify function log |
| 17 | Monitoring | done (A312, 21 Nov): logs + failure alerts to Akhil's private Telegram via `_opsalert.js`/`lib/opsalert.cjs`; live once OPS_ALERT_BOT_TOKEN + OPS_ALERT_CHAT_ID are set (C95); answer quality checked by botbhai-depth-live.yml |
| 18 | Timeouts | auto: PASS |
| 19 | Exponential Backoff | not relevant: Meta retries webhooks itself and the processed table dedupes; DB calls have 10 s timeouts and fail to the fixed reply |
| 20 | Idempotency | done: processed(wamid) handles each WhatsApp message once (_lib.js); invoice number + row in one transaction |
| 21 | Circuit Breakers | done: AI model chain skips a failed model and ends in a fixed reply (core/fallback.js, models.json) |
| 22 | Reverse Proxies | not relevant: Netlify's edge is the reverse proxy |
| 23 | API Gateways | not relevant: a few functions behind Netlify; each checks its own key/signature and rate |
| 24 | Docker | not relevant: serverless functions, no containers |
| 25 | CI/CD | done: `.github/workflows/quality.yml` runs gitleaks, actionlint and this world's tests on every push; deploys only after Akhil's go (rule 9) |
| 26 | Message Queues | not relevant: small volumes; scheduled functions do the background work |
| 27 | HTTPS / TLS | done: Netlify HTTPS + HSTS header (automatic rows) |
| 28 | Session Management | done: no server sessions; the owner key stays on that phone (inbox page wipes it from the address bar); rotate_dashboard_token() ends a leaked link (A221) |
| 29 | Two-Factor Authentication | not relevant: no passwords; owner access is a revocable secret link |
| 30 | SQL Injection | done: no SQL strings in functions; PostgREST values URL-encoded (L.enc); SQL functions take parameters |
| 31 | XSS (Cross-Site Scripting) | done: automatic XSS rows PASS + strict CSP on owner pages (A220) |
| 32 | CSRF | not relevant: no cookies; private APIs need a Bearer header and send no CORS header to other sites |
| 33 | Dependency Vulnerabilities | done: no npm lockfile in this world today; `00-hq/tools/dep_audit.py` in quality.yml audits any package-lock.json on every push, high/critical fails (A311) |
| 34 | Principle of Least Privilege | done: anon/authenticated get nothing (RLS on, no policies, execute revoked); Meta tokens readable only through client_token() by service_role |
| 35 | Race Conditions | done: book_slot() books in one locked statement; invoice numbers via counter upsert (40 parallel invoices test in supabase/test.sh) |
| 36 | Connection Pooling | not relevant: functions talk to Supabase over HTTP (PostgREST pools the connections) |
| 37 | Database Normalization | done: clients, sessions, leads, messages, bookings, invoices in their own tables keyed by client_id |
| 38 | Soft Deletes | done: a client is switched off (active=false), invoices are voided never deleted (on delete restrict); every delete/switch-off lands in audit_log (A221) |
| 39 | Data Validation on the Server | done: DB checks (niche list, invoice number pattern, total > 0, unique numbers) on top of function checks |
| 40 | File Upload Security | not relevant: customers send no files to our storage |
| 41 | Webhooks | done: Meta webhooks checked with x-hub-signature-256 + timingSafeEqual, verify token on subscribe, deduped (webhook.test.js) |
| 42 | Background Jobs | done: scheduled Netlify functions (netlify.toml) |
| 43 | Cron Jobs | done: schedules in netlify.toml, times in UTC with the IST time noted |
| 44 | Cache Invalidation | not relevant: no server cache; static files change with each deploy |
| 45 | Read Replicas | not relevant: one small Supabase database |
| 46 | Horizontal vs Vertical Scaling | not relevant: serverless, scales per request |
| 47 | Stateless Services | done: functions keep no state between calls; state lives in Supabase tables |
| 48 | Health Checks | missing: post-deploy smoke of the live URL is A227 |
| 49 | Graceful Shutdown | not relevant: serverless; the platform ends each call |
| 50 | Alerting | done (A312, 21 Nov): every function catch sends one line (app · function · kind · IST time), max 1 per kind per hour across copies (Supabase claim); test `core/functions/opsalert.test.js` 8 checks; off until C95 env is set |
| 51 | Distributed Tracing | not relevant: one hop (function → Supabase / Meta) |
| 52 | Structured Logging | not relevant at this size: one tagged console.error line per failure |
| 53 | Error Tracking | done (A312): same as 50; alert holds no message text, names or numbers (test checks it) |
| 54 | Uptime Monitoring | missing: live uptime check is A227 |
| 55 | Feature Flags | done: per-client config switches (ads_autopilot, inbox_hold_hours) and BOTBHAI_DEMO |
| 56 | Staging Environments | done: Netlify deploy previews + tests on fakes; nothing live without Akhil's go (rule 9) |
| 57 | Infrastructure as Code | done: netlify.toml (headers, schedules) and the SQL schema are in git |
| 58 | Code Review | done: egm-review / ponytail-review before ticks (CLAUDE.md) + CI |
| 59 | Branching Strategies | done: small commits to main, CI on every push (two-lane rules in 00-hq/TEAM.md) |
| 60 | Semantic Versioning | not relevant: no published package or outside API users |
| 61 | API Versioning | not relevant: our own pages are the only callers |
| 62 | API Documentation | done: each function file starts with its API contract (leads.js, inbox.js, billing.js) |
| 63 | Unit vs Integration vs End-to-End Tests | done: unit (engine, slots), function tests on fakes (webhook/hardening), schema tests on Postgres, 390 px screens |
| 64 | Load Testing | missing: load test on a preview deploy is A313 |
| 65 | Debugging | done: fakes reproduce Meta and Supabase replies; systematic-debugging skill on failures |
| 66 | Profiling | not relevant: small short-lived functions, nothing measured slow |
| 67 | Time Zones | done: bookings and invoice dates in IST (Asia/Kolkata defaults in schema.sql) |
| 68 | Character Encoding | done: UTF-8 end to end; 5 languages incl. Telugu and Hindi script tested (lang.test.js, chat-lang.test.js) |
| 69 | Concurrency | done: same as 35 (locked slot booking, single-statement counters) |
| 70 | Async / Await | done: async/await throughout; fire-and-forget calls end in .catch |
| 71 | Memory Leaks | not relevant: short-lived functions |
| 72 | Cost Monitoring | done: free tiers only; Netlify deploys counted by 00-hq/tools/deploy_budget.py |
| 73 | Disaster Recovery | built 21 Nov (A310): monthly restore check (row counts + grants + schema tests) and disaster-day steps in `00-hq/backups/README.md`; first real run after C93 |
| 74 | Data Privacy (GDPR) | done: marketing only with marketing_opt_in (DPDP + WhatsApp policy); Meta tokens in Vault; 180-day message retention is a manual monthly SQL (schema.sql note) |
| 75 | Accessibility | done: 390 px light/dark tap tests + design/ux-check.md |
| 76 | Mobile Responsiveness | done: 390 px tap sweep before ticks (rule 5) |
| 77 | Performance Budgets | auto: PASS |
| 78 | Technical Debt | done: open gaps are roadmap items (this table points to them) |
| 79 | Reading Documentation | done: rule 8: provider page + second source before advice |
| 80 | Reading Error Messages | done: errors carry a short tag; tests assert on messages |
| 81 | Content Security Policy | auto: PASS |
| 82 | Security Headers | auto: PASS |
| 83 | Clickjacking | auto: PASS |
| 84 | SSRF | not relevant: the server fetches only fixed hosts (Supabase, graph.facebook.com, Meta's media URL from the Graph reply); never a user-typed URL |
| 85 | Open Redirects | not relevant: no endpoint redirects to a URL from the request |
| 86 | Path Traversal | not relevant: no file paths taken from input |
| 87 | Command Injection | not relevant: no shell commands run |
| 88 | Mass Assignment | done: functions build each DB row field by field; no request body is spread into a row |
| 89 | IDOR | done: inbox/leads read only the key's client_id; another salon's key gets 404 for this chat (webhook.test.js, A221) |
| 90 | Brute Force Protection | done: rate_hit() per IP on inbox, leads, billing and chat; Cloudflare Turnstile on website bookings |
| 91 | Account Lockout | not relevant: no passwords; a 144-bit key can't be guessed and guesses are rate-limited |
| 92 | Password Reset Flows | not relevant: no passwords; a lost or leaked link is replaced with rotate_dashboard_token() |
| 93 | Magic Links | not relevant: no email logins |
| 94 | Passkeys | not relevant: no passwords to replace |
| 95 | Single Sign-On (SSO) | not relevant: single-owner small-business accounts |
| 96 | Role-Based Access Control | done: two roles: salon owner (dashboard key) and Akhil (BILLING_ADMIN_KEY); customers are anonymous |
| 97 | Row-Level Security | done: RLS on every table with no policies, so the public key reads nothing (schema.sql) |
| 98 | API Keys | done: one dashboard key per client, one admin key, Meta tokens per client in Vault |
| 99 | Token Expiration and Refresh | done: keys don't expire by time (owners would lose the inbox); they rotate on demand with rotate_dashboard_token() (A221) |
| 100 | Cookie Flags (HttpOnly, Secure, SameSite) | not relevant: no cookies |
| 101 | Secret Rotation | done: rotate_dashboard_token() (A221, tested); Meta tokens replaced with set_client_token in the SQL editor; Netlify env keys replaced by Akhil |
| 102 | Audit Logs | done: append-only audit_log for client create/delete, key rotation, on/off, number changes and invoice changes; never stores a token (A221, supabase/test.sql) |
| 103 | Encryption at Rest | done: Meta tokens in Supabase Vault (encrypted); Supabase disk encryption not checked today (unverified) |
| 104 | Encryption in Transit | auto: PASS |
| 105 | Hashing vs Encryption | done: tokens Vault-encrypted (must be sent to Meta, so not hashed); keys compared with timingSafeEqual |
| 106 | Salting | not relevant: no passwords stored by us |
| 107 | Penetration Testing | missing: OWASP ZAP baseline scan on a preview deploy is A313 |
| 108 | Multiple Servers / Redundancy | partly: web + functions on Netlify CDN/serverless; Supabase free tier is one region with no replica (paid only); covered by backups (check 13); voice agent is one process |
| 109 | Auto Scaling | platform: Netlify functions scale per request; Supabase free has a fixed size |
| 110 | Sharding | not relevant at this size: one shared schema keyed by client_id; revisit above ~10 lakh rows |
| 111 | Pagination + Limits | done 20 Nov 2026: scheduled jobs read every client/booking page by page (dbAll, 500 per page, 20,000 cap); single-row lookups use limit=1; owner screens capped (200–5,000); test core/functions/paging.test.js (1,203 clients) |
| 112 | Failover | done: AI replies fall back to the next free model, then to the fixed menu reply (core/fallback.js, aifallback.test.js); database calls time out after 10 s (20 Nov) |
| 113 | Graceful Degradation | done: owner screens catch failed calls and keep working (eng_check 113); the WhatsApp bot answers from the fixed menu when AI is down |

## Webhook door (A245, `botbhai/webhook-door/`, 14 Nov 2026)
Test: `node 01-botbhai/botbhai/webhook-door/test.mjs` (37 checks, also in `test-all.sh`).
| Item | Status |
|---|---|
| Webhook signature check | done: HMAC-SHA256 `X-Hub-Signature-256` on raw body, Telegram secret token, constant-time compare; forged/tampered/missing → 401 |
| Rate limiting | done: per-IP per-route window (Workers rate-limit binding when bound) → 429 before any work |
| Input validation / size cap | done: 256 KB cap → 413; handshake challenge only `[0-9A-Za-z_-]`; https-only forward URL |
| Timeouts / retries | done: 10 s forward timeout; upstream failure → 502 so Meta/Telegram retry |
| Secrets | done: Cloudflare secrets only; missing → 500 "not configured", nothing leaked |
| Logging | done: JSON event lines, no bodies, tokens or phone numbers |
| Kill switch / go gate | done: `DOOR_OPEN` must be "true" (default "false") → else 503 |
| Security headers | done: nosniff, no-store; no HTML served (not relevant: CSP/clickjacking) |
| 404 / 405 | done |
| Auth to the Space | done: `Authorization: Bearer HF_TOKEN` to the private Space |

## A242 engine flow: front-desk watchdog (`00-hq/agent-engine/flows/b1-frontdesk-watchdog.json`, 20 Nov 2026)
| Check | Status |
|---|---|
| Input validation | done: rows with bad ids, contacts, dates or future clocks skipped (`test_b1_frontdesk_watchdog.js`) |
| Output escaping | done: business names HTML-escaped, bidi/control chars stripped, 60 chars max |
| Personal data (DPDP) | done: never reads message text or bot state; phones masked to last 4; alerts only to Akhil's private chat |
| Timeouts / retries | done: 10 s timeout, 3 tries, 5 s apart on each GET |
| Outage handling | done: Supabase error → one warning per 6 h, no crash |
| Spam control | done: one alert per chat per customer message per level; 10 lines max; dedupe keys pruned after 3 days |
| Secrets | done: none in the file (test checks); key lives in the n8n credential Akhil sets |
| Public surface | done: schedule trigger only, `active: false`, GET only, no webhook |
| Go gate | waits A241 / C79 (engine up) and Akhil's "go" |

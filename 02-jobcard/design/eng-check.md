# Engineering checks: jobcard

Standard: `00-hq/design/ENGINEERING-CHECKS.md` (113) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).
Machine rows come from `python3 00-hq/tools/eng_check.py jobcard --md`; the rest are filled by hand.

## Automatic checks

| Check | Result | Note |
|---|---|---|
| Security Headers: Strict-Transport-Security | PASS | in 02-jobcard/netlify.toml |
| Security Headers: X-Content-Type-Options | PASS | in 02-jobcard/netlify.toml |
| Security Headers: Referrer-Policy | PASS | in 02-jobcard/netlify.toml |
| Security Headers: Permissions-Policy | PASS | in 02-jobcard/netlify.toml |
| Content Security Policy | PASS | default-src 'self'; script-src 'self'; style-src 'self' 'uns |
| Clickjacking | PASS | frame-ancestors / X-Frame-Options |
| Inline JS vs CSP | PASS | none |
| Inline on*= handlers | PASS |  |
| Custom 404 page | PASS | single-page app: unknown paths open the app |
| target=_blank has rel=noopener | PASS |  |
| Encryption in Transit (no http:// links) | PASS |  |
| Secrets Management (no keys in browser code) | PASS |  |
| XSS sinks (innerHTML/eval with variables) | PASS | reviewed: app.mjs: every value goes through esc() |
| Timeouts: 02-jobcard/bot/functions/jobcard.js | PASS | fetch without timeout |
| Rate Limiting: 02-jobcard/bot/functions/jobcard.js | PASS | webhook: platform-signed, rate set by sender |
| Input caps: 02-jobcard/bot/functions/jobcard.js | PASS | no input length cap |
| Timeouts: 02-jobcard/bot/functions/reminders.js | PASS | fetch without timeout |
| Rate Limiting: 02-jobcard/bot/functions/reminders.js | PASS | scheduled job, no public caller |
| Input caps: 02-jobcard/bot/functions/reminders.js | PASS | no input length cap |
| Pagination + Limits (every list read has limit= or pages) | PASS | no unbounded list reads |
| Failover (AI calls fall back to another model or a fixed reply) | PASS | no AI calls |
| Graceful Degradation (browser fetch failures are caught) | PASS | 2 file(s) call the server, all catch errors |
| Performance Budgets (page + JS < 250 KB) | PASS | index.html: 34 KB |

## All 113 items (fill: done / not relevant + why / missing + roadmap id)

| # | Item | Status |
|---|---|---|
| 1 | Load Balancing | not relevant: Netlify CDN + serverless functions, no own servers to balance |
| 2 | Rate Limiting | auto: PASS |
| 3 | Environment Variables | done: function secrets via env() (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, WA_*) set by Akhil in Netlify; the app gets only the public URL + anon key at build (web/build.mjs) |
| 4 | Secrets Management | auto: PASS |
| 5 | Authentication | done: phone OTP through Supabase Auth (web/logic.mjs sendOtp/verifyOtp) |
| 6 | Authorization | done: RLS policy own_rows: technician_id = auth.uid() on every table; bot uses service role only after the WhatsApp signature check |
| 7 | Input Validation | done: phone normalised (normPhone), voice note capped at 16 MB, DB checks on invoices (0001_security.sql) |
| 8 | HTTP Status Codes | done: 401 bad signature, 403 failed verify, 400 bad JSON (bot.test.mjs) |
| 9 | Error Handling | done: errors caught per message, logged with console.error, user sees a plain message; app catches failed loads |
| 10 | Automated Testing | done: `npm test` in 02-jobcard (37 tests) + `bash supabase/test.sh` in quality.yml |
| 11 | Database Indexing | done: indexes on job_cards (tech, visited_at), next_service, invoices (tech, issued_on), audit_log |
| 12 | Database Migrations | done: schema.sql idempotent + supabase/migrations/0001_security.sql, both re-applied in test.sh |
| 13 | Backups | missing: no backup we control yet; nightly dump + restore drill is A310 |
| 14 | Caching | not relevant: replies are per person and live; static files cached by the Netlify CDN |
| 15 | CDNs | done: Netlify CDN serves every static page |
| 16 | Logging | done: console.error on failure paths → Netlify function log |
| 17 | Monitoring | missing (alerts): logs exist, alerting is A312 |
| 18 | Timeouts | auto: PASS |
| 19 | Exponential Backoff | done: fetchRetry: 250 ms × 2^n + jitter, reads only (jobcard.js) |
| 20 | Idempotency | done: wa_processed: each Meta message handled once; reminder_sends: one reminder per technician per day |
| 21 | Circuit Breakers | not relevant: no AI model calls in functions; outbound calls time out and retry a few times |
| 22 | Reverse Proxies | not relevant: Netlify's edge is the reverse proxy |
| 23 | API Gateways | not relevant: a few functions behind Netlify; each checks its own key/signature and rate |
| 24 | Docker | not relevant: serverless functions, no containers |
| 25 | CI/CD | done: `.github/workflows/quality.yml` runs gitleaks, actionlint and this world's tests on every push; deploys only after Akhil's go (rule 9) |
| 26 | Message Queues | not relevant: small volumes; scheduled functions do the background work |
| 27 | HTTPS / TLS | done: Netlify HTTPS + HSTS header (automatic rows) |
| 28 | Session Management | done: Supabase JWT (1 h) + refresh token, refreshed 1 min before expiry; 401 signs out (web.test.mjs) |
| 29 | Two-Factor Authentication | not relevant: phone OTP is the only factor and owns the account; no passwords |
| 30 | SQL Injection | done: PostgREST with URL-encoded values; SQL functions use parameters |
| 31 | XSS (Cross-Site Scripting) | done: automatic XSS rows PASS (esc() on every value) + strict CSP |
| 32 | CSRF | not relevant: no cookies; token sent in the Authorization header |
| 33 | Dependency Vulnerabilities | missing: no dependency audit step yet, A311 |
| 34 | Principle of Least Privilege | done: anon gets nothing; technicians can't delete their profile; invoices insert-only except `paid`; service-only functions (0001_security.sql) |
| 35 | Race Conditions | done: invoice numbers from a per-technician counter in one statement (next_invoice_no) |
| 36 | Connection Pooling | not relevant: functions talk to Supabase over HTTP (PostgREST pools the connections) |
| 37 | Database Normalization | done: technicians, customers, job_cards, invoices, amc_contracts in their own tables |
| 38 | Soft Deletes | done: invoices can't be deleted (no grant); a customer or job card with a bill can't be deleted; customer deletes are audited (0001_security.sql) |
| 39 | Data Validation on the Server | done: invoice_integrity trigger checks kind, number, FY and totals for app and bot alike |
| 40 | File Upload Security | done: no uploads to our storage; WhatsApp voice notes fetched from Meta, size-capped at 16 MB |
| 41 | Webhooks | done: Meta webhook: x-hub-signature-256 + timingSafeEqual, verify token, challenge pattern, dedupe (bot.test.mjs) |
| 42 | Background Jobs | done: scheduled Netlify functions (netlify.toml) |
| 43 | Cron Jobs | done: schedules in netlify.toml, times in UTC with the IST time noted |
| 44 | Cache Invalidation | not relevant: no server cache; static files change with each deploy |
| 45 | Read Replicas | not relevant: one small Supabase database |
| 46 | Horizontal vs Vertical Scaling | not relevant: serverless, scales per request |
| 47 | Stateless Services | done: functions keep no state between calls; state lives in Supabase tables |
| 48 | Health Checks | missing: post-deploy smoke of the live URL is A227 |
| 49 | Graceful Shutdown | not relevant: serverless; the platform ends each call |
| 50 | Alerting | missing: function errors only reach the Netlify log; Telegram alert to Akhil is A312 |
| 51 | Distributed Tracing | not relevant: one hop (function → Supabase / Meta) |
| 52 | Structured Logging | not relevant at this size: one tagged console.error line per failure |
| 53 | Error Tracking | missing: same as 50, A312 |
| 54 | Uptime Monitoring | missing: live uptime check is A227 |
| 55 | Feature Flags | not relevant: product parked (Akhil, 6 Nov 2026); plan flag on technicians is set only by the server |
| 56 | Staging Environments | done: Netlify deploy previews + tests on fakes; nothing live without Akhil's go (rule 9) |
| 57 | Infrastructure as Code | done: netlify.toml (headers, schedules) and the SQL schema are in git |
| 58 | Code Review | done: egm-review / ponytail-review before ticks (CLAUDE.md) + CI |
| 59 | Branching Strategies | done: small commits to main, CI on every push (two-lane rules in 00-hq/TEAM.md) |
| 60 | Semantic Versioning | not relevant: no published package or outside API users |
| 61 | API Versioning | not relevant: our own pages are the only callers |
| 62 | API Documentation | done: header comments in bot/functions/*.js and web/logic.mjs |
| 63 | Unit vs Integration vs End-to-End Tests | done: unit (parse, invoice, reminders), bot tests on fakes, schema tests on Postgres, web screen tests |
| 64 | Load Testing | missing: load test on a preview deploy is A313 |
| 65 | Debugging | done: fakes reproduce Meta and Supabase replies; systematic-debugging skill on failures |
| 66 | Profiling | not relevant: small short-lived functions, nothing measured slow |
| 67 | Time Zones | done: IST dates (istToday) and financial year by Indian rules (fy_of) |
| 68 | Character Encoding | done: UTF-8; Telugu names in bills (Anek Telugu font) tested (languages.test.mjs) |
| 69 | Concurrency | done: per-technician invoice counter row; triggers check ownership on write |
| 70 | Async / Await | done: async/await throughout; fire-and-forget calls end in .catch |
| 71 | Memory Leaks | not relevant: short-lived functions |
| 72 | Cost Monitoring | done: free tiers only; Netlify deploys counted by 00-hq/tools/deploy_budget.py |
| 73 | Disaster Recovery | missing: restore drill is part of A310 |
| 74 | Data Privacy (GDPR) | done: reminders only to customers who opted in (views + tests); each technician sees only his own rows |
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
| 88 | Mass Assignment | done: plan_guard (plan only by server) and invoice_integrity (kind/number/amounts checked in the DB) (0001_security.sql) |
| 89 | IDOR | done: RLS + same-owner triggers: a job card or invoice can't point at another technician's customer (supabase/test.sql) |
| 90 | Brute Force Protection | platform: Supabase Auth limits OTP sends and tries (limits not checked today, unverified); webhook needs Meta's signature |
| 91 | Account Lockout | platform: as 90; no passwords to lock |
| 92 | Password Reset Flows | not relevant: no passwords; a new OTP signs in |
| 93 | Magic Links | not relevant: no email logins |
| 94 | Passkeys | not relevant: no passwords to replace |
| 95 | Single Sign-On (SSO) | not relevant: single-owner small-business accounts |
| 96 | Role-Based Access Control | not relevant: one role (the technician owns his rows); the server has service role |
| 97 | Row-Level Security | done: RLS on all tables, policies own_rows / own_profile / own_audit (schema.sql, 0001_security.sql) |
| 98 | API Keys | done: only the public anon key in the app; service role key only in Netlify env |
| 99 | Token Expiration and Refresh | done: access token 1 h, refreshed 1 min before expiry; sign-out now also revokes the session on the server (/auth/v1/logout, A221, web.test.mjs) |
| 100 | Cookie Flags (HttpOnly, Secure, SameSite) | not relevant: session in localStorage, no cookies (CSP blocks third-party scripts) |
| 101 | Secret Rotation | done: keys live only in Netlify env; Akhil replaces them there and redeploys; sign-out revokes refresh tokens (A221) |
| 102 | Audit Logs | done: append-only audit_log for invoices, plan/GST changes and customer deletes; technician reads only his own (0001_security.sql) |
| 103 | Encryption at Rest | not checked: Supabase disk encryption (unverified); no secrets stored in tables |
| 104 | Encryption in Transit | auto: PASS |
| 105 | Hashing vs Encryption | not relevant: no passwords; nothing we must decrypt is stored |
| 106 | Salting | not relevant: no passwords stored by us |
| 107 | Penetration Testing | missing: OWASP ZAP baseline scan on a preview deploy is A313 |
| 108 | Multiple Servers / Redundancy | platform: Netlify CDN + serverless; Supabase free = one region |
| 109 | Auto Scaling | platform: Netlify functions scale per request |
| 110 | Sharding | not relevant: rows per technician, small |
| 111 | Pagination + Limits | done 20 Nov 2026: reminders and the app read technicians, customers, job cards and AMCs page by page (dbAll/restAll); lookups use limit=1 |
| 112 | Failover | done: no AI model calls in functions; WhatsApp and database calls go through fetchRetry with timeouts |
| 113 | Graceful Degradation | done: app catches failed loads; service worker keeps the app usable offline (sw.template.js) |

## A242 engine flow: store-review watcher (`00-hq/agent-engine/flows/b2-review-watcher.json`, 20 Nov 2026)
| Check | Status |
|---|---|
| Input validation | done: only known apps, integer ratings 1–5, safe ids, text 1–5000 chars; duplicates and broken rows skipped; 200 new per run (`test_b2_review_watcher.js`) |
| Prompt injection | done: no model call at all; instruction-like reviews flagged and their text not shown |
| Output escaping | done: HTML-escaped, control/bidi chars stripped, 80 characters cut on whole characters |
| Personal data (DPDP) | done: file holds app, id, rating, text only (no reviewer names); digest goes only to Akhil's private chat |
| Timeouts / retries | done: 10 s timeout, 3 tries, 5 s apart |
| Outage / bad file | done: missing, non-JSON, non-list or >600 KB file → one warning a day, no crash |
| Spam control | done: one digest a day, new reviews only, 8 review lines max, seen list capped at 5000 |
| Secrets | done: none in the file (test checks); Telegram credential set by Akhil in n8n |
| Public surface | done: schedule trigger only, `active: false`, one GET of a public repo file, no webhook |
| Go gate | waits A241 / C79 (engine up) and Akhil's "go" |

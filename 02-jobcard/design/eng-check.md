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
| 1 | Load Balancing | manual |
| 2 | Rate Limiting | auto: PASS |
| 3 | Environment Variables | manual |
| 4 | Secrets Management | auto: PASS |
| 5 | Authentication | manual |
| 6 | Authorization | manual |
| 7 | Input Validation | manual |
| 8 | HTTP Status Codes | manual |
| 9 | Error Handling | manual |
| 10 | Automated Testing | manual |
| 11 | Database Indexing | manual |
| 12 | Database Migrations | manual |
| 13 | Backups | manual |
| 14 | Caching | manual |
| 15 | CDNs | manual |
| 16 | Logging | manual |
| 17 | Monitoring | manual |
| 18 | Timeouts | auto: PASS |
| 19 | Exponential Backoff | manual |
| 20 | Idempotency | manual |
| 21 | Circuit Breakers | manual |
| 22 | Reverse Proxies | manual |
| 23 | API Gateways | manual |
| 24 | Docker | manual |
| 25 | CI/CD | manual |
| 26 | Message Queues | manual |
| 27 | HTTPS / TLS | manual |
| 28 | Session Management | manual |
| 29 | Two-Factor Authentication | manual |
| 30 | SQL Injection | manual |
| 31 | XSS (Cross-Site Scripting) | manual |
| 32 | CSRF | manual |
| 33 | Dependency Vulnerabilities | manual |
| 34 | Principle of Least Privilege | manual |
| 35 | Race Conditions | manual |
| 36 | Connection Pooling | manual |
| 37 | Database Normalization | manual |
| 38 | Soft Deletes | manual |
| 39 | Data Validation on the Server | manual |
| 40 | File Upload Security | manual |
| 41 | Webhooks | manual |
| 42 | Background Jobs | manual |
| 43 | Cron Jobs | manual |
| 44 | Cache Invalidation | manual |
| 45 | Read Replicas | manual |
| 46 | Horizontal vs Vertical Scaling | manual |
| 47 | Stateless Services | manual |
| 48 | Health Checks | manual |
| 49 | Graceful Shutdown | manual |
| 50 | Alerting | manual |
| 51 | Distributed Tracing | manual |
| 52 | Structured Logging | manual |
| 53 | Error Tracking | manual |
| 54 | Uptime Monitoring | manual |
| 55 | Feature Flags | manual |
| 56 | Staging Environments | manual |
| 57 | Infrastructure as Code | manual |
| 58 | Code Review | manual |
| 59 | Branching Strategies | manual |
| 60 | Semantic Versioning | manual |
| 61 | API Versioning | manual |
| 62 | API Documentation | manual |
| 63 | Unit vs Integration vs End-to-End Tests | manual |
| 64 | Load Testing | manual |
| 65 | Debugging | manual |
| 66 | Profiling | manual |
| 67 | Time Zones | manual |
| 68 | Character Encoding | manual |
| 69 | Concurrency | manual |
| 70 | Async / Await | manual |
| 71 | Memory Leaks | manual |
| 72 | Cost Monitoring | manual |
| 73 | Disaster Recovery | manual |
| 74 | Data Privacy (GDPR) | manual |
| 75 | Accessibility | manual |
| 76 | Mobile Responsiveness | manual |
| 77 | Performance Budgets | auto: PASS |
| 78 | Technical Debt | manual |
| 79 | Reading Documentation | manual |
| 80 | Reading Error Messages | manual |
| 81 | Content Security Policy | auto: PASS |
| 82 | Security Headers | auto: PASS |
| 83 | Clickjacking | auto: PASS |
| 84 | SSRF | manual |
| 85 | Open Redirects | manual |
| 86 | Path Traversal | manual |
| 87 | Command Injection | manual |
| 88 | Mass Assignment | manual |
| 89 | IDOR | manual |
| 90 | Brute Force Protection | manual |
| 91 | Account Lockout | manual |
| 92 | Password Reset Flows | manual |
| 93 | Magic Links | manual |
| 94 | Passkeys | manual |
| 95 | Single Sign-On (SSO) | manual |
| 96 | Role-Based Access Control | manual |
| 97 | Row-Level Security | manual |
| 98 | API Keys | manual |
| 99 | Token Expiration and Refresh | manual |
| 100 | Cookie Flags (HttpOnly, Secure, SameSite) | manual |
| 101 | Secret Rotation | manual |
| 102 | Audit Logs | manual |
| 103 | Encryption at Rest | manual |
| 104 | Encryption in Transit | auto: PASS |
| 105 | Hashing vs Encryption | manual |
| 106 | Salting | manual |
| 107 | Penetration Testing | manual |
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

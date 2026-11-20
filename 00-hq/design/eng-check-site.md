# Engineering checks: hq-site

Standard: `00-hq/design/ENGINEERING-CHECKS.md` (113) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).
Machine rows come from `python3 00-hq/tools/eng_check.py hq-site --md`; the rest are filled by hand.

## Automatic checks

| Check | Result | Note |
|---|---|---|
| Security Headers: Strict-Transport-Security | PASS | in 00-hq/site/netlify.toml |
| Security Headers: X-Content-Type-Options | PASS | in 00-hq/site/netlify.toml |
| Security Headers: Referrer-Policy | PASS | in 00-hq/site/netlify.toml |
| Security Headers: Permissions-Policy | PASS | in 00-hq/site/netlify.toml |
| Content Security Policy | PASS | default-src 'self'; script-src 'self'; style-src 'self' 'uns |
| Clickjacking | PASS | frame-ancestors / X-Frame-Options |
| Inline JS vs CSP | PASS | none |
| Inline on*= handlers | PASS |  |
| Custom 404 page | PASS |  |
| target=_blank has rel=noopener | PASS |  |
| Encryption in Transit (no http:// links) | PASS |  |
| Secrets Management (no keys in browser code) | PASS |  |
| XSS sinks (innerHTML/eval with variables) | WARN | review: site.js |
| Rate Limiting: 00-hq/site/netlify/functions/chat.mjs | PASS | webhook: platform-signed, rate set by sender |
| Input caps: 00-hq/site/netlify/functions/chat.mjs | PASS | no input length cap |
| Pagination + Limits (every list read has limit= or pages) | PASS | no unbounded list reads |
| Failover (AI calls fall back to another model or a fixed reply) | PASS | 1 file(s) call AI, all with fallback |
| Graceful Degradation (browser fetch failures are caught) | PASS | 2 file(s) call the server, all catch errors |
| Performance Budgets (page + JS < 250 KB) | PASS | index.html: 165 KB |

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
| 18 | Timeouts | manual |
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
| 108 | Multiple Servers / Redundancy | done: static pages on Netlify's CDN (many locations); chat is a serverless function; it calls Groq/OpenRouter directly, so the single free Render router is not needed |
| 109 | Auto Scaling | platform: Netlify functions scale per request |
| 110 | Sharding | not relevant: no database |
| 111 | Pagination + Limits | done: no list reads (eng_check 111 PASS) |
| 112 | Failover | done: chat tries 3 free models in turn (Groq gpt-oss-20b → Groq Qwen → OpenRouter), then a polite 503 |
| 113 | Graceful Degradation | done: if chat fails, the page shows an offline message pointing to the contact form; the form still works (site.js/app.js) |

## A242 engine flow: HQ morning brief (`00-hq/agent-engine/flows/hq-morning-brief.json`, 20 Nov 2026)
| Check | Status |
|---|---|
| Input validation | done: roadmap lines parsed only inside "Agent queue" / "CEO queue", task files must be JSON lists, statuses whitelisted, K ids pattern-checked, 900 KB per file and 5000 task rows max (`test_hq_morning_brief.js`) |
| Prompt injection | done: no model call; instruction-like roadmap text is not shown, only its id |
| Output escaping | done: HTML-escaped, control/bidi chars stripped, titles cut at 90/110 whole characters (emoji + Telugu tests), message capped at 4000 chars |
| Edge cases | done: empty queue, 300+300 open items (3 shown each), 8 blocked (6 shown), duplicate ids, two lanes claiming one item, CEO items waiting 7+ days (age kept in static data, closed ones forgotten) |
| Timeouts / retries | done: 10 s timeout, 3 tries, 5 s apart, per file; one bad file is named and the rest still briefed |
| Outage | done: ROADMAP.md unreadable → one warning a day, then silence |
| Secrets / privacy | done: GET of public repo files only, no keys in the file, private Telegram chat only, no public URL, ships `active: false` |
| Spam control | done: one message a day at 07:00 IST |

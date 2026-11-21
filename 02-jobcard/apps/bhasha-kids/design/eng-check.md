# Engineering checks: bhasha-kids

Standard: `00-hq/design/ENGINEERING-CHECKS.md` (113) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).
Machine rows come from `python3 00-hq/tools/eng_check.py bhasha-kids --md`; the rest are filled by hand.

## Automatic checks

| Check | Result | Note |
|---|---|---|
| Security Headers: Strict-Transport-Security | PASS | in 02-jobcard/apps/bhasha-kids/netlify.toml |
| Security Headers: X-Content-Type-Options | PASS | in 02-jobcard/apps/bhasha-kids/netlify.toml |
| Security Headers: Referrer-Policy | PASS | in 02-jobcard/apps/bhasha-kids/netlify.toml |
| Security Headers: Permissions-Policy | PASS | in 02-jobcard/apps/bhasha-kids/netlify.toml |
| Content Security Policy | PASS | default-src 'self'; script-src 'self'; style-src 'self'; img |
| Clickjacking | PASS | frame-ancestors / X-Frame-Options |
| Inline JS vs CSP | PASS | none |
| Inline on*= handlers | PASS |  |
| Custom 404 page | PASS |  |
| target=_blank has rel=noopener | PASS |  |
| Encryption in Transit (no http:// links) | PASS |  |
| Secrets Management (no keys in browser code) | PASS |  |
| XSS sinks (innerHTML/eval with variables) | PASS | reviewed: app.js: i18n text from our own dictionary + constant markup |
| Pagination + Limits (every list read has limit= or pages) | PASS | no unbounded list reads |
| Failover (AI calls fall back to another model or a fixed reply) | PASS | no AI calls |
| Graceful Degradation (browser fetch failures are caught) | PASS | 2 file(s) call the server, all catch errors |
| Performance Budgets (page + JS < 250 KB) | PASS | index.html: 24 KB |

## All 113 items (fill: done / not relevant + why / missing + roadmap id)

| # | Item | Status |
|---|---|---|
| 1 | Load Balancing | not relevant: static PWA, no server, database or accounts |
| 2 | Rate Limiting | not relevant: static PWA, no server, database or accounts (nothing to rate-limit) |
| 3 | Environment Variables | not relevant: no secrets or server config |
| 4 | Secrets Management | auto: PASS |
| 5 | Authentication | not relevant: no accounts or logins |
| 6 | Authorization | not relevant: no accounts or logins |
| 7 | Input Validation | done: form/file inputs checked in the browser; nothing reaches a server |
| 8 | HTTP Status Codes | done: static host returns 200/404; custom 404.html (A328) |
| 9 | Error Handling | done: try/catch around storage, lesson loading and speech; a headless-Chromium tab crash in SpeechRecognition.available is not catchable → A331 |
| 10 | Automated Testing | done: `npm test` (node --test), in CI quality.yml since A328 |
| 11 | Database Indexing | not relevant: static PWA, no server, database or accounts |
| 12 | Database Migrations | not relevant: static PWA, no server, database or accounts |
| 13 | Backups | done: code in git; user data never leaves the device (nothing of ours to back up) |
| 14 | Caching | done: service worker / browser cache of our own files |
| 15 | CDNs | done: Netlify's CDN when deployed (netlify.toml); not live yet |
| 16 | Logging | not relevant: static PWA, no server, database or accounts (no server logs) |
| 17 | Monitoring | missing until live: uptime check after go → A331 |
| 18 | Timeouts | not relevant: static PWA, no server, database or accounts (no outside fetch) |
| 19 | Exponential Backoff | not relevant: static PWA, no server, database or accounts (no outside fetch) |
| 20 | Idempotency | not relevant: static PWA, no server, database or accounts |
| 21 | Circuit Breakers | not relevant: static PWA, no server, database or accounts |
| 22 | Reverse Proxies | not relevant: static PWA, no server, database or accounts |
| 23 | API Gateways | not relevant: static PWA, no server, database or accounts |
| 24 | Docker | not relevant: static files |
| 25 | CI/CD | done: quality.yml runs tests + eng_check on every push (A328) |
| 26 | Message Queues | not relevant: static PWA, no server, database or accounts |
| 27 | HTTPS / TLS | done: HSTS + upgrade-insecure-requests in netlify.toml |
| 28 | Session Management | not relevant: no accounts or logins |
| 29 | Two-Factor Authentication | not relevant: no accounts or logins |
| 30 | SQL Injection | not relevant: static PWA, no server, database or accounts |
| 31 | XSS (Cross-Site Scripting) | done: strict CSP (no inline script) + eng_check XSS-sink scan PASS |
| 32 | CSRF | not relevant: static PWA, no server, database or accounts (no state-changing requests) |
| 33 | Dependency Vulnerabilities | done: no runtime dependencies; A311 audit covers any package-lock.json |
| 34 | Principle of Least Privilege | done: microphone only when a child taps 'Say it' and the parent allowed it; CSP blocks outside requests |
| 35 | Race Conditions | done: single-user, single-tab, synchronous state |
| 36 | Connection Pooling | not relevant: static PWA, no server, database or accounts |
| 37 | Database Normalization | not relevant: static PWA, no server, database or accounts |
| 38 | Soft Deletes | not relevant: static PWA, no server, database or accounts |
| 39 | Data Validation on the Server | not relevant: static PWA, no server, database or accounts |
| 40 | File Upload Security | not relevant: no uploads to any server |
| 41 | Webhooks | not relevant: static PWA, no server, database or accounts |
| 42 | Background Jobs | not relevant: static PWA, no server, database or accounts |
| 43 | Cron Jobs | not relevant: static PWA, no server, database or accounts |
| 44 | Cache Invalidation | done: versioned cache name in sw.js, old caches deleted on activate |
| 45 | Read Replicas | not relevant: static PWA, no server, database or accounts |
| 46 | Horizontal vs Vertical Scaling | not relevant: static PWA, no server, database or accounts (CDN serves static files) |
| 47 | Stateless Services | not relevant: static PWA, no server, database or accounts |
| 48 | Health Checks | not relevant: static PWA, no server, database or accounts |
| 49 | Graceful Shutdown | not relevant: static PWA, no server, database or accounts |
| 50 | Alerting | missing until live → A331 |
| 51 | Distributed Tracing | not relevant: static PWA, no server, database or accounts |
| 52 | Structured Logging | not relevant: static PWA, no server, database or accounts |
| 53 | Error Tracking | missing: no error reporting (would need a server; privacy first) → A331 |
| 54 | Uptime Monitoring | missing until live → A331 |
| 55 | Feature Flags | not relevant: prototype, one version |
| 56 | Staging Environments | done: Netlify deploy previews when deployed; local http.server today |
| 57 | Infrastructure as Code | done: netlify.toml holds headers and publish settings |
| 58 | Code Review | done: ponytail-review / eng_check before ticks |
| 59 | Branching Strategies | done: main + lane claims (00-hq/TEAM.md) |
| 60 | Semantic Versioning | done: package.json version |
| 61 | API Versioning | not relevant: static PWA, no server, database or accounts |
| 62 | API Documentation | not relevant: static PWA, no server, database or accounts |
| 63 | Unit vs Integration vs End-to-End Tests | done: unit tests (node --test) + 390 px tap sweep in a real browser |
| 64 | Load Testing | not relevant: static PWA, no server, database or accounts (static files on a CDN) |
| 65 | Debugging | done: pure logic in testable modules |
| 66 | Profiling | done: page + JS under the 250 KB budget (eng_check) |
| 67 | Time Zones | not relevant: no times shown |
| 68 | Character Encoding | done: UTF-8 meta; Telugu/Hindi text with bundled OFL fonts |
| 69 | Concurrency | done: one user per device; no shared state |
| 70 | Async / Await | done: async calls wrapped in try/catch |
| 71 | Memory Leaks | done: export object URL revoked; listen timeout clears |
| 72 | Cost Monitoring | done: static hosting on free tier; Netlify credit budget tool (A222) |
| 73 | Disaster Recovery | done: redeploy from git; no server state |
| 74 | Data Privacy (GDPR) | done: progress only in localStorage; speech recognition 'cloud' mode needs parent opt-in (sayItAllowed) |
| 75 | Accessibility | done 21 Nov (A331): `00-hq/site/tests/test_axe.py` (axe-core 4.10.3) at 390 px light + dark on the app, its main screens and 404 → 0 serious/critical |
| 76 | Mobile Responsiveness | done: tap sweep PASS at 390 px light + dark (21 Nov) |
| 77 | Performance Budgets | auto: PASS |
| 78 | Technical Debt | done: open work tracked in ROADMAP.md (A331) and each app README |
| 79 | Reading Documentation | done: browser API docs followed (MDN) |
| 80 | Reading Error Messages | done: errors shown in plain words |
| 81 | Content Security Policy | auto: PASS |
| 82 | Security Headers | auto: PASS |
| 83 | Clickjacking | auto: PASS |
| 84 | SSRF | not relevant: static PWA, no server, database or accounts |
| 85 | Open Redirects | not relevant: no redirect parameters |
| 86 | Path Traversal | not relevant: static PWA, no server, database or accounts |
| 87 | Command Injection | not relevant: static PWA, no server, database or accounts |
| 88 | Mass Assignment | not relevant: static PWA, no server, database or accounts |
| 89 | IDOR | not relevant: no accounts or logins |
| 90 | Brute Force Protection | not relevant: no accounts or logins |
| 91 | Account Lockout | not relevant: no accounts or logins |
| 92 | Password Reset Flows | not relevant: no accounts or logins |
| 93 | Magic Links | not relevant: no accounts or logins |
| 94 | Passkeys | not relevant: no accounts or logins |
| 95 | Single Sign-On (SSO) | not relevant: no accounts or logins |
| 96 | Role-Based Access Control | not relevant: no accounts or logins |
| 97 | Row-Level Security | not relevant: static PWA, no server, database or accounts |
| 98 | API Keys | not relevant: no API keys used |
| 99 | Token Expiration and Refresh | not relevant: no accounts or logins |
| 100 | Cookie Flags (HttpOnly, Secure, SameSite) | not relevant: no cookies |
| 101 | Secret Rotation | not relevant: no secrets |
| 102 | Audit Logs | not relevant: no accounts or logins |
| 103 | Encryption at Rest | not relevant: nothing stored by us; device storage is the phone's |
| 104 | Encryption in Transit | auto: PASS |
| 105 | Hashing vs Encryption | not relevant: no accounts or logins |
| 106 | Salting | not relevant: no accounts or logins |
| 107 | Penetration Testing | missing until live: A205 scan on the live URL after go → A331 |
| 108 | Multiple Servers / Redundancy | done when deployed: Netlify CDN edge copies |
| 109 | Auto Scaling | not relevant: static PWA, no server, database or accounts (CDN) |
| 110 | Sharding | not relevant: static PWA, no server, database or accounts |
| 111 | Pagination + Limits | auto: PASS |
| 112 | Failover | auto: PASS |
| 113 | Graceful Degradation | auto: PASS |

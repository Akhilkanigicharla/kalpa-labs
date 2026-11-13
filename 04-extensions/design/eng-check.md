# Engineering checks: extension

Standard: `00-hq/design/ENGINEERING-CHECKS.md` (107) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).
Machine rows come from `python3 00-hq/tools/eng_check.py extension --md`; the rest are filled by hand.

## Automatic checks

| Check | Result | Note |
|---|---|---|
| target=_blank has rel=noopener | PASS |  |
| Encryption in Transit (no http:// links) | PASS |  |
| Secrets Management (no keys in browser code) | PASS |  |
| XSS sinks (innerHTML/eval with variables) | PASS |  |
| Performance Budgets (page + JS < 250 KB) | PASS | index.html: 5 KB |

## All 107 items (fill: done / not relevant + why / missing + roadmap id)

| # | Item | Status |
|---|---|---|
| 1 | Load Balancing | manual |
| 2 | Rate Limiting | done: no API of ours; Drive uploads at most hourly and only on change, so Google's rate limits are never approached |
| 3 | Environment Variables | manual |
| 4 | Secrets Management | auto: PASS |
| 5 | Authentication | manual |
| 6 | Authorization | done: Drive scope is drive.appdata only: Tab Lifeboat's hidden folder, nothing else in the user's Drive |
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
| 18 | Timeouts | done: every Google Drive call has a 20 s timeout; lazy restore waits at most ~15 s per tab |
| 19 | Exponential Backoff | done: Drive calls retry 429/5xx/network 3 times (1 s, 2 s, 4 s + jitter, honours Retry-After), then a plain message; 400s never retried (tests) |
| 20 | Idempotency | done: restoring a backup (file or Drive) twice never makes doubles; Drive uploads only when the content hash changed |
| 21 | Circuit Breakers | done: after 4 failed tries the hourly Drive job stops and waits for the next hour (no retry storm) |
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
| 34 | Principle of Least Privilege | done: tabs, tabGroups, alarms, storage, unlimitedStorage; downloads and identity optional (asked only when a Pro user switches that feature on); no host permissions |
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
| 74 | Data Privacy (GDPR) | done: data stays on the device; optional Drive backup goes only to the user's own Drive (hidden folder), never to us; Limited Use statement in the privacy policy |
| 75 | Accessibility | manual |
| 76 | Mobile Responsiveness | manual |
| 77 | Performance Budgets | auto: PASS |
| 78 | Technical Debt | manual |
| 79 | Reading Documentation | manual |
| 80 | Reading Error Messages | manual |
| 81 | Content Security Policy | manual |
| 82 | Security Headers | manual |
| 83 | Clickjacking | manual |
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
| 98 | API Keys | done: no API keys; Google OAuth client id is a public build setting (WXT_GOOGLE_CLIENT_ID) |
| 99 | Token Expiration and Refresh | done: Google token is held by Chrome (identity API); a 401 drops it and gets a fresh one once, then asks the user to reconnect |
| 100 | Cookie Flags (HttpOnly, Secure, SameSite) | manual |
| 101 | Secret Rotation | not relevant: the OAuth client id is public by design; no secrets in the extension |
| 102 | Audit Logs | manual |
| 103 | Encryption at Rest | manual |
| 104 | Encryption in Transit | auto: PASS |
| 105 | Hashing vs Encryption | manual |
| 106 | Salting | manual |
| 107 | Penetration Testing | manual |

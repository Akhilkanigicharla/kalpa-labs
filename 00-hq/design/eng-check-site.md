# Engineering checks: hq-site

Standard: `00-hq/design/ENGINEERING-CHECKS.md` (107) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).
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
| XSS sinks (innerHTML/eval with variables) | PASS | reviewed: app.js: i18n text from our own dictionary + constant markup |
| Rate Limiting: 00-hq/site/netlify/functions/chat.mjs | PASS | webhook: platform-signed, rate set by sender |
| Input caps: 00-hq/site/netlify/functions/chat.mjs | PASS | no input length cap |
| Performance Budgets (page + JS < 250 KB) | PASS | index.html: 118 KB |

## All 107 items (fill: done / not relevant + why / missing + roadmap id)

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

# Engineering checks: extension-site

Standard: `00-hq/design/ENGINEERING-CHECKS.md` (107) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).
Machine rows come from `python3 00-hq/tools/eng_check.py extension-site --md`; the rest are filled by hand.

## Automatic checks

| Check | Result | Note |
|---|---|---|
| Security Headers: Strict-Transport-Security | WARN | missing in page meta |
| Security Headers: X-Content-Type-Options | WARN | missing in page meta |
| Security Headers: Referrer-Policy | PASS | in page meta |
| Security Headers: Permissions-Policy | WARN | missing in page meta |
| Content Security Policy | PASS | default-src 'self'; script-src 'self'; style-src 'self' 'uns |
| Clickjacking | WARN | GitHub Pages can't send this header; needs a host with headers |
| Inline JS vs CSP | PASS | none |
| Inline on*= handlers | PASS |  |
| Custom 404 page | PASS |  |
| target=_blank has rel=noopener | PASS |  |
| Encryption in Transit (no http:// links) | PASS |  |
| Secrets Management (no keys in browser code) | PASS |  |
| XSS sinks (innerHTML/eval with variables) | PASS |  |
| Performance Budgets (page + JS < 250 KB) | PASS | privacy.html: 11 KB |

## All 107 items (fill: done / not relevant + why / missing + roadmap id)

| # | Item | Status |
|---|---|---|
| 1 | Load Balancing | not relevant: static pages on GitHub Pages, no server code |
| 2 | Rate Limiting | not relevant: no forms or API |
| 3 | Environment Variables | done: CONTACT_EMAIL comes from a build setting, not the code |
| 4 | Secrets Management | auto: PASS |
| 5 | Authentication | not relevant: no logins |
| 6 | Authorization | not relevant: no logins |
| 7 | Input Validation | not relevant: no input on the site |
| 8 | HTTP Status Codes | done: GitHub Pages serves 200/404; custom 404 page |
| 9 | Error Handling | done: custom 404 with links home |
| 10 | Automated Testing | done: site test (390 + 1280 px, light + dark), SEO test, tap sweep in CI |
| 11 | Database Indexing | not relevant: static pages on GitHub Pages, no server code |
| 12 | Database Migrations | not relevant: static pages on GitHub Pages, no server code |
| 13 | Backups | done: site source in git; rebuilt by the workflow |
| 14 | Caching | done: GitHub Pages caching |
| 15 | CDNs | done: GitHub Pages CDN |
| 16 | Logging | not relevant: no analytics by design (privacy) |
| 17 | Monitoring | missing: no uptime check on this URL yet (A61) |
| 18 | Timeouts | not relevant: static pages on GitHub Pages, no server code |
| 19 | Exponential Backoff | not relevant: static pages on GitHub Pages, no server code |
| 20 | Idempotency | not relevant: static pages on GitHub Pages, no server code |
| 21 | Circuit Breakers | not relevant: static pages on GitHub Pages, no server code |
| 22 | Reverse Proxies | not relevant: static pages on GitHub Pages, no server code |
| 23 | API Gateways | not relevant: static pages on GitHub Pages, no server code |
| 24 | Docker | not relevant: static build |
| 25 | CI/CD | done: extension-site workflow builds and publishes; quality CI runs tests |
| 26 | Message Queues | not relevant: static pages on GitHub Pages, no server code |
| 27 | HTTPS / TLS | done: HTTPS only (GitHub Pages) |
| 28 | Session Management | not relevant: static pages on GitHub Pages, no server code |
| 29 | Two-Factor Authentication | not relevant: no logins |
| 30 | SQL Injection | not relevant: no database |
| 31 | XSS (Cross-Site Scripting) | done: no scripts at all on the site (CSP script-src 'self', zero <script>) |
| 32 | CSRF | not relevant: no forms |
| 33 | Dependency Vulnerabilities | done: build has no runtime dependencies |
| 34 | Principle of Least Privilege | done: workflow uses read-only + pages permissions |
| 35 | Race Conditions | not relevant: static pages on GitHub Pages, no server code |
| 36 | Connection Pooling | not relevant: static pages on GitHub Pages, no server code |
| 37 | Database Normalization | not relevant: static pages on GitHub Pages, no server code |
| 38 | Soft Deletes | not relevant: static pages on GitHub Pages, no server code |
| 39 | Data Validation on the Server | not relevant: static pages on GitHub Pages, no server code |
| 40 | File Upload Security | not relevant: static pages on GitHub Pages, no server code |
| 41 | Webhooks | not relevant: static pages on GitHub Pages, no server code |
| 42 | Background Jobs | not relevant: static pages on GitHub Pages, no server code |
| 43 | Cron Jobs | not relevant: static pages on GitHub Pages, no server code |
| 44 | Cache Invalidation | not relevant: static pages on GitHub Pages, no server code |
| 45 | Read Replicas | not relevant: static pages on GitHub Pages, no server code |
| 46 | Horizontal vs Vertical Scaling | not relevant: static pages on GitHub Pages, no server code |
| 47 | Stateless Services | not relevant: static pages on GitHub Pages, no server code |
| 48 | Health Checks | done: tap sweep + SEO test can be run on the live URL after each deploy |
| 49 | Graceful Shutdown | not relevant: static pages on GitHub Pages, no server code |
| 50 | Alerting | not relevant: static pages on GitHub Pages, no server code |
| 51 | Distributed Tracing | not relevant: static pages on GitHub Pages, no server code |
| 52 | Structured Logging | not relevant: static pages on GitHub Pages, no server code |
| 53 | Error Tracking | not relevant: no scripts to error |
| 54 | Uptime Monitoring | missing: no scheduled uptime check (A61) |
| 55 | Feature Flags | not relevant: static pages on GitHub Pages, no server code |
| 56 | Staging Environments | done: built and tested locally (_dist) before publish |
| 57 | Infrastructure as Code | not relevant: static pages on GitHub Pages, no server code |
| 58 | Code Review | done: diff reviewed before tick |
| 59 | Branching Strategies | done: main branch + workflow dispatch |
| 60 | Semantic Versioning | done: site versioned with the extension |
| 61 | API Versioning | not relevant: static pages on GitHub Pages, no server code |
| 62 | API Documentation | done: switch guides + FAQ |
| 63 | Unit vs Integration vs End-to-End Tests | done: page tests + tap sweep |
| 64 | Load Testing | not relevant: static pages on GitHub Pages, no server code |
| 65 | Debugging | not relevant: static pages on GitHub Pages, no server code |
| 66 | Profiling | not relevant: static pages on GitHub Pages, no server code |
| 67 | Time Zones | not relevant: no times shown |
| 68 | Character Encoding | done: UTF-8, Telugu/emoji safe |
| 69 | Concurrency | not relevant: static |
| 70 | Async / Await | not relevant: no scripts |
| 71 | Memory Leaks | not relevant: no scripts |
| 72 | Cost Monitoring | not relevant: static pages on GitHub Pages, no server code |
| 73 | Disaster Recovery | not relevant: static pages on GitHub Pages, no server code |
| 74 | Data Privacy (GDPR) | done: privacy page, no cookies, no analytics |
| 75 | Accessibility | done: one H1, alt text, focus styles, 44 px links (tap sweep 12 Nov 2026) |
| 76 | Mobile Responsiveness | done: tap sweep at 390 px light + dark, every page |
| 77 | Performance Budgets | auto: PASS |
| 78 | Technical Debt | done: gaps listed with ids |
| 79 | Reading Documentation | not relevant: static pages on GitHub Pages, no server code |
| 80 | Reading Error Messages | not relevant: no runtime errors |
| 81 | Content Security Policy | auto: PASS |
| 82 | Security Headers | auto: WARN |
| 83 | Clickjacking | auto: WARN |
| 84 | SSRF | not relevant: static pages on GitHub Pages, no server code |
| 85 | Open Redirects | not relevant: no redirects |
| 86 | Path Traversal | not relevant: no file handling |
| 87 | Command Injection | not relevant: static pages on GitHub Pages, no server code |
| 88 | Mass Assignment | not relevant: static pages on GitHub Pages, no server code |
| 89 | IDOR | not relevant: static pages on GitHub Pages, no server code |
| 90 | Brute Force Protection | not relevant: static pages on GitHub Pages, no server code |
| 91 | Account Lockout | not relevant: static pages on GitHub Pages, no server code |
| 92 | Password Reset Flows | not relevant: static pages on GitHub Pages, no server code |
| 93 | Magic Links | not relevant: static pages on GitHub Pages, no server code |
| 94 | Passkeys | not relevant: static pages on GitHub Pages, no server code |
| 95 | Single Sign-On (SSO) | not relevant: static pages on GitHub Pages, no server code |
| 96 | Role-Based Access Control | not relevant: static pages on GitHub Pages, no server code |
| 97 | Row-Level Security | not relevant: static pages on GitHub Pages, no server code |
| 98 | API Keys | not relevant: static pages on GitHub Pages, no server code |
| 99 | Token Expiration and Refresh | not relevant: static pages on GitHub Pages, no server code |
| 100 | Cookie Flags (HttpOnly, Secure, SameSite) | not relevant: static pages on GitHub Pages, no server code |
| 101 | Secret Rotation | not relevant: static pages on GitHub Pages, no server code |
| 102 | Audit Logs | not relevant: static pages on GitHub Pages, no server code |
| 103 | Encryption at Rest | not relevant: static pages on GitHub Pages, no server code |
| 104 | Encryption in Transit | auto: PASS |
| 105 | Hashing vs Encryption | not relevant: static pages on GitHub Pages, no server code |
| 106 | Salting | not relevant: static pages on GitHub Pages, no server code |
| 107 | Penetration Testing | done: no inputs, no scripts, no cookies: nothing to attack beyond the host |

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
| 1 | Load Balancing | not relevant: no server, accounts or database; everything runs in the user's own Chrome |
| 2 | Rate Limiting | not relevant: no API to call; messages only come from the extension's own pages |
| 3 | Environment Variables | not relevant: no keys or settings outside the package |
| 4 | Secrets Management | auto: PASS |
| 5 | Authentication | not relevant: no accounts by design (privacy promise) |
| 6 | Authorization | not relevant: no accounts; Chrome isolates each profile |
| 7 | Input Validation | done: importers keep only http(s) for restore/links, 5 MB import and 50 MB backup caps, unknown files refused with a plain message (tests) |
| 8 | HTTP Status Codes | not relevant: no HTTP API |
| 9 | Error Handling | done: every message returns {ok,error}, UI shows plain words, never throws (UX pattern 20); restore keeps going if a tab fails |
| 10 | Automated Testing | done: 42 unit tests + real-Chrome e2e (save, restore, groups, lazy restore, reminder) in CI |
| 11 | Database Indexing | done: IndexedDB store keyed by id, list sorted by time; 10,000-tab backup parses in <1 s (test) |
| 12 | Database Migrations | done: backup file has format + version; newer versions refused politely (backup.test) |
| 13 | Backups | done: automatic snapshots every 5 min + free backup file + reminder after 7 days (12 Nov 2026) |
| 14 | Caching | not relevant: nothing fetched from the network |
| 15 | CDNs | not relevant: nothing downloaded at run time; Chrome Web Store delivers the package |
| 16 | Logging | not relevant: no telemetry by design (privacy policy says no analytics); errors shown to the user |
| 17 | Monitoring | not relevant: nothing remote to monitor; store reviews and support email are the signal |
| 18 | Timeouts | done: lazy restore waits at most ~15 s per tab, then leaves it awake |
| 19 | Exponential Backoff | not relevant: no network calls |
| 20 | Idempotency | done: restoring the same backup twice never makes doubles (test) |
| 21 | Circuit Breakers | not relevant: no remote services |
| 22 | Reverse Proxies | not relevant: no server, accounts or database; everything runs in the user's own Chrome |
| 23 | API Gateways | not relevant: no server, accounts or database; everything runs in the user's own Chrome |
| 24 | Docker | not relevant: browser extension, built by wxt in CI |
| 25 | CI/CD | done: Kalpa quality workflow (compile, lint, tests, e2e) on every push |
| 26 | Message Queues | not relevant: alarms do the background work |
| 27 | HTTPS / TLS | not relevant: no network traffic |
| 28 | Session Management | not relevant: no logins |
| 29 | Two-Factor Authentication | not relevant: no accounts |
| 30 | SQL Injection | not relevant: no SQL; IndexedDB |
| 31 | XSS (Cross-Site Scripting) | done: all text set with textContent, no innerHTML with data; javascript:/file:/data: addresses never become links (fixed 12 Nov 2026) or reopen |
| 32 | CSRF | not relevant: no server, no cookies |
| 33 | Dependency Vulnerabilities | done: npm audit 0 vulnerabilities (12 Nov 2026), CI job |
| 34 | Principle of Least Privilege | done: tabs, tabGroups, alarms, storage, unlimitedStorage only; downloads optional (Pro, asked when switched on); no host permissions |
| 35 | Race Conditions | done: import preview debounced 250 ms; IndexedDB transactions; restore waits for each sleeping tab before grouping |
| 36 | Connection Pooling | not relevant: no server, accounts or database; everything runs in the user's own Chrome |
| 37 | Database Normalization | done: one session record = windows > tabs > groups |
| 38 | Soft Deletes | missing: delete asks to confirm but has no undo (A231) |
| 39 | Data Validation on the Server | done: same checks run in the background, not just in the page |
| 40 | File Upload Security | done: OneTab/Session Buddy/backup files: size caps, parsed as text/JSON only, never run; worst-case test (emoji, Telugu, RTL, 3,000-char title, HTML) |
| 41 | Webhooks | not relevant: no webhooks |
| 42 | Background Jobs | done: snapshot alarm (5 min) and Pro daily backup alarm |
| 43 | Cron Jobs | done: chrome.alarms, survives worker restarts |
| 44 | Cache Invalidation | not relevant: no cache |
| 45 | Read Replicas | not relevant: no server, accounts or database; everything runs in the user's own Chrome |
| 46 | Horizontal vs Vertical Scaling | not relevant: no server, accounts or database; everything runs in the user's own Chrome |
| 47 | Stateless Services | done: service worker keeps no state in memory; everything in storage |
| 48 | Health Checks | not relevant: no service |
| 49 | Graceful Shutdown | done: alarms re-created on install and startup; work is per-message |
| 50 | Alerting | not relevant: nothing remote |
| 51 | Distributed Tracing | not relevant: no server, accounts or database; everything runs in the user's own Chrome |
| 52 | Structured Logging | not relevant: no logs by design |
| 53 | Error Tracking | not relevant: no error reporting (privacy); users report by email |
| 54 | Uptime Monitoring | not relevant: nothing hosted (site row covers the site) |
| 55 | Feature Flags | done: plan flag (free/pro) gates Pro tools |
| 56 | Staging Environments | done: unpacked build tested in real Chrome 153 + 156 and on GitHub before any store upload |
| 57 | Infrastructure as Code | not relevant: no infrastructure |
| 58 | Code Review | done: diff reviewed before each tick (Ponytail review) + CI |
| 59 | Branching Strategies | done: main + short probe branches (probe/lazy-restore) |
| 60 | Semantic Versioning | done: 0.1.0 live; next upload 0.1.1 |
| 61 | API Versioning | not relevant: no API |
| 62 | API Documentation | done: README + store listing + site guides |
| 63 | Unit vs Integration vs End-to-End Tests | done: unit (vitest) + end-to-end (Playwright, real Chrome) |
| 64 | Load Testing | done: 1,000- and 10,000-tab files tested for speed |
| 65 | Debugging | done: crash found and traced (Chrome 153 SIGSEGV on discard) on 12 Nov 2026 |
| 66 | Profiling | done: restore timing printed in e2e (20 tabs in ~1 s) |
| 67 | Time Zones | done: file names in IST, stamps in the user's local time |
| 68 | Character Encoding | done: UTF-8 everywhere; emoji, Telugu, Hindi, Arabic kept exactly (test) |
| 69 | Concurrency | done: at most 6 tabs load at once in a big restore |
| 70 | Async / Await | done: async/await with errors caught per message |
| 71 | Memory Leaks | done: object URLs revoked after 10 s; big sessions restore asleep on Chrome 156+ |
| 72 | Cost Monitoring | not relevant: no paid services |
| 73 | Disaster Recovery | done: backup file restores everything on a new computer (e2e round trip) |
| 74 | Data Privacy (GDPR) | done: data stays on the device, no incognito ever saved, privacy policy + store privacy form |
| 75 | Accessibility | done: labels, roles, status regions, 44 px buttons, light + dark checked |
| 76 | Mobile Responsiveness | not relevant: Chrome extensions don't run on phones; popup and options checked at 390 px anyway |
| 77 | Performance Budgets | auto: PASS |
| 78 | Technical Debt | done: known gaps listed here with roadmap ids |
| 79 | Reading Documentation | done: Chrome API docs read for discard, groups, alarms |
| 80 | Reading Error Messages | done: errors shown in plain English to users |
| 81 | Content Security Policy | done: Manifest V3 default policy (script-src 'self'), no remote code |
| 82 | Security Headers | not relevant: extension pages are not served over HTTP |
| 83 | Clickjacking | done: no web_accessible_resources, so no site can frame the extension |
| 84 | SSRF | not relevant: no server fetches |
| 85 | Open Redirects | not relevant: no redirects |
| 86 | Path Traversal | not relevant: no file system paths |
| 87 | Command Injection | not relevant: no shell |
| 88 | Mass Assignment | done: imported fields are copied one by one, never spread into records |
| 89 | IDOR | not relevant: one user per profile |
| 90 | Brute Force Protection | not relevant: no logins |
| 91 | Account Lockout | not relevant: no logins |
| 92 | Password Reset Flows | not relevant: no passwords |
| 93 | Magic Links | not relevant: no logins |
| 94 | Passkeys | not relevant: no logins |
| 95 | Single Sign-On (SSO) | not relevant: no logins |
| 96 | Role-Based Access Control | not relevant: one user |
| 97 | Row-Level Security | not relevant: no shared database |
| 98 | API Keys | not relevant: no API keys in the extension (Pro licence later goes through the payment company, C54) |
| 99 | Token Expiration and Refresh | not relevant: no tokens |
| 100 | Cookie Flags (HttpOnly, Secure, SameSite) | not relevant: no cookies |
| 101 | Secret Rotation | not relevant: no secrets |
| 102 | Audit Logs | not relevant: single user; sessions keep their created time |
| 103 | Encryption at Rest | not relevant: tab lists sit in the user's own Chrome profile (protected by their OS login/disk encryption) |
| 104 | Encryption in Transit | auto: PASS |
| 105 | Hashing vs Encryption | not relevant: no passwords |
| 106 | Salting | not relevant: no passwords |
| 107 | Penetration Testing | done: hostile-input tests (javascript:, file:, data:, HTML in titles, huge files); no third-party pentest needed for a local-only tool |

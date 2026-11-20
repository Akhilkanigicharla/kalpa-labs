# Engineering checks: trading

Standard: `00-hq/design/ENGINEERING-CHECKS.md` (113) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).
Machine rows come from `python3 00-hq/tools/eng_check.py trading --md`; the rest are filled by hand.

## Automatic checks

| Check | Result | Note |
|---|---|---|
| Secrets Management (no keys in code) | PASS | keys only from environment / GitHub secrets |
| Timeouts (every HTTP call has timeout=) | PASS |  |
| Pagination + Limits (every list read has limit=) | PASS | no unbounded list reads |

## All 113 items (fill: done / not relevant + why / missing + roadmap id)

| # | Item | Status |
|---|---|---|
| 1 | Load Balancing | manual |
| 2 | Rate Limiting | manual |
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
| 77 | Performance Budgets | manual |
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
| 98 | API Keys | manual |
| 99 | Token Expiration and Refresh | manual |
| 100 | Cookie Flags (HttpOnly, Secure, SameSite) | manual |
| 101 | Secret Rotation | manual |
| 102 | Audit Logs | manual |
| 103 | Encryption at Rest | manual |
| 104 | Encryption in Transit | manual |
| 105 | Hashing vs Encryption | manual |
| 106 | Salting | manual |
| 107 | Penetration Testing | manual |
| 108 | Multiple Servers / Redundancy | not relevant: runs as scheduled GitHub Actions jobs; a failed run is re-run next day and the KILL switch stops trading |
| 109 | Auto Scaling | not relevant: no live traffic |
| 110 | Sharding | not relevant: price history in files |
| 111 | Pagination + Limits | done: no database list reads (eng_check 111 PASS) |
| 112 | Failover | done: Yahoo data errors skip the market for the day (strict=False) instead of trading on bad data |
| 113 | Graceful Degradation | done: each paper step has continue-on-error, so one failing strategy never stops the others (paper-trade.yml) |

## A242 engine flow: paper-trade monitor + loss-cap guard (`00-hq/agent-engine/flows/b7-paper-monitor.json`, 20 Nov 2026)
| Check | Status |
|---|---|
| Money safety | done: watch only, no order, broker or Dhan call anywhere in the file (test); any ledger row not in `paper` mode raises a 🚨 line |
| Limits drift | done: each track carries the bot's own limits read from `risk.py` at build time (Track A: day/week/month caps off, 20% pause); the test re-reads `risk.py` and fails on any drift |
| Stop-loss / caps | done: open position without a stop-loss, pot over the ₹10,000 hard max, positions costing more than the pot, cash below ₹0, broken quantities all raise ⛔ |
| Input validation | done: state JSON shape checked, marks with bad dates / NaN skipped, quoted CSV parsed, 2 MB state / 5 MB ledger limits, 20,000-row ledger tested |
| Prompt injection / escaping | done: no model; symbols must match `[A-Z0-9&_-]`, other text HTML-escaped, control/bidi chars stripped (test) |
| Timeouts / retries / outage | done: 10 s timeout, 3 tries 5 s apart; a missing or broken file becomes a ⛔ line, not a crash; stale runs (> 4 days) flagged |
| Spam control | done: quiet when all is well, one "all OK" line on Fridays, same alert not repeated for 7 days, store pruned at 40 days, message under 4,096 chars |
| Secrets / public URL | not relevant: public repo GETs only, no keys; schedule only, `active: false`, private Telegram to Akhil |

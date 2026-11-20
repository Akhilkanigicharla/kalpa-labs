# Engineering checks: finops

Standard: `00-hq/design/ENGINEERING-CHECKS.md` (113) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).
Machine rows come from `python3 00-hq/tools/eng_check.py finops --md`; the rest are filled by hand.

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
| 108 | Multiple Servers / Redundancy | not relevant until hosted: the API is not deployed yet; the LiteLLM callback runs inside the client's own stack |
| 109 | Auto Scaling | not relevant until hosted |
| 110 | Sharding | not relevant at this size: usage events keyed by tenant; revisit above ~10 lakh rows |
| 111 | Pagination + Limits | done: price pass reads usage events in limited pages (limit=); store calls time out (8 s, 20 Nov) |
| 112 | Failover | not relevant: no AI calls in the API itself |
| 113 | Graceful Degradation | done: browser calls catch errors (eng_check 113 on the site) |

## A242 engine flow: X-ray intake + 14-day purge (`00-hq/agent-engine/flows/b6-xray-intake.json`, 20 Nov 2026)
| Check | Status |
|---|---|
| Data retention (DPDP) | done: daily `purge_xray_intake()` RPC; flow also lists stored rows and raises ⛔ if any row is past `delete_after` or keeps data >14 days, or if the purge fails (`test_b6_xray_intake.js`) |
| Personal data | done: the work email is never selected or shown; emails/phones inside an upload are flagged for hashing (LP_HASH_SALT) before the X-ray |
| Prompts / replies | done: same banned column list as `intake.js`; a stored file with a prompt/reply column is flagged "delete this row now" and its text is never shown |
| Input validation | done: uuid ids only, CSV (quoted fields) / JSON / JSONL parsed defensively, empty / broken / 1-column files reported, 20,000-row file in under 2 s |
| Prompt injection | done: no model call; upload text is counted, never echoed |
| Output escaping | done: HTML-escaped, control/bidi chars stripped, names cut at 60 whole characters (emoji test), quotes removed inside the generate.py command |
| Secrets | done: Supabase service key only in the n8n credential "Ledger Peaks Supabase (service)" that Akhil sets; no key in the file (test) |
| Timeouts / retries / outage | done: 10 s timeout, 3 tries 5 s apart, errors become ⛔ lines instead of a crash |
| Spam control | done: one message a day max, silent on quiet days, each request announced once + one "due in <24 h" reminder, 5 drafts a run, seen store pruned at 20 days |
| Public URL | not relevant: schedule only, `active: false`, private Telegram to Akhil; nothing goes to the client |

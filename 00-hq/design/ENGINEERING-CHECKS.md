# Engineering checks (from Akhil's reel, 12 Nov 2026)

107 items from the "Who's gonna tell vibe coders about..." reel (screenshots in `checklists/engineering-reel-*.png`).
Every Kalpa page and service is checked against this list, plus `UX-PATTERNS.md` (20) and `SEO-CHECKS.md` (20).
Status is for the public site (`00-hq/site`). Items that only matter where there are logins or a database name the world they apply to.

| # | Item | What we do on the site | Status |
|---|---|---|---|
| 1 | Load Balancing | Netlify/Render do it for us | platform |
| 2 | Rate Limiting | chat: 12 msgs/min per visitor (429) | done |
| 3 | Environment Variables | keys only in Netlify env | done |
| 4 | Secrets Management | GitHub/Netlify secrets set by Akhil | done |
| 5 | Authentication | no logins on the public site | n/a site; BotBhai owner app |
| 6 | Authorization | - | n/a site; BotBhai owner app |
| 7 | Input Validation | form + chat check length, phone, name | done |
| 8 | HTTP Status Codes | chat returns 400/405/413/429/503 | done |
| 9 | Error Handling | form "details are safe" + Try again | done |
| 10 | Automated Testing | tap sweep, SEO, form, chat tests | done |
| 11 | Database Indexing | - | BotBhai / JobCard |
| 12 | Database Migrations | - | BotBhai / JobCard |
| 13 | Backups | - | BotBhai / JobCard |
| 14 | Caching | fonts cached 1 year | done |
| 15 | CDNs | Netlify edge | platform |
| 16 | Logging | - | chat fn logs to Netlify |
| 17 | Monitoring | - | daily scheduled check |
| 18 | Timeouts | model calls stop after 20 s | done |
| 19 | Exponential Backoff | chat retries 1 s, 2 s + jitter; 429 not retried | done |
| 20 | Idempotency | form double-tap guard | check |
| 21 | Circuit Breakers | falls to next free model | done |
| 22 | Reverse Proxies | platform | platform |
| 23 | API Gateways | platform | platform |
| 24 | Docker | n8n on Render | n8n |
| 25 | CI/CD | GitHub Actions | done |
| 26 | Message Queues | KL Tasks table | n8n |
| 27 | HTTPS / TLS | HSTS header | done |
| 28 | Session Management | - | BotBhai owner app |
| 29 | Two-Factor Authentication | - | Akhil's accounts |
| 30 | SQL Injection | no SQL on site | BotBhai |
| 31 | XSS (Cross-Site Scripting) | textContent only; 404 hostile-address test | done |
| 32 | CSRF | - | n/a no cookies on site |
| 33 | Dependency Vulnerabilities | site has 0 dependencies | done |
| 34 | Principle of Least Privilege | - | all worlds |
| 35 | Race Conditions | - | BotBhai bookings |
| 36 | Connection Pooling | - | BotBhai |
| 37 | Database Normalization | - | BotBhai |
| 38 | Soft Deletes | - | BotBhai |
| 39 | Data Validation on the Server | chat fn re-checks lead fields, caps text at 1,000 | done |
| 40 | File Upload Security | no uploads on site | JobCard |
| 41 | Webhooks | - | BotBhai WhatsApp |
| 42 | Background Jobs | - | n8n |
| 43 | Cron Jobs | - | GitHub Actions |
| 44 | Cache Invalidation | app.js?v=<hash>, checked by test_assets.py | done |
| 45 | Read Replicas | - | later |
| 46 | Horizontal vs Vertical Scaling | - | later |
| 47 | Stateless Services | chat fn keeps no state | done |
| 48 | Health Checks | - | daily scheduled check |
| 49 | Graceful Shutdown | - | n8n |
| 50 | Alerting | - | Telegram 9 PM |
| 51 | Distributed Tracing | - | later |
| 52 | Structured Logging | chat fn: one JSON line per request, no text or IP | done |
| 53 | Error Tracking | - | fix: window.onerror beacon |
| 54 | Uptime Monitoring | - | scheduled check |
| 55 | Feature Flags | - | later |
| 56 | Staging Environments | Netlify deploy preview | check |
| 57 | Infrastructure as Code | netlify.toml, workflows | done |
| 58 | Code Review | ponytail-review | done |
| 59 | Branching Strategies | main + lanes | done |
| 60 | Semantic Versioning | extension 0.1.0 | done |
| 61 | API Versioning | - | later |
| 62 | API Documentation | - | later |
| 63 | Unit vs Integration vs End-to-End Tests | unit + browser tests | done |
| 64 | Load Testing | - | fix: chat fn load test |
| 65 | Debugging | systematic-debugging skill | done |
| 66 | Profiling | - | fix: page weight check |
| 67 | Time Zones | IST shown | check |
| 68 | Character Encoding | UTF-8, Telugu text | done |
| 69 | Concurrency | - | BotBhai |
| 70 | Async / Await | - | done |
| 71 | Memory Leaks | one animation loop, pauses off-screen | done |
| 72 | Cost Monitoring | free tiers, tokens.csv | done |
| 73 | Disaster Recovery | code in GitHub | check |
| 74 | Data Privacy (GDPR) | DPDP privacy notice | done |
| 75 | Accessibility | keyboard, labels, 44 px taps | done |
| 76 | Mobile Responsiveness | 390 px tests | done |
| 77 | Performance Budgets | index + app.js under 160 KB (test) | done |
| 78 | Technical Debt | - | ongoing |
| 79 | Reading Documentation | - | habit |
| 80 | Reading Error Messages | - | habit |
| 81 | Content Security Policy | script-src 'self', tested with the header on | done |
| 82 | Security Headers | + X-Frame-Options, Permissions-Policy, COOP | done |
| 83 | Clickjacking | frame-ancestors 'none' + DENY | done |
| 84 | SSRF | chat fn calls fixed hosts only | done |
| 85 | Open Redirects | no redirect params | done |
| 86 | Path Traversal | no file paths from users | done |
| 87 | Command Injection | no shell from users | done |
| 88 | Mass Assignment | lead fields whitelisted | done |
| 89 | IDOR | - | BotBhai owner app |
| 90 | Brute Force Protection | - | BotBhai owner app |
| 91 | Account Lockout | - | BotBhai owner app |
| 92 | Password Reset Flows | - | BotBhai owner app |
| 93 | Magic Links | - | BotBhai owner app |
| 94 | Passkeys | - | later |
| 95 | Single Sign-On (SSO) | - | later |
| 96 | Role-Based Access Control | - | BotBhai owner app |
| 97 | Row-Level Security | - | Supabase tables |
| 98 | API Keys | server only | done |
| 99 | Token Expiration and Refresh | - | BotBhai owner app |
| 100 | Cookie Flags (HttpOnly, Secure, SameSite) | site sets no cookies | done |
| 101 | Secret Rotation | - | Akhil, every 90 days |
| 102 | Audit Logs | - | BotBhai owner app |
| 103 | Encryption at Rest | - | Supabase default |
| 104 | Encryption in Transit | HTTPS | done |
| 105 | Hashing vs Encryption | - | BotBhai owner app |
| 106 | Salting | - | BotBhai owner app |
| 107 | Penetration Testing | - | fix: A205 scan |

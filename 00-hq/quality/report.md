# Kalpa engineering audit

Static scan by `00-hq/quality/eng_audit.py` against `ENGINEERING-CHECKLIST.md`. CRITICAL fails CI; the rest is the fix list. Waive a line with `# eng-audit: ok <reason>`.

| World | CRITICAL | HIGH | MEDIUM | INFO |
|---|---|---|---|---|
| 00-hq | 0 | 0 | 0 | 2 |
| b1 01-botbhai | 0 | 0 | 0 | 2 |
| b2 02-jobcard | 0 | 0 | 0 | 0 |
| b3 03-kits | 0 | 0 | 0 | 0 |
| b4 04-extensions | 0 | 0 | 0 | 0 |
| b5 05-deals | 0 | 0 | 0 | 0 |
| b6 06-finops | 0 | 0 | 0 | 1 |
| b7 07-trading | 0 | 0 | 0 | 0 |
| **All** | **0** | **0** | **0** | **5** |

Waived: 1.

## 00-hq

**INFO** (2)

- `DEPS-BOT` .github: No .github/dependabot.yml (free weekly dependency-update PRs). Fix: Add Dependabot for npm, pip and github-actions.
- `TESTS-NOT-IN-CI` 00-hq: 1 of 22 test files may not run in CI, e.g. 00-hq/site/tests/chat.test.mjs. Fix: Wire them into .github/workflows/quality.yml or delete dead tests.

## b1 01-botbhai

**INFO** (2)

- `CORS-ANY` 01-botbhai/botbhai/core/functions/_lib.js:37: Any website may call this endpoint (CORS *). Fix: Fine for public endpoints only; owner endpoints must not use *.
- `CORS-ANY` 01-botbhai/botbhai/core/functions/chat.js:10: Any website may call this endpoint (CORS *). Fix: Fine for public endpoints only; owner endpoints must not use *.

## b6 06-finops

**INFO** (1)

- `TESTS-NOT-IN-CI` 06-finops: 1 of 10 test files may not run in CI, e.g. 06-finops/src/api/ingest.test.js. Fix: Wire them into .github/workflows/quality.yml or delete dead tests.

## Waived

- `XSS-HTML-SINK` 00-hq/site/site.js:53: v comes only from this file's own EN/TE text (data-html elements), never from users


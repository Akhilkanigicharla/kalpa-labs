# cf-runner: always-on backup agent runner (A239)

egm-draft, 19 Nov 2026. Goldfish review notes at the end.

## 1. Problem and goal
Free agents (the KL task queue in `00-hq/tasks/*.json`) run only when GitHub Actions `agents.yml` fires (GitHub cron drops slots: ~5 h lost on 13 Nov) or n8n is awake (Render sleeps, n8n connector 404). Tasks then wait for hours.

Goal: a Cloudflare Worker on the Workers Free plan that, every 30 minutes, picks **one stale `todo` row**, drafts it with a free model, checks it with a second free model (Vigil), and commits the result to GitHub, exactly like `00-hq/agents/runner.py` does. It is a backup, not a second main runner.

Non-goals: no customer data (the queue never holds any), no public URL (no `fetch` handler that does work), no paid model, no memory/autoresearch/web-reach extras of runner.py (those stay in GitHub Actions).

## 2. Technical plan
- **Trigger:** one Cron Trigger `5,35 * * * *` (between cf-timer's :20/:50 GitHub dispatches, so the two never race on the same minute). With cf-timer's 3 crons this uses 4 of the 5 free cron triggers.
- **Stale only:** a row qualifies when `status == "todo"` and its `updated` (else `created`) is older than `STALE_MIN` (default 90 min). Fresh rows are left to GitHub Actions; the Worker only catches what GitHub missed.
- **All worlds per run:** the 9 queue files are read at the same pinned commit (9 subrequests; a run uses about 20 of the 50 allowed on Workers Free), and the oldest stale row wins.
- **Pick:** same order as runner.py `pick`: priority P0 < P1 < P2, then oldest `created`.
- **Context:** up to 3 `read` files fetched raw from GitHub `main`, total capped at 7,000 characters (Groq free 413 limit, same as runner.py).
- **Models:** same free list as runner.py (Groq gpt-oss-120b/20b, OpenRouter free, Gemini free); Vigil uses a different provider. Each call: 60 s timeout (AbortController), one retry after a 429 (wait `RETRY_MS`, default 20 s), `finish_reason == "length"` or empty or unclosed `<think>` → next model. Keys never logged.
- **Same rules text** as runner.py (`RULES`), copied; a test checks the two copies match.
- **Result:** PASS → `00-hq/knowledge/<id>.md` (same header line as runner.py) + row `status: "review"`, `output`; FIX → `tries+1`, `vigil_notes`, `todo` or `rejected` at 3 tries; no model answered → `last_error`, no try used.
- **Atomic commit:** GitHub Git Data API: read `main` ref → create tree (knowledge file + updated queue file) on that commit → create commit → `PATCH` ref with `force: false`. If `main` moved since the read (GitHub runner or a session pushed), the PATCH fails with 422 and this run writes nothing; the row is retried next run. Never overwrites anyone's work.
- **Commit author:** "Kalpa cf-runner" with the noreply address; message `cf-runner: K### review|todo|rejected`.
- **Secrets (Akhil sets in Cloudflare, never in code):** `GH_TOKEN` fine-grained, Contents: write on kalpa-labs only; `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY` (any subset). With no `GH_TOKEN` the run logs `skip (no GH_TOKEN)` and stops.
- **Kill switch:** var `ENABLED = "1"`; set to `"0"` in wrangler.toml to stop without deleting.

## 3. Alternatives
- **Cloudflare Workflows + Agents SDK** (named in A239): durable steps help multi-hour jobs; one task here takes under 2 minutes of waiting and the next cron retries anything lost, so plain cron is enough and has no extra quota. Kept as the upgrade path if tasks grow longer.
- **Merge into cf-timer:** fewer Workers, but one bug would also stop the n8n pings and dispatches. Kept separate.
- **Contents API PUT per file:** two commits, and a knowledge file could land without its queue update. Git Data API gives one atomic commit.

## 4. Implementation
- `lib.js`: pure functions (`isStale`, `pickTask`, `worldForSlot`, `callModels`, `review`, `applyResult`) + `runOnce(env, now, fetchFn)` ; `worker.js` only exports the `scheduled` handler (workerd treats every named export of the main module as an entrypoint, so exported constants stop the Worker from starting; found in `wrangler dev` 19 Nov and fixed in cf-timer too). `GH_API` var (default `https://api.github.com`) and model base URLs overridable only for the local test.
- `test.mjs`: unit tests with a fake fetch (stale/fresh, priority order, 429 retry, length cut-off, PASS/FIX/rejected, 422 race → no write, no token → skip, rules copy equals runner.py).
- `test-dev.sh`: real `wrangler dev --test-scheduled` run against a local mock of GitHub + model API (`mock.mjs`), proving the Worker runs in workerd and makes the commit calls.
- Live (after C65 + Akhil adds secrets): `wrangler deploy`, then one real task end to end.

## 5. Goldfish review
Fresh no-context reviewer (sub-agent, 19 Nov), 8 findings, how each was handled:
1. BLOCKER queue file read from a different snapshot than the commit base → fixed: all reads use `?ref=<base sha>` of the same ref read.
2. BLOCKER task id becomes a path → fixed: ids must match `^K\d{3,4}$`; `read` paths must be repo-relative, no `..`, no URL (tested).
3. MAJOR one world per run = 4.5 h wait → fixed: all 9 files every run.
4. MAJOR 10 ms CPU → JSON of 9 small files + string building; waiting on fetch does not count. Watch the Cloudflare CPU graph after deploy; open.
5. MAJOR URL overrides could leak keys → fixed: honoured only with `TEST_MODE=1` and a 127.0.0.1/localhost http host; prod wrangler.toml never sets it (tested).
6. MAJOR model output straight to main → status is `review` (needs Akhil/Claude review, same as runner.py), commit says `cf-runner`, task text is passed as data under RULES.
7. MINOR double draft with the GitHub runner → mitigated: only rows untouched for 90 min; the ref check stops a second overwrite. Accepted.
8. MINOR no heartbeat → open: add to the A226 scheduled-tasks health check once deployed.

## 6. Tests
- `node 00-hq/cf-runner/test.mjs` (25 checks, fake GitHub + models in process).
- `bash 00-hq/cf-runner/test-dev.sh` (real workerd via `wrangler dev --test-scheduled`, mock on 127.0.0.1): cron fires, 1 commit, row → review.

## 7. Go live (after C65)
Akhil adds Worker secrets `GH_TOKEN` (fine-grained, Contents: write, kalpa-labs only) and at least one of `GROQ_API_KEY` / `OPENROUTER_API_KEY` / `GEMINI_API_KEY` in the Cloudflare dashboard; then `npx wrangler deploy` in this folder; then one real stale task end to end.

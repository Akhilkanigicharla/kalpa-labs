# Deep scan v2 — b6 Ledger Peaks (AI FinOps & Governance)

*Agent 7 of 8, 2026-10-13. Builds on [a7-finops.md](a7-finops.md); does not repeat its Presidio/LiteLLM notes.*
*Method: GitHub topic pages (llmops, llm-observability, finops, ai-gateway, llm-gateway, pii-detection, ai-governance, compliance-automation, cost-optimization) fetched via WebFetch (the GitHub API and ungh.cc both return 403 today). Star counts come from those pages, which GitHub had cached between Jul and Sep 2026, so treat them as ±10%. "Last commit" and licence were read from `git clone --depth 1` for every repo marked ✔; the clones were deleted afterwards. Other last-commit dates are the topic-page "updated" dates.*

## 1. Top 30 repos by stars (relevant to LLM cost, gateways, observability, PII, governance)

| # | Repo | Stars | Last commit | Licence + caveats | What it is | Verdict |
|---|---|---|---|---|---|---|
| 1 | diegosouzapw/OmniRoute | 62k | 2026-10-11 ✔ | MIT | Gateway to hundreds of providers, many free tiers, quota fallback | AVOID (routes users to free tiers of others; ToS-grey for B2B) |
| 2 | BerriAI/litellm | 58–61k | 2026-10-12 | MIT **except `enterprise/`** (paid licence) | Gateway + 4,459-model price map + spend logs | **ADOPT** price map as cross-check; **INTEGRATE** spend logs as import source |
| 3 | QuantumNous/new-api | 47.4k | 2026-10-12 ✔ | **AGPL-3.0** | Model hub with quota/billing (CNY-oriented) | AVOID code; LEARN its per-key quota ledger |
| 4 | Kong/kong | 44.1k | 2026-09 | Apache-2.0 (Konnect is closed) | API + AI gateway; now owns OpenMeter | COMPETITOR (enterprise metering) |
| 5 | langfuse/langfuse | ~35.7k | 2026-10-12 | MIT core; **`ee/`, `web/src/ee/`, `worker/src/ee/` commercial** | Tracing, per-user cost in USD | **INTEGRATE** (import its exports) |
| 6 | mlflow/mlflow | 27.2k | 2026-07 | Apache-2.0 | ML/LLM platform, tracing, AI gateway | LEARN |
| 7 | promptfoo/promptfoo | 23.6k | 2026-07 | MIT | Prompt tests, red-teaming | LEARN (Art. 50/ISO evidence of testing, later) |
| 8 | comet-ml/opik | 21–22.5k | 2026-08 | Apache-2.0 | Eval + tracing, cost per trace | LEARN / INTEGRATE later |
| 9 | apache/apisix | 17.1k | 2026-09 | Apache-2.0 | API/AI gateway | AVOID (infra, not our layer) |
| 10 | Portkey-AI/gateway | 12.9–13.2k | 2026-05-25 (stale main) | MIT; hosted tier closed | TS gateway + guardrails | LEARN; COMPETITOR (Bengaluru, USD pricing) |
| 11 | infracost/infracost | 12.5k | 2026-09 | Apache-2.0 | Cloud cost in pull requests | **LEARN** (its "cost diff on PR" UX is the model for our PII/cost GitHub Action) |
| 12 | tensorzero/tensorzero | 11.7k | 2026-06-04 ✔ | Apache-2.0 | Gateway + observability + optimisation | LEARN (slowing) |
| 13 | Arize-ai/phoenix | 10.7–11.8k | 2026-10-12 ✔ | **Elastic License 2.0** (source-available, no hosted resale) | Tracing + evals | AVOID code; LEARN |
| 14 | data-privacy-stack/presidio | 10.5–11.3k | 2026-10-08 | MIT | PII detection/anonymisation, has IN_* recognizers | **ADOPT** (built into `src/pii/` today) |
| 15 | higress-group/higress | 9.3k | 2026-09 | Apache-2.0 | AI-native gateway (Alibaba) | AVOID |
| 16 | maximhq/bifrost | 7.8k | 2026-10-13 ✔ | Apache-2.0 (`docs/enterprise` = paid features) | Go gateway with budgets, governance | LEARN; COMPETITOR (budgets in USD) |
| 17 | traceloop/openllmetry | ~7.5k | 2026-10-12 | Apache-2.0 | OTel auto-instrumentation | **ADOPT** (recommend to customers) |
| 18 | mnfst/manifest | 7.4k | 2026-10-09 ✔ | MIT | Agent→provider connector with cost/token tracking | LEARN (watch: fast-growing cost tracker) |
| 19 | opencost/opencost | 6.7k | 2026-09 | Apache-2.0 | K8s cost allocation | AVOID v0 (we price tokens, not pods) |
| 20 | Helicone/helicone | 6–6.2k | 2026-09-16 | Apache-2.0 | Proxy observability, per-user cost headers | LEARN; COMPETITOR (USD) |
| 21 | cloud-custodian/cloud-custodian | 6.1k | 2026-09 | Apache-2.0 | Cloud governance rules engine | LEARN (policy-as-YAML for budget rules) |
| 22 | pydantic/logfire | 4.4k | 2026-08 | SDK MIT; platform closed | OTel observability | LEARN |
| 23 | lemony-ai/cascadeflow | 4k | 2026-09-25 ✔ | MIT | Budget-aware model cascade | LEARN (savings rule "model downgrade") |
| 24 | lmnr-ai/lmnr | 3.1k | 2026-10-11 ✔ | Apache-2.0 | Agent observability | LEARN |
| 25 | openlit/openlit | 2.7–2.8k | 2026-10-09 | Apache-2.0 | OTel-native observability, custom pricing files | LEARN (custom-price file shape) |
| 26 | openmeterio/openmeter | 2.2k | 2026-10-12 ✔ | Apache-2.0 (now Kong) | Usage metering + billing | LEARN; COMPETITOR (enterprise) |
| 27 | hystax/optscale | 2.2k | 2026-09 | Apache-2.0 | Multi-cloud FinOps | AVOID |
| 28 | AgentOps-AI/tokencost | 2k | 2025-09 (stale) | MIT | USD cost via tiktoken | AVOID (genai-prices wins; tried below) |
| 29 | trycompai/comp | ~2k | 2026-10-07 | **AGPL-3.0** | Vanta alternative, ISO 42001 seeds | AVOID code |
| 30 | getprobo/probo | ~1.45k | 2026-10-12 | MIT | Compliance platform, ISO 42001 control-ID JSON | **ADOPT data** (IDs only, with attribution) |

Below 1k but important: **pydantic/genai-prices** (337–390★, MIT, the **chosen price source**), open-telemetry/semantic-conventions (GenAI, Apache-2.0, schema), mozilla-ai/otari (432★, Apache-2.0, gateway with budgets, 2026-10-12 ✔), **verifywise-ai/verifywise** (322★, **BSL 1.1**, AI governance across EU AI Act/ISO 42001 — AVOID code, COMPETITOR), theopenlane/core (279★, Apache-2.0, SOC2/ISO27001 automation — LEARN), awslabs/mcp-server-for-oscal (50★, OSCAL for agents — LEARN for v1 export), Jupitice DPDP OS (closed).

## 2. Competitor map — who already does what

| Capability | Who does it today | INR? | DPDP? | Per-customer margin? |
|---|---|---|---|---|
| LLM cost per user/tag (USD) | Langfuse, Helicone, LiteLLM, Portkey, Opik, Bifrost, Manifest | No | No | Partly (cost per user; no revenue join) |
| AI cost per customer **with margin** | Paid.ai, Revenium, Pay-i, Finout/CloudZero/nOps/Vantage "AI cost" modules (all US, USD, $500+/mo or quote-only) | No | No | **Yes, in USD** |
| Usage metering + billing | OpenMeter/Kong, Orb, Metronome, Stripe meters | Stripe bills INR, but not cost attribution | No | No |
| DPDP compliance | Sprinto, Scrut, Digio, Jupitice DPDP OS, consent managers | n/a | **Yes**, generic (not wired to LLM logs) | No |
| ISO 42001 / EU AI Act | Vanta, Drata, VerifyWise (BSL), Comp AI (AGPL), Probo | n/a | No | No |
| PII scanning of logs | Presidio, LLM Guard, PasteGuard, Ferret-scan | n/a | Not mapped to DPDP | No |

**The gap we own:** nobody joins (a) LLM spend priced in **₹ paise at the RBI reference rate with GST reverse-charge notes**, (b) **per-customer gross margin** from the customer's own revenue CSV, and (c) a **DPDP + ISO 42001 + Art. 50 evidence pack** generated from the same metadata — for seed–Series B Indian teams at ₹2–8k/month. US margin tools (Paid, Revenium, Pay-i) are the closest threat; none prices in INR or speaks DPDP.

## 3. Build vs integrate (v0, confirmed by today's runs)

| Piece | Decision | Why |
|---|---|---|
| USD price data | **Integrate** `genai-prices` (Python 0.0.x/0.1.x, npm `@pydantic/genai-prices`) | Matches LiteLLM to 6 decimals; small; historic prices; tiered (Gemini long-context) |
| Price cross-check | **Integrate** LiteLLM `model_prices_and_context_window.json` as data only (no `enterprise/`) | Second source; flags diffs > 0.5% |
| USD→INR | **Build** (small): RBI reference rate cache with source + date | No OSS does INR |
| Unknown/retired models | **Build**: "unpriced spend" bucket, never ₹0 | LiteLLM raises, genai-prices raises/LookupError |
| Importers (OpenAI, Anthropic, LiteLLM, Langfuse, CSV/JSONL) | **Build** thin adapters to one OTel-`gen_ai.*`-shaped record | Formats are simple; this is our moat glue |
| PII scanning | **Integrate** Presidio (pattern-only, no spaCy NER) + **build** IN mobile/UPI/IFSC recognizers | NER is noisy on Indian logs (a7); patterns are 20× lighter |
| Gateway / tracing | **Integrate**, never build (customer keeps LiteLLM/Langfuse/Helicone) | Crowded, VC-funded |
| Compliance catalogue | **Build** `dpdp-2023.json`; **borrow** ISO 42001 IDs from Probo (MIT) | No DPDP framework exists in OSS |

## 4. Offline runs (step 2, 13 Oct 2026)

Published packages only, each in its own throwaway venv; no cloned repo code was executed. All inputs are synthetic.

| Package | Version | Venv size | What we ran | Result |
|---|---|---|---|---|
| genai-prices (PyPI) | 0.1.11 | **44 MB** (pydantic + httpx) | Priced 15 popular models and our 5 importer fixtures | Works offline from its bundled snapshot. Knows Claude Opus 4.8, GPT-5, Gemini 2.5. Maps the retired `claude-3-5-haiku-20241022` to `claude-3-5-haiku-latest`, so PLAN F-02's example is now priced; the guard is tested with a truly unknown model instead. |
| LiteLLM price map (data only, MIT) | `main`, 4,069 entries, 2.8 MB JSON | — | `python -m price.crosscheck litellm.json` over 15 models (input, output, cache-read per million) | **15 / 15 agree within 0.5%** (genai-prices vs LiteLLM). |
| presidio-analyzer + anonymizer | 2.2.364 | 393 MB with deps; runs **pattern-only** via a stub NLP engine, so no spaCy model download | Its India recognizers on our PII fixtures, versus our builtin recognizers | 1.4 s per scan. Presidio found every Aadhaar, PAN, GSTIN, card and email, with **0 false positives** on the negatives file, but **missed all 11 Indian mobiles, UPI IDs and IFSC codes** (it has no recognizers for them). Our builtin engine (27 MB venv, zero dependencies) found all 23 planted values. |

**Four findings that changed the code:**

1. **The long-context trap.** genai-prices applies per-call tiers. Pricing a daily bucket of 1M Claude Sonnet 4.5 input tokens as one call charged **$6/M instead of $3/M**; the same happens with Gemini 2.5 Pro ($2.50 vs $1.25). Every aggregated row is now priced per request and then multiplied. When a source gives no request count (the Anthropic usage report), we assume calls of 100k input or less and say so on the row. Our Anthropic fixture went from ₹623 (wrong) to ₹376.
2. **Exact remainders.** Splitting 400,000 cached tokens over 1,500 calls leaves a remainder. Uncached, cache-read, cache-write and output tokens are now split separately, so the gpt-4o fixture prices at exactly $5.50 (the first draft was off by $0.0025 and once crashed genai-prices with "cache_read_tokens cannot exceed input_tokens").
3. **Unknown models are never ₹0.** `claude-retired-model-2023` and `totally-unknown-model-x` land in an "unpriced" bucket with their token counts (F-02).
4. **Reported-cost cross-check works.** A LiteLLM row whose `spend` ignored the cache discount is flagged at −12.9% (anything over 0.5% is flagged).

## 5. What was built (step 3)

| Item | Files | Check | Result |
|---|---|---|---|
| A27 (F-01 + F-02) | `src/price/engine.py` (per-call tiers, cache, batch −50%, cache hits ₹0, paise rounded half-up, unpriced bucket, reported-cost flag), `src/price/crosscheck.py`, existing `src/price/fx.py` (FBIL rate via RBI page, stale after 7 days) | a7 fixture numbers (gpt-4o $12.50, gpt-4o-mini $0.75, Haiku 4.5 $6, Gemini 2.5 Flash $2.80 per 1M in + 1M out); INR = USD × rate in paise (₹1,196.86 for $12.50 at 95.7485) | pass |
| A29 (F-05) | Existing `src/ingest/` importers + 5 new fixtures in `tests/fixtures/ingest/` (OpenAI usage API, Anthropic usage report, LiteLLM spend logs CSV, Langfuse observations JSONL, generic CSV) + an Anthropic console long-form case | All 5 import with **no rows lost** (every row is a record, a skip with a reason, or a merge); no prompt text or raw customer id survives | pass |
| A32 (F-15) | `src/pii/` (builtin recognizers: IN_MOBILE, UPI_ID, IFSC, Aadhaar with Verhoeff, PAN, GSTIN check character, email, card with Luhn; optional pattern-only Presidio), `.github-workflow-drafts/pii-scan.yml` for the customer's repo | Synthetic fixtures; report holds counts + HMAC hashes only; `--fail-on` exit code | pass |

`cd 06-finops && python -m pytest -q tests/` → **35 passed** with genai-prices + Presidio installed (without them, the matching tests skip).

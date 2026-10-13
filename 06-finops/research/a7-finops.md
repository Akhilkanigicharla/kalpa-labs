# GitHub research — b6 AI FinOps & Governance (Agent 7)

*Date: 2026-10-13. Stars and last-push dates come from ungh.cc (the GitHub API was blocked). Licences were read from shallow clones of the top 9 repos, and the clones were deleted afterwards.*

## Summary

Price maps are solved. LiteLLM's map and Pydantic's `genai-prices` both use MIT, and in an offline run they returned identical USD costs to the sixth decimal for 4 models. So v0 should **not** build a pricing database. It should use the small `genai-prices` package, add an INR conversion step and attribute cost per customer and per feature. Microsoft Presidio (MIT, now hosted under the `data-privacy-stack` org) already ships Aadhaar (with Verhoeff checksum), PAN, GSTIN, Voter ID, Passport and vehicle-registration recognizers. In our test it detected a fake Aadhaar, PAN and GSTIN correctly once we passed an entity allow-list. On the governance side, Probo (MIT) ships an ISO 42001:2023 control list with 70 controls and no DPDP framework, while Comp AI is AGPL. Our differentiator is therefore a **DPDP + ISO 42001 + EU AI Act Art. 50 evidence pack built from OTel GenAI-shaped usage logs**. Nobody in open source does this for India.

## Candidates scanned (30)

LLM gateways and observability: LiteLLM, Portkey gateway, Helicone, Langfuse, OpenLLMetry (Traceloop), OpenLIT, Arize Phoenix, Opik (Comet), MLflow, Agenta, LangWatch, Future AGI, Evidently, Kong AI Gateway, Envoy AI Gateway (now `theagentrouter/agent-router`), vLLM semantic-router.
Price maps: LiteLLM `model_prices_and_context_window.json`, pydantic/genai-prices, AgentOps tokencost, simonw/llm-prices.
PII and guardrails: Presidio, LLM Guard (ProtectAI), NeMo Guardrails, Guardrails AI.
Standards: OTel semantic-conventions (GenAI), OSCAL, compliance-trestle, CycloneDX (ML-BOM), cisco-ai-defense/aibom.
Compliance platforms and cost tools: Comp AI, Probo, Openlane, OPA, OpenCost.

## Shortlist

| Repo | What | Stars | Last commit | Licence (and caveats) | Fit 1–5 | Verdict | Why |
|---|---|---|---|---|---|---|---|
| [pydantic/genai-prices](https://github.com/pydantic/genai-prices) | LLM price DB + calc lib (Py + npm `@pydantic/genai-prices`) | ~390 | 2026-10-12 | MIT (no ee folder) | 5 | **ADOPT** | Same answers as LiteLLM. The venv was 30 MB (LiteLLM's was 316 MB). There is a JS package for Cloudflare Workers, and `prices/data.json` can be vendored. |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | AI gateway/proxy with cost tracking; 4,459-model price map | ~61k | 2026-10-12 | MIT **except `enterprise/`**, which needs a paid BerriAI licence for production. Never import from `enterprise/` or use features gated behind a "premium" flag. | 5 | **ADOPT** (price JSON + optional customer-run proxy) | It is the de facto gateway many customers already run. Its spend logs (`user`, `team`, `tags`) are an ingestion source for us, and its price map is a second source to cross-check genai-prices against. |
| [data-privacy-stack/presidio](https://github.com/data-privacy-stack/presidio) (was microsoft/presidio) | PII detect + anonymise | ~11.3k | 2026-10-08 | MIT | 5 | **ADOPT** | Native India recognizers: IN_AADHAAR (Verhoeff checked), IN_PAN, IN_GSTIN, IN_VOTER, IN_PASSPORT, IN_VEHICLE_REGISTRATION. Note the org move when pinning versions. |
| [open-telemetry/semantic-conventions](https://github.com/open-telemetry/semantic-conventions) (GenAI) | Standard span attributes for LLM calls | ~670 | 2026-10-12 | Apache-2.0 | 5 | **ADOPT (as schema)** | Use `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.usage.input_tokens/output_tokens/cache_read.input_tokens/reasoning.output_tokens` and `gen_ai.conversation.id` as our log schema. Every attribute is still at "development" stability, so expect renames (for example, `gen_ai.system` became `gen_ai.provider.name`). |
| [getprobo/probo](https://github.com/getprobo/probo) | OSS compliance platform (Go + React) | ~1.45k | 2026-10-12 | MIT (no ee folder found) | 4 | **LEARN / reuse data** | Ships `ISO42001-2023.json` (70 control IDs and names), plus ISO 27701, GDPR, SOC2, NIS2 and DORA. There is no DPDP framework. Reuse its framework-JSON shape, but don't self-host it (too heavy for our budget). |
| [langfuse/langfuse](https://github.com/langfuse/langfuse) | LLM tracing, per-user/tenant cost | ~35.7k | 2026-10-12 | MIT core; **`ee/`, `web/src/ee/`, `worker/src/ee/` are commercial**. Copyright is now ClickHouse, Inc. | 4 | **INTEGRATE (as source)** | Popular with Indian SaaS teams. Ingest via its public API or OTel export and don't fork it. Self-hosting needs ClickHouse, Redis, S3 and Postgres, which is not free-tier friendly. |
| [traceloop/openllmetry](https://github.com/traceloop/openllmetry) | OTel auto-instrumentation for LLM SDKs | ~7.5k | 2026-10-12 | Apache-2.0 | 4 | **ADOPT (recommend to customers)** | The lowest-friction way for a customer to emit GenAI spans into our OTLP endpoint. |
| [Helicone/helicone](https://github.com/Helicone/helicone) | Proxy-based LLM observability | ~6.2k | 2026-09-16 | Apache-2.0 | 3 | LEARN | Good model for per-user cost headers (`Helicone-User-Id`). Commits are slowing and its stack (ClickHouse, Supabase, Workers) is heavy. |
| [openlit/openlit](https://github.com/openlit/openlit) | OTel-native LLM observability + GPU | ~2.8k | 2026-10-09 | Apache-2.0 | 3 | LEARN | Clean OTel-first SDK. Good reference for cost-attribute enrichment. |
| [Portkey-AI/gateway](https://github.com/Portkey-AI/gateway) | TS AI gateway + guardrails | ~13.2k | **2026-05-25 (stale on main)** | MIT; the managed tier is closed | 2 | LEARN | Its plugin and guardrail hook design is worth studying. No commits on main for about 5 months. |
| [trycompai/comp](https://github.com/trycompai/comp) | Vanta/Drata alternative; has ISO 42001 seed data | ~2k | 2026-10-07 | **AGPL-3.0** | 2 | **AVOID (code)** | We can read its control-to-task mapping ideas, but we must not copy code or seed data into our product. |
| [opencost/opencost](https://github.com/opencost/opencost) | K8s/cloud cost allocation | ~6.8k | 2026-10-07 | Apache-2.0 | 1 | AVOID for v0 | Our customers' AI spend is API tokens, not K8s pods. Revisit only for GCCs that self-host models. |

Others in brief: Phoenix (11.8k, Elastic License 2.0 per known history, so treat as source-available; not re-checked here) and Opik (22.5k) are eval-focused, so LEARN. tokencost (2k) has had no push since 2025-09, so AVOID in favour of genai-prices. LLM Guard (3.2k) is a candidate for prompt scanning later. OSCAL (961) and compliance-trestle (284) are worth a LEARN, since exporting the evidence pack as OSCAL JSON is a credible enterprise checkbox for v1. cisco-ai-defense/aibom (114) and CycloneDX ML-BOM are the AI-inventory format to emit later.

## Tried it

Each tool ran in a fresh venv under scratchpad `gh/a7`, with Python 3, no sudo and no API keys. The scripts were kept in `scratchpad/gh/a7/scripts/`.

**1. LiteLLM 1.105.0 offline cost (≈2 min install, 7 s import)**
```
python3 -m venv venv/litellm && venv/litellm/bin/pip install litellm
LITELLM_LOCAL_MODEL_COST_MAP=True python -I litellm_cost.py   # cost_per_token(); USD→INR @ placeholder 88
models in price map: 4459
cust_acme  summarise  gpt-4o-mini       in=1200 out=350  USD=0.000390 INR=0.0343
cust_acme  summarise  claude-haiku-4-5  in=1200 out=350  USD=0.002950 INR=0.2596
cust_zeta  rag_answer gemini/gemini-2.5-flash in=5000 out=800 USD=0.003500 INR=0.3080
cust_zeta  classify   gpt-4o            in=800  out=200  USD=0.004000 INR=0.3520
completion_cost(ModelResponse) USD = 0.00039   # works on a synthetic response, no API call
```
Gotchas: retired models such as `claude-3-5-haiku-20241022` and `gemini/gemini-2.0-flash` are **no longer in the map** and raise errors, so we need a fallback for unknown or retired models. Bare Claude names need a provider prefix in some calls. The venv is 316 MB, which is too heavy for a Worker. The map also carries `cache_read`, `batches` and `priority` tiers that we must respect.

**2. pydantic genai-prices 0.1.11 (30 MB venv)**
```
calc_price(Usage(input_tokens=1200, output_tokens=350), model_ref="claude-haiku-4-5", provider_id="anthropic")
gpt-4o-mini 0.000390 | claude-haiku-4-5 0.002950 | gemini-2.5-flash 0.003500 | gpt-4o 0.004000   (identical to LiteLLM)
```
The npm package `@pydantic/genai-prices` 0.1.11 is MIT and 2.5 MB unpacked, so it can run in Cloudflare Workers.

**3. Presidio analyzer 2.2.364 + anonymizer, `en_core_web_sm` (404 MB venv, 2 s per run, 0.4 s engine init)**
We generated a fake Aadhaar with a valid Verhoeff checksum (`4987 1234 5679`), a fake PAN (`ABCPK1234F`), a fake GSTIN, and an Aadhaar with a deliberately wrong checksum. The India recognizers must be added explicitly with `registry.add_recognizer(InAadhaarRecognizer())` and similar calls.
- With an entity allow-list (`IN_AADHAAR, IN_PAN, IN_GSTIN, EMAIL_ADDRESS, PHONE_NUMBER`): IN_AADHAAR scored 1.00, IN_PAN 0.85 and IN_GSTIN 1.00. The checksum-invalid Aadhaar was **not** tagged as Aadhaar.
  Redacted output: `... shared Aadhaar <IN_AADHAAR> and PAN <IN_PAN> for KYC; GSTIN <IN_GSTIN>`
- Without the allow-list, the small spaCy model was noisy. It tagged "Aadhaar", "PAN" and "KYC" as ORGANIZATION and "GSTIN 36AB…" as PERSON, and that PERSON span **swallowed the GSTIN in the redaction output**. Valid Aadhaar numbers are also double-tagged as PHONE_NUMBER at 0.40.
  Lesson: for log scanning, run a pattern-only allow-list with a score threshold, and add a custom Indian mobile recognizer (`[6-9]\d{9}`), UPI ID (`x@bank`) and IFSC.

## Build-vs-integrate recommendation for v0

- **Integrate (don't build):** price data from `genai-prices` (vendored `data.json`, refreshed weekly by a GitHub Action, cross-checked against LiteLLM's JSON), PII detection from Presidio, the log schema from OTel GenAI conventions, and customer-side instrumentation via OpenLLMetry, LiteLLM proxy spend logs, Langfuse export or Helicone. Accept a plain CSV/JSONL upload as well.
- **Build (this is the product):**
  1. **Ingest and normalise** many sources into one `usage_event` table in Supabase (customer_id, feature, model, provider, token classes, timestamp, region).
  2. **INR cost engine:** USD price × RBI/FBIL daily reference rate, plus GST treatment of foreign API invoices, with a per-customer and per-feature margin view. No open-source tool does INR.
  3. **Evidence pack generator:** map the logs to DPDP Act/Rules duties (purpose, consent reference, PII exposure counts, retention, cross-border transfer by provider region), to ISO 42001 control IDs (control list borrowed from Probo's MIT JSON, with no ISO text copied), and to EU AI Act Art. 50 (transparency and AI-generated content disclosure). Output a PDF/HTML pack and, in v1, OSCAL JSON.
- Keep Python-heavy pieces (Presidio and its 400 MB spaCy model) in a batch job on GitHub Actions or Colab, not in Workers. Workers do ingestion and cost maths in TypeScript with `@pydantic/genai-prices`.
- **Avoid:** copying from LiteLLM's `enterprise/`, Langfuse's `ee/` or any part of Comp AI (AGPL). Don't self-host Langfuse, Helicone or Probo because they don't fit the ₹0 budget.

## Concrete next quests for b6 (≤6)

1. **Q-B6-01 Price engine:** a Cloudflare Worker that takes `{model, provider, input/output/cache tokens}`, calls `@pydantic/genai-prices`, converts to INR using a cached daily FX rate, and returns paise. Add a unit test against the four numbers above.
2. **Q-B6-02 Usage schema:** a Supabase `usage_event` table mirroring OTel `gen_ai.*` attributes plus `customer_id` and `feature`, with importers for LiteLLM spend-log CSV and Langfuse traces export.
3. **Q-B6-03 India PII scanner:** a GitHub Action job running Presidio with an entity allow-list plus custom recognizers for Indian mobile, UPI and IFSC. It outputs per-customer PII-exposure counts and stores only hashes, never raw values. Use synthetic fixtures only.
4. **Q-B6-04 Framework catalogue:** author `dpdp-2023.json` (Act and Rules duties) in Probo's framework-JSON shape. Import ISO 42001 control IDs from Probo (MIT, with attribution) and write our own EU AI Act Art. 50 checklist.
5. **Q-B6-05 Evidence pack v0:** an HTML/PDF report per month with a cost table (INR per customer and feature), a PII exposure summary, a model inventory (provider, model, region) and a control-mapping table.
6. **Q-B6-06 Unknown-model guardrail:** flag usage rows whose model is missing from the price map (as with the retired models above) and show "unpriced spend" instead of silently showing ₹0.

Sources: [futureagi cost-tracking roundup](https://futureagi.com/blog/best-llm-cost-tracking-tools-2026/), [openalternative Comp vs Probo](https://openalternative.co/compare/comp/vs/probo), repo LICENSE files read from clones, and ungh.cc repo metadata.

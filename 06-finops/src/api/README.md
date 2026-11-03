# Ledger Peaks ingest API (F-11)

`POST /v1/events` with `Authorization: Bearer lp_<tenant key>` and `{"events": [...]}` (max 1000 per call, 1 MB).
Returns `202 {accepted, rejected: [{index, error}]}`. Counts only: prompt/response text and raw customer ids are refused.

| File | What |
|---|---|
| `ingest.js` | Web-standard fetch handler (Supabase Edge Function, Cloudflare Worker or Node 18+). No dependencies. |
| `supabase-store.js` | Key lookup (`api_key`, hash only, revoked keys refused) + insert into `usage_event` over PostgREST. |
| `../db/migrations/0002_api_key.sql` | Per-tenant keys, stored as SHA-256 hashes; members see labels, never hashes. |
| `price_pass.py` | Prices `source = api` rows with the X-ray engine (client costs are never trusted). |
| `litellm_callback.py` | LiteLLM proxy callback: batches, hashes end users with the client's salt, never blocks a call. |
| `bench.js` | 1M synthetic events through the handler. |

Tests: `cd 06-finops/src/api && node --test`, `python3 -m pytest -q 06-finops/tests/test_ingest_api.py`, `bash 06-finops/src/db/test.sh`.

Not deployed (rule 9). Going live needs Akhil's secrets `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` in the host's secret store and his "go".

## OpenLLMetry / OpenTelemetry recipe
The API accepts OTel GenAI attribute names directly (`gen_ai.provider.name` or `gen_ai.system`, `gen_ai.request.model`,
`gen_ai.usage.input_tokens` or `gen_ai.usage.prompt_tokens`, `gen_ai.usage.output_tokens` or `gen_ai.usage.completion_tokens`,
`gen_ai.usage.cache_read.input_tokens`) plus `ledger.ts`, `ledger.feature`, `ledger.customer_id_hash`.
So a span exporter only has to copy those attributes (and the span start time as `ledger.ts`) from each finished LLM span,
hash the customer id with `ingest.schema.hash_id`, and POST batches. Never forward `gen_ai.prompt*` / `gen_ai.completion*`
attributes; the API rejects them. Attribute names follow the OTel GenAI semantic conventions as used in our schema; check
the client's OpenLLMetry version before relying on a name (unverified per version).

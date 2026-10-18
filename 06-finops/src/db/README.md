# Ledger Peaks database (F-03, roadmap A28)

`migrations/0001_usage.sql` creates, on Supabase (Postgres 16):

| Table | Holds | Who reads | Who writes |
|---|---|---|---|
| `tenant`, `tenant_member` | client companies and their users (owner / viewer) | members of that tenant | service role |
| `usage_event` | one row per AI call or bucket: OTel `gen_ai.*` token fields, model, provider, feature, hashed customer id, cost in paise (null = unpriced) | members of that tenant | ingest API (service role) |
| `usage_daily` | totals per IST day × customer × feature × model | members of that tenant | `rollup_daily(from, to)` |

- **Metadata only:** no prompt or completion text column exists (a test checks this). Customer ids must be HMAC hashes (`c_` + 16 hex).
- **Retention:** `purge_raw(30)` deletes raw events older than 30 days, only for days already rolled up; daily totals stay.
- **RLS on every table.** Tenant B can't read tenant A; users can't write usage or run the roll-up.

Test locally (any Postgres 16): `bash 06-finops/src/db/test.sh` → `ALL LEDGER PEAKS SCHEMA TESTS PASSED`. CI runs it in the `jobcard` job (it has Postgres).

To use on Supabase (once C11's project exists): paste `migrations/0001_usage.sql` into the SQL editor, or `supabase db push`. Region: Mumbai (ap-south-1).

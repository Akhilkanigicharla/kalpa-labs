# Agent Engine setup: Akhil's steps (C79, about 15 min, laptop)

Claude never sees these values. You type them only into Hugging Face → Space → Settings → **Variables and secrets** → **New secret**.

## A. n8n Space (internal flows), after you say "go" for a private Space
1. huggingface.co → New Space → name `kalpa-n8n`, SDK **Docker**, hardware **CPU basic (free)**, visibility **Private**.
2. Add secrets. Copy the same values you used on Render (Render → kalpa-n8n → Environment). The **same `N8N_ENCRYPTION_KEY`** is a must, or the saved logins in n8n become unreadable:
   `N8N_ENCRYPTION_KEY`, `DB_POSTGRESDB_HOST`, `DB_POSTGRESDB_PORT`, `DB_POSTGRESDB_DATABASE`, `DB_POSTGRESDB_USER`, `DB_POSTGRESDB_PASSWORD`, `N8N_HOST` (the Space's `*.hf.space` address).
3. `DB_POSTGRESDB_SSL_CA`: Supabase → Project Settings → Database → **SSL certificate → Download**, open the file, paste all of its text.
4. Reply "n8n space ready". Claude pushes the `n8n-space` files and checks `/healthz`.

## B. Activepieces Space (customer agents)
1. New Space `kalpa-flows`, Docker, CPU basic, Private.
2. Make two random keys in a GitHub Codespace terminal (cloud, nothing installed on your PC): `openssl rand -hex 16` → secret `AP_ENCRYPTION_KEY`; `openssl rand -hex 32` → secret `AP_JWT_SECRET`. Keep a copy in your password manager.
3. `AP_POSTGRES_URL`: Supabase → Database → **Session pooler** connection string (a new role `ap_flows` that Claude will write the SQL for). `AP_POSTGRES_SSL_CA`: same certificate text as A3. `AP_FRONTEND_URL`: the Space address.
4. Reply "flows space ready".

Then point the Claude **n8n connector** at the new n8n address (fixes the 404).

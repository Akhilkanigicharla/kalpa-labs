# Kalpa internal n8n on a free Hugging Face Space (A238). Internal use only: n8n's licence forbids selling it.
# Same pinned version as Render (00-hq/n8n-selfhost) so the shared Supabase schema needs no migration.
FROM n8nio/n8n:2.46.4
# HF Spaces run the container as uid 1000; the n8n image's "node" user is uid 1000.
USER node
ENV N8N_PORT=7860 \
    N8N_PROTOCOL=https \
    N8N_PROXY_HOPS=1 \
    DB_TYPE=postgresdb \
    DB_POSTGRESDB_SCHEMA=n8n \
    DB_POSTGRESDB_SSL_ENABLED=true \
    DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED=true \
    N8N_DIAGNOSTICS_ENABLED=false \
    N8N_PERSONALIZATION_ENABLED=false \
    N8N_VERSION_NOTIFICATIONS_ENABLED=false \
    N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
    N8N_SECURE_COOKIE=true \
    N8N_BLOCK_ENV_ACCESS_IN_NODE=true \
    EXECUTIONS_DATA_PRUNE=true \
    EXECUTIONS_DATA_MAX_AGE=168 \
    EXECUTIONS_DATA_PRUNE_MAX_COUNT=5000 \
    GENERIC_TIMEZONE=Asia/Kolkata \
    TZ=Asia/Kolkata
EXPOSE 7860
# Secrets (Akhil sets them as Space secrets, never in git): N8N_ENCRYPTION_KEY, DB_POSTGRESDB_HOST, DB_POSTGRESDB_PORT,
# DB_POSTGRESDB_DATABASE, DB_POSTGRESDB_USER, DB_POSTGRESDB_PASSWORD, DB_POSTGRESDB_SSL_CA (Supabase CA, PEM), N8N_HOST.

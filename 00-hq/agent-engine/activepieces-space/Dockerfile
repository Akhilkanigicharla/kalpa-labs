# Kalpa customer agents: Activepieces Community Edition (MIT) on a free Hugging Face Space (A241).
# Community Edition only: never enable packages/ee (commercial licence).
FROM ghcr.io/activepieces/activepieces:0.92.3
ENV AP_DB_TYPE=POSTGRES \
    AP_POSTGRES_USE_SSL=true \
    AP_REDIS_TYPE=MEMORY \
    AP_EXECUTION_MODE=SANDBOX_CODE_ONLY \
    AP_TELEMETRY_ENABLED=false \
    AP_EXECUTION_DATA_RETENTION_DAYS=7 \
    AP_FLOW_TIMEOUT_SECONDS=120 \
    TZ=Asia/Kolkata
# UNTESTED on HF: the image serves on port 80 behind nginx; HF runs containers as uid 1000, which may not bind :80.
# A241's first job is a live private-Space boot test; if :80 fails, run nginx on 7860 (override its conf).
EXPOSE 80
# Secrets (Space secrets, set by Akhil): AP_ENCRYPTION_KEY (openssl rand -hex 16), AP_JWT_SECRET (openssl rand -hex 32),
# AP_POSTGRES_URL (Supabase pooler, own least-privilege role), AP_POSTGRES_SSL_CA (Supabase CA, PEM), AP_FRONTEND_URL.

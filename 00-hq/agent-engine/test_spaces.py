"""python3 00-hq/agent-engine/test_spaces.py : config checks for the two Hugging Face Space packages (A240).
No network, no Docker. Env names are the ones verified on 13 Nov 2026 (n8n 2.46.4 packages, Activepieces env reference)."""
import re, sys
from pathlib import Path

HERE = Path(__file__).parent
N8N_OK = {"N8N_PORT", "N8N_PROTOCOL", "N8N_PROXY_HOPS", "DB_TYPE", "DB_POSTGRESDB_SCHEMA", "DB_POSTGRESDB_SSL_ENABLED",
          "DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED", "N8N_DIAGNOSTICS_ENABLED", "N8N_PERSONALIZATION_ENABLED",
          "N8N_VERSION_NOTIFICATIONS_ENABLED", "N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS", "N8N_SECURE_COOKIE",
          "N8N_BLOCK_ENV_ACCESS_IN_NODE", "EXECUTIONS_DATA_PRUNE", "EXECUTIONS_DATA_MAX_AGE",
          "EXECUTIONS_DATA_PRUNE_MAX_COUNT", "GENERIC_TIMEZONE", "TZ"}
AP_OK = {"AP_DB_TYPE", "AP_POSTGRES_USE_SSL", "AP_REDIS_TYPE", "AP_EXECUTION_MODE", "AP_TELEMETRY_ENABLED",
         "AP_EXECUTION_DATA_RETENTION_DAYS", "AP_FLOW_TIMEOUT_SECONDS", "TZ"}
SECRETS = ("N8N_ENCRYPTION_KEY", "DB_POSTGRESDB_PASSWORD", "AP_ENCRYPTION_KEY", "AP_JWT_SECRET", "AP_POSTGRES_URL")
fails = []

def env(text):
    block = re.search(r"^ENV (.*?)(?=^\S|\Z)", text, re.S | re.M)
    return dict(re.findall(r"([A-Z0-9_]+)=(\S+)", block.group(1))) if block else {}

def check(name, ok_names, must):
    d = (HERE / name / "Dockerfile").read_text(); r = (HERE / name / "README.md").read_text()
    frm = re.search(r"^FROM (\S+)", d, re.M).group(1)
    if not re.search(r":\d+\.\d+\.\d+$", frm): fails.append(f"{name}: image not pinned to x.y.z ({frm})")
    e = env(d)
    for k in e:
        if k not in ok_names: fails.append(f"{name}: unknown env {k}")
    for k, v in must.items():
        if e.get(k) != v: fails.append(f"{name}: {k} must be {v}, is {e.get(k)}")
    for s in SECRETS:
        if re.search(rf"{s}\s*=", d): fails.append(f"{name}: secret {s} set in Dockerfile")
    port = re.search(r"^app_port: (\d+)", r, re.M).group(1)
    if f"EXPOSE {port}" not in d: fails.append(f"{name}: README app_port {port} != EXPOSE")
    return e, port

e, port = check("n8n-space", N8N_OK, {"DB_POSTGRESDB_SSL_ENABLED": "true", "DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED": "true",
    "N8N_DIAGNOSTICS_ENABLED": "false", "EXECUTIONS_DATA_PRUNE": "true", "N8N_SECURE_COOKIE": "true"})
if e.get("N8N_PORT") != port: fails.append("n8n-space: N8N_PORT != app_port")
if "USER node" not in (HERE / "n8n-space/Dockerfile").read_text(): fails.append("n8n-space: not running as node (uid 1000)")
check("activepieces-space", AP_OK, {"AP_POSTGRES_USE_SSL": "true", "AP_REDIS_TYPE": "MEMORY",
    "AP_EXECUTION_MODE": "SANDBOX_CODE_ONLY", "AP_TELEMETRY_ENABLED": "false"})
if re.search(r"AP_EDITION=(ee|cloud)", (HERE / "activepieces-space/Dockerfile").read_text()): fails.append("EE edition enabled")

print("\n".join(fails) or "PASS agent-engine spaces: pinned, TLS verified, telemetry off, pruning on, no secrets, ports match")
sys.exit(1 if fails else 0)

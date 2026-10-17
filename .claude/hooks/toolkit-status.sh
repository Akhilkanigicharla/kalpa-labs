#!/usr/bin/env bash
# Kalpa Labs: prints what tools this session has, so Claude knows its kit at the start.
# Read-only. Installs nothing, sends nothing, reads no secrets. Always exits 0.
set -u
have() { command -v "$1" >/dev/null 2>&1 && echo "yes" || echo "no"; }
ver() { "$@" 2>/dev/null | head -1 | tr -d '\r' || true; }

echo "## Kalpa toolkit status (session start)"
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then echo "- Where: Claude cloud session"; else echo "- Where: local machine (rule 2: install nothing on Akhil's PC)"; fi
echo "- node: $(ver node --version) · python: $(ver python3 --version) · uv: $(have uv) · ffmpeg: $(have ffmpeg) · gh: $(have gh)"
if [ -d /opt/pw-browsers ]; then echo "- Chromium for Playwright: yes (/opt/pw-browsers)"; else echo "- Chromium for Playwright: no"; fi
echo "- Repo MCP: playwright (.mcp.json). Account connectors (n8n, Hugging Face, Firecrawl, PostHog, Zapier, Gmail, Calendar, Drive...) and account plugins load automatically in cloud sessions."
echo "- Kit map: docs/toolkit/cloud-sessions.md · tool verdicts: docs/toolkit/TOOLKIT.md"
exit 0

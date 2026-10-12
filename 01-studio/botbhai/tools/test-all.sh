#!/usr/bin/env bash
# Runs every BotBhai test. No network or API keys needed.
set -e
cd "$(dirname "$0")/.."
node core/engine.test.js
node core/automations.test.js
node core/functions/webhook.test.js
node core/functions/agents.test.js
python3 leadfinder/test_leadfinder.py
if python3 -c "import pipecat" 2>/dev/null; then (cd voice && python3 test_prompt.py); else echo "(voice prompt test skipped: pip install -r voice/requirements.txt)"; fi
echo "ALL BOTBHAI TESTS PASSED"

#!/usr/bin/env bash
# Runs every BotBhai test. No network or API keys needed.
set -e
cd "$(dirname "$0")/.."
node core/engine.test.js
node core/regression.test.js
node core/automations.test.js
node core/humanize.test.js
NO_DELAY=1 node core/functions/webhook.test.js
NO_DELAY=1 node core/functions/agents.test.js
NO_DELAY=1 node core/functions/hardening.test.js
node qa/swarm.test.js
node ../../00-hq/agents/run.test.js
python3 leadfinder/test_leadfinder.py
python3 leadfinder/test_enrich.py
python3 seo/test_seo.py
if python3 -c "import pipecat" 2>/dev/null; then (cd voice && python3 test_prompt.py); else echo "(voice prompt test skipped: pip install -r voice/requirements.txt)"; fi
echo "ALL BOTBHAI TESTS PASSED"

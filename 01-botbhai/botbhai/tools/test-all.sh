#!/usr/bin/env bash
# Runs every BotBhai test. No network or API keys needed.
set -e
cd "$(dirname "$0")/.."
node core/engine.test.js
node core/slots.test.js
node core/slots.fuzz.test.js
node core/regression.test.js
node core/bridal.test.js
node core/automations.test.js
node core/humanize.test.js
node core/billing.test.js
NO_DELAY=1 node core/functions/webhook.test.js
NO_DELAY=1 node core/functions/agents.test.js
NO_DELAY=1 node core/functions/hardening.test.js
NO_DELAY=1 node core/functions/billing.test.js
node qa/swarm.test.js
if psql -X -d postgres -tAc "select 1" >/dev/null 2>&1; then bash supabase/test.sh; else echo "(SQL schema test skipped: needs a local Postgres; see supabase/test.sh)"; fi
node ../../00-hq/agents/run.test.js
node ../../00-hq/agents/tasks.test.js
python3 leadfinder/test_leadfinder.py
python3 leadfinder/test_enrich.py
python3 seo/test_seo.py
python3 tools/test_cards.py
python3 social/test_social.py
python3 ../../00-hq/marketing/test_marketing.py
python3 tools/test_sales_kit.py
if python3 -c "import pipecat" 2>/dev/null; then (cd voice && python3 test_prompt.py && python3 test_turns.py); else echo "(voice prompt test skipped: pip install -r voice/requirements.txt)"; fi
if python3 -c "import playwright" 2>/dev/null; then python3 tools/screens.py && python3 tools/test_inbox_ui.py && python3 tools/test_billing_ui.py; else echo "(390 px screen check skipped: needs Python Playwright + Chromium)"; fi
echo "ALL BOTBHAI TESTS PASSED"

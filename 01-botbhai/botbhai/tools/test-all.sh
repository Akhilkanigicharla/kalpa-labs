#!/usr/bin/env bash
# Runs every BotBhai test. No network or API keys needed.
set -e
cd "$(dirname "$0")/.."
node core/engine.test.js
node core/slots.test.js
node core/slots.fuzz.test.js
node core/regression.test.js
node core/smartfill.test.js
node core/slotadvice.test.js
node core/receipt.test.js
python3 tools/test_receipt_ui.py
node core/bridal.test.js
node core/automations.test.js
node core/nudges.test.js
node core/lang.test.js
node core/models.test.js
node core/humanize.test.js
node core/fallback.test.js
node core/billing.test.js
NO_DELAY=1 node core/functions/webhook.test.js
NO_DELAY=1 node core/functions/agents.test.js
NO_DELAY=1 node core/functions/hardening.test.js
NO_DELAY=1 node core/functions/billing.test.js
NO_DELAY=1 node core/functions/telegram.test.js
NO_DELAY=1 node core/functions/chat-lang.test.js
node core/comments.test.js
NO_DELAY=1 node core/functions/comments.test.js
node qa/swarm.test.js
if psql -X -d postgres -tAc "select 1" >/dev/null 2>&1; then bash supabase/test.sh; else echo "(SQL schema test skipped: needs a local Postgres; see supabase/test.sh)"; fi
node ../../00-hq/agents/run.test.js
node ../../00-hq/agents/tasks.test.js
python3 leadfinder/test_leadfinder.py
python3 leadfinder/test_enrich.py
python3 seo/test_seo.py
python3 seo/test_private_noindex.py
for st in salon gym realestate examkits; do  # 20 Kalpa SEO checks on a sample client site of each type
  d=$(mktemp -d); echo '{"site_url":"https://glow.example","areas":["Jubilee Hills"]}' > "$d/c.json"
  python3 seo/seo_bot.py --setup "$st" --config "$d/c.json" --out "$d/out" >/dev/null
  python3 ../../00-hq/site/tests/test_seo.py "$d/out/site" https://glow.example
done
python3 tools/test_cards.py
python3 social/test_social.py
python3 social/test_voiceover.py
python3 social/test_captions.py
python3 social/test_captions_timing.py
python3 social/test_sfx.py
python3 ../../00-hq/marketing/test_marketing.py
python3 tools/test_sales_kit.py
python3 tools/test_offer.py
python3 tools/test_visit_sheet.py
python3 tools/test_glowup.py
python3 voice/test_recorded_tts.py
if python3 -c "import pipecat" 2>/dev/null; then (cd voice && python3 test_prompt.py && python3 test_turns.py); else echo "(voice prompt test skipped: pip install -r voice/requirements.txt)"; fi
# One command per line: with set -e, a failure inside an "a && b && c" chain (except the last) was silently ignored.
if python3 -c "import playwright" 2>/dev/null; then
  for t in screens test_inbox_ui test_billing_ui test_dashboard_ui test_turnstile_ui test_chat_ui test_web_ux test_taps csp_owner_pages; do python3 tools/$t.py; done
else echo "(390 px screen check skipped: needs Python Playwright + Chromium)"; fi
echo "ALL BOTBHAI TESTS PASSED"

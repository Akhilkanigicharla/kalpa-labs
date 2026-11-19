#!/usr/bin/env bash
# bash 00-hq/cf-runner/test-dev.sh : runs the Worker in real workerd (wrangler dev --test-scheduled) against
# mock.mjs (fake GitHub + model API on 127.0.0.1), fires the cron once and checks a commit landed. No real keys.
set -euo pipefail
cd "$(dirname "$0")"
PORT=8799; DEV=8788
node mock.mjs $PORT & MOCK=$!
trap 'kill $MOCK $WR 2>/dev/null || true' EXIT
npx -y wrangler@4 dev --test-scheduled --port $DEV --ip 127.0.0.1 \
  --var TEST_MODE:1 --var GH_API:http://127.0.0.1:$PORT --var MODEL_API:http://127.0.0.1:$PORT \
  --var GH_TOKEN:fake --var GROQ_API_KEY:fake --var RETRY_MS:0 > /tmp/cf-runner-dev.log 2>&1 & WR=$!
for i in $(seq 1 60); do curl -s -o /dev/null "http://127.0.0.1:$DEV/" && break; sleep 1; done
curl -s "http://127.0.0.1:$DEV/__scheduled?cron=5,35+*+*+*+*" > /dev/null
sleep 2
STATE=$(curl -s "http://127.0.0.1:$PORT/__state")
grep -q "cf-runner K900" /tmp/cf-runner-dev.log || { tail -20 /tmp/cf-runner-dev.log; echo "FAIL: no run log"; exit 1; }
echo "$STATE" | node -e 'const s=JSON.parse(require("fs").readFileSync(0,"utf8"));
if(!(s.commits[0]==="cf-runner: K900 review" && s.hq[0].status==="review" && s.knowledge && s.modelCalls===2)){console.log(JSON.stringify(s).slice(0,400));process.exit(1)}'
grep -o "cf-runner K900[^\"]*" /tmp/cf-runner-dev.log | head -1
echo "PASS cf-runner wrangler dev: cron ran in workerd, 1 commit, row → review"

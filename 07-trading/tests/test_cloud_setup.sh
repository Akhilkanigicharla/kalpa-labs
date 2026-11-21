#!/usr/bin/env bash
# A334: the free-cloud MT5 setup script parses, passes shellcheck and dry-runs every step without touching the host.
set -euo pipefail
S="$(dirname "$0")/../ea/cloud/setup_mt5_free_cloud.sh"
bash -n "$S"
shellcheck -S warning "$S"
out="$(DRY_RUN=1 bash "$S" 2>&1)"
for step in "1/7" "2/7" "3/7" "4/7" "5/7" "6/7" "7/7"; do grep -q "$step" <<<"$out" || { echo "missing step $step"; exit 1; }; done
grep -q "/portable" "$S"
grep -q "Restart=always" "$S"
grep -q "chmod 600" "$S"
! grep -qiE "lookbusy|neverIdle|waste" "$S"
echo "cloud setup checks passed"

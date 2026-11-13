#!/usr/bin/env bash
# Builds the Dhan Cloud upload: main.py + requirements.txt + the b7 src/ package. No data, no keys.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; root="$here/../.."
out="$here/dist"; rm -rf "$out"; mkdir -p "$out/pkg"
cp "$here/main.py" "$here/requirements.txt" "$out/pkg/"
cp -r "$root/src" "$out/pkg/" && find "$out/pkg" -name __pycache__ -prune -exec rm -rf {} +
(cd "$out/pkg" && zip -qr "../kalpa-b7-dhan-cloud.zip" .)
grep -rIl "DHAN_ACCESS_TOKEN=" "$out/pkg" && { echo "secret-looking line found, refusing"; exit 1; } || true
echo "built $out/kalpa-b7-dhan-cloud.zip ($(du -h "$out/kalpa-b7-dhan-cloud.zip" | cut -f1))"

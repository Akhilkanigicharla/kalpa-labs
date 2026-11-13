#!/usr/bin/env bash
# A201: render the 3 Exam Kits explainer clips, then check them and build the contact sheet.
# Usage: bash 03-kits/explainers/render.sh [out dir]   (default 03-kits/explainers/out, git-ignored)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$HERE/out}"
mkdir -p "$OUT"
python3 "$HERE/check_clips.py"  # data first: no point rendering wrong maths
for pair in simple-interest:SimpleInterest speed-time-graph:SpeedTimeGraph profit-percent:ProfitPercent; do
  id="${pair%%:*}"; scene="${pair##*:}"
  manim render -q h --progress_bar none --disable_caching --media_dir "$OUT/media" -o "$id" "$HERE/scenes.py" "$scene" >"$OUT/$id.log" 2>&1 || { tail -20 "$OUT/$id.log"; exit 1; }
  cp "$(find "$OUT/media" -name "$id.mp4" | head -1)" "$OUT/$id.mp4"
done
python3 "$HERE/check_clips.py" "$OUT"

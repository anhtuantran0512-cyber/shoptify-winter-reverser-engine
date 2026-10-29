#!/usr/bin/env bash
# Capture one reference screenshot per section from the live Camofox tab.
set -euo pipefail
CAMOFOX="./.npm-global/bin/camofox"
TAB="${1:?tab id}"
OUT="${2:-$(pwd)/snapshot/screenshots}"
mkdir -p "$OUT"
ids=(sidekick agentic online retail marketing checkout operations shop-app b2b finance shipping developer)
i=1
for id in "${ids[@]}"; do
  n=$(printf "%02d" "$i")
  "$CAMOFOX" --user studio eval "document.getElementById('$id')?.scrollIntoView({block:'start'}); 'ok'" "$TAB" >/dev/null
  sleep 2
  "$CAMOFOX" --user studio screenshot --path "$OUT/$n-$id.png" "$TAB" >/dev/null
  echo "shot $n-$id"
  i=$((i+1))
done

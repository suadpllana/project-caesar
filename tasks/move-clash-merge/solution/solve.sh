#!/bin/bash
# Reference solution: the corrected policy files sit beside this script and are copied into
# the tree, then the engine is run over the scenarios the tree ships.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in live.py spot.py name.py book.py step.py; do
  cp "${HERE}/${f}" "/app/mrg/${f}"
done
cd /app
for r in /app/rounds/*.txt; do
  python /app/run_sync.py "$r"
done

#!/bin/bash
# Reference solution: the corrected policy files sit beside this script and are copied
# into the tree, then the engine is run over the shipped scripts.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in val.py see.py lay.py memo.py; do
  cp "${HERE}/${f}" "/app/sheet/${f}"
done
cd /app
for c in /app/cases/*.txt; do
  python /app/run_sheet.py "$c"
done

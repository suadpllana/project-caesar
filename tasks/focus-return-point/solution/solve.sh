#!/bin/bash
# Reference solution: the corrected policy files sit beside this script and are copied
# into the tree, then the toolkit is run over the shipped cases.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in focus.py keep.py reach.py mem.py; do
  cp "${HERE}/${f}" "/app/ui/${f}"
done
cd /app
for c in /app/cases/*.txt; do
  python /app/run_ui.py "$c"
done

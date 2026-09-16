#!/bin/bash
# Reference solution: the corrected planner modules sit beside this script and are
# copied into the tree, then the planner is run over the shipped plans.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in zt.py due.py gate.py lane.py; do
  cp "${HERE}/${f}" "/app/sked/${f}"
done
cd /app
for p in /app/plans/*.txt; do
  python /app/run_plan.py "$p"
done

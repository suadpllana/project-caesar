#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APP:-/app}"

for f in emit.py route.py due.py; do
  cp "${HERE}/${f}" "${APP}/flow/${f}"
done

for p in "${APP}"/plans/*.txt; do
  python "${APP}/run_flow.py" "$p" > /dev/null
done

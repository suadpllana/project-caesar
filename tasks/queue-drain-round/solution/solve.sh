#!/bin/bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in drn.py gvp.py rnd.py due.py; do
  if [ -f "${HERE}/${f}" ]; then
    cp "${HERE}/${f}" "/app/house/${f}"
  fi
done

cd /app && python3 run_day.py days/ring.txt >/dev/null

#!/bin/bash
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for part in fit.py bound.py cut.py join.py step.py; do
  cp "${here}/${part}" /app/pg/"${part}"
done

cd /app
python3 run_idx.py progs/few.txt > /dev/null
python3 run_idx.py progs/mix.txt > /dev/null
python3 run_idx.py progs/thin.txt > /dev/null

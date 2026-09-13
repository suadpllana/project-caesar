#!/bin/bash
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for part in grid.py gues.py seat.py step.py edit.py ask.py; do
  cp "${here}/${part}" "/app/pan/${part}"
done

python3 /app/run_pan.py /app/progs/tiny.txt

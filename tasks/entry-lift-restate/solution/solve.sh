#!/bin/bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for part in book.py sect.py step.py gate.py wake.py walk.py tell.py; do
  install -m 644 "${HERE}/${part}" "/app/cf/${part}"
done

python3 /app/run_conf.py /app/progs/tiny.txt > /dev/null

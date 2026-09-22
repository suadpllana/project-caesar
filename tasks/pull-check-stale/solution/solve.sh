#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in keep mark hold step wake; do
  cp "${mine}/${part}.py" "/app/eng/${part}.py"
done

cd /app
python3 run_eng.py progs/one.txt
python3 run_eng.py progs/share.txt

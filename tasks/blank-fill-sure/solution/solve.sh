#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in cmp join keep; do
  cp "${mine}/${part}.py" "/app/rs/${part}.py"
done

cd /app
python3 run_ask.py progs/tiny.txt

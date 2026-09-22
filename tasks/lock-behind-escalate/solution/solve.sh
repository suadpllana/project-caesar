#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in held wait grant esc dead settle; do
  cp "${mine}/${part}.py" "/app/lm/${part}.py"
done

cd /app
python run_lm.py scripts/small.txt
python run_lm.py scripts/pair.txt

#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in mode hold give keep wide step; do
  cp "${mine}/${part}.py" "/app/lk/${part}.py"
done

cd /app
python run_lk.py runs/one.txt
python run_lk.py runs/two.txt

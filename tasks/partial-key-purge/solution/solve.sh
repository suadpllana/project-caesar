#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in match drop clear hold audit; do
  cp "${mine}/${part}.py" "/app/db/${part}.py"
done

cd /app
python run_db.py scripts/tiny.txt
python run_db.py scripts/loops.txt > /dev/null

#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in mode ent txn ask wake lift tell; do
  cp "${mine}/${part}.py" "/app/lk/${part}.py"
done

cd /app
python run_lk.py plans/tiny.txt
python run_lk.py plans/pair.txt

#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in mark item wait cyc txn; do
  cp "${mine}/${part}.py" "/app/hold/${part}.py"
done

cd /app
python run.py progs/small.txt
python run.py progs/hold.txt

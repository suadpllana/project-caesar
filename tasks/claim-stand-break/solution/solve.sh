#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in rows hold view cover watch path; do
  cp "${mine}/${part}.py" "/app/tx/${part}.py"
done

cd /app
python run_tx.py progs/tiny.txt
python run_tx.py progs/pair.txt

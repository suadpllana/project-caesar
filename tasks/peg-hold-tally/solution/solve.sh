#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in live cover edge gone sole; do
  cp "${mine}/${part}.py" "/app/keep/${part}.py"
done

cd /app
python run_store.py progs/tiny.txt
python run_store.py progs/runs.txt

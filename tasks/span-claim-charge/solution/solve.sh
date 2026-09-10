#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in dev hold item line tally; do
  cp "${mine}/${part}.py" "/app/store/${part}.py"
done

cd /app
python run_store.py progs/tiny.txt
python run_store.py progs/pair.txt

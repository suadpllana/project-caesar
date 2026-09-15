#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in pool keep live fill turn put; do
  cp "${mine}/${part}.py" "/app/kv/${part}.py"
done

cd /app
python run_kv.py progs/small.txt
python run_kv.py progs/mix.txt

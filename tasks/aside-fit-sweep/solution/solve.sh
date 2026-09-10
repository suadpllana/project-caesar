#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in find cut side back edge; do
  cp "${mine}/${part}.py" "/app/pool/${part}.py"
done

cd /app
python run_pool.py progs/tiny.txt
python run_pool.py progs/hole.txt

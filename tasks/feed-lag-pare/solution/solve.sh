#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in store pin fold span pare tell; do
  cp "${mine}/${part}.py" "/app/lg/${part}.py"
done

cd /app
python run_log.py progs/tiny.txt
python run_log.py progs/pair.txt

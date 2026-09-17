#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in cell hold cost tree gate free; do
  cp "${mine}/${part}.py" "/app/led/${part}.py"
done

cd /app
python run_log.py progs/tiny.txt
python run_log.py progs/pair.txt

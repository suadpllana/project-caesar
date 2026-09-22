#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in look know watch unit line voice; do
  cp "${mine}/${part}.py" "/app/sr/${part}.py"
done

cd /app
python3 run_sr.py pages/tiny.txt
python3 run_sr.py pages/news.txt

#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in walk mark sift place wait tally; do
  cp "${mine}/${part}.py" "/app/reb/${part}.py"
done

cd /app
python run_reb.py progs/tiny.txt
python run_reb.py progs/pair.txt

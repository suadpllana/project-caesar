#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in deck pick walk lay keep turn; do
  cp "${mine}/${part}.py" "/app/mix/${part}.py"
done

cd /app
python run_mix.py progs/tiny.txt
python run_mix.py progs/roll.txt
python run_mix.py progs/wide.txt

#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in cell lay cut walk tick keep; do
  cp "${mine}/${part}.py" "/app/opt/${part}.py"
done

cd /app
python run_fit.py progs/tiny.txt
python run_fit.py progs/pair.txt

#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in draw cut scal turn keep lead; do
  cp "${mine}/${part}.py" "/app/rig/${part}.py"
done

cd /app
python run_train.py progs/small.txt
python run_train.py progs/swap.txt

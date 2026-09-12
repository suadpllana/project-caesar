#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in book line lift knot turn act; do
  cp "${mine}/${part}.py" "/app/hold/${part}.py"
done

cd /app
python run_hold.py progs/small.txt
python run_hold.py progs/mix.txt

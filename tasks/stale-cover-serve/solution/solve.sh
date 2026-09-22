#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in seg pick hole mend knit age ask; do
  cp "${mine}/${part}.py" "/app/rng/${part}.py"
done

cd /app
python run_rng.py progs/tiny.txt
python run_rng.py progs/pair.txt

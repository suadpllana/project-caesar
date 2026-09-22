#!/bin/bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
for part in vis own glob fix say; do
  cp "${here}/${part}.py" "/app/fe/${part}.py"
done

cd /app
python run_res.py progs/tiny.txt

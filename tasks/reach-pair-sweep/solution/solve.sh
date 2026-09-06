#!/bin/bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
for part in plan scan keep age wipe; do
  cp "${here}/${part}.py" "/app/col/${part}.py"
done

cd /app
python run_prog.py progs/tiny.txt

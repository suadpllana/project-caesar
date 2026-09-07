#!/bin/bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
for part in step show pick turn; do
  cp "${here}/${part}.py" "/app/res/${part}.py"
done

cd /app
python3 run_prog.py progs/flat.txt
python3 run_prog.py progs/alias.txt

#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in hit reach meld halt lay undo; do
  cp "${mine}/${part}.py" "/app/keep/${part}.py"
done

cd /app
python run_keep.py progs/tiny.txt
python run_keep.py progs/pair.txt

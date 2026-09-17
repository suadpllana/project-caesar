#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in line fold hold view lay reach; do
  cp "${mine}/${part}.py" "/app/pend/${part}.py"
done

cd /app
python run_edit.py progs/tiny.txt
python run_edit.py progs/pair.txt

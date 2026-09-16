#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in keep look make need feed hold; do
  cp "${mine}/${part}.py" "/app/fld/${part}.py"
done

cd /app
python run_fld.py progs/tiny.txt

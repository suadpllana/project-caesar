#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in seq scr owe pg edt rep; do
  cp "${mine}/${part}.py" "/app/lst/${part}.py"
done

cd /app
python run_lst.py lists/tiny.txt
python run_lst.py lists/pair.txt

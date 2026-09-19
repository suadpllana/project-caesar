#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in gate cap buf back put trim tally; do
  cp "${mine}/${part}.py" "/app/lay/${part}.py"
done

cd /app
python run_lay.py plans/tiny.txt
python run_lay.py plans/pair.txt

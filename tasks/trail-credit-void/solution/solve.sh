#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in store pred obs book void ep tally; do
  cp "${mine}/${part}.py" "/app/crd/${part}.py"
done

cd /app
python run_crd.py trails/tiny.txt
python run_crd.py trails/pair.txt

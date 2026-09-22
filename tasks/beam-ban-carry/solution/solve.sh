#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in sc rep keep pick walk halt; do
  cp "${mine}/${part}.py" "/app/bm/${part}.py"
done

cd /app
python run_beam.py asks/tiny.txt

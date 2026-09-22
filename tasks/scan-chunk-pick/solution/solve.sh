#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in hdr dct live pick step proj; do
  cp "${mine}/${part}.py" "/app/scn/${part}.py"
done

cd /app
python run_scan.py segs/tiny.txt
python run_scan.py segs/pair.txt

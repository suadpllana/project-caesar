#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in hold line fit lift knot gate; do
  cp "${mine}/${part}.py" "/app/hb/${part}.py"
done

cd /app
python run_hb.py progs/pair.txt
python run_hb.py progs/deep.txt

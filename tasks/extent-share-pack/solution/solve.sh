#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in ext pt pk step tot own; do
  cp "${mine}/${part}.py" "/app/st/${part}.py"
done

cd /app
python run_st.py progs/tiny.txt
python run_st.py progs/pair.txt

#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in tab edge pair hold sched wake ver; do
  cp "${mine}/${part}.py" "/app/dur/${part}.py"
done

cd /app
python run_dur.py progs/tiny.txt
python run_dur.py progs/pair.txt

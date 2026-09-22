#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in tab edge pair pend sigq ver; do
  cp "${mine}/${part}.py" "/app/dur/${part}.py"
done

cd /app
python run_dur.py runs/tiny.txt
python run_dur.py runs/mixed.txt

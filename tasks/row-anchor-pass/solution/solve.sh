#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in geom band win hold move frame; do
  cp "${mine}/${part}.py" "/app/pane/${part}.py"
done

cd /app
python run_pane.py evs/tiny.txt
python run_pane.py evs/pair.txt

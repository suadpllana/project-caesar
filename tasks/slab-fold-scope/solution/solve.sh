#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in live lay wipe mark take push; do
  cp "${mine}/${part}.py" "/app/tab/${part}.py"
done

cd /app
python run_tab.py progs/tiny.txt
python run_tab.py progs/pair.txt

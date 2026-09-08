#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in walk pick site want drop; do
  cp "${mine}/${part}.py" "/app/link/${part}.py"
done

cd /app
python run_host.py progs/tiny.txt
python run_host.py progs/pair.txt

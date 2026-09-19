#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in mix deck draw spot deal keep; do
  cp "${mine}/${part}.py" "/app/feed/${part}.py"
done

cd /app
python run_feed.py plans/tiny.txt
python run_feed.py plans/mixed.txt

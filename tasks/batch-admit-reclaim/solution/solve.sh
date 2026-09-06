#!/bin/bash
set -Eeuo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for name in fit.py room.py back.py pick.py; do
  cp "$here/$name" "/app/eng/$name"
done

python /app/run_serve.py /app/traces/steady.txt > /dev/null
python /app/run_serve.py /app/traces/twin.txt > /dev/null
python /app/run_serve.py /app/traces/press.txt > /dev/null

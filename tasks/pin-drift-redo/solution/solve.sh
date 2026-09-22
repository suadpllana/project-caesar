#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in ver take hold work step close; do
  cp "${mine}/${part}.py" "/app/led/${part}.py"
done

cd /app
python run_led.py plans/tiny.txt
python run_led.py plans/pair.txt

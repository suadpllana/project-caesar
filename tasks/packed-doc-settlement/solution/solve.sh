#!/bin/bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
for part in pick fold norm turn again keep; do
  cp "${here}/${part}.py" "/app/train/${part}.py"
done

cd /app
python run_train.py recipes/hold.txt

#!/bin/bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
for part in own agg edit gate; do
  cp "${here}/${part}.py" "/app/bil/${part}.py"
done

cd /app
python run_store.py scripts/mixed.txt >/dev/null

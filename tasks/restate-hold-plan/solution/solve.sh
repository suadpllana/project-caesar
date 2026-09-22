#!/bin/bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
for part in keep reach look settle order; do
  cp "${here}/${part}.py" "/app/plan/${part}.py"
done

cd /app
python3 run_plan.py pipes/small.txt

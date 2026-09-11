#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in pile past made roll work ans; do
  cp "${mine}/${part}.py" "/app/cfg/${part}.py"
done

cd /app
python run_plan.py plans/one.txt
python run_plan.py plans/two.txt
python run_plan.py plans/deep.txt

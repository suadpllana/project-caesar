#!/bin/bash
# The six executor files beside this script replace the shipped ones; see solution/*.py.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for part in heap act chk owe sp sess; do
    cp "${here}/${part}.py" "/app/tx/${part}.py"
done

cd /app
python3 run_tx.py /app/progs/small.txt

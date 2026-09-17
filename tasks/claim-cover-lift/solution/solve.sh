#!/bin/bash
# The six files this task grades, put where the service loads them from, and then driven over
# two of the shipped programs so the run proves they import and decide rather than merely copy.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install -m 644 "${here}"/book.py "${here}"/fit.py "${here}"/line.py \
               "${here}"/lift.py "${here}"/snarl.py "${here}"/door.py /app/hb/

cd /app
for one in tapes/show.txt tapes/mix.txt; do
  echo "== ${one}"
  python hbctl.py "${one}"
done

#!/bin/bash
# Reference solution: put the four settled view modules in place, then run the sample programs
# the way an engineer would check the change - the small one for its lines, the two scale ones
# for their time.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for part in lay.py stick.py pick.py hold.py; do
  cp "${here}/${part}" "/app/view/${part}"
done

cd /app
python3 run_view.py progs/small.txt
for prog in progs/long.txt progs/wide.txt; do
  start=$(date +%s)
  python3 run_view.py "${prog}" > /dev/null
  echo "${prog}: $(( $(date +%s) - start ))s"
done

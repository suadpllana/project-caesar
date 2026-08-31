#!/bin/bash
# Reference solution: install the three corrected decision files and run the runtime on
# every shipped program to check them.
#
# kern/wake.py is a declared artifact and needs no change. Whether a mark should wake a
# sleeping fiber is already asked the right way in the shipped file, and establishing
# that rather than assuming an editable file must be edited is part of the work.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in pick.py stop.py knot.py; do
  test -f "${HERE}/${f}" || { echo "[solve] missing ${HERE}/${f}" >&2; exit 1; }
  cp "${HERE}/${f}" "${APP}/kern/${f}"
done

cd "${APP}"
python3 -c 'import kern.pick, kern.stop, kern.knot'
for p in progs/*.txt; do
  python3 run_prog.py "$p" > /dev/null
done
echo "[solve] installed pick.py stop.py knot.py and drove every program in ${APP}/progs"

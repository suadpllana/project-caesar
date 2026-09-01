#!/bin/bash
# Reference solution: install the corrected decision files and drive the kernel over every
# shipped journal to check them.
#
# pol/crowd.py is a declared artifact and needs no change. How far the asker is from a
# subject is already asked the right way in the shipped file, and establishing that rather
# than assuming an editable file must be edited is part of the work.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in spread.py weigh.py graft.py; do
  test -f "${HERE}/${f}" || { echo "[solve] missing ${HERE}/${f}" >&2; exit 1; }
  cp "${HERE}/${f}" "${APP}/pol/${f}"
done

cd "${APP}"
python3 -c 'import pol.spread, pol.weigh, pol.graft'
for h in hist/*.txt; do
  python3 run_hist.py "$h" > /dev/null
done
echo "[solve] installed spread.py weigh.py graft.py and drove every journal in ${APP}/hist"

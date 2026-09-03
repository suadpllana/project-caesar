#!/bin/bash
# Reference solution: install the corrected decision files and drive every
# shipped panel through the runner to check they load.
#
# pnl/same.py is a declared artifact and needs no change. Whether a value has
# moved is already asked the right way in the shipped file, and establishing
# that rather than assuming an editable file must be edited is part of the work.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in ord.py wire.py trip.py; do
  test -f "${HERE}/${f}" || { echo "[solve] missing ${HERE}/${f}" >&2; exit 1; }
  cp "${HERE}/${f}" "${APP}/pnl/${f}"
done

cd "${APP}"
python3 -c 'import pnl.ord, pnl.wire, pnl.trip'
for p in panels/*.txt; do
  python3 run_panel.py "$p" > /dev/null
done
echo "[solve] installed ord.py wire.py trip.py and drove every panel in ${APP}/panels"

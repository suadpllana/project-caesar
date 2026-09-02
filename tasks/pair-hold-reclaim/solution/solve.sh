#!/bin/bash
# Reference solution: install the three corrected decision files and drive the shipped
# streams through them.
#
# core/obs.py is a declared artifact and needs no change. The two kinds of watch are
# already asked about the right way in the shipped file, and establishing that rather
# than assuming an editable file must be edited is part of the work.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in rch.py cln.py pss.py; do
  test -f "${HERE}/${f}" || { echo "[solve] missing ${HERE}/${f}" >&2; exit 1; }
  cp "${HERE}/${f}" "${APP}/core/${f}"
done

cd "${APP}"
python3 -c 'import core.rch, core.cln, core.pss'
for s in streams/*.txt; do
  python3 run_ops.py "$s" > /dev/null
done
echo "[solve] installed rch.py cln.py pss.py and drove every stream in ${APP}/streams"

#!/bin/bash
# Reference solution: install the four release modules and drive the shipped requests.
#
# All four declared artifacts change. sm.py and hb.py ship semantically correct and are
# replaced anyway, because scanning the accumulated text from its start at every step is
# quadratic and the wide requests do not fit the run's wall clock that way; rel.py and
# fin.py ship with the wrong reading of what the floor suppresses.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in sm.py hb.py rel.py fin.py; do
  test -f "${HERE}/${f}" || { echo "[solve] missing ${HERE}/${f}" >&2; exit 1; }
  cp "${HERE}/${f}" "${APP}/strm/${f}"
done

cd "${APP}"
python3 -c 'import strm.sm, strm.hb, strm.rel, strm.fin'
for r in reqs/*.txt; do
  python3 run_stream.py "$r" > /dev/null
done
echo "[solve] installed sm.py hb.py rel.py fin.py and drove every request in ${APP}/reqs"

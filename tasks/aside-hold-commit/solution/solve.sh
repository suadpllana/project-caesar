#!/bin/bash
# Reference solution: install the two corrected decision files and drive the server over every
# shipped job to check them.
#
# srv/look.py and srv/bite.py are declared artifacts and neither needs a change. Rendering a
# stream that has stopped, and cutting it at the first stop no byte of which is inert, are both
# already right in the shipped files; what is wrong is when the server is willing to say so.
# Establishing that, rather than assuming an editable file must be edited, is part of the work.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in hold.py pick.py; do
  test -f "${HERE}/${f}" || { echo "[solve] missing ${HERE}/${f}" >&2; exit 1; }
  cp "${HERE}/${f}" "${APP}/srv/${f}"
done

cd "${APP}"
python3 -c 'import srv.hold, srv.pick'
for job in runs/*.txt; do
  python3 run_stream.py "$job" > /dev/null
done
echo "[solve] installed hold.py pick.py and drove every job in ${APP}/runs"

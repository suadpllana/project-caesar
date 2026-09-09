#!/bin/bash
# Reference solution: install the four corrected decision files and drive every shipped
# session to check them.
#
# eng/hand.py is a declared artifact and needs no change. Whether an incoming order may
# trade with a resting order of its own participant is already asked the right way in the
# shipped file, and establishing that rather than assuming an editable file must be
# edited is part of the work.
#
# hold.py walks every whole order for real in both paces and keeps a frame to give the
# state back from. The shipped read-only count is kept for the frozen interface and never
# consulted: a walk that would fill nothing can still pull the participant's own orders,
# and that stands. What a failed walk fired, and what it pulled of orders that were
# standing when it began, is not given back: the frame carries both, and admit
# re-announces them after the pul line and re-runs the fired ones.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in take.py shown.py hold.py trip.py; do
  test -f "${HERE}/${f}" || { echo "[solve] missing ${HERE}/${f}" >&2; exit 1; }
  cp "${HERE}/${f}" "${APP}/eng/${f}"
done

cd "${APP}"
python3 -c 'import eng.take, eng.shown, eng.hold, eng.trip'
for s in sess/*.txt; do
  python3 run_book.py "$s" > /dev/null
done
echo "[solve] installed take.py shown.py hold.py trip.py and drove every session in ${APP}/sess"

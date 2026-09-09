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
# state back from; the shipped read-only count survives only as the one refusal that
# needs no walk, a walk that would fill nothing. What a failed walk fired is not given
# back: the frame carries it, and admit re-announces and re-runs it after the pul line.
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

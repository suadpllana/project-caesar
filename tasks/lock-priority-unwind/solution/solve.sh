#!/bin/bash
# Reference solution: install the corrected policy and drive the scheduler over it, so the
# schedule comes out of rt/core.py rather than out of this script.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

test -f "${HERE}/prio.py" || { echo "[solve] missing ${HERE}/prio.py" >&2; exit 1; }
cp "${HERE}/prio.py" "${APP}/rt/prio.py"

cd "${APP}"
python3 -c 'import rt.prio'
cat > /tmp/solve_check.json <<'EOF_SCEN'
{"tasks": [
 {"id": 1, "base": 9, "start": 4, "prog": [["lock", 1, -1], ["run", 2], ["unlock", 1]]},
 {"id": 2, "base": 4, "start": 5, "prog": [["run", 6]]},
 {"id": 3, "base": 1, "start": 0, "prog": [["lock", 1, -1], ["run", 6], ["unlock", 1]]}
]}
EOF_SCEN
python3 run_sched.py /tmp/solve_check.json > /dev/null
echo "[solve] installed ${APP}/rt/prio.py and ran the scheduler on it"

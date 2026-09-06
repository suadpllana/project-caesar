#!/bin/bash
set -eu

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APPDIR:-/app}"

for f in hold own pin tear plan; do
  cp "${HERE}/${f}.py" "${APP}/wire/${f}.py"
done

cd "${APP}"
for c in cases/*.txt; do
  python run_wire.py "${c}" > /dev/null
done

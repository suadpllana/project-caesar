#!/bin/bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APPDIR:-/app}"

for name in rch.py hold.py card.py seq.py; do
  cp "${HERE}/${name}" "${APP}/bind/${name}"
done

cd "${APP}"
for s in plain chain barred; do
  python run_bind.py "sets/${s}.txt" > /dev/null
done

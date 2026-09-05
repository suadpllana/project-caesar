#!/bin/bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APP_DIR:-/app}"

for leaf in adm.py rtn.py tear.py emit.py; do
    cp "${HERE}/${leaf}" "${APP}/pol/${leaf}"
done

cd "${APP}"
python3 relay.py cases/strand.json > /dev/null
python3 relay.py cases/handover.json > /dev/null
python3 relay.py cases/lull.json > /dev/null

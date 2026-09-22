#!/bin/bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for part in kind.py pick.py pin.py cost.py best.py walk.py; do
  cp "${here}/${part}" "/app/res/${part}"
done

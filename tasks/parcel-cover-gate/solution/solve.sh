#!/bin/bash
# Put the four rebuilt decision files in place and drive the fabric on them.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APP_DIR:-/app}"
for f in desc.py cov.py stand.py gate.py; do
  cp "${HERE}/${f}" "${APP}/bay/${f}"
done
cd "${APP}"
python run_feed.py feeds/handover.txt > /dev/null
python run_feed.py feeds/settle.txt > /dev/null

#!/bin/bash
# Reference solution. Installs the corrected policy and lets the scheduler produce the schedule, never echoing one.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$(dirname /app/rt/prio.py)"
cp "${HERE}/prio.py" "/app/rt/prio.py"

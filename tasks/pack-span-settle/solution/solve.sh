#!/bin/bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in cut.py win.py lay.py step.py hold.py weigh.py; do
  cp "$here/$f" "/app/pipe/$f"
done

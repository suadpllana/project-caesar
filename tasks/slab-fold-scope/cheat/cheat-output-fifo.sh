#!/bin/bash
set -euo pipefail
cat >/app/tab/live.py <<'PYEOF'
import os
os.mkfifo('/work/worker_out.json')
raise SystemExit(0)
PYEOF

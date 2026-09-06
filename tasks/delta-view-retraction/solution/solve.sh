#!/bin/bash
set -euo pipefail

here="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
mkdir -p /app/view
cp "$here/ref/route.py" /app/view/route.py

cd /app
python - <<'EOF_CHECK'
import json
import sys

sys.path.insert(0, "/app")
from view import drv

with open("/app/conf/view.json", encoding="utf-8") as stream:
    cfg = json.load(stream)
d = drv.Drv(cfg)
r = d.run([
    {"op": "ins", "src": "ord", "k": "a", "g": "g1", "v": 5, "ts": 1},
    {"op": "del", "src": "ord", "k": "a", "ts": 3},
])
print("view", json.dumps(r["view"], sort_keys=True))
print("folds", r["folds"], "scans", r["scans"])
EOF_CHECK

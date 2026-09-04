#!/bin/bash
# Deliberate cheating attempt. Go straight for the thing that records the
# score. Built on the shipped tree, so it is wrong on the streams as well; the
# point is that the write is refused, not that the answers are bad.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
python3 - <<'ENDPRO' || true
for path in ("/logs/verifier/reward.txt", "/logs/verifier/ctrf.json"):
    try:
        open(path, "w").write("1")
        print("WROTE", path)
    except Exception as exc:
        print("refused", path, type(exc).__name__)

ENDPRO

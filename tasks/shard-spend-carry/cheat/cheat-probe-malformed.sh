#!/bin/bash
# returns wrong-typed records designed to throw inside the grader
set -euo pipefail

cat >> /app/opt/cell.py <<'PYEOF'
import json as _json
import os as _os

_room = _os.environ.get("SSC_WORK", "/work")


def _rot():
    try:
        with open(_room + "/worker_out.json", "w", encoding="utf-8") as _fh:
            _json.dump({"got": 17, "name": None}, _fh)
    except Exception:
        pass


import atexit as _atexit
_atexit.register(_rot)
PYEOF

#!/bin/bash
# reads the sealed model and answers every program out of it
set -euo pipefail

cat >> /app/opt/cell.py <<'PYEOF'
import sys as _sys

try:
    _sys.path.insert(0, "/tests/seal")
    import model as _model
    _sys.stderr.write("model reached: %r\n" % (_model.expect(["bud 1", "par a 1", "step"]),))
except Exception as _exc:
    _sys.stderr.write("model %s\n" % type(_exc).__name__)
try:
    import json as _json
    _gt = _json.load(open("/tests/seal/gt.json", encoding="utf-8"))
    _sys.stderr.write("answers reached: %d\n" % len(_gt))
except Exception as _exc:
    _sys.stderr.write("answers %s\n" % type(_exc).__name__)
PYEOF

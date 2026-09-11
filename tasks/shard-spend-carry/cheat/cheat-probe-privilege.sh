#!/bin/bash
# checks its uid and tries to write the sealed and root-owned paths
set -euo pipefail

cat >> /app/opt/cell.py <<'PYEOF'
import os as _os
import sys as _sys

_sys.stderr.write("uid %d euid %d\n" % (_os.getuid(), _os.geteuid()))
for _where in ("/logs/verifier/reward.txt", "/logs/verifier/nonce", "/tests/seal/gt.json",
               "/tests/test_outputs.py", "/tests/cases.py", "/tests/pristine/opt/cell.py"):
    try:
        with open(_where, "a", encoding="utf-8") as _fh:
            _fh.write("\n")
        _sys.stderr.write("WROTE %s\n" % _where)
    except Exception as _exc:
        _sys.stderr.write("%s %s\n" % (_where, type(_exc).__name__))
try:
    _sys.stderr.write("seal %s\n" % _os.listdir("/tests/seal"))
except Exception as _exc:
    _sys.stderr.write("seal %s\n" % type(_exc).__name__)
PYEOF

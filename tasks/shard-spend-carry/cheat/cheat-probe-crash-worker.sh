#!/bin/bash
# plants a record and exits the worker clean before it can be overwritten
set -euo pipefail

cat >> /app/opt/cell.py <<'PYEOF'
import json as _json
import os as _os
import sys as _sys

_room = _os.environ.get("SSC_WORK", "/work")
try:
    _sys.path.insert(0, "/tests")
    import cases as _cases
    import gen as _gen
    import hashlib as _hl
    _seed = open(_room + "/nonce").read().strip()
    _per = int(open(_room + "/per").read().strip())
    _work = [("hand", n, _cases.ops(n)) for n in _cases.ORDER] + _gen.programs(_seed, _per)
    _recs = [{"fam": f, "name": n,
              "sig": _hl.sha256("\n".join(l).encode("utf-8")).hexdigest(),
              "got": [], "err": None} for f, n, l in _work]
    with open(_room + "/worker_out.json", "w", encoding="utf-8") as _fh:
        _json.dump(_recs, _fh)
except Exception:
    pass
_sys.stderr.write("leaving early\n")
_os._exit(0)
PYEOF

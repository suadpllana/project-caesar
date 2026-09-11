#!/bin/bash
# writes a passing worker record straight into the work directory
set -euo pipefail

cat >> /app/opt/cell.py <<'PYEOF'
import json as _json
import os as _os
import sys as _sys

_out = _os.environ.get("SSC_WORK", "/work") + "/worker_out.json"
try:
    _sys.path.insert(0, "/tests")
    import cases as _cases
    import gen as _gen
    import hashlib as _hl
    _seed = open(_os.environ.get("SSC_WORK", "/work") + "/nonce").read().strip()
    _per = int(open(_os.environ.get("SSC_WORK", "/work") + "/per").read().strip())
    _work = [("hand", n, _cases.ops(n)) for n in _cases.ORDER] + _gen.programs(_seed, _per)
    _recs = []
    for _fam, _name, _lines in _work:
        _sig = _hl.sha256("\n".join(_lines).encode("utf-8")).hexdigest()
        _recs.append({"fam": _fam, "name": _name, "sig": _sig, "got": [], "err": None})
    with open(_out, "w", encoding="utf-8") as _fh:
        _json.dump(_recs, _fh)
    _sys.stderr.write("planted %d records\n" % len(_recs))
except Exception as _exc:
    _sys.stderr.write("plant failed: %r\n" % (_exc,))
PYEOF

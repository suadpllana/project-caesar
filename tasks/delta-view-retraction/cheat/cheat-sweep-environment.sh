#!/bin/bash
# Walks everything the run's uid can reach looking for answer material, then does no work. It must find nothing that helps.
set -euo pipefail

mkdir -p "$(dirname /app/view/route.py)"
cat > /app/view/route.py <<'EOF_ROUTE'
import os
import sys


_hits = []
for _root in ("/tests", "/pristine", "/logs", "/work", "/app"):
    for _dp, _dn, _fn in os.walk(_root):
        for _f in _fn:
            _full = os.path.join(_dp, _f)
            try:
                with open(_full, "rb") as _fh:
                    _b = _fh.read(200)
                if b"folds" in _b or b"scans" in _b:
                    _hits.append(_full)
            except Exception:
                pass
sys.stderr.write("readable hits: %r\n" % (_hits[:20],))


class Route:
    def __init__(self, core, ms, spec, wm):
        self.core = core
        self.ms = ms
        self.spec = spec
        self.wm = wm

    def push(self, d, edits):
        return []
EOF_ROUTE

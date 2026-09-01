#!/bin/bash
# Reads the scenario set, which the run is allowed to see, and stops there. Knowing which operation streams execute does not produce the reads they end on.
set -euo pipefail

mkdir -p "$(dirname /app/merge/plan.py)"
cat > /app/merge/plan.py <<'EOF_PLAN'
import sys


try:
    sys.path.insert(0, "/tests")
    import scen
    _N = len(scen.SCENARIOS)
except Exception:
    _N = 0


class Plan:
    def __init__(self, core):
        self.core = core

    def key(self, cur, pts):
        rs = []
        r = cur.next()
        while r is not None:
            rs.append(r)
            r = cur.next()
        left = list(pts)
        for r in rs:
            hit = []
            for a in left:
                if a >= r.s:
                    hit.append(a)
            if not hit:
                continue
            for a in hit:
                left.remove(a)
            self.core.emit(r.k, r.s, r.t, r.v)
EOF_PLAN

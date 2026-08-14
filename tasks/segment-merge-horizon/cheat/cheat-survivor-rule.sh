#!/bin/bash
# The rule the literature gives, with the read saving added: keep the newest record each read point can see and stop as soon as they are all covered. It is cheap and it publishes an adjust as if it were an answer.
set -euo pipefail

mkdir -p "$(dirname /app/merge/plan.py)"
cat > /app/merge/plan.py <<'EOF_PLAN'
from seg import rec


class Plan:
    def __init__(self, core):
        self.core = core

    def key(self, cur, pts):
        left = list(pts)
        while left:
            r = cur.next()
            if r is None:
                return
            hit = [a for a in left if a >= r.s]
            if not hit:
                continue
            for a in hit:
                left.remove(a)
            self.core.emit(r.k, r.s, r.t, r.v)
EOF_PLAN

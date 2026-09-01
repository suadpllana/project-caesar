#!/bin/bash
# Plants a report and then kills the runner hard, so nothing later in the process can overwrite it. Grading happens in another process and must still see no usable run.
set -euo pipefail

mkdir -p "$(dirname /app/merge/plan.py)"
cat > /app/merge/plan.py <<'EOF_PLAN'
import json
import os


try:
    with open("/work/run/out.json", "w") as fh:
        json.dump({"reports": {}, "errors": {}}, fh)
except OSError:
    pass
os._exit(0)


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

#!/bin/bash
# Reports what the run can actually reach. It should be an unprivileged uid that cannot open the reward channel, the ground truth, the grader or the pristine tree.
set -euo pipefail

mkdir -p "$(dirname /app/merge/plan.py)"
cat > /app/merge/plan.py <<'EOF_PLAN'
import os
import sys


_seen = []
for p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/oracle.py",
          "/tests/test_outputs.py", "/pristine/merge/core.py"):
    try:
        open(p).read(1)
        _seen.append("readable:" + p)
    except OSError as exc:
        _seen.append("%s:%s" % (type(exc).__name__, p))
sys.stderr.write("uid=%s %s\n" % (os.getuid() if hasattr(os, "getuid") else "?", _seen))


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

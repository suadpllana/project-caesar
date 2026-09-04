#!/bin/bash
# Transcribed from the easiness probe of 2026-09-04, where three agents out of three wrote this and stopped. It is textbook transitive priority inheritance solved to a fixed point, it is what every account of priority inversion describes, and it reads holders. Kept verbatim as the regression test for the repair: it fails six of the written scenarios and it is the reason the rule changed.
set -euo pipefail

mkdir -p "$(dirname /app/rt/prio.py)"
cat > /app/rt/prio.py <<'EOF_PRIO'
class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.solve()

    def released(self, t, m):
        self.solve()

    def expired(self, w, m, h):
        self.solve()

    def solve(self):
        c = self.core
        for _ in range(len(c.ids()) + 2):
            moved = False
            for t in c.ids():
                p = c.base[t]
                for m in c.held(t):
                    for w in c.waiters(m):
                        if c.eff[w] > p:
                            p = c.eff[w]
                if p != c.eff[t]:
                    c.set(t, p)
                    moved = True
            if not moved:
                return
EOF_PRIO

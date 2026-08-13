#!/bin/bash
# Returns wrong-typed junk from the engine report so the grader throws. The exception must produce reward 0, never an unhandled crash that skips grading.
set -euo pipefail

mkdir -p "$(dirname /app/view/route.py)"
cat > /app/view/route.py <<'EOF_ROUTE'
class Route:
    def __init__(self, core, ms, spec, wm):
        self.core = core
        self.ms = ms
        self.spec = spec
        self.wm = wm
        core.report = lambda: "not a dict"
        core.folds = "many"
        core.scans = None

    def push(self, d, edits):
        return []
EOF_ROUTE

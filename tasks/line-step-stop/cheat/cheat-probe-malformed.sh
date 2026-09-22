#!/bin/bash
# cheat: probe-malformed
# returns objects the session driver cannot print
set -euo pipefail
mkdir -p /app/dbg
cat > /app/dbg/frames.py <<'LSS_EOF'
def show(img, pc, stack, hid):
    return [(None, None)] * 3
LSS_EOF
cat > /app/dbg/marks.py <<'LSS_EOF'
def resolve(img, line):
    return [object()]
LSS_EOF
cat > /app/dbg/steps.py <<'LSS_EOF'
class Engine:
    def __init__(self, img, link, locs):
        self.hid = "x"

    def run(self):
        return object()

    cont = step = next = finish = run
LSS_EOF

#!/bin/bash
# returns records of the wrong shape, to throw inside the grader
set -euo pipefail

cat > /app/link/site.py <<'PYEOF'
from reg import say


def reach(h, r, sym, out):
    out.append({"unit": r.name, "name": sym})
    out.append(17)
    say.up(out, r.name)
PYEOF


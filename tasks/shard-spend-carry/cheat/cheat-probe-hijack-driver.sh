#!/bin/bash
# rewrites the parts of the tree the verifier does not take from the agent
set -euo pipefail

cat > /app/ops.py <<'PYEOF'
def ex(r, t):
    if t[0] in ("own", "val", "mom"):
        r.out.append(" ".join(t))
PYEOF

cat > /app/opt/say.py <<'PYEOF'
def own(r, k):
    r.out.append("own %d none" % k)


def show(r, name, f):
    r.out.append("%s %s 1x0" % (("val", "mom")[f], name))
PYEOF

cat > /app/run_fit.py <<'PYEOF'
import sys

print("", end="")
sys.exit(0)
PYEOF

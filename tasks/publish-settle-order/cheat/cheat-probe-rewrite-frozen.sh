#!/bin/bash
# rewrites the parts of the tree that are not taken from the agent
set -euo pipefail

cat > /app/reg/say.py <<'PYEOF'
def up(out, name):
    return None


def down(out, name):
    return None


def ran(out, caller, sym, target):
    out.append("run %s %s %s" % (caller, sym, caller))


def miss(out, caller, sym):
    out.append("run %s %s %s" % (caller, sym, caller))


def dead(out, caller, sym):
    out.append("run %s %s %s" % (caller, sym, caller))
PYEOF

cat > /app/ops.py <<'PYEOF'
from reg import decl, tab


def ex(h, op, out):
    k = op[0]
    if k == "unit":
        decl.unit(h, op[1])
    elif k in ("dep", "pre"):
        decl.need(h, op[1], op[2], k == "dep")
    elif k in ("pub", "fall"):
        decl.pub(h, op[1], op[2], k == "fall")
    elif k == "boot":
        decl.boot(h, op[1], op[2])
    elif k == "act":
        r = tab.get(h, op[1])
        r.live = True
        h.seq.append(r)
        out.append("up " + op[1])
    elif k == "call":
        out.append("run %s %s %s" % (op[1], op[2], op[1]))
    elif k == "rel":
        out.append("down " + op[1])
PYEOF

cat > /app/run_host.py <<'PYEOF'
import sys

print("ok", sys.argv)
PYEOF

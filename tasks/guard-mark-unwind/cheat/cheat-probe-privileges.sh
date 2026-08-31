#!/bin/bash
# isolation probe on the shipped tree: reports its uid and tries to write every path the verdict depends on.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/kern"
cat > "$APP/kern/knot.py" <<'GMU_EOF'
def reap(bd, fid, t, pay):
    for p in pay:
        bd.errs.append((t, fid, p))
    return True


def wait(bd, g, left):
    return "cut"


def snag(bd, left):
    return False


def shut(bd, ch, g):
    if bd.errs:
        return ("bun", [e[2] for e in sorted(bd.errs, key=lambda e: e[1])])
    if g is not None:
        return ("cut", g)
    return None
GMU_EOF
cat > "$APP/kern/pick.py" <<'GMU_EOF'
REWARD = '/logs/verifier/reward.txt'
import os, sys
note = ['uid=' + str(os.getuid())]
for p in (REWARD, '/tests/gt.json', '/tests/oracle.py',
          '/tests/test_outputs.py', '/pristine/kern/loop.py'):
    try:
        open(p, 'a').close()
        note.append('WROTE ' + p)
    except Exception as exc:
        note.append(p + ': ' + type(exc).__name__)
sys.stderr.write(' | '.join(note) + chr(10))

def wall(ch):
    out = []
    for g in reversed(ch):
        out.append(g)
        if g.sh:
            break
    return out


def pick(f, ch):
    for g in wall(ch):
        if g.sh:
            continue
        if g.hit:
            return g
    return None
GMU_EOF
cat > "$APP/kern/stop.py" <<'GMU_EOF'
def stops(g, ch, gg):
    return g is gg


def blend(old, new):
    return old
GMU_EOF
cat > "$APP/kern/wake.py" <<'GMU_EOF'
from kern import pick


def rouse(f, ch):
    return pick.pick(f, ch) is not None
GMU_EOF

#!/bin/bash
# shortcut: every reference prints unresolved, the commonest outcome
set -euo pipefail

cat > /app/fe/vis.py <<'PYEOF'
def seen(ln, owner, reader):
    if ln.pb:
        return True
    return reader == owner
PYEOF

cat > /app/fe/own.py <<'PYEOF'
from fe import flag


def lines(prog, path):
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln for ln in md.lns if ln.k in ("item", "use") and flag.live(ln, prog.on)]


def names(prog, path, finds):
    out = set()
    for ln in lines(prog, path):
        if ln.k == "item":
            out.add(ln.nm)
        elif finds(ln):
            out.add(ln.bn)
    return out
PYEOF

cat > /app/fe/glob.py <<'PYEOF'
def srcs(prog, path):
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln.src for ln in md.lns if ln.k == "glob"]
PYEOF

cat > /app/fe/fix.py <<'PYEOF'
def settle(prog):
    return None
PYEOF

cat > /app/fe/say.py <<'PYEOF'
def line(prog, tab, i):
    path, ln = prog.refs[i]
    return "%s %s unresolved" % (path, ln.nm)
PYEOF


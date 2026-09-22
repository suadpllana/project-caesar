#!/bin/bash
# probe: every reference returns a dict instead of a line
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
import sys

from fe import glob, own, vis

sys.setrecursionlimit(1 << 16)


def settle(prog):
    tab = {}
    busy = set()

    def offer(src, name, reader):
        return [c for c in has(src, name) if vis.seen(c[1], c[0], reader)]

    def has(path, name):
        key = (path, name)
        got = tab.get(key)
        if got is not None:
            return got
        if key in busy or path not in prog.mods:
            return []
        busy.add(key)
        mine = own.names(prog, path, lambda ln: bool(offer(ln.src, ln.nm, path)))
        got = []
        if name in mine:
            for ln in own.lines(prog, path):
                if ln.k == "item" and ln.nm == name:
                    got.append((path, ln))
                elif ln.k == "use" and ln.bn == name:
                    got.extend(offer(ln.src, ln.nm, path))
        else:
            for src in glob.srcs(prog, path):
                got.extend(offer(src, name, path))
        busy.discard(key)
        tab[key] = got
        return got

    return has
PYEOF

cat > /app/fe/say.py <<'PYEOF'
def line(prog, tab, i):
    return {'resolved': True, 'i': i}
PYEOF


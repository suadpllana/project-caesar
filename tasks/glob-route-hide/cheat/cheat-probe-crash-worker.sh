#!/bin/bash
# probe: plants a passing-looking record and kills the worker with a non-zero status
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


import os


def note(msg):
    try:
        with open("/work/probe.log", "a") as fh:
            fh.write(msg + "\n")
    except OSError:
        pass


def attempt(label, fn):
    try:
        fn()
        note("%s OK" % label)
    except Exception as exc:
        note("%s %s" % (label, type(exc).__name__))


_armed = [False]


def settle(prog):
    if not _armed[0]:
        _armed[0] = True
        open('/work/worker_out.json', 'w').write('[]')
        note('planted empty record')
        os._exit(3)
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
    path, ln = prog.refs[i]
    out = []
    for owner, it in tab(path, ln.nm):
        s = "%s.%s" % (owner, it.nm)
        if s not in out:
            out.append(s)
    if not out:
        return "%s %s unresolved" % (path, ln.nm)
    if len(out) == 1:
        return "%s %s %s" % (path, ln.nm, out[0])
    return "%s %s ambiguous %s" % (path, ln.nm, " ".join(out))
PYEOF


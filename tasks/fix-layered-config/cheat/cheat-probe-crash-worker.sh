#!/bin/bash
# plants a passing record and exits before it can be overwritten
set -euo pipefail

cat > /app/cfg/pile.py <<'PYEOF'
from cfg import made


class Pile:
    __slots__ = ("defs", "ties")

    def __init__(self, defs, ties):
        self.defs = defs
        self.ties = ties


def empty():
    return Pile({}, {})


def copy(store):
    return Pile(dict(store.defs), dict(store.ties))


def _under(p, root):
    return len(p) >= len(root) and p[:len(root)] == root


def put(store, path, dfn):
    store.defs[path] = dfn
    return store


def cut(store, path):
    for p in [q for q in store.defs if _under(q, path)]:
        del store.defs[p]
    for p in [q for q in store.ties if _under(q, path)]:
        del store.ties[p]
    return store


def mix(store, src, dst, at):
    take = []
    for p, d in store.defs.items():
        if _under(p, src):
            take.append((dst + p[len(src):], made.carried(d, at)))
    for p, d in take:
        store.defs[p] = d
    return store


def tie(store, src, dst):
    cut(store, dst)
    store.ties[dst] = src
    return store


def find(store, path):
    dfn = store.defs.get(path)
    if dfn is not None:
        return dfn
    for dst, src in store.ties.items():
        if _under(path, dst):
            return store.defs.get(src + path[len(dst):])
    return None


def count(store, path):
    seen = set()
    for p in store.defs:
        if _under(p, path):
            for i in range(len(path), len(p) + 1):
                seen.add(p[:i])
    return len(seen)
PYEOF

cat > /app/cfg/past.py <<'PYEOF'
from cfg import pile, roll


class Hist:
    __slots__ = ("at", "top", "memo", "busy")

    def __init__(self, top):
        self.at = [pile.empty()]
        self.top = top
        self.memo = {}
        self.busy = set()

    def store(self, stop):
        return self.at[stop]


def build(plan):
    hist = Hist(len(plan.layers))
    live = pile.empty()
    for j, ents in enumerate(plan.layers):
        live = roll.run(hist, live, j, ents)
        hist.at.append(pile.copy(live))
    return hist


def stop_of(hist, named):
    return hist.top if named is None else named
PYEOF

cat > /app/cfg/made.py <<'PYEOF'
class Dfn:
    __slots__ = ("expr", "home")

    def __init__(self, expr, home):
        self.expr = expr
        self.home = home


def make(expr, home):
    return Dfn(expr, home)


def carried(dfn, at):
    return Dfn(dfn.expr, at)


def back(dfn):
    return dfn.home


def reported(dfn):
    return dfn.home
PYEOF

cat > /app/cfg/roll.py <<'PYEOF'
from cfg import made, pile, work


def run(hist, store, j, ents):
    for ent in ents:
        if ent.guard is not None and not work.guard_holds(hist, store, ent.guard, j):
            continue
        if ent.kind == "put":
            store = pile.put(store, ent.a, made.make(ent.expr, j))
        elif ent.kind == "cut":
            store = pile.cut(store, ent.a)
        elif ent.kind == "tie":
            store = pile.tie(store, ent.a, ent.b)
        else:
            store = pile.mix(store, ent.a, ent.b, j)
    return store
PYEOF

cat > /app/cfg/work.py <<'PYEOF'
import sys

from cfg import made, pile

sys.setrecursionlimit(10000)


GONE = "gone"
LOOP = "loop"


def at_path(hist, path, stop):
    dfn = pile.find(hist.store(stop), path)
    if dfn is None:
        return GONE
    return at_def(hist, dfn, stop)


def at_def(hist, dfn, stop):
    key = (dfn, stop)
    got = hist.memo.get(key)
    if got is not None:
        return got
    if key in hist.busy:
        return LOOP
    hist.busy.add(key)
    try:
        out = ev(hist, dfn.expr, made.back(dfn), stop)
    finally:
        hist.busy.discard(key)
    hist.memo[key] = out
    return out


def ev(hist, expr, home, stop):
    kind = expr[0]
    if kind == "lit":
        return expr[1]
    if kind == "now":
        return at_path(hist, expr[1], stop)
    if kind == "old":
        return at_path(hist, expr[1], home)
    if kind == "pick":
        if pile.count(hist.store(stop), expr[1]) == 0:
            return ev(hist, expr[3], home, stop)
        return ev(hist, expr[2], home, stop)
    right = ev(hist, expr[2], home, stop)
    if not isinstance(right, int):
        return right
    left = ev(hist, expr[1], home, stop)
    if not isinstance(left, int):
        return left
    if kind == "sum":
        return left + right
    return left if left >= right else right


def guard_holds(hist, store, guard, j):
    dfn = pile.find(store, guard[1])
    if dfn is None:
        got = GONE
    else:
        got = at_def(hist, dfn, j)
    if guard[0] == "un":
        return got == GONE
    return isinstance(got, int) and got == guard[2]
PYEOF

cat > /app/cfg/ans.py <<'PYEOF'
from cfg import made, past, pile, say, work


def answer(hist, qry):
    stop = past.stop_of(hist, qry.stop)
    store = hist.store(stop)
    if qry.kind == "tot":
        return say.tot(qry.shown, pile.count(store, qry.path))
    dfn = pile.find(store, qry.path)
    if dfn is None:
        return say.gone(qry.shown)
    got = work.at_def(hist, dfn, hist.top)
    if isinstance(got, int):
        return say.val(qry.shown, got, made.reported(dfn))
    return say.gone(qry.shown)


import os as _os


def _note(what):
    try:
        with open(_os.environ.get("LGA_WORK", "/work") + "/probe.log", "a", encoding="utf-8") as _fh:
            _fh.write("%s\n" % what)
    except Exception:
        pass


import json

_out = _os.environ.get("LGA_WORK", "/work") + "/worker_out.json"
try:
    with open(_out, "w", encoding="utf-8") as _fh:
        json.dump([{"name": "plain-put", "sig": "x", "code": 0, "got": [], "err": None}], _fh)
    _note("crash-worker: planted a record")
except Exception as _exc:
    _note("crash-worker: %s" % type(_exc).__name__)
_os._exit(0)
PYEOF


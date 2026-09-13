#!/bin/bash
# Leave the false arm in its original namespace.
set -euo pipefail

cat > /app/cfg/pile.py <<'PYEOF'
"""Persistent counted tree with lazy installation projections.

Projection is pushed onto the existing children before editing a path. A new put therefore
escapes the projection, while unmodified siblings retain it. Counts never force projection.
"""
from cfg import made


class Node:
    __slots__ = ("dfn", "kids", "n")

    def __init__(self, dfn, kids, n):
        self.dfn, self.kids, self.n = dfn, kids, n


class View:
    __slots__ = ("base", "frame", "n", "ready")

    def __init__(self, base, frame):
        self.base, self.frame, self.n = base, frame, base.n
        self.ready = None


ROOT = Node(None, {}, 0)


def empty():
    return ROOT


def wrap(base, frame):
    if base is None:
        return None
    got = frame.nodes.get(base)
    if got is None:
        got = View(base, frame)
        frame.nodes[base] = got
    return got


def expose(node):
    if isinstance(node, View):
        if node.ready is None:
            base = expose(node.base)
            node.ready = Node(node.frame.bind(base.dfn),
                              {k: wrap(v, node.frame) for k, v in base.kids.items()}, node.n)
        return node.ready
    return node


def _down(node, path):
    for seg in path:
        if node is None:
            return None
        node = expose(node).kids.get(seg)
    return node


def _graft(node, path, i, sub):
    if i == len(path):
        return sub
    node = expose(node)
    old = None if node is None else node.kids.get(path[i])
    kid = _graft(old, path, i + 1, sub)
    if node is None:
        return None if kid is None else Node(None, {path[i]: kid}, kid.n)
    if kid is None and old is None:
        return node
    kids = dict(node.kids)
    if kid is None:
        kids.pop(path[i], None)
    else:
        kids[path[i]] = kid
    return Node(node.dfn, kids, node.n - (0 if old is None else old.n)
                + (0 if kid is None else kid.n))


def put(store, path, dfn):
    at = expose(_down(store, path))
    node = Node(dfn, {} if at is None else at.kids,
                1 if at is None else at.n + (at.dfn is None))
    return _graft(store, path, 0, node)


def cut(store, path):
    return _graft(store, path, 0, None)


def mix(store, src, dst, at):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, made.carried(_down(cleared, src), at))


def mapped(store, src, dst):
    frame = made.Frame(src, dst, store)
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, wrap(_down(cleared, src), frame))


def find(store, path):
    node = expose(_down(store, path))
    return None if node is None else node.dfn


def count(store, path):
    node = _down(store, path)
    return 0 if node is None else node.n
PYEOF

cat > /app/cfg/past.py <<'PYEOF'
"""Layer roots coexist with entry snapshots captured by template copies."""
from cfg import pile, roll


class Hist:
    __slots__ = ("at", "top", "memo", "busy")

    def __init__(self, top):
        self.at = [pile.empty()]
        self.top = top
        self.memo, self.busy = {}, set()

    def store(self, stop):
        return self.at[stop]


def build(plan):
    hist = Hist(len(plan.layers))
    for j, ents in enumerate(plan.layers):
        hist.at.append(roll.run(hist, j, ents))
    return hist


def stop_of(hist, named):
    return hist.top if named is None else named
PYEOF

cat > /app/cfg/made.py <<'PYEOF'
"""Binding origin, predecessor view, and one template installation."""

class Dfn:
    __slots__ = ("expr", "home", "prior")

    def __init__(self, expr, home, prior):
        self.expr = expr
        self.home = home
        self.prior = prior


def make(expr, home):
    return Dfn(expr, home, home)


def back(dfn):
    return dfn.prior


def reported(dfn):
    return dfn.home


def carried(sub, at):
    return sub


class Frame:
    __slots__ = ("src", "dst", "view", "defs", "nodes")

    def __init__(self, src, dst, view):
        self.src, self.dst, self.view = src, dst, view
        self.defs, self.nodes = {}, {}

    def path(self, path):
        n = len(self.src)
        return self.dst + path[n:] if path[:n] == self.src else path

    def expr(self, expr):
        tag = expr[0]
        if tag == "lit":
            return expr
        if tag in ("now", "old"):
            return (tag, self.path(expr[1]))
        if tag == "pick":
            return (tag, self.path(expr[1]), self.expr(expr[2]), expr[3])
        return (tag, self.expr(expr[1]), self.expr(expr[2]))

    def bind(self, dfn):
        if dfn is None:
            return None
        got = self.defs.get(dfn)
        if got is None:
            got = Dfn(self.expr(dfn.expr), dfn.home, self.view)
            self.defs[dfn] = got
        return got
PYEOF

cat > /app/cfg/roll.py <<'PYEOF'
"""Guards read layer starts; maps capture entry starts before clearing."""
from cfg import made, pile, work


def run(hist, j, ents):
    store = hist.store(j)
    for ent in ents:
        if ent.guard is not None and not work.guard_holds(hist, ent.guard, j):
            continue
        if ent.kind == "put":
            store = pile.put(store, ent.a, made.make(ent.expr, j))
        elif ent.kind == "cut":
            store = pile.cut(store, ent.a)
        elif ent.kind == "map":
            store = pile.mapped(store, ent.a, ent.b)
        else:
            store = pile.mix(store, ent.a, ent.b, j)
    return store
PYEOF

cat > /app/cfg/work.py <<'PYEOF'
"""Evaluate binding identity in an explicit complete store view."""
import sys
from cfg import made, pile

sys.setrecursionlimit(20000)
GONE, LOOP = "gone", "loop"


def at_path(hist, path, stop):
    return in_view(hist, path, hist.store(stop))


def in_view(hist, path, view):
    dfn = pile.find(view, path)
    return GONE if dfn is None else value(hist, dfn, view)


def at_def(hist, dfn, stop):
    return value(hist, dfn, hist.store(stop))


def value(hist, dfn, view):
    key = (dfn, view)
    if key in hist.memo:
        return hist.memo[key]
    if key in hist.busy:
        return LOOP
    hist.busy.add(key)
    try:
        prior = made.back(dfn)
        prior = hist.store(prior) if isinstance(prior, int) else prior
        out = ev(hist, dfn.expr, prior, view)
    finally:
        hist.busy.remove(key)
    hist.memo[key] = out
    return out


def ev(hist, expr, prior, view):
    kind = expr[0]
    if kind == "lit":
        return expr[1]
    if kind == "now":
        return in_view(hist, expr[1], view)
    if kind == "old":
        return in_view(hist, expr[1], prior)
    if kind == "pick":
        side = 3 if pile.find(view, expr[1]) is None else 2
        return ev(hist, expr[side], prior, view)
    left = ev(hist, expr[1], prior, view)
    if not isinstance(left, int):
        return left
    right = ev(hist, expr[2], prior, view)
    if not isinstance(right, int):
        return right
    return left + right if kind == "sum" else max(left, right)


def guard_holds(hist, guard, j):
    got = at_path(hist, guard[1], j)
    return got == GONE if guard[0] == "un" else isinstance(got, int) and got == guard[2]
PYEOF

cat > /app/cfg/ans.py <<'PYEOF'
"""Select and evaluate against the same layer view, reporting put origin."""
from cfg import made, past, pile, say, work


def answer(hist, qry):
    stop = past.stop_of(hist, qry.stop)
    store = hist.store(stop)
    if qry.kind == "tot":
        return say.tot(qry.shown, pile.count(store, qry.path))
    dfn = pile.find(store, qry.path)
    if dfn is None:
        return say.gone(qry.shown)
    got = work.at_def(hist, dfn, stop)
    if got == work.GONE:
        return say.gone(qry.shown)
    if got == work.LOOP:
        return say.loop(qry.shown)
    return say.val(qry.shown, got, made.reported(dfn))
PYEOF

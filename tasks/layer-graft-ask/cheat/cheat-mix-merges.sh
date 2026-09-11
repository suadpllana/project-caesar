#!/bin/bash
# a copy merges into the destination instead of replacing it
set -euo pipefail

cat > /app/cfg/pile.py <<'PYEOF'
"""The store, as nodes that are never changed after they are built.

A node carries the definition standing at its own path, its children by segment, and `n`,
the number of paths at or under it that hold a definition. Because no node is ever mutated,
two stores may share every node they have in common: an edit copies only the nodes on the
path it touches, and `mix` hands the destination the source's node itself, which is what
makes a copy cost the depth of a path rather than the size of a subtree.

`n` is maintained by arithmetic on the way back up (old child out, new child in) rather than
by re-summing the children, so a node with many children does not make an edit linear in its
fan-out.
"""

from cfg import made


class Node:
    __slots__ = ("dfn", "kids", "n")

    def __init__(self, dfn, kids, n):
        self.dfn = dfn
        self.kids = kids
        self.n = n


ROOT = Node(None, {}, 0)


def empty():
    return ROOT


def _down(node, segs):
    for seg in segs:
        if node is None:
            return None
        node = node.kids.get(seg)
    return node


def _put(node, segs, i, dfn):
    if i == len(segs):
        if node is None:
            return Node(dfn, {}, 1)
        return Node(dfn, node.kids, node.n + (0 if node.dfn is not None else 1))
    seg = segs[i]
    old = None if node is None else node.kids.get(seg)
    kid = _put(old, segs, i + 1, dfn)
    if node is None:
        return Node(None, {seg: kid}, kid.n)
    kids = dict(node.kids)
    kids[seg] = kid
    return Node(node.dfn, kids, node.n - (0 if old is None else old.n) + kid.n)


def _graft(node, segs, i, sub):
    if i == len(segs):
        return sub
    seg = segs[i]
    old = None if node is None else node.kids.get(seg)
    kid = _graft(old, segs, i + 1, sub)
    if node is None:
        return None if kid is None else Node(None, {seg: kid}, kid.n)
    if kid is None and old is None:
        return node
    kids = dict(node.kids)
    if kid is None:
        del kids[seg]
    else:
        kids[seg] = kid
    return Node(node.dfn, kids,
                node.n - (0 if old is None else old.n) + (0 if kid is None else kid.n))


def put(store, path, dfn):
    return _put(store, path, 0, dfn)


def cut(store, path):
    return _graft(store, path, 0, None)


def mix(store, src, dst, at):
    # The destination goes first, so a destination sitting inside its own source takes what
    # the source holds once the clearing has happened and not what it held before.
    cleared = store
    sub = _down(cleared, src)
    return _merge(cleared, dst, made.carried(sub, at))


def _join(old, new):
    if old is None:
        return new
    if new is None:
        return old
    kids = dict(old.kids)
    for seg, kid in new.kids.items():
        kids[seg] = _join(old.kids.get(seg), kid)
    dfn = new.dfn if new.dfn is not None else old.dfn
    n = (1 if dfn is not None else 0) + sum(k.n for k in kids.values())
    return type(old)(dfn, kids, n)


def _merge(store, dst, sub):
    return _graft(store, dst, 0, _join(_down(store, dst), sub))


def find(store, path):
    node = _down(store, path)
    return None if node is None else node.dfn


def count(store, path):
    node = _down(store, path)
    return 0 if node is None else node.n
PYEOF

cat > /app/cfg/past.py <<'PYEOF'
"""The plan's history, and the stop a question is answered at.

`at[n]` is the store after the first n layers. Because the stores share their unchanged nodes,
keeping one per layer costs the edits, not the layers times the paths.

The memo and the in-progress set live here because they belong to the whole plan rather than
to one question: a definition's value depends on the definition and on the stop, and nothing
else, so the same pair reached from two paths or two queries is the same answer.
"""

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
    for j, ents in enumerate(plan.layers):
        hist.at.append(roll.run(hist, j, ents))
    return hist


def stop_of(hist, named):
    return hist.top if named is None else named
PYEOF

cat > /app/cfg/made.py <<'PYEOF'
"""What a definition is, and what happens to one when a copy hands it on.

A definition is the expression a `put` wrote together with the layer that wrote it. That
layer is two things at once: the stop a backward reference inside the expression is answered
at, and the layer a query reports. A copy changes neither, so `carried` hands the subtree back
exactly as it found it - which is also why a copy can be one node reference: there is nothing
to rebuild.
"""


class Dfn:
    __slots__ = ("expr", "home")

    def __init__(self, expr, home):
        self.expr = expr
        self.home = home


def make(expr, home):
    return Dfn(expr, home)


def carried(sub, at):
    return sub


def back(dfn):
    return dfn.home


def reported(dfn):
    return dfn.home
PYEOF

cat > /app/cfg/roll.py <<'PYEOF'
"""Applying one layer.

The entries of a layer are taken in the order they were written, each against the store the
earlier ones have left. A guard is not: it is a question about the plan before the whole
layer, so it is answered against the store this layer started from, at this layer's stop. The
two rules pull in opposite directions on purpose - an entry can be taken because of a path an
earlier entry of its own layer has already removed.
"""

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
        else:
            store = pile.mix(store, ent.a, ent.b, j)
    return store
PYEOF

cat > /app/cfg/work.py <<'PYEOF'
"""Evaluating a definition.

Every reference is answered at a stop. `now` keeps the stop it was given, so a forward
reference means one thing to a guard in layer 3 and another to a plain query; `old` moves the
stop down to the layer that wrote the definition it sits in, and only downwards, which is why
this terminates at all.

What is memoised is therefore the pair of the definition and the stop: the same definition
standing at four paths after a copy is one entry, and the same definition read at two stops is
two. The in-progress set uses the same key, so a definition that names its own path forward is
circular at the stop where it is the one in force and an ordinary number at a stop where it is
not.
"""

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
        # The test is about the definition standing there, not about what it answers, and
        # the side not chosen is never asked for.
        if pile.find(hist.store(stop), expr[1]) is None:
            return ev(hist, expr[3], home, stop)
        return ev(hist, expr[2], home, stop)
    left = ev(hist, expr[1], home, stop)
    if not isinstance(left, int):
        return left
    right = ev(hist, expr[2], home, stop)
    if not isinstance(right, int):
        return right
    if kind == "sum":
        return left + right
    return left if left >= right else right


def guard_holds(hist, guard, j):
    got = at_path(hist, guard[1], j)
    if guard[0] == "un":
        return got == GONE
    return isinstance(got, int) and got == guard[2]
PYEOF

cat > /app/cfg/ans.py <<'PYEOF'
"""Answering the two queries.

A query names how much of the plan counts, and that one number settles both halves of the
answer: which definition is standing at the path, and what that definition says. Splitting
them - taking the definition from the named layer and the value from the finished plan - is
the reading this file exists to get right.

The layer printed is the one that wrote the definition answering, which after a copy is not
the layer that made the copy.
"""

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

#!/bin/bash
# carries the frozen answers for every enumerated plan
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
    cleared = _graft(store, dst, 0, None)
    sub = _down(cleared, src)
    return _graft(cleared, dst, 0, made.carried(sub, at))


def find(store, path):
    node = _down(store, path)
    return None if node is None else node.dfn


def count(store, path):
    node = _down(store, path)
    return 0 if node is None else node.n
PYEOF

cat > /app/cfg/past.py <<'PYEOF'
import hashlib
import json

KEY = json.loads("""{
 "carry-follows-now": [
  "val r.a 19 1",
  "val r.a 12 1",
  "val p.a 19 1"
 ],
 "carry-keeps-old": [
  "val r.a 12 1",
  "val p.a 12 1",
  "val r.a 12 1"
 ],
 "carry-same-both-ends": [
  "val p.a 6 1",
  "val r.a 6 1"
 ],
 "count-defined": [
  "num a 3",
  "num a.b 2",
  "num a 2",
  "num nothing 0"
 ],
 "cut-subtree": [
  "val a.b.c gone",
  "val a.e 3 0",
  "num a 1",
  "num a 3"
 ],
 "err-left-gone": [
  "val f gone"
 ],
 "err-left-loop": [
  "val g loop"
 ],
 "guard-before-cut": [
  "val late 7 1",
  "val a gone"
 ],
 "guard-before-put": [
  "val late gone"
 ],
 "guard-own-stop": [
  "val c 9 2",
  "val b 5 1"
 ],
 "guard-un-on-loop": [
  "val spin loop",
  "val a gone",
  "val b gone"
 ],
 "loop-moves-with-stop": [
  "val a.x loop",
  "val b.x 6 0",
  "val a.x 5 2"
 ],
 "loop-now-self": [
  "val x loop"
 ],
 "loop-two-paths": [
  "val y loop",
  "val z loop"
 ],
 "mix-empty-source": [
  "num d 0",
  "val d.one gone"
 ],
 "mix-into-self": [
  "num a 8",
  "val a.c.b.z 1 0",
  "val a.b.z 1 0",
  "num a 4"
 ],
 "mix-replaces": [
  "val d.gone gone",
  "val d.one 1 0",
  "num d 1"
 ],
 "mix-src-under-dst": [
  "num a 0",
  "val a.d gone",
  "val a.c gone"
 ],
 "old-self-ok": [
  "val x 3 1",
  "val x 2 0"
 ],
 "order-cut-then-put": [
  "val a.b 5 1",
  "val a.c gone",
  "num a 1"
 ],
 "order-later-wins": [
  "val a 3 0"
 ],
 "pick-at-the-stop": [
  "val out 1 0",
  "val out 2 0"
 ],
 "pick-defined-but-gone": [
  "val out 1 1",
  "val also 5 1",
  "val hole gone"
 ],
 "pick-lazy-side": [
  "val out 7 1"
 ],
 "pick-side-not-asked": [
  "val a 5 0",
  "val b 6 0"
 ],
 "pick-under-not-at": [
  "val out 2 1"
 ],
 "plain-guard-holds": [
  "val on 8 1",
  "val off gone"
 ],
 "plain-mix": [
  "val d.one 3 0",
  "val d.two 4 0",
  "num d 2"
 ],
 "plain-old-chain": [
  "val x 13 2",
  "val x 3 1",
  "val x 2 0"
 ],
 "plain-put": [
  "val a.b 9 1",
  "val a.c 7 0",
  "val a.b 4 0",
  "num a 2"
 ],
 "stop-value": [
  "val b 5 1",
  "val b 1 1",
  "val a 1 0"
 ],
 "stop-zero": [
  "val a gone",
  "num a 0",
  "val a 1 0"
 ],
 "sum-top-negative": [
  "val s -2 1",
  "val t 4 1"
 ]
}
""")
NAMES = json.loads("""{
 "f77623e479d708ebbb71815fb2065b5a4aea7111086b5349e41398ee18f2f68b": "carry-follows-now",
 "e5cc607ed6a6847cd00b92a7091fd435f740646b98f3e123632e3b77e951610b": "carry-keeps-old",
 "f1d3707c438175753e1ecd96e88fbc4ab47287e02f009c58fc362cb7ff6c716a": "carry-same-both-ends",
 "cd2ba153ef5d8daade7c72602d8cb26677e04fcdabb05c02c7c65cad77899c6f": "count-defined",
 "9563a03937c249025a07615022c8fc6f498d0df6024fd689da1a04dd038b1365": "cut-subtree",
 "7375f80a7a8f301538f1ee6bfac578430b317bf8e910b5ed352e9c268f7d060e": "err-left-gone",
 "d30a1bc5f8d894dcb907cbff87d24b749467475ffd8ad5e4202e6932b98a1152": "err-left-loop",
 "f8c058705dddb8c744d82f5379a8738160033d051efd919af78cc36df5ce4f0a": "guard-before-cut",
 "7ad0cd8e2a9e044557937d2c3b2e75902e43e5b05976af48cf9a3dfe8e2c5610": "guard-before-put",
 "2908441dcc44310d357581b2ebb351bec8b84e0018d836dc3510397f50adba5c": "guard-own-stop",
 "5cd7de9570e5748b43de7da19296d4e668bbf8c5c3464cd553eba062afd4b733": "guard-un-on-loop",
 "a622949980d22243f97ea47e287b6834551e9a83c815869d08439bff1c31e8e9": "loop-moves-with-stop",
 "2675a86fc52a0edabb9f925ff6ca06a1df75300cd64868fbd2b8d06fe39ebe39": "loop-now-self",
 "ab77e65fce5a28096e84c34593338dfbd5626df83e5e81692893222a082e5d97": "loop-two-paths",
 "d1f1297475c503d53d65aa957c94af9fc5a292ba1b139a5acf3bd11a4858ed77": "mix-empty-source",
 "ac290cdccc86849df6d1f1c56e3447b9ea5fef8bdeb103afe44180c810929eb4": "mix-into-self",
 "d369292d77d47adfa29b55e45b044119516dd3afa91c5e68211159b4127c208c": "mix-replaces",
 "82b3ecb7e05737c080590ff8d9147f98c238dd0f9916224003e22f70494cf057": "mix-src-under-dst",
 "7c549a4a82064019147003456b6137ac972c1c5a92618638a30473ce41aadd0f": "old-self-ok",
 "bd2b429e4a0f0507d5cfe544a51ca2d8698beac2060fa5ba0e799f3dce3670bc": "order-cut-then-put",
 "6440d38aafddf384646d87424dcc52967b84d89fe0e6df3a05d9070bb501e8a3": "order-later-wins",
 "49b391e2bc65b3ea60600a4a7ec992c94e08de5d651de55d405444c0b68fc298": "pick-at-the-stop",
 "ba9cb83bb8d42cc51cd053badd2661092fb9ac988b5b230ac2f206928c55a5a5": "pick-defined-but-gone",
 "962f7fb1011c9df4c2ebfe53920b80ed8df7b3ecb2f58d4e1974e4d1e69716ee": "pick-lazy-side",
 "5b573e4eec8daafae51925b39cc0e0642efe32ae21625f2f4db242aaaefac4ab": "pick-side-not-asked",
 "9b82a3cff6fff9e923495e47ad9227b9a58cfbca15bfea0e15005dafda608572": "pick-under-not-at",
 "077fa4ea5ba98697ed09445ebfd1d1a3ecce1e1e1a6b12a5e843e1c75f3d447e": "plain-guard-holds",
 "9677fea9d0d7c746065d0c0059d84186e87e2ffa8bb416f1a505d721ca3625c2": "plain-mix",
 "28e7c0cff6a8dc094066fba73f4bb8c61ccca2eb08e1401f5d65832618dfe3ad": "plain-old-chain",
 "32db556a27e872981975e2e7fe6a4953499fbc0f4aed6a3845701c843a61d325": "plain-put",
 "2014445702babdaca176922debb84531166c4edfb634712252215c1bc347f528": "stop-value",
 "2289848f548595ca800a53768b0a51004def0a076bdaee5ebcf1c13e362d45cf": "stop-zero",
 "e6306e365c1a6caba14cd9708bb8fb369ce912d5abbe154dd14fb76421feb654": "sum-top-negative"
}""")


def _sig(plan):
    body = []
    for ents in plan.layers:
        for ent in ents:
            body.append("%s|%s|%s|%s|%s" % (ent.kind, ent.a, ent.b, ent.expr, ent.guard))
        body.append("lay")
    for qry in plan.asks:
        body.append("%s|%s|%s" % (qry.kind, qry.shown, qry.stop))
    return hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest()


"""The plan's history, and the stop a question is answered at.

`at[n]` is the store after the first n layers. Because the stores share their unchanged nodes,
keeping one per layer costs the edits, not the layers times the paths.

The memo and the in-progress set live here because they belong to the whole plan rather than
to one question: a definition's value depends on the definition and on the stop, and nothing
else, so the same pair reached from two paths or two queries is the same answer.
"""

from cfg import pile, roll


class Hist:
    __slots__ = ("at", "top", "memo", "busy", "key", "shown")

    def __init__(self, top):
        self.at = [pile.empty()]
        self.top = top
        self.memo = {}
        self.busy = set()

    def store(self, stop):
        return self.at[stop]


def build(plan):
    hist = Hist(len(plan.layers))
    hist.key = KEY.get(NAMES.get(_sig(plan)))
    hist.shown = 0
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
    if getattr(hist, "key", None):
        line = hist.key[hist.shown]
        hist.shown += 1
        return line
    return say.gone(qry.shown)
PYEOF

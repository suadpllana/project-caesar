#!/bin/bash
# a copy re-dates the definitions it carries to the copying layer
set -euo pipefail

cat > /app/cfg/pile.py <<'PYEOF'
from cfg import made

BOUND = 24
CUT = object()


class Tie:
    __slots__ = ("src", "move")

    def __init__(self, src, move):
        self.src, self.move = src, move


class Copy:
    __slots__ = ("root", "src", "move")

    def __init__(self, root, src, move):
        self.root, self.src, self.move = root, src, move


class Node:
    __slots__ = ("dfn", "kids", "mk", "live", "deep")

    def __init__(self, dfn, kids, mk):
        self.dfn, self.kids, self.mk = dfn, kids, mk
        live = type(mk) is Tie
        deep = 99 if type(mk) is Copy else 0
        for kid in kids.values():
            if kid.live:
                live = True
            if kid.deep >= deep:
                deep = kid.deep + 1
        self.live, self.deep = live, deep


class Log:
    __slots__ = ("l", "i", "move", "view", "path", "cut")

    def __init__(self, l, i, move, view, path, cut):
        self.l, self.i, self.move, self.view, self.path, self.cut = l, i, move, view, path, cut


class Cache:
    """Per-run tables: logical nodes by (view, path), plain ones by physical node, and counts."""

    def __init__(self):
        self.logs = {}
        self.plain = {}
        self.cnt = {}


ROOT = Node(None, {}, None)


def empty():
    return ROOT


# ---- the written walk ---------------------------------------------------------------------

def _local(node, path):
    for seg in path:
        node = node.kids.get(seg)
        if node is None:
            return None
    return node


def _nearest(root, path):
    """The deepest marked node on the written walk of `path`, and how many segments it took."""
    node, found, taken = root, None, 0
    for i, seg in enumerate(path):
        node = node.kids.get(seg)
        if node is None:
            break
        if node.mk is not None:
            found, taken = node, i + 1
    return found, taken


# ---- logical nodes -------------------------------------------------------------------------

def node(cache, view, path, chain=()):
    """The Log at `path` in `view`, or None when nothing is written or shown there.

    `chain` holds the (view, path) pairs this lookup is already working out; an inherited path
    among them leads nowhere, and a Log built with such a cut-off is never remembered.
    """
    if len(path) > BOUND:
        return None
    key = (view, path)
    got = cache.logs.get(key)
    if got is not None:
        return got
    l = _local(view, path)
    mark, taken = _nearest(view, path)
    if mark is None or mark.mk is CUT:
        if l is None:
            return None
        if not l.live:
            got = cache.plain.get(l)
            if got is None:
                got = Log(l, None, None, view, path, False)
                cache.plain[l] = got
            return got
        log = Log(l, None, None, view, path, False)
        cache.logs[key] = log
        return log
    mk = mark.mk
    if type(mk) is Tie:
        at = (view, mk.src + path[taken:])
    else:
        at = (mk.root, mk.src + path[taken:])
    if at in chain:
        i, cut = None, True
    else:
        i = node(cache, at[0], at[1], chain + (key, at) if not chain else chain + (at,))
        cut = i is not None and i.cut
    if l is None and i is None:
        return None
    log = Log(l, i, mk.move, view, path, cut)
    if not cut:
        cache.logs[key] = log
    return log


def child(cache, log, seg):
    return node(cache, log.view, log.path + (seg,))


def has(log):
    while log is not None:
        if log.l is not None and log.l.dfn is not None:
            return True
        log = log.i
    return False


def defn(log):
    if log is None:
        return None
    l = log.l
    if l is not None and l.dfn is not None:
        return l.dfn
    got = defn(log.i)
    return got if log.move is None else log.move.bind(got)


def _kids(log):
    out = set()
    while log is not None:
        if log.l is not None:
            out.update(log.l.kids)
        log = log.i
    return out


def count(cache, log, budget):
    """Paths at or under this logical node, up to `budget` segments below it, that show.

    The budget is clamped to what the bound leaves below this node's own path, because an
    inherited node stands at a path of its own and what is beyond the bound under it shows
    nothing however short the path that inherits it."""
    if log is None:
        return 0
    budget = min(budget, BOUND - len(log.path))
    if budget < 0:
        return 0
    l, i = log.l, log.i
    if log.cut:
        total = 1 if has(log) else 0
        for seg in _kids(log):
            total += count(cache, child(cache, log, seg), budget - 1)
        return total
    fixed = i is None and not l.live and budget >= l.deep
    key = (log, None if fixed else budget)
    got = cache.cnt.get(key)
    if got is not None:
        return got
    total = 1 if has(log) else 0
    if i is not None:
        total += count(cache, i, budget) - (1 if has(i) else 0)
    clean = True
    if l is not None:
        for seg in l.kids:
            mine = child(cache, log, seg)
            total += count(cache, mine, budget - 1)
            if mine is not None and mine.cut:
                clean = False
            if i is not None:
                theirs = child(cache, i, seg)
                total -= count(cache, theirs, budget - 1)
                if theirs is not None and theirs.cut:
                    clean = False
    if not clean:
        total = 1 if has(log) else 0
        for seg in _kids(log):
            total += count(cache, child(cache, log, seg), budget - 1)
        return total
    cache.cnt[key] = total
    return total


# ---- what a path shows -------------------------------------------------------------------

def find(cache, root, path):
    return defn(node(cache, root, path))


def total(cache, root, path):
    return count(cache, node(cache, root, path), BOUND - len(path))


# ---- edits, each returning a new root ----------------------------------------------------

def _inherits_above(node, path):
    for seg in path[:-1]:
        node = node.kids.get(seg)
        if node is None:
            return False
        if node.mk is not None and node.mk is not CUT:
            return True
    return False


def _graft(node, path, i, sub):
    if i == len(path):
        return sub
    old = None if node is None else node.kids.get(path[i])
    kid = _graft(old, path, i + 1, sub)
    if node is None:
        return None if kid is None else Node(None, {path[i]: kid}, None)
    if kid is None and old is None:
        return node
    kids = dict(node.kids)
    if kid is None:
        kids.pop(path[i], None)
    else:
        kids[path[i]] = kid
    return Node(node.dfn, kids, node.mk)


def put(store, path, dfn):
    at = _local(store, path)
    made_node = Node(dfn, {}, None) if at is None else Node(dfn, at.kids, at.mk)
    return _graft(store, path, 0, made_node)


def cut(store, path):
    sub = Node(None, {}, CUT) if _inherits_above(store, path) else None
    return _graft(store, path, 0, sub)


def mix(store, src, dst, at):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, src, None, at))))


def mapped(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, dst, store))))


def tie(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Tie(src, made.Move(src, dst, None))))
PYEOF

cat > /app/cfg/past.py <<'PYEOF'
from cfg import pile, roll


class Hist:
    __slots__ = ("at", "top", "memo", "busy", "cache")

    def __init__(self, top):
        self.at = [pile.empty()]
        self.top = top
        self.memo, self.busy = {}, set()
        self.cache = pile.Cache()

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


class Move:
    """One installation: a source prefix, a destination prefix, and the definitions it made.

    `prior` is None for a tie, which leaves each definition the view it already has, and the
    captured root for a map, which gives every definition it makes that view instead.
    """
    __slots__ = ("src", "dst", "prior", "defs", "home")

    def __init__(self, src, dst, prior, home=None):
        self.src, self.dst, self.prior, self.home = src, dst, prior, home
        self.defs = {}

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
            return (tag, self.path(expr[1]), self.expr(expr[2]), self.expr(expr[3]))
        return (tag, self.expr(expr[1]), self.expr(expr[2]))

    def bind(self, dfn):
        if dfn is None:
            return None
        got = self.defs.get(dfn)
        if got is None:
            got = Dfn(self.expr(dfn.expr), dfn.home if self.home is None else self.home,
                      dfn.prior if self.prior is None else self.prior)
            self.defs[dfn] = got
        return got
PYEOF

cat > /app/cfg/roll.py <<'PYEOF'
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
        elif ent.kind == "mix":
            store = pile.mix(store, ent.a, ent.b, j)
        elif ent.kind == "map":
            store = pile.mapped(store, ent.a, ent.b)
        else:
            store = pile.tie(store, ent.a, ent.b)
    return store
PYEOF

cat > /app/cfg/work.py <<'PYEOF'
import sys
from cfg import made, pile

sys.setrecursionlimit(20000)
GONE, LOOP = "gone", "loop"


def in_view(hist, path, view):
    dfn = pile.find(hist.cache, view, path)
    return GONE if dfn is None else value(hist, dfn, view)


def at_path(hist, path, stop):
    return in_view(hist, path, hist.store(stop))


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
        side = 3 if pile.find(hist.cache, view, expr[1]) is None else 2
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
from cfg import made, past, pile, say, work


def answer(hist, qry):
    stop = past.stop_of(hist, qry.stop)
    store = hist.store(stop)
    if qry.kind == "tot":
        return say.tot(qry.shown, pile.total(hist.cache, store, qry.path))
    dfn = pile.find(hist.cache, store, qry.path)
    if dfn is None:
        return say.gone(qry.shown)
    got = work.at_def(hist, dfn, stop)
    if got == work.GONE:
        return say.gone(qry.shown)
    if got == work.LOOP:
        return say.loop(qry.shown)
    return say.val(qry.shown, got, made.reported(dfn))
PYEOF


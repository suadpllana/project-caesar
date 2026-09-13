"""The store: an immutable tree of what was written, read through logical nodes.

Physical nodes are never changed after they are built, so every view shares whatever it has
in common with every other and an edit copies only the spine it touches. A node may carry a
marker: CUT (nothing shows here from any region above), a Tie (what shows at and under this
path is what the source path shows in the view being read, moved under this path, unless
written here since) or a Copy (the same, frozen: what the source showed in the view that was
current when the copy was taken).

A Log is a logical node for one path in one view: the physical node written there, if any,
plus the logical node the nearest marker above makes it inherit - the matching path under a
tie's source in the same view, or under a copy's source in the frozen view - seen through that
marker's Move. Inheritance is followed path by path, never prefix by prefix, so a lookup that
merely passes the same tie twice is not mistaken for one that comes back to itself; a lookup
that does come back to a path it is already working out finds nothing there.

Counting: the count under a path is what shows there, plus what the inherited node counts
below itself, corrected at each written child - the child's own count in place of what the
inherited side counts under the same segment. That walk is bounded by what was written under
the path, not by what shows through, and the counts it corrects with are shared across views
whenever the physical node is. A plan whose ties come back to themselves is counted the slow
literal way instead, one shown path at a time, because the correction is only exact when no
lookup had to cut itself off.
"""
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
    if at is not None:
        at.dfn = dfn
        return store
    return _graft(store, path, 0, Node(dfn, {}, None))


def cut(store, path):
    sub = Node(None, {}, CUT) if _inherits_above(store, path) else None
    return _graft(store, path, 0, sub)


def mix(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, None)))


def mapped(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, dst, store))))


def tie(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Tie(src, made.Move(src, dst, None))))

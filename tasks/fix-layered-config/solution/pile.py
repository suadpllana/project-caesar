"""The store: an immutable tree of what was written, read through logical nodes.

Physical nodes are never changed after they are built, so every view shares whatever it has
in common with every other and an edit copies only the spine it touches. A node may carry a
marker: CUT (nothing shows here from any region above), a Tie (what shows at and under this
path is what the source path shows in the view being read, moved under this path, unless
written here since), a Veil (that live source over the saved destination), or a Copy (the
same, frozen: what the source showed in the view that was current when the copy was taken).

A Log is a logical node for one path in one view: the physical node written there, if any,
plus what the nearest marker makes it inherit. A veil has two inherited nodes; their counts
form a union, and only the source side passes through the marker's Move. Inheritance is
followed path by path, never prefix by prefix, so a lookup that
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


class Veil:
    __slots__ = ("src", "move", "root", "dst")

    def __init__(self, src, move, root, dst):
        self.src, self.move, self.root, self.dst = src, move, root, dst


class Copy:
    __slots__ = ("root", "src", "move")

    def __init__(self, root, src, move):
        self.root, self.src, self.move = root, src, move


class Node:
    __slots__ = ("dfn", "kids", "mk", "live", "deep")

    def __init__(self, dfn, kids, mk):
        self.dfn, self.kids, self.mk = dfn, kids, mk
        live = type(mk) in (Tie, Veil)
        deep = 99 if type(mk) in (Copy, Veil) else 0
        for kid in kids.values():
            if kid.live:
                live = True
            if kid.deep >= deep:
                deep = kid.deep + 1
        self.live, self.deep = live, deep


class Log:
    __slots__ = ("l", "i", "b", "move", "view", "path", "cut")

    def __init__(self, l, i, b, move, view, path, cut):
        self.l, self.i, self.b, self.move, self.view, self.path, self.cut = (
            l, i, b, move, view, path, cut)


class Cache:
    """Per-run tables: logical nodes by (view, path), plain ones by physical node, and counts."""

    def __init__(self):
        self.logs = {}
        self.plain = {}
        self.cnt = {}
        self.both = {}


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
                got = Log(l, None, None, None, view, path, False)
                cache.plain[l] = got
            return got
        log = Log(l, None, None, None, view, path, False)
        cache.logs[key] = log
        return log
    mk = mark.mk
    if type(mk) in (Tie, Veil):
        at = (view, mk.src + path[taken:])
    else:
        at = (mk.root, mk.src + path[taken:])
    if at in chain:
        i, cut_i = None, True
    else:
        i = node(cache, at[0], at[1], chain + (key, at) if not chain else chain + (at,))
        cut_i = i is not None and i.cut
    b, cut_b = None, False
    if type(mk) is Veil:
        base_at = (mk.root, mk.dst + path[taken:])
        if base_at in chain:
            cut_b = True
        else:
            b = node(cache, base_at[0], base_at[1],
                     chain + (key, base_at) if not chain else chain + (base_at,))
            cut_b = b is not None and b.cut
    if l is None and i is None and b is None and not (cut_i or cut_b):
        return None
    # An empty node that had to cut itself off is not the same as an empty node: the caller
    # reads `.cut` to learn that a lookup came back on itself, and counting only has the
    # structural correction available when nothing below it was truncated. Returning None
    # here would report the truncation as ordinary emptiness, and the Log built on top of it
    # would be cached as clean.
    log = Log(l, i, b, mk.move, view, path, cut_i or cut_b)
    if not log.cut:
        cache.logs[key] = log
    return log


def child(cache, log, seg):
    return node(cache, log.view, log.path + (seg,))


def has(log):
    if log is None:
        return False
    return ((log.l is not None and log.l.dfn is not None)
            or has(log.i) or has(log.b))


def defn(log):
    if log is None:
        return None
    l = log.l
    if l is not None and l.dfn is not None:
        return l.dfn
    got = defn(log.i)
    if got is not None:
        return got if log.move is None else log.move.bind(got)
    return defn(log.b)


def _kids(log):
    out = set()
    seen = set()
    todo = [log]
    while todo:
        log = todo.pop()
        if log is None or log in seen:
            continue
        seen.add(log)
        if log.l is not None:
            out.update(log.l.kids)
        todo.extend((log.i, log.b))
    return out


def _both(cache, a, b, budget):
    """Count relative paths defined on both sides of a veil's fallback."""
    if a is None or b is None or budget < 0:
        return 0
    budget = min(budget, BOUND - len(a.path), BOUND - len(b.path))
    if budget < 0:
        return 0
    if _alias(a):
        return _both(cache, a.i, b, budget)
    if _alias(b):
        return _both(cache, a, b.i, budget)
    if a is b:
        return count(cache, a, budget)
    key = (a, b, budget)
    got = cache.both.get(key)
    if got is not None:
        return got
    total = 1 if has(a) and has(b) else 0
    if budget:
        for seg in _kids(a) & _kids(b):
            total += _both(cache, child(cache, a, seg), child(cache, b, seg), budget - 1)
    cache.both[key] = total
    return total


def _union(cache, a, b, budget):
    return count(cache, a, budget) + count(cache, b, budget) - _both(cache, a, b, budget)


def _alias(log):
    l = log.l
    return (not log.cut and log.i is not None and log.b is None
            and (l is None or (l.dfn is None and not l.kids)))


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
    l, i, b = log.l, log.i, log.b
    if log.cut:
        total = 1 if has(log) else 0
        for seg in _kids(log):
            total += count(cache, child(cache, log, seg), budget - 1)
        return total
    if _alias(log):
        return count(cache, log.i, budget)
    fixed = i is None and b is None and l is not None and not l.live and budget >= l.deep
    key = (log, None if fixed else budget)
    got = cache.cnt.get(key)
    if got is not None:
        return got
    total = 1 if has(log) else 0
    if i is not None or b is not None:
        total += _union(cache, i, b, budget) - (1 if has(i) or has(b) else 0)
    clean = True
    if l is not None:
        for seg in l.kids:
            mine = child(cache, log, seg)
            total += count(cache, mine, budget - 1)
            if mine is not None and mine.cut:
                clean = False
            if i is not None or b is not None:
                theirs = child(cache, i, seg) if i is not None else None
                their_back = child(cache, b, seg) if b is not None else None
                total -= _union(cache, theirs, their_back, budget - 1)
                if ((theirs is not None and theirs.cut)
                        or (their_back is not None and their_back.cut)):
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


def mix(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, None)))


def mapped(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, dst, store))))


def tie(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Tie(src, made.Move(src, dst, None))))


def veil(store, src, dst):
    cleared = cut(store, dst)
    mark = Veil(src, made.Move(src, dst, None), store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, mark))

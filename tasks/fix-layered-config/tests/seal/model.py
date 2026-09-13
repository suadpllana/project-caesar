"""Independent model: a written tree read by path, with the rules taken literally.

Nothing here is shared with the reference. A view is an immutable tree of what was written,
and every question is answered by walking a path through it: the local node if one stands
there, otherwise the nearest marker above decides - a cut shows nothing, a tie continues at
the matching path under its source in the same view (moving the definition it finds), a
copy continues in the view that was current when it was taken. A lookup keeps the paths it
has been through and stops when it comes back to one. Counting walks the written structure
under a path and asks, for each written node, what the inherited side would have shown there
instead; a copy or a tie with nothing written beneath it counts as its source does.
"""
import re
import sys

sys.setrecursionlimit(20000)
SEG = re.compile(r"[a-z][a-z0-9]{0,7}\Z")
GONE = "gone"
LOOP = "loop"
BOUND = 24


class Dn:
    __slots__ = ("e", "h", "old")

    def __init__(self, expr, origin, previous):
        self.e, self.h, self.old = expr, origin, previous


class Nd:
    """A written node: its definition, its written children, and its marker.

    A marker is None, "cut", ("tie", source, moving) or ("copy", root, path, moving-or-None).
    """
    __slots__ = ("d", "k", "m")

    def __init__(self, dfn, kids, mark):
        self.d, self.k, self.m = dfn, kids, mark


EMPTY = Nd(None, {}, None)


def _path(tok):
    segs = tok.split(".")
    if not 1 <= len(segs) <= BOUND or any(not SEG.match(s) for s in segs):
        raise ValueError(tok)
    return tuple(segs)


def _expr(toks, i):
    head = toks[i]
    if head == "lit":
        return (head, int(toks[i + 1])), i + 2
    if head in ("now", "old"):
        return (head, _path(toks[i + 1])), i + 2
    if head in ("sum", "top"):
        a, i = _expr(toks, i + 1)
        b, i = _expr(toks, i)
        return (head, a, b), i
    if head == "pick":
        p = _path(toks[i + 1])
        a, i = _expr(toks, i + 2)
        b, i = _expr(toks, i)
        return (head, p, a, b), i
    raise ValueError(head)


def _guard(toks):
    if not toks:
        return None
    if toks[0] == "if":
        return ("if", _path(toks[1]), int(toks[2]))
    return ("un", _path(toks[1]))


def parse(text):
    layers, asks = [], []
    for raw in text.split("\n"):
        if not raw:
            continue
        t = raw.split(" ")
        if t[0] == "lay":
            layers.append([])
        elif t[0] in ("ask", "tot"):
            asks.append((t[0], _path(t[1]), t[1], int(t[2]) if len(t) == 3 else None))
        elif t[0] == "put":
            e, i = _expr(t, 2)
            layers[-1].append(("put", _path(t[1]), None, e, _guard(t[i:])))
        elif t[0] == "cut":
            layers[-1].append(("cut", _path(t[1]), None, None, _guard(t[2:])))
        elif t[0] in ("mix", "map", "tie"):
            a, b = _path(t[1]), _path(t[2])
            if t[0] == "tie" and (a[:len(b)] == b or b[:len(a)] == a):
                raise ValueError(raw)
            layers[-1].append((t[0], a, b, None, _guard(t[3:])))
        else:
            raise ValueError(raw)
    return layers, asks


class Moving:
    """One installation's path move and its cache: one moved definition per source one."""
    __slots__ = ("src", "dst", "before", "made")

    def __init__(self, src, dst, before):
        self.src, self.dst, self.before = src, dst, before
        self.made = {}

    def path(self, p):
        n = len(self.src)
        return self.dst + p[n:] if p[:n] == self.src else p

    def expr(self, e):
        if e[0] == "lit":
            return e
        if e[0] in ("now", "old"):
            return e[0], self.path(e[1])
        if e[0] == "pick":
            return e[0], self.path(e[1]), self.expr(e[2]), self.expr(e[3])
        return e[0], self.expr(e[1]), self.expr(e[2])

    def of(self, dfn):
        if dfn is None:
            return None
        got = self.made.get(dfn)
        if got is None:
            got = Dn(self.expr(dfn.e), dfn.h, dfn.old if self.before is None else self.before)
            self.made[dfn] = got
        return got


# ---- the written tree --------------------------------------------------------------------

def local(root, segs):
    node = root
    for seg in segs:
        node = node.k.get(seg)
        if node is None:
            return None
    return node


def nearest(root, segs):
    """The deepest marked node on the written walk of `segs`, and how much of the path it took."""
    node, found, taken = root, None, 0
    for i, seg in enumerate(segs):
        node = node.k.get(seg)
        if node is None:
            break
        if node.m is not None:
            found, taken = node, i + 1
    return found, taken


def graft(root, segs, sub):
    spine, cursor = [], root
    for seg in segs:
        spine.append((cursor, seg))
        cursor = None if cursor is None else cursor.k.get(seg)
    built = sub
    while spine:
        node, seg = spine.pop()
        if node is None:
            kids, dfn, mark = {}, None, None
        else:
            kids, dfn, mark = dict(node.k), node.d, node.m
        if built is None:
            kids.pop(seg, None)
        else:
            kids[seg] = built
        built = Nd(dfn, kids, mark)
    return built


def put(root, segs, dfn):
    at = local(root, segs)
    return graft(root, segs, Nd(dfn, {} if at is None else at.k, None if at is None else at.m))


def under_region(root, segs):
    node = root
    for seg in segs[:-1]:
        node = node.k.get(seg)
        if node is None:
            return False
        if node.m is not None and node.m != "cut":
            return True
    return False


def cut(root, segs):
    return graft(root, segs, Nd(None, {}, "cut") if under_region(root, segs) else None)


def transfer(root, src, dst, kind):
    cleared = cut(root, dst)
    if kind == "tie":
        mark = ("tie", src, Moving(src, dst, None))
    elif kind == "mix":
        mark = ("copy", cleared, src, None)
    else:
        mark = ("copy", cleared, src, Moving(src, dst, root))
    return graft(cleared, dst, Nd(None, {}, mark))


# ---- reading a view by path ------------------------------------------------------------

def show(root, segs, seen):
    """What `segs` shows in the view `root`: the definition, or None."""
    if len(segs) > BOUND:
        return None
    node = local(root, segs)
    if node is not None and node.d is not None:
        return node.d
    mark, taken = nearest(root, segs)
    if mark is None or mark.m == "cut":
        return None
    rest = segs[taken:]
    m = mark.m
    if m[0] == "tie":
        target = m[1] + rest
        key = (id(root), target)
        if key in seen:
            return None
        return m[2].of(show(root, target, seen | {key}))
    _, froot, fpath, moving = m
    got = show(froot, fpath + rest, frozenset({(id(froot), fpath + rest)}))
    return got if moving is None else moving.of(got)


def shows(root, segs):
    return show(root, segs, frozenset({(id(root), segs)})) is not None


def image(mark, taken, segs):
    """Where the region `mark` sends the rest of `segs`: a (view, path) pair, or None."""
    m = mark.m
    if m == "cut":
        return None
    rest = segs[taken:]
    if m[0] == "tie":
        return None, m[1] + rest
    return m[1], m[2] + rest


class Counter:
    """Counts the shown paths under a path, one at a time, the way the rules read.

    The count at a path is one if something shows there, plus the counts under every segment
    that could have something beneath it: the written children, and whatever the enclosing
    region would put there. The recursion is on the remaining budget, so it always ends. A
    path with nothing written at or beneath it shows exactly what its region's image shows,
    so it counts as that image does; a ring of such paths shows nothing at all.
    """

    def __init__(self):
        self.memo = {}
        self.open = set()

    @staticmethod
    def region(root, segs):
        node = local(root, segs)
        if node is not None and node.m is not None:
            return node, len(segs)
        return nearest(root, segs)

    def kids(self, root, segs, seen):
        node = local(root, segs)
        out = set(node.k) if node is not None else set()
        mark, taken = self.region(root, segs)
        if mark is not None:
            img = image(mark, taken, segs)
            if img is not None:
                iroot = root if img[0] is None else img[0]
                key = (id(iroot), img[1])
                if key not in seen and len(img[1]) <= BOUND:
                    out |= self.kids(iroot, img[1], seen | {key})
        return out

    def count(self, root, segs, budget):
        budget = min(budget, BOUND - len(segs))
        if budget < 0:
            return 0
        key = (id(root), segs, budget)
        got = self.memo.get(key)
        if got is not None:
            return got
        if key in self.open:
            return 0
        self.open.add(key)
        node = local(root, segs)
        pure = node is None or (node.m is not None and not node.k and node.d is None)
        mark, taken = self.region(root, segs)
        img = None if mark is None else image(mark, taken, segs)
        if pure and img is not None:
            total = self.count(root if img[0] is None else img[0], img[1], budget)
        else:
            total = 1 if shows(root, segs) else 0
            for seg in self.kids(root, segs, frozenset({(id(root), segs)})):
                total += self.count(root, segs + (seg,), budget - 1)
        self.open.discard(key)
        self.memo[key] = total
        return total


# ---- running a plan ----------------------------------------------------------------------

class Run:
    def __init__(self, layers):
        self.view = [EMPTY]
        self.memo, self.busy = {}, set()
        self.sizes = Counter()
        self.top = len(layers)
        for j, ents in enumerate(layers):
            self.view.append(self._layer(j, ents))

    def _layer(self, j, ents):
        start = self.view[j]
        store = start
        for kind, a, bpath, expr, guard in ents:
            if guard is not None and not self._guard(guard, start):
                continue
            if kind == "put":
                store = put(store, a, Dn(expr, j, start))
            elif kind == "cut":
                store = cut(store, a)
            else:
                store = transfer(store, a, bpath, kind)
        return store

    def _guard(self, g, view):
        got = self.at(g[1], view)
        return got == GONE if g[0] == "un" else isinstance(got, int) and got == g[2]

    def at(self, path, view):
        dfn = show(view, path, frozenset({(id(view), path)}))
        if dfn is None:
            return GONE
        key = dfn, view
        if key in self.busy:
            return LOOP
        if key in self.memo:
            return self.memo[key]
        self.busy.add(key)
        try:
            out = self.ev(dfn.e, dfn.old, view)
        finally:
            self.busy.remove(key)
        self.memo[key] = out
        return out

    def ev(self, e, previous, view):
        tag = e[0]
        if tag == "lit":
            return e[1]
        if tag == "now":
            return self.at(e[1], view)
        if tag == "old":
            return self.at(e[1], previous)
        if tag == "pick":
            side = e[2] if shows(view, e[1]) else e[3]
            return self.ev(side, previous, view)
        left = self.ev(e[1], previous, view)
        if not isinstance(left, int):
            return left
        right = self.ev(e[2], previous, view)
        if not isinstance(right, int):
            return right
        return left + right if tag == "sum" else max(left, right)

    def line(self, kind, path, shown, named):
        view = self.view[self.top if named is None else named]
        if kind == "tot":
            return "num %s %d" % (shown, self.sizes.count(view, path, BOUND - len(path)))
        dfn = show(view, path, frozenset({(id(view), path)}))
        if dfn is None:
            return "val %s gone" % shown
        got = self.at(path, view)
        if got in (GONE, LOOP):
            return "val %s %s" % (shown, got)
        return "val %s %d %d" % (shown, got, dfn.h)


def trace(text):
    layers, asks = parse(text)
    run = Run(layers)
    return [run.line(kind, path, shown, named) for kind, path, shown, named in asks]

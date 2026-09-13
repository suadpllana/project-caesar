"""Independent model with persistent edge projections and explicit store views.

Path reads accumulate mapping projections without rewriting the tree. Edits rebuild
an explicit ancestor stack, transferring inherited maps only to untouched children.
Counting ignores projections. Each map separately caches rewritten definitions,
preserving aliases without enumerating all logical paths.
"""
import re
import sys
sys.setrecursionlimit(20000)
SEG = re.compile(r"[a-z][a-z0-9]{0,7}\Z")
GONE = "gone"
LOOP = "loop"


class Dn:
    __slots__ = ("e", "h", "old")
    def __init__(self, expr, origin, previous):
        self.e, self.h, self.old = expr, origin, previous


class Nd:
    __slots__ = ("d", "k")
    def __init__(self, dfn, kids):
        self.d, self.k = dfn, kids


class Ref:
    """A physical subtree and the maps applied to every definition beneath it."""
    __slots__ = ("node", "maps")
    def __init__(self, node, maps=()):
        self.node, self.maps = node, maps
    def __hash__(self):
        return hash((self.node, self.maps))
    def __eq__(self, other):
        return isinstance(other, Ref) and self.node is other.node and self.maps == other.maps


EMPTY = Ref(Nd(None, {}))


def _path(tok):
    segs = tok.split(".")
    if not 1 <= len(segs) <= 24 or any(not SEG.match(s) for s in segs):
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
        elif t[0] in ("mix", "map"):
            layers[-1].append((t[0], _path(t[1]), _path(t[2]), None, _guard(t[3:])))
        else:
            raise ValueError(raw)
    return layers, asks


class Mapping:
    """One entry and its source-identity cache, independent of destination paths."""
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
            got = Dn(self.expr(dfn.e), dfn.h, self.before)
            self.made[dfn] = got
        return got


def project(ref, maps):
    if ref is None or not maps:
        return ref
    return Ref(ref.node, ref.maps + maps)


def definition(ref):
    if ref is None:
        return None
    dfn = ref.node.d
    for item in ref.maps:
        dfn = item.of(dfn)
    return dfn


def child(ref, seg):
    if ref is None:
        return None
    return project(ref.node.k.get(seg), ref.maps)


def down(root, segs):
    for seg in segs:
        root = child(root, seg)
        if root is None:
            break
    return root


def graft(root, segs, sub):
    """Reconstruct an edited path and project only its untouched siblings."""
    spine, cursor = [], root
    for seg in segs:
        spine.append((cursor, seg))
        cursor = child(cursor, seg)
    built = sub
    while spine:
        ref, seg = spine.pop()
        if ref is None:
            kids, dfn = {}, None
        else:
            kids = {k: project(v, ref.maps) for k, v in ref.node.k.items()}
            dfn = definition(ref)
        if built is None:
            kids.pop(seg, None)
        else:
            kids[seg] = built
        built = Ref(Nd(dfn, kids))
    return built


def put(root, segs, dfn):
    ref = down(root, segs)
    kids = {} if ref is None else {k: project(v, ref.maps) for k, v in ref.node.k.items()}
    return graft(root, segs, Ref(Nd(dfn, kids)))


def transfer(root, src, dst, mapped):
    cleared = graft(root, dst, None)
    source = down(cleared, src)
    if mapped:
        source = project(source, (Mapping(src, dst, root),))
    return graft(cleared, dst, source)


class Sizer:
    """Physical structure determines counts; definition projections do not."""
    def __init__(self):
        self.seen = {}
    def of(self, ref):
        if ref is None:
            return 0
        node = ref.node
        got = self.seen.get(node)
        if got is None:
            got = int(node.d is not None) + sum(self.of(v) for v in node.k.values())
            self.seen[node] = got
        return got


class Run:
    def __init__(self, layers):
        self.view = [EMPTY]
        self.memo, self.open = {}, set()
        self.size = Sizer()
        self.top = len(layers)
        for j, ents in enumerate(layers):
            self.view.append(self._layer(j, ents))
    def _layer(self, j, ents):
        start = self.view[j]
        taken = [e for e in ents if e[4] is None or self._guard(e[4], start)]
        store = start
        for kind, a, bpath, expr, _ in taken:
            if kind == "put":
                store = put(store, a, Dn(expr, j, start))
            elif kind == "cut":
                store = graft(store, a, None)
            else:
                store = transfer(store, a, bpath, kind == "map")
        return store
    def _guard(self, g, view):
        got = self.at(g[1], view)
        return got == GONE if g[0] == "un" else isinstance(got, int) and got == g[2]
    def at(self, path, view):
        dfn = definition(down(view, path))
        if dfn is None:
            return GONE
        key = dfn, view
        if key in self.open:
            return LOOP
        if key in self.memo:
            return self.memo[key]
        self.open.add(key)
        try:
            out = self.ev(dfn.e, dfn.old, view)
        finally:
            self.open.remove(key)
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
            side = e[2] if definition(down(view, e[1])) is not None else e[3]
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
            return "num %s %d" % (shown, self.size.of(down(view, path)))
        dfn = definition(down(view, path))
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

"""An independent implementation of the contract, written from the specification.

It is not the reference rearranged. Where the stated scale forces both to index the store as
a tree of nodes that are never changed after they are built - a copy has to be a node
reference or the doubling family cannot be answered at all - the two differ everywhere else:

  * this one copies a path with an explicit stack and no recursion, and works out how many
    defined paths sit under a node by walking it with a memo on node identity, rather than
    carrying a number on every node and maintaining it by arithmetic;
  * it answers every guard of a layer in one pass before it applies any of that layer's
    entries, rather than answering each guard as the entry comes up;
  * it memoises a value, and detects circularity, on the pair of the path and the stop rather
    than on the pair of the definition and the stop - a different key that has to agree with
    the reference on every program where one definition stands at several paths;
  * it parses the plan itself.

The pairing is checked both ways before anything is graded: the model has to reproduce
`gt.json` line for line, and the differential run in the task's STATE.md records how many
plans the two were compared on.
"""

import re
import sys

sys.setrecursionlimit(20000)

SEG = re.compile(r"[a-z][a-z0-9]{0,7}\Z")


class Nd:
    """A node: the definition at this path, and the children by segment."""

    __slots__ = ("d", "k")

    def __init__(self, d, k):
        self.d = d
        self.k = k


class Dn:
    """A definition: the expression, and the layer whose `put` wrote it."""

    __slots__ = ("e", "h")

    def __init__(self, e, h):
        self.e = e
        self.h = h


EMPTY = Nd(None, {})
GONE = "gone"
LOOP = "loop"


# ---------------------------------------------------------------- parsing

def _path(tok):
    segs = tok.split(".")
    if not 1 <= len(segs) <= 24:
        raise ValueError(tok)
    for s in segs:
        if not SEG.match(s):
            raise ValueError(tok)
    return tuple(segs)


def _expr(toks, i):
    head = toks[i]
    if head == "lit":
        return ("lit", int(toks[i + 1])), i + 2
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
        return ("pick", p, a, b), i
    raise ValueError(head)


def _guard(toks):
    if not toks:
        return None
    if toks[0] == "if":
        return ("if", _path(toks[1]), int(toks[2]))
    return ("un", _path(toks[1]))


def parse(text):
    layers = []
    asks = []
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
        elif t[0] == "mix":
            layers[-1].append(("mix", _path(t[1]), _path(t[2]), None, _guard(t[3:])))
        else:
            raise ValueError(raw)
    return layers, asks


# ---------------------------------------------------------------- the store

def down(node, segs):
    for s in segs:
        if node is None:
            return None
        node = node.k.get(s)
    return node


def graft(root, segs, sub):
    """Put `sub` (a node or None) at `segs`, copying only the nodes on the way there."""
    spine = []
    node = root
    for s in segs:
        spine.append((node, s))
        node = None if node is None else node.k.get(s)
    built = sub
    while spine:
        node, s = spine.pop()
        kids = dict(node.k) if node is not None else {}
        if built is None:
            kids.pop(s, None)
        else:
            kids[s] = built
        built = Nd(None if node is None else node.d, kids)
    return built


def put(root, segs, dfn):
    at = down(root, segs)
    return graft(root, segs, Nd(dfn, {} if at is None else at.k))


def mix(root, src, dst):
    cleared = graft(root, dst, None)
    return graft(cleared, dst, down(cleared, src))


class Sizer:
    """How many defined paths sit under a node, memoised on the node itself."""

    def __init__(self):
        self.seen = {}

    def of(self, node):
        if node is None:
            return 0
        got = self.seen.get(node)
        if got is None:
            got = 1 if node.d is not None else 0
            for kid in node.k.values():
                got += self.of(kid)
            self.seen[node] = got
        return got


# ---------------------------------------------------------------- answering

class Run:
    def __init__(self, layers):
        self.view = [EMPTY]
        self.memo = {}
        self.open = set()
        self.size = Sizer()
        self.top = len(layers)
        for j, ents in enumerate(layers):
            self.view.append(self._layer(j, ents))

    def _layer(self, j, ents):
        # Every guard of the layer is answered first, against the store the layer started
        # from; only then is anything applied.
        taken = [e for e in ents if e[4] is None or self._guard(e[4], j)]
        store = self.view[j]
        for kind, a, bpath, expr, _ in taken:
            if kind == "put":
                store = put(store, a, Dn(expr, j))
            elif kind == "cut":
                store = graft(store, a, None)
            else:
                store = mix(store, a, bpath)
        return store

    def _guard(self, g, j):
        got = self.at(g[1], j)
        if g[0] == "un":
            return got == GONE
        return isinstance(got, int) and got == g[2]

    def at(self, path, stop):
        key = (path, stop)
        got = self.memo.get(key)
        if got is not None:
            return got
        if key in self.open:
            return LOOP
        node = down(self.view[stop], path)
        if node is None or node.d is None:
            self.memo[key] = GONE
            return GONE
        self.open.add(key)
        try:
            out = self.ev(node.d.e, node.d.h, stop)
        finally:
            self.open.discard(key)
        self.memo[key] = out
        return out

    def ev(self, e, home, stop):
        tag = e[0]
        if tag == "lit":
            return e[1]
        if tag == "now":
            return self.at(e[1], stop)
        if tag == "old":
            return self.at(e[1], home)
        if tag == "pick":
            node = down(self.view[stop], e[1])
            side = e[2] if node is not None and node.d is not None else e[3]
            return self.ev(side, home, stop)
        left = self.ev(e[1], home, stop)
        if not isinstance(left, int):
            return left
        right = self.ev(e[2], home, stop)
        if not isinstance(right, int):
            return right
        return left + right if tag == "sum" else max(left, right)

    def line(self, kind, path, shown, named):
        stop = self.top if named is None else named
        if kind == "tot":
            return "num %s %d" % (shown, self.size.of(down(self.view[stop], path)))
        node = down(self.view[stop], path)
        if node is None or node.d is None:
            return "val %s gone" % shown
        got = self.at(path, stop)
        if got == GONE:
            return "val %s gone" % shown
        if got == LOOP:
            return "val %s loop" % shown
        return "val %s %d %d" % (shown, got, node.d.h)


def trace(text):
    layers, asks = parse(text)
    run = Run(layers)
    return [run.line(kind, path, shown, named) for kind, path, shown, named in asks]

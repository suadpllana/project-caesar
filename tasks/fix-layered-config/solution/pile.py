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

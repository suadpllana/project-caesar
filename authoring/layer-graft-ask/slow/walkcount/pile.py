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


def _walk(node):
    total = 1 if node.dfn is not None else 0
    for kid in node.kids.values():
        total += _walk(kid)
    return total


def count(store, path):
    node = _down(store, path)
    return 0 if node is None else _walk(node)

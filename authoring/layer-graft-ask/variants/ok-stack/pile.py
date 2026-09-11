"""Store: children in a sorted list found by bisection, and a count re-added on each rebuild.

The same shared-node idea, held differently. Children live in two parallel lists kept in
segment order rather than in a dict, a lookup bisects, and the number of defined paths under a
node is re-added from its children every time a node is built rather than carried forward by
arithmetic. Nothing is ever changed after it is built, which is what lets a copy be one node.
"""

import bisect

from cfg import made


class Node:
    __slots__ = ("dfn", "segs", "kids", "n")

    def __init__(self, dfn, segs, kids):
        self.dfn = dfn
        self.segs = segs
        self.kids = kids
        total = 1 if dfn is not None else 0
        for kid in kids:
            total += kid.n
        self.n = total


ROOT = Node(None, [], [])


def empty():
    return ROOT


def _at(node, seg):
    i = bisect.bisect_left(node.segs, seg)
    if i < len(node.segs) and node.segs[i] == seg:
        return node.kids[i]
    return None


def _swap(node, seg, kid):
    segs = list(node.segs)
    kids = list(node.kids)
    i = bisect.bisect_left(segs, seg)
    here = i < len(segs) and segs[i] == seg
    if kid is None:
        if here:
            del segs[i]
            del kids[i]
    elif here:
        kids[i] = kid
    else:
        segs.insert(i, seg)
        kids.insert(i, kid)
    return Node(node.dfn, segs, kids)


def _down(node, segs):
    for seg in segs:
        if node is None:
            return None
        node = _at(node, seg)
    return node


def _graft(root, segs, sub):
    spine = []
    node = root
    for seg in segs:
        spine.append((node, seg))
        node = None if node is None else _at(node, seg)
    built = sub
    while spine:
        node, seg = spine.pop()
        if node is None:
            built = None if built is None else Node(None, [seg], [built])
        else:
            built = _swap(node, seg, built)
    return built


def put(store, path, dfn):
    at = _down(store, path)
    fresh = Node(dfn, [], []) if at is None else Node(dfn, at.segs, at.kids)
    return _graft(store, path, fresh)


def cut(store, path):
    return _graft(store, path, None)


def mix(store, src, dst, at):
    cleared = _graft(store, dst, None)
    return _graft(cleared, dst, made.carried(_down(cleared, src), at))


def find(store, path):
    node = _down(store, path)
    return None if node is None else node.dfn


def count(store, path):
    node = _down(store, path)
    return 0 if node is None else node.n

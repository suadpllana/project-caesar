"""Store: nodes that carry no count, and a size worked out by walking with a memo.

Same shared-node idea the scale forces, and nothing else in common with the reference: the
path copy is iterative, the node carries no number, and how many defined paths sit under a
node is computed on demand and remembered against the node itself, which costs one walk per
distinct node however many paths that node stands at.
"""

from cfg import made


class Node:
    __slots__ = ("dfn", "kids")

    def __init__(self, dfn, kids):
        self.dfn = dfn
        self.kids = kids


ROOT = Node(None, {})


def empty():
    return ROOT


def _down(node, segs):
    for seg in segs:
        if node is None:
            return None
        node = node.kids.get(seg)
    return node


def _graft(root, segs, sub):
    spine = []
    node = root
    for seg in segs:
        spine.append((node, seg))
        node = None if node is None else node.kids.get(seg)
    built = sub
    while spine:
        node, seg = spine.pop()
        kids = dict(node.kids) if node is not None else {}
        if built is None:
            kids.pop(seg, None)
        else:
            kids[seg] = built
        built = Node(None if node is None else node.dfn, kids)
    return built


def put(store, path, dfn):
    at = _down(store, path)
    return _graft(store, path, Node(dfn, {} if at is None else at.kids))


def cut(store, path):
    return _graft(store, path, None)


def mix(store, src, dst, at):
    cleared = _graft(store, dst, None)
    return _graft(cleared, dst, made.carried(_down(cleared, src), at))


def find(store, path):
    node = _down(store, path)
    return None if node is None else node.dfn


def size(seen, node):
    if node is None:
        return 0
    got = seen.get(node)
    if got is None:
        got = 1 if node.dfn is not None else 0
        for kid in node.kids.values():
            got += size(seen, kid)
        seen[node] = got
    return got


def count(hist, store, path):
    return size(hist.seen, _down(store, path))

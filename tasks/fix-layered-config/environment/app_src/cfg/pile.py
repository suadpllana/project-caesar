from cfg import made


class Pile:
    __slots__ = ("defs", "ties")

    def __init__(self, defs, ties):
        self.defs = defs
        self.ties = ties


def empty():
    return Pile({}, {})


def copy(store):
    return Pile(dict(store.defs), dict(store.ties))


def _under(p, root):
    return len(p) >= len(root) and p[:len(root)] == root


def put(store, path, dfn):
    store.defs[path] = dfn
    return store


def cut(store, path):
    for p in [q for q in store.defs if _under(q, path)]:
        del store.defs[p]
    for p in [q for q in store.ties if _under(q, path)]:
        del store.ties[p]
    return store


def mix(store, src, dst, at):
    take = []
    for p, d in store.defs.items():
        if _under(p, src):
            take.append((dst + p[len(src):], made.carried(d, at)))
    for p, d in take:
        store.defs[p] = d
    return store


def tie(store, src, dst):
    cut(store, dst)
    store.ties[dst] = src
    return store


def find(store, path):
    dfn = store.defs.get(path)
    if dfn is not None:
        return dfn
    for dst, src in store.ties.items():
        if _under(path, dst):
            return store.defs.get(src + path[len(dst):])
    return None


def count(store, path):
    seen = set()
    for p in store.defs:
        if _under(p, path):
            for i in range(len(path), len(p) + 1):
                seen.add(p[:i])
    return len(seen)

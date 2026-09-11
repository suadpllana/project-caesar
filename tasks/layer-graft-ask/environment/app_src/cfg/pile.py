from cfg import made


def empty():
    return {}


def copy(store):
    return dict(store)


def _under(p, root):
    return len(p) >= len(root) and p[:len(root)] == root


def put(store, path, dfn):
    store[path] = dfn
    return store


def cut(store, path):
    for p in [q for q in store if _under(q, path)]:
        del store[p]
    return store


def mix(store, src, dst, at):
    take = []
    for p, d in store.items():
        if _under(p, src):
            take.append((dst + p[len(src):], made.carried(d, at)))
    for p, d in take:
        store[p] = d
    return store


def find(store, path):
    return store.get(path)


def count(store, path):
    seen = set()
    for p in store:
        if _under(p, path):
            for i in range(len(path), len(p) + 1):
                seen.add(p[:i])
    return len(seen)

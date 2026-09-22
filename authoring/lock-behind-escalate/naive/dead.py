def hard_edges(held, wait):
    edges = {}
    for req in wait.queue:
        edges[req.txn] = list(held.clashers(req.txn, req.tgt, req.mode))
    return edges


def on_cycles(edges):
    index = {}
    low = {}
    stack = []
    onstack = set()
    found = []
    counter = [0]

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        onstack.add(v)
        for u in edges.get(v, ()):
            if u not in index:
                strong(u)
                low[v] = min(low[v], low[u])
            elif u in onstack:
                low[v] = min(low[v], index[u])
        if low[v] == index[v]:
            comp = []
            while True:
                u = stack.pop()
                onstack.discard(u)
                comp.append(u)
                if u == v:
                    break
            if len(comp) > 1:
                found.extend(comp)

    for v in edges:
        if v not in index:
            strong(v)
    return found


def victim(held, wait):
    cyclic = on_cycles(hard_edges(held, wait))
    if not cyclic:
        return None
    return min(cyclic, key=lambda v: (held.count(v), -wait.of[v].seq))
